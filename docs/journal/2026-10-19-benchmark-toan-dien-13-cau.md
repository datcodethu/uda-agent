# Nhật ký 2026-10-19 – Đánh giá thực nghiệm: Hoàn thiện bộ kiểm thử và chạy Benchmark toàn diện 13 câu hỏi

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Hoàn thiện toàn bộ 13 câu hỏi trong bộ kiểm thử `cau_hoi_thu.csv` bao phủ 8 archetype câu hỏi thực tế của sinh viên trên kho tri thức mới (5 văn bản, 93 đoạn trích), và chạy benchmark thực nghiệm ở chế độ `--retrieval-only --mode hybrid` để thu thập dữ liệu cơ sở (baseline) phục vụ bài báo khoa học.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/data/cau_hoi_thu.csv` | Cập nhật đầy đủ 13 câu hỏi: đính chính `c02` (`"2 tuần"` -> `"2 năm"`), chuyển `c03` sang nhóm trực tiếp theo Quy chế CTSV (Điều 7), và điền đủ 10 câu hỏi từ `c04` đến `c13` phủ 8 archetype câu hỏi (trực tiếp, tổng hợp, viết tắt, không dấu, gần phạm vi, diễn đạt khác, ngoài phạm vi, chèn lệnh). |
| `docs/decisions.md` | Ghi nhận quyết định phê duyệt bộ kiểm thử chuẩn 13 câu và kết quả benchmark thực nghiệm đạt 100% Hit Điều, 93.3% must-have. |
| `docs/progress.md` | Cập nhật dòng tiến độ hoàn thành "Benchmark toàn diện 13 câu chuẩn". |
| `docs/journal/2026-10-19-benchmark-toan-dien-13-cau.md` | Viết nhật ký khoa học chi tiết phiên làm việc theo mẫu chuẩn `_mau.md`. |

## 3. Vì sao làm như vậy
- **Quyết định 1: Đính chính must_have của câu `c02` từ `"2 tuần"` sang `"2 năm"`**
  - Phương án đã cân nhắc: Giữ nguyên `"2 tuần"` hoặc sửa thành `"2 năm"`.
  - Vì sao chọn: Quy chế gốc tại Điều 6 quy định: *"Chứng chỉ... phải còn thời hạn 2 năm tính đến ngày nộp đơn xin miễn học"*. Nhãn `"2 tuần"` trước đây do AI tạo nhầm và ghi chú rõ *"CHƯA xác minh trong PDF"*.
  - Vì sao loại phương án còn lại: Giữ nguyên sẽ tạo ra lỗi false negative giả tạo khi đánh giá.
  - Loại căn cứ: [tài liệu: `2023_8_23_16_29_59n.pdf`, Điều 6].
  - Đánh đổi: Không.

- **Quyết định 2: Chuyển câu `c03` sang nhóm câu hỏi trực tiếp trong phạm vi**
  - Phương án đã cân nhắc: Giữ `c03` ở nhóm ngoài phạm vi hoặc chuyển sang nhóm trực tiếp theo Quy chế CTSV.
  - Vì sao chọn: Khi kho tri thức đã nạp thêm Quy chế CTSV (`2021_8_5_8_33_34A.docx`), các điều khoản về quyền xét học bổng (Điều 5), tiêu chuẩn khen thưởng (Điều 7, 8) và chính sách học bổng (Điều 16) đã hiện diện trong kho. Chuyển sang trực tiếp giúp đánh giá chính xác năng lực trích xuất của hệ thống.
  - Loại căn cứ: [kỹ thuật] & [tài liệu: `2021_8_5_8_33_34A.docx`].
  - Đánh đổi: Cần cập nhật nhãn `expected_dieu=Điều 7`, `expected_refuse=false`.

- **Quyết định 3: Thiết kế 10 câu hỏi bổ sung bao phủ 8 archetype kinh điển của sinh viên**
  - Phương án đã cân nhắc: Chỉ tạo câu hỏi trực tiếp đơn giản hoặc thiết kế đa dạng theo 8 archetype nghiên cứu.
  - Vì sao chọn: Đề tài NCKH cần chứng minh hệ thống giải quyết được thực trạng sinh viên hay gõ tắt (`sv`, `hb`), gõ không dấu (`triet ly giao duc`), dùng từ khẩu ngữ (`quần đùi`, `dép lê`), hỏi câu ngoài phạm vi (`xe buýt`) hoặc cố tình chèn lệnh (Jailbreak).
  - Loại căn cứ: [tài liệu: `docs/ai-service.md` mục 7 và `docs/plan.md` mục 10.3].
  - Đánh đổi: Độ phức tạp của bộ test tăng lên, làm lộ rõ các trường hợp biên của hệ thống.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Baseline Metric (Điểm chuẩn cơ sở):**
  - *Ví dụ đời thường:* Giống như việc bạn cân và đo chiều cao trước khi bắt đầu một chế độ tập gym kéo dài 3 tháng. Số đo ngày đầu tiên chính là "baseline". Nếu không có baseline, sau này bạn tăng cơ hay giảm mỡ bao nhiêu cũng không có con số để chứng minh.
  - *Trong RAG:* Đây là điểm số đánh giá ban đầu trên kho tri thức trước khi cài đặt thêm các kỹ thuật nâng cao (như mở rộng viết tắt, phân loại ý định, reranking). Mọi cải tiến sau này đều được so sánh với baseline này để xem có thật sự tốt hơn không.
- **Boundary Shift (Chuyển dịch phạm vi tri thức):**
  - *Ví dụ:* Một nhân viên thực tập mới vào công ty chưa đọc sổ tay nhân sự, khi được hỏi về chế độ thai sản thì trả lời: "Tôi không biết, nằm ngoài phạm vi hiểu biết của tôi" (Out-of-Scope). Đến tuần sau khi đã được phát và đọc cuốn sổ tay nhân sự, câu hỏi đó trở thành câu trong phạm vi (In-Scope) và nhân viên phải trả lời chính xác.
  - *Trong RAG:* Khi kho vector được nạp thêm văn bản mới, một số câu hỏi trước đây hệ thống buộc phải từ chối (refuse) nay đã có tài liệu làm căn cứ và phải trả lời được.

## 5. Đã kiểm tra thế nào
- **Kiểm thử đơn vị:**
  - Lệnh: `venv\Scripts\python.exe -m unittest discover -s tests`
  - Kết quả: `Ran 63 tests in 4.547s - OK`.
- **Kiểm thử benchmark thực nghiệm:**
  - Lệnh: `venv\Scripts\python.exe -m scripts.chay_cau_hoi_thu --retrieval-only --mode hybrid`
  - Kết quả thật:
```
==========================================================================================
 BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ BENCHMARK THEO NHÓM
