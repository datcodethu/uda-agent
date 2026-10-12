from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core.security import verify_key
from app.pipeline import rag_pipeline
from app.pipeline.generator.stream_handler import stream_answer
from app.schemas.query_schema import QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"], dependencies=[Depends(verify_key)])


@router.post("", response_model=QueryResponse)
def query(req: QueryRequest):
    history = [t.model_dump() for t in req.history]
    return rag_pipeline.answer(req.question, history, req.mode, req.top_k)


@router.post("/stream")
def query_stream(req: QueryRequest):
    history = [t.model_dump() for t in req.history]
    p = rag_pipeline.prepare(req.question, history, req.mode, req.top_k)
    return StreamingResponse(
        stream_answer(p), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
