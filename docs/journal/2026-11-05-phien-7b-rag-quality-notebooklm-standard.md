# Nhật ký 2026-11-05 – Phiên 7B: Nâng cao Chất lượng Trả lời RAG Tiệm cận Chuẩn Tham chiếu NotebookLM

## 1. Mục tiêu
Nâng cao chất lượng câu trả lời của trợ lý hỏi đáp Advanced RAG trên kho tri thức `donga_kb_v2` để đạt chuẩn tham chiếu NotebookLM (trả lời trực tiếp, đầy đủ điều kiện/ngoại lệ, đính kèm biểu mẫu và hướng dẫn thực tế, không từ chối vội), giải quyết dứt điểm các ca PARTIAL/FAIL mà không crawl thêm hay thay đổi dữ liệu gốc.

## 2. Đã làm gì

| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/generator/verifier.py` | Sửa regex trong `unsupported_numbers()` để bỏ qua số thứ tự danh sách và tiêu đề Markdown (`### 1.`, `**1.**`, `1.`); bổ sung hàm `verify_claim_faithfulness()` kiểm tra độ trung thực từng khẳng định dựa trên trích dẫn nguồn. |
| `ai-service/app/core/prompts.py` | Bổ sung Quy tắc 3 (Quy tắc NotebookLM) trong `SYSTEM_PROMPT` và `build_messages`: hướng dẫn trả lời trực diện câu đầu, phân biệt giữa "Quy chế không cấm" và "Thông tin không có", liên kết biểu mẫu tài chính/học vụ khi người học gặp vướng mắc. |
| `ai-service/scripts/run_v2_benchmark.py` | Nâng cấp Adaptive Retrieval: Top-K tăng từ 5 lên 7, tăng dung lượng ứng viên từ 20 lên 30 điểm (Dense & BM25), RRF $K=60$, tích hợp Token Expansion thích ứng theo nhóm ý định (`biểu mẫu`, `đơn`, `gia hạn`, `xác nhận`, `kế toán`, `đào tạo`). |
| `ai-service/scripts/run_10_focal_traces.py` | Xây dựng công cụ truy vết chuyên sâu chuỗi suy luận Question -> Retrieved Chunks -> Context -> Generated Answer -> Verified Claims cho 10 câu hỏi trọng điểm. |
| `ai-service/scripts/run_generalizability.py` | Cập nhật bộ kiểm thử khái quát hóa 5 câu mới sang pipeline Top-K=7 và Intent/Risk classification để phát hiện overfitting. |
| `evaluation/kb_rebuild_v2/10_focal_traces.md` | Xuất báo cáo truy vết Before vs After chi tiết cho 10 câu hỏi trọng điểm (10/10 PASS). |
| `evaluation/kb_rebuild_v2/10_focal_traces.json` | Dữ liệu cấu trúc truy vết 10 ca trọng điểm. |
| `evaluation/kb_rebuild_v2/final_acceptance_report.md` | Xuất báo cáo nghiệm thu duy nhất toàn diện cho Trưởng dự án đánh giá. |
| `docs/decisions.md` | Ghi nhận Quyết định 46 về việc chuẩn hóa năng lực trả lời tiệm cận NotebookLM. |
| `docs/progress.md` | Cập nhật tiến độ Phiên 7B. |
| `docs/todo.md` | Cập nhật danh mục hoàn thành Phiên 7B và kế hoạch Phiên 7C. |

## 3. Vì sao làm như vậy

### Quyết định 1: Tăng Top-K từ 5 lên 7 và mở rộng Token Expansion trong Adaptive Retrieval
- **Quyết định:** Mở rộng ngữ cảnh đưa vào LLM từ 5 lên 7 chunks; khi câu hỏi liên quan đến tài chính, học phí, điều kiện thi, tự động mở rộng truy vấn BM25 với các từ khóa thủ tục hành chính (`biểu mẫu`, `đơn`, `gia hạn`, `xác nhận`, `kế toán`, `đào tạo`).
- **Phương án đã cân nhắc:**
  - *Phương án A:* Giữ nguyên Top-K=5 và viết thêm prompt ép LLM đoán quy trình.
  - *Phương án B (chọn):* Tăng Top-K=7 kết hợp token expansion để kéo đúng chunk biểu mẫu thực tế (`src-v2-020`) vào ngữ cảnh.
- **Vì sao chọn:** Bằng chứng thực nghiệm cho thấy chunk `src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1` (chứa mẫu Đơn gia hạn học phí và Giấy nhờ đóng học phí kiêm xác nhận đủ điều kiện dự thi) trước đây đứng ở Rank 7 trong RRF fusion. Nếu chỉ lấy Top-K=5 thì chunk này bị rớt khỏi Context. Khi tăng lên Top-K=7, chunk này lập tức lọt vào ngữ cảnh, cung cấp đầy đủ bằng chứng giải quyết câu hỏi.
- **Vì sao loại phương án còn lại:** Phương án A ép LLM đoán quy trình sẽ vi phạm nguyên tắc chống hallucination và dẫn đến trả lời bịa đặt.
- **Loại căn cứ:** [kỹ thuật] & [thực nghiệm đo đạc]
- **Đánh đổi:** Tăng số lượng token đầu vào đưa vào LLM (từ ~2,200 token lên ~3,100 token), khiến P50 Latency tăng từ 2.5s lên 7.19s, nhưng đổi lại chất lượng câu trả lời từ SUFFICIENT/PASS tăng vọt.

### Quyết định 2: Bổ sung Quy tắc NotebookLM chống từ chối vội (Premature Refusal)
- **Quyết định:** Thêm chỉ dẫn rõ ràng trong System Prompt: Khi quy chế không có điều cấm (ví dụ: không có điều cấm sinh viên nợ học phí đăng ký môn hay dự thi), phải khẳng định rõ thực tế này ở câu đầu tiên, sau đó hướng dẫn các biểu mẫu và quy trình hỗ trợ hành chính (đơn xin gia hạn, liên hệ Phòng Kế toán P.201, Cổng `my.uda.edu.vn`).
- **Phương án đã cân nhắc:**
  - *Phương án A:* Giữ luật cũ "Nếu không thấy thông tin cấm thì trả lời: Mình chưa tìm thấy thông tin này...".
  - *Phương án B (chọn):* Phân biệt rạch ròi giữa "Quy chế không cấm" và "Tài liệu không có".
- **Vì sao chọn:** Trong quản lý đào tạo đại học, nguyên tắc là "người học được làm những gì pháp luật và quy chế không cấm". Sinh viên hỏi nợ học phí có được đăng ký môn/thi không, trả lời "chưa tìm thấy" khiến sinh viên hoang mang. Chuẩn NotebookLM sẽ trả lời ngay là quy chế không cấm cứng ngắc, đồng thời chỉ ra thủ tục xin gia hạn.
- **Loại căn cứ:** [tài liệu: GEMINI.md & Yêu cầu chuẩn tham chiếu NotebookLM]
- **Đánh đổi:** Cần kiểm soát chặt chẽ để LLM không suy diễn vượt quá các biểu mẫu và đầu mối thực tế có trong ngữ cảnh.

### Quyết định 3: Khắc phục lỗi Regex Unsupported Numbers đối với Tiêu đề và Danh sách Markdown
- **Quyết định:** Mở rộng regex lọc bỏ tiền tố danh sách và tiêu đề Markdown: `re.sub(r"(?m)^\s*(?:#{1,6}\s+|(?:[-*•]\s+)?(?:\*\*)?)\d+[\.)](?:\*\*)?\s*", "", ans)`.
- **Phương án đã cân nhắc:**
  - *Phương án A:* Tắt tính năng Unsupported Numbers.
  - *Phương án B (chọn):* Sửa regex lọc sạch các ký tự đánh số thứ tự Markdown (`1.`, `2.`, `### 1.`, `### 2.`).
- **Vì sao chọn:** Hai ca kiểm thử `TC-SVQ-015` và `TC-SVQ-040` trước đây bị đánh FAIL hoàn toàn do bắt nhầm các số `1`, `2`, `3` trong các tiêu đề Markdown (`### 1. Chuẩn đầu ra`, `### 2. Hỗ trợ việc làm`). Bản thân câu trả lời hoàn toàn chính xác và trung thực. Lọc bỏ các tiền tố này giúp giữ vững tính năng bảo vệ số liệu mà không gây ra false positive.
- **Loại căn cứ:** [kỹ thuật]
- **Đánh đổi:** Không có đánh đổi tiêu cực.

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)

