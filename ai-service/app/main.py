from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1 import health_routes, ingest_routes, query_routes
from app.pipeline.retrieval.bm25_search import bm25_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    bm25_index.rebuild()   # dựng chỉ mục BM25 từ data/chunks.jsonl khi khởi động
    yield


app = FastAPI(title="Donga RAG - AI Service", version="0.1.0", lifespan=lifespan)
app.include_router(health_routes.router, prefix="/v1")
app.include_router(ingest_routes.router, prefix="/v1")
app.include_router(query_routes.router, prefix="/v1")
