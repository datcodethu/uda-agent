"""Finalize and update benchmark results with the latest verifier and full context checking."""
from __future__ import annotations
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.pipeline.generator.verifier import evaluate_verification
from scripts.run_v2_benchmark import (
    EVAL_DIR,
    TEST_CASES_CSV,
    grade_response,
    retrieve_v2,
    build_messages,
    get_llm,
    classify_academic_intent_and_risk,
)

logger = logging.getLogger("finalize_results")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main():
    responses_jsonl = EVAL_DIR / "chatbot_responses.jsonl"
    results_csv = EVAL_DIR / "results.csv"

    # 1. Load full chunks map
    chunks_file = BASE_DIR / "data" / "chunks_v2.jsonl"
    all_chunks = {}
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                c = json.loads(line)
                all_chunks[c["chunk_id"]] = c

    # 2. Load existing records
    records = []
    with open(responses_jsonl, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    rec_by_id = {r["test_id"]: r for r in records}

    # 3. Handle TC-SVQ-007 if it had an error
    if "TC-SVQ-007" in rec_by_id and "504" in rec_by_id["TC-SVQ-007"].get("answer", ""):
        logger.info("Re-running TC-SVQ-007 due to transient 504 in earlier run...")
        q = "Em đang thắc mắc học cải thiện nhiều thì có hạ bằng giống học lại không"
        ret = retrieve_v2(q, top_k=7)
        intent, risk = classify_academic_intent_and_risk(q)
        msgs = build_messages(q, ret["chunks"], academic_intent=intent.value, risk_level=risk.value)
        llm = get_llm()
        for _ in range(5):
            try:
                ans = llm.generate(msgs)
                if ans and "Lỗi" not in ans[:10]:
                    break
            except Exception as e:
                logger.warning(f"Retry TC-SVQ-007: {e}")
                time.sleep(3)

        rec_by_id["TC-SVQ-007"]["answer"] = ans
        rec_by_id["TC-SVQ-007"]["sources"] = [
            {
                "index": i + 1,
                "chunk_id": c["chunk_id"],
                "doc_title": c.get("doc_title", ""),
                "source_url": c.get("source_url", ""),
                "snippet": c["text"][:200],
            }
            for i, c in enumerate(ret["chunks"])
        ]

    # 4. Re-evaluate all records using full chunk contexts
    updated_records = []
    results_rows = []
    pass_cnt = 0
    partial_cnt = 0
    fail_cnt = 0
    latencies = []

    for r in records:
        tid = r["test_id"]
        rec = rec_by_id[tid]
        q = rec["question"]
        ans = rec["answer"]
        srcs = rec.get("sources", [])

        # Build full chunk objects for verifier
        full_chunks = []
        for s in srcs:
            cid = s.get("chunk_id")
            if cid in all_chunks:
                full_chunks.append(all_chunks[cid])
            else:
                full_chunks.append({"text": s.get("snippet", ""), "chunk_id": cid, "doc_title": s.get("doc_title", "")})

        v = evaluate_verification(
            question=q,
            answer=ans,
            chunks=full_chunks,
            refused=False,
        )

        score, verdict, sub_scores = grade_response(
            question=q,
            answer=ans,
            chunks=full_chunks,
            sufficiency=v["sufficiency"],
            citation_ok=v["citations_valid"],
            bad_numbers=v["unsupported_numbers"],
            faithfulness_score=v.get("faithfulness_score", 1.0),
            faithfulness_valid=v.get("faithfulness_valid", True),
        )

        rec["citations_extracted"] = v["citations"]
        rec["citation_valid"] = v["citations_valid"]
        rec["sufficiency"] = v["sufficiency"]
        rec["badges"] = v["badges"]
        rec["unsupported_numbers"] = v["unsupported_numbers"]
        rec["faithfulness_score"] = v.get("faithfulness_score", 1.0)
        rec["faithfulness_valid"] = v.get("faithfulness_valid", True)
        rec["supported_claims"] = v.get("supported_claims", [])
        rec["unsupported_claims"] = v.get("unsupported_claims", [])
        rec["scores"] = sub_scores
        rec["total_score"] = score
        rec["verdict"] = verdict

        if verdict == "PASS":
            pass_cnt += 1
        elif verdict == "PARTIAL":
            partial_cnt += 1
        else:
            fail_cnt += 1

        tot_ms = rec.get("timing_ms", {}).get("total", 3000)
        latencies.append(tot_ms)

        updated_records.append(rec)
        results_rows.append({
            "test_id": tid,
            "question": q,
            "category": rec.get("category", ""),
            "verdict": verdict,
            "total_score": score,
            "sufficiency": v["sufficiency"],
            "citations_valid": str(v["citations_valid"]),
            "citations_count": len(v["citations"]),
            "unsupported_numbers": "; ".join(v["unsupported_numbers"]) if v["unsupported_numbers"] else "NONE",
            "latency_ms": tot_ms,
        })

    # Save updated jsonl
    with open(responses_jsonl, "w", encoding="utf-8") as f:
        for r in updated_records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Save updated csv
    fields = [
        "test_id", "question", "category", "verdict", "total_score",
        "sufficiency", "citations_valid", "citations_count",
        "unsupported_numbers", "latency_ms"
    ]
    with open(results_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results_rows)

    tot = len(records)
    latencies.sort()
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0

    print("=" * 60)
    print(f"KẾT QUẢ CUỐI CÙNG SAU KHI CẢI TIẾN TRÊN KHO V2 ({tot} CÂU):")
    print(f"PASS   : {pass_cnt}/{tot} ({pass_cnt / tot * 100:.1f}%)")
    print(f"PARTIAL: {partial_cnt}/{tot} ({partial_cnt / tot * 100:.1f}%)")
    print(f"FAIL   : {fail_cnt}/{tot} ({fail_cnt / tot * 100:.1f}%)")
    print(f"P50 Latency: {p50}ms | P95 Latency: {p95}ms")
    print("=" * 60)


if __name__ == "__main__":
    main()
