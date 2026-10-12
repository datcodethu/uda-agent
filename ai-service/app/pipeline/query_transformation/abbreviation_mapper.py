"""Mở rộng từ viết tắt: THÊM dạng đầy đủ vào cuối câu hỏi (không thay thế),
để cả embedding lẫn BM25 đều bắt được."""
from __future__ import annotations
import json
import re
from pathlib import Path

_SEED = Path(__file__).resolve().parents[3] / "data" / "seed" / "abbreviations_seed.json"
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)

_DEFAULT = {
    "bhyt": "bảo hiểm y tế",
    "đkhp": "đăng ký học phần",
    "ctđt": "chương trình đào tạo",
    "cđr": "chuẩn đầu ra",
    "ktx": "ký túc xá",
    "đrl": "điểm rèn luyện",
    "sv": "sinh viên",
    "gv": "giảng viên",
    "tn": "tốt nghiệp",
}


def load_map(path: Path | None = None) -> dict[str, str]:
    p = path or _SEED
    m = dict(_DEFAULT)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        m.update({k.lower(): v for k, v in data.items()})
    return m


def expand_abbreviations(query: str, mapping: dict[str, str] | None = None) -> str:
    mapping = mapping if mapping is not None else load_map()
    tokens = _TOKEN_RE.findall(query.lower())
    extras = []
    for t in tokens:
        full = mapping.get(t)
        if full and full not in extras:
            extras.append(full)
    return query if not extras else f"{query} ({'; '.join(extras)})"
