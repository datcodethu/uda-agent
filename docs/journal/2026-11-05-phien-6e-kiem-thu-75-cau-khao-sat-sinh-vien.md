# Nhật ký 2026-11-05 – Phiên 6E: Kiểm thử Toàn diện 75 Lượt Câu hỏi Khảo sát Sinh viên (Survey QA)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Tiến hành kiểm thử tự động toàn diện và chấm điểm khách quan chất lượng trả lời của chatbot trên toàn bộ 75 lượt câu hỏi khảo sát sinh viên thực tế theo đúng yêu cầu [request.md](file:///E:/workspace/donga-rag-system/docs/repository/request.md); xuất trọn bộ ma trận kết quả độc lập, không làm đẹp số liệu và không tự tạo đáp án giả.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/run_survey_evaluation.py` | Xây dựng test runner độc lập: nạp 75 câu hỏi khảo sát, sinh `test_cases.csv` chuẩn, khởi tạo `run_manifest.json` (SHA-256 xác thực), gửi request live SSE streaming tới endpoint `http://127.0.0.1:8000/api/chat/stream`, chấm điểm 6 tiêu chí (0–2) và xuất đầy đủ báo cáo. |
| `ai-service/scripts/retry_blocked.py` | Xây dựng công cụ chuyên biệt để chạy lại các câu hỏi bị ngắt kết nối do máy chủ Google Gemini quá tải tạm thời (503 UNAVAILABLE Spike) và tái chấm điểm toàn bộ ma trận kết quả mà không phải gọi lại 70 câu đã thành công. |
| `evaluation/survey_qa_20261105_01/test_cases.csv` | 75 kịch bản kiểm thử chi tiết bao phủ 12 nhóm chủ đề và 3 mức rủi ro (HIGH/MEDIUM/LOW). |
| `evaluation/survey_qa_20261105_01/responses.jsonl` | Lưu trữ nguyên văn 75 câu hỏi, câu trả lời, mảng sources, timing (TTFT, latency), và metadata verifier. |
| `evaluation/survey_qa_20261105_01/results.csv` | Ma trận 75 dòng theo chuẩn mẫu `test_results_template.csv` gồm điểm chi tiết 6 tiêu chí, execution status, verdict và ghi chú reviewer. |
| `evaluation/survey_qa_20261105_01/report.md` | Báo cáo kiểm thử tổng hợp theo chuẩn mẫu `test_report_template.md` (Executive summary, phân bổ rủi ro, P50/P95 latency/TTFT, top câu cần sửa, ví dụ trả lời tốt). |
| `evaluation/survey_qa_20261105_01/issues.md` | Bảng theo dõi phân loại lỗi P0/P1/P2 và phân tích khoảng trống dữ liệu (Data Gap). |
| `evaluation/survey_qa_20261105_01/run_manifest.json` | Lưu trữ đầy đủ Git SHA, Dataset SHA-256, model, tham số và thời gian đo đạc. |
| `docs/progress.md`, `docs/decisions.md`, `docs/todo.md` | Cập nhật tiến độ Phiên 6E, Quyết định 41 và các việc cần khắc phục tiếp theo. |

## 3. Vì sao làm như vậy
### Quyết định 1: Tách bạch tuyệt đối giữa Trạng thái Kỹ thuật (Execution Status) và Chất lượng Học vụ (Verdict)
- Quyết định: Một request trả về mã HTTP 200 không có nghĩa là câu trả lời đạt (PASS). Trạng thái kỹ thuật chỉ ghi nhận `SUCCESS`, còn kết luận học vụ (`verdict`) phải dựa trên việc chấm điểm 6 tiêu chí nội dung (`PASS`, `PARTIAL`, `NEEDS_REVIEW`, `FAIL`, `BLOCKED`).
- Phương án đã cân nhắc:
  - Phương án A: Nếu API trả về 200 và có trích dẫn thì tự động gán PASS.
  - Phương án B: Phân tách riêng `execution_status` và `verdict`, đánh giá độc lập từng tiêu chí.
- Vì sao chọn: Phương án B theo đúng yêu cầu nghiêm ngặt của `request.md`. Rất nhiều câu hỏi chatbot trả lời HTTP 200 thành công nhưng câu trả lời chỉ là "chưa có thông tin" (PARTIAL/NO_EVIDENCE) do kho dữ liệu chưa nạp văn bản liên quan. Nếu gán PASS sẽ là làm đẹp số liệu giả dối.
- Vì sao loại phương án còn lại: Phương án A sai lệch bản chất nghiên cứu khoa học.
- Loại căn cứ: [tài liệu: `request.md`, Mục I & Mục V]
- Đánh đổi: Tỷ lệ PASS thấp hơn (24.0%), phản ánh đúng thực tế kho dữ liệu hiện có 10 văn bản chuẩn.

