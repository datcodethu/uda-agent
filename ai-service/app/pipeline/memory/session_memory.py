"""Quản lý bộ nhớ hội thoại theo phiên (Session Memory) phục vụ Contextual RAG.

Đặc tính:
- Tách biệt tuyệt đối theo conversation_id.
- In-memory thread-safe, tự động hết hạn (TTL 30 phút).
- Lưu giữ lịch sử hội thoại và danh sách tài liệu/chunk đã dùng ở lượt trước.
- Kiểm tra tính hợp lệ của nguồn cũ (source invalidation) trước khi tái sử dụng.
"""
from __future__ import annotations
import time
import threading
from dataclasses import dataclass, field
from app.pipeline.retrieval import chunk_store


@dataclass
class SessionData:
    conversation_id: str
    history: list[dict] = field(default_factory=list)
    last_chunks: list[dict] = field(default_factory=list)
    last_sources: list[dict] = field(default_factory=list)
    last_topic: str = ""
    updated_at: float = field(default_factory=time.time)


class SessionMemoryStore:
    def __init__(self, ttl_seconds: int = 1800, max_turns: int = 6) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_turns = max_turns
        self._sessions: dict[str, SessionData] = {}
        self._lock = threading.RLock()

    def get_or_create(self, conversation_id: str) -> SessionData:
        with self._lock:
            self._cleanup_expired_locked()
            if conversation_id not in self._sessions:
                self._sessions[conversation_id] = SessionData(conversation_id=conversation_id)
            session = self._sessions[conversation_id]
            session.updated_at = time.time()
            return session

    def get_session(self, conversation_id: str) -> SessionData | None:
        with self._lock:
            self._cleanup_expired_locked()
            session = self._sessions.get(conversation_id)
            if session:
                session.updated_at = time.time()
            return session

    def save_turn(
        self,
        conversation_id: str,
        question: str,
        answer: str,
        chunks: list[dict] | None = None,
        sources: list[dict] | None = None,
        topic: str | None = None,
    ) -> None:
        with self._lock:
            session = self.get_or_create(conversation_id)
            # Thêm turn mới
            session.history.append({"role": "user", "content": question})
            session.history.append({"role": "assistant", "content": answer})
            # Giới hạn số lượt
            if len(session.history) > self.max_turns * 2:
                session.history = session.history[-(self.max_turns * 2):]
            if chunks is not None:
                session.last_chunks = list(chunks)
            if sources is not None:
                session.last_sources = list(sources)
            if topic:
                session.last_topic = topic
            session.updated_at = time.time()

    def validate_cached_sources(self, chunks: list[dict]) -> tuple[bool, list[dict]]:
        """Kiểm tra nguồn cũ có còn hợp lệ trong kho hay không (chống dùng tài liệu đã bị gỡ/thu hồi)."""
        if not chunks:
            return False, []
        try:
            active_docs = {
                d["doc_name"]: d.get("status", "ACTIVE")
                for d in chunk_store.list_documents()
            }
        except Exception:
            return False, []

        valid_chunks = []
        for c in chunks:
            dn = c.get("doc_name")
            if not dn or dn not in active_docs:
                return False, []  # Tài liệu đã bị xóa khỏi kho
            if active_docs[dn] != "ACTIVE":
                return False, []  # Tài liệu không còn hiệu lực
            valid_chunks.append(c)

        return True, valid_chunks

    def clear_session(self, conversation_id: str) -> None:
        with self._lock:
            self._sessions.pop(conversation_id, None)

    def clear_all(self) -> None:
        with self._lock:
            self._sessions.clear()

    def _cleanup_expired_locked(self) -> None:
        now = time.time()
        expired = [
            cid for cid, s in self._sessions.items()
            if now - s.updated_at > self.ttl_seconds
        ]
        for cid in expired:
            del self._sessions[cid]


session_memory = SessionMemoryStore()
