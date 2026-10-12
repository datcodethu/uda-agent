"""Lớp bọc LLM. Muốn đổi sang OpenAI/Ollama: thêm class mới có generate() và stream()."""
from __future__ import annotations
import time
from functools import lru_cache
from typing import Iterator

from app.core.config import settings
from app.core.textutils import extract_text

_ROLE = {"system": "system", "user": "human", "assistant": "ai"}


class GeminiLLM:
    def __init__(self) -> None:
        from langchain_google_genai import ChatGoogleGenerativeAI
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_chat_model,
            google_api_key=settings.google_api_key or None,
            temperature=settings.llm_temperature,
        )

    @staticmethod
    def _to_lc(messages: list[dict]) -> list[tuple[str, str]]:
        return [(_ROLE[m["role"]], m["content"]) for m in messages]

    def generate(self, messages: list[dict]) -> str:
        return extract_text(self.llm.invoke(self._to_lc(messages)).content).strip()

    def stream(self, messages: list[dict]) -> Iterator[str]:
        for chunk in self.llm.stream(self._to_lc(messages)):
            t = extract_text(chunk.content)
            if t:
                yield t


class MockLLM:
    """Không gọi LLM thật: để thử nhanh API/SSE/giao diện mà không tốn quota."""
    TEXT = ("[MOCK] Đây là câu trả lời giả lập vì LLM_PROVIDER=mock. "
            "Hãy xem trường 'sources' để biết hệ thống đã truy xuất những đoạn nào.")

    def generate(self, messages: list[dict]) -> str:
        return self.TEXT

    def stream(self, messages: list[dict]) -> Iterator[str]:
        for w in self.TEXT.split(" "):
            time.sleep(0.02)
            yield w + " "


@lru_cache
def get_llm():
    if settings.llm_provider == "mock":
        return MockLLM()
    return GeminiLLM()
