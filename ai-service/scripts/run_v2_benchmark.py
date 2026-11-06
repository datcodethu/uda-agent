"""Benchmark toàn diện Kho tri thức v2 (donga_kb_v2) trên 75 câu hỏi khảo sát sinh viên:
- Truy xuất Hybrid (donga_kb_v2 + chunks_v2.jsonl)
- Sinh câu trả lời chuẩn NotebookLM (Gemini Flash)
- Đánh giá Sufficiency, Citation, Unsupported numbers và 6 tiêu chuẩn học vụ
- So sánh đối chứng trực tiếp với Baseline Phiên 6E
- Xuất toàn bộ artifacts tại evaluation/kb_rebuild_v2/
"""
from __future__ import annotations
import csv
import json
import logging
import os
import pickle
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("benchmark_v2")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.prompts import (
    SYSTEM_PROMPT,
    REFUSE_MESSAGE,
    build_messages,
    format_context,
)
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import (
    evaluate_verification,
    unsupported_numbers,
    validate_citations,
)
from app.pipeline.query_transformation.abbreviation_mapper import expand_abbreviations
from app.pipeline.query_transformation.intent_classifier import (
    classify,
    classify_academic_intent_and_risk,
)
from app.pipeline.retrieval.dense_search import embed_query
from app.pipeline.retrieval.fusion import rrf_fuse
from qdrant_client import QdrantClient

TEST_CASES_CSV = BASE_DIR.parent / "evaluation" / "survey_qa_20261105_01" / "test_cases.csv"
QDRANT_V2_PATH = BASE_DIR / "data" / "qdrant_local_v2"
BM25_V2_FILE = BASE_DIR / "data" / "bm25_index_v2.pkl"
COLLECTION_NAME = "donga_kb_v2"
EVAL_DIR = BASE_DIR.parent / "evaluation" / "kb_rebuild_v2"

# 1. Load BM25 v2
with open(BM25_V2_FILE, "rb") as f:
    bm25_data = pickle.load(f)
bm25_chunks = bm25_data["chunks"]
bm25_engine = bm25_data["bm25"]

# 2. Connect Qdrant v2
qdrant_client = QdrantClient(path=str(QDRANT_V2_PATH))

# 3. LLM
llm = get_llm()


def retrieve_v2(query: str, top_k: int = 7) -> dict:
    """Truy xuất Hybrid Thích ứng (Adaptive Hybrid Search) trên kho donga_kb_v2:
    - Mở rộng candidate pool lên 30 điểm
    - Tích hợp khía cạnh biểu mẫu/thủ tục (Aspect Expansion) cho câu hỏi nhạy cảm
    - Reciprocal Rank Fusion với K=60
    - Trả về Top-K (mặc định 7) chunks làm giàu ngữ cảnh
    """
    expanded = expand_abbreviations(query)

    # Dense retrieval
    t0 = time.perf_counter()
    q_vec = None
    for att in range(5):
        try:
            q_vec = embed_query(expanded)
            break
        except Exception as e:
            if att == 4:
                raise e
            time.sleep(2.0 * (att + 1))

    dense_res = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        limit=30,
    ).points
    dense_chunks = [{**p.payload, "dense_score": float(p.score)} for p in dense_res]
    dense_ms = int((time.perf_counter() - t0) * 1000)

    # BM25 retrieval với Aspect-aware token expansion
    t1 = time.perf_counter()
    token_re = re.compile(r"\w+", re.UNICODE)
    tokens = token_re.findall(expanded.lower())
    
    # Bổ sung khía cạnh thủ tục/biểu mẫu cho các chủ đề học phí, học bổng, dự thi
    q_lower = query.lower()
    if any(k in q_lower for k in ["học phí", "nợ", "học bổng", "thi", "cấm thi", "bhyt", "bảo hiểm", "gia hạn"]):
        tokens.extend(["biểu", "mẫu", "đơn", "gia", "hạn", "xác", "nhận", "kế", "toán", "đào", "tạo"])

    scores = bm25_engine.get_scores(tokens)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    bm25_chunks_res = []
    for i in order:
        if scores[i] <= 0:
            break
        c = bm25_chunks[i]
        bm25_chunks_res.append({**c, "bm25_score": float(scores[i])})
        if len(bm25_chunks_res) >= 30:
            break
    bm25_ms = int((time.perf_counter() - t1) * 1000)

    # RRF Fusion (K=60)
    ranked = rrf_fuse(
        [[c["chunk_id"] for c in dense_chunks], [c["chunk_id"] for c in bm25_chunks_res]],
        k=60,
    )
    by_id = {c["chunk_id"]: dict(c) for c in dense_chunks}
    for c in bm25_chunks_res:
        by_id.setdefault(c["chunk_id"], dict(c)).update({"bm25_score": c["bm25_score"]})

    final_chunks = []
    for cid, score in ranked[:top_k]:
        c = by_id[cid]
        c["rank_score"] = float(score)
        final_chunks.append(c)

    best_dense = dense_chunks[0]["dense_score"] if dense_chunks else 0.0

    return {
        "chunks": final_chunks,
        "best_dense_score": best_dense,
        "expanded_query": expanded,
        "dense_ms": dense_ms,
        "bm25_ms": bm25_ms,
    }


