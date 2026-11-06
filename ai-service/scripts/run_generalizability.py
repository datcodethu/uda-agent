"""Đánh giá tính khái quát hóa (Generalizability Test) trên 5 câu hỏi học vụ mới chưa từng có trong tập huấn luyện/khảo sát.
Kho tri thức: donga_kb_v2
"""
import csv
import json
import os
import sys
import time
from pathlib import Path

# Thêm ai-service vào path
sys.path.insert(0, os.path.abspath(str(Path(__file__).parent.parent)))
sys.stdout.reconfigure(encoding="utf-8")

from scripts.run_v2_benchmark import (
    EVAL_DIR,
    build_messages,
    evaluate_verification,
    get_llm,
    grade_response,
    retrieve_v2,
    classify_academic_intent_and_risk,
)

llm = get_llm()

TEST_QUERIES = [
    {
        "id": "GEN-001",
        "domain": "Tài khoản học tập & LMS Canvas",
        "question": "Cách đăng nhập và đổi mật khẩu tài khoản Canvas sinh viên như thế nào?",
    },
    {
        "id": "GEN-002",
        "domain": "Nội quy thư viện",
        "question": "Sinh viên mượn sách thư viện được tối đa mấy cuốn và trong bao lâu?",
    },
    {
        "id": "GEN-003",
        "domain": "Quy định gửi xe & bãi đỗ xe",
        "question": "Sinh viên gửi xe trong trường nếu vi phạm quy định thì bị xử lý thế nào?",
    },
    {
        "id": "GEN-004",
        "domain": "Học kỳ hè & kế hoạch năm học",
        "question": "Học kỳ hè có bắt buộc đối với tất cả sinh viên không?",
    },
    {
        "id": "GEN-005",
        "domain": "Chuẩn đầu ra ngoại ngữ",
        "question": "Chuẩn đầu ra tiếng Anh đối với sinh viên không chuyên ngữ khóa 2024 yêu cầu chứng chỉ gì?",
    },
]


def main():
    print("=" * 60)
    print("BẮT ĐẦU KIỂM THỬ KHÁI QUÁT HÓA (GENERALIZABILITY TEST - 5 CÂU)")
    print("=" * 60)

    results = []
    for item in TEST_QUERIES:
        q = item["question"]
        t_start = time.perf_counter()
        ret = retrieve_v2(q, top_k=7)
        chunks = ret["chunks"]
        intent_enum, risk_enum = classify_academic_intent_and_risk(q)
        messages = build_messages(
            question=q,
            chunks=chunks,
            academic_intent=intent_enum.value,
            risk_level=risk_enum.value,
        )

        ans = ""
        for att in range(5):
            try:
                ans = llm.generate(messages)
                break
            except Exception as e:
                print(f"Lần thử {att+1} lỗi: {e}")
                time.sleep(4)

        total_ms = int((time.perf_counter() - t_start) * 1000)
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

        rec = {
            "id": item["id"],
            "domain": item["domain"],
            "question": q,
            "answer": ans,
            "sources": [
                {
                    "index": i + 1,
                    "chunk_id": c["chunk_id"],
                    "doc_title": c.get("doc_title", ""),
                    "source_url": c.get("source_url", ""),
                }
                for i, c in enumerate(chunks)
            ],
            "verdict": verdict,
            "total_score": score,
            "sub_scores": sub,
            "sufficiency": v["sufficiency"],
            "citations_valid": v["citations_valid"],
            "unsupported_numbers": v["unsupported_numbers"],
            "latency_ms": total_ms,
        }
        results.append(rec)
        print(f"[{item['id']}] {verdict} | Điểm: {score}/12 | Sufficiency: {v['sufficiency']} | Trích dẫn: {v['citations_valid']} | Latency: {total_ms}ms")
        print(f"   Hỏi: {q}")
        print(f"   Đáp tắt: {ans[:130]}...\n")

    out_file = EVAL_DIR / "generalizability_test.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Hoàn thành! Đã lưu kết quả vào {out_file}")


if __name__ == "__main__":
    main()
