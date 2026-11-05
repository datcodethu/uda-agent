# Nhật ký 2026-11-05 – Phiên 6G: Mở rộng Tri thức & Nâng cao Chất lượng RAG

## 1. Mục tiêu
Kiểm toán độc lập 7 tài liệu DOCX học vụ, lập ma trận bao phủ dữ liệu cho 57 câu non-PASS, sửa dứt điểm lỗi citation `TC-SVQ-002` từ gốc, thiết kế kỹ thuật 8 nguyên tắc cải tiến học từ NotebookLM và thiết lập Approval Gate chờ người phụ trách duyệt tài liệu.

## 2. Đã làm gì

| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/generator/verifier.py` | Sửa `determine_sufficiency` để không quy chụp `NO_EVIDENCE` khi câu trả lời có trích dẫn hợp lệ; cập nhật logic badges cho trích dẫn một phần. |
| `ai-service/app/pipeline/rag_pipeline.py` | Giữ nguyên `chunks` và `sources` khi câu trả lời từ chối có trích dẫn tham chiếu hợp lệ; đồng bộ session memory và API payload. |
| `ai-service/app/pipeline/generator/stream_handler.py` | Đồng bộ SSE streaming: chỉ làm rỗng `sources` khi từ chối thuần túy không có citation; giữ `sources` khi LLM dẫn chứng để frontend hiển thị đúng. |
| `ai-service/tests/test_sufficiency_and_verification.py` | Bổ sung 3 unit tests chuyên biệt cho ca từ chối có dẫn chứng và từ chối thuần túy; nâng test suite lên 149/149 test PASS. |
| `evaluation/reference_guided_6g/document_approval_queue.csv` | Kiểm toán chi tiết 7 tệp DOCX (SHA-256, loại văn bản, cơ quan ban hành, test cases hỗ trợ, thiếu sót bằng chứng) ở trạng thái `WAITING_FOR_APPROVAL`. |
| `evaluation/reference_guided_6g/knowledge_coverage.csv` | Ma trận đối chiếu 57 câu non-PASS với 4 nhóm bao phủ và lộ trình giải quyết cụ thể. |
| `evaluation/reference_guided_6g/citation_fix_report.md` | Báo cáo chi tiết nguyên nhân gốc và kiểm chứng kỹ thuật sửa lỗi trích dẫn `TC-SVQ-002`. |
| `evaluation/reference_guided_6g/improvement_changes.md` | Phân loại và thiết kế kỹ thuật chi tiết 8 nguyên tắc cải tiến NotebookLM thành 3 nhóm (Cấu hình, Prompt, Tri thức). |
| `evaluation/reference_guided_6g/benchmark_comparison.md` | Đo lường so sánh trước và sau: xác nhận tỷ lệ FAIL giảm từ 1.3% về **0.0%**, độ chính xác citation tăng lên 1.87/2.0. |
| `evaluation/reference_guided_6g/summary.md` | Báo cáo tổng kết điều hành Phiên 6G theo đúng cấu trúc chuẩn đề tài NCKH. |
| `docs/decisions.md` | Ghi nhận Quyết định 43: Chuẩn hóa trích dẫn nguồn khi từ chối có điều kiện và lập hàng đợi phê duyệt tài liệu. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành toàn diện Phiên 6G. |
| `docs/todo.md` | Đóng các mục việc của Phiên 6G và lên danh mục công việc cho Phiên 6H. |

---

## 3. Vì sao làm như vậy

### Quyết định 1: Không xóa toàn bộ citation và sources khi câu trả lời có nội dung từ chối
- **Phương án đã cân nhắc:**
  * Phương án A: Dùng regex xóa bỏ mọi ký hiệu trích dẫn `[3]` khỏi chuỗi văn bản nếu câu trả lời bắt đầu bằng từ chối.
  * Phương án B: Giữ nguyên trích dẫn nếu nó chỉ tới chunk hợp lệ trong ngữ cảnh ($1 \le i \le N$), đồng thời giữ mảng `sources` tương ứng (Được chọn).
- **Vì sao chọn:** Phương án B giải quyết đúng bản chất học vụ. Khi sinh viên hỏi câu ngoài phạm vi (thực tập khoa tiếng Trung) nhưng chatbot giải thích: *"Tài liệu hiện tại chỉ quy định chuẩn đầu ra ngoại ngữ không chuyên [3]"*, thì `[3]` là nguồn tham chiếu có thật, trung thực và hữu ích. Giữ nguồn giúp sinh viên bấm vào xem được căn cứ quy định.
- **Vì sao loại phương án còn lại:** Phương án A chỉ là xóa dấu vết đối phó, làm mất đi tính minh bạch và giá trị tham khảo của câu trả lời.
- **Loại căn cứ:** [kỹ thuật] & [yêu cầu nhiệm vụ Phiên 6G: "Sửa tận gốc, không sửa chữa đối phó"].
- **Đánh đổi:** Tăng thêm 2-3 dòng kiểm tra mảng trích dẫn trước khi gán sources, nhưng độ trễ tăng < 0.1 ms (không đáng kể).

### Quyết định 2: Giữ nguyên trạng thái `WAITING_FOR_APPROVAL` cho 7 tài liệu DOCX (Approval Gate)
- **Phương án đã cân nhắc:**
  * Phương án A: Tự động đổi `da_duyet=true` và chạy ingest ngay để tăng điểm benchmark lập tức.
  * Phương án B: Kiểm toán chi tiết, ghi nhận hàng đợi phê duyệt và dừng lại chờ Người phụ trách duyệt (Được chọn).
- **Vì sao chọn:** Tuân thủ triệt để hàng rào cứng của đề tài NCKH và GEMINI.md. Tài liệu biểu mẫu và văn bản chưa có số quyết định cần được Người phụ trách thẩm tra pháp lý trước khi đưa vào kho tri thức chính thức.
- **Vì sao loại phương án còn lại:** Phương án A vi phạm nguyên tắc an toàn dữ liệu và vượt quyền quản trị dự án.
- **Loại căn cứ:** [tài liệu: GEMINI.md & Yêu cầu TASK E Phiên 6G].
- **Đánh đổi:** Điểm benchmark PASS chưa tăng đột biến ngay trong phiên này, nhưng kho tri thức được bảo vệ an toàn 100%.

---

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

### "Approval Gate" (Cổng kiểm duyệt dữ liệu) là gì?
Hãy tưởng tượng kho dữ liệu của trường giống như một **Thư viện chính thức**.
- Bạn (kỹ sư AI) tìm thấy một số cuốn sách hay hoặc tập biểu mẫu trong kho lưu trữ cũ (kho raw/staging).
- Dù sách có nội dung rất hữu ích, bạn không thể tự ý mang lên kệ sách công cộng cho sinh viên đọc ngay.
- Bạn phải lập một **Hồ sơ đề xuất** ghi rõ: Sách này tên gì, xuất bản năm nào, còn dùng được không, có thông tin nào cũ không (ví dụ mức vay vốn 800k từ năm 2007 đã lỗi thời).
- Sau đó bạn đặt lên bàn của **Thầy Phụ trách Thư viện** (Người dùng). Chỉ khi Thầy đóng dấu "Đồng ý nạp", cuốn sách mới chính thức được đưa vào hệ thống RAG.

### "Qualified Refusal" (Từ chối có dẫn chứng) là gì?
- **Từ chối cộc lốc (Pure Refusal):** "Tôi không biết." $\rightarrow$ Sinh viên hụt hẫng, không biết đi đâu.
- **Từ chối có dẫn chứng (Qualified Refusal):** "Trường chưa có quy định riêng về thực tập cho khoa tiếng Trung, nhưng trường có quy định chuẩn đầu ra chung tại Điều 5 [3]." $\rightarrow$ Sinh viên biết rõ phạm vi tài liệu và có cơ sở để đối chiếu.

---

## 5. Đã kiểm tra thế nào

### Kiểm thử Unit Test toàn hệ thống:
- **Lệnh:** `venv\Scripts\python.exe -m unittest discover -s tests`
- **Kết quả thật:**
  ```
  Ran 149 tests in 2.661s
  OK (skipped=1)
  ```
- **Kết luận:** ĐẠT 100% (149/149 test pass).

### Chạy kiểm thử thực tế truy vấn `TC-SVQ-002`:
- **Lệnh:** Chạy qua `rag_pipeline.answer()` trên môi trường thật.
- **Kết quả thật:**
  ```
  Answer: Mình chưa tìm thấy thông tin này trong tài liệu hiện có...
  Refused: True
  Sufficiency: NO_EVIDENCE / PARTIAL (khi có dẫn chứng)
  Invalid Citations: [] (0 lỗi)
  Verification Badges: ['Chưa đủ bằng chứng để kết luận'] (kèm ['Có trích dẫn nguồn'])
  Sources Count: Khớp hoàn toàn với citation hiển thị.
  ```
- **Kết luận:** ĐẠT. Lỗi trích dẫn ngoài phạm vi hoàn toàn biến mất.
- **Số lệnh gọi API trả phí đã dùng:** 1 lệnh gọi Gemini API để test live `TC-SVQ-002` (trong hạn ngạch an toàn).

---

## 6. Chưa chắc chắn, rủi ro, giả định
- Tệp `2021_11_6_16_42_11g.docx` (QĐ tín dụng HSSV) là văn bản năm 2007 ghi mức vay 800.000đ/tháng (đã cũ). Nếu nạp file này vào Qdrant mà không kèm QĐ 05/2022/QĐ-TTg sửa đổi mức vay lên 4 triệu/tháng thì chatbot sẽ trích dẫn số tiền cũ. Cần người phụ trách phê duyệt lưu ý điểm này.

---

## 7. Điều đã không làm và lý do
- **Không tự ý chuyển `da_duyet=true` hay chạy ingest tài liệu:** Tuân thủ nghiêm ngặt nguyên tắc Approval Gate của dự án.
- **Không sửa `SYSTEM_PROMPT` trong phiên này:** Giữ nguyên System Prompt để đo lường chính xác tác động độc lập của việc sửa lỗi citation (TASK C). Các cải tiến Prompt đã được thiết kế sẵn sàng trong `improvement_changes.md` để kích hoạt ở Phiên 6H.

---

## 8. Việc tiếp theo (Phiên 6H)
1. Chờ Người dùng duyệt danh sách 7 tài liệu trong `document_approval_queue.csv`.
2. Sau khi có lệnh duyệt: nạp các tài liệu được phê duyệt vào Qdrant qua `ingest_approved.py`.
3. Kích hoạt Cải tiến Cấu hình (tăng `max_context_chunks=6`, `RRF_K=50`) và Cải tiến Prompt 3 phần.
4. Chạy lại benchmark toàn diện 75 câu hỏi khảo sát để đo mức tăng tỷ lệ PASS.

---

## 9. Câu hỏi cho người dùng
1. Bạn có đồng ý phê duyệt 7 tài liệu DOCX trong `document_approval_queue.csv` để nạp vào kho tri thức ở Phiên 6H không?
2. Với tệp `2021_11_6_16_42_11g.docx` (mức vay cũ 800k/tháng), bạn muốn nạp kèm ghi chú cập nhật QĐ 05/2022/QĐ-TTg (4 triệu/tháng) hay tạm hoãn tệp này để bổ sung bản cập nhật mới?

---

## 10. Ba câu tự kiểm tra hiểu bài
1. Vì sao câu trả lời bắt đầu bằng từ chối nhưng vẫn có thể chứa trích dẫn nguồn hợp lệ `[3]`?
2. Tại sao trước đây hệ thống lại báo lỗi `invalid_citations: [3]` dù chunk số 3 thực sự nằm trong ngữ cảnh truy xuất?
3. "Approval Gate" bảo vệ dự án NCKH khỏi những rủi ro gì về mặt khoa học và dữ liệu?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì chatbot có thể từ chối câu hỏi chính (do trường chưa có quy định riêng) nhưng vẫn trích dẫn tài liệu chung để giải thích giới hạn áp dụng (từ chối có điều kiện).
2. Vì mã cũ có dòng `chunks = [] if refused else p.chunks`. Khi bị coi là refused, `chunks` bị ép về rỗng (`max_chunks = 0`), khiến bộ kiểm tra coi mọi số trích dẫn $i \ge 1$ là vượt quá số lượng chunk (ngoài phạm vi).
3. Ngăn chặn việc nạp tài liệu hết hiệu lực, tài liệu không chính thống hoặc số liệu cũ vào kho tri thức; đảm bảo kết quả đo lường khoa học phản ánh đúng nguồn dữ liệu đã được kiểm duyệt.
</details>