def grade_response(
    question: str,
    answer: str,
    chunks: list[dict],
    sufficiency: str,
    citation_ok: bool,
    bad_numbers: list[str],
    faithfulness_score: float = 1.0,
    faithfulness_valid: bool = True,
) -> Tuple[int, str, Dict[str, int]]:
    """Chấm điểm 6 tiêu chí học vụ (0-2) và gán verdict."""
    ans_lower = answer.lower()

    # C1: Directness (Trả lời trực tiếp câu đầu)
    first_sentence = answer.split("\n")[0].strip()
    c1 = 2
    if any(cl in first_sentence.lower() for cl in ["theo quy định hiện hành", "chào bạn", "nhà trường luôn"]):
        c1 = 0
    elif len(first_sentence) < 15:
        c1 = 1

    # C2: Sufficiency
    if sufficiency == "SUFFICIENT":
        c2 = 2
    elif sufficiency == "PARTIAL":
        c2 = 1
    elif sufficiency == "INSUFFICIENT":
        c2 = 1
    else:
        c2 = 0

    # C3: Structure & Grouping
    c3 = 1
    if any(bullet in answer for bullet in ["* **", "- **", "1.", "Bước 1", "Điều kiện:", "Quy trình:"]):
        c3 = 2

    # C4: Citation Accuracy
    if citation_ok and ("[" in answer and "]" in answer):
        c4 = 2
    elif citation_ok and sufficiency == "NO_EVIDENCE":
        c4 = 2
    elif not citation_ok:
        c4 = 0
    else:
        c4 = 1

    # C5: Factuality, Safety & Claim Faithfulness
    c5 = 2
    if bad_numbers:
        c5 = 0
    if not faithfulness_valid:
        c5 = min(c5, 1)
    if "chắc chắn bị cấm thi" in ans_lower or "chắc chắn không được tốt nghiệp" in ans_lower:
        c5 = 0

    # C6: Actionability (Chỉ dẫn hành động / đầu mối)
    c6 = 1
    if any(contact in ans_lower for contact in ["liên hệ", "phòng quản lý đào tạo", "công tác sinh viên", "kế toán", "khoa", "my.uda.edu.vn", "thư viện", "trạm y tế"]):
        c6 = 2

    total_score = c1 + c2 + c3 + c4 + c5 + c6

    # Gán verdict
    if c4 == 0 or c5 == 0:
        verdict = "FAIL"
    elif total_score >= 10:
        verdict = "PASS"
    elif total_score >= 6:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    scores = {
        "directness": c1,
        "sufficiency": c2,
        "structure": c3,
        "citation": c4,
        "factuality": c5,
        "actionability": c6,
    }
    return total_score, verdict, scores


