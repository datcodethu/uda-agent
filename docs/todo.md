# Việc phát sinh ngoài phạm vi (chưa làm)

## 1. Giai đoạn 2: Cải tiến bộ cắt đoạn (Làm sau khi nghiệm thu Giai đoạn 1)
Cần tái hiện từng lỗi trên file `2023_8_23_16_29_59n.pdf` trước khi sửa:
- [x] **Lỗi a (Bảng bị làm phẳng):** Các bảng bị mất dòng tiêu đề cột và trải dài thành dòng đơn lẻ (đoạn 8, 10, 13, 14, 16). Sửa: Giữ bảng trọn vẹn trong một đoạn; nếu bảng quá dài thì tách theo từng nhóm hàng và lặp lại dòng tiêu đề (header).
- [x] **Lỗi b (Trùng số Điều giữa Quyết định & Quy định):** Văn bản có "Quyết định" (Điều 1-3) và "Quy định kèm theo" (Điều 1-8) trùng số Điều bị đánh hậu tố `-x1`. Sửa: Khi gặp "Điều 1" đứng đầu dòng và số Điều quay về 1 thì mở phần văn bản mới; bổ sung trường `phan_van_ban` (`quyet_dinh` / `quy_dinh_kem_theo` / `phu_luc`) vào metadata và mã đoạn, loại bỏ hậu tố `-x1`.
- [x] **Lỗi c (Lấy nhầm câu đầu làm tiêu đề):** Các Điều không có tiêu đề bị cắt cứng ~80 ký tự câu đầu làm tiêu đề (đoạn 3, 4, 5). Sửa: Tiêu đề phải ở đầu dòng, ngắn (< 120 ký tự), không kết thúc bằng dấu chấm; nếu không thỏa mãn thì để `(Không)` và giữ nguyên câu trong thân bài.
- [x] **Lỗi d (Cắt giữa câu, thiếu gối đầu):** Cắt theo độ dài 1200 ký tự cắt cụt giữa câu và không có overlap (đoạn 1 sang 2, 7 sang 8). Sửa: Ưu tiên cắt theo Khoản ("1.", "2.") hoặc ranh giới câu, gối đầu 100-150 ký tự, không cắt giữa bảng.
- [x] **Lỗi e (Tiền tố đoạn là tên file):** Đổi tiền tố sang `doc_title` lấy từ `docs_registry.csv` hoặc trích xuất từ trang đầu tài liệu.

## 2. Xử lý tồn đọng dữ liệu
- [ ] **15 file PDF scan:** Đang chờ xin lại bản gốc Word/PDF có chữ từ Phòng Đào tạo (chưa chạy OCR).
- [ ] **Tài liệu loại trừ khỏi kho chatbot:** 
  - 2 file Luật Nhà nước: `2026_10_6_10_15_26g.pdf` (An ninh mạng) và `2026_10_6_10_16_15ộ.pdf` (ATGT) -> Gắn nhãn `category=phap_luat`, chưa nạp vào kho.
  - Các file biểu mẫu đơn từ sinh viên.
  - File nghi lỗi font: `2026_10_6_10_18_43c.pdf`.
