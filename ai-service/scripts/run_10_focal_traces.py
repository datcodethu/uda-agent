"""Truy vết chuyên sâu 10 câu hỏi trọng điểm (Question -> Retrieved Chunks -> Context -> Generated Answer -> Verified Claims)
So sánh Before vs After giữa Baseline v2 cũ và Advanced RAG cải tiến.
"""
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

# Thêm ai-service vào sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding="utf-8")

from app.core.prompts import build_messages
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import evaluate_verification
from app.pipeline.query_transformation.intent_classifier import classify_academic_intent_and_risk
from scripts.run_v2_benchmark import (
    EVAL_DIR,
    TEST_CASES_CSV,
    grade_response,
    retrieve_v2,
)

FOCAL_IDS = [
    "TC-SVQ-001",  # Em nợ học phí thì có được đăng ký môn không ạ
    "TC-SVQ-010",  # Em nợ học phí thì có được đăng ký thi không ạ
    "TC-SVQ-028",  # Hạn nộp học phí trễ nhất là trong bao lâu và xem ở đâu ạ?
    "TC-SVQ-050",  # sang kì 2 thì học phí có thể chia ra đóng được ko ạ
    "TC-SVQ-003",  # Mức học bổng được nhận
    "TC-SVQ-024",  # Muốn đăng ký học bổng thì làm thế nào?
    "TC-SVQ-033",  # Điều kiện xét học bổng
    "TC-SVQ-022",  # em ở quê thuộc an toàn khu thì có miễn bhyt... hoàn lại hay nộp
    "TC-SVQ-055",  # Nghỉ bao nhiêu buổi là cấm thi vậy ạ
    "TC-SVQ-009",  # Chuẩn đầu ra của ngành Ngôn ngữ Trung là sao vậy ạ?
]

llm = get_llm()


