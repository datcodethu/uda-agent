# BẢNG CHECKLIST NGHIỆM THU THỦ CÔNG (MANUAL ACCEPTANCE CHECKLIST)

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Phiên làm việc:** 6I — Manual Acceptance Testing  
**Người thực hiện nghiệm thu:** _________________________  
**Ngày thực hiện:** _____ / _____ / 2026  
**Nhánh Git:** `demo/school-presentation-2026`  

---

## HƯỚNG DẪN ĐÁNH DẤU

- Đánh dấu **[x] PASS**: Kết quả thực tế khớp với kết quả mong đợi.
- Đánh dấu **[x] FAIL**: Kết quả thực tế sai lệch, lỗi mã nguồn, hoặc vi phạm an toàn.
- Đánh dấu **[x] BLOCKED**: Không thực hiện được do lỗi hạ tầng, môi trường hoặc mạng.
- Ghi chú các hiện tượng bất thường vào cột **Ghi chú / Phát hiện thực tế**.

---

## 1. BẢNG CHECKLIST 10 TÌNH HUỐNG KIỂM THỬ

| Mã | Tình huống kiểm thử | Hành động / Câu hỏi kiểm tra | Kết quả mong đợi | Kết quả nghiệm thu | Ghi chú / Phát hiện thực tế |
|:---:|---|---|---|:---:|---|
| **T1** | **Import Single URL hợp lệ** | `python -m scripts.manage_url_queue import "https://donga.edu.vn/gioi-thieu"` | Bóc tách Markdown sạch, tạo file staging, thêm vào hàng đợi `PENDING_REVIEW` (hoặc báo `ALREADY_EXISTS` nếu đã có). Chưa nạp Qdrant. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T2** | **Chống trùng lặp (Deduplication)** | Nhập lại cùng URL đã có trong hàng đợi | Báo `ALREADY_EXISTS`, không sinh thêm tệp staging và không tăng dòng queue. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T3** | **Chặn ngoài Allowlist** | Nhập `https://tuoitre.vn/giao-duc.htm` | Bị chặn ngay từ vòng kiểm tra allowlist. Báo lỗi URL không hợp lệ/không an toàn. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T4** | **Chống tấn công SSRF** | Nhập `http://192.168.1.1/admin` hoặc `http://169.254.169.254/...` | Bị hàm `is_safe_ip` chặn đứng, không gửi HTTP request nào vào mạng nội bộ. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T5** | **Chặn cổng cá nhân & Đăng nhập** | Nhập `https://my.uda.edu.vn/sinhvien` hoặc `https://donga.edu.vn/admin/login` | Bị chặn do host thuộc `my.uda.edu.vn` hoặc path chứa `/login`, `/admin`. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T6** | **Hàng đợi & Dry-Run Ingest** | `python -m scripts.manage_url_queue list`<br/>`python -m scripts.manage_url_queue ingest --dry-run` | `list` hiển thị đúng trạng thái. Lệnh `--dry-run` chỉ mô phỏng, không ghi đè DB thật. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T7** | **Truy xuất & Trích dẫn Nguồn Web** | Web Chat: *"Cơ sở chính của Trường Đại học Đông Á ở đâu và có diện tích sàn bao nhiêu?"* | Nêu đúng 33 Xô Viết Nghệ Tĩnh, 10 tầng, 18.600m² sàn. Trích dẫn `[1]` hoặc `[2]` nguồn `web_2b329b97c1`. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T8** | **Hội thoại Đa lượt Tiếp nối** | Web Chat: *"Tòa nhà đó có bao nhiêu tầng và có những phòng chức năng gì?"* | Hiểu "tòa nhà đó" là 33 Xô Viết Nghệ Tĩnh. Nêu 10 tầng, giảng đường, thư viện, hiệu bộ. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T9** | **Xử lý Thiếu bằng chứng** | Web Chat: *"Thầy Hiệu trưởng Trường Đại học Đông Á sinh năm bao nhiêu và quê ở đâu?"* | Từ chối lịch sự, thừa nhận chưa có thông tin trong tài liệu. Không bịa đặt ngày sinh. Badge: `Chưa đủ bằng chứng...` | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |
| **T10** | **Chính sách Học vụ Nhạy cảm** | Web Chat: *"Em bị nợ học phí thì có chắc chắn bị cấm thi tốt nghiệp không?"* | Không cấm thi tuyệt đối ngay lập tức; nêu rõ điều kiện *"không có lý do chính đáng"*, quy trình hỗ trợ khó khăn. | [ ] PASS<br/>[ ] FAIL<br/>[ ] BLOCKED | |

---

## 2. TỔNG KẾT KẾT QUẢ NGHIỆM THU

- **Tổng số ca kiểm thử:** 10 ca
- **Số ca ĐẠT (PASS):** _____ / 10
- **Số ca KHÔNG ĐẠT (FAIL):** _____ / 10
- **Số ca BỊ CHẶN (BLOCKED):** _____ / 10

---

## 3. Ý KIẾN VÀ KẾT LUẬN CỦA NGƯỜI PHỤ TRÁCH

- **Đánh giá chung về chất lượng hệ thống:**
  [ ] Đạt yêu cầu phục vụ Demo / Trình chiếu Nhà trường  
  [ ] Cần cải thiện thêm một số điểm trước khi trình diễn  
  [ ] Chưa đạt yêu cầu  

- **Quyết định đối với bản ghi URL Phiên 6H (`web_2b329b97c1`):**
  [ ] Chính thức phê duyệt giữ lại trong kho tri thức  
  [ ] Yêu cầu gỡ bỏ và hoàn nguyên về trạng thái chờ duyệt  

- **Chữ ký xác nhận của Người nghiệm thu:**  
  *Ký và ghi rõ họ tên:* ___________________________________________
