# BÁO CÁO TỔNG KẾT PHIÊN 6H — NOTEBOOKLM-LIKE URL KNOWLEDGE IMPORT & RAG QUALITY IMPROVEMENT

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Thời gian thực hiện:** Ngày 05 tháng 11 năm 2026  
**Nhánh Git:** `demo/school-presentation-2026`  
**Kỹ sư thực hiện:** Antigravity AI Assistant  

---

## 1. MỤC TIÊU PHIÊN LÀM VIỆC

Phiên 6H được thiết kế nhằm giải quyết bài toán cốt lõi đã phát hiện ở Phiên 6F và 6G: **Khoảng cách về độ phong phú và tính linh hoạt nạp tri thức so với Google NotebookLM.**

1. **Nâng cấp trải nghiệm nạp tri thức:** Xây dựng tính năng nạp tài liệu từ URL đơn giản như NotebookLM: Quản trị viên chỉ cần dán một URL $\rightarrow$ hệ thống tự động bóc tách Markdown sạch, giữ bảng và cấu trúc, đưa vào hàng đợi kiểm duyệt an toàn $\rightarrow$ Người có thẩm quyền phê duyệt $\rightarrow$ Nạp tăng dần (Incremental Ingest) vào Qdrant và BM25 $\rightarrow$ Chatbot trả lời và trích dẫn trực tiếp nguồn web.
2. **Tuân thủ kỷ luật NCKH & Bảo mật:**
   - Bảo đảm nguyên tắc **Default-Deny** (không tự động nạp thẳng dữ liệu web vào cơ sở dữ liệu chính khi chưa có sự phê duyệt).
   - Thiết lập hàng rào chống SSRF (chặn IP private RFC 1918, loopback, cloud metadata) và chặn thu thập cổng sinh viên cá nhân (`my.uda.edu.vn`, `/login`).
   - Phân loại tài liệu web thành `tai_lieu_tong_hop` (web_page), tuyệt đối không xếp vào `quy_che_truong`.
3. **Thẩm định nguồn 7 tài liệu DOCX:** Rà soát nguồn gốc, hiệu lực, và tính khả thi của 7 tài liệu DOCX phát hiện ở Phiên 6F.

---

## 2. KẾT QUẢ ĐẠT ĐƯỢC

### 2.1. Về Kiến trúc và Mã nguồn mới
- **Module `URLImporter` (`ai-service/app/pipeline/importer/url_importer.py`):**
  * Hỗ trợ 2 chế độ: **Single URL Import** và **Website Discovery** (có giới hạn depth, max_urls, delay).
  * Bộ phòng thủ an toàn `is_safe_url` & `is_safe_ip`: Ngăn chặn SSRF, kiểm tra Domain Allowlist (`donga.edu.vn`, `uda.edu.vn`), chặn cổng sinh viên cá nhân `my.uda.edu.vn`.
  * Bộ trích xuất HTML sang Markdown: Giữ nguyên cấu trúc Tiêu đề, Bảng Markdown (`| col | col |`), Danh sách gạch đầu dòng và tự động bóc tách liên kết đính kèm (`.pdf`, `.docx`).
  * Xử lý tối ưu cho nền tảng DotNetNuke/ASP.NET của Trường ĐH Đông Á (giữ container `<form>` để không làm mất nội dung trang web).
- **Module Nạp tăng dần `IncrementalIndexer` (`ai-service/app/pipeline/importer/incremental_indexer.py`):**
  * Đọc hàng đợi `data/url_approval_queue.csv`.
  * Chỉ nạp các bản ghi có trạng thái `APPROVED`.
  * Gọi `index_service.index_document` để phân đoạn cấu trúc, nạp vector vào Qdrant Local và xây dựng lại BM25.
- **Công cụ dòng lệnh CLI (`ai-service/scripts/manage_url_queue.py`):**
  * Cung cấp các thao tác: `list`, `import <url>`, `approve <url_id>`, `reject <url_id>`, `ingest [--dry-run]`.
- **Mở rộng Metadata Chunk (`ai-service/app/pipeline/index_service.py`):**
  * Bổ sung các trường `source_url`, `crawled_at`, `content_type` vào `ALLOWED_CHUNK_META_KEYS` để hỗ trợ trích dẫn liên kết URL.

