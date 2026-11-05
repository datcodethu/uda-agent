# Nhật ký 2026-11-04 – Phiên 6A: Chuẩn bị Đông Á Advanced RAG Chatbot cho Buổi Demo Nhà trường

## 1. Mục tiêu
Chuẩn bị hệ thống chatbot hỏi đáp học vụ Đông Á đạt trạng thái DEMO READY để trình diễn trước nhà trường; tạo nhánh Git riêng `demo/school-presentation-2026`; sao lưu snapshot an toàn dữ liệu kho; rà soát và phân loại 4 nhóm dữ liệu (A, B, C, D); kiểm thử toàn diện backend, RAG pipeline và giao diện Web Chat; ánh xạ danh sách 43 câu hỏi thực tế của sinh viên để chuẩn bị kịch bản demo an toàn, có trích dẫn nguồn chuẩn xác.

## 2. Đã làm gì
| File / Thư mục | Thay đổi |
|---|---|
| Git Branch | Tạo và chuyển sang nhánh riêng `demo/school-presentation-2026`, bảo toàn nguyên vẹn working tree và nhánh `main`. |
| `ai-service/data/backup_pre_demo_20261104/` | Tạo bản sao lưu snapshot đầy đủ dữ liệu: `docs_registry.csv`, `chunks.jsonl`, `cau_hoi_thu.csv` và `qdrant_local/`. |
| Bảng kiểm kê dữ liệu (Inventory) | Lập bảng kiểm kê 60 tài liệu trong registry và 50 trang crawler, phân loại thành 4 nhóm A, B, C, D rõ ràng. |
| `docs/todo.md` | Bổ sung Mục 4 (Tồn đọng dữ liệu và kiểm thử): chuẩn hóa `loai` tài liệu Markdown, rà soát nhãn benchmark. |
| `docs/progress.md` | Cập nhật tiến độ Phiên 6A đạt trạng thái DEMO READY cho buổi demo nhà trường. |
| `docs/decisions.md` | Ghi nhận quyết định phân nhóm dữ liệu kiểm kê (A/B/C/D) và chiến lược demo an toàn. |

## 3. Vì sao làm như vậy
- Quyết định: Tạo nhánh Git `demo/school-presentation-2026` và sao lưu snapshot vật lý thư mục dữ liệu trước mọi thao tác.
  - Phương án đã cân nhắc: Thao tác trực tiếp trên nhánh `main` và kho hiện tại.
  - Vì sao chọn: Đảm bảo cách ly tuyệt đối mã nguồn và cấu hình demo với nhánh chính của đề tài NCKH; có bản backup khôi phục tức thì nếu xảy ra sự cố.
  - Loại căn cứ: [kỹ thuật] / Yêu cầu người dùng tại TASK B.
  - Đánh đổi: Tốn thêm ~2MB dung lượng lưu trữ snapshot backup.

- Quyết định: Phân tách minh bạch Nhóm A (Quy chế chính thức) và Nhóm B (Tài liệu hướng dẫn tổng hợp) thay vì coi tất cả là quy chế trường.
  - Phương án đã cân nhắc: Giữ nguyên gán nhãn `loai=quy_che_truong` cho 5 file Markdown.
  - Vì sao chọn: Bảo đảm tính trung thực học thuật và pháp lý khi trình bày trước lãnh đạo nhà trường; chatbot trích dẫn rõ nguồn nào là Quyết định Hiệu trưởng, nguồn nào là Hướng dẫn sinh viên.
  - Loại căn cứ: [tài liệu: GEMINI.md, docs/decisions.md] & TASK C2.

- Quyết định: Giữ 50 trang crawler và 59 liên kết đính kèm ở trạng thái chờ duyệt (Nhóm C), không tự ý nạp.
  - Phương án đã cân nhắc: Viết script nạp hàng loạt trang crawler vào kho để tăng số lượng tài liệu demo.
  - Vì sao loại: Vi phạm nguyên tắc Default-Deny và quy tắc an toàn nội dung crawler chưa tin cậy trong GEMINI.md.
  - Loại căn cứ: [tài liệu: GEMINI.md, docs/agent-workflow.md].

