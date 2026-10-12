# Nhật ký 2026-10-11 – Bước 3 & Bước 4: Đọc file, làm sạch, cắt đoạn quy chế và chuẩn hóa trạng thái

## 1. Mục tiêu
Thực hiện đọc và làm sạch văn bản quy chế thực tế trong `ai-service/data/raw_documents/`, tinh chỉnh bộ cắt đoạn ngữ nghĩa theo Chương và Điều (mục 4.1, 4.2, 4.3 trong `docs/ai-service.md`), thống nhất cờ trạng thái sang chữ in hoa `ACTIVE` / `EXPIRED` (mục 4.5), và tạo bản xem trước (preview chunks) vào `ai-service/data/chunk_preview/` để người dùng đối chiếu.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/preprocessor/structural_chunker.py` | Cập nhật `DIEU_RE` hỗ trợ các biến thể tiêu đề (`Điều 5 - ...`, `Điều 5 – ...`, `Điều 5 Học phí`, `ĐIỀU 5. ...`), giữ nguyên logic tránh nhận nhầm câu tham chiếu trong thân bài; đổi giá trị mặc định của `status` thành `"ACTIVE"`. |
| `ai-service/app/pipeline/index_service.py` | Đổi giá trị mặc định `status` trong hàm `index_document` thành `"ACTIVE"`. |
| `ai-service/app/api/v1/ingest_routes.py` | Đổi mặc định Form `status` thành `"ACTIVE"`, cập nhật kiểm tra dữ liệu thành `("ACTIVE", "EXPIRED")` và câu thông báo lỗi tương ứng. |
| `ai-service/app/pipeline/retrieval/bm25_search.py` | Cập nhật điều kiện lọc văn bản còn hiệu lực sang `c.get("status") != "ACTIVE"`. |
| `ai-service/app/pipeline/retrieval/dense_search.py` | Cập nhật bộ lọc Qdrant Filter sang `models.MatchValue(value="ACTIVE")`. |
| `ai-service/app/pipeline/retrieval/chunk_store.py` | Cập nhật giá trị fallback trong `list_documents()` sang `"ACTIVE"`. |
| `ai-service/tests/test_core.py` | Bổ sung 2 test method mới (`test_dieu_regex_variants` và `test_default_status_is_active_uppercase`), không sửa đổi bất kỳ assert hay test nào có từ trước (tổng số test tăng từ 20 lên 22 test, toàn bộ PASS). |
| `ai-service/scripts/preview_chunks.py` | Tạo script đọc các tài liệu văn bản hợp lệ, làm sạch qua `clean_text`, cắt đoạn qua `chunk_document`, và ghi thông tin xem trước (mã đoạn, số ký tự, 200 ký tự đầu) vào `ai-service/data/chunk_preview/`. |
| `docs/progress.md` | Cập nhật trạng thái tiến độ của Bước 3 và Bước 4. |
| `docs/decisions.md` | Ghi nhận quyết định thống nhất `status = "ACTIVE" / "EXPIRED"`, cập nhật regex `DIEU_RE`, và phân loại 56 file dữ liệu thật. |

## 3. Vì sao làm như vậy

### Khối 1: Thống nhất giá trị trạng thái thành `ACTIVE` và `EXPIRED` (chữ in hoa)
- **Quyết định:** Đổi toàn bộ chuỗi `"active"` / `"expired"` trong 6 file nguồn thành `"ACTIVE"` / `"EXPIRED"`.
- **Phương án đã cân nhắc:**
  1. Giữ nguyên chữ thường `"active"`/`"expired"` như mã khung ban đầu.
  2. Dùng chữ in hoa `"ACTIVE"`/`"EXPIRED"`.
- **Vì sao chọn:** Đồng bộ chặt chẽ với lược đồ CSDL PostgreSQL của backend Spring Boot (`documents.status` theo `plan.md` mục 5.1 và 6.1) và đúng với hướng dẫn ở mục 3, mục 4.5 của `docs/ai-service.md`.
- **Vì sao loại phương án còn lại:** Nếu để chữ thường, khi Spring Boot truyền `status = "ACTIVE"` sang endpoint `/v1/ingest`, hệ thống sẽ trả về lỗi HTTP 400 hoặc không khớp với bộ lọc truy xuất của Qdrant/BM25.
- **Loại căn cứ:** [tài liệu: docs/ai-service.md, mục 3 và 4.5; docs/plan.md, mục 5.1 và 6.1]
- **Đánh đổi:** Cần sửa đồng bộ tại 6 file khác nhau và phải kiểm thử lại toàn bộ các hàm lọc.

### Khối 2: Tinh chỉnh biểu thức chính quy nhận diện Điều (`DIEU_RE`)
- **Quyết định:** Mở rộng regex thành `r"^\s*(?i:điều)\s+(\d+[a-z]?)(?:\s*[.:\-–—]\s*(.*)|\s+([A-ZÀ-ỸĐ][^\n]*)|[.:\-–—]?\s*)$"`.
- **Phương án đã cân nhắc:**
  1. Giữ nguyên regex cũ `r"^\s*điều\s+(\d+[a-z]?)\s*[.:]\s*(.*)$"`.
  2. Cho phép dấu phân cách tùy ý không kiểm soát chữ hoa/thường.
  3. Mở rộng hỗ trợ dấu gạch ngang (`-`, `–`, `—`) hoặc khoảng trắng kèm chữ hoa đầu tiêu đề (phương án chọn).
- **Vì sao chọn:** Bắt chính xác các biến thể tiêu đề thực tế trong các văn bản pháp quy của trường như `Điều 5 - Học phí`, `Điều 5 – Học phí`, `Điều 5 Học phí`, `ĐIỀU 5. HỌC PHÍ`, đồng thời không nhận nhầm các câu tham chiếu văn bản trong thân bài như `Điều 5 của quy chế này...` (vì chữ "của" bắt đầu bằng chữ thường).
- **Vì sao loại phương án còn lại:** Regex cũ bỏ sót các điều dùng dấu gạch ngang hoặc không có dấu chấm; regex lỏng lẻo sẽ phá vỡ unit test `test_reference_inside_sentence_is_not_a_new_article`.
- **Loại căn cứ:** [kỹ thuật] & [tài liệu: docs/ai-service.md, mục 4.3]
- **Đánh đổi:** Biểu thức chính quy phức tạp hơn, cần chú ý phân nhóm match khi lấy `dieu_title`.

### Khối 3: Xử lý phân loại 56 tệp trong `data/raw_documents/`
- **Quyết định:** Bỏ qua `quy_che_mau_demo.txt`; xử lý 9 file PDF có lớp văn bản; bỏ qua 15 file PDF scan (không tự ý cài OCR); bỏ qua 19 file `.doc` (Word 97-2003 nhị phân) và 12 file `.docx` (biểu mẫu đơn từ hành chính).
- **Phương án đã cân nhắc:**
  1. Tự cài thêm thư viện OCR bên ngoài và cài thêm bộ đọc Word.
  2. Bỏ qua các file không đọc được, báo cáo danh sách rõ ràng cho người dùng.
- **Vì sao chọn:** Tuân thủ nghiêm ngặt quy tắc cốt lõi của dự án và chỉ đạo trực tiếp của người dùng trong tin nhắn giao việc: "Nếu gặp PDF scan hoặc file không đọc được, đừng tự cài OCR, hãy bỏ qua file đó và báo tôi".
- **Vì sao loại phương án còn lại:** Tự ý cài OCR vi phạm hàng rào an toàn của dự án và có thể gây lỗi môi trường; các file `.docx` khảo sát thực tế chỉ là mẫu đơn, không chứa quy chế.
- **Loại căn cứ:** [chỉ đạo của người dùng] & [kỹ thuật]
- **Đánh đổi:** Chỉ có 9 tài liệu PDF được cắt đoạn trong phiên này, các tài liệu dạng scan cần xử lý ở giai đoạn sau.

### Khối 4: Xuất bản xem trước (preview chunks) ra thư mục riêng
- **Quyết định:** Ghi chi tiết từng đoạn cắt vào các file text trong `ai-service/data/chunk_preview/`, không in nội dung ra màn hình chat.
- **Phương án đã cân nhắc:** In một phần hoặc toàn bộ ra khung chat/terminal.
- **Vì sao chọn:** Đảm bảo không làm tràn bộ nhớ ngữ cảnh và giữ khung chat gọn gàng theo đúng yêu cầu: "không in nội dung quy chế ra khung chat". Thư mục `ai-service/data/chunk_preview/` đã được cấu hình trong `.gitignore` nên an toàn cho git.
- **Loại căn cứ:** [chỉ đạo của người dùng]
- **Đánh đổi:** Người dùng cần mở file text trong thư mục để đối chiếu mắt.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)

### 1. Cắt đoạn theo cấu trúc (Structural Chunking) là gì?
- **Ví dụ đời thường:** Hãy tưởng tượng bạn đang đọc một cuốn sách giáo khoa để ôn thi. Nếu bạn dùng kéo cắt trang sách cứ đúng mỗi 5 cm một mảnh bất kể chữ đang ở đâu (cắt mù theo độ dài - fixed size), mảnh giấy của bạn có thể chứa nửa câu của định lý, còn phần công thức và điều kiện lại rơi sang mảnh giấy khác. Khi đọc mảnh giấy đó, bạn sẽ không hiểu gì cả.
- **Trong RAG:** Thay vì cắt mù, **Structural Chunking** giống như việc bạn dùng mục lục và các đề mục lớn: mỗi mảnh giấy sẽ là trọn vẹn một **Điều** quy chế (ví dụ `Điều 15. Chuẩn đầu ra`). Ở đầu mảnh giấy luôn được dán sẵn tiêu đề `[Tên văn bản | Chương | Điều]`. Nhờ vậy, dù đem mảnh giấy đó đi đâu, AI vẫn biết chính xác đoạn văn đó quy định về cái gì và thuộc điều khoản nào.

### 2. Chuẩn hóa ký tự Unicode (NFC vs NFD)
- **Ví dụ đời thường:** Trong tiếng Việt, chữ `ế` có thể được máy tính lưu theo 2 cách:
  - **NFC (Precomposed - Dựng sẵn):** Máy coi `ế` là 1 ký tự duy nhất (mã `\u1ebf`).
  - **NFD (Decomposed - Tổ hợp):** Máy ghép chữ `e` với dấu mũ `^` và dấu sắc `'` (thành 3 ký tự ghép lại).
