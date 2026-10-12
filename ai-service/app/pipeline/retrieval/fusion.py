"""Reciprocal Rank Fusion (RRF): trộn nhiều danh sách xếp hạng chỉ dựa vào THỨ HẠNG
(không cần chuẩn hóa điểm của vector và BM25 vốn khác thang đo)."""
from __future__ import annotations


def rrf_fuse(rank_lists: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for lst in rank_lists:
        for rank, cid in enumerate(lst, start=1):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
