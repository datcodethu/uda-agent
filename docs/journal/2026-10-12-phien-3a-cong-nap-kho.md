# Nhật ký 2026-10-12 – Phiên 3A: Cổng nạp kho theo bảng đăng ký (docs_registry.csv)

## 1. Mục tiêu
Thiết lập cổng kiểm soát nạp tài liệu vào kho vector và BM25 theo bảng đăng ký `docs_registry.csv` với cơ chế Default-Deny nghiêm ngặt, hỗ trợ chế độ xem trước an toàn `--dry-run` mặc định và bổ sung metadata hiệu lực pháp lý vào từng đoạn trích mà không tốn chi phí gọi API.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/ingest_approved.py` | Tạo mới script cổng nạp kho: đọc `docs_registry.csv` (UTF-8 BOM), kiểm tra 3 điều kiện (`da_duyet=true`, `loai=quy_che_truong`, `status=ACTIVE`) và đối chiếu file thực tế trong `raw_documents`; mặc định chạy `--dry-run` xem trước thống kê; chỉ nạp thật khi có `--apply`. |
| `ai-service/scripts/ingest_folder.py` | Sửa script cũ: in cảnh báo hướng dẫn chuyển sang dùng `ingest_approved.py` và thoát ngay, không nạp bất kỳ file nào. |
| `ai-service/app/pipeline/index_service.py` | Nâng cấp `index_document`: hỗ trợ tham số tùy chọn `meta` và `doc_title`, làm giàu metadata cho từng chunk và chuyển `doc_title` vào tiền tố đoạn. |
| `ai-service/app/pipeline/rag_pipeline.py` | Cập nhật hàm `_sources`: bổ sung `effective_date` và `doc_number` vào từng nguồn trích dẫn trả về nếu chunk có thông tin này. |
| `ai-service/tests/test_core.py` | Bổ sung lớp kiểm thử `TestIngestApproved` gồm 9 test case độc lập: kiểm tra chọn file hợp lệ, chặn file không đăng ký, chặn `da_duyet=false`, chặn `loai=phap_luat`, chặn `status=EXPIRED`, chặn file ảo không có trên đĩa, xác minh chế độ dry-run, kiểm tra `_sources` gắn metadata, và kiểm tra `ingest_folder` in cảnh báo. Nâng tổng số test lên 38/38 PASS. |
| `docs/progress.md` | Cập nhật hoàn thành mục Phiên 3A (Cổng nạp kho theo bảng đăng ký). |
| `docs/decisions.md` | Bổ sung quyết định kỹ thuật về cổng nạp kho và mã hóa BOM UTF-8. |

## 3. Vì sao làm như vậy

### Khối 1: Cơ chế kiểm soát nạp mặc định cấm (Default-Deny)
- **Quyết định:** Mọi file trong thư mục `raw_documents` nếu không có dòng trong bảng đăng ký `docs_registry.csv` hoặc thiếu bất kỳ điều kiện nào (`da_duyet != true`, `loai != quy_che_truong`, `status != ACTIVE`, file không tồn tại trên đĩa) đều bị chặn và thông báo lý do cụ thể.
- **Phương án đã cân nhắc:**
  1. Nạp tất cả các file có đuôi `.pdf`/`.docx` trong thư mục (cách cũ của `ingest_folder.py`).
  2. Chỉ lọc qua các dòng trong bảng CSV mà không đối chiếu các file dư thừa trên đĩa.
  3. Quét đối chiếu 2 chiều: bảng CSV và thư mục đĩa (phương án chọn).
- **Vì sao chọn:** Trong hệ thống RAG học vụ trường đại học, việc nạp nhầm tài liệu cũ hết hạn, tài liệu mẫu đơn, hoặc văn bản luật chung sẽ làm loãng độ chính xác của vector search và khiến chatbot trả lời sai quy chế hiện hành của trường.
- **Vì sao loại phương án còn lại:** Phương án 1 không có kiểm duyệt; phương án 2 bỏ sót nguy cơ có file rác/file nhạy cảm nằm sẵn trong thư mục mà không ai quản lý.
- **Loại căn cứ:** [tài liệu: GEMINI.md & docs/ai-service.md mục 4.4]
- **Đánh đổi:** Cần duy trì bảng đăng ký CSV chuẩn xác trước khi nạp tài liệu mới.

### Khối 2: Chế độ kiểm duyệt Dry-run là mặc định
- **Quyết định:** Lệnh `python -m scripts.ingest_approved` mặc định chạy ở chế độ `--dry-run`: tính toán trước số đoạn và tổng ký tự trong bộ nhớ, in báo cáo chi tiết mà tuyệt đối không gọi API embedding Gemini, không ghi Qdrant, không ghi `chunks.jsonl`. Chỉ khi có cờ tường minh `--apply` mới tiến hành nạp thật.
- **Phương án đã cân nhắc:**
  1. Nạp thẳng dữ liệu vào DB mỗi khi chạy script.
  2. Thêm cờ `--dry-run` nhưng mặc định là nạp thật.
  3. Mặc định là `--dry-run`, chỉ nạp khi có `--apply` (phương án chọn).
- **Vì sao chọn:** Chi phí gọi API embedding và dung lượng vector database cần được bảo vệ tối đa. Người quản trị cần xem trước danh sách file sẽ nạp và các file bị chặn để phát hiện sai sót trước khi ghi đè dữ liệu kho.
- **Vì sao loại phương án còn lại:** Phương án 1 và 2 dễ dẫn đến thao tác nhầm lẫn làm hỏng kho vector hoặc tốn hạn mức API.
- **Loại căn cứ:** [yêu cầu giao việc Phiên 3A]
- **Đánh đổi:** Người dùng phải gõ thêm cờ `--apply` khi muốn nạp dữ liệu thật.

### Khối 3: Xử lý UTF-8 có BOM bằng `encoding="utf-8-sig"`
- **Quyết định:** Sử dụng chuẩn mã hóa `utf-8-sig` khi mở đọc tệp CSV trong Python.
- **Phương án đã cân nhắc:**
  1. Dùng `encoding="utf-8"` thông thường.
  2. Cắt thủ công chuỗi ký tự byte đầu tiên.
  3. Dùng `encoding="utf-8-sig"` có sẵn của thư viện chuẩn Python (phương án chọn).
- **Vì sao chọn:** Trên hệ điều hành Windows, phần mềm Microsoft Excel thường tự động gắn tiền tố byte order mark (BOM `\xef\xbb\xbf`) vào đầu file CSV. Nếu dùng `utf-8`, cột đầu tiên `doc_id` sẽ bị biến thành `\ufeffdoc_id`, gây lỗi truy cập dictionary. `utf-8-sig` tự động nuốt BOM và hoạt động trơn tru với cả file có hoặc không có BOM.
- **Vì sao loại phương án còn lại:** Phương án 1 gây lỗi key dictionary; phương án 2 thủ công và dễ vỡ khi file không có BOM.
- **Loại căn cứ:** [kỹ thuật]
- **Đánh đổi:** Không có.

### Khối 4: Làm giàu Metadata trong Chunks và Nguồn trích dẫn
- **Quyết định:** Bổ sung metadata từ bảng (`doc_id`, `doc_title`, `doc_number`, `effective_date`, `category`, `applies_to`) vào từng chunk qua `index_service.py` và đưa `effective_date`, `doc_number` vào `rag_pipeline._sources`.
- **Phương án đã cân nhắc:**
  1. Chỉ lưu `doc_name` và `dieu` như phiên bản ban đầu.
  2. Bổ sung đầy đủ thông tin pháp lý từ bảng đăng ký (phương án chọn).
- **Vì sao chọn:** Phù hợp với thiết kế tại `plan.md` mục 5.1 và `docs/ai-service.md` mục 4.4. Giúp giao diện sinh viên hiển thị được số hiệu văn bản (ví dụ: Quyết định 123/QĐ-ĐHĐA) và ngày có hiệu lực để sinh viên tin tưởng câu trả lời.
- **Vì sao loại phương án còn lại:** Phương án 1 thiếu ngữ cảnh pháp lý cần thiết cho một hệ thống hỏi đáp văn bản quy phạm.
- **Loại căn cứ:** [tài liệu: docs/ai-service.md mục 4.4]
- **Đánh đổi:** Kích thước mỗi bản ghi JSONL và payload trên Qdrant tăng nhẹ.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)
1. **Nguyên tắc "Mặc định từ chối" (Default-Deny):**
   - *Khái niệm:* Một chính sách bảo mật mà theo đó mọi thứ đều bị cấm, trừ những thứ được ghi danh cụ thể trong danh sách trắng (whitelist) và đáp ứng đầy đủ điều kiện.
   - *Ví dụ đời thường:* Giống như cổng kiểm soát vé vào cổng trường thi đại học. Nếu bạn không có tên trong danh sách phòng thi hoặc quên mang thẻ dự thi, giám thị sẽ chặn lại ngay ở cổng chứ không cho vào thi rồi mới xét sau.
2. **Chế độ chạy thử (Dry-Run):**
   - *Khái niệm:* Chế độ chạy mô phỏng toàn bộ tiến trình để kiểm tra lỗi và tính toán kết quả dự kiến mà không thực hiện bất kỳ thay đổi nào lên dữ liệu thật (không ghi đĩa, không ghi DB).
   - *Ví dụ đời thường:* Giống như việc tổng duyệt một chương trình văn nghệ: các đội hình chạy thử vị trí trên sân khấu, căn chỉnh thời gian nhưng chưa bật loa công suất lớn và chưa phát vé cho khán giả.
3. **BOM (Byte Order Mark) trong UTF-8:**
   - *Khái niệm:* Ký tự đặc biệt (`\ufeff`) đặt ở đầu tệp văn bản để báo hiệu thứ tự byte và kiểu mã hóa.
   - *Ví dụ đời thường:* Giống như chiếc bìa màu đánh dấu đặt ở trang đầu tiên của tập tài liệu. Nếu người đọc không biết quy ước, họ sẽ đọc nhầm chiếc bìa đó thành chữ của trang nội dung đầu tiên.

## 5. Đã kiểm tra thế nào
- **Lệnh 1 (Chạy toàn bộ unit test với môi trường giả lập):**
```powershell
$env:PYTHONUTF8='1'; venv\Scripts\python.exe -m unittest discover -s tests -v
```
- **Kết quả thật:**
```
Ran 38 tests in 4.667s