### 2.2. Về Kết quả Thực nghiệm Thực tế (Live Verification)
- **Nạp thử nghiệm thành công URL:** `https://donga.edu.vn/gioi-thieu` (Mã định danh: `URL-20261105-2B329B`, 1.367 ký tự Markdown, 2 chunks).
- **So sánh Đối chứng Câu hỏi kiểm nghiệm:**
  * *Câu hỏi 1 (Địa chỉ cơ sở chính và diện tích sàn):*
    - Trước khi nạp: Chatbot trả lời `INSUFFICIENT` và thừa nhận không có số liệu diện tích sàn.
    - Sau khi nạp: Chatbot trả lời chính xác `18.600m²`, 10 tầng tại `33 Xô Viết Nghệ Tĩnh`, trích dẫn `[1]` nguồn `web_2b329b97c1`, đánh giá `SUFFICIENT`.
  * *Câu hỏi 2 (Tầm nhìn phát triển của trường đến 2030/2050):*
    - Chatbot tổng hợp hoàn hảo giữa nguồn web `web_2b329b97c1` và quy chế đào tạo `2023_8_29_8_50_20c`, trích dẫn `[1, 3]`, đánh giá `SUFFICIENT`.
- **Kiểm thử Hồi quy (Regression Tests):**
  * Chạy toàn bộ test suite: **159/159 test PASS** (1 skipped do offline không có API key) trong 5.945 giây.
  * Bộ test chuyên biệt `test_url_importer.py`: **7/7 test PASS**.
  * 10 tài liệu quy chế cốt lõi (103 chunks) giữ nguyên tính toàn vẹn 100%.

### 2.3. Về Thẩm định 7 Tài liệu DOCX (Kế thừa TASK A)
- Đã thẩm định và lập báo cáo chi tiết tại `evaluation/reference_guided_6h/approval_review.md`.
- Kết quả: 6/7 tài liệu đủ điều kiện trình phê duyệt (các văn bản hướng dẫn thủ tục trực tuyến, biểu mẫu hoãn NVQS, chuyển ngành, rút học phần, đổi lớp, xin vắng thi); 1/7 tài liệu tạm hoãn (quyết định tín dụng HSSV năm 2007 do mức vay đã cũ so với QĐ 05/2022/QĐ-TTg).

---

## 3. DANH MỤC HỒ SƠ BÀN GIAO PHIÊN 6H

1. **Mã nguồn tính năng mới:**
   - `ai-service/app/pipeline/importer/__init__.py`
   - `ai-service/app/pipeline/importer/url_importer.py`
   - `ai-service/app/pipeline/importer/incremental_indexer.py`
   - `ai-service/scripts/manage_url_queue.py`
   - `ai-service/tests/test_url_importer.py`
2. **Cập nhật mã nguồn hiện hữu:**
   - `ai-service/app/pipeline/index_service.py` (Mở rộng `ALLOWED_CHUNK_META_KEYS`)
   - `ai-service/data/url_approval_queue.csv` (Bản ghi hàng đợi nạp URL)
   - `ai-service/data/staging_url_imports/2b329b97c189971f.md` (Tệp Staging đã duyệt và nạp)
3. **Bộ tài liệu báo cáo kiểm nghiệm (`evaluation/reference_guided_6h/`):**
   - `url_import_architecture.md`: Tài liệu thiết kế kiến trúc toàn diện và luồng dữ liệu bảo mật.
   - `url_approval_queue.csv`: Nhật ký hàng đợi phê duyệt URL.
   - `indexing_report.md`: Báo cáo thực nghiệm nạp tăng dần và kết quả đối chứng Before/After.
   - `regression_test_report.md`: Báo cáo kiểm thử hồi quy 159/159 ca test.
   - `approval_review.md`: Báo cáo thẩm định nguồn 7 tài liệu DOCX.
   - `summary.md`: Báo cáo tổng kết phiên 6H.

---

## 4. BƯỚC TIẾP THEO ĐỀ XUẤT

1. **Tích hợp Web UI:** Mở rộng giao diện Web Chat Demo (hoặc bảng điều khiển Admin) bằng cách tạo API endpoint `POST /api/admin/urls/import` và `POST /api/admin/urls/approve` dựa trên các hàm của `url_importer.py` và `incremental_indexer.py`.
2. **Khám phá các phân vùng học vụ:** Sử dụng chế độ Discovery hoặc nạp Single URL cho các trang cẩm nang sinh viên, hướng dẫn học phí, học bổng từ website ĐH Đông Á để chuẩn bị cho đợt Re-benchmark 75 câu khảo sát.
3. **Trình cấp có thẩm quyền:** Xem xét phê duyệt 6 tài liệu DOCX hướng dẫn thủ tục trực tuyến để nạp vào kho tri thức phục vụ sinh viên.
