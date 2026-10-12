"""Nạp / xoá tài liệu: làm sạch -> cắt đoạn -> lưu JSONL -> embedding vào Qdrant -> dựng lại BM25."""
from __future__ import annotations
from app.core.config import settings
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.structural_chunker import chunk_document
from app.pipeline.retrieval import chunk_store, dense_search
from app.pipeline.retrieval.bm25_search import bm25_index


def index_document(doc_name: str, text: str, status: str = "ACTIVE") -> dict:
    chunks = [c.to_dict() for c in chunk_document(
        clean_text(text), doc_name, status, settings.chunk_max_chars, settings.chunk_overlap_chars)]
    if not chunks:
        raise ValueError("Không cắt được đoạn nào từ tài liệu (văn bản rỗng?)")
    dense_search.delete_document(doc_name)       # nạp lại cùng tên = thay thế bản cũ
    chunk_store.replace_document(doc_name, chunks)
    dense_search.upsert_chunks(chunks)
    bm25_index.rebuild()
    return {"doc_name": doc_name, "chunks": len(chunks), "status": status}


def remove_document(doc_name: str) -> dict:
    dense_search.delete_document(doc_name)
    n = chunk_store.delete_document(doc_name)
    bm25_index.rebuild()
    return {"doc_name": doc_name, "deleted_chunks": n}
