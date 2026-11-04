"""Router phục vụ giao diện Web Chat và các endpoint chat tương tác trực tiếp."""
from __future__ import annotations
from pathlib import Path
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import BASE_DIR
from app.pipeline import rag_pipeline
from app.pipeline.generator.stream_handler import stream_answer
from app.schemas.query_schema import ChatTurn

router = APIRouter(tags=["web-chat"])

HTML_FILE = BASE_DIR / "app" / "static" / "index.html"


class WebChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = []
    conversation_id: str | None = Field(default=None, description="Mã định danh phiên hội thoại")
    mode: Literal["dense", "bm25", "hybrid"] = "hybrid"
    top_k: int | None = Field(default=None, ge=1, le=20)
    use_intent: bool = True


@router.get("/", response_class=HTMLResponse)
@router.get("/chat", response_class=HTMLResponse)
def get_chat_page() -> HTMLResponse:
    """Trả về giao diện Web Chat đơn trang trực quan phục vụ Demo."""
    if not HTML_FILE.exists():
        return HTMLResponse(
            content="<h1>Không tìm thấy file giao diện app/static/index.html</h1>",
            status_code=404,
        )
    return HTMLResponse(content=HTML_FILE.read_text(encoding="utf-8"))


@router.post("/api/chat/stream")
def chat_stream(req: WebChatRequest):
    """Endpoint Server-Sent Events (SSE) cho trình duyệt nhận từng token."""
    history = [t.model_dump() for t in req.history]
    p = rag_pipeline.prepare(
        question=req.question,
        history=history,
        conversation_id=req.conversation_id,
        mode=req.mode,
        top_k=req.top_k,
        use_intent=req.use_intent,
    )
    return StreamingResponse(
        stream_answer(p),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/api/chat")
def chat_sync(req: WebChatRequest) -> dict:
    """Endpoint trả lời JSON đầy đủ (non-streaming fallback)."""
    history = [t.model_dump() for t in req.history]
    return rag_pipeline.answer(
        question=req.question,
        history=history,
        conversation_id=req.conversation_id,
        mode=req.mode,
        top_k=req.top_k,
        use_intent=req.use_intent,
    )
