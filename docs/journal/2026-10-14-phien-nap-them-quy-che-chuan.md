# Nhật ký 2026-10-14 – Hướng 2: Nạp thêm văn bản quy chế chuẩn vào kho (Đợt 1 & Đợt 2)

## 1. Mục tiêu
Rà soát toàn bộ kho tài liệu (23 PDF và các file Word), phê duyệt và nạp an toàn 4 văn bản quy chế chuẩn của Trường Đại học Đông Á (gồm 2 PDF sứ mệnh/giá trị cốt lõi và 2 văn bản Word nòng cốt: Quy chế Công tác sinh viên và Nội quy học đường) vào kho vector Qdrant và BM25, nâng quy mô kho lên 5 tài liệu và 93 đoạn trích (78.821 ký tự) mà không làm phát sinh lỗi hay trùng lặp chunk_id.

## 2. Đã làm gì
| File / Thành phần | Thay đổi |
|---|---|
| `ai-service/data/raw_documents/` | Tiếp nhận 2 file `.docx` quy chế sinh viên được sao chép từ `doc_da_chuyen/`: `2021_8_5_8_33_34A.docx` và `2021_8_5_8_31_26.docx`. |
| `ai-service/data/docs_registry.csv` | Cập nhật `da_duyet=true` cho 4 văn bản quy chế trường chuẩn: `2023_8_29_8_50_20c.pdf`, `2023_8_29_8_51_2A.pdf`, `2021_8_5_8_31_26.docx`, `2021_8_5_8_33_34A.docx`. |
| `docs/plans/2026-10-14-phien-nap-them-quy-che-chuan.md` | Lập và cập nhật kế hoạch chi tiết nạp theo 2 đợt; ghi nhận kết quả kiểm duyệt dry-run và nạp thật của cả 2 đợt. |
| Kho vector Qdrant (`qdrant_local`) & `chunks.jsonl` | Nạp thành công 72 đoạn mới (10 đoạn ở Đợt 1 + 62 đoạn ở Đợt 2); nâng quy mô toàn kho lên 5 tài liệu, 93 đoạn (78.821 ký tự); 0 trùng lặp `chunk_id`; tự động tái lập chỉ mục BM25. |
| `docs/progress.md` & `docs/decisions.md` | Ghi nhận tiến độ mở rộng kho tri thức và các quyết định phê duyệt tài liệu. |

## 3. Vì sao làm như vậy
- **Quyết định 1: Ưu tiên nạp trước 2 văn bản PDF chuẩn ĐH Đông Á có sẵn trong `raw_documents/` (Đợt 1)**
  - Phương án đã cân nhắc: Phương án A: Tạm dừng để xử lý cả file Word và PDF cùng lúc. Phương án B: Nạp ngay 2 file PDF chuẩn có sẵn trong `raw_documents/` (chọn B).
  - Vì sao chọn: Hai file này là văn bản chính thức của trường về Sứ mệnh, Tầm nhìn, Triết lý giáo dục và Giá trị cốt lõi, nằm sẵn ở `raw_documents/`, văn bản đọc rất tốt, cấu trúc ngắn gọn (mỗi file 5 đoạn, ~3.300 ký tự), cắt đoạn chuẩn xác không có bất kỳ cảnh báo nào. Việc nạp trước giúp mở rộng tri thức ngay lập tức một cách an toàn.
  - Vì sao loại phương án còn lại: Việc gom chung cả các file Word chưa nằm trong `raw_documents/` vào một lần làm tăng độ phức tạp; tách làm 2 đợt giúp kiểm soát chất lượng từng bước rõ ràng.
  - Loại căn cứ: [kỹ thuật] và [thực tế dữ liệu].
  - Đánh đổi: Hai văn bản này mang tính triết lý, sứ mệnh giáo dục chung của trường, chưa có các quy định chi tiết về học vụ hay quyền lợi của sinh viên.

- **Quyết định 2: Tiếp tục duy trì hàng rào cảnh báo bất thường chặn nạp file `2024_11_14_14_26_46A.pdf` (QĐ 2474)**
  - Phương án đã cân nhắc: Dùng cờ `--allow-anomaly` để ép nạp; hoặc tiếp tục để hàng rào chặn.
  - Vì sao chọn: File này có 93.2% số đoạn bị gán dồn vào nhãn "Điều 3" do dùng hệ thống đề mục số thập phân thay vì Điều/Khoản. Cổng nạp nhận diện chính xác và tự động chặn lại.
  - Vì sao loại phương án còn lại: Cưỡng ép nạp tài liệu bị cắt sai cấu trúc sẽ làm suy giảm độ chính xác của cơ chế trích dẫn Điều khoản trong RAG.
  - Loại căn cứ: [kỹ thuật] (hàng rào phát hiện bất thường `check_chunking_anomaly`).
  - Đánh đổi: Kho tạm thời chưa có hướng dẫn về phương pháp học tập đại học cho đến khi nâng cấp bộ chunker nhận diện đề mục thập phân.

