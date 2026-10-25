"""Bộ điều phối: câu hỏi -> truy xuất -> (từ chối?) -> prompt -> LLM -> kiểm chứng."""
from __future__ import annotations
import time
from dataclasses import dataclass, field

from app.core.config import settings
from app.core.prompts import (
    REFUSE_MESSAGE,
    PERSONAL_REPLY,
    OUT_OF_SCOPE_REPLY,
    AMBIGUOUS_REPLY,
    build_messages,
)
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import unsupported_numbers
from app.pipeline.query_transformation.intent_classifier import Intent, classify
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
    timing: dict = field(default_factory=dict)


def _sources(chunks: list[dict]) -> list[dict]:
    res = []
    for i, c in enumerate(chunks, 1):
        item = {
            "index": i,
            "chunk_id": c["chunk_id"],
            "doc_name": c["doc_name"],
            "chuong": c.get("chuong", ""),
            "dieu": c.get("dieu", ""),
            "score": c.get("dense_score", c.get("rank_score", 0.0)),
            "snippet": c["text"][:240],
        }
        if c.get("effective_date"):
            item["effective_date"] = c["effective_date"]
        if c.get("doc_number"):
            item["doc_number"] = c["doc_number"]
        res.append(item)
    return res


def prepare(question: str, history: list[dict] | None = None,
            mode: str = "hybrid", top_k: int | None = None) -> Prepared:
    t0 = time.perf_counter()

    # 1. Phân loại ý định trước khi tìm kiếm (Fast-path guardrail)
    intent = classify(question)
    if intent != Intent.ACADEMIC:
        ms = int((time.perf_counter() - t0) * 1000)
        reason = intent.value
        timing = {
            "embedding_ms": 0,
            "qdrant_ms": 0,
            "bm25_ms": 0,
            "retrieval_ms": ms,
            "llm_ms": 0,
            "total_ms": ms,
        }
        return Prepared(
            question=question,
            refused=True,
            refuse_reason=reason,
            messages=[],
            chunks=[],
            sources=[],
            best_dense_score=None,
            retrieval_ms=ms,
            extra={"expanded_query": question, "intent": reason},
            timing=timing,
        )

    # 2. Truy xuất tài liệu cho câu hỏi học vụ
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

    timing = dict(res.get("timing", {}))
    timing["retrieval_ms"] = ms
    timing["llm_ms"] = 0
    timing["total_ms"] = ms

    return Prepared(
        question, refused, reason, messages, chunks, _sources(chunks), best, ms,
        {"expanded_query": res["expanded_query"], "intent": Intent.ACADEMIC.value},
        timing=timing,
    )


def answer(question: str, history: list[dict] | None = None,
           mode: str = "hybrid", top_k: int | None = None) -> dict:
    t0 = time.perf_counter()
    p = prepare(question, history, mode, top_k)
    t_llm_0 = time.perf_counter()
    if p.refused:
        if p.refuse_reason == Intent.PERSONAL.value:
            text = PERSONAL_REPLY
        elif p.refuse_reason == Intent.OUT_OF_SCOPE.value:
            text = OUT_OF_SCOPE_REPLY
        elif p.refuse_reason == Intent.AMBIGUOUS.value:
            text = AMBIGUOUS_REPLY
        else:
            text = REFUSE_MESSAGE
        llm_ms = 0
    else:
        text = get_llm().generate(p.messages)
        llm_ms = int((time.perf_counter() - t_llm_0) * 1000)

    total_ms = int((time.perf_counter() - t0) * 1000)
    timing = dict(p.timing)
    timing["llm_ms"] = llm_ms
    timing["total_ms"] = total_ms

    # Câu trả lời chính là câu từ chối mà LLM tự quyết định -> cũng coi là từ chối
    refused = p.refused or text.strip().startswith(REFUSE_MESSAGE[:40])
    warnings = [] if refused else unsupported_numbers(text, [c["text"] for c in p.chunks])
    return {
        "answer": text,
        "refused": refused,
        "refuse_reason": p.refuse_reason or ("llm_refused" if refused else ""),
        "sources": [] if refused else p.sources,
        "unsupported_numbers": warnings,
        "best_dense_score": p.best_dense_score,
        "retrieval_ms": p.retrieval_ms,
        "latency_ms": total_ms,
        "timing": timing,
        "intent": p.extra.get("intent", Intent.ACADEMIC.value),
    }
