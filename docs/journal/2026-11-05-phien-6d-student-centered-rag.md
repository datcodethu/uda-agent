# Nhật ký 2026-11-05 – Phiên 6D: Lấy Sinh viên làm Trung tâm & Xử lý Chính sách Học vụ Nhạy cảm

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Nâng cấp hệ thống hỏi đáp RAG để xử lý chuẩn xác, có trách nhiệm và thấu cảm với các chủ đề học vụ nhạy cảm (học phí, BHYT, điều kiện dự thi, kỷ luật, hỗ trợ tài chính); tuyệt đối không tự tiện suy diễn chế tài có điều kiện thành khẳng định cấm thi tuyệt đối gây hoang mang cho sinh viên.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/query_transformation/intent_classifier.py` | Bổ sung `AcademicIntent` (8 nhóm ý định học vụ), `RiskLevel` (3 cấp độ rủi ro: LOW, MEDIUM, HIGH) và hàm `classify_academic_intent_and_risk()` bằng regex rule-based chạy dưới 1 ms (0 extra LLM call). |
| `ai-service/app/core/prompts.py` | Bổ sung Mục 11 (*Nguyên tắc lấy sinh viên làm trung tâm & xử lý chính sách nhạy cảm*) vào `SYSTEM_PROMPT` và chèn hướng dẫn chiến lược trả lời động (`[LƯU Ý CHIẾN LƯỢC TRẢ LỜI CHO SINH VIÊN]`) theo từng nhóm ý định trong `build_messages()`. |
| `ai-service/app/pipeline/generator/verifier.py` | Xây dựng hàm `verify_claims()` kiểm tra các khẳng định tuyệt đối cực đoan ("chắc chắn bị cấm thi", "bạn sẽ bị cấm thi") có đi kèm điều kiện hay không; cập nhật `evaluate_verification()` tự động giáng cấp huy hiệu ("Cần đối chiếu điều kiện áp dụng") nếu vi phạm. |
| `ai-service/app/schemas/query_schema.py` | Mở rộng schema `QueryResponse` bổ sung các trường `academic_intent`, `risk_level`, `claim_warnings`. |
| `ai-service/app/pipeline/rag_pipeline.py` | Tích hợp phân loại ý định học vụ vào `prepare()`, chuyển intent và risk level sang `build_messages()`, trả về đầy đủ metadata trong `answer()`. |
| `ai-service/app/pipeline/generator/stream_handler.py` | Phát các sự kiện SSE `verify` và `done` đồng bộ đầy đủ các trường `academic_intent`, `risk_level`, `claim_warnings`, `sufficiency`, `verification_badges`. |
| `ai-service/app/static/index.html` | Bổ sung kiểu hiển thị badge màu vàng cam cảnh báo cho huy hiệu `Cần đối chiếu điều kiện áp dụng`. |
| `ai-service/tests/test_student_centered_rag.py` | Tạo bộ kiểm thử mới gồm 23 unit test cases bao phủ toàn diện Task A (phân loại ý định/rủi ro), Task E (kiểm định khẳng định), và 12 tình huống học vụ nhạy cảm thực tế (T1–T12). |
| `docs/progress.md`, `docs/decisions.md`, `docs/todo.md` | Ghi nhận mốc tiến độ Phiên 6D, Quyết định 40 và cập nhật danh mục công việc. |

## 3. Vì sao làm như vậy
### Quyết định 1: Không biến chế tài có điều kiện thành kết luận tuyệt đối
- Quyết định: Khi sinh viên hỏi về việc chậm nộp học phí hay BHYT có bị cấm thi không, chatbot phải trả lời có điều kiện, nêu rõ điều kiện kích hoạt trong quy chế gốc (*"cố tình chậm nộp hoặc không nộp... mà không có lý do chính đáng"*), không được trả lời tuyệt đối kiểu *"Không được. Bạn sẽ bị cấm thi."*
- Phương án đã cân nhắc:
  - Phương án A: Trả lời ngắn gọn "Có, bạn bị cấm thi" cho an toàn kỷ luật.
  - Phương án B: Giữ nguyên văn bản quy chế và nêu rõ điều kiện áp dụng, hướng dẫn các trường hợp có lý do chính đáng và cách liên hệ nhà trường.
- Vì sao chọn: Phương án B. Trong văn bản gốc `2021-8-5-8-33-34a-pl-d0-4` (Phụ lục Khung kỷ luật dòng 10), nhà trường chỉ cấm thi đối với hành vi "cố tình... mà không có lý do chính đáng". Nếu chatbot cắt bỏ cụm từ này, câu trả lời vừa sai lệch văn bản pháp lý, vừa làm sinh viên hoảng loạn vô cớ.
- Vì sao loại phương án còn lại: Phương án A sai về mặt pháp lý và gây hại tâm lý cho sinh viên có hoàn cảnh khó khăn thực sự.
- Loại căn cứ: [tài liệu: `2021_8_5_8_33_34A.docx`, Phụ lục Khung kỷ luật; Quyết định 40]
- Đánh đổi: Câu trả lời cần dài hơn 1–2 câu để giải thích rõ điều kiện và lưu ý phân biệt.

### Quyết định 2: Phân loại ý định học vụ và rủi ro bằng Rule-based Regex thay vì gọi thêm LLM
- Quyết định: Sử dụng module regex tiếng Việt chuẩn hóa NFC nhận diện 8 nhóm ý định và 3 cấp độ rủi ro trong `classify_academic_intent_and_risk()`.
- Phương án đã cân nhắc:
  - Phương án A: Gọi thêm 1 lượt LLM prompt phụ để phân loại intent và đánh giá risk.
  - Phương án B: Phân loại bằng bộ luật regex nhanh dựa trên các gốc từ khóa học vụ đặc trưng.
- Vì sao chọn: Phương án B chạy tức thì (< 1 ms), hoàn toàn offline, 0 tốn chi phí token và không làm tăng TTFT (Time-to-First-Token) của người dùng.
- Vì sao loại phương án còn lại: Phương án A tốn thêm 1–2 giây độ trễ và làm tăng gấp đôi chi phí API.
- Loại căn cứ: [kỹ thuật: tối ưu độ trễ và chi phí hệ thống RAG]
- Đánh đổi: Phải duy trì danh sách từ khóa đại diện cho các nhóm chính sách học vụ.

### Quyết định 3: Claim Verifier giáng cấp Badge khi câu trả lời chứa khẳng định cực đoan thiếu căn cứ
- Quyết định: Trong `verify_claims()`, nếu câu trả lời chứa các khẳng định tuyệt đối ("chắc chắn bị cấm thi", "bạn sẽ bị cấm thi") mà không đi kèm các từ hạn định ("có thể", "nếu không có lý do chính đáng", "tùy thuộc"), hệ thống sẽ tự động hạ cấp huy hiệu từ `Đã đối chiếu nguồn cho các khẳng định` thành `Cần đối chiếu điều kiện áp dụng`.
- Phương án đã cân nhắc:
  - Phương án A: Cắt bỏ câu trả lời và từ chối phát sinh.
  - Phương án B: Giữ nguyên văn bản nhưng giáng cấp huy hiệu kiểm chứng và cảnh báo trên giao diện.
- Vì sao chọn: Phương án B cung cấp phản hồi minh bạch, bảo vệ sinh viên khỏi việc hiểu lầm rằng khẳng định cực đoan đó là quyết định chính thức đã được kiểm chứng của nhà trường.
- Vì sao loại phương án còn lại: Phương án A gây đứt gãy trải nghiệm người dùng khi câu trả lời thực tế vẫn có thể chứa thông tin tham khảo hữu ích.
- Loại căn cứ: [kỹ thuật: Verification Pipeline & User Trust Guardrail]
- Đánh đổi: Thêm một bước kiểm tra chuỗi regex sau khi sinh văn bản (< 1 ms).

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Chế tài có điều kiện (Conditional Sanction) vs. Khẳng định tuyệt đối (Absolute Claim):**
  - *Ví dụ đời thường:* Luật giao thông quy định: *"Người vượt đèn đỏ sẽ bị phạt tiền, trừ trường hợp xe cứu thương đang làm nhiệm vụ hoặc có hiệu lệnh của cảnh sát giao thông"*. Nếu ai đó nói: *"Cứ vượt đèn đỏ là chắc chắn bị phạt 100%"*, họ đã bỏ qua điều kiện ngoại lệ.
  - *Trong đại học:* Quy chế ghi: *"Cố tình chậm nộp học phí mà không có lý do chính đáng thì bị cấm thi"*. Chatbot phải giải thích cả phần "lý do chính đáng" (như sinh viên có đơn xin gia hạn vì hoàn cảnh khó khăn đột xuất) chứ không được dọa dẫm sinh viên bằng một phán quyết tuyệt đối.
- **Kiểm định khẳng định (Claim-Level Verification):**
  - Là bộ lọc tự động kiểm tra xem từng tuyên bố mạnh trong câu trả lời của AI có đủ bằng chứng và điều kiện đi kèm hay không. Nếu AI tự ý "phán quyết" thay cho nhà trường mà không có chứng cứ cá nhân cụ thể, hệ thống sẽ bật đèn vàng cảnh báo sinh viên cần kiểm tra lại.

## 5. Đã kiểm tra thế nào
- Lệnh 1: `ai-service\venv\Scripts\python.exe -m unittest tests.test_student_centered_rag -v`
- Kết quả thật:
  ```text
  Ran 23 tests in 0.002s
  OK
  ```
- Lệnh 2: `cd ai-service; venv\Scripts\python.exe -m unittest discover -s tests -v`
- Kết quả thật:
  ```text
  Ran 146 tests in 7.466s
  OK (skipped=1)
  ```
- Lệnh 3 (Kiểm thử thực tế API Streaming SSE trên live server):
  `ai-service\venv\Scripts\python.exe C:\Users\dat70\.gemini\antigravity-cli\brain\f79cba6c-80dc-4e4e-bb72-afe6f17963b8\scratch\live_stream_test.py`
- Kết quả thật:
  1. Câu hỏi `BHYT có bắt buộc không và có quyền lợi gì?`:
     - Intent: `BENEFIT_EXPLANATION` | Risk: `LOW` | Sufficiency: `SUFFICIENT`
     - Badges: `['Có trích dẫn nguồn', 'Đã đối chiếu nguồn cho các khẳng định']`
     - Trả lời: Mở đầu trực tiếp bằng quyền lợi chăm sóc sức khỏe ban đầu [4], sau đó mới giải thích nghĩa vụ đóng [1].
  2. Câu hỏi `Em chưa kịp đóng học phí thì ngày mai có bị cấm thi không?`:
     - Intent: `PERSONAL_CASE` | Risk: `HIGH` | Sufficiency: `SUFFICIENT`
     - Trả lời: Nêu rõ điều kiện "cố tình... mà không có lý do chính đáng" [2], khẳng định chatbot không thể tra cứu dữ liệu cá nhân hay quyết định thay nhà trường, hướng dẫn kiểm tra thông báo thi và phòng Đào tạo/Kế toán.
  3. Câu hỏi `Chậm nộp học phí có bị cấm thi không?`:
     - Intent: `ACADEMIC_CONSEQUENCE` | Risk: `HIGH` | Sufficiency: `SUFFICIENT`
     - Trả lời: Khẳng định có thể bị cấm thi nếu cố tình vi phạm không có lý do chính đáng [1], đồng thời hướng dẫn thủ tục xin gia hạn nếu có hoàn cảnh khó khăn.
- Kết luận: **ĐẠT 100%**.
- Số lệnh gọi API trả phí đã dùng: 3 lượt gọi thực tế phục vụ đo benchmark live stream.

## 6. Chưa chắc chắn, rủi ro, giả định
- Quy định chi tiết về mẫu đơn và quy trình xét duyệt gia hạn học phí cụ thể của từng học kỳ hiện nằm trong các thông báo hướng dẫn thời vụ (chưa có trong 10 văn bản quy chế chuẩn cốt lõi đã nạp), nên chatbot đang hướng dẫn sinh viên liên hệ Phòng Kế hoạch - Tài chính hoặc Cổng thông tin sinh viên để nhận mẫu thông báo mới nhất.

## 7. Điều đã không làm và lý do
- Không tự bịa đặt thời hạn gia hạn cụ thể (ví dụ "được gia hạn 30 ngày") vì trong các văn bản quy chế hiện tại không có con số này.
- Không yêu cầu hay thu thập bất kỳ thông tin cá nhân nhạy cảm nào (CCCD, số tài khoản, mật khẩu) của sinh viên.
- Không sửa đổi hay bổ sung nhãn cho tập dữ liệu benchmark `cau_hoi_thu.csv` (tuân thủ quy tắc Agent không tự soạn nhãn).

## 8. Việc tiếp theo
- Chuẩn bị báo cáo tổng kết hoàn thành gói nhiệm vụ Student-Centered RAG cho người dùng.
- Sẵn sàng kịch bản trình diễn Demo Nhà trường với các ca kiểm thử chính sách nhạy cảm đạt độ an toàn và thấu cảm tối đa.

## 9. Câu hỏi cho người dùng
- Hiện tại khi sinh viên có hoàn cảnh khó khăn cần gia hạn học phí, nhà trường có biểu mẫu trực tuyến trên cổng portal hay sinh viên phải nộp đơn giấy tại Phòng Kế hoạch - Tài chính? Nếu có link portal chính thức, chúng ta có thể bổ sung đường dẫn vào câu trả lời hướng dẫn thủ tục.

## 10. Ba câu tự kiểm tra hiểu bài
1. Vì sao câu trả lời *"Bạn chưa đóng học phí nên chắc chắn bị cấm thi"* lại bị coi là câu trả lời sai lệch và nguy hại đối với sinh viên?
2. Trong RAG lấy sinh viên làm trung tâm, khi sinh viên hỏi về quyền lợi BHYT, vì sao không nên mở đầu câu trả lời bằng các điều khoản kỷ luật trừ điểm rèn luyện?
3. Khi sinh viên hỏi một câu hỏi mang tính cá nhân cao (ví dụ *"Em nợ 5 triệu có được thi ngày mai không?"*), chatbot cần phản hồi theo nguyên tắc nào?

(Hãy tự trả lời trước khi mở phần đáp án bên dưới.)

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì trong văn bản quy chế gốc của nhà trường (Phụ lục Khung kỷ luật), chế tài cấm thi chỉ áp dụng đối với hành vi *"Cố tình chậm nộp hoặc không nộp... mà không có lý do chính đáng"*. Khẳng định chắc chắn bị cấm thi đã tự ý bỏ qua điều kiện cốt lõi về "lý do chính đáng" và tự ý tước đoạt quyền được giải trình/gia hạn của sinh viên.
2. Vì mục đích chính của BHYT là bảo vệ sức khỏe và hỗ trợ tài chính y tế cho sinh viên. Mở đầu bằng đe dọa kỷ luật sẽ tạo cảm giác trừng phạt, gây tâm lý tiêu cực và sai lệch bản chất của chính sách an sinh xã hội.
3. Chatbot cần: (1) Cung cấp khung quy định chung của trường; (2) Nói rõ chatbot không có thẩm quyền và không tra cứu dữ liệu cá nhân nên không thể khẳng định quyết định cụ thể; (3) Hướng dẫn sinh viên kiểm tra danh sách thi chính thức trên cổng thông tin hoặc liên hệ trực tiếp đơn vị phụ trách (Phòng Đào tạo / Tài chính); (4) Tuyệt đối không yêu cầu sinh viên cung cấp CCCD hay mật khẩu cá nhân.

</details>