### Adaptive Retrieval (Truy xuất Thích ứng)
- **Giải thích:** Bình thường, hệ thống RAG dùng một cách tìm kiếm cố định cho mọi câu hỏi: người dùng gõ gì thì tìm đúng cụm từ đó và lấy ra 5 đoạn văn bản đầu tiên. Nhưng câu hỏi của sinh viên rất đa dạng: có câu hỏi định nghĩa ("Học bổng là gì?"), có câu hỏi về quy trình xử lý khó khăn ("Em nợ tiền học thì có bị cấm thi không?").
- **Ví dụ đời thường:** Giống như khi bạn đến phòng Đào tạo hỏi xin hoãn thi: nếu cô giáo chỉ nhìn vào cuốn Sổ tay quy chế, cô sẽ không thấy từ "hoãn thi vì nợ học phí". Nhưng nếu cô là một người có kinh nghiệm (thích ứng), cô sẽ biết mở thêm ngăn kéo tủ đựng **"Biểu mẫu và Đơn từ gia hạn học phí"** để đưa cho bạn điền. Đó chính là Adaptive Retrieval: khi thấy câu hỏi về khó khăn tài chính, hệ thống tự động tìm thêm các "ngăn kéo biểu mẫu và quy trình hành chính".

### Claim-level Verification (Kiểm chứng theo Từng Khẳng định)
- **Giải thích:** Thay vì chỉ kiểm tra xem câu trả lời có gắn thẻ trích dẫn `[1]`, `[2]` bằng regex hay không, hệ thống bóc tách câu trả lời thành từng câu khẳng định độc lập. Sau đó, nó đối chiếu từng khẳng định đó với chính đoạn văn bản nguồn được trích dẫn xem ý nghĩa có trùng khớp không, có bị "nói quá", "chế thêm số liệu" hay không.

## 5. Đã kiểm tra thế nào

- **Lệnh 1 (Truy vết 10 câu trọng điểm):**
  `cd ai-service; venv\Scripts\python.exe scripts\run_10_focal_traces.py`
  - Kết quả: Hoàn thành 10/10 ca trọng điểm; 10/10 câu đạt PASS, 0 FAIL, Faithfulness 100%.

- **Lệnh 2 (Benchmark toàn diện 75 câu khảo sát thực tế):**
  `cd ai-service; venv\Scripts\python.exe scripts\run_v2_benchmark.py` & `scripts\finalize_v2_results.py`
  - Kết quả thật:
    - **PASS: 67/75 (89.3%)** (tăng từ 58/75 - 77.3% của baseline cũ, +12.0%)
    - **PARTIAL: 8/75 (10.7%)** (giảm từ 15/75 - 20.0%)
    - **FAIL: 0/75 (0.0%)** (giảm từ 2/75 - 2.7%, triệt tiêu 100% lỗi thất bại)
    - P50 Latency: 7,192 ms | P95 Latency: 81,186 ms

- **Lệnh 3 (Kiểm thử Khái quát hóa chống Overfitting):**
  `cd ai-service; venv\Scripts\python.exe scripts\run_generalizability.py`
  - Kết quả thật: **5/5 ca kiểm thử mới đạt PASS (100%)**, điểm trung bình 11.4/12đ, không overfitting.

- **Lệnh 4 (Kiểm thử Hồi quy Unit Test hệ thống):**
  `cd ai-service; venv\Scripts\python.exe -m unittest discover -s tests -v`
  - Kết quả thật: `Ran 159 tests in 5.604s: OK (skipped=1)`. 0 regressions.

- **Kết luận:** **ĐẠT XUẤT SẮC**
- **Số lượt gọi API trả phí đã dùng trong phiên:**
  - Embedding: 75 lượt (Gemini-embedding-001)
  - LLM Generation: 112 lượt (Gemini-flash-lite-latest, gồm 75 lượt chính + 37 lượt retry do lỗi 503/504)

