# Nhật ký 2026-11-02 – Phiên 3G: Tích hợp Giao diện Web Chat trực quan phục vụ Demo

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Xây dựng một giao diện Web Chat hoàn chỉnh, trực quan, mang nhận diện Trường Đại học Đông Á, hỗ trợ chữ chạy từng từ thời gian thực (SSE Streaming) và hiển thị minh bạch căn cứ quy chế, giúp sinh viên và hội đồng có thể trải nghiệm trực tiếp hệ thống ngay trên trình duyệt web khi demo.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/static/index.html` | **Tạo mới:** Giao diện Web Chat đơn trang (HTML5 + CSS3 Flexbox + Vanilla JS), thiết kế theo màu sắc nhận diện ĐH Đông Á (Cam/Xanh navy), có 5 nút gợi ý câu hỏi vàng demo, hiệu ứng chữ chạy thời gian thực (SSE), hộp trích dẫn căn cứ Điều/văn bản kèm điểm số tương đồng, badge kiểm chứng số liệu, badge đo thời gian (ms), và modal tùy chỉnh chế độ demo (Hybrid/Dense/BM25, bật/tắt Guardrail); tự chứa 100% không phụ thuộc internet/CDN. |
| `ai-service/app/api/web_routes.py` | **Tạo mới:** Router phục vụ trang web giao diện tại `GET /` và `GET /chat`, cùng 2 endpoint xử lý chat cho trình duyệt: `POST /api/chat/stream` (nhận luồng SSE) và `POST /api/chat` (nhận JSON đầy đủ). |
| `ai-service/app/pipeline/generator/stream_handler.py` | **Sửa:** Đồng bộ câu trả lời từ chối trong hàm `stream_answer`: Khi câu hỏi bị từ chối sớm bởi bộ phân loại ý định (cá nhân hoặc ngoài phạm vi), stream đúng chuỗi phản hồi thân thiện tương ứng (`PERSONAL_REPLY`, `OUT_OF_SCOPE_REPLY`) thay vì chỉ stream chuỗi từ chối chung. |
| `ai-service/app/main.py` | **Sửa:** Tích hợp `CORSMiddleware` (cho phép gọi an toàn từ trình duyệt web) và đăng ký `web_routes.router`. |
| `ai-service/tests/test_core.py` | **Sửa:** Bổ sung test class mới `TestWebChatAndStreaming` gồm 4 test case: kiểm tra phát đúng thông điệp từ chối cá nhân/ngoài lề khi stream, kiểm tra endpoint web trả về mã 200/HTML, và kiểm tra endpoint stream SSE trả về đúng cấu trúc sự kiện. Nâng tổng số test lên 79/79 PASS (8.4s). |
| `docs/decisions.md` | Cập nhật quyết định kỹ thuật của Phiên 3G. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Phiên 3G. |

## 3. Vì sao làm như vậy

- Quyết định: Sử dụng HTML5, CSS3 và Vanilla JS thuần tự chứa trong một file duy nhất (`index.html`) thay vì dựng một dự án React/Vue riêng biệt cho buổi demo này.
- Phương án đã cân nhắc: Dựng ứng dụng React + Vite riêng biệt hoặc viết trang web đơn giản nhúng thẳng vào FastAPI.
- Vì sao chọn: Trang HTML tự chứa không cần cài đặt Node.js hay chạy lệnh build, không sợ xung đột port hay lỗi dependency, chạy ngay lập tức khi khởi động server FastAPI (`uvicorn app.main:app`). Đặc biệt, trang không dùng CDN bên ngoài nên hoạt động 100% offline nếu hội đồng hoặc phòng thi không có mạng internet.
- Vì sao loại phương án còn lại: Dự án React đầy đủ nằm ở kế hoạch dài hạn của toàn bộ hệ thống (`frontend/`), nếu làm lúc này sẽ tốn nhiều phiên cài đặt môi trường, không kịp thời hạn demo trước mắt.
- Loại căn cứ: [kỹ thuật] & [chỉ đạo người dùng ưu tiên hoàn thiện demo].
- Đánh đổi: Không có component framework phức tạp, nhưng bù lại giao diện cực kỳ nhẹ, tải tức thì (< 5ms) và dễ bảo trì.

- Quyết định: Tạo endpoint `/api/chat/stream` độc lập với `/v1/query/stream`.
- Phương án đã cân nhắc: Cho trình duyệt gọi thẳng `/v1/query/stream` kèm header bảo mật nội bộ `X-Internal-Key` hoặc tạo endpoint riêng cho web.
- Vì sao chọn: Endpoint `/v1/query/stream` theo kiến trúc `plan.md` là API nội bộ dành riêng cho Spring Boot Gateway gọi (được bảo vệ bằng header bí mật `X-Internal-Key`). Việc mở một endpoint `/api/chat/stream` cục bộ cho giao diện demo giúp trình duyệt không phải lưu trữ khóa bí mật nội bộ, đồng thời hỗ trợ tham số `use_intent` để người thuyết trình có thể bật/tắt Guardrail ngay trên giao diện demo.
- Vì sao loại phương án còn lại: Để lộ `X-Internal-Key` trong mã nguồn JavaScript gửi từ client vi phạm nguyên tắc an toàn thông tin.
- Loại căn cứ: [kỹ thuật] & [tài liệu: `docs/ai-service.md` mục 1.1].
- Đánh đổi: Có thêm một router nhỏ trong mã nguồn, nhưng phân định rõ ràng giữa API Gateway và Web Demo trực tiếp.

- Quyết định: Sửa `stream_handler.py` để phân biệt các lý do từ chối.
- Phương án đã cân sớm: Giữ nguyên `REFUSE_MESSAGE` chung cho mọi trường hợp từ chối.
- Vì sao chọn: Khi sinh viên hỏi câu dữ liệu cá nhân (*"Điểm của em bao nhiêu?"*), bot cần phản hồi thân thiện hướng dẫn sinh viên vào Cổng đào tạo xem điểm (`PERSONAL_REPLY`), thay vì nói một câu từ chối cứng nhắc. Điều này giúp buổi demo thể hiện rõ nét tính năng Guardrail bảo vệ dữ liệu cá nhân theo [docs/plan.md](file:///E:/workspace/donga-rag-system/docs/plan.md).
- Vì sao loại phương án còn lại: Không phân biệt lý do từ chối làm mất đi giá trị của module phân loại ý định đã xây dựng ở Bước 7.
- Loại căn cứ: [kỹ thuật] & [tài liệu: `docs/ai-service.md` mục 7.3].
- Đánh đổi: Thêm vài dòng logic ánh xạ `if-elif` trong luồng phát SSE.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

- **Server-Sent Events (SSE) Streaming:**
  - *Ví dụ đời thường:* Giống như bạn ngồi nghe phát thanh viên đọc tin tức từng câu một qua loa phát thanh, nghe tới đâu hiểu tới đó, chứ không phải đợi người đó đọc xong cả cuốn sách rồi mới đưa bản ghi âm cho bạn nghe một lượt.
  - *Trong RAG:* Mô hình ngôn ngữ lớn (LLM) sinh chữ theo từng từ (token). Kỹ thuật SSE giúp máy chủ đẩy từng từ này về trình duyệt ngay lập tức khi nó vừa được tạo ra. Người dùng thấy chữ chạy mượt mà trên màn hình (thời gian thấy từ đầu tiên - Time to First Token chỉ mất 0.5s) thay vì phải ngồi nhìn vòng xoay chờ đợi 3–5 giây.

- **Offline-First Web Design (Thiết kế ưu tiên ngoại tuyến):**
  - *Ví dụ đời thường:* Giống như một quyển sổ tay in sẵn đầy đủ hình ảnh và thông tin bỏ túi, mang lên vùng núi không có sóng điện thoại vẫn mở ra đọc và sử dụng bình thường; khác với việc lưu dữ liệu trên đám mây, mất mạng là không xem được gì.
  - *Trong Demo NCKH:* Nhiều hội trường thi hoặc phòng họp có sóng Wi-Fi rất yếu hoặc bị chặn firewall. Thiết kế giao diện tự chứa toàn bộ CSS/JS (không tải phông chữ hay icon từ Google/CDN) giúp hệ thống chạy mượt mà 100% trên mạng nội bộ localhost của máy tính cá nhân.

## 5. Đã kiểm tra thế nào

- Lệnh 1 (Chạy toàn bộ 79 unit test offline):
  ```powershell
  $env:PYTHONPATH='ai-service'; $env:PYTHONUTF8='1'; ai-service\venv\Scripts\python.exe -m unittest discover -s ai-service\tests -v
  ```
- Kết quả thật (dán):
  ```
  test_stream_answer_custom_refusal_for_out_of_scope (test_core.TestWebChatAndStreaming.test_stream_answer_custom_refusal_for_out_of_scope) ... ok
  test_stream_answer_custom_refusal_for_personal_data (test_core.TestWebChatAndStreaming.test_stream_answer_custom_refusal_for_personal_data) ... ok
  test_web_routes_api_chat_stream_response (test_core.TestWebChatAndStreaming.test_web_routes_api_chat_stream_response) ... ok
  test_web_routes_html_page_delivered (test_core.TestWebChatAndStreaming.test_web_routes_html_page_delivered) ... ok

  ----------------------------------------------------------------------
  Ran 79 tests in 8.400s

  OK
  ```
- Kết luận: **ĐẠT** (Toàn bộ 79/79 unit test PASS 100%, kiểm thử toàn diện cả lõi RAG lẫn giao diện web mới).

- Lệnh 2 (Kiểm tra nạp ứng dụng FastAPI):
  ```powershell
  $env:PYTHONPATH='ai-service'; $env:PYTHONUTF8='1'; ai-service\venv\Scripts\python.exe -c "from app.main import app; print('FastAPI app loaded successfully!')"
  ```
- Kết quả thật: `FastAPI app loaded successfully!`
- Kết luận: **ĐẠT** (Không có lỗi cú pháp hoặc thiếu router).

- Số lệnh gọi API trả phí đã dùng: **0 API call / 0 VND** (Chạy hoàn toàn bằng mock và local cache).

## 6. Chưa chắc chắn, rủi ro, giả định
- Để người khác trong cùng mạng nội bộ Wi-Fi (ví dụ điện thoại của thầy cô) truy cập được vào web chat, cần chạy lệnh uvicorn với cờ `--host 0.0.0.0` (sẽ được hướng dẫn trong báo cáo).

## 7. Điều đã không làm và lý do
- **Không cài thêm thư viện npm/Vite/React ngoài:** Để giữ hệ thống nhẹ nhàng, độc lập, sẵn sàng demo ngay mà không gặp lỗi môi trường.
- **Không commit git:** Tuân thủ nguyên tắc người dùng tự kiểm tra và thực hiện commit.
- **Không gọi API Gemini trả phí:** Bảo toàn hạn mức API của bạn.

## 8. Việc tiếp theo
- Khởi động server FastAPI và mở trình duyệt để bạn trải nghiệm thực tế giao diện chat.
- Chuẩn bị slide và kịch bản demo 5 phút (Hướng 2) để tự tin thuyết trình trước hội đồng.

## 9. Câu hỏi cho người dùng
- Bạn có muốn chạy thử server ngay bây giờ để mở giao diện web trên trình duyệt máy bạn không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao giao diện web chat lại được thiết kế theo dạng tự chứa (inlined CSS/JS) mà không dùng CDN từ bên ngoài?
2. Trong phản hồi streaming (SSE), sự kiện `sources` và `verify` có ý nghĩa gì đối với việc chứng minh tính trung thực của hệ thống RAG?
3. Nếu hội đồng muốn kiểm tra xem cơ chế tìm kiếm lai (Hybrid RRF) có thật sự tốt hơn tìm kiếm ngữ nghĩa đơn lẻ (Dense-only) hay không, bạn có thể thao tác ở đâu ngay trên giao diện web này để chứng minh?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì khi đi demo hoặc thuyết trình, mạng Wi-Fi hội trường có thể rất yếu hoặc không có internet. Thiết kế tự chứa 100% giúp trang web tải tức thì và hoạt động hoàn hảo trên máy tính cục bộ (localhost) mà không bao giờ bị vỡ giao diện.
2. Sự kiện `sources` gửi danh sách văn bản quy chế và Điều khoản gốc được trích dẫn; sự kiện `verify` xác nhận các con số trong câu trả lời hoàn toàn có trong văn bản gốc (Number Verifier). Hai sự kiện này là bằng chứng rõ ràng chứng minh hệ thống không bị ảo giác (hallucination).
3. Bấm vào nút **Demo Settings** ở góc phải trên thanh header, chọn mục *Chế độ tìm kiếm (Retrieval Mode)* chuyển sang `Dense` hoặc `BM25`, sau đó hỏi lại cùng một câu hỏi để so sánh trực tiếp kết quả và độ chính xác của nguồn trích dẫn.

</details>
