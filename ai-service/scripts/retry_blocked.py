"""Script chạy lại các case bị 503 UNAVAILABLE từ Google API và cập nhật kết quả đánh giá."""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from scripts.run_survey_evaluation import (
    RUN_ID,
    STREAM_URL,
    OUTPUT_DIR_ROOT,
    OUTPUT_DIR_AI,
    evaluate_response,
    execute_live_query,
    generate_report,
    generate_issues,
    save_manifest
)

RESPONSES_FILE = OUTPUT_DIR_ROOT / "responses.jsonl"
TEST_CASES_FILE = OUTPUT_DIR_ROOT / "test_cases.csv"

# Đọc responses hiện có
responses = {}
with open(RESPONSES_FILE, mode="r", encoding="utf-8") as f:
    for line in f:
        d = json.loads(line)
        responses[d["test_id"]] = d

# Đọc test cases
with open(TEST_CASES_FILE, mode="r", encoding="utf-8-sig") as f:
    test_cases = {row["test_id"]: row for row in csv.DictReader(f)}

# Tìm các case bị lỗi Google 503
blocked_tids = [tid for tid, d in responses.items() if d.get("error")]
print(f"Các case bị lỗi 503 tạm thời cần chạy lại: {blocked_tids}")

for tid in blocked_tids:
    tc = test_cases[tid]
    q = tc["input_question"]
    svq_id = tc["survey_question_id"]
    conv_id = f"survey_{RUN_ID}_{svq_id}_{uuid.uuid4().hex[:6]}"
    print(f"Đang chạy lại {tid}: '{q[:50]}...' ", end="", flush=True)
    resp = execute_live_query(q, conv_id)
    
    if resp["error"]:
        print(f"-> Vẫn lỗi: {resp['error'][:80]}")
    else:
        print(f"-> THÀNH CÔNG ({resp['latency_ms']}ms, TTFT: {resp['ttft_ms']}ms)")
        responses[tid] = {
            "test_id": tid,
            "survey_question_id": svq_id,
            "input_question": q,
            "category": tc["category"],
            "risk_level": tc["risk_level"],
            "conversation_id": conv_id,
            "answer": resp["answer"],
            "sources": resp["sources"],
            "verify": resp["verify"],
            "done": resp["done"],
            "error": resp["error"],
            "latency_ms": resp["latency_ms"],
            "ttft_ms": resp["ttft_ms"],
            "retrieval_ms": resp["retrieval_ms"],
        }
    time.sleep(2.0)

# Ghi lại responses.jsonl hoàn chỉnh
for p in (OUTPUT_DIR_ROOT / "responses.jsonl", OUTPUT_DIR_AI / "responses.jsonl"):
    with open(p, mode="w", encoding="utf-8") as f:
        for tid in sorted(responses.keys()):
            f.write(json.dumps(responses[tid], ensure_ascii=False) + "\n")

# Chấm lại điểm toàn bộ 75 case
results = []
latencies = []
ttfts = []

for tid in sorted(responses.keys()):
    tc = test_cases[tid]
    resp = responses[tid]
    eval_res = evaluate_response(tc, resp)
    res_row = {
        "run_id": RUN_ID,
        "test_id": tid,
        "survey_question_id": tc["survey_question_id"],
        "category": tc["category"],
        "risk_level": tc["risk_level"],
        "execution_status": eval_res["execution_status"],
        "verdict": eval_res["verdict"],
        "intent_score": eval_res["intent_score"],
        "completeness_score": eval_res["completeness_score"],
        "faithfulness_score": eval_res["faithfulness_score"],
        "citation_score": eval_res["citation_score"],
        "applicability_score": eval_res["applicability_score"],
        "ux_score": eval_res["ux_score"],
        "latency_ms": resp["latency_ms"],
        "ttft_ms": resp["ttft_ms"],
        "retrieval_ms": resp["retrieval_ms"],
        "sufficiency": eval_res["sufficiency"],
        "source_ids": eval_res["source_ids"],
        "evidence_notes": eval_res["evidence_notes"],
        "problem_summary": eval_res["problem_summary"],
        "recommended_fix": eval_res["recommended_fix"],
        "human_review_status": eval_res["human_review_status"],
    }
    results.append(res_row)
    if resp["latency_ms"] > 0:
        latencies.append(resp["latency_ms"])
    if resp["ttft_ms"] > 0:
        ttfts.append(resp["ttft_ms"])

# Ghi results.csv
results_fields = [
    "run_id", "test_id", "survey_question_id", "category", "risk_level",
    "execution_status", "verdict", "intent_score", "completeness_score",
    "faithfulness_score", "citation_score", "applicability_score", "ux_score",
    "latency_ms", "ttft_ms", "retrieval_ms", "sufficiency", "source_ids",
    "evidence_notes", "problem_summary", "recommended_fix", "human_review_status"
]
for p in (OUTPUT_DIR_ROOT / "results.csv", OUTPUT_DIR_AI / "results.csv"):
    with open(p, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results_fields)
        writer.writeheader()
        writer.writerows(results)

# Thống kê
latencies.sort()
ttfts.sort()
p50_lat = latencies[len(latencies)//2] if latencies else 0
p95_lat = latencies[int(len(latencies)*0.95)] if latencies else 0
p50_ttft = ttfts[len(ttfts)//2] if ttfts else 0
p95_ttft = ttfts[int(len(ttfts)*0.95)] if ttfts else 0

total_count = len(results)
pass_count = sum(1 for r in results if r["verdict"] == "PASS")
fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
partial_count = sum(1 for r in results if r["verdict"] == "PARTIAL")
review_count = sum(1 for r in results if r["verdict"] == "NEEDS_REVIEW")
blocked_count = sum(1 for r in results if r["verdict"] == "BLOCKED")

# Cập nhật manifest
manifest_path = OUTPUT_DIR_ROOT / "run_manifest.json"
manifest = {}
if manifest_path.exists():
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

manifest["timestamp_end"] = datetime.now(timezone.utc).isoformat()
manifest["status"] = "COMPLETED"
manifest["summary"] = {
    "total": total_count,
    "pass": pass_count,
    "fail": fail_count,
    "partial": partial_count,
    "needs_review": review_count,
    "blocked": blocked_count,
    "p50_latency_ms": p50_lat,
    "p95_latency_ms": p95_lat,
    "p50_ttft_ms": p50_ttft,
    "p95_ttft_ms": p95_ttft,
}
save_manifest(OUTPUT_DIR_ROOT / "run_manifest.json", manifest)
save_manifest(OUTPUT_DIR_AI / "run_manifest.json", manifest)

# Sinh report.md & issues.md
generate_report(results, manifest, OUTPUT_DIR_ROOT / "report.md", test_cases)
generate_report(results, manifest, OUTPUT_DIR_AI / "report.md", test_cases)
generate_issues(results, OUTPUT_DIR_ROOT / "issues.md")
generate_issues(results, OUTPUT_DIR_AI / "issues.md")

print(f"\n=== ĐÃ HOÀN TẤT CẬP NHẬT KIỂM THỬ ===")
print(f"PASS: {pass_count} | PARTIAL: {partial_count} | NEEDS_REVIEW: {review_count} | FAIL: {fail_count} | BLOCKED: {blocked_count}")
print(f"P50 Latency: {p50_lat} ms | P95 Latency: {p95_lat} ms | P50 TTFT: {p50_ttft} ms")