## 6. Chưa chắc chắn, rủi ro, giả định
- **Rủi ro quá tải từ máy chủ Google AI Studio:** Trong các giờ cao điểm, API Gemini Flash Lite thường xuyên trả mã lỗi `503 UNAVAILABLE` hoặc `504 DEADLINE_EXCEEDED`. Pipeline đã xử lý tự động bằng Exponential Backoff thành công 100%, nhưng làm P95 latency tăng lên ~81 giây.
- **Khoảng trống quy chế Điểm Rèn luyện (ĐRL):** Nhóm câu hỏi ĐRL đạt tỷ lệ PASS 55.6% (5/9 câu) do kho hiện tại chưa có văn bản hướng dẫn chi tiết thang điểm ĐRL từng tiêu chí (0-100đ).

## 7. Điều đã không làm và lý do
- Không crawl lại hay ingest thêm tài liệu mới vào kho v2, không tạo thêm collection mới: Tuân thủ nghiêm ngặt chỉ đạo của Trưởng dự án.
- Không sửa nhãn benchmark hay can thiệp dữ liệu kiểm thử: Bảo toàn tính khách quan khoa học của đề tài NCKH.
- Không hardcode các câu trả lời tham chiếu của NotebookLM: Toàn bộ câu trả lời được sinh động từ pipeline RAG cải tiến.
- Không tự ý chạy `git commit` hay `git push`: Người dùng tự quản lý version control.

## 8. Việc tiếp theo
- Bàn giao báo cáo nghiệm thu duy nhất `evaluation/kb_rebuild_v2/final_acceptance_report.md` để Trưởng dự án trực tiếp đánh giá.
- Khi được phê duyệt, chuyển đổi cấu hình `.env` để Web Chat chính thức trỏ sang kho `donga_kb_v2`.
- Khảo sát và bổ sung 01 URL văn bản hướng dẫn chấm ĐRL ở đợt cập nhật tiếp theo.

## 9. Câu hỏi cho người dùng
- Anh/chị có muốn tôi hỗ trợ cập nhật cấu hình file `.env` sang collection `donga_kb_v2` để khởi chạy máy chủ Web Chat cho anh/chị trải nghiệm thử trực tiếp trên trình duyệt không?

## 10. Ba câu tự kiểm tra hiểu bài
1. *Vì sao trước đây khi sinh viên hỏi "Nợ học phí có được thi không?", chatbot lại trả lời "Mình chưa tìm thấy thông tin này..." mặc dù kho dữ liệu đã có biểu mẫu gia hạn đóng học phí?*  
   **Đáp án:** Do hai nguyên nhân: (1) Cấu hình `Top-K = 5` khiến chunk chứa biểu mẫu học vụ nằm ở Rank 7 bị rớt khỏi ngữ cảnh đưa vào LLM; (2) System Prompt cũ quy định quá máy móc: khi quy chế không có điều khoản cấm rõ ràng thì tự động kích hoạt câu từ chối.
2. *Lỗi Unsupported Numbers ở hai ca kiểm thử `TC-SVQ-015` và `TC-SVQ-040` trước đây thực chất bắt nguồn từ đâu?*  
   **Đáp án:** Bắt nguồn từ việc hàm regex kiểm tra số liệu lạ chỉ lọc các số thứ tự dạng `1.`, `2.`, nhưng bỏ sót các tiêu đề Markdown có chứa số dạng `### 1.`, `### 2.`, dẫn đến việc các số `1`, `2` trong tiêu đề bị đánh đồng là "số liệu hallucination không có trong tài liệu".
3. *Cơ chế Exponential Backoff trong pipeline có tác dụng gì khi gọi API Gemini?*  
   **Đáp án:** Khi máy chủ Google AI Studio gặp đỉnh tải và trả về mã lỗi 503 (Unavailable) hoặc 504 (Deadline Exceeded), cơ chế này giúp hệ thống tự động tạm dừng một khoảng thời gian tăng dần (1.5s, 3s, 5s, 15s...) rồi thử lại, thay vì báo lỗi làm hỏng toàn bộ lượt chạy benchmark.
