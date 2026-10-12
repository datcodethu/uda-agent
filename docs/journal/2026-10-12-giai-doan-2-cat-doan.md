# Nhật ký 2026-10-12 – Giai đoạn 2: Cải tiến bộ cắt đoạn và kiểm tra thứ tự Điều

## 1. Mục tiêu
Giải quyết dứt điểm 5 lỗi cắt đoạn phát sinh trên file quy chế `2023_8_23_16_29_59n.pdf` (bảo toàn bảng biểu, xử lý trùng số Điều giữa Quyết định và Quy định kèm theo, chuẩn hóa tiêu đề Điều, cắt ranh giới câu/Khoản có gối đầu, đổi tiền tố sang tên văn bản) và bổ sung tính năng kiểm tra thứ tự Điều ở chế độ cảnh báo mềm.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/preprocessor/cleaner.py` | Bảo vệ các dòng chứa ký tự bảng `\|` không bị khử nhầm khi gặp tiêu đề trang trùng lặp. |
| `ai-service/app/pipeline/preprocessor/pdf_loader.py` | Bổ sung `from pathlib import Path` bị thiếu ở đầu file theo đúng phê duyệt điều kiện (1). |
| `ai-service/app/pipeline/preprocessor/structural_chunker.py` | Sửa 5 lỗi cắt đoạn và thêm kiểm tra thứ tự Điều: (a) bảo tồn dòng bảng và lặp lại header khi tách bảng; (b) phân biệt `quyet_dinh`/`quy_dinh_kem_theo`/`phu_luc`, bỏ hậu tố `-x1`; (c) nhận diện Điều không có tiêu đề, giữ nguyên câu mở đầu trong thân bài; (d) cắt theo Khoản/câu với gối đầu 100-150 ký tự; (e) trích xuất `doc_title` làm tiền tố chunk; thêm hàm `check_article_order`. |
| `ai-service/scripts/preview_chunks.py` | Lọc các file bị loại trừ theo `excluded_documents.json`, truyền `doc_title`, thu thập cảnh báo thứ tự Điều và xuất ra `data/chunk_preview/canh_bao_dieu.txt`. |
| `ai-service/tests/test_core.py` | Bổ sung 7 unit test độc lập với dữ liệu giả lập ngắn: kiểm tra bảng, phân đoạn QĐ/QĐKT, Điều không tiêu đề, gối đầu ranh giới câu, trích xuất tiêu đề văn bản, kiểm tra thứ tự Điều, và nạp file txt qua loader. Toàn bộ 29/29 test PASS. |
| `ai-service/data/chunk_preview/canh_bao_dieu.txt` | Tạo tệp ghi nhận cảnh báo thứ tự Điều tự động (kết quả thực tế: 0 cảnh báo bất thường). |
| `docs/todo.md` | Đánh dấu hoàn thành toàn bộ 5 hạng mục của Giai đoạn 2. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Giai đoạn 2 (Cắt đoạn). |
| `docs/decisions.md` | Bổ sung 4 quyết định kỹ thuật của Giai đoạn 2 đã chốt. |

## 3. Vì sao làm như vậy

### Khối 1: Bảo toàn cấu trúc bảng Markdown và lặp lại header cột khi tách đoạn (Lỗi a)
- **Quyết định:** Giữ nguyên các hàng bảng trong cùng một đoạn; nếu một bảng quá dài vượt ngưỡng kích thước đoạn (1200 ký tự), tách bảng theo từng nhóm hàng và tự động lặp lại các dòng tiêu đề cột (`| Cột 1 | Cột 2 |` và `|---|---|`) ở đầu mỗi phần tiếp theo. Đồng thời bảo vệ các dòng chứa `|` trong `cleaner.py` không bị lọc mất.
- **Phương án đã cân nhắc:**
  1. Trải phẳng bảng thành các dòng văn bản đơn lẻ (cách cũ).
  2. Bỏ qua không cắt bảng dù bảng dài tới đâu (giữ 1 đoạn khổng lồ).
  3. Tách theo nhóm hàng và lặp lại header cột (phương án chọn).
- **Vì sao chọn:** Trong hệ thống RAG, khi mô hình tìm kiếm vector hoặc BM25 truy xuất một đoạn trích giữa bảng, nếu không có dòng tiêu đề cột, mô hình ngôn ngữ sẽ không thể hiểu các ô dữ liệu (ví dụ: điểm số, số tín chỉ, lệ phí) thuộc về cột nào. Lặp lại header giúp mỗi đoạn đều độc lập và tự giải nghĩa được.
- **Vì sao loại phương án còn lại:** Phương án 1 làm mất hoàn toàn quan hệ hàng - cột; phương án 2 tạo ra đoạn quá dài làm suy giảm chất lượng embedding và tràn ngữ cảnh.
- **Loại căn cứ:** [kỹ thuật] & [yêu cầu Giai đoạn 2]
- **Đánh đổi:** Cần logic bóc tách và chèn header phức tạp hơn trong hàm chia nhỏ thân bài.

### Khối 2: Phân biệt các phần văn bản và loại bỏ hậu tố `-x1` (Lỗi b)
- **Quyết định:** Bổ sung trường `phan_van_ban` (`quyet_dinh`, `quy_dinh_kem_theo`, `phu_luc`) vào metadata của Chunk; tự động phát hiện chuyển phần khi gặp dòng tiêu đề "QUY ĐỊNH...", "PHỤ LỤC..." hoặc khi số Điều quay lại Điều 1; tiền tố mã đoạn đổi thành `qd-d1-1`, `qdkt-d1-1`, loại bỏ hoàn toàn hậu tố `-x1`.
- **Phương án đã cân nhắc:**
  1. Giữ nguyên đánh số thứ tự và gắn cờ đếm lặp `-x1`, `-x2` (cách cũ).
  2. Gom Quyết định và Quy định thành 2 tài liệu riêng biệt trên đĩa.
  3. Thêm trường `phan_van_ban` và định danh đoạn theo ngữ cảnh phần (phương án chọn).
- **Vì sao chọn:** Một văn bản quy chế chuẩn Việt Nam thường có 2 phần: Quyết định ban hành (Điều 1 đến 3) và Quy chế/Quy định kèm theo (Điều 1 đến N). Hậu tố `-x1` là giải pháp chắp vá làm mất ngữ nghĩa của Điều 1 ở phần Quy chế chính. Phân chia rõ ràng giúp người dùng hỏi "Điều 1 Quy định đào tạo" sẽ truy xuất trúng phần Quy định thay vì phần Quyết định ban hành.
- **Vì sao loại phương án còn lại:** Phương án 1 làm xấu ID và mất phân biệt ngữ cảnh; phương án 2 đòi hỏi tách file thủ công làm phức tạp khâu tiền xử lý.
- **Loại căn cứ:** [kỹ thuật] & [thực tế văn bản quy chế ĐH Đông Á]
- **Đánh đổi:** Cần thêm biểu thức chính quy để nhận diện chính xác các tiêu đề chuyển phần.

### Khối 3: Chuẩn hóa tiêu đề Điều, không cắt cụt câu quy phạm (Lỗi c)
- **Quyết định:** Chỉ công nhận chuỗi sau "Điều X." là tiêu đề nếu nó đứng cùng dòng (hoặc ngay sau), ngắn hơn 120 ký tự, và KHÔNG kết thúc bằng dấu chấm câu. Nếu vi phạm, gán `dieu_title = ""` (hiển thị `(Không)`) và bảo tồn trọn vẹn câu mở đầu đó trong thân bài của Điều.
- **Phương án đã cân nhắc:**
  1. Cắt cứng 80 ký tự đầu tiên của đoạn làm tiêu đề (cách cũ).
  2. Bỏ qua hoàn toàn tiêu đề Điều, chỉ dùng số Điều.
  3. Kiểm tra độ dài và dấu chấm kết thúc; nếu không phải tiêu đề thì giữ nguyên trong thân bài (phương án chọn).
- **Vì sao chọn:** Nhiều Điều không có tiêu đề mà bắt đầu ngay bằng câu quy phạm: *"Điều 1. Quy định này áp dụng đối với sinh viên..."*. Nếu cắt 80 ký tự làm tiêu đề và xóa khỏi thân bài, câu quy phạm pháp lý sẽ bị đứt cụt, gây mất từ khóa cốt lõi khi tìm kiếm đoạn trích.
- **Vì sao loại phương án còn lại:** Phương án 1 làm cụt câu quy phạm; phương án 2 làm mất thông tin tiêu đề hữu ích của các Điều có đặt tên rõ ràng (ví dụ: *Điều 2. Đối tượng áp dụng*).
- **Loại căn cứ:** [kỹ thuật] & [yêu cầu Giai đoạn 2]
- **Đánh đổi:** Một số Điều ngắn không tiêu đề sẽ hiển thị tiêu đề là `(Không)`.

### Khối 4: Cắt đoạn theo ranh giới câu/Khoản và gối đầu 100-150 ký tự (Lỗi d)
- **Quyết định:** Khi một Điều vượt quá 1200 ký tự, thuật toán ưu tiên cắt tại điểm bắt đầu Khoản mới (`\n1. `, `\n2. `) hoặc kết thúc câu (`. `, `? `, `! `); đoạn tiếp theo được gối đầu (overlap) sạch từ 100 đến 150 ký tự từ câu hoàn chỉnh trước đó; không cắt giữa bảng biểu.
- **Phương án đã cân nhắc:**
  1. Cắt mù theo số ký tự tuyệt đối và không có gối đầu (cách cũ).
  2. Cắt cố định đúng 150 ký tự gối đầu bất kể rơi vào giữa từ hay giữa câu.
  3. Tìm ranh giới câu và gối đầu theo câu trọn vẹn từ 100-150 ký tự (phương án chọn).
- **Vì sao chọn:** Cắt mù giữa câu làm mất ngữ cảnh, khiến mô hình ngôn ngữ đọc một nửa câu vô nghĩa ở cuối đoạn này và một nửa câu lơ lửng ở đầu đoạn sau. Gối đầu theo ranh giới câu giúp mô hình giữ trọn vẹn ngữ nghĩa ngay tại điểm tiếp giáp giữa hai đoạn.
- **Vì sao loại phương án còn lại:** Phương án 1 làm đứt mạch ý; phương án 2 làm xuất hiện các từ bị cắt đôi (như `...h sinh viên...`).
- **Loại căn cứ:** [kỹ thuật RAG chuẩn quốc tế] & [yêu cầu Giai đoạn 2]
- **Đánh đổi:** Tổng ký tự lưu trữ tăng nhẹ do có phần gối đầu giữa các đoạn.

### Khối 5: Kiểm tra thứ tự Điều ở dạng CẢNH BÁO MỀM
- **Quyết định:** Viết hàm `check_article_order` phân tích dãy số Điều trong từng phần văn bản; hỗ trợ cả số thường và hậu tố chữ (ví dụ: Điều 5, Điều 5a, Điều 6); nếu phát hiện nhảy số, trùng số hoặc giảm số thì chỉ ghi cảnh báo vào `ai-service/data/chunk_preview/canh_bao_dieu.txt`, không làm ngắt quá trình cắt đoạn và không từ chối file.
- **Phương án đã cân nhắc:**
  1. Báo lỗi ngoại lệ (raise Exception) và dừng chương trình khi thứ tự sai.
  2. Tự động sửa lại số Điều cho liên tục.
  3. Ghi log cảnh báo mềm vào file riêng, giữ nguyên dữ liệu gốc (phương án chọn).
- **Vì sao chọn:** Văn bản quy chế gốc có thể có những trường hợp đặc thù (Điều bổ sung, Điều bãi bỏ theo quyết định sửa đổi). Hệ thống không được tự tiện sửa số Điều của văn bản pháp lý, cũng không được từ chối văn bản thật của nhà trường nếu không có lệnh của người quản trị.
- **Vì sao loại phương án còn lại:** Phương án 1 làm sập pipeline khi gặp văn bản có cấu trúc đặc biệt; phương án 2 vi phạm nguyên tắc toàn vẹn dữ liệu quy chế.
- **Loại căn cứ:** [yêu cầu giao việc của người dùng]
- **Đánh đổi:** Cần theo dõi thủ công file log `canh_bao_dieu.txt` để phát hiện bất thường nếu có.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)
1. **Overlap (Đoạn gối đầu) trong Chunking:**
   - *Khái niệm:* Kỹ thuật lặp lại một đoạn văn ngắn cuối của Chunk trước vào phần mở đầu của Chunk sau khi một văn bản dài bị chia cắt.
   - *Ví dụ đời thường:* Giống như bạn đọc một cuốn sách giáo trình dày, ở trang cuối có một câu dài bị ngắt giữa chừng. Khi sang trang mới, đầu trang in lại trọn vẹn câu đó để bạn đọc liền mạch suy nghĩ mà không bị quên ý ở trang trước.
2. **Table Header Propagation (Lặp lại dòng tiêu đề bảng):**
   - *Khái niệm:* Khi một bảng số liệu quá dài bị cắt thành nhiều đoạn khác nhau, hệ thống tự động chèn lại dòng tên cột ở đầu mỗi đoạn mới.
   - *Ví dụ đời thường:* Giống như xem bảng điểm học tập có 100 hàng in trên 3 trang A4. Nếu trang 2 và trang 3 không in lại dòng tiêu đề "Môn học - Số tín chỉ - Điểm thi", bạn nhìn vào con số sẽ không biết số đó là điểm thi hay số tín chỉ.
3. **Cảnh báo mềm (Soft Warning / Non-breaking Warning):**
   - *Khái niệm:* Một cơ chế kiểm tra phát hiện điều bất thường nhưng chỉ ghi nhận vào sổ nhật ký cảnh báo để con người xem xét, không làm dừng hay sập chương trình đang chạy.
   - *Ví dụ đời thường:* Giống như đèn báo nhắc nhở sắp hết nước rửa kính trên ô tô: xe vẫn chạy bình thường đưa bạn về đích, nhưng đèn sáng để bạn biết kiểm tra khi rảnh.

## 5. Đã kiểm tra thế nào
- **Lệnh 1 (Chạy toàn bộ unit test):**
```powershell
$env:PYTHONUTF8='1'; venv\Scripts\python.exe -m unittest discover -s tests -v
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
test_load_text_from_txt (test_core.TestPdfLoader.test_load_text_from_txt) ... ok
test_slug (test_core.TestSlug.test_slug) ... ok
test_all_supported (test_core.TestVerifier.test_all_supported) ... ok
test_citation_markers_ignored (test_core.TestVerifier.test_citation_markers_ignored) ... ok
test_detects_wrong_number (test_core.TestVerifier.test_detects_wrong_number) ... ok
test_thousand_separators_normalized (test_core.TestVerifier.test_thousand_separators_normalized) ... ok

