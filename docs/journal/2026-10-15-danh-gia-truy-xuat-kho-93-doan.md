# Nhật ký 2026-10-15 – Đánh giá truy xuất trên kho tri thức mới (93 đoạn)

## 1. Mục tiêu
Thực hiện đánh giá thực nghiệm truy xuất (retrieval-only) trên kho dữ liệu vừa mở rộng lên 5 văn bản (93 đoạn), đo lường sự thay đổi của các chỉ số Hit Điều, must_have và kiểm chứng độ phủ tri thức thực tế của 2 văn bản mới nạp (Quy chế CTSV và Nội quy học đường).

## 2. Đã làm gì
| File / Thành phần | Thay đổi / Kết quả |
|---|---|
| `ai-service/evaluation/benchmarks_result/benchmark_20261015_081656.json` | Tự động sinh file JSON lưu kết quả đo lường chi tiết 3 câu hỏi, phân rã thời gian và trạng thái trúng Điều, cụm must_have. |
| `ai-service/evaluation/benchmarks_result/cham_tay_20261015_081656.csv` | Tự động sinh file CSV chấm tay UTF-8 BOM 9 cột mở bằng Excel, ghi nhận trích dẫn nguồn thực tế cho từng câu. |
| `docs/progress.md` & `docs/decisions.md` | Cập nhật tiến độ và ghi nhận phát hiện khoa học về sự chuyển dịch phạm vi câu hỏi c03 (học bổng) từ ngoài phạm vi sang trong phạm vi. |

## 3. Vì sao làm như vậy
- **Quyết định: Chạy đánh giá ở chế độ `--retrieval-only` kết hợp `--mode hybrid`**
  - Phương án đã cân nhắc: Phương án A: Gọi cả mô hình sinh LLM để trả lời văn bản. Phương án B: Chỉ đo lường truy xuất (`--retrieval-only`) không gọi LLM (chọn B).
  - Vì sao chọn: Ở bước này, mục tiêu trọng tâm là kiểm tra chất lượng của tầng truy xuất (Retrieval) sau khi nạp thêm 62 đoạn mới từ 2 file Word; việc chạy `--retrieval-only` giúp cô lập hoàn toàn hiệu năng của Qdrant và BM25, không tốn thời gian sinh chữ của LLM, không mất chi phí API và cho ra số liệu đo lường Hit Điều khách quan.
  - Vì sao loại phương án còn lại: Gọi LLM ở bước này sẽ làm tăng thời gian đo lường và làm lu mờ câu hỏi: "Tầng truy xuất có lấy đúng văn bản mới nạp hay không?".
  - Loại căn cứ: [kỹ thuật] và [phương pháp luận NCKH].
  - Đánh đổi: Chỉ số từ chối và tỷ lệ must_have trong câu trả lời hiển thị `N/A` (sẽ được đánh giá khi chạy kèm mô hình sinh).

## 4. Khái niệm mới
- **Chuyển dịch phạm vi tri thức (Knowledge Boundary Shift):**
  - *Ví dụ đời thường:* Trước đây bạn chỉ học cuốn sách Tiếng Anh, ai hỏi về Luật giao thông thì bạn buộc phải nói "tôi không biết" (ngoài phạm vi). Sau khi bạn đọc thêm cuốn sách Luật giao thông, câu hỏi đó lập tức trở thành "trong phạm vi" và bạn có thể trả lời trôi chảy.
  - *Trong RAG:* Khi kho vector được nạp thêm văn bản mới, một số câu hỏi trước đây bị xếp vào nhóm "ngoài phạm vi" (Out-of-scope) sẽ tự động chuyển thành "trong phạm vi" (In-scope). Câu c03 ("Điều kiện xét học bổng...") trước đây hệ thống bắt buộc phải từ chối do kho chỉ có chuẩn ngoại ngữ; nay kho có Quy chế CTSV (Điều 5, 8, 16), tầng truy xuất đã tự động chuyển hướng tìm đúng các Điều về học bổng trong văn bản mới.

## 5. Đã kiểm tra thế nào
- **Lệnh thực thi:**
  ```powershell
  venv\Scripts\python.exe -X utf8 -m scripts.chay_cau_hoi_thu --retrieval-only --mode hybrid
  ```
- **Kết quả thật:**
  ```text
  [THÔNG TIN] Đọc từ file: cau_hoi_thu.csv (Đường dẫn: ai-service\data\cau_hoi_thu.csv)
  [THÔNG TIN] Đọc 3 câu hỏi hợp lệ từ cau_hoi_thu.csv (Tập: 'dev').
  [THÔNG TIN] Đã bỏ qua 10 dòng có câu hỏi rỗng.
  [DỰ TOÁN API] Dự kiến gọi tối đa ~3 lệnh API (Ngưỡng chặn max-calls: 30).
  [XUẤT KẾT QUẢ] Đã lưu file kết quả JSON: benchmark_20261015_081656.json
  [XUẤT KẾT QUẢ] Đã lưu file CSV chấm tay: cham_tay_20261015_081656.csv

  ==========================================================================================
   BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ BENCHMARK THEO NHÓM
  ==========================================================================================
  Nhóm câu hỏi       | Số câu | MH Đoạn        | MH Trả lời     | Hit Điều       | TC Đúng        | TC Nhầm        | TG TB
  ------------------------------------------------------------------------------------------
  ngoai_pham_vi      | 1      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 380 ms
  truc_tiep          | 2      | 87.5% (7/8)    | N/A (retrieval) | 100.0% (2/2)   | N/A            | N/A            | 2312 ms
  ------------------------------------------------------------------------------------------
  TỔNG CỘNG          | 3      | 87.5% (7/8)    | N/A (retrieval) | 100.0% (2/2)   | N/A            | N/A            | 1668 ms
  ==========================================================================================

  [PHÂN RÃ THỜI GIAN TRUNG BÌNH (ms)]:
    - Embedding câu hỏi : 1555.0 ms
    - Tìm kiếm Qdrant   : 104.3 ms
    - Tìm kiếm BM25     : 0.3 ms
    - Sinh chữ LLM      : 0.0 ms
    - Tổng cộng         : 1668.3 ms

  ==========================================================================================
   DANH SÁCH CÁC CỤM MUST_HAVE BỊ THIẾU TRONG CÁC ĐOẠN TRUY XUẤT
  ==========================================================================================
  Câu ID   | Cụm thiếu                 | Chunk IDs đã truy xuất
  ------------------------------------------------------------------------------------------
  c02      | 2 tuần                    | 2023-8-23-16-29-59n-qdkt-d6-1, 2023-8-23-16-29-59n-qdkt-d6-2, 2023-8-23-16-29-59n-qdkt-d4-1, 2023-8-23-16-29-59n-qdkt-d3-1, 2023-8-23-16-29-59n-qdkt-d5-1
  ==========================================================================================
  ```
