"""Chuyển token từ LLM thành các sự kiện SSE để Spring Boot / trình duyệt đọc."""
from __future__ import annotations
import json
from typing import Iterator

from app.core.prompts import (
    REFUSE_MESSAGE,
    PERSONAL_REPLY,
    OUT_OF_SCOPE_REPLY,
    AMBIGUOUS_REPLY,
)
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import unsupported_numbers
from app.pipeline.query_transformation.intent_classifier import Intent
from app.pipeline.rag_pipeline import Prepared


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_answer(p: Prepared) -> Iterator[str]:
    try:
        if p.refused:
            if p.refuse_reason == Intent.PERSONAL.value:
                reply_text = PERSONAL_REPLY
            elif p.refuse_reason == Intent.OUT_OF_SCOPE.value:
                reply_text = OUT_OF_SCOPE_REPLY
            elif p.refuse_reason == Intent.AMBIGUOUS.value:
                reply_text = AMBIGUOUS_REPLY
            else:
                reply_text = REFUSE_MESSAGE
            yield sse("token", {"text": reply_text})
            yield sse("done", {
                "refused": True,
                "refuse_reason": p.refuse_reason,
                "timing": p.timing,
                "intent": p.extra.get("intent", p.refuse_reason),
            })
            return

        full = []
        for tok in get_llm().stream(p.messages):
            full.append(tok)
            yield sse("token", {"text": tok})
        text = "".join(full)
        refused = text.strip().startswith(REFUSE_MESSAGE[:40])
        yield sse("sources", {"sources": [] if refused else p.sources})
        if not refused:
            bad = unsupported_numbers(text, [c["text"] for c in p.chunks])
            yield sse("verify", {"unsupported_numbers": bad})
        yield sse("done", {
            "refused": refused,
            "refuse_reason": "llm_refused" if refused else "",
            "timing": p.timing,
            "intent": p.extra.get("intent", Intent.ACADEMIC.value),
        })
    except Exception as e:  # đừng làm sập kết nối SSE
        yield sse("error", {"message": f"{type(e).__name__}: {e}"})
