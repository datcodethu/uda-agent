from fastapi import APIRouter
from app.core.config import settings
from app.pipeline.retrieval import chunk_store

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "llm_provider": settings.llm_provider,
            "chat_model": settings.gemini_chat_model,
            "documents": len(chunk_store.list_documents())}