- Nhìn trên màn hình hai chữ giống hệt nhau, nhưng khi dùng máy tính tìm kiếm, máy sẽ báo "không tìm thấy" vì mã số nhị phân của chúng hoàn toàn khác nhau. Hàm `clean_text` đưa toàn bộ chữ về chuẩn **NFC** để đảm bảo việc tìm kiếm luôn chính xác.

## 5. Đã kiểm tra thế nào

- **Lệnh 1:** Chạy toàn bộ bộ kiểm thử đơn vị (Unit Tests)
  ```powershell
  $env:PYTHONUTF8=1; venv\Scripts\python.exe -m unittest discover -s tests -v
  ```
  *Kết quả thật:*
  ```text
  test_expand_appends_not_replaces (test_core.TestAbbreviation.test_expand_appends_not_replaces) ... ok
  test_no_abbrev_unchanged (test_core.TestAbbreviation.test_no_abbrev_unchanged) ... ok
  test_chuong_and_title_carried (test_core.TestChunker.test_chuong_and_title_carried) ... ok
  test_default_status_is_active_uppercase (test_core.TestChunker.test_default_status_is_active_uppercase) ... ok
  test_dieu_regex_variants (test_core.TestChunker.test_dieu_regex_variants) ... ok
  test_header_in_text_and_content_kept (test_core.TestChunker.test_header_in_text_and_content_kept) ... ok
  test_long_article_is_split_with_header_each_part (test_core.TestChunker.test_long_article_is_split_with_header_each_part) ... ok
  test_one_chunk_per_dieu (test_core.TestChunker.test_one_chunk_per_dieu) ... ok
  test_reference_inside_sentence_is_not_a_new_article (test_core.TestChunker.test_reference_inside_sentence_is_not_a_new_article) ... ok
  test_unique_ids (test_core.TestChunker.test_unique_ids) ... ok
  test_keep_dieu_lines_even_if_repeated (test_core.TestCleaner.test_keep_dieu_lines_even_if_repeated) ... ok
  test_nfc_normalization (test_core.TestCleaner.test_nfc_normalization) ... ok
  test_remove_page_numbers_and_repeated_header (test_core.TestCleaner.test_remove_page_numbers_and_repeated_header) ... ok
  test_blocks_with_signature (test_core.TestExtractText.test_blocks_with_signature) ... ok
  test_none (test_core.TestExtractText.test_none) ... ok
  test_plain_string (test_core.TestExtractText.test_plain_string) ... ok
  test_rrf_prefers_items_in_both_lists (test_core.TestFusion.test_rrf_prefers_items_in_both_lists) ... ok
  test_slug (test_core.TestSlug.test_slug) ... ok
  test_all_supported (test_core.TestVerifier.test_all_supported) ... ok
  test_citation_markers_ignored (test_core.TestVerifier.test_citation_markers_ignored) ... ok
  test_detects_wrong_number (test_core.TestVerifier.test_detects_wrong_number) ... ok
  test_thousand_separators_normalized (test_core.TestVerifier.test_thousand_separators_normalized) ... ok

  ----------------------------------------------------------------------
  Ran 22 tests in 0.008s

  OK
  ```
  *Kết luận:* **ĐẠT** (22/22 tests pass, bao gồm 20 test cũ và 2 test mới thêm).