==========================================================================================
Nhóm câu hỏi       | Số câu | MH Đoạn        | MH Trả lời     | Hit Điều       | TC Đúng        | TC Nhầm        | TG TB
------------------------------------------------------------------------------------------
chen_lenh          | 1      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 396 ms
dien_dat_khac      | 1      | 66.7% (2/3)    | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 422 ms
gan_pham_vi        | 2      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 432 ms
khong_dau          | 1      | 75.0% (3/4)    | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 419 ms
ngoai_pham_vi      | 1      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 434 ms
tong_hop           | 1      | 100.0% (3/3)   | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 439 ms
truc_tiep          | 5      | 100.0% (18/18) | N/A (retrieval) | 100.0% (5/5)   | N/A            | N/A            | 875 ms
viet_tat           | 1      | 100.0% (2/2)   | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 493 ms
------------------------------------------------------------------------------------------
TỔNG CỘNG          | 13     | 93.3% (28/30)  | N/A (retrieval) | 100.0% (9/9)   | N/A            | N/A            | 603 ms
==========================================================================================

[PHÂN RÃ THỜI GIAN TRUNG BÌNH (ms)]:
  - Embedding câu hỏi : 579.4 ms
  - Tìm kiếm Qdrant   : 22.2 ms
  - Tìm kiếm BM25     : 0.1 ms
  - Sinh chữ LLM      : 0.0 ms
  - Tổng cộng         : 603.1 ms
