"""Kiểm chứng câu trả lời, trích dẫn, số liệu, mức độ đầy đủ của bằng chứng (Answer Sufficiency)
và kiểm chứng mức độ khẳng định (Claim-Level Verification).

Cung cấp:
1. unsupported_numbers: Bắt lỗi LLM viết sai con số so với tài liệu gốc (không gọi LLM).
2. validate_citations: Kiểm tra tính hợp lệ của các thẻ trích dẫn [1], [2] theo số lượng chunk thực tế.
3. determine_sufficiency: Đánh giá 4 trạng thái: SUFFICIENT, PARTIAL, INSUFFICIENT, NO_EVIDENCE.
4. verify_claims: Bắt lỗi khẳng định tuyệt đối thiếu điều kiện (như chắc chắn cấm thi) và chế tài không có nguồn.
5. evaluate_verification: Tổng hợp kết quả xác minh và sinh danh sách nhãn hiển thị (badges) chính xác.
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

# Các mẫu khẳng định tuyệt đối thiếu điều kiện bảo vệ (cần kiểm tra trong Claim-Level Verification)
_UNQUALIFIED_PATTERNS = [
    re.compile(r"\b(?:chắc\s+chắn|bạn\s+sẽ|sẽ)\s+bị\s+cấm\s+thi\b", re.I),
    re.compile(r"\bchắc\s+chắn\s+(?:bị|không\s+được|không\s+thể)\b", re.I),
    re.compile(r"\btất\s+cả\s+sinh\s+viên\s+đều\s+bị\b", re.I),
    re.compile(r"^không\s+được[!\.\s]+bạn\s+sẽ\s+bị\b", re.I),
]

_QUALIFIERS = [
    r"nếu\s+không\s+có\s+lý\s+do\s+chính\s+đáng",
    r"cố\s+tình",
    r"có\s+thể\s+bị",
    r"tùy\s+thuộc",
    r"theo\s+quyết\s+định",
    r"cần\s+kiểm\s+tra",
    r"xem\s+xét",
]
_QUALIFIER_RE = re.compile("|".join(_QUALIFIERS), re.IGNORECASE)

_HEAVY_TERMS = [
    "buộc thôi học", "đình chỉ học tập", "hủy kết quả thi", "truy cứu trách nhiệm"
]


def _norm(n: str) -> str:
    """Chuẩn hóa chuỗi số: bỏ dấu phẩy và chấm phân cách hàng nghìn/thập phân."""
    return re.sub(r"[.,]", "", n.rstrip(".,"))


def unsupported_numbers(answer: str, contexts: list[str]) -> list[str]:
    """Tìm các con số xuất hiện trong câu trả lời nhưng không có trong bất kỳ đoạn ngữ cảnh nào."""
    ans = re.sub(r"\[\d+\]", "", answer)  # bỏ số thứ tự trích dẫn [1], [2]
    # Bỏ số thứ tự danh sách hoặc tiêu đề Markdown đầu dòng: ví dụ "1.", "2.", "### 1.", "**1.**", "* 1.", "- 1.", "1)"
    ans = re.sub(r"(?m)^\s*(?:#{1,6}\s+|(?:[-*•]\s+)?(?:\*\*)?)\d+[\.)](?:\*\*)?\s*", "", ans)
    ctx_nums = {_norm(x) for c in contexts for x in _NUM_RE.findall(c)}
    bad = []
    for x in _NUM_RE.findall(ans):
        n = _norm(x)
        if n and n not in ctx_nums:
            bad.append(x.rstrip(".,"))
    return sorted(set(bad))


def verify_claim_faithfulness(answer: str, contexts: list[str]) -> dict[str, Any]:
    """Kiểm tra độ trung thực của các khẳng định theo chuẩn Claim-Level Verification:
    - Đối chiếu câu chứa trích dẫn [i] với ngữ cảnh tương ứng chunk i.
    - Phát hiện các khẳng định có số liệu hoặc chế tài bị đặt ngoài nguồn.
    """
    if not answer or not contexts:
        return {
            "faithfulness_score": 1.0,
            "supported_claims": [],
            "unsupported_claims": [],
            "faithfulness_valid": True,
        }

    # Tách các câu hoàn chỉnh
    sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", answer) if len(s.strip()) > 10]
    total_claims = 0
    supported = []
    unsupported = []

    for s in sentences:
        citations = [int(m.group(1)) for m in _CITATION_RE.finditer(s)]
        if not citations:
            continue
        total_claims += 1
        s_clean = re.sub(r"\[\d+\]", "", s).strip().lower()
        # Trích xuất các từ khóa ngữ nghĩa (> 3 ký tự)
        words = set(re.findall(r"\b\w{3,}\b", s_clean))
        
        # Kiểm tra mức độ giao thoa từ khóa với các chunk được trích dẫn
        matched = False
        for c_idx in citations:
            if 1 <= c_idx <= len(contexts):
                ctx_lower = contexts[c_idx - 1].lower()
                overlap = [w for w in words if w in ctx_lower]
                # Nếu có từ 3 từ khóa hoặc > 30% từ khóa xuất hiện trong chunk
                if len(overlap) >= 3 or (words and len(overlap) / len(words) >= 0.3):
                    matched = True
                    break
        if matched:
            supported.append(s[:100])
        else:
            unsupported.append(s[:100])

    score = 1.0
    if total_claims > 0:
        score = round(len(supported) / total_claims, 3)

    return {
        "faithfulness_score": score,
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "faithfulness_valid": len(unsupported) == 0 or score >= 0.7,
    }


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
    - NO_EVIDENCE: Không có tài liệu hoặc hệ thống từ chối hoàn toàn không dẫn chứng.
    - INSUFFICIENT: Có tài liệu nhưng không chứa thông tin cụ thể mà người dùng hỏi.
    - PARTIAL: Tài liệu chỉ hỗ trợ một phần yêu cầu, phần còn lại chưa có thông tin.
    - SUFFICIENT: Tài liệu có đủ căn cứ để trả lời trực tiếp câu hỏi.
    """
    if not chunks:
        return "NO_EVIDENCE"

    cit_info = validate_citations(answer, len(chunks))
    has_citations = cit_info["has_citations"]

    if refused and not has_citations:
        return "NO_EVIDENCE"

    ans_lower = answer.strip().lower()
    if ans_lower.startswith(_REFUSE_START) and not has_citations:
        return "NO_EVIDENCE"

    has_missing_indicator = bool(_MISSING_INFO_RE.search(ans_lower))

    if has_missing_indicator:
        if has_citations:
            return "PARTIAL"
        return "INSUFFICIENT"

    if not has_citations and len(chunks) > 0:
        return "INSUFFICIENT"

    return "SUFFICIENT"