- **Lệnh 2:** Chạy script tạo bản xem trước các đoạn cắt trên dữ liệu thật
  ```powershell
  $env:PYTHONUTF8=1; venv\Scripts\python.exe -m scripts.preview_chunks
  ```
  *Kết quả thật:*
  - Xử lý thành công và tạo file preview cho 9 tài liệu PDF:
    + `2021_8_3_15_25_37.pdf`: 2 đoạn
    + `2023_8_23_16_29_59n.pdf`: 18 đoạn (Chuẩn đầu ra ngoại ngữ - quy chế trọng tâm)
    + `2023_8_29_8_50_20c.pdf`: 5 đoạn
    + `2023_8_29_8_51_2A.pdf`: 5 đoạn
    + `2024_11_14_14_26_46A.pdf`: 47 đoạn
    + `2026_10_6_10_15_26g.pdf`: 87 đoạn (Luật An ninh mạng)
    + `2026_10_6_10_16_15ộ.pdf`: 216 đoạn (Luật Trật tự ATGT đường bộ)
    + `2026_10_6_10_18_43c.pdf`: 77 đoạn
    + `2026_7_8_17_19_23o.pdf`: 2 đoạn
  - Bỏ qua 15 file PDF scan/rỗng: `2021_11_6_16_27_47̉.pdf`, `2023_8_23_16_29_26ữ.pdf`, `2024_11_15_15_37_50ữ.pdf`, `2024_11_15_15_39_561.pdf`, `2025_4_21_9_36_499.pdf`, `2025_4_8_8_52_231.pdf`, `2026_10_5_14_48_44H.pdf`, `2026_10_5_14_54_115.pdf`, `2026_10_6_10_17_64.pdf`, `2026_7_15_13_29_56n.pdf`, `2026_7_15_13_31_575.pdf`, `2026_7_15_13_33_476.pdf`, `2026_7_15_13_35_21A.pdf`, `2026_7_15_13_36_13A.pdf`, `2026_7_15_13_37_19g.pdf`.
  - Bỏ qua 31 file định dạng khác (19 file `.doc`, 12 file `.docx`).
  *Kết luận:* **ĐẠT**.
