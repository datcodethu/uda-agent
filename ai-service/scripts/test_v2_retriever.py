"""Kiểm thử truy xuất v2 độc lập trên collection donga_kb_v2 và bm25_index_v2.pkl"""
from __future__ import annotations
import pickle
import sys
import time
from pathlib import Path
from qdrant_client import QdrantClient

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.pipeline.retrieval.dense_search import embed_query
from app.pipeline.retrieval.fusion import rrf_fuse
from app.pipeline.query_transformation.abbreviation_mapper import expand_abbreviations

QDRANT_V2_PATH = BASE_DIR / "data" / "qdrant_local_v2"
BM25_V2_FILE = BASE_DIR / "data" / "bm25_index_v2.pkl"
COLLECTION_NAME = "donga_kb_v2"

# 1. Load BM25 v2
with open(BM25_V2_FILE, "rb") as f:
    bm25_data = pickle.load(f)
bm25_chunks = bm25_data["chunks"]
bm25_engine = bm25_data["bm25"]

# 2. Connect Qdrant v2
client = QdrantClient(path=str(QDRANT_V2_PATH))


def retrieve_v2(query: str, top_k: int = 5) -> dict:
    expanded = expand_abbreviations(query)

    # Dense
    t0 = time.perf_counter()
    q_vec = embed_query(expanded)
    dense_res = client.query_points(
        collection_name=COLLECTION_NAME,
        query=q_vec,
        limit=20,
    ).points
    dense_chunks = [
        {**p.payload, "dense_score": float(p.score)}
        for p in dense_res
    ]
    dense_ms = int((time.perf_counter() - t0) * 1000)

    # BM25
    t1 = time.perf_counter()
    import re
    token_re = re.compile(r"\w+", re.UNICODE)
    tokens = token_re.findall(expanded.lower())
    scores = bm25_engine.get_scores(tokens)
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    bm25_chunks_res = []
    for i in order:
        if scores[i] <= 0:
            break
        c = bm25_chunks[i]
        bm25_chunks_res.append({**c, "bm25_score": float(scores[i])})
        if len(bm25_chunks_res) >= 20:
            break
    bm25_ms = int((time.perf_counter() - t1) * 1000)

    # RRF Fusion (K=50)
    ranked = rrf_fuse(
        [[c["chunk_id"] for c in dense_chunks], [c["chunk_id"] for c in bm25_chunks_res]],
        k=50,
    )
    by_id = {c["chunk_id"]: dict(c) for c in dense_chunks}
    for c in bm25_chunks_res:
        by_id.setdefault(c["chunk_id"], dict(c)).update({"bm25_score": c["bm25_score"]})

    final_chunks = []
    for cid, score in ranked[:top_k]:
        c = by_id[cid]
        c["rank_score"] = float(score)
        final_chunks.append(c)

    return {
        "query": query,
        "expanded_query": expanded,
        "dense_ms": dense_ms,
        "bm25_ms": bm25_ms,
        "chunks": final_chunks,
    }


if __name__ == "__main__":
    test_queries = [
        "Sinh viên mượn sách thư viện được tối đa mấy cuốn và trong bao lâu?",
        "Quy định đỗ xe và bấm lỗ thẻ xe sinh viên như thế nào?",
        "Cách đăng nhập vào phần mềm học online Canvas?",
        "Chuẩn đầu ra ngoại ngữ tiếng Anh đối với khóa 2024?",
        "Sinh viên bị nợ học phí thì có được thi tốt nghiệp không?",
    ]
    for q in test_queries:
        print("=" * 60)
        res = retrieve_v2(q, top_k=3)
        print(f"Query: {res['query']}")
        print(f"Timing: Dense {res['dense_ms']}ms | BM25 {res['bm25_ms']}ms")
        for i, c in enumerate(res["chunks"], 1):
            print(f"  [{i}] {c['chunk_id']} | {c.get('doc_title', '')[:30]} | {c.get('source_url', '')}")
            print(f"      Snippet: {c['text'][:120]}...")
