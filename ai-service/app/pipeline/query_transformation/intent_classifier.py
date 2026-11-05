"""Phân loại ý định của câu hỏi: học vụ, dữ liệu cá nhân, chào hỏi thuần túy, và đánh giá rủi ro chính sách.

Cung cấp:
1. classify(question): Fast-path Guardrail (ACADEMIC, PERSONAL, OUT_OF_SCOPE, AMBIGUOUS).
2. classify_academic_intent_and_risk(question): Phân loại sâu 8 nhóm ý định học vụ và 3 mức độ rủi ro (LOW, MEDIUM, HIGH)
   nhằm định hướng chiến lược trả lời Student-Centered RAG (Task A).
"""
from __future__ import annotations
import re
from enum import Enum


class Intent(str, Enum):
    ACADEMIC = "academic"           # Quy chế, quy định học vụ (mặc định, đi tiếp vào RAG)
    PERSONAL = "personal_data"     # Dữ liệu riêng tư (điểm, nợ học phí, lịch học cá nhân)
    OUT_OF_SCOPE = "out_of_scope"   # Chào hỏi thuần túy
    AMBIGUOUS = "ambiguous"         # Dự phòng cho kiến trúc mở rộng


class AcademicIntent(str, Enum):
    GENERAL_INFORMATION = "GENERAL_INFORMATION"
    BENEFIT_EXPLANATION = "BENEFIT_EXPLANATION"
    POLICY_REQUIREMENT = "POLICY_REQUIREMENT"
    ELIGIBILITY_CHECK = "ELIGIBILITY_CHECK"
    ACADEMIC_CONSEQUENCE = "ACADEMIC_CONSEQUENCE"
    FINANCIAL_DIFFICULTY = "FINANCIAL_DIFFICULTY"
    PROCEDURE_GUIDANCE = "PROCEDURE_GUIDANCE"
    PERSONAL_CASE = "PERSONAL_CASE"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


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

# Mẫu nhận diện ý định học vụ chi tiết
_BENEFIT_RE = re.compile(r"\b(có quan trọng không|lợi ích|quyền lợi|tại sao cần|ý nghĩa của|tác dụng gì)\b", re.I)
_REQUIREMENT_RE = re.compile(r"\b(có bắt buộc không|bắt buộc không|quy định về|chuẩn đầu ra là gì|nghĩa vụ)\b", re.I)
_FINANCIAL_DIFF_RE = re.compile(r"\b(gia đình.*khó khăn|hoàn cảnh.*khó khăn|hộ nghèo|gia hạn học phí|xin gia hạn|hoãn đóng|vay vốn|hỗ trợ tài chính)\b", re.I)
_PROCEDURE_RE = re.compile(r"\b(phải làm gì|làm thế nào|quy trình|thủ tục|các bước|nộp ở đâu|chưa cập nhật|bị cấm thi.*(phải|làm gì))\b", re.I)
_CONSEQUENCE_RE = re.compile(r"\b(có bị cấm thi|có bị trừ|có ảnh hưởng|có bị kỷ luật|có bị đình chỉ|tốt nghiệp.*công nợ|công nợ.*tốt nghiệp|hậu quả|chế tài|hình thức xử lý)\b", re.I)
_ELIGIBILITY_RE = re.compile(r"\b(có được.*(thi|đăng ký|tốt nghiệp|xét)|được không|phải đóng thêm không|điều kiện để)\b", re.I)
_PERSONAL_CASE_RE = re.compile(r"\b(?:em|mình|tôi)\b.*(?:\d+\s*(?:triệu|nghìn|tr|k|đ|đồng|buổi|môn)|ngày mai|chiều nay|kỳ này)", re.I)

_HIGH_RISK_KEYWORDS = re.compile(r"\b(cấm thi|dự thi|học phí|công nợ|tốt nghiệp|kỷ luật|đình chỉ|đuổi học|tiền)\b", re.I)


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


def classify_academic_intent_and_risk(question: str) -> tuple[AcademicIntent, RiskLevel]:
    """Phân loại sâu ý định học vụ và đánh giá mức độ rủi ro phục vụ Student-Centered RAG (Task A)."""
    q = question.strip()

    # 1. Xác định AcademicIntent
    if _PERSONAL_CASE_RE.search(q):
        intent = AcademicIntent.PERSONAL_CASE
    elif _FINANCIAL_DIFF_RE.search(q):
        intent = AcademicIntent.FINANCIAL_DIFFICULTY
    elif _PROCEDURE_RE.search(q):
        intent = AcademicIntent.PROCEDURE_GUIDANCE
    elif _CONSEQUENCE_RE.search(q):
        intent = AcademicIntent.ACADEMIC_CONSEQUENCE
    elif _BENEFIT_RE.search(q):
        intent = AcademicIntent.BENEFIT_EXPLANATION
    elif _REQUIREMENT_RE.search(q):
        intent = AcademicIntent.POLICY_REQUIREMENT
    elif _ELIGIBILITY_RE.search(q):
        intent = AcademicIntent.ELIGIBILITY_CHECK
    else:
        intent = AcademicIntent.GENERAL_INFORMATION

    # 2. Đánh giá RiskLevel
    if _HIGH_RISK_KEYWORDS.search(q) or intent in (
        AcademicIntent.ACADEMIC_CONSEQUENCE,
        AcademicIntent.FINANCIAL_DIFFICULTY,
        AcademicIntent.PERSONAL_CASE,
    ):
        # Ngoại lệ: Hỏi về lợi ích đơn thuần (ví dụ BHYT có quan trọng không) thì không gán HIGH
        if intent == AcademicIntent.BENEFIT_EXPLANATION:
            risk = RiskLevel.LOW
        else:
            risk = RiskLevel.HIGH
    elif intent in (
        AcademicIntent.POLICY_REQUIREMENT,
        AcademicIntent.ELIGIBILITY_CHECK,
        AcademicIntent.PROCEDURE_GUIDANCE,
    ):
        risk = RiskLevel.MEDIUM
    else:
        risk = RiskLevel.LOW

    return intent, risk