def verify_claims(answer: str, contexts: list[str]) -> dict[str, Any]:
    """Kiểm tra độ chuẩn xác của các khẳng định (Claim-Level Verification - Task E):
    - Phát hiện các khẳng định tuyệt đối nguy hiểm (như khẳng định chắc chắn bị cấm thi) mà không nêu điều kiện.
    - Phát hiện các chế tài nặng không xuất hiện trong ngữ cảnh tài liệu trích xuất.
    """
    warnings: list[str] = []
    unqualified: list[str] = []

    ans_clean = answer.strip()
    if not ans_clean or ans_clean.lower().startswith(_REFUSE_START):
        return {
            "valid": True,
            "warnings": [],
            "unqualified_claims": [],
        }

    # 1. Bắt lỗi khẳng định tuyệt đối thiếu điều kiện bảo vệ
    for p in _UNQUALIFIED_PATTERNS:
        if p.search(ans_clean):
            if not _QUALIFIER_RE.search(ans_clean):
                unqualified.append(p.pattern)
                warnings.append("Khẳng định tuyệt đối chưa nêu điều kiện kích hoạt (ví dụ: không có lý do chính đáng)")

    # 2. Bắt lỗi chế tài nặng không có trong nguồn
    ctx_text = " ".join(contexts).lower()
    for term in _HEAVY_TERMS:
        if term in ans_clean.lower() and term not in ctx_text:
            warnings.append(f"Chế tài nặng '{term}' không có trong tài liệu trích xuất")

    return {
        "valid": len(warnings) == 0,
        "warnings": sorted(set(warnings)),
        "unqualified_claims": unqualified,
    }


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
    - Kiểm chứng khẳng định (Claim-Level Verification)
    - Tạo danh sách nhãn hiển thị chính xác (badges)
    """
    contexts = [c.get("text", "") for c in chunks] if chunks else []
    bad_numbers = unsupported_numbers(answer, contexts) if not refused and contexts else []
    cit_info = validate_citations(answer, len(chunks))
    claim_info = verify_claims(answer, contexts) if not refused and contexts else {"valid": True, "warnings": []}
    faithfulness_info = verify_claim_faithfulness(answer, contexts) if not refused and contexts else {
        "faithfulness_score": 1.0,
        "supported_claims": [],
        "unsupported_claims": [],
        "faithfulness_valid": True,
    }
    
    sufficiency = determine_sufficiency(
        question=question,
        answer=answer,
        chunks=chunks,
        refused=refused,
        refuse_reason=refuse_reason,
    )

    badges: list[str] = []

    if sufficiency == "NO_EVIDENCE":
        badges.append("Chưa đủ bằng chứng để kết luận")
    elif sufficiency == "INSUFFICIENT":
        badges.append("Chưa đủ bằng chứng để kết luận")
    elif sufficiency == "PARTIAL":
        if cit_info["has_citations"]:
            badges.append("Có trích dẫn nguồn")
        badges.append("Chưa đủ bằng chứng để kết luận (Một phần)")
        if not claim_info["valid"]:
            badges.append("Cần đối chiếu điều kiện áp dụng")
        if bad_numbers:
            badges.append(f"Số liệu chưa rõ nguồn: {', '.join(bad_numbers)}")
    elif sufficiency == "SUFFICIENT":
        if cit_info["has_citations"]:
            badges.append("Có trích dẫn nguồn")
        if cit_info["citations_valid"] and not bad_numbers and claim_info["valid"]:
            badges.append("Đã đối chiếu nguồn cho các khẳng định")
        else:
            if not claim_info["valid"]:
                badges.append("Cần đối chiếu điều kiện áp dụng")
            if bad_numbers:
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
        "claim_valid": claim_info["valid"],
        "claim_warnings": claim_info["warnings"],
        "faithfulness_score": faithfulness_info["faithfulness_score"],
        "faithfulness_valid": faithfulness_info["faithfulness_valid"],
        "supported_claims": faithfulness_info["supported_claims"],
        "unsupported_claims": faithfulness_info["unsupported_claims"],
        "badges": badges,
    }
