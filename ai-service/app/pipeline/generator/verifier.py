"""Kiểm chứng câu trả lời, trích dẫn, số liệu và mức độ đầy đủ của bằng chứng (Answer Sufficiency).

Cung cấp:
1. unsupported_numbers: Bắt lỗi LLM viết sai con số so với tài liệu gốc (không gọi LLM).
2. validate_citations: Kiểm tra tính hợp lệ của các thẻ trích dẫn [1], [2] theo số lượng chunk thực tế.
3. determine_sufficiency: Đánh giá 4 trạng thái: SUFFICIENT, PARTIAL, INSUFFICIENT, NO_EVIDENCE.
4. evaluate_verification: Tổng hợp kết quả xác minh và sinh danh sách nhãn hiển thị (badges) chính xác.
"""
from __future__ import annotations

import re
from typing import Any, Literal

SufficiencyState = Literal["SUFFICIENT", "PARTIAL", "INSUFFICIENT", "NO_EVIDENCE"]

_NUM_RE = re.compile(r"\d[\d.,]*")
_CITATION_RE = re.compile(r"\[(\d+)\]")

# Các mẫu cụm từ thể hiện tài liệu chỉ có thông tin một phần hoặc thiếu thông tin cụ thể
_MISSING_INFO_PATTERNS = [
    r"chưa\s+(?:có\s+)?quy\s+định(?:\s+chi\s+tiết|\s+cụ\s+thể)?",
    r"chưa\s+(?:tìm\s+thấy|có)\s+thông\s+tin",
    r"tài\s+liệu.*chưa\s+(?:quy\s+định|đề\s+cập|nêu\s+rõ|có)",
    r"chỉ\s+(?:quy\s+định|đề\s+cập)\s+(?:chung|chính\s+sách\s+chung)",
    r"chưa\s+nêu\s+rõ",
    r"phần\s+còn\s+lại\s+chưa",
    r"tuy\s+nhiên.*chưa",
]
_MISSING_INFO_RE = re.compile("|".join(_MISSING_INFO_PATTERNS), re.IGNORECASE)

_REFUSE_START = "mình chưa tìm thấy thông tin này trong tài liệu hiện có"


def _norm(n: str) -> str:
    """Chuẩn hóa chuỗi số: bỏ dấu phẩy và chấm phân cách hàng nghìn/thập phân."""
    return re.sub(r"[.,]", "", n.rstrip(".,"))


def unsupported_numbers(answer: str, contexts: list[str]) -> list[str]:
    """Tìm các con số xuất hiện trong câu trả lời nhưng không có trong bất kỳ đoạn ngữ cảnh nào."""
    ans = re.sub(r"\[\d+\]", "", answer)  # bỏ số thứ tự trích dẫn [1], [2]
    ctx_nums = {_norm(x) for c in contexts for x in _NUM_RE.findall(c)}
    bad = []
    for x in _NUM_RE.findall(ans):
        n = _norm(x)
        if n and n not in ctx_nums:
            bad.append(x.rstrip(".,"))
    return sorted(set(bad))


def validate_citations(answer: str, max_chunks: int) -> dict[str, Any]:
    """Kiểm tra các trích dẫn [i] trong câu trả lời.
    Trích dẫn hợp lệ khi 1 <= i <= max_chunks.
    """
    raw_citations = [int(m.group(1)) for m in _CITATION_RE.finditer(answer)]
    unique_citations = sorted(set(raw_citations))

    if max_chunks <= 0:
        return {
            "has_citations": len(unique_citations) > 0,
            "citations": unique_citations,
            "invalid_citations": unique_citations,
            "citations_valid": len(unique_citations) == 0,
        }

    valid_citations = [c for c in unique_citations if 1 <= c <= max_chunks]
    invalid_citations = [c for c in unique_citations if c < 1 or c > max_chunks]

    return {
        "has_citations": len(valid_citations) > 0,
        "citations": valid_citations,
        "invalid_citations": invalid_citations,
        "citations_valid": len(invalid_citations) == 0,
    }


