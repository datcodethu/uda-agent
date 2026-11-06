# Nhật ký 2026-11-05 – Phiên 6H: NotebookLM-Like URL Knowledge Import & RAG Quality Improvement

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)

Nâng cấp hệ thống Advanced RAG để người quản trị có thể nạp tri thức từ một đường link web dễ dàng và an toàn như Google NotebookLM (dán link $\rightarrow$ bóc tách Markdown $\rightarrow$ duyệt $\rightarrow$ nạp vector $\rightarrow$ chatbot trích dẫn trực tiếp nguồn web), đồng thời bảo đảm an toàn thông tin, không làm hỏng kho quy chế đào tạo cốt lõi có sẵn.

---

## 2. Đã làm gì

| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/importer/__init__.py` | Khởi tạo module importer, xuất các hàm chính: `URLImporter`, `import_single_url`, `discover_website`, `is_safe_url`. |
| `ai-service/app/pipeline/importer/url_importer.py` | Hiện thực module nạp URL: phòng chống SSRF (`is_safe_ip`, `is_safe_url`), kiểm tra Allowlist (`donga.edu.vn`, `uda.edu.vn`), chặn cổng sinh viên cá nhân `my.uda.edu.vn`, bóc tách HTML sang Markdown giữ bảng/tiêu đề/danh sách và liên kết đính kèm; xử lý tối ưu cho nền tảng ASP.NET. |
| `ai-service/app/pipeline/importer/incremental_indexer.py` | Hiện thực module nạp tăng dần: đọc hàng đợi `url_approval_queue.csv`, xử lý các mục `APPROVED`, gọi `index_service.index_document` để phân đoạn cấu trúc, nạp Qdrant và tái dựng BM25. |
| `ai-service/app/pipeline/index_service.py` | Bổ sung `source_url`, `crawled_at`, `content_type` vào `ALLOWED_CHUNK_META_KEYS` để lưu trữ và hiển thị nguồn web. |
| `ai-service/scripts/manage_url_queue.py` | CLI quản trị hàng đợi nạp URL hỗ trợ các lệnh: `list`, `import`, `approve`, `reject`, `ingest` (hỗ trợ cờ `--dry-run`). |
| `ai-service/tests/test_url_importer.py` | Bộ kiểm thử đơn vị chuyên biệt gồm 7 test cases kiểm tra allowlist, SSRF, chống crawl cổng cá nhân, bóc tách bảng Markdown, deduplication và approval workflow. |
| `ai-service/data/url_approval_queue.csv` | Bảng hàng đợi phê duyệt 5 trạng thái quản lý các bản ghi URL nhập vào. |
| `ai-service/data/staging_url_imports/2b329b97c189971f.md` | Tệp Markdown bóc tách từ trang giới thiệu trường (`https://donga.edu.vn/gioi-thieu`). |
| `evaluation/reference_guided_6h/url_import_architecture.md` | Tài liệu thiết kế kiến trúc toàn diện của module URL Knowledge Import. |
| `evaluation/reference_guided_6h/indexing_report.md` | Báo cáo thực nghiệm nạp tăng dần và kết quả đối chứng Trước/Sau khi nạp URL `URL-20261105-2B329B`. |
| `evaluation/reference_guided_6h/regression_test_report.md` | Báo cáo kiểm thử hồi quy 159/159 test PASS (1 skipped), 0 lỗi phát sinh. |
| `evaluation/reference_guided_6h/approval_review.md` | Báo cáo thẩm định nguồn 7 tài liệu DOCX học vụ (kế thừa từ kiểm toán Phiên 6G). |
| `evaluation/reference_guided_6h/summary.md` | Báo cáo tổng kết điều hành Phiên 6H. |
| `docs/decisions.md` | Ghi nhận Quyết định 44 về kiến trúc URL Knowledge Import và chu trình phê duyệt 5 trạng thái. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Phiên 6H. |
| `docs/todo.md` | Đóng các hạng mục Phiên 6H và phác thảo kế hoạch Phiên 6I. |

---

## 3. Vì sao làm như vậy

### Khối 1: Hàng rào phòng thủ SSRF và Domain Allowlist độc lập
- **Quyết định:** Viết hàm `is_safe_url` và `is_safe_ip` kiểm tra chặt chẽ DNS resolution, dải IP RFC 1918, loopback, cloud metadata (169.254.169.254) và chỉ cho phép miền con của `donga.edu.vn` và `uda.edu.vn`.
- **Phương án đã cân nhắc:** Cho phép nạp bất kỳ URL nào trên Internet hoặc dùng thư viện crawler bên ngoài tự do.
- **Vì sao chọn:** Ngăn chặn tuyệt đối lỗ hổng Server-Side Request Forgery (SSRF). Kẻ tấn công hoặc người dùng vô tình nhập đường link nội bộ (như `http://192.168.1.1` hay `http://localhost:8000`) có thể biến server chatbot thành công cụ tấn công dò quét mạng trường hoặc rò rỉ token.
- **Vì sao loại phương án còn lại:** Cho phép cào tự do mọi trang web sẽ biến chatbot thành nguồn phát tán thông tin sai lệch ngoài tầm kiểm soát của nhà trường.
- **Loại căn cứ:** [kỹ thuật] & [tiêu chuẩn an toàn thông tin OWASP Top 10].
- **Đánh đổi:** Không thể nạp nhanh các bài báo từ báo Giáo dục hoặc Bộ GD&ĐT nếu tên miền nằm ngoài `donga.edu.vn`/`uda.edu.vn` (cần thêm miền vào allowlist nếu sau này có nhu cầu).

### Khối 2: Tối ưu bộ bóc tách HTML-to-Markdown cho nền tảng ASP.NET
- **Quyết định:** Không xóa thẻ `<form>` khi lọc sạch DOM, chỉ loại bỏ các thẻ rác (`<script>`, `<style>`, `<nav>`, `<footer>`, `<input>`, `<button>`).
- **Phương án đã cân nhắc:** Dùng bộ parser thông thường coi thẻ `<form>` là thành phần giao diện và xóa cả cụm `<form>...</form>`.
- **Vì sao chọn:** Cổng thông tin ĐH Đông Á chạy trên DotNetNuke / ASP.NET WebForms, toàn bộ nội dung bài viết và thân trang đều được bọc trong `<form id="aspnetForm">`. Nếu xóa thẻ `<form>`, nội dung trang web sẽ bị xóa trắng hoàn toàn (`CONTENT_EMPTY`).
- **Vì sao loại phương án còn lại:** Khiến crawler không lấy được chữ từ website chính của trường.
- **Loại căn cứ:** [kỹ thuật: phân tích cấu trúc DOM thực tế của donga.edu.vn].
- **Đánh đổi:** Nếu trang web có form khảo sát dài, có thể sót lại một số nhãn trường (đã được khắc phục bằng cách xóa thẻ con `<input>` và `<button>`).

### Khối 3: Cỗ máy trạng thái phê duyệt 5 nấc (Approval Gate)
- **Quyết định:** Mọi URL khi nhập chỉ dừng ở trạng thái `EXTRACTED` hoặc `PENDING_REVIEW` lưu tại `staging_url_imports/`, bắt buộc có lệnh `approve` từ người quản trị mới được chuyển sang `APPROVED` và nạp vào Vector DB.
- **Phương án đã cân nhắc:** Cho phép URL tự động nạp thẳng vào Qdrant ngay khi tải xong (như NotebookLM cá nhân).
- **Vì sao chọn:** Tuân thủ nguyên tắc **Default-Deny** và quy chế NCKH. Website có thể chứa thông tin cũ, bài viết tuyển sinh hết hạn hoặc liên kết không chính thức. Phê duyệt thủ công bảo vệ tính pháp lý của câu trả lời.
- **Vì sao loại phương án còn lại:** Nạp tự động dễ làm rác vector database và không thể thu hồi kiểm soát khi gặp bài viết sai lệch.
- **Loại căn cứ:** [tài liệu: GEMINI.md & docs/agent-workflow.md].
- **Đánh đổi:** Cần thêm một bước người quản trị chạy lệnh `approve` (hoặc nhấn nút trên UI sau này).

