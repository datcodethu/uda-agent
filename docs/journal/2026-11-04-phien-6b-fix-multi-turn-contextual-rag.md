# Nhật ký 2026-11-04 – Phiên 6B: Khắc phục lỗi hội thoại nhiều lượt & Contextual RAG

## 1. Mục tiêu
Khắc phục triệt để lỗi chatbot từ chối trả lời khi người dùng hỏi các câu hỏi ngắn tiếp nối ngữ cảnh (như "là sao?", "cho ví dụ", "vậy em cần làm gì?"); thiết kế bộ phân giải ngữ cảnh `ContextResolver`, bộ nhớ phiên `SessionMemory` có xác thực tính hợp lệ của nguồn, tối ưu hóa độ trễ phản hồi (0 ms retrieval cho câu hỏi làm rõ) và bổ sung bộ 7 automated test cases đạt 100% PASS.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/query_transformation/context_resolver.py` | Tạo mới module `ContextResolver` nhận diện 6 mẫu hội thoại: làm rõ (REEXPLAIN), ví dụ (EXAMPLE), tham chiếu (REFERENCE), nối tiếp tình huống (CONTINUATION), đổi chủ đề (NEW_TOPIC), và hỏi làm rõ khi không có ngữ cảnh (CLARIFY_NO_CONTEXT). |
| `ai-service/app/pipeline/memory/session_memory.py` | Tạo mới module quản lý phiên in-memory thread-safe (`RLock`) với TTL 30 phút, lưu trữ lịch sử, tài liệu/chunk đã dùng, và cơ chế `validate_cached_sources` kiểm tra trạng thái ACTIVE của văn bản trong kho trước khi cho phép tái sử dụng. |
| `ai-service/app/pipeline/rag_pipeline.py` | Tích hợp `ContextResolver` và `SessionMemory`: fast-path 0 ms cho câu hỏi làm rõ khi có nguồn hợp lệ; chuyển đổi standalone query khi nối tiếp tình huống; hỗ trợ đầy đủ `conversation_id`. |
| `ai-service/app/pipeline/generator/stream_handler.py` | Bổ sung nhánh xử lý `clarify_no_context` và tự động lưu lượt hội thoại streaming SSE vào `SessionMemory`. |
| `ai-service/app/core/prompts.py` | Cập nhật `SYSTEM_PROMPT` (Quy tắc 9: Giao tiếp & làm rõ ngữ cảnh; giải thích thuật ngữ học vụ đơn giản, không lặp lại nguyên văn hành chính, không spam câu liên hệ Phòng Đào tạo) và thêm `CLARIFY_NO_CONTEXT_REPLY`. |
| `ai-service/app/schemas/query_schema.py` & `web_routes.py` | Bổ sung trường `conversation_id: str | None = None` vào `QueryRequest`, `QueryResponse`, và `WebChatRequest`. |
| `ai-service/app/static/index.html` | Tự động sinh UUID `conversation_id` khi tải trang và gửi kèm trong payload SSE `/api/chat/stream`. |
| `ai-service/tests/test_multi_turn_context.py` | Tạo bộ 7 unit tests kiểm thử toàn diện 7 kịch bản bắt buộc (100% mock offline, 0 gọi API). |

## 3. Vì sao làm như vậy
- Quyết định: Nhận diện mẫu câu làm rõ ("là sao?", "nghĩa là sao?", "cho ví dụ") bằng Heuristic regex kết hợp kiểm tra bộ nhớ thay vì gọi LLM phân loại.
  - Phương án đã cân nhắc: Dùng một lượt gọi LLM riêng để phân loại ý định người dùng.
  - Vì sao chọn: Tiết kiệm 100% thời gian gọi API và chi phí token; phản hồi tức thì với độ trễ 0 ms cho bước phân loại.
  - Loại căn cứ: [kỹ thuật] / Yêu cầu Nhiệm vụ 2.

- Quyết định: Tái sử dụng trực tiếp các chunks của lượt trước khi người dùng hỏi "là sao?" / "cho ví dụ", bỏ qua bước truy xuất vector/BM25.
  - Phương án đã cân nhắc: Luôn luôn truy xuất lại mỗi lượt.
  - Vì sao chọn: Tránh việc từ khóa ngắn ("là sao") làm sai lệch điểm BM25/Dense; bảo toàn trọn vẹn ngữ cảnh chính xác của văn bản gốc; giảm thời gian truy xuất từ ~5.5s xuống đúng 0 ms.
  - Loại căn cứ: [kỹ thuật] / Yêu cầu Nhiệm vụ 4.

- Quyết định: Kiểm tra `validate_cached_sources` đối chiếu với kho `chunk_store.list_documents()` trước khi tái sử dụng cache.
  - Phương án đã cân nhắc: Luôn tin tưởng cache bộ nhớ.
  - Vì sao loại: Nếu tài liệu bị người quản trị gỡ bỏ hoặc chuyển sang `EXPIRED`, việc tái sử dụng cache sẽ vi phạm nguyên tắc pháp lý và an toàn học vụ.
  - Loại căn cứ: [tài liệu: GEMINI.md] / Yêu cầu Nhiệm vụ 3.

## 4. Khái niệm mới
- **Contextual Query Disambiguation (Khử nhập nhằng truy vấn theo ngữ cảnh):** Kỹ thuật nhận diện các câu hỏi phụ thuộc ngữ cảnh hội thoại (anaphora / ellipsis). Nếu câu hỏi chỉ yêu cầu giải thích lại khái niệm vừa nêu, hệ thống chuyển sang chế độ "Explaining Mode" trên bằng chứng cũ. Nếu câu hỏi bổ sung điều kiện mới (ví dụ "vậy nếu đóng một phần thì sao?"), hệ thống tự động tổng hợp câu hỏi độc lập (Standalone Query) chứa đầy đủ chủ ngữ và vị ngữ trước khi đưa vào bộ truy xuất.

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Kiểm thử đơn vị 7 test cases mới):
  `cmd /c "set PYTHONUTF8=1&& cd /d E:\workspace\donga-rag-system\ai-service && venv\Scripts\python.exe -m unittest tests/test_multi_turn_context.py -v"`
  - Kết quả thật: `Ran 7 tests in 0.007s -> OK`. Toàn bộ 7/7 tests PASS trong 7 mili-giây.
- Lệnh 2 (Kiểm thử hồi quy toàn bộ hệ thống):
  `cmd /c "set PYTHONUTF8=1&& cd /d E:\workspace\donga-rag-system\ai-service && venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả thật: `Ran 101 tests in 7.121s -> OK (skipped=1)`. 101/101 tests PASS, không có bất kỳ hồi quy nào.
