"""Chạy bộ câu hỏi kiểm thử đánh giá benchmark cho hệ thống hỏi đáp quy chế.

Chạy:
    python -m scripts.chay_cau_hoi_thu [--mode hybrid|dense|bm25] [--retrieval-only] [--tap dev] [--max-calls 30] [--gom-ca-chua-xac-nhan] [--no-intent]
"""
from __future__ import annotations
import argparse
import copy
import csv
import datetime
import io
import json
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

from app.core.config import BASE_DIR, settings
from app.pipeline import rag_pipeline
from app.pipeline.retrieval.bm25_search import bm25_index

REQUIRED_COLUMNS = [
    "id", "nhom", "cau_hoi", "expected_dieu", "must_have", "expected_refuse", "tap"
]


def default_csv_path() -> Path:
    return BASE_DIR / "data" / "cau_hoi_thu.csv"


def get_git_commit() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(BASE_DIR.parent),
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def parse_cau_hoi_thu_csv(csv_path: Path, tap: str = "dev") -> tuple[list[dict], int]:
    """Đọc file CSV câu hỏi thử (UTF-8 BOM), lọc theo tập, bỏ qua câu hỏi rỗng.

    Đọc cờ da_xac_nhan (mặc định False nếu thiếu cột hoặc giá trị khác 'true').
    """
    resolved_path = csv_path.resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {resolved_path}")

    questions: list[dict] = []
    skipped_empty = 0

    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [k.strip() for k in (reader.fieldnames or []) if k]
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            raise ValueError(
                f"File CSV {csv_path.name} thiếu cột bắt buộc: {', '.join(missing)}. "
                f"Yêu cầu đủ các cột: {', '.join(REQUIRED_COLUMNS)}"
            )

        for row in reader:
            cleaned = {
                (k.strip() if k else ""): (v.strip() if isinstance(v, str) else v)
                for k, v in row.items()
                if k is not None
            }
            cau_hoi = cleaned.get("cau_hoi", "")
            if not cau_hoi:
                skipped_empty += 1
                continue

            row_tap = cleaned.get("tap", "").lower()
            if tap.lower() != "all" and row_tap != tap.lower():
                continue

            # Xử lý cờ da_xac_nhan: chỉ True khi chuỗi là 'true' (không phân biệt hoa thường)
            da_xac_nhan_raw = str(cleaned.get("da_xac_nhan", "")).strip().lower()
            cleaned["da_xac_nhan"] = (da_xac_nhan_raw == "true")

            questions.append(cleaned)

    return questions, skipped_empty


