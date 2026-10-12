"""Bộ điều phối: câu hỏi -> truy xuất -> (từ chối?) -> prompt -> LLM -> kiểm chứng."""
from __future__ import annotations
import time
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.prompts import REFUSE_MESSAGE, build_messages
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import unsupported_numbers
from app.pipeline.retrieval.hybrid_retriever import retrieve


@dataclass
class Prepared:
    question: str
    refused: bool
    refuse_reason: str
    messages: list[dict]
    chunks: list[dict]
    sources: list[dict]
    best_dense_score: float | None
    retrieval_ms: int
    extra: dict = field(default_factory=dict)


def _sources(chunks: list[dict]) -> list[dict]:
    return [{
        "index": i, "chunk_id": c["chunk_id"], "doc_name": c["doc_name"],
        "chuong": c.get("chuong", ""), "dieu": c.get("dieu", ""),
        "score": c.get("dense_score", c.get("rank_score", 0.0)),
        "snippet": c["text"][:240],
    } for i, c in enumerate(chunks, 1)]


def prepare(question: str, history: list[dict] | None = None,
            mode: str = "hybrid", top_k: int | None = None) -> Prepared:
    t0 = time.perf_counter()
    res = retrieve(question, mode, top_k)
    ms = int((time.perf_counter() - t0) * 1000)
    chunks = res["chunks"][: settings.max_context_chunks]
    best = res["best_dense_score"]

    refused, reason = False, ""
    if not chunks:
        refused, reason = True, "no_chunks"
    elif settings.min_dense_score > 0 and (best is None or best < settings.min_dense_score):
        refused, reason = True, "low_score"

    hist = (history or [])[-settings.history_turns:]
    messages = [] if refused else build_messages(question, chunks, hist)
    return Prepared(question, refused, reason, messages, chunks, _sources(chunks), best, ms,
                    {"expanded_query": res["expanded_query"]})


def answer(question: str, history: list[dict] | None = None,
           mode: str = "hybrid", top_k: int | None = None) -> dict:
    t0 = time.perf_counter()
    p = prepare(question, history, mode, top_k)
    if p.refused:
        text = REFUSE_MESSAGE
    else:
        text = get_llm().generate(p.messages)
    # Câu trả lời chính là câu từ chối mà LLM tự quyết định -> cũng coi là từ chối
    refused = p.refused or text.strip().startswith(REFUSE_MESSAGE[:40])
    warnings = [] if refused else unsupported_numbers(text, [c["text"] for c in p.chunks])
    return {
        "answer": text, "refused": refused,
        "refuse_reason": p.refuse_reason or ("llm_refused" if refused else ""),
        "sources": [] if refused else p.sources,
        "unsupported_numbers": warnings,
        "best_dense_score": p.best_dense_score,
        "retrieval_ms": p.retrieval_ms,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }
