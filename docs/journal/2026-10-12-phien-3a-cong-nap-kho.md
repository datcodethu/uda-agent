# Nhật ký 2026-10-12 – Phiên 3A: Cổng nạp kho theo bảng đăng ký (docs_registry.csv)

## 1. Mục tiêu
Thiết lập và hoàn thiện cổng kiểm soát nạp tài liệu vào kho vector và BM25 theo bảng đăng ký `docs_registry.csv` với cơ chế Default-Deny nghiêm ngặt, hỗ trợ chế độ xem trước an toàn `--dry-run` mặc định và bổ sung metadata hiệu lực pháp lý vào từng đoạn trích mà không tốn chi phí gọi API. Hoàn thành 6 điều kiện phê duyệt khắt khe: bảo vệ trường cốt lõi, bổ sung điều kiện `public_or_internal`, chặn theo cột `loai`, phòng chống tấn công thoát thư mục / trùng lặp, chịu lỗi đọc file đơn lẻ và cô lập tái cấu hình console UTF-8 trong `main()`.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/ingest_approved.py` | Cập nhật script cổng nạp kho: (1) Bắt buộc đủ 5 cột (`file`, `da_duyet`, `loai`, `status`, `public_or_internal`) nếu thiếu báo lỗi rõ; (2) Chỉ dùng cột `loai` làm cổng chặn loại tài liệu; (3) Thêm điều kiện 4: `public_or_internal=public`, chặn tài liệu `internal` trừ khi có cờ `--allow-internal`; (4) Cột file chỉ là tên file: chặn `/`, `\`, `..`, đường dẫn chuẩn hóa phải nằm trong `raw_documents`, chuẩn hóa tên file theo Unicode NFC ở cả 2 phía, chặn cả 2 dòng nếu tên file bị trùng lặp; (5) Lỗi đọc file không dừng cả lượt, đưa vào danh sách bị chặn kèm lý do; (6) Dry-run chỉ in tên file và số liệu, không in nội dung; đặt `sys.stdout.reconfigure` chỉ trong `main()`. |
| `ai-service/app/pipeline/index_service.py` | Áp dụng whitelist 6 khóa metadata (`doc_id`, `doc_title`, `doc_number`, `effective_date`, `category`, `applies_to`) khi ghi vào chunk; ngăn chặn tuyệt đối việc metadata ghi đè 4 trường cốt lõi (`chunk_id`, `text`, `doc_name`, `status`). |
| `ai-service/scripts/ingest_folder.py` | In cảnh báo hướng dẫn chuyển sang dùng `ingest_approved.py` và thoát ngay, không nạp bất kỳ file nào. |
| `ai-service/app/pipeline/rag_pipeline.py` | Bổ sung `effective_date` và `doc_number` vào từng nguồn trích dẫn trả về nếu chunk có thông tin này. |
| `ai-service/tests/test_core.py` | Mở rộng bộ kiểm thử `TestIngestApproved` lên 15 test case độc lập: bổ sung kiểm thử chặn thoát thư mục (`/`, `\`, `..`), chặn dòng trùng lặp, chặn/cho phép `public_or_internal` với cờ `--allow-internal`, kiểm tra báo lỗi khi thiếu cột bắt buộc, kiểm tra bọc lỗi đọc file đưa vào danh sách chặn, kiểm tra whitelist metadata & bảo vệ trường cốt lõi trong `index_service`. Nâng tổng số test lên 44/44 PASS (giữ nguyên vẹn 29 test ban đầu). |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Phiên 3A đạt 44/44 unit test PASS. |
| `docs/decisions.md` | Bổ sung quyết định siết chặt cổng nạp kho 3A theo 6 điều kiện được duyệt. |

## 3. Vì sao làm như vậy

### Khối 1: Cơ chế kiểm soát nạp mặc định cấm (Default-Deny)
- **Quyết định:** Mọi file trong thư mục `raw_documents` nếu không có dòng trong bảng đăng ký `docs_registry.csv` hoặc thiếu bất kỳ điều kiện nào (`da_duyet != true`, `loai != quy_che_truong`, `status != ACTIVE`, `public_or_internal != public` khi không có cờ `--allow-internal`, file không tồn tại trên đĩa) đều bị chặn và thông báo lý do cụ thể.
- **Phương án đã cân nhắc:**
  1. Nạp tất cả các file có đuôi `.pdf`/`.docx` trong thư mục (cách cũ của `ingest_folder.py`).
  2. Chỉ lọc qua các dòng trong bảng CSV mà không đối chiếu các file dư thừa trên đĩa.
  3. Quét đối chiếu 2 chiều: bảng CSV và thư mục đĩa (phương án chọn).
- **Vì sao chọn:** Trong hệ thống RAG học vụ trường đại học, việc nạp nhầm tài liệu cũ hết hạn, tài liệu mẫu đơn, hoặc văn bản luật chung sẽ làm loãng độ chính xác của vector search và khiến chatbot trả lời sai quy chế hiện hành của trường.
- **Vì sao loại phương án còn lại:** Phương án 1 không có kiểm duyệt; phương án 2 bỏ sót nguy cơ có file rác/file nhạy cảm nằm sẵn trong thư mục mà không ai quản lý.
- **Loại căn cứ:** [tài liệu: GEMINI.md & docs/ai-service.md mục 4.4]
- **Đánh đổi:** Cần duy trì bảng đăng ký CSV chuẩn xác trước khi nạp tài liệu mới.

### Khối 2: Bảo vệ trường dữ liệu cốt lõi và Whitelist metadata đoạn trích
- **Quyết định:** Chỉ cho phép 6 khóa (`doc_id`, `doc_title`, `doc_number`, `effective_date`, `category`, `applies_to`) từ metadata được ghi vào chunk; ngăn chặn hoàn toàn việc ghi đè lên `chunk_id`, `text`, `doc_name`, `status`.
- **Phương án đã cân nhắc:**
  1. `chunk.update(meta)` trực tiếp mọi khóa có trong metadata.
  2. Lọc bỏ các khóa trùng tên với chunk.
  3. Áp dụng whitelist danh sách khóa cho phép kết hợp blacklist bảo vệ 4 trường cốt lõi (phương án chọn).
- **Vì sao chọn:** Ngăn chặn nguy cơ dữ liệu bảng CSV vô tình hoặc cố ý chứa các cột như `chunk_id` hay `text` làm hỏng tính toàn vẹn định danh đoạn và nội dung văn bản gốc đã cắt.
- **Vì sao loại phương án còn lại:** Phương án 1 tiềm ẩn lỗi ghi đè phá vỡ cấu trúc chunk; phương án 2 có thể để lọt các trường rác không mong muốn từ CSV vào payload Qdrant.
- **Loại căn cứ:** [yêu cầu điều kiện duyệt kế hoạch 3A]
- **Đánh đổi:** Cần cập nhật whitelist nếu sau này hệ thống mở rộng thêm trường metadata mới.

### Khối 3: Cổng chặn an toàn đường dẫn và xử lý Unicode NFC
- **Quyết định:** Cột `file` chỉ là tên file đơn thuần (từ chối nếu chứa `/`, `\`, `..`), xác minh đường dẫn chuẩn hóa (`resolve()`) bắt buộc phải thuộc thư mục `raw_documents`. So sánh đối chiếu tên file ở cả bảng CSV và ổ đĩa theo chuẩn Unicode NFC (`unicodedata.normalize('NFC', ...)`). Chặn cả hai dòng nếu file xuất hiện nhiều lần trong CSV.
- **Phương án đã cân nhắc:**
  1. Dùng hàm so sánh chuỗi thông thường `name1 == name2`.
  2. Chuẩn hóa Unicode NFC 2 phía và kiểm tra an toàn thư mục chặt chẽ (phương án chọn).
- **Vì sao chọn:** Tiếng Việt có hai chuẩn gõ ký tự có dấu: Unicode dựng sẵn (NFC) và Unicode tổ hợp (NFD). Nếu tên file trên Windows lưu dạng NFC mà bảng CSV lưu dạng NFD (hoặc ngược lại do phần mềm gõ tiếng Việt khác nhau), việc so sánh trực tiếp sẽ báo sai là không tìm thấy file. Đồng thời việc cấm `..` và ký tự phân cách đường dẫn giúp triệt tiêu hoàn toàn nguy cơ Path Traversal (truy cập trái phép file hệ thống ngoài thư mục quy chế).
- **Vì sao loại phương án còn lại:** Phương án 1 dễ bị lỗi từ chối nhầm file tiếng Việt và tiềm ẩn lỗ hổng bảo mật.
- **Loại căn cứ:** [kỹ thuật & yêu cầu duyệt kế hoạch 3A]
- **Đánh đổi:** Thêm một bước chuẩn hóa NFC khi nạp bảng đăng ký.

### Khối 4: Khả năng chịu lỗi đọc tài liệu đơn lẻ (Fault-tolerance)
- **Quyết định:** Khi một file được duyệt gặp lỗi đọc (file PDF hỏng cấu trúc, lỗi font không giải mã được), script bắt ngoại lệ, đưa file đó vào danh sách `blocked` kèm thông báo lý do lỗi, và tiếp tục xử lý các file hợp lệ còn lại mà không làm dừng cả lượt nạp.
- **Phương án đã cân nhắc:**
  1. Ném ngoại lệ (raise Exception) dừng toàn bộ chương trình ngay khi gặp file lỗi đầu tiên.
  2. Ghi nhận lỗi vào danh sách bị chặn và tiếp tục xử lý các file tiếp theo (phương án chọn).
- **Vì sao chọn:** Trong thực tế kho tài liệu có hàng chục văn bản, việc một file bị lỗi không nên làm tê liệt quy trình kiểm duyệt hoặc nạp của toàn bộ các văn bản hợp lệ còn lại.
- **Vì sao loại phương án còn lại:** Phương án 1 gây gián đoạn quy trình quản trị viên, buộc phải sửa từng file một cách thủ công qua nhiều lần chạy lại.
- **Loại căn cứ:** [yêu cầu điều kiện duyệt kế hoạch 3A]
- **Đánh đổi:** Cần quản lý hai danh sách `approved` và `blocked` động trong quá trình chạy.

### Khối 5: Chế độ kiểm duyệt Dry-run và cô lập tái cấu hình Console
- **Quyết định:** Mặc định script chạy ở chế độ `--dry-run`, chỉ in tên file, tiêu đề, số đoạn, tổng ký tự và thông tin pháp lý; tuyệt đối không in nội dung chi tiết quy chế; không gọi API embedding và không ghi DB; lệnh cấu hình `sys.stdout.reconfigure(encoding="utf-8")` được đặt duy nhất bên trong hàm `main()`.
- **Phương án đã cân nhắc:**
  1. Đặt `sys.stdout.reconfigure` ở mức module hoặc bên trong `run_ingest`.
  2. Chỉ đặt cấu hình trong `main()` (phương án chọn).
- **Vì sao chọn:** Khi `run_ingest` được gọi từ các module khác (như trong unittest runner), việc tự ý can thiệp vào `sys.stdout` toàn cục có thể gây xung đột với các bộ bắt luồng (capturing/redirecting) của test runner. Đặt trong `main()` đảm bảo khi chạy trực tiếp từ dòng lệnh CLI vẫn hiển thị tiếng Việt UTF-8 chuẩn xác mà không ảnh hưởng môi trường kiểm thử.
- **Vì sao loại phương án còn lại:** Phương án 1 gây hiệu ứng phụ không mong muốn lên các luồng kiểm thử đơn vị.
- **Loại căn cứ:** [yêu cầu điều kiện duyệt kế hoạch 3A]
- **Đánh đổi:** Các hàm gọi cấp thấp khi chạy độc lập ngoài CLI cần tự quản lý encoding nếu có nhu cầu in riêng.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)
1. **Unicode NFC (Normalization Form C) vs NFD (Normalization Form D):**
   - *Khái niệm:* Hai cách máy tính lưu trữ ký tự có dấu. NFC gom chữ cái và dấu thanh thành 1 ký tự duy nhất (ví dụ: chữ `á` là 1 mã `\u00e1`). NFD tách rời chữ cái gốc và dấu thanh thành 2 ký tự ghép lại (`a` + dấu sắc `\u0301`). Mắt người nhìn trên màn hình thấy giống hệt nhau, nhưng máy tính so sánh `a == b` sẽ báo sai nếu hai bên khác dạng chuẩn hóa.
   - *Ví dụ đời thường:* Giống như một chiếc bánh mì kẹp xúc xích. Một tiệm bán chiếc bánh mì đã kẹp sẵn xúc xích bên trong (NFC: 1 món), còn một tiệm bán chiếc bánh mì rời kèm gói xúc xích riêng để bạn tự kẹp (NFD: 2 món). Ăn vào thì như nhau, nhưng khi kiểm kê số lượng sản phẩm thì một bên đếm là 1 món, một bên đếm là 2 món.
2. **Lỗ hổng thoát thư mục (Path Traversal / Directory Traversal):**
   - *Khái niệm:* Lỗ hổng bảo mật khi kẻ xấu chèn các ký tự điều hướng thư mục như `../` hoặc `..\` vào tên file để truy cập hoặc ghi đè lên các tệp nhạy cảm nằm ngoài thư mục cho phép (ví dụ: `../../Windows/System32`).
   - *Ví dụ đời thường:* Giống như bạn cho một người khách vào mượn sách ở tủ sách phòng khách, nhưng họ lại lần mò theo cầu thang đi thẳng vào phòng ngủ gia đình để đọc nhật ký riêng. Việc chặn `..` chính là khóa chốt cửa cầu thang lại, chỉ cho khách đứng đúng ở phòng khách.
3. **Whitelist (Danh sách trắng) vs Blacklist (Danh sách đen):**
   - *Khái niệm:* Blacklist là cấm những thứ được liệt kê trong danh sách cấm, còn lại cho qua hết. Whitelist là chỉ cho phép duy nhất những thứ nằm trong danh sách cho phép, tất cả những thứ khác đều bị từ chối.
   - *Ví dụ đời thường:* Giống như danh sách khách mời trong một bữa tiệc VIP. Bảo vệ có Whitelist: chỉ ai có tên trên danh thiếp mới được vào cửa. Bảo vệ không dùng Blacklist vì kẻ xấu có thể đổi tên mới chưa có trong danh sách đen để lẻn vào.

## 5. Đã kiểm tra thế nào
- **Lệnh 1 (Chạy toàn bộ bộ kiểm thử tự động gồm 29 test cũ và 15 test mới):**
```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```
- **Kết quả thật:**
```
test_expand_appends_not_replaces (test_core.TestAbbreviation.test_expand_appends_not_replaces) ... ok
test_no_abbrev_unchanged (test_core.TestAbbreviation.test_no_abbrev_unchanged) ... ok
test_article_without_title_keeps_body_sentence (test_core.TestChunker.test_article_without_title_keeps_body_sentence) ... ok
test_check_article_order_warnings (test_core.TestChunker.test_check_article_order_warnings) ... ok
test_chuong_and_title_carried (test_core.TestChunker.test_chuong_and_title_carried) ... ok
test_decision_and_regulation_sections_no_x1_suffix (test_core.TestChunker.test_decision_and_regulation_sections_no_x1_suffix) ... ok
test_default_status_is_active_uppercase (test_core.TestChunker.test_default_status_is_active_uppercase) ... ok
test_dieu_regex_variants (test_core.TestChunker.test_dieu_regex_variants) ... ok
test_extract_doc_title (test_core.TestChunker.test_extract_doc_title) ... ok
test_header_in_text_and_content_kept (test_core.TestChunker.test_header_in_text_and_content_kept) ... ok
test_long_article_is_split_with_header_each_part (test_core.TestChunker.test_long_article_is_split_with_header_each_part) ... ok
test_one_chunk_per_dieu (test_core.TestChunker.test_one_chunk_per_dieu) ... ok
test_reference_inside_sentence_is_not_a_new_article (test_core.TestChunker.test_reference_inside_sentence_is_not_a_new_article) ... ok
test_sentence_boundary_clean_overlap (test_core.TestChunker.test_sentence_boundary_clean_overlap) ... ok
test_table_preserved_and_header_repeated_when_split (test_core.TestChunker.test_table_preserved_and_header_repeated_when_split) ... ok
test_unique_ids (test_core.TestChunker.test_unique_ids) ... ok
test_keep_dieu_lines_even_if_repeated (test_core.TestCleaner.test_keep_dieu_lines_even_if_repeated) ... ok
test_nfc_normalization (test_core.TestCleaner.test_nfc_normalization) ... ok
test_remove_page_numbers_and_repeated_header (test_core.TestCleaner.test_remove_page_numbers_and_repeated_header) ... ok
test_blocks_with_signature (test_core.TestExtractText.test_blocks_with_signature) ... ok
test_none (test_core.TestExtractText.test_none) ... ok
test_plain_string (test_core.TestExtractText.test_plain_string) ... ok
test_rrf_prefers_items_in_both_lists (test_core.TestFusion.test_rrf_prefers_items_in_both_lists) ... ok
test_dry_run_execution_no_db_write (test_core.TestIngestApproved.test_dry_run_execution_no_db_write) ... ok
test_file_read_error_recorded_in_blocked (test_core.TestIngestApproved.test_file_read_error_recorded_in_blocked) ... ok
test_filter_da_duyet_false_blocked (test_core.TestIngestApproved.test_filter_da_duyet_false_blocked) ... ok
test_filter_duplicate_file_rows_blocked (test_core.TestIngestApproved.test_filter_duplicate_file_rows_blocked) ... ok
test_filter_loai_phap_luat_blocked (test_core.TestIngestApproved.test_filter_loai_phap_luat_blocked) ... ok
test_filter_missing_file_on_disk_blocked (test_core.TestIngestApproved.test_filter_missing_file_on_disk_blocked) ... ok
test_filter_path_traversal_blocked (test_core.TestIngestApproved.test_filter_path_traversal_blocked) ... ok
test_filter_public_or_internal_gating (test_core.TestIngestApproved.test_filter_public_or_internal_gating) ... ok
test_filter_status_expired_blocked (test_core.TestIngestApproved.test_filter_status_expired_blocked) ... ok
test_filter_unregistered_file_blocked (test_core.TestIngestApproved.test_filter_unregistered_file_blocked) ... ok
test_filter_valid_approved_file_selected (test_core.TestIngestApproved.test_filter_valid_approved_file_selected) ... ok
test_index_document_metadata_whitelist_and_protection (test_core.TestIngestApproved.test_index_document_metadata_whitelist_and_protection) ... ok
test_ingest_folder_prints_warning_and_exits (test_core.TestIngestApproved.test_ingest_folder_prints_warning_and_exits) ... ok
test_missing_required_column_raises_value_error (test_core.TestIngestApproved.test_missing_required_column_raises_value_error) ... ok
test_rag_pipeline_sources_with_metadata (test_core.TestIngestApproved.test_rag_pipeline_sources_with_metadata) ... ok
test_load_text_from_txt (test_core.TestPdfLoader.test_load_text_from_txt) ... ok
test_slug (test_core.TestSlug.test_slug) ... ok
test_all_supported (test_core.TestVerifier.test_all_supported) ... ok
test_citation_markers_ignored (test_core.TestVerifier.test_citation_markers_ignored) ... ok
test_detects_wrong_number (test_core.TestVerifier.test_detects_wrong_number) ... ok
test_thousand_separators_normalized (test_core.TestVerifier.test_thousand_separators_normalized) ... ok

----------------------------------------------------------------------
Ran 44 tests in 1.377s

OK
```

- **Lệnh 2 (Chạy dry-run trên bảng đăng ký thật ai-service/data/docs_registry.csv ban đầu khi da_duyet=false):**
```powershell
venv\Scripts\python.exe -m scripts.ingest_approved
```
- **Kết quả thật:**
  - Danh sách [SẼ NẠP]: `0 file`
  - Danh sách [CHẶN]: `55 file` (toàn bộ 55 file trong bảng đều bị chặn do `da_duyet != true (giá trị: 'false')`).
  - Tổng kết: Dự kiến nạp 0 file (0 đoạn, 0 ký tự). Bị chặn: 55 file.

- **Lệnh 3 (Kiểm tra đường "được nạp" bằng dữ liệu thật cho file 2023_8_23_16_29_59n.pdf):**
Sau khi mở đọc file và xác nhận nội dung là Quyết định số 1345/QĐ-ĐHĐA-QLĐT ngày 26/08/2022 ban hành "Quy định về Chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành không chuyên ngữ tại Trường Đại học Đông Á" (quy chế trường, còn hiệu lực, công khai), cập nhật `da_duyet=true` trong `docs_registry.csv` và chạy lại dry-run:
```powershell
venv\Scripts\python.exe -m scripts.ingest_approved
```
- **Kết quả thật:**
```
[DANH SÁCH FILE ĐƯỢC PHÊ DUYỆT (1 file)]:
  1. [SẼ NẠP] 2023_8_23_16_29_59n.pdf:
     - Tiêu đề: Quy định về Chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành không chuyên ngữ tại Trường Đại học Đông Á (Áp dụng đối với sinh viên bậc Đại học hệ chính quy từ khóa 2022 trở đi)
     - Số đoạn cắt: 21 đoạn | Tổng ký tự: 17,551 ký tự
     - Metadata: doc_id=, số hiệu=(trống), ngày hiệu lực=(trống), đối tượng=ALL