def evaluate_single_question(
    q: dict,
    mode: str,
    retrieval_only: bool,
    use_intent: bool = True
) -> dict:
    """Đánh giá 1 câu hỏi: tiền xử lý + truy xuất (+ sinh câu trả lời nếu không retrieval-only)."""
    question_text = q["cau_hoi"]
    item_result = {
        "id": q.get("id", ""),
        "nhom": q.get("nhom", "khac"),
        "cau_hoi": question_text,
        "expected_dieu": q.get("expected_dieu", ""),
        "must_have": q.get("must_have", ""),
        "expected_refuse": q.get("expected_refuse", "").lower() == "true",
        "tap": q.get("tap", ""),
        "ghi_chu": q.get("ghi_chu", ""),
        "da_xac_nhan": q.get("da_xac_nhan", False),
        "cham_tay": "",  # Cột trống để người dùng tự chấm tay (dung, thieu hoặc sai)
        "error": False,
        "loi_api": "",
    }

    try:
        if retrieval_only:
            p = rag_pipeline.prepare(question_text, mode=mode, use_intent=use_intent)
            chunks = p.chunks
            sources = p.sources
            refused = p.refused
            refuse_reason = p.refuse_reason
            answer_text = ""
            timing = p.timing
        else:
            r = rag_pipeline.answer(question_text, mode=mode, use_intent=use_intent)
            chunks = r.get("sources", [])
            sources = r.get("sources", [])
            refused = r["refused"]
            refuse_reason = r["refuse_reason"]
            answer_text = r["answer"]
            timing = r.get("timing", {})
    except Exception as e:
        item_result["error"] = True
        item_result["loi_api"] = str(e)
        item_result["timing"] = {}
        return item_result

    # 1. Ghi chunk_id của mọi đoạn được truy xuất kèm Điều và điểm (KHÔNG lưu nội dung đoạn)
    retrieved_meta = []
    for s in sources:
        retrieved_meta.append({
            "chunk_id": s.get("chunk_id", ""),
            "dieu": s.get("dieu", ""),
            "score": s.get("score", 0.0),
        })
    item_result["retrieved_chunks"] = retrieved_meta

    # 2. Đối chiếu must_have (kiểm tra theo ký tự chuỗi, chuẩn hóa Unicode NFC và không phân biệt hoa/thường)
    must_have_raw = q.get("must_have", "")
    must_have_phrases = [p.strip() for p in must_have_raw.split("|") if p.strip()]

    combined_chunks_text = unicodedata.normalize(
        "NFC", " ".join(c.get("text", "") for c in chunks)
    ).lower()
    norm_answer = unicodedata.normalize("NFC", answer_text).lower()

    must_have_eval = []
    missing_must_have = []
    for phrase in must_have_phrases:
        norm_phrase = unicodedata.normalize("NFC", phrase).lower()
        in_retrieval = norm_phrase in combined_chunks_text if combined_chunks_text else False
        in_answer = (norm_phrase in norm_answer) if (not retrieval_only and norm_answer) else False
        must_have_eval.append({
            "phrase": phrase,
            "in_retrieval": in_retrieval,
            "in_answer": in_answer,
        })
        if not in_retrieval:
            missing_must_have.append(phrase)
    item_result["must_have_eval"] = must_have_eval
    item_result["missing_must_have"] = missing_must_have
    item_result["retrieved_chunk_ids"] = [c.get("chunk_id", "") for c in chunks]

    # 3. Đối chiếu expected_dieu
    exp_dieu_raw = q.get("expected_dieu", "")
    exp_dieu_list = [
        unicodedata.normalize("NFC", d.strip()).lower()
        for d in exp_dieu_raw.split("|")
        if d.strip()
    ]
    if exp_dieu_list:
        retrieved_dieus = [
            unicodedata.normalize("NFC", c.get("dieu", "")).lower()
            for c in chunks
            if c.get("dieu")
        ]
        hit_dieu = any(
            any(ed in rd or rd in ed for ed in exp_dieu_list)
            for rd in retrieved_dieus
        )
    else:
        hit_dieu = None
    item_result["hit_expected_dieu"] = hit_dieu

    # 4. Đối chiếu expected_refuse
    exp_refuse = item_result["expected_refuse"]
    if retrieval_only:
        item_result["bot_refused"] = "N/A"
        item_result["refuse_reason"] = "N/A"
        item_result["refusal_match"] = "N/A"
        item_result["true_refusal"] = "N/A"
        item_result["false_refusal"] = False
    else:
        item_result["bot_refused"] = refused
        item_result["refuse_reason"] = refuse_reason
        item_result["refusal_match"] = (refused == exp_refuse)
        item_result["true_refusal"] = (exp_refuse is True and refused is True)
        item_result["false_refusal"] = (exp_refuse is False and refused is True)

    item_result["timing"] = timing
    return item_result