### Khối 4: Tái sử dụng pipeline `index_service.index_document` cho nạp tăng dần
- **Quyết định:** Gọi trực tiếp `index_service.index_document` với `category="tai_lieu_tong_hop"` thay vì viết pipeline index riêng.
- **Phương án đã cân nhắc:** Viết riêng hàm insert vector đơn giản chỉ ghi vào Qdrant.
- **Vì sao chọn:** `index_service.index_document` là đường ống chuẩn đã được kiểm chứng qua nhiều phiên: tự động làm sạch text, chạy `structural_chunker`, đồng bộ `chunks.jsonl`, đẩy vector vào Qdrant Local và tự động dựng lại chỉ mục BM25 đồng bộ.
- **Vì sao loại phương án còn lại:** Viết riêng sẽ gây lệch pha giữa BM25 và Vector DB, khiến tính năng Hybrid Search bị lỗi trích dẫn.
- **Loại căn cứ:** [kỹ thuật: kiến trúc hệ thống hiện có].
- **Đánh đổi:** Phải mở rộng danh sách `ALLOWED_CHUNK_META_KEYS` trong `index_service.py` để chấp nhận `source_url`.

---

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

### 1. SSRF (Server-Side Request Forgery) là gì?
- **Ví dụ đời thường:** Hãy tưởng tượng bạn thuê một shipper (server) đi mua đồ hộ. Thay vì bảo shipper đến tiệm bánh ngoài phố (web công cộng), bạn lại bảo shipper: *"Hãy lẻn vào phòng ngủ của chủ nhà bên cạnh và chụp lại két sắt hộ tôi"*. Vì shipper đang ở trong khu nhà riêng, bảo vệ nội bộ sẽ mở cửa cho shipper vào mà không nghi ngờ gì!
- **Trong hệ thống:** Khi cho phép server nhận một URL và tải về, nếu không kiểm tra, kẻ xấu có thể nhập `http://192.168.1.1` (trang quản trị router trường) hoặc `http://169.254.169.254` (nơi lưu mật khẩu server cloud). Server sẽ tự gửi request vào bên trong và tuồn thông tin mật ra ngoài. Hàm `is_safe_url` chính là chốt chặn bảo vệ: cấm shipper không được đi vào bất kỳ địa chỉ nhà riêng nào!

### 2. Incremental Indexing (Chỉ mục hóa tăng dần) là gì?
- **Ví dụ đời thường:** Giống như một cuốn từ điển dày 1.000 trang. Khi thư viện nhập thêm một cuốn sách nhỏ 10 trang mới, thủ thư không cần phải xé bỏ toàn bộ mục lục của 1.000 trang cũ để in lại từ đầu; thủ thư chỉ cần đánh chỉ mục cho 10 trang mới và bổ sung thêm vào cuối bảng mục lục.
- **Trong hệ thống:** Trước đây khi nạp tài liệu, hệ thống thường nạp cả thư mục. Với module nạp tăng dần, khi quản trị viên duyệt trang giới thiệu trường, hệ thống chỉ cắt nhỏ 2 đoạn của trang đó, nhúng vector và đẩy thêm vào Qdrant, đồng thời cập nhật nhanh từ khóa vào BM25 mà 103 đoạn quy chế cũ vẫn nằm nguyên vị trí an toàn.

---

## 5. Đã kiểm tra thế nào

### 5.1. Chạy Unit Test Suite toàn hệ thống
- **Lệnh:**
  ```cmd
  venv\Scripts\python.exe -m unittest discover -s tests -v
  ```