- **Số lệnh gọi API trả phí đã dùng:** 0 (hoàn toàn chạy offline trên máy).

## 6. Chưa chắc chắn, rủi ro, giả định
1. **15 file PDF scan:** Không có lớp chữ để trích xuất bằng thư viện PDF thông thường; phòng Đào tạo cần cung cấp bản gốc Word hoặc chạy OCR độc lập trước khi nạp.
2. **File `.doc` nhị phân (19 file):** Là tài liệu định dạng Word cũ, cần chuyển sang `.docx` hoặc xuất lại PDF trước khi xử lý.
3. **Chất lượng file `2026_10_6_10_18_43c.pdf`:** Có lớp văn bản nhưng chữ bị lỗi font / gõ sai dấu tiếng Việt từ nguồn PDF, không nhận diện được cấu trúc Điều.

## 7. Điều đã không làm và lý do
1. **Không tự ý cài đặt công cụ OCR:** Tuân thủ quy tắc an toàn của dự án và chỉ định của người dùng.
2. **Không gọi API Gemini hay tạo file `.env`:** Phạm vi phiên chỉ tập trung vào làm sạch và cắt đoạn dữ liệu.
3. **Không viết mã đọc `docs_registry.csv`:** Đúng theo hướng dẫn "bảng chỉ để tham khảo, đừng viết mã đọc nó".
4. **Không in nội dung quy chế ra chat:** Tuân thủ yêu cầu bảo mật thông tin và chống tràn context.

