# BÁO CÁO KIỂM THỬ HỒI QUY TOÀN DIỆN (REGRESSION TEST REPORT)

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Phiên:** 6H — NotebookLM-Like URL Knowledge Import  
**Ngày kiểm thử:** 05/11/2026  
**Lệnh thực thi:** `venv\Scripts\python.exe -m unittest discover -s tests -v`  

---

## 1. MỤC TIÊU VÀ NGUYÊN TẮC KIỂM THỬ

1. **Bảo đảm không suy thoái (Zero Regression):** Mọi module đã phát triển từ Phiên 1 đến Phiên 6G (tiền xử lý câu hỏi, phân đoạn cấu trúc, truy xuất hybrid, đánh giá an toàn, prompts sinh câu trả lời) phải tiếp tục hoạt động chính xác 100%.
2. **Kiểm thử đơn vị chuyên biệt cho URL Import:** Kiểm tra toàn diện các lớp phòng thủ an toàn (SSRF, Allowlist, Anti-Portal, Deduplication, HTML-to-Markdown parsing, Approval State Machine).
3. **Tuân thủ quy tắc NCKH:** Kết quả ghi nhận là kết quả thực tế từ bộ kiểm thử, không can thiệp, không bỏ qua các ca kiểm thử thất bại.

---

## 2. KẾT QUẢ TỔNG QUAN

```text
Ran 160 tests in 5.945s

OK (skipped=1)
```

| Chỉ số | Kết quả | Trạng thái |
|---|:---:|:---:|
| **Tổng số ca kiểm thử (Total Tests)** | 160 | - |
| **Số ca kiểm thử thành công (Passed)** | 159 | ✅ 100% |
| **Số ca kiểm thử thất bại (Failures)** | 0 | ✅ Hoàn hảo |
| **Số ca kiểm thử phát sinh lỗi (Errors)** | 0 | ✅ Hoàn hảo |
| **Số ca tạm bỏ qua (Skipped)** | 1 | ℹ️ Cần API key (offline run) |
| **Thời gian thực thi** | 5.945s | ⚡ Tốc độ cao |

---

## 3. CHI TIẾT CÁC CA KIỂM THỬ MODULE `URLImporter`

Module kiểm thử mới được triển khai tại `ai-service/tests/test_url_importer.py` gồm 7 test cases độc lập:

### 3.1. Danh sách kiểm thử chi tiết

1. **`test_is_safe_url_allowlist` (PASS)**
   - *Mục tiêu:* Kiểm tra cơ chế lọc tên miền cho phép (Domain Allowlist).
   - *Đầu vào kiểm thử:*
     * `https://donga.edu.vn/gioi-thieu` $\rightarrow$ Hợp lệ (True).
     * `https://subdomain.uda.edu.vn/page` $\rightarrow$ Hợp lệ (True).
     * `https://evil.com` $\rightarrow$ Bị chặn (False).
     * `https://phishing-donga.edu.vn` $\rightarrow$ Bị chặn (False).
     * `ftp://donga.edu.vn` $\rightarrow$ Bị chặn scheme không phải HTTP/HTTPS (False).

2. **`test_is_safe_url_ssrf_and_ip` (PASS)**
   - *Mục tiêu:* Kiểm tra hàng rào chống tấn công SSRF vào mạng nội bộ và Cloud Metadata.
   - *Đầu vào kiểm thử:*
     * `http://127.0.0.1/admin` $\rightarrow$ Bị chặn (Loopback).
     * `http://192.168.1.1/router` $\rightarrow$ Bị chặn (RFC 1918 Private IP).
     * `http://10.0.0.1/internal` $\rightarrow$ Bị chặn (RFC 1918 Private IP).
     * `http://169.254.169.254/latest/meta-data` $\rightarrow$ Bị chặn (Link-local Cloud Metadata).

3. **`test_is_safe_url_blocks_login_and_student_portal` (PASS)**
   - *Mục tiêu:* Kiểm tra tính năng ngăn chặn truy cập cổng cá nhân sinh viên hoặc trang đăng nhập.
   - *Đầu vào kiểm thử:*
     * `https://my.uda.edu.vn/sinhvien/diem` $\rightarrow$ Bị chặn (Host thuộc cổng thông tin cá nhân).
     * `https://donga.edu.vn/admin/login` $\rightarrow$ Bị chặn (Đường dẫn đăng nhập).
     * `https://donga.edu.vn/dang-nhap` $\rightarrow$ Bị chặn (Đường dẫn xác thực).

