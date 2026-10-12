"""Đánh giá truy xuất (miễn phí, không gọi LLM) và tuỳ chọn cả câu trả lời.

  python -m evaluation.run_eval --mode hybrid --top-k 5
  python -m evaluation.run_eval --mode dense  --top-k 5     # so sánh các cấu hình
  python -m evaluation.run_eval --mode hybrid --with-llm    # thêm chấm câu trả lời + xuất file cho RAGAS

Chỉ số:
  hit@k      : tỉ lệ câu có ít nhất 1 chunk đúng Điều trong top-k
  MRR        : trung bình 1/hạng của chunk đúng đầu tiên
  điểm vector: phân bố điểm cao nhất của câu trả lời được vs câu ngoài phạm vi -> chọn MIN_DENSE_SCORE
"""
from __future__ import annotations
import argparse
import json
import statistics as st
import time
from datetime import datetime
from pathlib import Path

from app.core.config import BASE_DIR
from app.pipeline import rag_pipeline
from app.pipeline.retrieval.bm25_search import bm25_index

DS = BASE_DIR / "evaluation" / "test_datasets"
OUT = BASE_DIR / "evaluation" / "benchmarks_result"


def _load(name: str) -> list[dict]:
    p = DS / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return round(st.mean(xs), 4) if xs else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="hybrid", choices=["dense", "bm25", "hybrid"])
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--with-llm", action="store_true")
    a = ap.parse_args()

    bm25_index.rebuild()
    answerable, adversarial = _load("academic_regulations.json"), _load("adversarial_test.json")
    rows, hits, rr = [], [], []
    best_ok, best_oos = [], []

    for q in answerable:
        t0 = time.perf_counter()
        p = rag_pipeline.prepare(q["question"], None, a.mode, a.top_k)
        row = {"id": q["id"], "type": q["type"], "question": q["question"],
               "best_dense_score": p.best_dense_score,
               "retrieved": [(s["dieu"], round(s["score"], 3)) for s in p.sources],
               "retrieval_ms": p.retrieval_ms}
        found_rank = next((i for i, c in enumerate(p.chunks, 1) if c.get("dieu") in q["expected_dieu"]), None)
        hits.append(found_rank is not None)
        rr.append(1 / found_rank if found_rank else 0.0)
        best_ok.append(p.best_dense_score)
        row["hit"], row["rank"] = found_rank is not None, found_rank
        if a.with_llm:
            r = rag_pipeline.answer(q["question"], None, a.mode, a.top_k)
            row.update(answer=r["answer"], refused=r["refused"], unsupported_numbers=r["unsupported_numbers"],
                       contexts=[c["text"] for c in p.chunks], ground_truth=q.get("ground_truth", ""),
                       contains_ok=all(m in r["answer"] for m in q.get("must_contain", [])),
                       latency_ms=r["latency_ms"])
        rows.append(row)

    adv_rows = []
    for q in adversarial:
        p = rag_pipeline.prepare(q["question"], None, a.mode, a.top_k)
        row = {"id": q["id"], "type": q["type"], "question": q["question"], "best_dense_score": p.best_dense_score}
        if q["type"] in ("out_of_scope", "near_scope"):
            best_oos.append(p.best_dense_score)
        if a.with_llm:
            r = rag_pipeline.answer(q["question"], None, a.mode, a.top_k)
            row.update(answer=r["answer"], refused=r["refused"], expected_refuse=q["expected_refuse"],
                       refuse_correct=(r["refused"] == q["expected_refuse"]),
                       leaked=any(m.lower() in r["answer"].lower() for m in q.get("must_not_contain", [])))
        adv_rows.append(row)

    summary = {
        "mode": a.mode, "top_k": a.top_k, "n_answerable": len(answerable),
        "hit@k": round(sum(hits) / len(hits), 4) if hits else None,
        "MRR": round(st.mean(rr), 4) if rr else None,
        "avg_best_score_answerable": _mean(best_ok),
        "avg_best_score_out_of_scope": _mean(best_oos),
        "avg_retrieval_ms": _mean([r["retrieval_ms"] for r in rows]),
    }
    if a.with_llm:
        summary["answer_contains_expected"] = _mean([1.0 if r["contains_ok"] else 0.0 for r in rows])
        summary["answers_with_unsupported_numbers"] = sum(1 for r in rows if r["unsupported_numbers"])
        summary["refusal_correct"] = _mean([1.0 if r["refuse_correct"] else 0.0 for r in adv_rows])

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / f"{datetime.now():%Y%m%d_%H%M%S}_{a.mode}_k{a.top_k}{'_llm' if a.with_llm else ''}.json"
    f.write_text(json.dumps({"summary": summary, "answerable": rows, "adversarial": adv_rows},
                            ensure_ascii=False, indent=2), encoding="utf-8")
    print("Đã lưu:", f)


if __name__ == "__main__":
    main()