### Quyết định 2: Chạy độc lập từng câu hỏi với Session UUID mới để chống nhiễm chéo ngữ cảnh
- Quyết định: Với mỗi câu hỏi trong 75 câu khảo sát, sinh một `conversation_id = f"survey_{run_id}_{svq_id}_{uuid.uuid4().hex[:6]}"`.
- Phương án đã cân nhắc:
  - Phương án A: Dùng chung một phiên chat liên tục để tiết kiệm thời gian kết nối.
  - Phương án B: Tạo session độc lập cho từng câu hỏi khảo sát.
- Vì sao chọn: Phương án B. Nếu dùng chung session, câu hỏi sau (ví dụ: "có được thi không?") sẽ bị cơ chế nhớ ngữ cảnh hiểu nhầm là câu hỏi tiếp nối của câu hỏi trước (ví dụ: "chuẩn đầu ra tiếng Trung"), gây sai lệch hoàn toàn kết quả retrieval.
- Loại căn cứ: [kỹ thuật: Session Isolation & Contextual RAG Guardrail]
- Đánh đổi: Không tái sử dụng cache ngữ cảnh, mỗi câu phải chạy đầy đủ retrieval hybrid.

### Quyết định 3: Ghi nhận trung thực lỗi P1 (Citation Marker trong câu từ chối) thay vì che giấu
- Quyết định: Ghi nhận lỗi FAIL cho `TC-SVQ-002` do câu trả lời từ chối vẫn còn sót lại ký hiệu trích dẫn `[3]` khi `sources` rỗng, kích hoạt cảnh báo `invalid_citations: [3]`.
- Phương án đã cân nhắc:
  - Phương án A: Chỉnh sửa lại tiêu chí chấm để bỏ qua lỗi này và cho PASS.
  - Phương án B: Báo cáo trung thực là FAIL (Issue P1), phân tích nguyên nhân và đề xuất phương án sửa code.
- Vì sao chọn: Phương án B. Đây là nguyên tắc cốt lõi của GEMINI.md: "Không làm đẹp kết quả kiểm thử. Cần báo cáo chi tiết để tự đọc và đánh giá".
- Loại căn cứ: [tài liệu: GEMINI.md, Quy tắc cốt lõi số 3]
- Đánh đổi: Tỷ lệ FAIL là 1.3% (1 câu), nhưng đem lại giá trị phát hiện lỗi kỹ thuật thật sự cho hệ thống.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Khoảng trống Dữ liệu (Data Gap) vs. Ảo giác (Hallucination):**
  - *Ví dụ đời thường:* Bạn vào thư viện hỏi: *"Ở trường có lớp dạy bơi không?"*. Người thủ thư nói: *"Trong sách hướng dẫn của trường hiện chưa có mục này, bạn hỏi thử bên Trung tâm Thể thao nhé"* $\rightarrow$ Đó là **Khoảng trống Dữ liệu (Data Gap)**; thủ thư trả lời trung thực về những gì sách có. Nhưng nếu thủ thư bảo: *"Có, học ở hồ bơi lầu 5 tòa nhà A lúc 8h sáng nhé"* (trong khi trường không có hồ bơi) $\rightarrow$ Đó là **Ảo giác (Hallucination)**.
  - *Trong RAG:* Khi sinh viên hỏi về đăng ký thi bằng lái xe máy (SVQ-075) hay thủ tục hoãn NVQS (SVQ-063), chatbot hiện chỉ có 10 văn bản quy chế đào tạo, chưa nạp văn bản thủ tục hành chính. Chatbot trả lời "chưa có thông tin cụ thể trong tài liệu và hướng dẫn liên hệ phòng ban" $\rightarrow$ Đây là ứng xử an toàn (PARTIAL), không phải lỗi ảo giác (Hallucination).

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Chạy toàn bộ 75 câu khảo sát live E2E):
  `ai-service\venv\Scripts\python.exe -m scripts.run_survey_evaluation`
- Lệnh 2 (Chạy lại 5 câu bị 503 Spike từ Google server):
  `ai-service\venv\Scripts\python.exe -m scripts.retry_blocked`
- Kết quả thật thu được:
  - Tổng số câu hỏi: **75/75** (100% hoàn thành, 0 BLOCKED).
  - **PASS:** **18 câu (24.0%)** — Trả lời xuất sắc, trích dẫn chính xác, đầy đủ căn cứ.
  - **PARTIAL:** **51 câu (68.0%)** — Trả lời đúng trọng tâm một phần nhưng tài liệu hiện tại chưa có quy định chi tiết (Data Gap).
  - **NEEDS_REVIEW:** **5 câu (6.7%)** — Cần đối chiếu thêm với thông báo học vụ chuyên ngành.
  - **FAIL:** **1 câu (1.3%)** — Câu TC-SVQ-002 bị dính marker `[3]` trong câu từ chối.
  - **Hiệu năng:** P50 Latency = `2375 ms` (~2.38s), P50 TTFT = `1740 ms` (~1.74s), P95 Latency = `13648 ms`.
  - **An toàn chính sách:** **100% câu hỏi nhạy cảm (nợ học phí, cấm thi, BHYT) được bảo vệ an toàn**, không có bất kỳ câu trả lời nào khẳng định cấm thi tuyệt đối hay dọa dẫm sinh viên.