def compute_benchmark_summary(
    results: list[dict],
    retrieval_only: bool,
    gom_ca_chua_xac_nhan: bool = False
) -> dict:
    """Tổng hợp chỉ số theo từng nhóm câu hỏi và toàn bộ, báo rõ mẫu số từng tỷ lệ.

    Mặc định: CHỈ tính tỷ lệ trên các câu có da_xac_nhan = True (nếu có trường da_xac_nhan).
    Nếu gom_ca_chua_xac_nhan = True: tính trên toàn bộ các câu không lỗi API.
    """
    valid_results = [r for r in results if not r.get("error")]
    api_errors = [r for r in results if r.get("error")]

    # Nếu có trường da_xac_nhan và cờ gom_ca_chua_xac_nhan = False: lọc chỉ câu đã xác nhận
    has_da_xac_nhan_field = any("da_xac_nhan" in r for r in valid_results)
    if has_da_xac_nhan_field and not gom_ca_chua_xac_nhan:
        eval_pool = [r for r in valid_results if r.get("da_xac_nhan") is True]
    else:
        eval_pool = valid_results

    groups: dict[str, list[dict]] = {}
    for r in eval_pool:
        groups.setdefault(r["nhom"], []).append(r)

    def summarize_subset(subset: list[dict]) -> dict:
        total_q = len(subset)
        if total_q == 0:
            return {
                "count": 0,
                "must_have_retrieval": {"num": 0, "denom": 0, "rate": None},
                "must_have_answer": {"num": 0, "denom": 0, "rate": None},
                "hit_expected_dieu": {"num": 0, "denom": 0, "rate": None},
                "true_refuse": {"num": 0, "denom": 0, "rate": None},
                "false_refuse": {"num": 0, "denom": 0, "rate": None},
                "avg_timing_ms": {},
            }

        # must_have: chỉ tính trên câu có must_have
        mh_denom = 0
        mh_retrieval_num = 0
        mh_answer_num = 0
        for r in subset:
            for item in r.get("must_have_eval", []):
                mh_denom += 1
                if item["in_retrieval"]:
                    mh_retrieval_num += 1
                if item["in_answer"]:
                    mh_answer_num += 1

        mh_ret_rate = (mh_retrieval_num / mh_denom) if mh_denom > 0 else None
        mh_ans_rate = (mh_answer_num / mh_denom) if (mh_denom > 0 and not retrieval_only) else None

        # hit Điều: chỉ tính trên câu có expected_dieu
        dieu_subset = [r for r in subset if r.get("hit_expected_dieu") is not None]
        dieu_denom = len(dieu_subset)
        dieu_num = sum(1 for r in dieu_subset if r["hit_expected_dieu"] is True)
        dieu_rate = (dieu_num / dieu_denom) if dieu_denom > 0 else None

        # từ chối đúng: chỉ trên câu expected_refuse = True
        true_refuse_subset = [r for r in subset if r["expected_refuse"] is True]
        tr_denom = len(true_refuse_subset)
        tr_num = sum(1 for r in true_refuse_subset if r["true_refusal"] is True)
        tr_rate = (tr_num / tr_denom) if tr_denom > 0 else None

        # từ chối nhầm: chỉ trên câu expected_refuse = False
        false_refuse_subset = [r for r in subset if r["expected_refuse"] is False]
        fr_denom = len(false_refuse_subset)
        fr_num = sum(1 for r in false_refuse_subset if r["false_refusal"] is True)
        fr_rate = (fr_num / fr_denom) if fr_denom > 0 else None

        # Thời gian
        timing_keys = ["embedding_ms", "qdrant_ms", "bm25_ms", "llm_ms", "total_ms"]
        avg_timing = {}
        for k in timing_keys:
            vals = [r["timing"].get(k, 0) for r in subset if r.get("timing")]
            avg_timing[k] = round(sum(vals) / len(vals), 1) if vals else 0.0

        return {
            "count": total_q,
            "must_have_retrieval": {"num": mh_retrieval_num, "denom": mh_denom, "rate": mh_ret_rate},
            "must_have_answer": {"num": mh_answer_num, "denom": mh_denom, "rate": mh_ans_rate},
            "hit_expected_dieu": {"num": dieu_num, "denom": dieu_denom, "rate": dieu_rate},
            "true_refuse": {"num": tr_num, "denom": tr_denom, "rate": tr_rate},
            "false_refuse": {"num": fr_num, "denom": fr_denom, "rate": fr_rate},
            "avg_timing_ms": avg_timing,
        }

    summary_by_group = {grp: summarize_subset(items) for grp, items in sorted(groups.items())}
    overall_summary = summarize_subset(eval_pool)

    return {
        "by_group": summary_by_group,
        "overall": overall_summary,
        "total_evaluated": len(eval_pool),
        "total_valid_results": len(valid_results),
        "total_api_errors": len(api_errors),
        "gom_ca_chua_xac_nhan": gom_ca_chua_xac_nhan,
    }