## 4. Khái niệm mới
- **Data Provenance & Lineage (Nguồn gốc và Phả hệ Dữ liệu):** Trong một hệ thống RAG phục vụ môi trường giáo dục đại học, mỗi câu trả lời của mô hình ngôn ngữ phải truy xuất ngược được về đúng cấp độ văn bản: Văn bản quy phạm (Hiệu trưởng ký ban hành), Sổ tay hướng dẫn học vụ (Phòng/Ban ban hành), hay Tài liệu tham khảo. Việc gắn nhãn sai lệch nguồn gốc sẽ dẫn đến rủi ro pháp lý khi sinh viên viện dẫn thông tin.

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Tạo snapshot sao lưu):
  `ai-service\venv\Scripts\python.exe scratch\create_backup.py`
  - Kết quả thật: Đã sao lưu thành công `docs_registry.csv`, `chunks.jsonl`, `cau_hoi_thu.csv` và `qdrant_local/` vào `ai-service/data/backup_pre_demo_20261104/`.
- Lệnh 2 (Kiểm thử đơn vị toàn hệ thống):
  `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả thật: `Ran 94 tests in 16.297s -> OK (skipped=1)`. 100% test hệ thống PASS.
- Lệnh 3 (Kiểm tra API Backend & Web UI):
  Chạy `test_client.py` gọi FastAPI TestClient:
  - `GET /` -> Status 200 (HTML giao diện Web Chat 26,969 bytes).
  - `GET /chat` -> Status 200 (HTML giao diện Web Chat 26,969 bytes).
  - `POST /api/chat/stream` -> Status 200 (Streaming SSE phản hồi chuẩn).
- Lệnh 4 (Kiểm tra kho vector & BM25):
  - Qdrant Local collection `donga_regulations`: 10 tài liệu, 103 chunks, 0 trùng lặp `chunk_id`.
  - BM25 Index: Rebuild thành công 103 chunks.
- Lệnh 5 (Phân tích 43 câu hỏi thực tế của sinh viên qua BM25 offline):
  - 25 câu hỏi trúng trực tiếp văn bản Quy chế chính thức (Nhóm A).
  - 7 câu hỏi trúng tài liệu Hướng dẫn học vụ tổng hợp (Nhóm B).
  - 11 câu hỏi ngoài phạm vi / chưa có văn bản tương ứng (kích hoạt từ chối an toàn).
- Số lệnh gọi API trả phí đã dùng trong phiên: 1 lệnh embedding trong unit test integration.

## 6. Chưa chắc chắn, rủi ro, giả định
- 5 tài liệu Markdown tổng hợp (Nhóm B) giải quyết rất tốt các câu hỏi thường gặp của sinh viên (học lại, năm nhất, mất thẻ xe, thư viện, trang phục). Tuy nhiên khi demo trước lãnh đạo nhà trường, cần nhấn mạnh đây là nhóm tri thức "Hướng dẫn thực hành sinh viên" để phân biệt với "Quy chế đào tạo chính thức".
- Quota API Gemini: Cần sử dụng model `gemini-flash-lite-latest` đã được cấu hình sẵn để tránh chạm trần rate limit.

## 7. Điều đã không làm và lý do
- Không tự ý nạp 50 trang web cào được: Tuân thủ nghiêm ngặt quyền phê duyệt của người dùng.
- Không tự ý git commit hoặc push: Tuân thủ quy định để người dùng trực tiếp kiểm tra và commit.
- Không bịa nhãn benchmark khoa học: Giữ nguyên tính khách quan của bộ dữ liệu nghiên cứu.

## 8. Việc tiếp theo
1. Người dùng khởi động backend và mở trình duyệt trải nghiệm Web Chat.
2. Thử nghiệm demo với 5–10 câu hỏi tiêu biểu đã được phân loại nguồn.
3. Người dùng rà soát danh sách 50 trang crawler chờ duyệt nếu muốn nạp thêm vào kho.
