# Tiến độ

| Bước (theo docs/ai-service.md) | Trạng thái | Ghi chú |
|---|---|---|
| Bước 1 | Đạt (3 việc: venv, requirements, test) | 20/20 unit test PASS, môi trường sẵn sàng. Chưa tạo .env và chưa chạy server |
| Bước 3 | Đạt (Đọc file & làm sạch) | Đọc văn bản bằng `pypdf`, chuẩn hóa Unicode NFC, lọc số trang lặp qua `clean_text`. Bỏ qua 15 file PDF scan và 31 file Word (.doc/.docx). |
| Bước 4 | Đạt (Mục 4.1, 4.2, 4.3, 4.5) | Thống nhất status `ACTIVE`/`EXPIRED` ở 6 file; mở rộng `DIEU_RE` hỗ trợ biến thể; 22/22 unit test PASS; xuất preview chunks của 9 tài liệu vào `data/chunk_preview/`. |
| Giai đoạn 1 (Word) | Hoàn thành | Chuyển đổi 19/19 file .doc sang .docx an toàn qua Word COM; loader .docx đọc tuần tự text/table, giữ bảng bố cục 1xN/Nx1 dạng text, bảng dữ liệu thành Markdown; phát hiện lỗi font và hộp văn bản tự động. |
| Giai đoạn 2 (Cắt đoạn) | Hoàn thành | Sửa dứt điểm 5 lỗi cắt đoạn (giữ bảng/lặp header, phân đoạn văn bản/loại bỏ `-x1`, phân biệt câu mở đầu/tiêu đề, cắt ranh giới câu/Khoản có gối đầu 100-150 ký tự, tiền tố `doc_title`); bổ sung kiểm tra thứ tự Điều (cảnh báo mềm); 29/29 unit test PASS. |