OK
```
*(Toàn bộ 29 test cũ giữ nguyên + 9 test mới viết thêm đều PASS 100%).*

- **Lệnh 2 (Chạy thử script cũ ingest_folder để kiểm tra cảnh báo):**
```powershell
$env:PYTHONUTF8='1'; venv\Scripts\python.exe -m scripts.ingest_folder
```
- **Kết quả thật:**
```
CẢNH BÁO: scripts/ingest_folder.py đã ngừng sử dụng và được thay thế bằng scripts/ingest_approved.py.
Vui lòng sử dụng cú pháp mới để kiểm soát nạp theo bảng đăng ký:
    python -m scripts.ingest_approved          (mặc định --dry-run để xem trước)
    python -m scripts.ingest_approved --apply  (nạp thật vào kho)
```
- **Lệnh 3 (Chạy thử --dry-run trên thư mục hiện tại):**
```powershell
$env:PYTHONUTF8='1'; venv\Scripts\python.exe -m scripts.ingest_approved --dry-run
```
- **Kết quả thật:**
```
CẢNH BÁO: Bảng đăng ký không tồn tại: E:\workspace\donga-rag-system\ai-service\data\docs_registry.csv
```
- **Kết luận:** ĐẠT.
- **Số lệnh gọi API trả phí đã dùng:** 0 (hoàn toàn xử lý thuật toán offline và dữ liệu giả lập).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Điểm chưa chắc chắn:** Tệp `docs_registry.csv` thực tế của nhà trường hiện chưa được đặt trong thư mục `ai-service/data/` (chỉ có file mẫu `docs_registry_mau.csv`), do đó lệnh chạy dry-run trên dữ liệu thật đang thông báo chờ file này từ người dùng.
- **Rủi ro:** Người dùng điền giá trị `da_duyet` dạng tiếng Việt ("rồi", "đã duyệt") thay vì `true`. Biện pháp: Code đã hỗ trợ không phân biệt hoa thường (`TRUE`, `True`, `true`), tài liệu hướng dẫn cần nhắc điền đúng `true`/`false`.

## 7. Điều đã không làm và lý do
- Không tự tiện tạo hay sửa dữ liệu nhãn trong các bộ kiểm thử đánh giá.
- Không sửa bất kỳ bài unit test nào có từ trước (bảo toàn 100% 29 test).
- Không gọi API embedding hay chạm vào database Qdrant thật trong phiên này.

## 8. Việc tiếp theo
- Người dùng chuẩn bị/copy file `docs_registry.csv` thật vào `ai-service/data/` để tiến hành chạy dry-run nghiệm thu số liệu thực tế của toàn bộ kho tài liệu nhà trường.

## 9. Câu hỏi cho người dùng
- Bạn đã có file `docs_registry.csv` chuẩn bị cho các tài liệu thật chưa, hay bạn muốn tôi tạo một script hỗ trợ sinh trước file khung `docs_registry.csv` từ các file hiện có trong `raw_documents`?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao chế độ nạp kho theo bảng đăng ký lại cần áp dụng nguyên tắc Default-Deny (mặc định cấm) thay vì tự động nạp mọi file có trong thư mục?
2. Ký tự BOM (Byte Order Mark) xuất hiện khi nào, và vì sao trong Python nên dùng `encoding="utf-8-sig"` thay vì `encoding="utf-8"` khi đọc file CSV xuất từ Excel?
3. Tại sao `--dry-run` phải là chế độ mặc định của script `ingest_approved.py` thay vì nạp ngay vào cơ sở dữ liệu?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Để bảo vệ chất lượng câu trả lời của chatbot: ngăn chặn việc vô tình nạp tài liệu hết hiệu lực, văn bản pháp luật ngoài phạm vi trường, biểu mẫu rác, hoặc file chưa qua phòng Đào tạo thẩm định.
2. BOM thường được Microsoft Excel trên Windows tự động chèn vào đầu file CSV UTF-8. Dùng `utf-8` thông thường sẽ khiến tên cột đầu tiên bị dính ký tự lạ (`\ufeffdoc_id`), làm code không tìm thấy cột `doc_id`. `utf-8-sig` giúp tự động nhận diện và bóc bỏ BOM an toàn.
3. Vì việc embedding tài liệu lên kho vector tốn chi phí gọi API và thời gian tính toán. Chế độ dry-run giúp người quản trị rà soát trước danh sách các file được duyệt, số đoạn và lý do bị chặn mà không làm biến đổi dữ liệu hay phát sinh chi phí ngoài ý muốn.

</details>