- Kết luận: **ĐẠT YÊU CẦU KIỂM THỬ TOÀN DIỆN**.
- Số lệnh gọi API trả phí đã dùng: 75 lệnh đợt 1 + 5 lệnh đợt rerun = 80 lệnh gọi Gemini API (đã được người dùng duyệt).

## 6. Chưa chắc chắn, rủi ro, giả định
- 51 câu PARTIAL phản ánh chính xác giới hạn của kho tri thức hiện tại: chỉ mới có 10 tài liệu chuẩn (chủ yếu là Quy chế CTSV, Đào tạo đại học chính quy, Chuẩn đầu ra ngoại ngữ, Nội quy học đường). Các chủ đề sinh viên hỏi rất nhiều như: thủ tục hoãn nghĩa vụ quân sự (8 câu), thời khóa biểu/lịch học (11 câu), học phí GDQP (2 câu) đều thuộc về các thông báo hành chính thời vụ chưa được nạp.

## 7. Điều đã không làm và lý do
- Không tự ý sửa câu hỏi gốc của sinh viên (giữ nguyên "kco", "thắc mắcveef", "nm clb").
- Không tự gán nhãn PASS cho các câu trả lời thiếu chứng cứ.
- Không tự bịa đáp án quy chế cho các thủ tục chưa có văn bản chính thức.

## 8. Việc tiếp theo
- Bổ sung bước làm sạch hậu xử lý (post-processing) trong `stream_handler.py`: khi `sources` rỗng, tự động xóa bỏ mọi marker trích dẫn `\[\d+\]` để khắc phục triệt để lỗi P1 ở `TC-SVQ-002`.
- Đề xuất bổ sung nạp các văn bản hướng dẫn thủ tục hành chính một cửa (hoãn NVQS, vay vốn, miễn giảm BHYT) vào kho tri thức RAG để nâng tỷ lệ câu trả lời đầy đủ (PASS).

## 9. Câu hỏi cho người dùng
- Bạn có muốn tôi tiến hành sửa ngay lỗi P1 (loại bỏ marker trích dẫn thừa khi câu trả lời là từ chối) trong `stream_handler.py` không? Việc sửa này chỉ mất khoảng 3 dòng code và sẽ đưa tỷ lệ FAIL về 0%.

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao một phản hồi có mã HTTP 200 và có câu trả lời đầy đủ lại không thể mặc nhiên coi là một test case PASS?
2. Trong đợt kiểm thử 75 câu khảo sát, vì sao tỷ lệ PARTIAL lại chiếm tới 68%? Điều này là do lỗi của mô hình RAG hay do nguyên nhân nào khác?
3. Hiện tượng câu `TC-SVQ-002` bị đánh lỗi FAIL có nguyên nhân kỹ thuật là gì, và cách khắc phục đơn giản nhất là gì?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì HTTP 200 chỉ chứng minh server không bị sập hay lỗi mạng (trạng thái kỹ thuật). Câu trả lời bên trong hoàn toàn có thể là câu từ chối ("mình chưa tìm thấy thông tin"), câu trả lời thiếu căn cứ, bịa quy định hoặc sai lệch chính sách. Chất lượng học vụ (`verdict`) bắt buộc phải được chấm điểm độc lập dựa trên độ đầy đủ, tính trung thực và an toàn quy chế.
2. Không phải do lỗi của pipeline RAG, mà do **Khoảng trống Dữ liệu (Data Gap)**. Sinh viên khảo sát hỏi rất nhiều câu hỏi thực tế về thủ tục hành chính cụ thể (nộp đơn hoãn NVQS ở đâu, lịch học quân sự khi nào, học phí một tín chỉ bao nhiêu tiền, đăng ký thi bằng lái xe ở đâu). Trong khi đó, kho tri thức hiện tại mới chỉ nạp 10 văn bản quy chế học vụ cốt lõi, chưa nạp các thông báo hành chính thời vụ này. Chatbot đã xử lý đúng khi thừa nhận chưa có thông tin chi tiết thay vì tự bịa đặt.
3. Khi câu hỏi nằm ngoài phạm vi, LLM sinh câu từ chối nhưng trong văn bản sinh ra vẫn sót lại marker `[3]`. Khi phát hiện câu từ chối, pipeline đã chủ động xóa danh sách nguồn (`sources = []`) để không hiển thị nguồn giả mạo. Tuy nhiên, trong thân văn bản vẫn còn chữ `[3]` nên bộ kiểm định `CitationVerifier` phát hiện trích dẫn ngoài dải nguồn (`invalid_citations: [3]`). Cách sửa đơn giản nhất là thêm bước regex gỡ bỏ toàn bộ `\[\d+\]` khi `sources` rỗng trước khi trả lời.

</details>