def determine_sufficiency(
    question: str,
    answer: str,
    chunks: list[dict],
    refused: bool = False,
    refuse_reason: str = "",
) -> SufficiencyState:
    """Phân loại mức độ đầy đủ của bằng chứng thành 4 trạng thái:
    - NO_EVIDENCE: Không có tài liệu hoặc hệ thống từ chối.
    - INSUFFICIENT: Có tài liệu nhưng không chứa thông tin cụ thể mà người dùng hỏi.
    - PARTIAL: Tài liệu chỉ hỗ trợ một phần yêu cầu, phần còn lại chưa có thông tin.
    - SUFFICIENT: Tài liệu có đủ căn cứ để trả lời trực tiếp câu hỏi.
    """
    # 1. Trường hợp từ chối hoặc không có chunks
    if refused or not chunks:
        return "NO_EVIDENCE"

    ans_lower = answer.strip().lower()
    if ans_lower.startswith(_REFUSE_START):
        return "NO_EVIDENCE"

    # 2. Kiểm tra câu trả lời có chứa trích dẫn nào không
    cit_info = validate_citations(answer, len(chunks))
    has_citations = cit_info["has_citations"]
    has_missing_indicator = bool(_MISSING_INFO_RE.search(ans_lower))

    # 3. Phân biệt INSUFFICIENT vs PARTIAL vs SUFFICIENT
    if has_missing_indicator:
        # Nếu có nói rõ thông tin thiếu, kiểm tra xem có trích dẫn khẳng định nào khác không
        if has_citations:
            return "PARTIAL"
        return "INSUFFICIENT"

    # Nếu không trích dẫn được đoạn nào dù có chunks -> INSUFFICIENT
    if not has_citations and len(chunks) > 0:
        return "INSUFFICIENT"

    # Mặc định có trích dẫn và không báo thiếu thông tin -> SUFFICIENT
    return "SUFFICIENT"


def evaluate_verification(
    question: str,
    answer: str,
    chunks: list[dict],
    refused: bool = False,
    refuse_reason: str = "",
) -> dict[str, Any]:
    """Đánh giá toàn diện câu trả lời:
    - Bắt lỗi số lạ (unsupported numbers)
    - Kiểm tra trích dẫn hợp lệ (citations)
    - Xác định Answer Sufficiency
    - Tạo danh sách nhãn hiển thị chính xác (badges)
    """
    contexts = [c.get("text", "") for c in chunks] if chunks else []
    bad_numbers = unsupported_numbers(answer, contexts) if not refused and contexts else []
    cit_info = validate_citations(answer, len(chunks))
    sufficiency = determine_sufficiency(
        question=question,
        answer=answer,
        chunks=chunks,
        refused=refused,
        refuse_reason=refuse_reason,
    )

    badges: list[str] = []

    # Sinh nhãn hiển thị chuẩn hóa theo Task E
    if sufficiency == "NO_EVIDENCE":
        badges.append("Chưa đủ bằng chứng để kết luận")
    elif sufficiency == "INSUFFICIENT":
        badges.append("Chưa đủ bằng chứng để kết luận")
    elif sufficiency == "PARTIAL":
        if cit_info["has_citations"]:
            badges.append("Có trích dẫn nguồn")
        badges.append("Chưa đủ bằng chứng để kết luận (Một phần)")
        if bad_numbers:
            badges.append(f"Số liệu chưa rõ nguồn: {', '.join(bad_numbers)}")
    elif sufficiency == "SUFFICIENT":
        if cit_info["has_citations"]:
            badges.append("Có trích dẫn nguồn")
        if cit_info["citations_valid"] and not bad_numbers:
            badges.append("Đã đối chiếu nguồn cho các khẳng định")
        elif bad_numbers:
            badges.append(f"Số liệu chưa rõ nguồn: {', '.join(bad_numbers)}")

    if cit_info["invalid_citations"]:
        badges.append(f"Trích dẫn ngoài phạm vi: {cit_info['invalid_citations']}")

    return {
        "sufficiency": sufficiency,
        "has_citations": cit_info["has_citations"],
        "citations_valid": cit_info["citations_valid"],
        "citations": cit_info["citations"],
        "invalid_citations": cit_info["invalid_citations"],
        "unsupported_numbers": bad_numbers,
        "badges": badges,
    }
