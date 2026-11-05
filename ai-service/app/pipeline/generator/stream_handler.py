"""Chuyển token từ LLM thành các sự kiện SSE để Spring Boot / trình duyệt đọc."""
from __future__ import annotations
import json
from typing import Iterator

from app.core.prompts import (
    REFUSE_MESSAGE,
    PERSONAL_REPLY,
    OUT_OF_SCOPE_REPLY,
    AMBIGUOUS_REPLY,
    CLARIFY_NO_CONTEXT_REPLY,
)
from app.pipeline.generator.llm_adapter import get_llm
from app.pipeline.generator.verifier import evaluate_verification
from app.pipeline.memory.session_memory import session_memory
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
            elif p.refuse_reason == "clarify_no_context":
                reply_text = CLARIFY_NO_CONTEXT_REPLY
            else:
                reply_text = REFUSE_MESSAGE
            yield sse("token", {"text": reply_text})
            
            v_res = evaluate_verification(
                question=p.question,
                answer=reply_text,
                chunks=[],
                refused=True,
                refuse_reason=p.refuse_reason,
            )
            yield sse("verify", {
                "unsupported_numbers": [],
                "sufficiency": v_res["sufficiency"],
                "badges": v_res["badges"],
                "citations": [],
                "invalid_citations": [],
                "claim_warnings": [],
            })
            yield sse("done", {
                "refused": True,
                "refuse_reason": p.refuse_reason,
                "timing": p.timing,
                "intent": p.extra.get("intent", p.refuse_reason),
                "academic_intent": p.extra.get("academic_intent"),
                "risk_level": p.extra.get("risk_level", "LOW"),
                "claim_warnings": [],
                "sufficiency": v_res["sufficiency"],
                "verification_badges": v_res["badges"],
            })
            cid = p.extra.get("conversation_id")
            if cid:
                session_memory.save_turn(cid, p.question, reply_text, chunks=[], sources=[], topic=p.question)
            return

        full = []
        for tok in get_llm().stream(p.messages):
            full.append(tok)
            yield sse("token", {"text": tok})
        text = "".join(full)
        refused = text.strip().startswith(REFUSE_MESSAGE[:40])
        yield sse("sources", {"sources": [] if refused else p.sources})
        
        v_res = evaluate_verification(
            question=p.question,
            answer=text,
            chunks=p.chunks if not refused else [],
            refused=refused,
            refuse_reason="llm_refused" if refused else "",
        )
        yield sse("verify", {
            "unsupported_numbers": v_res["unsupported_numbers"],
            "sufficiency": v_res["sufficiency"],
            "badges": v_res["badges"],
            "citations": v_res["citations"],
            "invalid_citations": v_res["invalid_citations"],
            "claim_warnings": v_res.get("claim_warnings", []),
        })
        yield sse("done", {
            "refused": refused,
            "refuse_reason": "llm_refused" if refused else "",
            "timing": p.timing,
            "intent": p.extra.get("intent", Intent.ACADEMIC.value),
            "academic_intent": p.extra.get("academic_intent"),
            "risk_level": p.extra.get("risk_level"),
            "claim_warnings": v_res.get("claim_warnings", []),
            "sufficiency": v_res["sufficiency"],
            "verification_badges": v_res["badges"],
        })
        cid = p.extra.get("conversation_id")
        if cid:
            session_memory.save_turn(
                cid,
                p.question,
                text,
                chunks=p.chunks if not refused else [],
                sources=p.sources if not refused else [],
                topic=p.extra.get("expanded_query", p.question),
            )
    except Exception as e:  # đừng làm sập kết nối SSE
        msg = str(e)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            user_msg = (
                "Tài khoản Gemini API tạm thời hết hạn ngạch truy vấn miễn phí của Google (429 Quota Exceeded). "
                "Bạn có thể đổi sang LLM_PROVIDER=mock trong cấu hình để tiếp tục trải nghiệm ngay lập tức."
            )
        else:
            user_msg = f"{type(e).__name__}: {e}"
        yield sse("error", {"message": user_msg})