4. **`test_clean_html_to_markdown` (PASS)**
   - *Mục tiêu:* Kiểm tra năng lực chuyển đổi HTML sang Markdown giữ nguyên định dạng bảng, tiêu đề, danh sách và liên kết tài liệu.
   - *Kết quả bóc tách:*
     * Giữ nguyên cấu trúc `# Tiêu đề chính`, `## Mục 1`.
     * Giữ nguyên bảng HTML dưới dạng bảng Markdown: `| Mã HP | Tên học phần |`, `| --- | --- |`.
     * Bóc tách chính xác các đường link file đính kèm: `bieu_mau_1.docx`, `huong_dan.pdf`.
     * Loại bỏ sạch sẽ các thẻ rác (`<script>`, `<nav>`, `<footer>`).

5. **`test_import_single_url_success` (PASS)**
   - *Mục tiêu:* Kiểm tra chu trình nạp một URL giả lập vào Staging và Hàng đợi duyệt.
   - *Kết quả:*
     * Tệp staging `.md` được tạo đúng mã băm SHA-256.
     * Metadata tiêu đề và nội dung được trích xuất đầy đủ.
     * Bản ghi trong `url_approval_queue.csv` được tạo với trạng thái `EXTRACTED`.

6. **`test_import_single_url_deduplication` (PASS)**
   - *Mục tiêu:* Kiểm tra cơ chế chống trùng lặp dữ liệu (Deduplication).
   - *Kết quả:*
     * Nạp lại cùng 1 URL trả về kết quả `ALREADY_EXISTS`.
     * Không sinh thêm tệp staging dư thừa và không ghi đúp bản ghi trong queue CSV.

7. **`test_approval_and_dry_run_ingest` (PASS)**
   - *Mục tiêu:* Kiểm tra cỗ máy trạng thái (State Machine) và cơ chế Ingestion chế độ chạy thử (Dry-run).
   - *Kết quả:*
     * Chuyển trạng thái từ `EXTRACTED` $\rightarrow$ `APPROVED` chính xác.
     * Lệnh `dry_run=True` mô phỏng nạp thành công mà không làm thay đổi Vector DB thực tế.

---

## 4. BẢO ĐẢM TÍNH TOÀN VẸN CỦA CÁC MODULE HIỆN HỮU

| Bộ Test Suite | Số ca | Kết quả | Ghi chú |
|---|:---:|:---:|---|
| `tests/test_retrieval.py` | 14 | 14/14 PASS | Hybrid search Qdrant + BM25 hoạt động bình thường |
| `tests/test_structural_chunker.py` | 12 | 12/12 PASS | Giữ nguyên quy tắc cắt theo Điều khoản |
| `tests/test_prompts.py` | 10 | 10/10 PASS | System prompt và template câu trả lời ổn định |
| `tests/test_query_preprocessor.py` | 16 | 16/16 PASS | Nhận diện tiền đề sai, thực thể, viết tắt chuẩn |
| `tests/test_safety_eval.py` | 8 | 8/8 PASS | Đánh giá an toàn và từ chối ngoài phạm vi |
| `tests/test_ingest.py` | 15 | 15/15 PASS | Pipeline ingest tài liệu nội bộ không bị ảnh hưởng |
| `tests/test_index_service.py` | 11 | 11/11 PASS | Đã mở rộng `ALLOWED_CHUNK_META_KEYS` an toàn |
| `tests/test_docker_start.py` | 9 | 9/9 PASS | Khởi tạo môi trường Docker tương thích |
| `tests/test_url_importer.py` | 7 | 7/7 PASS | Module mới hoàn toàn đạt chuẩn |
| Các test khác (config, utils, api) | 58 | 57/58 PASS (1 skipped) | Giữ vững độ ổn định toàn hệ thống |

---

## 5. KẾT LUẬN

Hệ thống đạt trạng thái **Zero-Regression**. Việc bổ sung tính năng thu thập tri thức qua URL theo phong cách NotebookLM được tích hợp một cách độc lập, an toàn và hoàn toàn tương thích với hạ tầng RAG hiện tại.
