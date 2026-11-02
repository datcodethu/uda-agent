"""Phân loại ý định của câu hỏi: học vụ, dữ liệu cá nhân, chào hỏi thuần túy.

Nguyên tắc vàng: Chặn nhầm một câu học vụ thật tệ hơn để một câu ngoài phạm vi đi qua.
"""
from __future__ import annotations
import re
from enum import Enum


class Intent(str, Enum):
    ACADEMIC = "academic"           # Quy chế, quy định học vụ (mặc định, đi tiếp vào RAG)
    PERSONAL = "personal_data"     # Dữ liệu riêng tư (điểm, nợ học phí, lịch học cá nhân)
    OUT_OF_SCOPE = "out_of_scope"   # Chào hỏi thuần túy
    AMBIGUOUS = "ambiguous"         # Dự phòng cho kiến trúc mở rộng


# Từ khóa chính sách, quy chế: nếu xuất hiện thì KHÔNG BAO GIỜ chặn, luôn coi là ACADEMIC
_POLICY_EXCLUSIONS = re.compile(
    r"\b(quy định|tiêu chuẩn|khóa|ngành|điều kiện|bao nhiêu tín chỉ|thủ tục|hướng dẫn|học phần|được không|có bị|xét|chuẩn đầu ra)\b",
    re.I,
)

# Mẫu nhận diện tra cứu dữ liệu cá nhân (đại từ ngôi 1 + cụm từ tra cứu cụ thể)
_PERSONAL_PATTERNS = [
    re.compile(r"\b(điểm|công nợ)\b.*\bcủa\s+(?:riêng\s+)?(?:cá nhân\s+)?(?:em|mình|tôi|con)\b", re.I),
    re.compile(r"\b(?:em|mình|tôi|con)\b.*\b(?:còn\s+)?(?:nợ|thiếu)\s+(?:bao nhiêu|mấy|nhiêu)\b", re.I),
    re.compile(r"\b(?:xem|tra cứu)\s+(?:điểm|lịch thi|công nợ)\s+cá nhân\b", re.I),
    re.compile(r"\b(?:idsv|mssv|mã sinh viên)\s*[:=]?\s*\d+", re.I),
    re.compile(r"\b(?:cho em|cho mình|cho tôi)\s+(?:xem|biết)\s+điểm\s+của\s+(?:em|mình|tôi|con)\b", re.I),
]

# Mẫu nhận diện chào hỏi thuần túy
_SMALLTALK_PATTERNS = [
    re.compile(
        r"^(?:hi|hello|hey|alo|(?:xin\s+)?chào(?:\s+(?:bạn|bot|ad|em|anh|chị|thầy\s+cô|thầy|cô))?(?:\s+ạ)?)[!\.\?]*$",
        re.I,
    ),
]


def classify(question: str) -> Intent:
    """Phân loại câu hỏi thành Intent:
    - OUT_OF_SCOPE: Chào hỏi thuần túy.
    - PERSONAL: Tra cứu dữ liệu cá nhân (đại từ ngôi 1 + cụm tra cứu, KHÔNG chứa từ khóa chính sách).
    - ACADEMIC: Mọi câu hỏi khác (bao gồm câu học vụ, câu chứa từ khóa chính sách, câu ngoài phạm vi khác).
    """
    q = question.strip()
    if not q:
        return Intent.ACADEMIC

    # (a) Chào hỏi thuần túy
    if any(p.search(q) for p in _SMALLTALK_PATTERNS):
        return Intent.OUT_OF_SCOPE

    # (b) Tra cứu dữ liệu cá nhân: chỉ chặn khi KHÔNG chứa từ khóa chính sách
    if not _POLICY_EXCLUSIONS.search(q):
        if any(p.search(q) for p in _PERSONAL_PATTERNS):
            return Intent.PERSONAL

    # Mọi câu hỏi khác đều đi tiếp vào truy xuất
    return Intent.ACADEMIC
