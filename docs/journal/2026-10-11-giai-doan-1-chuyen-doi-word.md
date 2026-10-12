# Nhật ký 2026-10-11 – Giai đoạn 1: Chuyển đổi và đọc tài liệu Word (.doc/.docx) an toàn

## 1. Mục tiêu
Thực hiện Giai đoạn 1 của phương án đọc văn bản Word: Chuyển đổi ngoại tuyến an toàn 19 file `.doc` sang định dạng `.docx` bằng Word COM (`win32com.client.DispatchEx`), xây dựng mô-đun `docx_loader.py` đọc tuần tự nội dung văn bản và bảng theo đúng thứ tự xuất hiện, chuyển đổi bảng dữ liệu thành Markdown và bảng bố cục (1 hàng hoặc 1 cột) thành văn bản thuần, đối chiếu tự động số bảng/hộp văn bản/ảnh vẽ vào `ket_qua_chuyen_doi.csv`, đồng thời bảo đảm hệ thống chính độc lập nền tảng sẵn sàng cho Linux/Docker.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/requirements.txt` | Thêm `python-docx>=1.1.0` và `pywin32>=306; sys_platform == "win32"` để cô lập pywin32 chỉ cài trên Windows. |
| `ai-service/app/pipeline/preprocessor/docx_loader.py` | Tạo mới bộ đọc `.docx` theo thứ tự XML tự nhiên (`iter_block_items`), hàm xử lý bảng `format_table` (giữ bảng 1 hàng hoặc 1 cột dạng text thường, bảng >=2x2 thành Markdown có khử lặp ô gộp), và trích xuất chữ trong hộp văn bản (`w:txbxContent`). |
| `ai-service/app/pipeline/preprocessor/pdf_loader.py` | Bổ sung nạp `.docx` qua `docx_loader`, thêm hàm `check_pdf_health` phát hiện `can_ocr` và phân tích thống kê nhận diện nguy cơ `loi_font`. |
| `ai-service/data/excluded_documents.json` | Cấu hình danh mục tài liệu loại trừ mềm (`phap_luat`, `mau_don`, `loi_font`), không ghi cứng tên file trong code. |
| `.gitignore` | Thêm thư mục `ai-service/data/doc_da_chuyen/` để tránh đưa các file nhị phân trung gian vào git repository. |
| `ai-service/scripts/convert_doc_to_docx.py` | Viết script chuyển đổi .doc bằng `win32com.client.DispatchEx`, kiểm tra môi trường Windows với thông báo lỗi thân thiện nếu chạy trên Linux/Docker, tự động đối chiếu số bảng COM với `python-docx`, kiểm đếm `txbxContent` và `drawing`, trích 2-3 dòng đầu và gợi ý phân loại vào `data/ket_qua_chuyen_doi.csv`. |
| `docs/todo.md` | Ghi nhận chi tiết 5 lỗi cắt đoạn của Giai đoạn 2 (trên file `2023_8_23_16_29_59n.pdf`). |
| `docs/decisions.md` | Bổ sung quyết định: chuyển đổi .doc là thao tác ngoại tuyến 1 lần bằng COM; phương án chia sẻ tập file .docx đã chuyển đổi chờ chủ dự án quyết định. |
| `docs/progress.md` | Cập nhật hoàn thành Giai đoạn 1 (Word). |

## 3. Vì sao làm như vậy

### Khối 1: Dùng Word COM (`DispatchEx`) chỉ để chuyển `.doc` sang `.docx` một lần
- **Quyết định:** Dùng `win32com.client.DispatchEx` mở ngầm một phiên Word riêng biệt, lưu file dưới định dạng `wdFormatXMLDocument` (16), sau đó đọc toàn bộ nội dung bằng thư viện chuẩn `python-docx`.
- **Phương án đã cân nhắc:**
  1. Trích xuất chữ trực tiếp từ COM (`doc.Content.Text`).
  2. Dùng thư viện thuần Python của bên thứ ba như `antiword` hoặc `catdoc`.
  3. Dùng COM chỉ để SaveAs sang `.docx` một lần duy nhất (phương án chọn).
- **Vì sao chọn:** COM `doc.Content.Text` làm phẳng toàn bộ cấu trúc văn bản, mất hoàn toàn cấu trúc cột/hàng của bảng biểu và không trích xuất được metadata chi tiết. `antiword`/`catdoc` hỗ trợ tiếng Việt Unicode kém và khó chạy trên Windows. Chuyển sang `.docx` cho phép dùng `python-docx` phân tích sâu XML DOM, chuẩn hóa bảng và hoàn toàn không phụ thuộc Microsoft Word khi đưa lên server/Docker sau này. Dùng `DispatchEx` thay vì `Dispatch` bảo đảm tạo phiên Word độc lập, khi gọi `Quit()` không làm tắt các file Word người dùng đang mở trên máy.
- **Vì sao loại phương án còn lại:** Lấy text trực tiếp từ COM không đáp ứng được yêu cầu giữ cấu trúc bảng quy chế; hệ thống web admin sau này chạy Linux sẽ không có Word.
- **Loại căn cứ:** [kỹ thuật] & [chỉ đạo người dùng phiên Bước 3 & 4]
- **Đánh đổi:** Cần máy Windows có cài sẵn Office để thực hiện bước chuyển đổi ban đầu.

### Khối 2: Đọc tài liệu tuần tự và phân biệt bảng bố cục với bảng dữ liệu
- **Quyết định:** Sử dụng trình lặp XML `iter_block_items(doc)` để duyệt tuần tự các phần tử con (`w:p` và `w:tbl`). Nếu bảng có số hàng = 1 hoặc số cột = 1 thì coi là bảng bố cục và xuất text thông thường; nếu bảng >= 2x2 thì tạo Markdown table có dòng tiêu đề và khử lặp nội dung ô gộp (`gridSpan` / `vMerge`).
- **Phương án đã cân nhắc:**
  1. Đọc hết `doc.paragraphs` rồi mới đọc `doc.tables`.
  2. Đổi tất cả các bảng sang Markdown table.
  3. Duyệt tuần tự theo vị trí xuất hiện, phân tách bảng bố cục và bảng dữ liệu (phương án chọn).
- **Vì sao chọn:** Văn bản quy chế có các bảng nằm xen kẽ giữa các điều khoản. Nếu đọc tách riêng paragraph rồi table, thứ tự nội dung sẽ bị đảo lộn hoàn toàn. Các bảng bố cục như quốc hiệu, khối chữ ký, nơi nhận nếu đưa vào Markdown table `| --- |` sẽ làm vỡ ngữ nghĩa khi chia chunk. Khử lặp ô gộp giúp tránh hiện tượng một chuỗi văn bản bị nhân bản nhiều lần qua các ô liền kề.
- **Vì sao loại phương án còn lại:** Phương án 1 làm mất ngữ cảnh văn bản; phương án 2 làm ô nhiễm dữ liệu truy xuất bởi các bảng định dạng hành chính.
- **Loại căn cứ:** [kỹ thuật] & [chỉ đạo người dùng]
- **Đánh đổi:** Cần duyệt sâu vào cấu trúc phần tử XML của `python-docx` thay vì dùng API bề mặt.

### Khối 3: Xử lý hộp văn bản (txbxContent) và gắn cờ trạng thái "can_duyet"
- **Quyết định:** Tìm và trích xuất trực tiếp nội dung văn bản trong các thẻ `w:txbxContent` lồng bên trong các đoạn văn; đồng thời nếu phát hiện file có `txbxContent > 0` hoặc `drawing > 0` thì gắn trạng thái `can_duyet` thay vì `ok`.
- **Phương án đã cân nhắc:**
  1. Chỉ đọc các đoạn văn bản chính qua `p.text` mặc định của `python-docx`.
  2. Bỏ qua hộp văn bản và ảnh vì quy chế ít khi đặt nội dung cốt lõi trong shape.
  3. Trích xuất text trong `txbxContent` đồng thời gắn cờ `can_duyet` và thống kê vào CSV (phương án chọn).
- **Vì sao chọn:** Trong file thực tế `2021_11_6_16_22_31g.doc`, ghi chú quan trọng về xác nhận hoạt động ngoài trường nằm trọn trong một hộp văn bản nổi. Nếu dùng `python-docx` mặc định, đoạn này sẽ bị bỏ sót 100%. Bằng cách quét sâu `w:txbxContent`, nội dung được cứu lại đầy đủ, đồng thời cờ `can_duyet` nhắc người phát triển kiểm tra mắt để không sót thông tin.
- **Vì sao loại phương án còn lại:** Bỏ sót văn bản quy định của sinh viên là lỗi nghiêm trọng đối với hệ thống hỏi đáp.
- **Loại căn cứ:** [kỹ thuật] & [thực tế kiểm tra dữ liệu]
- **Đánh đổi:** Tăng độ phức tạp của hàm đọc văn bản.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)
1. **Word COM Automation (`win32com`):**
   - *Khái niệm:* Một cơ chế của Windows cho phép một chương trình (như Python) ra lệnh điều khiển một phần mềm khác (như Microsoft Word) đang cài trên máy thực hiện các tác vụ tự động.
   - *Ví dụ đời thường:* Giống như bạn thuê một trợ lý ngồi trước máy tính mở Word lên, bấm "Lưu thành..." (Save As) sang đuôi `.docx`, rồi tắt Word đi.
2. **Dispatch vs DispatchEx:**
   - *Khái niệm:* `Dispatch` sẽ tìm và tái sử dụng một cửa sổ Word đang mở sẵn nếu có; `DispatchEx` bắt buộc hệ điều hành khởi tạo một tiến trình Word hoàn toàn mới và độc lập.
   - *Ví dụ đời thường:* `Dispatch` giống như bạn vào ngồi chung bàn làm việc với người khác đang soạn thảo; nếu bạn dọn bàn (`Quit()`), tài liệu của người kia bị đóng theo. `DispatchEx` là bạn tự kê một chiếc bàn làm việc riêng trong phòng kín, khi xong việc bạn dọn đúng bàn của mình mà không ảnh hưởng tới ai.
3. **Cấu trúc XML của file .docx (Office Open XML - OOXML):**
   - *Khái niệm:* Bản chất file `.docx` là một file nén zip chứa các file XML bên trong. Đoạn văn được đánh dấu bằng thẻ `<w:p>`, bảng biểu bằng `<w:tbl>`, chữ bên trong hộp văn bản bằng `<w:txbxContent>`.
   - *Ví dụ đời thường:* Giống như một trang web HTML có các thẻ `<p>` và `<table>`, file docx lưu trữ các khối nội dung xếp chồng lên nhau theo thứ tự thẻ XML.

## 5. Đã kiểm tra thế nào
- **Chuyển đổi 19 file .doc:**
  - Lệnh: `$env:PYTHONUTF8=1; venv\Scripts\python.exe -m scripts.convert_doc_to_docx`
  - Kết quả: 19/19 file chuyển đổi thành công sang `.docx`, 19/19 file có số lượng bảng đọc ra từ `python-docx` khớp tuyệt đối 100% với số lượng bảng do Microsoft Word COM báo cáo (`doc.Tables.Count`).
  - Kiểm tra tiến trình: `Get-Process WINWORD` trả về rỗng (0 tiến trình Word chạy ngầm).
- **Trích xuất dữ liệu bảng đa hàng đa cột đối chiếu:**
  - File: `2021_8_5_8_33_34A.docx` (Khung kỷ luật sinh viên).
  - Kết quả: Bảng số 3 (31 hàng, 7 cột) được định dạng Markdown chuẩn, trích xuất đầy đủ 77 giá trị số (số thứ tự từ 1 đến 29, số lần vi phạm 4-8, 9-15, tỷ lệ nghỉ học 25%, v.v.).
- **Chạy kiểm thử cốt lõi (Unit Tests):**
  - Lệnh: `venv\Scripts\python.exe -m unittest discover -s tests -v`
  - Kết quả: 22/22 unit test PASS.
- **Chi phí API:** 0 VNĐ (không gọi API LLM/Embedding).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Giả định:** Tất cả 19 file `.docx` sau khi chuyển đổi từ `.doc` qua Word COM giữ nguyên định dạng gốc và không có lỗi font đặc thù của bảng mã cũ (TCVN3, VNI). Qua kiểm tra sơ bộ, 19 file đều dùng Unicode tiêu chuẩn.
- **Rủi ro:** 14 file có cờ `can_duyet` (do có drawing/ảnh hoặc textbox) cần người dùng rà soát xem có nội dung dạng hình ảnh scan lồng bên trong hay không.

## 7. Điều đã không làm và lý do
- **Chưa sao chép các file `.docx` mới chuyển vào `raw_documents/`:** Theo quy tắc chỉ đạo của người dùng, toàn bộ file đã chuyển phải được người dùng đối chiếu bảng dữ liệu trước khi nạp chính thức.
- **Chưa sửa 5 lỗi cắt đoạn của Giai đoạn 2:** Tuân thủ quy trình hai giai đoạn rõ ràng; chỉ tiến hành Giai đoạn 2 sau khi người dùng phê duyệt kết quả Giai đoạn 1.

## 8. Việc tiếp theo
1. Người dùng kiểm tra đối chiếu các con số trong bảng kỷ luật của file `2021_8_5_8_33_34A.doc` và danh sách phân loại trong `ket_qua_chuyen_doi.csv`.
2. Khi người dùng phê duyệt Giai đoạn 1: Chép các file `.docx` hợp lệ vào kho dữ liệu quy chế và bắt đầu Giai đoạn 2 (tái hiện và khắc phục 5 lỗi cắt đoạn ngữ nghĩa trên file `2023_8_23_16_29_59n.pdf`).

## 9. Câu hỏi cho người dùng
- Thầy/bạn có yêu cầu điều chỉnh thêm về cách định dạng bảng Markdown (ví dụ: cách lặp tiêu đề cho bảng dài) trước khi bước vào Giai đoạn 2 hay không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao không nên dùng `win32com` để trích xuất thẳng toàn bộ văn bản bằng lệnh `doc.Content.Text`?
2. Sự khác biệt giữa `win32com.client.Dispatch` và `win32com.client.DispatchEx` là gì và tại sao trong tự động hóa hàng loạt ta phải dùng `DispatchEx`?
3. Tại sao một bảng chỉ có 1 hàng hoặc 1 cột trong văn bản quy chế không nên được chuyển thành bảng Markdown `| --- |`?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Lệnh `doc.Content.Text` làm phẳng (flatten) toàn bộ văn bản thành một dòng text dài thô, làm mất hoàn toàn cấu trúc cột/hàng của bảng số liệu và đảo lộn thứ tự ngữ cảnh. Đồng thời code dùng COM chỉ chạy được trên Windows có cài Word, không thể chạy trên server Linux hoặc container Docker.
2. `Dispatch` sẽ gắn vào một phiên bản Word đang mở của người dùng nếu có; khi chương trình kết thúc và gọi `word.Quit()`, nó sẽ đóng luôn các tài liệu Word người dùng đang làm việc dở dang. `DispatchEx` tạo một phiên bản ngầm hoàn toàn độc lập, bảo đảm an toàn cho môi trường làm việc của người dùng.
3. Trong các văn bản hành chính Việt Nam, bảng 1 hàng hoặc 1 cột thường chỉ dùng để dàn trang (layout) như: tiêu ngữ bên phải và tên cơ quan bên trái, hoặc nơi nhận bên trái và chữ ký bên phải. Nếu biến thành Markdown table, mô hình AI sẽ hiểu lầm đó là bảng dữ liệu thống kê, làm nhiễu thông tin khi chia chunk và tìm kiếm.

</details>