----------------------------------------------------------------------
Ran 29 tests in 0.023s

OK
```

- **Lệnh 2 (Chạy tạo preview chunks và kiểm tra thứ tự Điều trên toàn bộ file quy chế):**
```powershell
$env:PYTHONUTF8='1'; venv\Scripts\python.exe -m scripts.preview_chunks
```
- **Kết quả thật:**
  - Hoàn tất xuất preview cho toàn bộ các file PDF hợp lệ trong `data/raw_documents/`.
  - File cảnh báo `data/chunk_preview/canh_bao_dieu.txt` ghi nhận: `Tổng số cảnh báo phát hiện: 0`.
- **Kết luận:** ĐẠT 100%.
- **Số lệnh gọi API trả phí đã dùng:** 0 (hoàn toàn miễn phí, xử lý thuật toán offline).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Giả định:** Tiêu đề chuyển tiếp văn bản ("QUY ĐỊNH...", "PHỤ LỤC...") xuất hiện độc lập trên một dòng hoặc số Điều quay về 1 là dấu hiệu đáng tin cậy để chuyển sang phân đoạn mới.
- **Rủi ro:** Nếu văn bản quy chế có định dạng bảng Markdown cực kỳ phức tạp (bảng lồng bảng hoặc bảng không có đường viền `|`), bộ bóc tách có thể xem là văn bản thường. Tuy nhiên ở Giai đoạn 1 chúng ta đã chuẩn hóa bảng `.docx` sang Markdown tiêu chuẩn có phân cách `|`.

## 7. Điều đã không làm và lý do
- Không sửa các unit test cũ: Toàn bộ 22 unit test ban đầu được giữ nguyên vẹn 100%, bảo đảm tương thích ngược tuyệt đối.
- Không tự ý sửa nội dung quy chế: Mọi thao tác chỉ tác động lên thuật toán phân tách, không thay đổi ngữ nghĩa nguyên bản.
- Không ngắt chương trình khi có cảnh báo thứ tự Điều: Tuân thủ yêu cầu chế độ CẢNH BÁO MỀM.

## 8. Việc tiếp theo
- Chuẩn bị bước đánh giá chất lượng truy xuất (Retrieval Evaluation) và tích hợp các file Word đã chuyển đổi (.docx) vào pipeline tạo kho chunks hoàn chỉnh.

## 9. Câu hỏi cho người dùng
- Không có câu hỏi ngăn trở. Các bước đã hoàn tất đúng kế hoạch và tiêu chí đề ra.

## 10. Ba câu tự kiểm tra hiểu bài
1. Vì sao khi cắt một bảng số liệu quá dài thành nhiều đoạn, chúng ta bắt buộc phải lặp lại dòng tiêu đề (header) ở đầu mỗi đoạn tiếp theo?
2. Tại sao việc loại bỏ hậu tố `-x1` và thay bằng mã phần văn bản (`qd-d1-1`, `qdkt-d1-1`) lại giúp cải thiện độ chính xác khi chatbot trả lời người dùng?
3. Tại sao kiểm tra thứ tự Điều chỉ nên đặt ở mức "cảnh báo mềm" (ghi log) mà không được ném lỗi (raise Exception) dừng chương trình?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì trong RAG, mô hình truy xuất một đoạn đơn lẻ. Nếu không có dòng tiêu đề cột, đoạn trích sẽ chỉ chứa các con số và văn bản vô nghĩa, khiến mô hình AI không thể biết giá trị đó thuộc về cột điểm, học phí hay số tín chỉ nào.
2. Vì một văn bản quy chế chuẩn thường có 2 phần riêng biệt cùng chứa Điều 1 (Điều 1 của Quyết định ban hành và Điều 1 của Quy chế thực thi). Gán mã `qdkt-d1-1` giúp phân biệt chính xác văn bản mà không làm hỏng tính định danh của Điều.
3. Vì văn bản hành chính thực tế có thể có các Điều đặc biệt (Điều bổ sung 5a, hoặc các Điều bị bãi bỏ dẫn đến nhảy số) hoàn toàn hợp lệ theo luật pháp. Dừng chương trình sẽ làm tê liệt toàn bộ hệ thống xử lý tài liệu.

</details>
