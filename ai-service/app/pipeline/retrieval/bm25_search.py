from __future__ import annotations
import re
from rank_bm25 import BM25Okapi
from app.pipeline.retrieval import chunk_store

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    # Mức đơn giản: chữ thường + tách từ. Nâng cấp: tách từ tiếng Việt (underthesea/pyvi).
    return _TOKEN_RE.findall(text.lower())


class BM25Index:
    def __init__(self) -> None:
        self.chunks: list[dict] = []
        self.bm25: BM25Okapi | None = None

    def rebuild(self) -> None:
        self.chunks = chunk_store.load_all()
        corpus = [tokenize(c["text"]) for c in self.chunks]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, top_k: int, only_active: bool = True) -> list[dict]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        out: list[dict] = []
        for i in order:
            if scores[i] <= 0:
                break
            c = self.chunks[i]
            if only_active and c.get("status") != "ACTIVE":
                continue
            out.append({**c, "bm25_score": float(scores[i])})
            if len(out) >= top_k:
                break
        return out


bm25_index = BM25Index()
