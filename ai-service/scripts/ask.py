"""Hỏi thử từ dòng lệnh, in ra cả bằng chứng truy xuất.
python -m scripts.ask "Nợ học phí có đăng ký môn được không?" [--mode dense|bm25|hybrid]"""
import argparse
from app.pipeline import rag_pipeline
from app.pipeline.retrieval.bm25_search import bm25_index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--mode", default="hybrid", choices=["dense", "bm25", "hybrid"])
    a = ap.parse_args()
    bm25_index.rebuild()
    r = rag_pipeline.answer(a.question, mode=a.mode)
    print("HỎI     :", a.question)
    print("TRẢ LỜI :", r["answer"])
    print("TỪ CHỐI :", r["refused"], r["refuse_reason"])
    print("SỐ LẠ   :", r["unsupported_numbers"] or "không")
    print(f"ĐIỂM VECTOR CAO NHẤT: {r['best_dense_score']}   |   truy xuất {r['retrieval_ms']} ms   |   tổng {r['latency_ms']} ms")
    for s in r["sources"]:
        print(f"  [{s['index']}] {s['doc_name']} | {s['chuong']} | {s['dieu']} | điểm {s['score']:.3f}")


if __name__ == "__main__":
    main()