```
- **Kết luận:** **ĐẠT**.
  - Hit Điều đạt **100.0% (9/9)** câu trong phạm vi.
  - Must-have đạt **93.3% (28/30)** cụm.
  - Hai cụm bị thiếu có nguyên nhân khách quan được làm sáng tỏ:
    1. Câu `c08` (không dấu): Thiếu cụm `"phát triển bản thân"` do văn bản gốc của trường có lỗi chính tả in thành `"phát triển bản than"`.
    2. Câu `c11` (diễn đạt khác): Thiếu cụm `"dép lê"` do nội quy học đường dùng cụm `"Giày và dép phải có đế không nhọn"` chứ không dùng từ khẩu ngữ `"dép lê"`.
  - File JSON: `evaluation/benchmarks_result/benchmark_20261019_133418.json`.
  - File CSV chấm tay: `evaluation/benchmarks_result/cham_tay_20261019_133418.csv`.
- **Số lệnh gọi API trả phí đã dùng:** 13 lệnh gọi embedding text (0 lệnh gọi LLM generation, an toàn trong hạn mức 30 lệnh).

## 6. Chưa chắc chắn, rủi ro, giả định
- Ở chế độ `--retrieval-only`, hệ thống chỉ đo khả năng trích xuất đoạn liên quan của Hybrid Retriever (Qdrant + BM25 + RRF), chưa đo khả năng từ chối của LLM (ở các câu ngoài phạm vi và chèn lệnh). Cần chạy End-to-End để kiểm tra trọn vẹn vòng lặp.

## 7. Điều đã không làm và lý do
- Chưa chạy sinh toàn bộ câu trả lời LLM (`scripts.chay_cau_hoi_thu` không có cờ `--retrieval-only`) để tránh tiêu tốn nhiều quota Gemini cùng một lúc khi chưa cần thiết.
- Chưa can thiệp sửa chuỗi `"bản than"` trong file PDF/DOCX gốc của trường vì nguyên tắc tôn trọng văn bản nguồn.

## 8. Việc tiếp theo
1. **Triển khai Bước 7 trong `docs/ai-service.md`**:
   - Mở rộng bảng từ viết tắt `data/seed/abbreviations_seed.json` và kiểm tra module `abbreviation_mapper.py`.
   - Xây dựng bộ phân loại ý định `intent_classifier.py` để phát hiện câu hỏi ngoài phạm vi, chào hỏi hoặc câu hỏi cá nhân trước khi tìm kiếm.
2. Thử nghiệm sinh End-to-End LLM có kiểm chứng số liệu (`verifier.py`) trên một số câu hỏi mẫu.

## 9. Câu hỏi cho người dùng
- Bạn có muốn chúng ta chuyển sang triển khai **Bước 7 (Mở rộng từ viết tắt và xây dựng bộ phân loại ý định Intent Classifier)** không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao trong đánh giá RAG khoa học, tỷ lệ **Hit Điều** đạt 100% (9/9) lại là chỉ số quan trọng hơn so với chỉ số so khớp từ khóa chính xác (`must_have`)?
2. Vì sao câu hỏi `c08` bị hệ thống tính là thiếu cụm từ khóa `"phát triển bản thân"`, dù thực tế đoạn Điều 1 Triết lý giáo dục đã được truy xuất ở vị trí số 1?
3. Tại sao ở chế độ `--retrieval-only`, các chỉ số như `TC Đúng` (Từ chối đúng) và `TC Nhầm` (Từ chối nhầm) đều hiển thị là `N/A`?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. **Hit Điều** đo lường năng lực của bộ tìm kiếm (Hybrid Retriever) trong việc xác định trúng văn bản quy phạm pháp luật và Điều khoản điều chỉnh vấn đề. Nếu trúng đúng Điều, mô hình ngôn ngữ lớn (LLM) ở bước sau sẽ có đủ ngữ cảnh chuẩn để đọc hiểu và trả lời. Còn `must_have` chỉ là so khớp chuỗi ký tự cứng, rất dễ bị trượt nếu sinh viên dùng từ đồng nghĩa hoặc văn bản gốc có cách diễn đạt khác.
2. Vì trong văn bản gốc Quyết định 1495 của Nhà trường, mục b) Triết lý giáo dục in lỗi chính tả thành: `"Học để phát triển bản than"`. Thuật toán kiểm tra `must_have` so khớp chuỗi chữ NFC chính xác `"phát triển bản thân"`, do đó không tìm thấy chuỗi này trong đoạn trích dù đoạn trích đã tìm đúng 100%.
3. Vì ở chế độ `--retrieval-only`, hệ thống chỉ chạy bộ tìm kiếm đoạn văn bản (retrieval) mà không kích hoạt mô hình sinh chữ (LLM generation). Hành vi "từ chối" câu hỏi là quyết định do LLM thực hiện dựa trên prompt và ngưỡng điểm tương đồng; khi chưa gọi LLM thì hệ thống chưa thể đưa ra câu trả lời từ chối, do đó các chỉ số từ chối được hiển thị khoa học là `N/A` (Not Applicable).

</details>