def export_benchmark_json(
    results: list[dict],
    summary: dict,
    mode: str,
    tap: str,
    retrieval_only: bool,
    actual_api_calls: int,
    output_dir: Path,
    timestamp_str: str | None = None,
    no_intent: bool = False,
    gom_ca_chua_xac_nhan: bool = False,
    so_da_xac_nhan: int = 0,
    so_chua_xac_nhan: int = 0,
) -> Path:
    """Xuất file kết quả chi tiết dạng JSON kèm cấu hình chạy và cột cham_tay."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts_str = timestamp_str or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"benchmark_{ts_str}.json"

    json_summary = copy.deepcopy(summary)
    json_results = copy.deepcopy(results)

    if retrieval_only:
        for grp_data in json_summary.get("by_group", {}).values():
            grp_data["true_refuse"] = {"status": "N/A", "num": "N/A", "denom": "N/A", "rate": "N/A"}
            grp_data["false_refuse"] = {"status": "N/A", "num": "N/A", "denom": "N/A", "rate": "N/A"}
        if "overall" in json_summary:
            json_summary["overall"]["true_refuse"] = {"status": "N/A", "num": "N/A", "denom": "N/A", "rate": "N/A"}
            json_summary["overall"]["false_refuse"] = {"status": "N/A", "num": "N/A", "denom": "N/A", "rate": "N/A"}

        for r in json_results:
            r["bot_refused"] = "N/A"
            r["refuse_reason"] = "N/A"
            r["refusal_match"] = "N/A"
            r["true_refusal"] = "N/A"
            r["false_refusal"] = "N/A"

    payload = {
        "config": {
            "git_commit": get_git_commit(),
            "chat_model": settings.gemini_chat_model,
            "embedding_model": settings.gemini_embedding_model,
            "top_k": settings.top_k,
            "candidate_k": settings.candidate_k,
            "max_context_chunks": settings.max_context_chunks,
            "min_dense_score": settings.min_dense_score,
            "mode": mode,
            "tap": tap,
            "retrieval_only": retrieval_only,
            "intent_enabled": not no_intent,
            "gom_ca_chua_xac_nhan": gom_ca_chua_xac_nhan,
            "so_da_xac_nhan": so_da_xac_nhan,
            "so_chua_xac_nhan": so_chua_xac_nhan,
            "actual_api_calls": actual_api_calls,
            "timestamp": datetime.datetime.now().isoformat(),
            "note": "Kiem tra must_have la so khop chuoi ky tu NFC, khong bat duoc dien dat khac.",
        },
        "summary": json_summary,
        "results": json_results,
    }

    with out_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return out_file


def export_benchmark_csv_cham_tay(
    results: list[dict],
    output_dir: Path,
    retrieval_only: bool = True,
    timestamp_str: str | None = None
) -> Path:
    """Xuất file CSV chấm tay UTF-8 có BOM (utf-8-sig) gồm 9 cột chuẩn để mở bằng Excel."""
    output_dir.mkdir(parents=True, exist_ok=True)
    ts_str = timestamp_str or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"cham_tay_{ts_str}.csv"

    fieldnames = [
        "id", "nhom", "cau_hoi", "cau_tra_loi", "nguon", "bot_refused", "tong_ms", "cham_tay", "ghi_chu"
    ]

    with out_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            retrieved_chunks = r.get("retrieved_chunks", [])
            nguon_str = "; ".join(
                f"{c.get('chunk_id', '')}|{c.get('dieu', '')}|{c.get('score', 0.0):.4f}"
                for c in retrieved_chunks
            )

            if retrieval_only:
                cau_tra_loi = ""
                bot_refused = "N/A"
            else:
                cau_tra_loi = r.get("answer", "")
                bot_refused = "true" if r.get("bot_refused") is True else "false"

            tong_ms = r.get("timing", {}).get("total_ms", 0)

            writer.writerow({
                "id": r.get("id", ""),
                "nhom": r.get("nhom", ""),
                "cau_hoi": r.get("cau_hoi", ""),
                "cau_tra_loi": cau_tra_loi,
                "nguon": nguon_str,
                "bot_refused": bot_refused,
                "tong_ms": tong_ms,
                "cham_tay": "",
                "ghi_chu": r.get("ghi_chu", ""),
            })

    return out_file


def format_rate(stat: dict) -> str:
    if not isinstance(stat, dict):
        return "N/A"
    if stat.get("rate") == "N/A" or stat.get("status") == "N/A":
        return "N/A"
    denom = stat.get("denom", 0)
    rate = stat.get("rate")
    if denom == 0 or rate is None or denom == "N/A":
        return "N/A"
    return f"{rate:.1%} ({stat['num']}/{denom})"


def print_summary_table(summary: dict, retrieval_only: bool, gom_ca_chua_xac_nhan: bool = False) -> None:
    """In bảng tổng hợp theo từng nhóm câu hỏi ra terminal (không in nội dung câu chữ)."""
    by_group = summary.get("by_group", {})
    overall = summary.get("overall", {})

    scope_title = "GỒM CẢ CÂU CHƯA XÁC NHẬN" if gom_ca_chua_xac_nhan else "CHỈ TÍNH CÂU ĐÃ XÁC NHẬN (da_xac_nhan=true)"

    print("\n" + "=" * 90)
    print(f" BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ BENCHMARK THEO NHÓM ({scope_title})")
    print("=" * 90)
    hdr = f"{'Nhóm câu hỏi':<18} | {'Số câu':<6} | {'MH Đoạn':<14} | {'MH Trả lời':<14} | {'Hit Điều':<14} | {'TC Đúng':<14} | {'TC Nhầm':<14} | {'TG TB'}"
    print(hdr)
    print("-" * 90)

    for grp, s in by_group.items():
        mh_ans = "N/A (retrieval)" if retrieval_only else format_rate(s["must_have_answer"])
        tc_dung = "N/A" if retrieval_only else format_rate(s["true_refuse"])
        tc_nham = "N/A" if retrieval_only else format_rate(s["false_refuse"])
        tg_str = f"{s['avg_timing_ms'].get('total_ms', 0):.0f} ms"
        row_str = (
            f"{grp:<18} | "
            f"{s['count']:<6} | "
            f"{format_rate(s['must_have_retrieval']):<14} | "
            f"{mh_ans:<14} | "
            f"{format_rate(s['hit_expected_dieu']):<14} | "
            f"{tc_dung:<14} | "
            f"{tc_nham:<14} | "
            f"{tg_str}"
        )
        print(row_str)

    print("-" * 90)
    ov = overall
    ov_mh_ans = "N/A (retrieval)" if retrieval_only else format_rate(ov["must_have_answer"])
    ov_tc_dung = "N/A" if retrieval_only else format_rate(ov["true_refuse"])
    ov_tc_nham = "N/A" if retrieval_only else format_rate(ov["false_refuse"])
    ov_tg_str = f"{ov['avg_timing_ms'].get('total_ms', 0):.0f} ms"
    print(
        f"{'TỔNG CỘNG':<18} | "
        f"{ov['count']:<6} | "
        f"{format_rate(ov['must_have_retrieval']):<14} | "
        f"{ov_mh_ans:<14} | "
        f"{format_rate(ov['hit_expected_dieu']):<14} | "
        f"{ov_tc_dung:<14} | "
        f"{ov_tc_nham:<14} | "
        f"{ov_tg_str}"
    )
    print("=" * 90)

    t = ov.get("avg_timing_ms", {})
    print(
        f"\n[PHÂN RÃ THỜI GIAN TRUNG BÌNH (ms)]:\n"
        f"  - Embedding câu hỏi : {t.get('embedding_ms', 0)} ms\n"
        f"  - Tìm kiếm Qdrant   : {t.get('qdrant_ms', 0)} ms\n"
        f"  - Tìm kiếm BM25     : {t.get('bm25_ms', 0)} ms\n"
        f"  - Sinh chữ LLM      : {t.get('llm_ms', 0)} ms\n"
        f"  - Tổng cộng         : {t.get('total_ms', 0)} ms\n"
    )

    if summary.get("total_api_errors", 0) > 0:
        print(f"[CẢNH BÁO] Có {summary['total_api_errors']} câu hỏi bị loại khỏi thống kê do lỗi API.")

    if not gom_ca_chua_xac_nhan and ov["count"] == 0:
        print("[LƯU Ý] Không có câu hỏi nào có da_xac_nhan=true. Để xem kết quả trên toàn bộ câu hỏi chưa xác nhận, thêm cờ --gom-ca-chua-xac-nhan.")


def print_missing_must_have_table(results: list[dict]) -> None:
    """In danh sách các cụm must_have bị thiếu theo từng câu (chỉ in cụm ngắn và mã chunk)."""
    items_with_missing = [r for r in results if r.get("missing_must_have")]

    print("\n" + "=" * 90)
    print(" DANH SÁCH CÁC CỤM MUST_HAVE BỊ THIẾU TRONG CÁC ĐOẠN TRUY XUẤT")
    print("=" * 90)
    if not items_with_missing:
        print("[THÔNG TIN] Không có cụm must_have nào bị thiếu khỏi các đoạn truy xuất.")
        print("=" * 90)
        return

    hdr = f"{'Câu ID':<8} | {'Cụm thiếu':<25} | {'Chunk IDs đã truy xuất'}"
    print(hdr)
    print("-" * 90)
    for r in items_with_missing:
        cid = r.get("id", "")
        missing_str = ", ".join(r.get("missing_must_have", []))
        retrieved_ids = ", ".join(r.get("retrieved_chunk_ids", []))
        print(f"{cid:<8} | {missing_str:<25} | {retrieved_ids}")
    print("=" * 90)


def run_benchmark(
    csv_path: Path,
    mode: str = "hybrid",
    retrieval_only: bool = True,
    tap: str = "dev",
    max_calls: int = 30,
    output_dir: Path | None = None,
    gom_ca_chua_xac_nhan: bool = False,
    no_intent: bool = False,
) -> dict:
    """Thực thi kiểm thử benchmark trên bộ câu hỏi."""
    resolved_path = csv_path.resolve()
    if not csv_path.exists():
        print(f"[LỖI] Không tìm thấy file: {resolved_path}")
        sys.exit(1)

    out_dir = output_dir or (BASE_DIR / "evaluation" / "benchmarks_result")

    # 1. Khởi động BM25 index
    bm25_index.rebuild()

    # 2. Đọc bộ câu hỏi
    print(f"[THÔNG TIN] Đọc từ file: {csv_path.name} (Đường dẫn: {resolved_path})")
    questions, skipped_empty = parse_cau_hoi_thu_csv(csv_path, tap=tap)
    so_da_xac_nhan = sum(1 for q in questions if q.get("da_xac_nhan") is True)
    so_chua_xac_nhan = len(questions) - so_da_xac_nhan
    print(
        f"[THÔNG TIN] Đọc {len(questions)} câu hỏi hợp lệ từ {csv_path.name} (Tập: '{tap}'): "
        f"{so_da_xac_nhan} câu đã xác nhận (da_xac_nhan=true), {so_chua_xac_nhan} câu chưa xác nhận."
    )
    if skipped_empty > 0:
        print(f"[THÔNG TIN] Đã bỏ qua {skipped_empty} dòng có câu hỏi rỗng.")

    if not gom_ca_chua_xac_nhan:
        print("[QUY TẮC ĐÁNH GIÁ] Mặc định CHỈ tính chỉ số đánh giá trên các câu có da_xac_nhan = true.")
    else:
        print("[QUY TẮC ĐÁNH GIÁ] Cờ --gom-ca-chua-xac-nhan đang BẬT: Tính chỉ số trên cả câu chưa xác nhận.")

    if no_intent:
        print("[CẤU HÌNH] Cờ --no-intent đang BẬT: Tắt bộ phân loại ý định (mọi câu đều truy xuất).")

    # 3. Dự toán số lượt gọi API
    estimated_calls = len(questions) * (0 if mode == "bm25" else 1) + (0 if retrieval_only else len(questions))
    print(f"[DỰ TOÁN API] Dự kiến gọi tối đa ~{estimated_calls} lệnh API (Ngưỡng chặn max-calls: {max_calls}).")
    if estimated_calls > max_calls:
        print(f"[CẢNH BÁO] Số lệnh dự kiến ({estimated_calls}) vượt quá max-calls ({max_calls}). Hệ thống sẽ dừng trước khi vượt.")

    results = []
    actual_api_calls = 0

    for idx, q in enumerate(questions, 1):
        if actual_api_calls >= max_calls:
            print(f"[DỪNG SỚM] Đã đạt hạn mức an toàn {max_calls} lệnh API gọi.")
            break

        if mode != "bm25":
            actual_api_calls += 1
        if not retrieval_only:
            actual_api_calls += 1

        res = evaluate_single_question(
            q,
            mode=mode,
            retrieval_only=retrieval_only,
            use_intent=(not no_intent)
        )
        results.append(res)

        if res.get("error"):
            err_msg = res.get("loi_api", "").lower()
            if "429" in err_msg or "quota" in err_msg or "resource_exhausted" in err_msg:
                print(f"[LỖI HẠN MỨC API] Gặp lỗi hạn mức ({res['loi_api']}), dừng sớm benchmark.")
                break

    # 4. Tính toán tổng hợp
    summary = compute_benchmark_summary(
        results,
        retrieval_only=retrieval_only,
        gom_ca_chua_xac_nhan=gom_ca_chua_xac_nhan
    )

    # 5. Xuất JSON và CSV
    ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = export_benchmark_json(
        results=results,
        summary=summary,
        mode=mode,
        tap=tap,
        retrieval_only=retrieval_only,
        actual_api_calls=actual_api_calls,
        output_dir=out_dir,
        timestamp_str=ts_str,
        no_intent=no_intent,
        gom_ca_chua_xac_nhan=gom_ca_chua_xac_nhan,
        so_da_xac_nhan=so_da_xac_nhan,
        so_chua_xac_nhan=so_chua_xac_nhan,
    )
    print(f"[XUẤT KẾT QUẢ] Đã lưu file kết quả JSON: {out_file}")

    out_csv = export_benchmark_csv_cham_tay(
        results=results,
        output_dir=out_dir,
        retrieval_only=retrieval_only,
        timestamp_str=ts_str
    )
    print(f"[XUẤT KẾT QUẢ] Đã lưu file CSV chấm tay: {out_csv}")

    # 6. In bảng tổng hợp ra terminal
    print_summary_table(
        summary,
        retrieval_only=retrieval_only,
        gom_ca_chua_xac_nhan=gom_ca_chua_xac_nhan
    )

    # 7. In bảng danh sách các cụm must_have bị thiếu
    print_missing_must_have_table(results)

    return {
        "summary": summary,
        "results": results,
        "json_path": out_file,
        "csv_path": out_csv,
    }


def main(argv: list[str] | None = None) -> None:
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, io.UnsupportedOperation):
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="Chạy bộ câu hỏi kiểm thử benchmark RAG.")
    parser.add_argument("--mode", default="hybrid", choices=["dense", "bm25", "hybrid"], help="Chế độ tìm kiếm")
    parser.add_argument("--retrieval-only", action="store_true", default=False, help="Chỉ kiểm tra truy xuất, không gọi LLM sinh câu trả lời")
    parser.add_argument("--tap", default="dev", help="Tập câu hỏi cần chạy (mặc định: dev, hoặc all)")
    parser.add_argument("--max-calls", type=int, default=30, help="Số lệnh gọi API tối đa trước khi dừng (mặc định: 30)")
    parser.add_argument("--csv", type=Path, default=default_csv_path(), help="Đường dẫn file CSV câu hỏi")
    parser.add_argument("--output-dir", type=Path, default=BASE_DIR / "evaluation" / "benchmarks_result", help="Thư mục xuất file JSON")
    parser.add_argument("--gom-ca-chua-xac-nhan", action="store_true", default=False, help="Tính các tỷ lệ đánh giá trên cả câu chưa xác nhận (da_xac_nhan != true)")
    parser.add_argument("--no-intent", action="store_true", default=False, help="Tắt bộ phân loại ý định (không kích hoạt đường tắt)")

    args = parser.parse_args(argv)
    run_benchmark(
        csv_path=args.csv,
        mode=args.mode,
        retrieval_only=bool(args.retrieval_only),
        tap=args.tap,
        max_calls=args.max_calls,
        output_dir=args.output_dir,
        gom_ca_chua_xac_nhan=bool(args.gom_ca_chua_xac_nhan),
        no_intent=bool(args.no_intent),
    )


if __name__ == "__main__":
    main()