- **Kết quả thật:**
  ```text
  Ran 160 tests in 5.945s
  OK (skipped=1)
  ```
- **Kết luận:** **ĐẠT** (159/159 PASS, 1 test eval skipped do offline).

### 5.2. Chạy Kiểm thử Đơn vị Chuyên biệt cho URL Import
- **Lệnh:**
  ```cmd
  venv\Scripts\python.exe -m unittest tests/test_url_importer.py -v
  ```
- **Kết quả thật:**
  ```text
  test_approval_and_dry_run_ingest (tests.test_url_importer.TestURLImporter.test_approval_and_dry_run_ingest) ... ok
  test_clean_html_to_markdown (tests.test_url_importer.TestURLImporter.test_clean_html_to_markdown) ... ok
  test_import_single_url_deduplication (tests.test_url_importer.TestURLImporter.test_import_single_url_deduplication) ... ok
  test_import_single_url_success (tests.test_url_importer.TestURLImporter.test_import_single_url_success) ... ok
  test_is_safe_url_allowlist (tests.test_url_importer.TestURLImporter.test_is_safe_url_allowlist) ... ok
  test_is_safe_url_blocks_login_and_student_portal (tests.test_url_importer.TestURLImporter.test_is_safe_url_blocks_login_and_student_portal) ... ok
  test_is_safe_url_ssrf_and_ip (tests.test_url_importer.TestURLImporter.test_is_safe_url_ssrf_and_ip) ... ok

  Ran 7 tests in 0.029s
  OK
  ```
- **Kết luận:** **ĐẠT**.

### 5.3. Kiểm chứng Thực tế Trước và Sau khi Nạp URL (Before vs. After)
- **URL nạp:** `https://donga.edu.vn/gioi-thieu`
- **Câu hỏi kiểm tra:** *"Địa chỉ cơ sở chính của Trường Đại học Đông Á ở đâu và diện tích sàn bao nhiêu?"*
- **Trước khi nạp:**
  ```text
  Mình chưa tìm thấy thông tin cụ thể về địa chỉ cơ sở chính và diện tích sàn của Trường Đại học Đông Á trong tài liệu hiện có...
  Sufficiency: INSUFFICIENT | Citations: []
  ```
- **Sau khi nạp & duyệt:**
  ```text
  Cơ sở chính của Trường Đại học Đông Á tọa lạc tại địa chỉ 33 Xô Viết Nghệ Tĩnh - Đà Nẵng, với tổng diện tích sàn là 18.600m² [1].

  Chi tiết thông tin cơ sở đào tạo của nhà trường:
  * Địa chỉ: 33 Xô Viết Nghệ Tĩnh, phường Hòa Cường Nam, quận Hải Châu, TP. Đà Nẵng [1].
  * Quy mô và diện tích sàn: Cơ sở có kết cấu gồm 10 tầng với tổng diện tích sàn xây dựng là 18.600m² [1]...
  Sufficiency: SUFFICIENT | Citations: [1] | Source: web_2b329b97c1
  ```
- **Kết luận:** **ĐẠT XUẤT SẮC**. Chuyển đổi thành công từ thiếu dữ liệu sang trả lời đầy đủ kèm trích dẫn nguồn web chính xác.

- **Số lệnh gọi API trả phí đã dùng:** 2 lệnh gọi Gemini Flash cho 2 câu hỏi kiểm chứng thực tế.

---

## 6. Chưa chắc chắn, rủi ro, giả định

- **Giả định về kết nối mạng:** Giả định máy chủ chạy `ai-service` có quyền truy cập Internet ra ngoài tên miền `donga.edu.vn`. Nếu triển khai máy chủ trong mạng nội bộ đóng hoàn toàn (air-gapped), tính năng URL Import cần proxy hoặc phải dùng file Markdown tải sẵn.
- **Rủi ro trang web đổi giao diện:** Nếu website trường thay đổi cấu trúc sang Single Page App (SPA) render hoàn toàn bằng Javascript Client-side (như React/Vue), `urllib` sẽ không render được DOM (khi đó cần dùng Crawl4AI với Chromium headless đã xây dựng ở Phiên 5A).

