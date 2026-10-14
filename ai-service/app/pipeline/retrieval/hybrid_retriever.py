from __future__ import annotations
import time
from app.core.config import settings
from app.pipeline.query_transformation.abbreviation_mapper import expand_abbreviations
from app.pipeline.retrieval.bm25_search import bm25_index
from app.pipeline.retrieval.dense_search import embed_query, dense_search_with_vector
from app.pipeline.retrieval.fusion import rrf_fuse


def retrieve(query: str, mode: str = "hybrid", top_k: int | None = None) -> dict:
    """mode: dense | bm25 | hybrid. Trả về các chunk + điểm vector cao nhất (để tính ngưỡng từ chối)."""
    top_k = top_k or settings.top_k
    expanded = expand_abbreviations(query)

    # 1. Đo thời gian nhúng vector (Gemini Embedding)
    t_emb_0 = time.perf_counter()
    query_vector = embed_query(expanded)
    emb_ms = int((time.perf_counter() - t_emb_0) * 1000)

    # 2. Đo thời gian tìm kiếm vector trong Qdrant
    t_qdrant_0 = time.perf_counter()
    dense = dense_search_with_vector(query_vector, settings.candidate_k)  # luôn tính để lấy best_dense_score
    qdrant_ms = int((time.perf_counter() - t_qdrant_0) * 1000)

    # 3. Đo thời gian tìm kiếm BM25
    t_bm25_0 = time.perf_counter()
    bm25 = bm25_index.search(expanded, settings.candidate_k) if mode in ("bm25", "hybrid") else []
    bm25_ms = int((time.perf_counter() - t_bm25_0) * 1000)

    best_dense = dense[0]["dense_score"] if dense else None

    by_id = {c["chunk_id"]: dict(c) for c in dense}
    for c in bm25:
        by_id.setdefault(c["chunk_id"], dict(c)).update({"bm25_score": c["bm25_score"]})

    if mode == "dense":
        ranked = [(c["chunk_id"], c["dense_score"]) for c in dense]
    elif mode == "bm25":
        ranked = [(c["chunk_id"], c["bm25_score"]) for c in bm25]
    else:
        ranked = rrf_fuse([[c["chunk_id"] for c in dense], [c["chunk_id"] for c in bm25]])

    chunks = []
    for cid, score in ranked[:top_k]:
        c = by_id[cid]
        c["rank_score"] = float(score)
        chunks.append(c)

    timing = {
        "embedding_ms": emb_ms,
        "qdrant_ms": qdrant_ms,
        "bm25_ms": bm25_ms,
    }
    return {
        "chunks": chunks,
        "best_dense_score": best_dense,
        "expanded_query": expanded,
        "timing": timing,
    }
