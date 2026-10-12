from __future__ import annotations
from app.core.config import settings
from app.pipeline.query_transformation.abbreviation_mapper import expand_abbreviations
from app.pipeline.retrieval.bm25_search import bm25_index
from app.pipeline.retrieval.dense_search import dense_search
from app.pipeline.retrieval.fusion import rrf_fuse


def retrieve(query: str, mode: str = "hybrid", top_k: int | None = None) -> dict:
    """mode: dense | bm25 | hybrid. Trả về các chunk + điểm vector cao nhất (để tính ngưỡng từ chối)."""
    top_k = top_k or settings.top_k
    expanded = expand_abbreviations(query)

    dense = dense_search(expanded, settings.candidate_k)           # luôn tính để lấy best_dense_score
    bm25 = bm25_index.search(expanded, settings.candidate_k) if mode in ("bm25", "hybrid") else []
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
    return {"chunks": chunks, "best_dense_score": best_dense, "expanded_query": expanded}