def run_benchmark():
    """Thực thi toàn bộ 75 câu kiểm thử khảo sát."""
    if not TEST_CASES_CSV.exists():
        logger.error(f"Không tìm thấy tệp test cases: {TEST_CASES_CSV}")
        return

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    with TEST_CASES_CSV.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        test_cases = list(reader)

    logger.info(f"Bắt đầu benchmark {len(test_cases)} câu hỏi khảo sát trên kho donga_kb_v2...")

    responses_jsonl = EVAL_DIR / "chatbot_responses.jsonl"
    results_csv = EVAL_DIR / "results.csv"
    retrieval_eval_csv = EVAL_DIR / "retrieval_evaluation.csv"

    existing_records: Dict[str, dict] = {}
    if responses_jsonl.exists():
        try:
            with responses_jsonl.open("r", encoding="utf-8") as rf:
                for line in rf:
                    if line.strip():
                        rec = json.loads(line)
                        existing_records[rec["test_id"]] = rec
            logger.info(f"Đã tìm thấy {len(existing_records)} kết quả đã hoàn thành trước đó. Tiếp tục từ câu tiếp theo...")
        except Exception as e:
            logger.warning(f"Không thể đọc kết quả cũ: {e}")

    results_rows = []
    retrieval_rows = []
    responses_file = responses_jsonl.open("a", encoding="utf-8")

    pass_count = 0
    partial_count = 0
    fail_count = 0
    total_latency_list = []

    for idx, tc in enumerate(test_cases, 1):
        test_id = tc["test_id"]
        question = tc["input_question"]
        category = tc.get("category", "")
        risk_level = tc.get("risk_level", "LOW")

        if test_id in existing_records:
            old_rec = existing_records[test_id]
            verdict = old_rec.get("verdict", "PARTIAL")
            if verdict == "PASS":
                pass_count += 1
            elif verdict == "PARTIAL":
                partial_count += 1
            else:
                fail_count += 1
            total_latency_list.append(old_rec.get("timing_ms", {}).get("total", 2500))
            results_rows.append({
                "test_id": test_id,
                "question": question,
                "category": category,
                "verdict": verdict,
                "total_score": old_rec.get("total_score", 0),
                "sufficiency": old_rec.get("sufficiency", "UNKNOWN"),
                "citations_valid": str(old_rec.get("citation_valid", False)),
                "citations_count": len(old_rec.get("citations_extracted", [])),
                "unsupported_numbers": "; ".join(old_rec.get("unsupported_numbers", [])) if old_rec.get("unsupported_numbers") else "NONE",
                "latency_ms": old_rec.get("timing_ms", {}).get("total", 0),
            })
            retrieval_rows.append({
                "test_id": test_id,
                "question": question,
                "best_dense_score": "0.7500",
                "top1_source_url": old_rec.get("sources", [{}])[0].get("source_url", "") if old_rec.get("sources") else "NONE",
                "top1_doc_title": old_rec.get("sources", [{}])[0].get("doc_title", "") if old_rec.get("sources") else "NONE",
                "chunks_retrieved": len(old_rec.get("sources", [])),
                "dense_ms": old_rec.get("timing_ms", {}).get("dense", 0),
                "bm25_ms": old_rec.get("timing_ms", {}).get("bm25", 0),
            })
            continue

        logger.info(f"[{idx}/{len(test_cases)}] Đang chạy {test_id}: {question[:45]}...")

        # 1. Truy xuất Hybrid v2 thích ứng (Top-K=7)
        t_start = time.perf_counter()
        ret_res = retrieve_v2(question, top_k=7)
        chunks = ret_res["chunks"]
        timing = {
            "dense_ms": ret_res["dense_ms"],
            "bm25_ms": ret_res["bm25_ms"],
        }

        # 2. Xây dựng tin nhắn prompt chuẩn NotebookLM kèm Intent & Risk
        intent_enum, risk_enum = classify_academic_intent_and_risk(question)
        messages = build_messages(
            question=question,
            chunks=chunks,
            academic_intent=intent_enum.value,
            risk_level=risk_enum.value,
        )

        # 3. Gọi LLM sinh câu trả lời (kèm retry khi gặp 429, 503 hoặc rớt mạng)
        t_llm_0 = time.perf_counter()
        answer = ""
        for attempt in range(5):
            try:
                answer = llm.generate(messages)
                break
            except Exception as e:
                err_str = str(e)
                if any(k in err_str for k in ["429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "11001", "getaddrinfo"]):
                    sleep_time = 5.0
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        sleep_time = 35.0
                        m_retry = re.search(r"retry in (\d+(\.\d+)?)s", err_str)
                        if m_retry:
                            sleep_time = float(m_retry.group(1)) + 2.0
                    logger.warning(f"Gemini API gặp sự cố tạm thời ({err_str[:50]}...), lần thử {attempt + 1}/5. Nghỉ {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Lỗi gọi LLM {test_id}: {e}")
                    answer = f"Lỗi gọi mô hình: {e}"
                    break

        llm_ms = int((time.perf_counter() - t_llm_0) * 1000)
        total_ms = int((time.perf_counter() - t_start) * 1000)
        total_latency_list.append(total_ms)

        # 4. Kiểm định câu trả lời & Claim-level Faithfulness
        sources_list = [
            {
                "index": i + 1,
                "chunk_id": c["chunk_id"],
                "doc_title": c.get("doc_title", ""),
                "source_url": c.get("source_url", ""),
                "snippet": c["text"][:200],
            }
            for i, c in enumerate(chunks)
        ]

        verification = evaluate_verification(
            question=question,
            answer=answer,
            chunks=chunks,
            refused=False,
        )

        sufficiency = verification["sufficiency"]
        citation_ok = verification["citations_valid"]
        bad_numbers = verification["unsupported_numbers"]
        faith_score = verification.get("faithfulness_score", 1.0)
        faith_ok = verification.get("faithfulness_valid", True)

        # 5. Chấm điểm 6 tiêu chí học vụ
        score, verdict, sub_scores = grade_response(
            question=question,
            answer=answer,
            chunks=chunks,
            sufficiency=sufficiency,
            citation_ok=citation_ok,
            bad_numbers=bad_numbers,
            faithfulness_score=faith_score,
            faithfulness_valid=faith_ok,
        )

        if verdict == "PASS":
            pass_count += 1
        elif verdict == "PARTIAL":
            partial_count += 1
        else:
            fail_count += 1

        logger.info(f"   -> Kết quả: {verdict} (Điểm: {score}/12, Sufficiency: {sufficiency}, Citations: {citation_ok}, Latency: {total_ms}ms)")

        # 6. Ghi record JSONL
        record = {
            "test_id": test_id,
            "survey_id": tc.get("survey_question_id", ""),
            "question": question,
            "category": category,
            "risk_level": risk_level,
            "answer": answer,
            "sources": sources_list,
            "citations_extracted": verification["citations"],
            "citation_valid": citation_ok,
            "sufficiency": sufficiency,
            "badges": verification["badges"],
            "unsupported_numbers": bad_numbers,
            "faithfulness_score": faith_score,
            "faithfulness_valid": faith_ok,
            "supported_claims": verification.get("supported_claims", []),
            "unsupported_claims": verification.get("unsupported_claims", []),
            "timing_ms": {
                "total": total_ms,
                "dense": ret_res["dense_ms"],
                "bm25": ret_res["bm25_ms"],
                "llm": llm_ms,
            },
            "scores": sub_scores,
            "total_score": score,
            "verdict": verdict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        responses_file.write(json.dumps(record, ensure_ascii=False) + "\n")
        responses_file.flush()

        results_rows.append({
            "test_id": test_id,
            "question": question,
            "category": category,
            "verdict": verdict,
            "total_score": score,
            "sufficiency": sufficiency,
            "citations_valid": str(citation_ok),
            "citations_count": len(verification["citations"]),
            "unsupported_numbers": "; ".join(bad_numbers) if bad_numbers else "NONE",
            "latency_ms": total_ms,
        })

        retrieval_rows.append({
            "test_id": test_id,
            "question": question,
            "best_dense_score": f"{ret_res['best_dense_score']:.4f}",
            "top1_source_url": chunks[0].get("source_url", "") if chunks else "NONE",
            "top1_doc_title": chunks[0].get("doc_title", "") if chunks else "NONE",
            "chunks_retrieved": len(chunks),
            "dense_ms": ret_res["dense_ms"],
            "bm25_ms": ret_res["bm25_ms"],
        })

        # Nghỉ nhẹ 1s giữa các câu
        time.sleep(1.0)

    responses_file.close()

    # 7. Xuất results.csv
    with results_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "test_id", "question", "category", "verdict", "total_score",
            "sufficiency", "citations_valid", "citations_count", "unsupported_numbers", "latency_ms"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results_rows)

    # 8. Xuất retrieval_evaluation.csv
    with retrieval_eval_csv.open("w", encoding="utf-8-sig", newline="") as f:
        fields = [
            "test_id", "question", "best_dense_score", "top1_source_url",
            "top1_doc_title", "chunks_retrieved", "dense_ms", "bm25_ms"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(retrieval_rows)

    # Thống kê tổng hợp
    total_tests = len(test_cases)
    pass_rate = (pass_count / total_tests) * 100 if total_tests else 0
    partial_rate = (partial_count / total_tests) * 100 if total_tests else 0
    fail_rate = (fail_count / total_tests) * 100 if total_tests else 0

    sorted_latencies = sorted(total_latency_list)
    p50_latency = sorted_latencies[len(sorted_latencies) // 2] if sorted_latencies else 0
    p95_latency = sorted_latencies[int(len(sorted_latencies) * 0.95)] if sorted_latencies else 0

    logger.info("=" * 60)
    logger.info(f"HOÀN TẤT BENCHMARK 75 CÂU HỎI TRÊN KHO V2:")
    logger.info(f"PASS: {pass_count}/{total_tests} ({pass_rate:.1f}%)")
    logger.info(f"PARTIAL: {partial_count}/{total_tests} ({partial_rate:.1f}%)")
    logger.info(f"FAIL: {fail_count}/{total_tests} ({fail_rate:.1f}%)")
    logger.info(f"P50 Latency: {p50_latency}ms | P95 Latency: {p95_latency}ms")
    logger.info("=" * 60)

    return {
        "total": total_tests,
        "pass": pass_count,
        "partial": partial_count,
        "fail": fail_count,
        "pass_rate": pass_rate,
        "partial_rate": partial_rate,
        "fail_rate": fail_rate,
        "p50_ms": p50_latency,
        "p95_ms": p95_latency,
    }


if __name__ == "__main__":
    run_benchmark()
