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
    CLARIFY_NO_CONTEXT_REPLY,
    build_messages,
)
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import evaluate_verification, unsupported_numbers
from app.pipeline.memory.session_memory import session_memory
from app.pipeline.query_transformation.context_resolver import resolve_context
from app.pipeline.query_transformation.intent_classifier import (
    Intent,
    classify,
    classify_academic_intent_and_risk,
)
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


def prepare(
    question: str,
    history: list[dict] | None = None,
    conversation_id: str | None = None,
    mode: str = "hybrid",
    top_k: int | None = None,
    use_intent: bool = True,
) -> Prepared:
    t0 = time.perf_counter()

    # 1. Đồng bộ và xác định ngữ cảnh hội thoại
    session = session_memory.get_session(conversation_id) if conversation_id else None
    effective_history = history if (history is not None and len(history) > 0) else (session.history if session else [])
    last_topic = session.last_topic if session else ""

    # 2. Phân giải ngữ cảnh (Context Resolution)
    res_ctx = resolve_context(question, effective_history, last_topic=last_topic)

    # 2a. Trường hợp hỏi làm rõ khi hoàn toàn chưa có ngữ cảnh
    if res_ctx.action == "CLARIFY_NO_CONTEXT":
        ms = int((time.perf_counter() - t0) * 1000)
        return Prepared(
            question=question,
            refused=True,
            refuse_reason="clarify_no_context",
            messages=[],
            chunks=[],
            sources=[],
            best_dense_score=None,
            retrieval_ms=ms,
            extra={
                "expanded_query": question,
                "intent": "clarify_no_context",
                "conversation_id": conversation_id,
            },
            timing={"retrieval_ms": ms, "llm_ms": 0, "total_ms": ms},
        )

    # 2b. Phân loại ý định trước khi tìm kiếm (Fast-path guardrail) chỉ với chủ đề mới
    if use_intent and res_ctx.action == "NEW_TOPIC":
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
                extra={
                    "expanded_query": question,
                    "intent": reason,
                    "conversation_id": conversation_id,
                },
                timing=timing,
            )

    # 3. Xử lý truy xuất tài liệu hoặc tái sử dụng bằng chứng
    chunks = []
    best_dense = None
    expanded_query = res_ctx.standalone_query
    timing = {}
    reused_cache = False

    # Trường hợp REEXPLAIN hoặc EXAMPLE: Kiểm tra và tái sử dụng chunks cũ
    if res_ctx.action in ("REEXPLAIN", "EXAMPLE"):
        cached_chunks = session.last_chunks if session else []
        is_valid, valid_chunks = session_memory.validate_cached_sources(cached_chunks)
        if is_valid and valid_chunks:
            chunks = valid_chunks[: settings.max_context_chunks]
            best_dense = chunks[0].get("dense_score", chunks[0].get("rank_score", 1.0))
            ms = int((time.perf_counter() - t0) * 1000)
            reused_cache = True
            timing = {
                "embedding_ms": 0,
                "qdrant_ms": 0,
                "bm25_ms": 0,
                "retrieval_ms": 0,
                "llm_ms": 0,
                "total_ms": ms,
            }

    # Nếu chưa có chunks (hoặc là NEW_TOPIC / REWRITE_AND_RETRIEVE / cache invalid):
    if not chunks:
        query_to_retrieve = res_ctx.standalone_query if res_ctx.action == "REWRITE_AND_RETRIEVE" else question
        res = retrieve(query_to_retrieve, mode, top_k)
        ms = int((time.perf_counter() - t0) * 1000)
        chunks = res["chunks"][: settings.max_context_chunks]
        best_dense = res["best_dense_score"]
        expanded_query = res["expanded_query"]
        timing = dict(res.get("timing", {}))
        timing["retrieval_ms"] = ms
        timing["total_ms"] = ms

    refused, reason = False, ""
    if not chunks:
        refused, reason = True, "no_chunks"
    elif settings.min_dense_score > 0 and (best_dense is None or best_dense < settings.min_dense_score):
        refused, reason = True, "low_score"

    acad_intent, risk_lvl = classify_academic_intent_and_risk(question)
    hist = effective_history[-settings.history_turns:]
    messages = (
        []
        if refused
        else build_messages(
            question,
            chunks,
            hist,
            context_action=res_ctx.action,
            academic_intent=acad_intent.value,
            risk_level=risk_lvl.value,
        )
    )

    retrieval_ms = 0 if reused_cache else timing.get("retrieval_ms", 0)
    return Prepared(
        question,
        refused,
        reason,
        messages,
        chunks,
        _sources(chunks),
        best_dense,
        retrieval_ms,
        {
            "expanded_query": expanded_query,
            "intent": Intent.ACADEMIC.value,
            "academic_intent": acad_intent.value,
            "risk_level": risk_lvl.value,
            "context_action": res_ctx.action,
            "reused_cache": reused_cache,
            "conversation_id": conversation_id,
        },
        timing=timing,
    )


def answer(
    question: str,
    history: list[dict] | None = None,
    conversation_id: str | None = None,
    mode: str = "hybrid",
    top_k: int | None = None,
    use_intent: bool = True,
) -> dict:
    t0 = time.perf_counter()
    p = prepare(
        question,
        history=history,
        conversation_id=conversation_id,
        mode=mode,
        top_k=top_k,
        use_intent=use_intent,
    )
    t_llm_0 = time.perf_counter()
    if p.refused:
        if p.refuse_reason == Intent.PERSONAL.value:
            text = PERSONAL_REPLY
        elif p.refuse_reason == Intent.OUT_OF_SCOPE.value:
            text = OUT_OF_SCOPE_REPLY
        elif p.refuse_reason == Intent.AMBIGUOUS.value:
            text = AMBIGUOUS_REPLY
        elif p.refuse_reason == "clarify_no_context":
            text = CLARIFY_NO_CONTEXT_REPLY
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
    v_res = evaluate_verification(
        question=question,
        answer=text,
        chunks=p.chunks if not refused else [],
        refused=refused,
        refuse_reason=p.refuse_reason,
    )
    warnings = v_res["unsupported_numbers"]

    # Cập nhật session memory nếu có conversation_id
    if conversation_id:
        session_memory.save_turn(
            conversation_id,
            question,
            text,
            chunks=p.chunks if not refused else [],
            sources=p.sources if not refused else [],
            topic=p.extra.get("expanded_query", question),
        )

    return {
        "answer": text,
        "refused": refused,
        "refuse_reason": p.refuse_reason or ("llm_refused" if refused else ""),
        "conversation_id": conversation_id,
        "standalone_query": p.extra.get("expanded_query", question),
        "sources": [] if refused else p.sources,
        "unsupported_numbers": warnings,
        "sufficiency": v_res["sufficiency"],
        "verification_badges": v_res["badges"],
        "citations": v_res["citations"],
        "invalid_citations": v_res["invalid_citations"],
        "academic_intent": p.extra.get("academic_intent"),
        "risk_level": p.extra.get("risk_level"),
        "claim_warnings": v_res.get("claim_warnings", []),
        "best_dense_score": p.best_dense_score,
        "retrieval_ms": p.retrieval_ms,
        "latency_ms": total_ms,
        "timing": timing,
        "intent": p.extra.get("intent", Intent.ACADEMIC.value),
    }
