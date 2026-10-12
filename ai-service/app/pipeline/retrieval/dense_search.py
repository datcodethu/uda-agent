"""Tìm kiếm vector: embedding bằng Gemini, lưu trong Qdrant (local hoặc server)."""
from __future__ import annotations
import uuid
from functools import lru_cache

from qdrant_client import QdrantClient, models
from app.core.config import settings

_ready = False


@lru_cache
def get_client() -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    # Chế độ local: thư mục bị KHOÁ cho 1 tiến trình. Không chạy script nạp dữ liệu
    # khi server đang chạy (dùng API /v1/ingest hoặc tắt server trước).
    return QdrantClient(path=settings.qdrant_path)


@lru_cache
def get_embedder():
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    return GoogleGenerativeAIEmbeddings(
        model=settings.gemini_embedding_model,
        google_api_key=settings.google_api_key or None,
    )


def embed_passages(texts: list[str]) -> list[list[float]]:
    emb, out = get_embedder(), []
    for i in range(0, len(texts), 50):
        batch = texts[i:i + 50]
        try:
            out.extend(emb.embed_documents(batch, task_type="RETRIEVAL_DOCUMENT"))
        except TypeError:  # phiên bản thư viện không nhận task_type
            out.extend(emb.embed_documents(batch))
    return out


def embed_query(text: str) -> list[float]:
    emb = get_embedder()
    try:
        return emb.embed_query(text, task_type="RETRIEVAL_QUERY")
    except TypeError:
        return emb.embed_query(text)


def ensure_collection() -> None:
    global _ready
    if _ready:
        return
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        dim = len(embed_query("kiểm tra số chiều vector"))
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )
    _ready = True


def upsert_chunks(chunks: list[dict]) -> None:
    ensure_collection()
    vectors = embed_passages([c["text"] for c in chunks])
    points = [
        models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])), vector=v, payload=c)
        for c, v in zip(chunks, vectors)
    ]
    get_client().upsert(collection_name=settings.qdrant_collection, points=points)


def delete_document(doc_name: str) -> None:
    client = get_client()
    if not client.collection_exists(settings.qdrant_collection):
        return
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key="doc_name", match=models.MatchValue(value=doc_name))
        ])),
    )


def dense_search(query: str, top_k: int, only_active: bool = True) -> list[dict]:
    ensure_collection()
    flt = None
    if only_active:  # chỉ lấy văn bản còn hiệu lực
        flt = models.Filter(must=[models.FieldCondition(key="status", match=models.MatchValue(value="ACTIVE"))])
    res = get_client().query_points(
        collection_name=settings.qdrant_collection,
        query=embed_query(query), limit=top_k, query_filter=flt, with_payload=True,
    ).points
    return [{**p.payload, "dense_score": float(p.score)} for p in res]