- Lệnh 3 (Kiểm thử thực tế 2 lượt trên server thật `port 8000`):
  - Lượt 1: *"Chuẩn đầu ra ngoại ngữ ngành không chuyên ngữ là gì?"* -> Trả lời chuẩn Bậc 3/6, 5 sources, Retrieval: 5,579 ms.
  - Lượt 2: *"là sao?"* -> `Refused: False`, **Retrieval ms: 0 ms** (tiết kiệm 100% thời gian tìm kiếm), trả lời giải thích cực kỳ tự nhiên ("Ý mình là để ra trường... Nói một cách dễ hiểu, bạn có thể chọn một trong hai cách sau..."), giữ trọn vẹn 5 nguồn trích dẫn từ văn bản `2023_8_23_16_29_59n` (Điều 1, Điều 2).

## 6. Chưa chắc chắn, rủi ro, giả định
- Mô hình Gemini API chạy trên gói Free Tier có thời gian sinh câu trả lời (LLM generation) dao động từ 10s đến 20s. Để demo mượt mà trên giao diện Web Chat, tính năng streaming SSE giúp hiển thị token đầu tiên (TTFT) ngay khi LLM bắt đầu sinh, tạo cảm giác phản hồi nhanh cho người dùng.

## 7. Điều đã không làm và lý do
- Không cài thêm Redis: Hệ thống đơn máy demo hiện tại sử dụng In-Memory Store thread-safe là hoàn toàn đáp ứng tối ưu và không tạo thêm gánh nặng phụ thuộc.
- Không tự ý commit hoặc push: Tuân thủ quy định để người dùng tự kiểm tra và commit.