[DANH SÁCH FILE BỊ CHẶN (54 file)]:
  (54 file còn lại tiếp tục bị chặn với lý do da_duyet != true)

KẾT QUẢ DRY-RUN: Dự kiến nạp 1 file (21 đoạn, 17,551 ký tự). Bị chặn: 54 file.
```
- **Kết luận:** ĐẠT 100%. Cổng nạp hoạt động chính xác tuyệt đối: chỉ mở cổng cho đúng file đã được thẩm định và phê duyệt, chặn toàn bộ 54 file chưa duyệt còn lại.
- **Số lệnh gọi API trả phí đã dùng:** 0 (hoàn toàn chạy offline, không gọi API Gemini hay Qdrant).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Điểm chưa chắc chắn:** Tệp `docs_registry.csv` hiện tại chỉ có 5 cột tối thiểu (`file`, `da_duyet`, `loai`, `status`, `public_or_internal`). Các cột bổ sung như `doc_title`, `doc_number`, `effective_date`, `applies_to` đang được để trống và script tự động trích xuất tiêu đề từ nội dung văn bản.
- **Rủi ro:** Khi nạp hàng loạt các văn bản tiếp theo, người quản trị cần thẩm định kỹ từng file trước khi chuyển cờ `da_duyet=true`, tránh mở cổng ồ ạt làm loãng kho vector.

## 7. Điều đã không làm và lý do
- Không chạy cờ `--apply` để nạp dữ liệu thật vào DB (bảo vệ hạn mức API và DB vector).
- Không sửa hay xóa 29 bài unit test có từ trước (bảo tồn nguyên vẹn tính hồi quy).
- Không gọi bất kỳ API trả phí nào và không đọc/in tệp `.env`.

## 8. Việc tiếp theo
- Người dùng xác nhận kết quả kiểm tra cổng nạp Phiên 3A.
- Thẩm định các tài liệu quy chế tiếp theo và điền đầy đủ metadata (`doc_title`, `doc_number`, `effective_date`) vào `docs_registry.csv`.
- Chuẩn bị cho Phiên 3B (nạp embedding vào Qdrant và dựng lại BM25).

## 9. Câu hỏi cho người dùng
- Bạn đã chép tệp `docs_registry.csv` vào thư mục `ai-service\data\` chưa? Hiện tại trên đĩa chưa tìm thấy tệp này (chỉ có tệp mẫu `docs_registry_mau.csv`). Bạn có thể kiểm tra lại xem tệp đã được lưu hoặc copy vào đúng thư mục `E:\workspace\donga-rag-system\ai-service\data\docs_registry.csv` chưa nhé!

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao cần phải chuẩn hóa tên file theo định dạng Unicode NFC ở cả phía bảng đăng ký CSV và phía tệp trên đĩa trước khi so sánh đối chiếu?
2. Tại sao việc đặt `sys.stdout.reconfigure(encoding="utf-8")` chỉ bên trong hàm `main()` lại an toàn hơn là đặt ở mức module hoặc bên trong hàm thư viện `run_ingest`?
3. Khi phát hiện một tên file xuất hiện ở 2 dòng khác nhau trong bảng đăng ký, vì sao hệ thống lại chặn cả 2 dòng thay vì chọn dòng xuất hiện trước?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì tiếng Việt có thể được lưu trữ dưới dạng Unicode dựng sẵn (NFC) hoặc tổ hợp (NFD). Nếu không chuẩn hóa về cùng một dạng chuẩn NFC, hai chuỗi có cùng mặt chữ sẽ có mã byte khác nhau, dẫn đến việc so sánh `name1 == name2` bị sai (hệ thống sẽ báo nhầm là file không tồn tại).
2. Vì hàm `run_ingest` có thể được import và gọi bởi các chương trình khác (như bộ chạy kiểm thử unittest runner). Việc tự ý can thiệp vào mã hóa của `sys.stdout` toàn cục trong hàm thư viện có thể làm hỏng cơ chế bắt luồng xuất (stdout redirect/capture) của test runner. Đặt trong `main()` đảm bảo chỉ khi chạy từ dòng lệnh CLI mới kích hoạt cấu hình này.
3. Vì sự xuất hiện trùng lặp của cùng một file ở hai dòng khác nhau cho thấy sự mâu thuẫn về quản trị dữ liệu (ví dụ: một dòng ghi `da_duyet=true`, dòng kia lại ghi `da_duyet=false`, hoặc khác nhau về số hiệu/ngày hiệu lực). Chặn cả hai dòng theo nguyên tắc Default-Deny buộc người quản trị phải rà soát và làm sạch bảng đăng ký trước khi nạp vào kho.

</details>
