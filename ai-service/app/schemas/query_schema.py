from typing import Literal
from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = []
    stream: bool = False
    mode: Literal["dense", "bm25", "hybrid"] = "hybrid"
    top_k: int | None = Field(default=None, ge=1, le=20)


class Source(BaseModel):
    index: int
    chunk_id: str
    doc_name: str
    chuong: str = ""
    dieu: str = ""
    score: float = 0.0
    snippet: str = ""


class QueryResponse(BaseModel):
    answer: str
    refused: bool
    refuse_reason: str = ""
    sources: list[Source] = []
    unsupported_numbers: list[str] = []
    best_dense_score: float | None = None
    retrieval_ms: int = 0
    latency_ms: int = 0
