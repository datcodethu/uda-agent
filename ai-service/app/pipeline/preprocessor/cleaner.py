"""Làm sạch văn bản trước khi cắt đoạn. Chỉ dùng thư viện chuẩn."""
from __future__ import annotations
import re
import unicodedata
from collections import Counter

_PAGE_NUM_RE = re.compile(r"^\s*(trang\s+)?\d+\s*(/\s*\d+)?\s*$", re.IGNORECASE)
_STRUCT_RE = re.compile(r"^\s*(điều|chương|mục)\s+", re.IGNORECASE)


def clean_text(text: str) -> str:
    # 1) Chuẩn hóa Unicode NFC: cực kỳ quan trọng với tiếng Việt
    #    (chữ 'ế' có thể được lưu dạng 1 ký tự hoặc 2 ký tự, khiến tìm kiếm trượt)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")

    lines = [ln.rstrip() for ln in text.split("\n")]

    # 2) Bỏ dòng chỉ có số trang
    lines = [ln for ln in lines if not _PAGE_NUM_RE.match(ln)]

    # 3) Bỏ header/footer lặp lại (dòng ngắn xuất hiện >= 4 lần, không phải Điều/Chương)
    counts = Counter(ln.strip() for ln in lines if ln.strip())
    repeated = {
        ln for ln, n in counts.items()
        if n >= 4 and len(ln) <= 100 and not _STRUCT_RE.match(ln) and "|" not in ln
    }
    lines = [ln for ln in lines if ln.strip() not in repeated]

    # 4) Gộp khoảng trắng thừa
    out = [re.sub(r"[ \t]+", " ", ln).strip() for ln in lines]
    text = "\n".join(out)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
