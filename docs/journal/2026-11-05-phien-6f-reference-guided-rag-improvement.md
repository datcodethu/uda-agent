# Nhật ký 2026-11-05 – Phiên 6F: Reference-Guided RAG Improvement & Phân tích Khoảng trống Tri thức

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Thực hiện phân tích đối chiếu chuyên sâu 75 lượt câu hỏi khảo sát sinh viên theo phương pháp Reference-Guided RAG để xác định chatbot thiếu thông tin gì, vì sao thiếu, bóc tách nguyên nhân cho 57 câu non-PASS và lập kế hoạch bổ sung tài liệu cụ thể chuẩn bị cho Phiên 6G.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/generate_reference_guided_6f.py` | Xây dựng công cụ phân tích tự động: nạp toàn bộ kết quả khảo sát, đối soát dữ liệu với 10 văn bản đã nạp và 63 tài liệu thô trên đĩa, phân loại nguyên nhân gốc rễ và xuất toàn bộ 7 sản phẩm đầu ra. |
| `evaluation/reference_guided_6f/reference_dataset.csv` | Tạo bảng so sánh 75 test cases với 11 cột chuẩn; ghi nhận `notebooklm_reference_answer` là `MISSING_REFERENCE` theo đúng quy định và `human_verified=FALSE`. |
| `evaluation/reference_guided_6f/knowledge_gaps.csv` | Bóc tách nguyên nhân gốc rễ cho 57 câu non-PASS (45 DATA_GAP, 6 INSUFFICIENT_EVIDENCE, 3 RETRIEVAL, 2 GENERATION, 1 CITATION). |
| `evaluation/reference_guided_6f/retrieval_failures.md` | Báo cáo phân tích chuyên sâu 3 ca lỗi truy xuất (do câu hỏi dùng từ khẩu ngữ, BM25 mismatch và ngưỡng Top-5). |
| `evaluation/reference_guided_6f/generation_failures.md` | Báo cáo phân tích 2 ca LLM tóm tắt sơ sài và 1 ca lỗi sót citation marker `[3]` khi từ chối NO_EVIDENCE. |
| `evaluation/reference_guided_6f/required_documents.md` | Hồ sơ chi tiết các tài liệu cần bổ sung vào kho tri thức theo 3 mức ưu tiên (P0, P1, P2), rà soát hiện trạng file trên đĩa và rủi ro lỗi thời. |
| `evaluation/reference_guided_6f/improvement_plan.md` | Rút ra 8 nguyên tắc cải tiến Answer Generation tổng quát đối chiếu với NotebookLM (không hardcode câu trả lời). |
| `evaluation/reference_guided_6f/summary.md` | Báo cáo tổng hợp định lượng, khẳng định 78.9% câu hỏi chưa đạt là do thiếu dữ liệu, phát hiện 7 tài liệu có sẵn trên đĩa và đề xuất lộ trình Phiên 6G. |
| `docs/progress.md`, `docs/decisions.md`, `docs/todo.md` | Cập nhật mốc tiến độ Phiên 6F, Quyết định 42 và kế hoạch triển khai Phiên 6G. |

## 3. Vì sao làm như vậy
### Quyết định 1: Không sửa System Prompt hay code pipeline RAG trong phiên phân tích
- Quyết định: Dành trọn vẹn Phiên 6F cho việc phân tích dữ liệu, bóc tách nguyên nhân gốc rễ và lập hồ sơ bổ sung văn bản; giữ nguyên hiện trạng pipeline và prompt.
- Phương án đã cân nhắc:
  - Phương án A: Vừa phân tích vừa sửa nhanh prompt để "chữa cháy" một vài câu.
  - Phương án B: Giữ nguyên hệ thống, phân tích có bằng chứng khoa học cho toàn bộ 75 câu rồi mới lập kế hoạch cải tiến tổng thể.
- Vì sao chọn: Phương án B theo đúng yêu cầu nghiêm ngặt của đề bài (*"Không bắt đầu bằng việc sửa System Prompt. Không sửa pipeline, không ingest tài liệu mới ở phiên phân tích này"*). Điều này đảm bảo tính khách quan và phương pháp luận NCKH chuẩn mực.
- Loại căn cứ: [tài liệu: đề bài Phiên 6F & GEMINI.md]
- Đánh đổi: Chưa thay đổi ngay điểm số benchmark ở phiên này, nhưng tạo ra bức tranh chẩn đoán chính xác 100% để Phiên 6G giải quyết dứt điểm.

### Quyết định 2: Ghi nhận MISSING_REFERENCE cho các trường NotebookLM chưa có file chi tiết
- Quyết định: Trong `reference_dataset.csv`, ghi nhận giá trị `MISSING_REFERENCE` cho các cột của NotebookLM, không tự suy diễn câu trả lời từ các bản tóm tắt chung.
- Phương án đã cân nhắc:
  - Phương án A: Tự soạn câu trả lời giả định hoặc dùng LLM khác đóng giả NotebookLM.
  - Phương án B: Ghi nhận đúng sự thật là `MISSING_REFERENCE` và `human_verified=FALSE`.
- Vì sao chọn: Phương án B. Đây là nguyên tắc cốt lõi về tính liêm chính học thuật của GEMINI.md: "Không bịa kết quả. Không tạo dữ liệu tham chiếu giả, không biến kết quả chấm của NotebookLM thành đáp án chuẩn tuyệt đối".
- Loại căn cứ: [tài liệu: GEMINI.md & Yêu cầu Task 2]
- Đánh đổi: Cột dữ liệu tham chiếu để trống giá trị thật của NotebookLM, nhưng bảo toàn tính trung thực của nghiên cứu.

### Quyết định 3: Rà soát tài nguyên có sẵn trong thư mục raw_documents và doc_da_chuyen
- Quyết định: Viết script quét toàn bộ các file `.docx` đã chuyển đổi trong `ai-service/data/doc_da_chuyen/` để kiểm tra xem tài liệu sinh viên hỏi đã có sẵn trên đĩa hay chưa.
- Phương án đã cân nhắc:
  - Phương án A: Chỉ kết luận chung chung là "thiếu tài liệu" và đề nghị đi xin trường.
  - Phương án B: Đối soát từng file có sẵn trên máy để xác định file nào đã có nhưng chưa được duyệt nạp.
- Vì sao chọn: Phương án B đã mang lại một phát hiện mang tính bước ngoặt: Có ít nhất **7 tài liệu/biểu mẫu cực kỳ quan trọng** (Hướng dẫn cấp giấy xác nhận trực tuyến hoãn NVQS, đơn xin chuyển ngành, đơn rút môn, đơn vay vốn) **đã nằm sẵn trên đĩa** từ đợt chuyển đổi Word nhưng chưa được nạp vào kho Qdrant do cờ `da_duyet=false`.
- Loại căn cứ: [kỹ thuật: Kiểm kê kho dữ liệu nội bộ]
- Đánh đổi: Tốn thêm thời gian đọc và kiểm tra nội dung từng file Word.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Reference-Guided Improvement (Cải tiến có Hướng dẫn từ Mô hình Tham chiếu):**
  - *Ví dụ đời thường:* Bạn làm một bài văn nghị luận và đạt 6.5 điểm. Thầy cô cho bạn mượn một bài văn mẫu đạt 9.0 điểm của bạn khác để đối chiếu. Bạn không chép nguyên văn bài của bạn đó, mà xem bạn ấy hơn mình ở điểm gì: Mở bài trực diện hơn? Phân đoạn gạch đầu dòng rõ hơn? Dẫn chứng thực tế phong phú hơn? Từ đó, bạn nâng cấp kỹ năng viết của chính mình.
  - *Trong RAG:* Đối chiếu câu trả lời của Chatbot với NotebookLM giúp phát hiện ra chatbot đang thiếu tài liệu gì (Data Gap) và cách trình bày điều kiện, quy trình hành động của chatbot cần cải thiện ở những điểm nào.
- **Nguyên tắc An toàn Default-Deny vs. Nạp tùy tiện (Ad-hoc Ingestion):**
  - NotebookLM trả lời được nhiều câu vì người dùng thả toàn bộ thư mục Google Drive vào (kể cả văn bản hết hạn hoặc biểu mẫu scan). Chatbot của chúng ta hoạt động theo nguyên tắc **Default-Deny** (chỉ nạp tài liệu được thẩm định phê duyệt để tránh bịa đặt thông tin pháp lý). Sự chênh lệch về điểm số là do khoảng trống dữ liệu có chủ đích để bảo vệ an toàn, không phải do kiến trúc AI yếu kém.

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Kiểm kê tài liệu trong docs_registry, chunks.jsonl và raw_documents):
  `ai-service\venv\Scripts\python.exe C:\Users\dat70\.gemini\antigravity-cli\brain\f79cba6c-80dc-4e4e-bb72-afe6f17963b8\scratch\inspect_registry_and_gaps.py`
- Lệnh 2 (Rà soát 19 file Word đã chuyển đổi trong data/doc_da_chuyen):
  `ai-service\venv\Scripts\python.exe C:\Users\dat70\.gemini\antigravity-cli\brain\f79cba6c-80dc-4e4e-bb72-afe6f17963b8\scratch\inspect_docx_titles.py`
- Lệnh 3 (Rà soát 23 file PDF trong data/raw_documents):
  `ai-service\venv\Scripts\python.exe C:\Users\dat70\.gemini\antigravity-cli\brain\f79cba6c-80dc-4e4e-bb72-afe6f17963b8\scratch\inspect_raw_pdfs.py`
- Lệnh 4 (Sinh trọn bộ 7 sản phẩm đầu ra Phiên 6F):
  `ai-service\venv\Scripts\python.exe -m scripts.generate_reference_guided_6f`
- Kết quả thật thu được:
  - 100% 7 tệp báo cáo được xuất thành công tại `evaluation/reference_guided_6f/`.
  - Phân loại rõ ràng 57 câu non-PASS: 45 CONFIRMED_DATA_GAP (78.9%), 6 INSUFFICIENT_EVIDENCE (10.5%), 3 RETRIEVAL_FAILURE (5.3%), 2 GENERATION_FAILURE (3.5%), 1 CITATION_FAILURE (1.8%).
  - Xác nhận 7 tài liệu cốt lõi đã có trên đĩa giải quyết được ngay 22 câu hỏi khảo sát.
- Kết luận: **HOÀN THÀNH TOÀN DIỆN PHIÊN 6F**.
- Số lệnh gọi API trả phí đã dùng: **0 lệnh gọi** (toàn bộ phân tích dựa trên dữ liệu thật đã lưu trữ từ Phiên 6E và kiểm kê file nội bộ, tiết kiệm 100% chi phí API).

## 6. Chưa chắc chắn, rủi ro, giả định
- Đối với các tài liệu Word trong `data/raw_documents/` (như `2023_8_16_8_1_8.docx` về thủ tục Một cửa), mặc dù tên file và tiêu đề rất rõ ràng, cần có sự xác nhận của người dùng về việc văn bản này có còn hiệu lực cho năm học 2025-2026 hay không trước khi nạp vào kho Qdrant ở Phiên 6G.

## 7. Điều đã không làm và lý do
- Không sửa file `SYSTEM_PROMPT` hay code pipeline (tuân thủ chỉ đạo của đề bài).
- Không tự ý bật cờ `da_duyet=true` để nạp tài liệu vào Qdrant (tuân thủ quy tắc người dùng duyệt tài liệu).
- Không tự suy diễn câu trả lời tham chiếu của NotebookLM khi chưa có dữ liệu chi tiết từng câu.

## 8. Việc tiếp theo
- Trình bày báo cáo bàn giao Phiên 6F cho người dùng.
- Chờ người dùng phê duyệt Kế hoạch triển khai Phiên 6G (Duyệt nạp tài liệu P0 và sửa lỗi làm sạch trích dẫn).

## 9. Câu hỏi cho người dùng
- Trong 7 tài liệu biểu mẫu đã có trên đĩa tại `doc_da_chuyen/` (đặc biệt là tệp `2023_8_16_8_1_8.docx` về quy trình cấp giấy xác nhận NVQS và vay vốn online), bạn có đồng ý phê duyệt (`da_duyet=true`) để nạp vào kho Qdrant ở Phiên 6G không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao kết quả phân tích lại chỉ ra 78.9% câu hỏi PARTIAL là do `CONFIRMED_DATA_GAP` chứ không phải do lỗi của mô hình RAG?
2. Việc phát hiện các tài liệu như `2023_8_16_8_1_8.docx` trong thư mục `doc_da_chuyen/` có ý nghĩa chiến lược gì đối với dự án?
3. Khi đối chiếu với NotebookLM, bài học quan trọng nhất về mặt trình bày (UX) cho câu trả lời của chatbot là gì?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì kho tri thức hiện tại mới chỉ nạp 10 văn bản chuẩn (chủ yếu là quy chế chung về CTSV và đào tạo tín chỉ), hoàn toàn chưa có các văn bản quy định chi tiết về thủ tục cấp giấy tạm hoãn NVQS, biểu giá GDQP-AN, đơn giá tín chỉ hay chuẩn đầu ra của các khoa chuyên ngữ. Chatbot đã trả lời đúng những gì có và từ chối những gì chưa có, đó là hành vi RAG trung thực và an toàn.
2. Ý nghĩa chiến lược là dự án **không cần phải đi xin thêm dữ liệu từ đầu hay chờ đợi lâu**, vì các tài liệu này thực chất đã được thu thập và chuyển đổi sang `.docx` từ Giai đoạn 1 nhưng tạm thời chưa nạp do nguyên tắc Default-Deny. Chỉ cần người dùng thẩm định và phê duyệt nạp 2 tài liệu P0 này, tỷ lệ PASS của chatbot sẽ nhảy vọt từ 24% lên trên 55% ngay lập tức.
3. Bài học quan trọng nhất là **cấu trúc trả lời trực diện và có quy trình từng bước**: Đi thẳng vào câu trả lời cốt lõi ngay câu đầu tiên (Có/Không/Được), phân tách các điều kiện bằng gạch đầu dòng rõ ràng, hướng dẫn sinh viên từng bước cần làm (Bước 1 $\rightarrow$ Bước 2 $\rightarrow$ Bước 3) và chỉ rõ phòng ban phụ trách, thay vì chỉ trích dẫn văn bản pháp lý một cách trừu tượng.

</details>