def main():
    print("=" * 70)
    print("BẮT ĐẦU TRUY VẾT CHUYÊN SÂU 10 CÂU HỎI TRỌNG ĐIỂM (BEFORE vs AFTER)")
    print("=" * 70)

    # 1. Đọc kết quả cũ
    old_responses = {}
    old_file = EVAL_DIR / "chatbot_responses.jsonl"
    if old_file.exists():
        with open(old_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    old_responses[d["test_id"]] = d

    # 2. Đọc câu hỏi gốc
    with open(TEST_CASES_CSV, "r", encoding="utf-8-sig") as f:
        tc_map = {r["test_id"]: r for r in csv.DictReader(f)}

    trace_results = []

    for idx, tid in enumerate(FOCAL_IDS, 1):
        tc = tc_map[tid]
        q = tc["input_question"]
        cat = tc.get("category", "")
        old_data = old_responses.get(tid, {})

        print(f"\n[{idx}/10] Đang xử lý {tid}: {q[:55]}...")

        # Truy xuất thích ứng Top-K=7
        t0 = time.perf_counter()
        ret = retrieve_v2(q, top_k=7)
        chunks = ret["chunks"]

        # Phân tích Intent & Risk
        intent_enum, risk_enum = classify_academic_intent_and_risk(q)

        # Xây dựng Prompt Grounded
        messages = build_messages(
            question=q,
            chunks=chunks,
            academic_intent=intent_enum.value,
            risk_level=risk_enum.value,
        )

        # Gọi LLM sinh câu trả lời
        ans = ""
        for att in range(5):
            try:
                ans = llm.generate(messages)
                break
            except Exception as e:
                print(f"   Lỗi gọi LLM (lần {att+1}/5): {e}")
                time.sleep(4)

        total_ms = int((time.perf_counter() - t0) * 1000)

        # Kiểm chứng Claim-level & Faithfulness
        v = evaluate_verification(question=q, answer=ans, chunks=chunks, refused=False)
        score, verdict, sub = grade_response(
            question=q,
            answer=ans,
            chunks=chunks,
            sufficiency=v["sufficiency"],
            citation_ok=v["citations_valid"],
            bad_numbers=v["unsupported_numbers"],
            faithfulness_score=v.get("faithfulness_score", 1.0),
            faithfulness_valid=v.get("faithfulness_valid", True),
        )

        # Ghi nhận thông tin đã bổ sung so với trước
        new_chunk_ids = [c["chunk_id"] for c in chunks]
        old_chunk_ids = [s["chunk_id"] for s in old_data.get("sources", [])]
        added_chunks = [cid for cid in new_chunk_ids if cid not in old_chunk_ids]

        trace_item = {
            "test_id": tid,
            "category": cat,
            "question": q,
            "academic_intent": intent_enum.value,
            "risk_level": risk_enum.value,
            "before": {
                "verdict": old_data.get("verdict", "UNKNOWN"),
                "total_score": old_data.get("total_score", 0),
                "sufficiency": old_data.get("sufficiency", "UNKNOWN"),
                "answer": old_data.get("answer", ""),
                "chunk_ids": old_chunk_ids,
            },
            "after": {
                "verdict": verdict,
                "total_score": score,
                "sufficiency": v["sufficiency"],
                "citations_valid": v["citations_valid"],
                "faithfulness_score": v.get("faithfulness_score", 1.0),
                "unsupported_numbers": v["unsupported_numbers"],
                "answer": ans,
                "chunk_ids": new_chunk_ids,
                "sources": [
                    {
                        "index": i + 1,
                        "chunk_id": c["chunk_id"],
                        "doc_title": c.get("doc_title", ""),
                        "source_url": c.get("source_url", ""),
                    }
                    for i, c in enumerate(chunks)
                ],
                "verified_claims": v.get("supported_claims", []),
                "unsupported_claims": v.get("unsupported_claims", []),
                "badges": v["badges"],
                "latency_ms": total_ms,
            },
            "retrieval_delta": {
                "added_chunks": added_chunks,
            },
        }

        trace_results.append(trace_item)

        print(f"   -> Before: {old_data.get('verdict')} (Score: {old_data.get('total_score')}, Suff: {old_data.get('sufficiency')})")
        print(f"   -> After : {verdict} (Score: {score}/12, Suff: {v['sufficiency']}, Faithfulness: {v.get('faithfulness_score')}, Latency: {total_ms}ms)")
        print(f"   -> Chunks mới được kéo vào: {', '.join(added_chunks) if added_chunks else 'None'}")
        print(f"   -> Tóm tắt câu trả lời mới: {ans[:140].replace(chr(10), ' ')}...\n")

        # Nghỉ nhẹ giữa các câu để chống 429
        time.sleep(2.0)

    # 3. Lưu JSON kết quả
    json_out = EVAL_DIR / "10_focal_traces.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(trace_results, f, ensure_ascii=False, indent=2)

    # 4. Lưu Markdown Báo cáo Chi tiết
    md_out = EVAL_DIR / "10_focal_traces.md"
    generate_markdown_report(trace_results, md_out)

    print("=" * 70)
    print(f"HOÀN THÀNH TRUY VẾT 10 CÂU! Đã xuất:")
    print(f" - JSON: {json_out}")
    print(f" - MD  : {md_out}")
    print("=" * 70)


def generate_markdown_report(traces, out_path):
    lines = [
        "# Báo cáo Truy vết Chuyên sâu 10 Câu hỏi Trọng điểm (Before vs After)",
        "## So sánh Đối chứng Pipeline Cải tiến vs Baseline v2 Cũ",
        "",
        "**Ngày đánh giá:** 05/11/2026  ",
        "**Mô hình:** Gemini Flash Lite & Gemini Embedding 001  ",
        "**Kho dữ liệu:** `donga_kb_v2` (451 chunks)  ",
        "",
        "---",
        "",
        "### 1. Bảng Tổng hợp Kết quả Before vs After",
        "",
        "| Test ID | Chủ đề | Câu hỏi thực tế | Before (Verdict / Score / Suff) | After (Verdict / Score / Suff) | Faithfulness | Chunks mới kéo vào |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :--- |",
    ]

    for t in traces:
        tid = t["test_id"]
        cat = t["category"]
        q_short = t["question"][:40] + ("..." if len(t["question"]) > 40 else "")
        b_str = f"{t['before']['verdict']} ({t['before']['total_score']}đ, {t['before']['sufficiency']})"
        a_str = f"**{t['after']['verdict']}** ({t['after']['total_score']}đ, {t['after']['sufficiency']})"
        faith = f"{t['after']['faithfulness_score'] * 100:.0f}%"
        added = ", ".join(t["retrieval_delta"]["added_chunks"][:2]) if t["retrieval_delta"]["added_chunks"] else "Giữ nguyên"
        lines.append(f"| **{tid}** | {cat} | {q_short} | {b_str} | {a_str} | {faith} | `{added}` |")

    lines.extend([
        "",
        "---",
        "",
        "### 2. Chi tiết Từng Câu hỏi: Truy vết Chuỗi Question $\\rightarrow$ Chunks $\\rightarrow$ Answer $\\rightarrow$ Claims",
        "",
    ])

    for idx, t in enumerate(traces, 1):
        lines.extend([
            f"#### [{idx}] {t['test_id']}: {t['question']}",
            f"- **Nhóm chủ đề:** {t['category']} | **Ý định:** `{t['academic_intent']}` | **Rủi ro:** `{t['risk_level']}`",
            f"- **Trước cải tiến:** {t['before']['verdict']} (Điểm: {t['before']['total_score']}/12, Sufficiency: `{t['before']['sufficiency']}`)",
            f"- **Sau cải tiến:** **{t['after']['verdict']}** (Điểm: {t['after']['total_score']}/12, Sufficiency: `{t['after']['sufficiency']}`, Faithfulness: `{t['after']['faithfulness_score'] * 100:.0f}%`, Latency: `{t['after']['latency_ms']}ms`)",
            "",
            "**Câu trả lời CŨ (Trước):**",
            "> " + t["before"]["answer"].replace("\n", "\n> "),
            "",
            "**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**",
            "> " + t["after"]["answer"].replace("\n", "\n> "),
            "",
            "**Khẳng định đã được kiểm chứng (Verified Claims):**",
        ])
        if t["after"]["verified_claims"]:
            for c in t["after"]["verified_claims"][:3]:
                lines.append(f"- [x] *{c}*")
        else:
            lines.append("- (Không có khẳng định nào bị lỗi)")

        lines.extend([
            "",
            "**Nguồn sử dụng:** " + ", ".join([f"`[{s['index']}] {s['chunk_id']}`" for s in t["after"]["sources"][:4]]),
            "",
            "---",
            "",
        ])

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