## 8. Việc tiếp theo
1. Người dùng kiểm tra bằng mắt đối chiếu 10 Điều ngẫu nhiên trong thư mục `ai-service/data/chunk_preview/`.
2. Chuẩn bị cho Bước 5 (Embedding và Qdrant) khi người dùng cấp cấu hình và khóa API.

## 9. Câu hỏi cho người dùng
1. Với 15 file PDF scan và 19 file `.doc`, bạn có kế hoạch nhờ phòng Đào tạo xuất lại bản PDF/DOCX có chữ hay dự kiến chạy OCR trước ở máy bên ngoài?
2. Trong các file xem trước ở `ai-service/data/chunk_preview/`, kết quả cắt đoạn của tài liệu quy chế trọng tâm `2023_8_23_16_29_59n.pdf` (Quy định Chuẩn đầu ra ngoại ngữ) đã khớp đúng cấu trúc thực tế của trường chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao cờ trạng thái phải đổi từ chữ thường `"active"` sang chữ in hoa `"ACTIVE"`?
2. Vì sao bộ cắt đoạn lại ưu tiên cắt theo cấu trúc Chương/Điều thay vì cắt cố định theo độ dài ký tự (ví dụ cứ 500 ký tự cắt một lần)?
3. Nếu một câu trong thân văn bản viết: *"Sinh viên không tuân thủ Điều 5 của quy chế này sẽ bị xử lý..."*, biểu thức `DIEU_RE` làm thế nào để không biến câu đó thành một Điều mới?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì cần khớp chính xác với kiểu dữ liệu trạng thái trong CSDL quan hệ PostgreSQL của backend Spring Boot (`documents.status` theo `plan.md`), đồng thời thống nhất giữa bộ lọc tìm kiếm của Vector DB (Qdrant) và BM25.
2. Cắt theo Chương/Điều giúp giữ trọn vẹn ngữ nghĩa của một quy định (điều kiện, đối tượng áp dụng, ngoại lệ nằm chung một đoạn), tránh tình trạng câu bị đứt quãng giữa chừng làm AI suy luận sai hoặc ảo giác.
3. Biểu thức `DIEU_RE` bắt buộc tiêu đề Điều phải có dấu phân cách (`.`, `:`, `-`) hoặc bắt đầu bằng chữ hoa (`(?=[A-ZÀ-ỸĐ])`). Từ "của" bắt đầu bằng chữ thường nên không thỏa mãn điều kiện tạo Điều mới.

</details>