---

## 7. Điều đã không làm và lý do

- **Không tự động nạp thẳng URL vào Qdrant:** Tuân thủ nguyên tắc Approval Gate và Default-Deny, tránh rác dữ liệu vector.
- **Không gắn loại tài liệu web thành `quy_che_truong`:** Văn bản web chỉ mang tính giới thiệu, hướng dẫn hoặc tổng hợp (`tai_lieu_tong_hop`), không phải văn bản quy phạm nội bộ do Hiệu trưởng ký.
- **Không tự ý commit hoặc push Git:** Tuân thủ nghiêm ngặt quy tắc GEMINI.md.
- **Không cài thêm thư viện bên ngoài nặng nề:** Tận dụng `html.parser`, regex và chuẩn DOM có sẵn của Python, giúp hệ thống gọn nhẹ và độc lập.

---

## 8. Việc tiếp theo

1. Bổ sung API endpoints (`/api/admin/urls/import`, `/api/admin/urls/approve`) vào FastAPI router để người dùng có thể dán link trực tiếp trên giao diện Web UI Demo.
2. Trình hội đồng phê duyệt 6 tài liệu DOCX hướng dẫn thủ tục trực tuyến (đã thẩm định ở `approval_review.md`).
3. Khám phá và nạp các trang web về Cẩm nang sinh viên, Biểu phí và Học bổng để chuẩn bị cho đợt Re-benchmark 75 câu khảo sát.

---

## 9. Câu hỏi cho người dùng

1. Bạn có muốn tích hợp luôn một tab "Quản trị Tri thức URL" (cho phép dán link và bấm duyệt) ngay trên giao diện Web Chat Demo ở phiên tiếp theo không?
2. Trong 7 tài liệu DOCX đã thẩm định (Phiên 6G/6H), bạn có đồng ý phê duyệt 6 tài liệu đủ điều kiện để tiến hành nạp chính thức vào kho không?

---

## 10. Ba câu tự kiểm tra hiểu bài

1. Vì sao hệ thống không cho phép URL tự động nạp thẳng vào Qdrant ngay sau khi người dùng nhập link?
2. Tại sao khi lọc sạch HTML cho website Trường ĐH Đông Á, chúng ta không được xóa thẻ `<form>`?
3. Cuộc tấn công SSRF là gì và hệ thống phòng chống nó bằng những cơ chế nào trong hàm `is_safe_url`?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì nguyên tắc an toàn **Default-Deny**: Dữ liệu web có thể chứa thông tin cũ, sai lệch hoặc ngoài phạm vi; cần sự thẩm định của người quản trị (`APPROVED`) trước khi đưa vào cơ sở tri thức chính thức để tránh làm hỏng độ tin cậy của câu trả lời.
2. Vì website ĐH Đông Á xây dựng trên nền tảng ASP.NET WebForms (DotNetNuke), toàn bộ nội dung hiển thị của trang web nằm bên trong một thẻ `<form id="aspnetForm">`. Nếu xóa thẻ `<form>`, toàn bộ nội dung của trang sẽ biến mất.
3. SSRF (Server-Side Request Forgery) là lỗ hổng mà kẻ tấn công lợi dụng máy chủ để gửi truy vấn độc hại vào các mạng nội bộ hoặc dịch vụ bí mật. Hệ thống phòng chống bằng cách: chỉ cho phép tên miền `donga.edu.vn`/`uda.edu.vn`, phân giải IP để chặn toàn bộ dải IP Private (10.x, 172.16.x, 192.168.x), loopback (127.0.0.1) và dải metadata cloud (169.254.169.254), đồng thời chặn cổng sinh viên cá nhân `my.uda.edu.vn`.

</details>
