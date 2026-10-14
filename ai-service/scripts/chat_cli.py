"""Giao diện dòng lệnh hỏi đáp (Chat CLI) với bộ nhớ ngữ cảnh hội thoại.

Chạy:
    python -m scripts.chat_cli [--mode hybrid|dense|bm25]
Gõ '/q' để thoát.
"""
from __future__ import annotations
import argparse
import io
import sys
from app.core.config import settings
from app.pipeline import rag_pipeline
from app.pipeline.retrieval.bm25_search import bm25_index


def run_chat_cli(mode: str = "hybrid") -> None:
    # 1. Tự động rebuild BM25 index khi khởi động
    bm25_index.rebuild()

    print("=" * 70)
    print(" TRỢ LÝ HỎI ĐÁP QUY CHẾ ĐẠI HỌC ĐÔNG Á (CHAT CLI)")
    print(f" Chế độ: {mode} | Model: {settings.gemini_chat_model} (Provider: {settings.llm_provider})")
    print(" Gõ câu hỏi của bạn và nhấn Enter. Gõ '/q' để thoát.")
    print("=" * 70 + "\n")

    # Quản lý tối đa 4 lượt gần nhất (1 lượt = 1 user + 1 assistant)
    history: list[dict] = []
    max_history_turns = 4

    while True:
        try:
            user_input = input("Sinh viên: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã thoát phiên chat.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/q", "/quit", "exit", "quit"):
            print("Tạm biệt bạn! Chúc bạn học tập tốt tại Đại học Đông Á.")
            break

        res = rag_pipeline.answer(user_input, history=history, mode=mode)

        print("\n" + "-" * 70)
        print(f"Trợ lý: {res['answer']}\n")

        # Danh sách nguồn trích dẫn (tên văn bản, Điều, điểm)
        if res.get("sources"):
            print("Nguồn trích dẫn:")
            for s in res["sources"]:
                dieu_str = s.get("dieu") or "(không Điều)"
                print(f"  [{s['index']}] {s['doc_name']} | {dieu_str} | điểm: {s.get('score', 0):.3f}")
        else:
            print("Nguồn trích dẫn: (không có)")

        # Cờ số lạ (unsupported_numbers)
        unsupported = res.get("unsupported_numbers")
        unsupported_str = ", ".join(unsupported) if unsupported else "không"
        print(f"Số lạ (unsupported): {unsupported_str}")

        # Lý do từ chối nếu có
        if res.get("refused"):
            print(f"Trạng thái: TỪ CHỐI (Lý do: {res.get('refuse_reason') or 'ngoài phạm vi'})")

        # Thời gian truy xuất và tổng cộng
        timing = res.get("timing", {})
        retrieval_ms = res.get("retrieval_ms", timing.get("retrieval_ms", 0))
        latency_ms = res.get("latency_ms", timing.get("total_ms", 0))
        print(f"Thời gian: truy xuất {retrieval_ms} ms | tổng cộng {latency_ms} ms")
        print("-" * 70 + "\n")

        # Cập nhật lịch sử (cắt giữ tối đa 4 lượt = 8 messages)
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": res["answer"]})
        if len(history) > max_history_turns * 2:
            history = history[-(max_history_turns * 2):]


def main(argv: list[str] | None = None) -> None:
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, io.UnsupportedOperation):
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="Chat CLI hỏi đáp quy chế ĐH Đông Á.")
    parser.add_argument("--mode", default="hybrid", choices=["dense", "bm25", "hybrid"], help="Chế độ tìm kiếm")
    args = parser.parse_args(argv)
    run_chat_cli(mode=args.mode)


if __name__ == "__main__":
    main()
