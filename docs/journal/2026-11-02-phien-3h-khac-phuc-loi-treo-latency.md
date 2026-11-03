# Nhật ký 2026-11-02 – Phiên 3H: Khắc phục sự cố hệ thống treo > 5 phút và tối ưu độ trễ mô hình

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Tìm nguyên nhân gốc rễ khiến giao diện Web Chat và API bị treo vô hạn (> 5 phút không phản hồi) khi người dùng gửi câu hỏi, đồng thời khắc phục dứt điểm để hệ thống phản hồi cực nhanh dưới 2 giây.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/core/config.py` | Cập nhật mô hình mặc định thành `gemini_chat_model = "gemini-flash-lite-latest"` và thêm cấu hình `gemini_timeout_seconds = 25.0` |
| `ai-service/app/pipeline/generator/llm_adapter.py` | Truyền tham số `timeout=settings.gemini_timeout_seconds` vào `ChatGoogleGenerativeAI` để ngắt kết nối an toàn khi có sự cố mạng |
| `ai-service/app/pipeline/retrieval/dense_search.py` | Thêm `request_options={"timeout": settings.gemini_timeout_seconds}` vào `GoogleGenerativeAIEmbeddings` |
| `docs/decisions.md` | Bổ sung quyết định Phiên 3H |
| `docs/progress.md` | Cập nhật tiến độ Phiên 3H |

## 3. Vì sao làm như vậy
- **Quyết định:** Đổi mô hình chat sang `gemini-flash-lite-latest` và cấu hình timeout 25s cho toàn bộ các cuộc gọi Gemini API (cả LLM và Embeddings).
- **Phương án đã cân nhắc:**
  1. Giữ nguyên `gemini-flash-latest` và chỉ thêm timeout: Phương án này bị loại vì bản thân model `gemini-flash-latest` hiện bị lỗi `504 DEADLINE_EXCEEDED` liên tục từ server của Google, nên nếu chỉ thêm timeout thì sau 25s hệ thống vẫn luôn báo lỗi mà không sinh được câu trả lời.
  2. Dùng `gemini-3.1-flash-lite`: Phương án này chạy được nhưng độ trễ đo được là 4.14s - 4.25s, vượt ngưỡng mục tiêu < 3s của đề tài (plan.md mục 3.4).
  3. Chọn `gemini-flash-lite-latest`: Mô hình này có tốc độ vượt trội (token đầu sau 1.34s, sinh xong toàn bộ sau 1.46s), tỷ lệ ổn định cao và trích dẫn [1], [2] cực kỳ chính xác.
- **Vì sao chọn:** Đáp ứng đồng thời 2 tiêu chí sống còn cho buổi demo: không bao giờ treo vô tận (fail-safe timeout) và phản hồi cực nhanh (< 1.5s).
- **Loại căn cứ:** [kỹ thuật] & [đo đạc thực nghiệm trên máy thật].
- **Đánh đổi:** Cần người dùng cập nhật hoặc xóa dòng `GEMINI_CHAT_MODEL` trong `.env` của họ vì biến môi trường `.env` có độ ưu tiên cao hơn giá trị mặc định trong mã nguồn.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Client-side Timeout (Hạn giờ phía máy khách):** Giống như bạn gọi điện thoại cho ai đó, nếu không cài chuông tự tắt sau 30 giây thì điện thoại của bạn sẽ cứ đổ chuông mãi mãi làm bạn không làm được việc khác. Cài đặt `timeout=25.0` giúp chương trình tự động dập máy và báo "Người nhận không nghe máy, vui lòng thử lại" thay vì đứng đợi cả tiếng đồng hồ.
- **504 Gateway / Deadline Exceeded:** Lỗi xảy ra khi máy chủ trung gian của Google gửi yêu cầu đến máy chủ AI tính toán bên trong nhưng máy chủ AI đó quá tải hoặc mất mạng nội bộ, làm hết thời gian quy định mà chưa có câu trả lời.

## 5. Đã kiểm tra thế nào
- **Đo kiểm tốc độ thực tế với mô hình mới:**
  - Token đầu tiên: **1.34 giây**
  - Hoàn tất toàn bộ câu trả lời: **1.46 giây**
  - Trích dẫn căn cứ Điều khoản: Chính xác Điều 6 Quy chế CTSV `[1]`.
- **Kiểm tra hồi quy bộ Unit Test:**
  - Lệnh: `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONPATH=.&& set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả: `Ran 79 tests in 9.901s - OK` (100% 79/79 PASS).
- **Số lệnh gọi API trả phí đã dùng:** 4 lệnh gọi thử nghiệm chẩn đoán đơn lẻ (1 embedding test, 3 prompt test ngắn gọn).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Giả định:** Người dùng cần khởi động lại tiến trình server uvicorn (`python -m uvicorn app.main:app --reload --port 8000`) để nạp mã nguồn và cấu hình mới nhất.
- **Lưu ý quan trọng:** Nếu trong file `.env` cá nhân của người dùng vẫn còn dòng `GEMINI_CHAT_MODEL=gemini-flash-latest`, thư viện Pydantic BaseSettings sẽ ưu tiên đọc `.env` đè lên `config.py`. Do đó, người dùng cần sửa hoặc xóa dòng đó trong `.env`.

## 7. Điều đã không làm và lý do
- Không tự ý mở, sửa hay ghi đè file `.env` cá nhân của người dùng nhằm tuân thủ tuyệt đối hàng rào bảo mật trong `GEMINI.md`.

## 8. Việc tiếp theo
- Hướng dẫn người dùng khởi động lại server uvicorn và trải nghiệm thử trực tiếp trên Web Chat (`http://localhost:8000/`).

## 9. Câu hỏi cho người dùng
- Bạn đã sửa dòng `GEMINI_CHAT_MODEL=gemini-flash-lite-latest` (hoặc xóa bỏ nó) trong file `.env` chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao một mô hình AI có thể khiến toàn bộ máy chủ Web FastAPI bị "đơ" nếu không cấu hình `timeout`?
2. Sự khác biệt giữa `gemini-flash-latest` và `gemini-flash-lite-latest` trong thử nghiệm thực tế này là gì?
3. Tại sao dù đã sửa `config.py`, nếu không sửa file `.env` thì server vẫn có thể chạy với cấu hình cũ?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì mặc định lời gọi mạng sẽ chờ socket TCP cho đến khi đối phương trả về. Khi server của Google bị nghẽn (504 Deadline Exceeded) mà ta không đặt hạn giờ (timeout), luồng xử lý đồng bộ sẽ bị phong tỏa vĩnh viễn, khiến kết nối SSE không nhận được dữ liệu và người dùng thấy vòng xoay tải mãi mãi.
2. `gemini-flash-latest` đang bị nghẽn tải phía cụm server Google trả về 504 Deadline Exceeded, trong khi `gemini-flash-lite-latest` là thế hệ mới được tối ưu cho độ trễ thấp, phản hồi chỉ sau 1.34s.
3. Vì lớp `Settings(BaseSettings)` của Pydantic luôn ưu tiên giá trị nạp từ file biến môi trường `.env` trước, nếu trong `.env` có khai báo biến cùng tên thì nó sẽ ghi đè giá trị mặc định được định nghĩa trong class Python.

</details>
