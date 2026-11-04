"""Bộ giải quyết ngữ cảnh hội thoại (Conversation Context Resolver) cho RAG.

Nhận diện 6 mẫu hành vi:
1. Follow-up clarification: "là sao?", "nghĩa là sao?", "ý là gì?", "chưa hiểu", "giải thích dễ hiểu hơn"
2. Example request: "cho ví dụ", "ví dụ cụ thể", "lấy ví dụ"
3. Reference resolution: "cái đó", "quy định này", "nó", "trường hợp này"
4. Topic continuation: "vậy nếu đóng một phần thì sao?", "vậy em cần làm gì?", "hồ sơ gồm những gì?"
5. Topic switching: Chuyển sang chủ đề hoàn toàn mới (ví dụ từ Ngoại ngữ sang Học bổng)
6. Clarification without context: "là sao?" nhưng chưa có lịch sử hội thoại trước
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Literal

ResolutionAction = Literal[
    "REEXPLAIN",
    "EXAMPLE",
    "REWRITE_AND_RETRIEVE",
    "NEW_TOPIC",
    "CLARIFY_NO_CONTEXT",
]


@dataclass
class ContextResolutionResult:
    action: ResolutionAction
    standalone_query: str
    reason: str
    target_concept: str | None = None


# 1. Các mẫu yêu cầu giải thích làm rõ / đơn giản hóa
_REEXPLAIN_PATTERNS = [
    re.compile(r"^(?:(?:nghĩa\s+)?là\s+sao|ý\s+(?:là\s+)?gì|ý\s+bạn\s+là\s+sao|sao\s+ạ)[!\?\.]*$", re.I),
    re.compile(r"^(?:em|mình|tôi)?\s*(?:vẫn\s+)?chưa\s+(?:hiểu|rõ)(?:\s+lắm|\s+ạ)?[!\?\.]*$", re.I),
    re.compile(r"^(?:hãy\s+)?giải\s+thích\s+(?:rõ|kỹ|chi\s+tiết|dễ\s+hiểu)\s+hơn(?:\s+được\s+không|\s+ạ)?[!\?\.]*$", re.I),
    re.compile(r"^(?:nói|viết)\s+(?:rõ|ngắn\s+gọn|dễ\s+hiểu)\s+hơn(?:\s+đi|\s+ạ)?[!\?\.]*$", re.I),
    re.compile(r"^cụ\s+thể\s+(?:hơn\s+)?(?:là\s+sao|như\s+thế\s+nào)[!\?\.]*$", re.I),
    re.compile(r"^(?:tóm\s+tắt|tóm\s+lại)(?:\s+ngắn\s+gọn)?(?:\s+giúp\s+em|\s+ạ)?[!\?\.]*$", re.I),
]

# 2. Các mẫu xin ví dụ minh họa
_EXAMPLE_PATTERNS = [
    re.compile(r"^(?:cho|lấy|nêu)(?:\s+cho\s+em)?\s+ví\s+dụ(?:\s+cụ\s+thể|\s+minh\s+họa)?(?:\s+được\s+không|\s+đi|\s+ạ)?[!\?\.]*$", re.I),
    re.compile(r"^ví\s+dụ\s+(?:cụ\s+thể\s+)?(?:như\s+thế\s+nào|là\s+sao)[!\?\.]*$", re.I),
]

# 3. Các từ tham chiếu đại từ / quy định trước
_REFERENCE_WORDS = re.compile(
    r"\b(cái\s+đó|điều\s+đó|quy\s+định\s+này|chính\s+sách\s+này|trường\s+hợp\s+(?:này|đó)|thủ\s+tục\s+(?:này|đó)|nó)\b",
    re.I,
)

# 4. Các mẫu tiếp nối chủ đề (continuation)
_CONTINUATION_PATTERNS = [
    re.compile(r"^(?:vậy|thế)?\s*(?:nếu|trong\s+trường\s+hợp)\s+.*\s+(?:thì\s+sao|như\s+thế\s+nào)[!\?\.]*$", re.I),
    re.compile(r"^(?:vậy|thế)?\s*(?:thì\s+)?(?:em|mình|sinh\s+viên)\s+cần\s+(?:phải\s+)?(?:làm\s+gì|chuẩn\s+bị\s+gì)[!\?\.]*$", re.I),
    re.compile(r"^(?:còn|thế\s+còn)\s+(?:ngành|khoa|khóa|trường\s+hợp)\s+.*\s+(?:thì\s+sao)[!\?\.]*$", re.I),
    re.compile(r"^(?:thời\s+gian|hạn\s+chót|khi\s+nào|ở\s+đâu|thủ\s+tục\s+gồm\s+gì)[!\?\.]*$", re.I),
]

# Từ khóa phát hiện chủ đề mới độc lập (Topic switching)
_INDEPENDENT_TOPIC_KEYWORDS = [
    "học bổng", "học phí", "kỷ luật", "khen thưởng", "thực tập", "điểm rèn luyện",
    "chuẩn đầu ra", "ngoại ngữ", "thẻ xe", "thư viện", "trang phục", "quân sự", "vay vốn",
]


def resolve_context(
    question: str,
    history: list[dict] | None = None,
    last_topic: str = "",
) -> ContextResolutionResult:
    """Phân giải câu hỏi hiện tại dựa trên lịch sử hội thoại."""
    q = question.strip()
    hist = history or []

    # 1. Trích xuất câu hỏi và câu trả lời trước đó (nếu có)
    last_user_q = ""
    last_assistant_a = ""
    for turn in reversed(hist):
        role = turn.get("role")
        content = turn.get("content", "").strip()
        if role == "assistant" and not last_assistant_a:
            last_assistant_a = content
        elif role == "user" and not last_user_q:
            last_user_q = content
        if last_user_q and last_assistant_a:
            break

    context_topic = last_topic or last_user_q

    # Mẫu 1: Yêu cầu giải thích / làm rõ ("là sao?", "nghĩa là sao?")
    if any(p.search(q) for p in _REEXPLAIN_PATTERNS):
        if not context_topic and not last_assistant_a:
            return ContextResolutionResult(
                action="CLARIFY_NO_CONTEXT",
                standalone_query=q,
                reason="Yêu cầu giải thích nhưng chưa có ngữ cảnh trước đó",
            )
        return ContextResolutionResult(
            action="REEXPLAIN",
            standalone_query=context_topic,
            reason="Yêu cầu giải thích làm rõ câu trả lời trước",
            target_concept=context_topic,
        )

    # Mẫu 2: Xin ví dụ minh họa ("cho ví dụ", "ví dụ như thế nào?")
    if any(p.search(q) for p in _EXAMPLE_PATTERNS):
        if not context_topic and not last_assistant_a:
            return ContextResolutionResult(
                action="CLARIFY_NO_CONTEXT",
                standalone_query=q,
                reason="Xin ví dụ nhưng chưa có ngữ cảnh trước đó",
            )
        return ContextResolutionResult(
            action="EXAMPLE",
            standalone_query=context_topic,
            reason="Yêu cầu đưa ví dụ cho nội dung trước",
            target_concept=context_topic,
        )

    # Mẫu 3: Đổi chủ đề hoàn toàn (Topic Switching)
    # Nếu câu hỏi mới có từ khóa chủ đề độc lập và khác biệt rõ với chủ đề cũ
    if context_topic:
        current_keywords = [kw for kw in _INDEPENDENT_TOPIC_KEYWORDS if kw in q.lower()]
        old_keywords = [kw for kw in _INDEPENDENT_TOPIC_KEYWORDS if kw in context_topic.lower()]
        if current_keywords and not any(kw in old_keywords for kw in current_keywords):
            # Ví dụ câu cũ là ngoại ngữ, câu mới có từ khóa 'học bổng' -> Chuyển chủ đề
            return ContextResolutionResult(
                action="NEW_TOPIC",
                standalone_query=q,
                reason=f"Chuyển chủ đề độc lập sang: {', '.join(current_keywords)}",
            )

    # Mẫu 4: Tham chiếu đại từ ("cái đó", "quy định này", "nó")
    if context_topic and _REFERENCE_WORDS.search(q):
        # Thay thế đại từ hoặc bổ sung chủ đề vào cuối
        rewritten = _REFERENCE_WORDS.sub(f"quy định về {context_topic}", q)
        return ContextResolutionResult(
            action="REWRITE_AND_RETRIEVE",
            standalone_query=rewritten,
            reason="Phân giải đại từ tham chiếu",
            target_concept=context_topic,
        )

    # Mẫu 5: Nối tiếp chủ đề ("vậy nếu đóng một phần thì sao?", "vậy em cần làm gì?")
    if context_topic and (any(p.search(q) for p in _CONTINUATION_PATTERNS) or len(q.split()) <= 6):
        # Kết hợp câu hỏi ngắn với chủ đề trước
        # Ví dụ: "vậy nếu đóng một phần thì sao?" + "Em nợ học phí thì có được thi không?"
        # -> "Em nợ học phí nếu đóng một phần thì có được dự thi không?"
        clean_q = re.sub(r"^(?:vậy|thế)?\s*(?:thì\s+)?", "", q, flags=re.I).strip()
        standalone = f"{context_topic}: {clean_q}"
        return ContextResolutionResult(
            action="REWRITE_AND_RETRIEVE",
            standalone_query=standalone,
            reason="Nối tiếp tình huống câu hỏi trước",
            target_concept=context_topic,
        )

    # Mặc định: Câu hỏi độc lập mới
    return ContextResolutionResult(
        action="NEW_TOPIC",
        standalone_query=q,
        reason="Câu hỏi độc lập thông thường",
    )
