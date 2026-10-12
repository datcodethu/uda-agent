"""Hàm tiện ích KHÔNG phụ thuộc thư viện ngoài (dễ test)."""
from __future__ import annotations
import re
import unicodedata


def extract_text(content) -> str:
    """Gemini (và vài model khác) có thể trả content là danh sách khối
    [{'type': 'text', 'text': ..., 'extras': {'signature': ...}}].
    Chỉ lấy phần chữ, bỏ siêu dữ liệu nội bộ (signature...)."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, str):
                parts.append(b)
            elif isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return "".join(parts)
    return str(content)


def slugify(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "doc"
