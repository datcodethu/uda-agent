"""Kiểm chứng số liệu: mọi con số trong câu trả lời có xuất hiện trong đoạn nguồn không?
Không thay thế việc đọc lại, nhưng bắt được lỗi 'LLM viết sai số' rất rẻ (không gọi LLM)."""
from __future__ import annotations
import re

_NUM_RE = re.compile(r"\d[\d.,]*")


def _norm(n: str) -> str:
    return re.sub(r"[.,]", "", n.rstrip(".,"))


def unsupported_numbers(answer: str, contexts: list[str]) -> list[str]:
    ans = re.sub(r"\[\d+\]", "", answer)  # bỏ số thứ tự trích dẫn [1], [2]
    ctx_nums = {_norm(x) for c in contexts for x in _NUM_RE.findall(c)}
    bad = []
    for x in _NUM_RE.findall(ans):
        n = _norm(x)
        if n and n not in ctx_nums:
            bad.append(x.rstrip(".,"))
    return sorted(set(bad))
