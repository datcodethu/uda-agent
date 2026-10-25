"""Phân loại ý định của câu hỏi: học vụ, dữ liệu cá nhân, ngoài phạm vi, mơ hồ."""
from __future__ import annotations
import re
from enum import Enum


class Intent(str, Enum):
    ACADEMIC = "academic"           # Quy chế, quy định học vụ (đưa vào RAG)
    PERSONAL = "personal_data"     # Dữ liệu riêng tư (điểm, nợ học phí, lịch học cá nhân)
    OUT_OF_SCOPE = "out_of_scope"   # Chào hỏi, tán gẫu, việc ngoài đời
    AMBIGUOUS = "ambiguous"         # Câu hỏi quá ngắn, tối nghĩa (< 3 từ)


# Mẫu nhận diện dữ liệu cá nhân (tra cứu điểm cụ thể của bản thân, công nợ, lịch học riêng...)
_PERSONAL_PATTERNS = [
    re.compile(r"\b(điểm|lịch học|lịch thi|công nợ|học phí)\b.*\bcủa (em|mình|tôi|con)\b", re.I),
    re.compile(r"\b(em|mình|tôi)\b.*\b(còn )?(nợ|thiếu)\b.*\b(bao nhiêu|mấy|nhiêu)\b", re.I),
    re.compile(r"\b(xem|tra cứu)\s+(điểm|lịch học|lịch thi|công nợ)\s+cá nhân\b", re.I),
    re.compile(r"\b(idsv|mssv|mã sinh viên)\s*[:=]?\s*\d+", re.I),
    re.compile(r"\b(điểm|kết quả học tập)\s+của (em|mình|tôi)\b", re.I),
    re.compile(r"\b(cho em|cho tôi|cho mình)\s+(xem|biết)\s+(điểm|lịch thi|lịch học)\b", re.I),
]

# Mẫu nhận diện chào hỏi, tán gẫu, hỏi việc ngoài xã hội không liên quan đào tạo
_SMALLTALK_PATTERNS = [
    re.compile(r"^(?:hi|hello|hey|alo|(?:xin\s+)?chào(?:\s+(?:bạn|bot|ad|em|anh|chị|thầy|cô))?)[!\.\?]*$", re.I),
    re.compile(r"\b(kết bạn|người yêu|bạn gái|bạn trai|thời tiết|bóng đá|chơi game|ăn gì)\b", re.I),
    re.compile(r"\b(quán cơm|quán ăn|trà sữa|quán cafe|quán cà phê)\b", re.I),
    re.compile(r"\b(tuyến xe buýt|xe buýt|xe bus)\b", re.I),
]


def classify(question: str) -> Intent:
    """Phân loại câu hỏi thành một trong bốn Intent."""
    q = question.strip()
    if not q:
        return Intent.AMBIGUOUS

    # 1. Kiểm tra câu hỏi dữ liệu cá nhân
    if any(p.search(q) for p in _PERSONAL_PATTERNS):
        return Intent.PERSONAL

    # 2. Kiểm tra chào hỏi hoặc ngoài phạm vi
    if any(p.search(q) for p in _SMALLTALK_PATTERNS):
        return Intent.OUT_OF_SCOPE

    # 3. Kiểm tra câu quá ngắn / mơ hồ (< 3 từ, ví dụ "học bổng", "học phí", ".")
    tokens = q.split()
    if len(tokens) < 3:
        return Intent.AMBIGUOUS

    # 4. Mặc định là câu hỏi học vụ
    return Intent.ACADEMIC