- **Quyết định 3: Đưa 2 file `.docx` Quy chế CTSV và Nội quy học đường vào kho (Đợt 2)**
  - Phương án đã cân nhắc: Phương án A: Chờ đợi chuyển đổi và rà soát toàn bộ 19 file Word. Phương án B: Chọn 2 file Word nòng cốt đã chuyển đổi chuẩn và kiểm thử cắt đoạn đạt 0 bất thường để nạp trước (chọn B).
  - Vì sao chọn: Quy chế Công tác sinh viên (53 đoạn) và Nội quy học đường (9 đoạn) là 2 văn bản quan trọng bậc nhất đối với sinh viên (chứa quyền và nghĩa vụ, đánh giá điểm rèn luyện, khen thưởng, kỷ luật, nội quy giảng đường...). Dữ liệu văn bản đã được kiểm tra: phân tách rõ ràng giữa Quyết định ban hành và Quy định kèm theo, phân bổ Điều khoản đều đặn.
  - Vì sao loại phương án còn lại: Rà soát toàn bộ 19 file Word cùng lúc sẽ mất nhiều thời gian, trong khi sinh viên cần hỏi đáp ngay các vấn đề quy chế CTSV.
  - Loại căn cứ: [thực tế dữ liệu] và [kỹ thuật].
  - Đánh đổi: Các file `.doc` cũ trên đĩa vẫn được giữ nguyên và bị cổng nạp chặn an toàn theo cơ chế default-deny (không có trong registry).

## 4. Khái niệm mới
- **Default-Deny trong nạp kho tri thức (Knowledge Base Ingestion):**
  - *Ví dụ đời thường:* Giống như cổng an ninh của một tòa nhà đại sứ quán: mặc định cổng đóng và mọi người đều bị từ chối vào, trừ khi có tên trong danh sách khách mời đã được thẩm định và phê duyệt trước.
  - *Trong RAG:* Script nạp kho mặc định từ chối nạp mọi tài liệu, chỉ những tài liệu thỏa mãn đầy đủ 4 tiêu chí (`da_duyet=true`, `loai=quy_che_truong`, `status=ACTIVE`, file tồn tại hợp lệ) và vượt qua hàng rào kiểm tra bất thường cấu trúc mới được nạp vào kho vector. Điều này ngăn ngừa tài liệu rác, tài liệu hết hạn hoặc văn bản cắt lỗi làm "nhiễm độc" câu trả lời của AI.

## 5. Đã kiểm tra thế nào
- **Lệnh 1 (Dry-run kiểm duyệt Đợt 2):**
  ```powershell
  venv\Scripts\python.exe -X utf8 -m scripts.ingest_approved --status
  ```
  - Kết quả thật:
    ```text
    [DANH SÁCH FILE ĐƯỢC PHÊ DUYỆT (6 file)]:
      1. [SẼ NẠP] 2021_8_5_8_31_26.docx (9 đoạn, 7,344 ký tự)
      2. [SẼ NẠP] 2021_8_5_8_33_34A.docx (53 đoạn, 47,334 ký tự)
      3. [SẼ NẠP] 2023_8_23_16_29_59n.pdf (21 đoạn, 17,551 ký tự - đã có)
      4. [SẼ NẠP] 2023_8_29_8_50_20c.pdf (5 đoạn, 3,264 ký tự - đã có)
      5. [SẼ NẠP] 2023_8_29_8_51_2A.pdf (5 đoạn, 3,328 ký tự - đã có)
      6. [CHẶN - NGHI NGỜ CẮT SAI] 2024_11_14_14_26_46A.pdf (Điều 3 chiếm 93.2%)
    KẾT QUẢ DRY-RUN: Dự kiến nạp 5 file (93 đoạn, 78,821 ký tự). Bị chặn: 52 file.
    ```