- **Kết luận:** ĐẠT.
  - Tỷ lệ Hit Điều: **100% (2/2)** câu trực tiếp.
  - Tỷ lệ must_have có trong đoạn: **87.5% (7/8)**. Cụm thiếu duy nhất là "2 tuần" (cần rà soát lại nhãn đáp án trong CSV vì tài liệu gốc quy định thời hạn 2 năm chứ không có 2 tuần).
  - Độ phủ văn bản mới: Câu c03 truy xuất trúng 5 đoạn từ Quy chế CTSV (`2021_8_5_8_33_34A.docx`: Điều 5, Điều 8, Điều 16).
- **Số lệnh gọi API đã dùng:** 3 lệnh embedding (miễn phí, không phát sinh chi phí).

## 6. Chưa chắc chắn, rủi ro, giả định
- Bộ câu hỏi `cau_hoi_thu.csv` hiện mới có 3 câu có nội dung (10 câu còn lại đang rỗng dòng `cau_hoi`). Cần bổ sung các câu hỏi học vụ đa dạng về Quy chế CTSV và Nội quy học đường để kiểm thử quy mô lớn hơn.
- Nhãn `expected_refuse=true` của câu c03 cần được cập nhật sang `false` kèm `expected_dieu=Điều 5|Điều 8|Điều 16` vì kho tri thức hiện nay đã có quy định học bổng.

## 7. Điều đã không làm và lý do
- Chưa tự ý sửa nhãn câu c03 trong `cau_hoi_thu.csv`: Tuân thủ nghiêm ngặt quy tắc cứng trong `GEMINI.md`: "Không bao giờ tự ghi hay sửa nhãn đáp án của bộ kiểm thử đánh giá mà không hỏi người dùng".

## 8. Việc tiếp theo
1. Bổ sung thêm các câu hỏi thử nghiệm cho các dòng c04–c13 trong `cau_hoi_thu.csv` liên quan đến Quy chế CTSV và Nội quy học đường.
2. Thử nghiệm hỏi đáp tương tác qua `scripts/chat_cli.py` với câu hỏi học bổng và điểm rèn luyện.

## 9. Câu hỏi cho người dùng
Bạn có muốn tôi đề xuất cập nhật nhãn cho câu c03 (chuyển `expected_refuse` từ `true` sang `false`, thêm `expected_dieu=Điều 5|Điều 8|Điều 16`) và soạn thảo thêm câu hỏi cho các dòng trống c04–c13 không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao việc mở rộng kho tri thức có thể làm thay đổi bản chất của một câu hỏi kiểm thử từ `ngoai_pham_vi` thành câu hỏi hợp lệ cần trả lời?
2. Trong phân rã thời gian, tại sao thời gian tìm kiếm BM25 (0.3 ms) và Qdrant (104.3 ms) lại chênh lệch lớn so với thời gian gọi embedding câu hỏi (1.555 ms)?
3. Tại sao ở chế độ `--retrieval-only`, chỉ số từ chối đúng và từ chối nhầm lại hiển thị `N/A` thay vì tính theo công thức thông thường?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì tính "trong" hay "ngoài" phạm vi của câu hỏi được định nghĩa tương đối dựa trên nội dung các văn bản có trong kho. Khi nạp thêm văn bản mới (như Quy chế CTSV có chứa thông tin học bổng), câu hỏi về học bổng đã có tài liệu làm căn cứ trả lời, do đó không còn là câu ngoài phạm vi nữa.
2. Vì BM25 và Qdrant chạy hoàn toàn cục bộ trên máy tính (local RAM/SSD), trong khi embedding câu hỏi phải gửi yêu cầu HTTP qua mạng Internet đến API của Google (chịu độ trễ truyền gói tin mạng (RTT) và thời gian xếp hàng xử lý của máy chủ đám mây).
3. Vì việc xác định bot có từ chối hay không phụ thuộc vào tầng suy luận của mô hình sinh (LLM) hoặc ngưỡng an toàn kết hợp với câu trả lời sinh ra. Chế độ retrieval-only không gọi LLM nên không có câu trả lời cuối cùng để thẩm định hành vi từ chối thực tế, hiển thị N/A là hoàn toàn chính xác về mặt phương pháp luận.
  
</details>
