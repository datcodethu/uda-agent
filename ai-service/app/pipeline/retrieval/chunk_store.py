"""Kho chunk dạng JSONL (nguồn sự thật cho BM25 và để xem lại chunk)."""
from __future__ import annotations
import json
import threading
from pathlib import Path
from app.core.config import settings

_lock = threading.Lock()


def _path() -> Path:
    p = Path(settings.chunks_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_all() -> list[dict]:
    p = _path()
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _save_all(chunks: list[dict]) -> None:
    with _path().open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


def replace_document(doc_name: str, new_chunks: list[dict]) -> None:
    with _lock:
        rest = [c for c in load_all() if c["doc_name"] != doc_name]
        _save_all(rest + new_chunks)


def delete_document(doc_name: str) -> int:
    with _lock:
        allc = load_all()
        rest = [c for c in allc if c["doc_name"] != doc_name]
        _save_all(rest)
        return len(allc) - len(rest)


def list_documents() -> list[dict]:
    docs: dict[str, dict] = {}
    for c in load_all():
        d = docs.setdefault(c["doc_name"], {"doc_name": c["doc_name"], "status": c.get("status", "ACTIVE"), "chunks": 0})
        d["chunks"] += 1
    return list(docs.values())