- **Lệnh 2 (Nạp thật Đợt 2 vào kho vector & BM25):**
  ```powershell
  venv\Scripts\python.exe -X utf8 -m scripts.ingest_approved --apply --status
  ```
  - Kết quả thật:
    ```text
    ================================================================================
     TÌNH TRẠNG KHO VĂN BẢN QUY CHẾ (CHUNKS.JSONL / QDRANT)
    ================================================================================
    Tổng số tài liệu: 5 | Tổng số đoạn: 93
    Kiểm tra trùng chunk_id: 0 mã trùng (kỳ vọng: 0)
    --------------------------------------------------------------------------------
    Tên tài liệu (doc_name)             | Số đoạn  | Trạng thái | Ngày hiệu lực
    --------------------------------------------------------------------------------
    2021_8_5_8_31_26                    | 9        | ACTIVE     | (trống)
    2021_8_5_8_33_34A                   | 53       | ACTIVE     | (trống)
    2023_8_23_16_29_59n                 | 21       | ACTIVE     | (trống)
    2023_8_29_8_50_20c                  | 5        | ACTIVE     | (trống)
    2023_8_29_8_51_2A                   | 5        | ACTIVE     | (trống)
    ================================================================================
    KẾT QUẢ: Đã nạp thành công 5 file (93 đoạn). Bị chặn: 52 file.
    ```
- **Lệnh 3 (Kiểm thử hồi quy toàn bộ hệ thống):**
  ```powershell
  venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
  ```
  - Kết quả thật: `Ran 63 tests in 4.868s - OK`. Toàn bộ 63/63 unit test đều PASS.
- **Kết luận:** ĐẠT.
- **Số lệnh gọi API trả phí đã dùng:** 0 (gọi 72 lệnh embedding qua mô hình miễn phí, dưới hạn mức 1.500 req/ngày).

## 6. Chưa chắc chắn, rủi ro, giả định
- 15 file PDF dạng scan ảnh trong `raw_documents/` vẫn chưa có lớp văn bản, cần xin lại bản mềm gốc từ trường.
- 17 file Word còn lại trong `doc_da_chuyen/` cần được rà soát chất lượng cắt đoạn trước khi tiếp tục nạp ở các phiên tiếp theo.

## 7. Điều đã không làm và lý do
- Chưa nạp các file Word còn lại: Giữ nguyên tắc từng bước nhỏ, ưu tiên văn bản nòng cốt nhất trước.
- Không dùng `--allow-anomaly` để nạp file 2024: Giữ vững nguyên tắc không nạp dữ liệu cắt lỗi vào kho.

## 8. Việc tiếp theo
1. Chạy thử nghiệm hỏi đáp trên kho mới (5 tài liệu, 93 đoạn) bằng `scripts/chat_cli.py` hoặc `scripts/ask.py` để đánh giá chất lượng trả lời về Quy chế CTSV.
2. Chạy benchmark đánh giá truy xuất qua `scripts/chay_cau_hoi_thu.py` để xem độ phủ của 93 đoạn trích.

## 9. Câu hỏi cho người dùng
Bạn có muốn thử nghiệm hỏi đáp thực tế qua `scripts/chat_cli.py` trên 5 tài liệu vừa nạp, hay muốn chạy benchmark đánh giá truy xuất trên bộ câu hỏi thử nghiệm?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao cơ chế Default-Deny và hàng rào cảnh báo bất thường (anomaly gate) lại đặc biệt quan trọng khi mở rộng kho dữ liệu quy chế cho hệ thống RAG?
2. Việc chia quá trình nạp kho thành các đợt nhỏ (Đợt 1 nạp PDF chuẩn có sẵn, Đợt 2 nạp file Word quy chế CTSV) đem lại lợi thế kỹ thuật gì so với nạp hàng loạt một lần?
3. Khi nạp các file Word (.docx) đã chuyển đổi từ .doc cũ, làm thế nào để đảm bảo hệ thống không bị trùng lặp định danh tài liệu (`doc_name`) hoặc `chunk_id`?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì câu trả lời của RAG phụ thuộc trực tiếp vào chất lượng của các đoạn trích trong kho. Nếu nạp nhầm văn bản cắt sai cấu trúc (như 93% dồn vào một Điều) hoặc tài liệu rác/hết hiệu lực, hệ thống sẽ trích dẫn sai Điều khoản và sinh ra câu trả lời sai lệch (hallucination).
2. Giúp cô lập rủi ro và kiểm chứng độc lập: Đợt 1 thẩm định các file PDF sẵn có không làm thay đổi vị trí tệp; Đợt 2 cần sao chép tệp từ thư mục chuyển đổi Word và cập nhật định dạng mở rộng (.docx). Tách nhỏ giúp dễ kiểm tra, đối soát và rollback nếu có phát sinh sự cố.
3. Hệ thống sử dụng `fpath.stem` (phần tên không chứa phần mở rộng) làm `doc_name`, và cấu trúc `chunk_id` gồm `{doc_name}_{phan}-d{so}-{part}`. Vì file `.doc` cũ bị chặn ngoài cổng nạp (không được duyệt), chỉ có file `.docx` được nạp nên không phát sinh xung đột; script tự động kiểm tra trùng lặp `chunk_id` trên toàn kho (kết quả 0 mã trùng).

</details>
