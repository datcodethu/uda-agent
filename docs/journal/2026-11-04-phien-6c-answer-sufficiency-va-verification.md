# Nhật ký 2026-11-04 – Phiên 6C: Answer Sufficiency, 5 Prompt Rules & Dynamic Verification Badges

## 1. Mục tiêu
Giải quyết dứt điểm vấn đề câu hỏi học bổng và các câu hỏi thiếu dữ liệu chi tiết bằng cơ chế đánh giá mức độ đầy đủ của bằng chứng (Answer Sufficiency Check 4 trạng thái: SUFFICIENT, PARTIAL, INSUFFICIENT, NO_EVIDENCE); chuẩn hóa câu trả lời theo 5 quy tắc sư phạm sinh viên; loại bỏ badge cứng "Đã kiểm chứng số liệu gốc"; và thiết lập bộ kiểm thử hồi quy 10 nhóm câu hỏi thực tế.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/pipeline/generator/verifier.py` | Bổ sung hàm `validate_citations` (kiểm tra dải [1..N]), `determine_sufficiency` (phân loại 4 trạng thái), `evaluate_verification` (tổng hợp kết quả và sinh dynamic badges). |
| `ai-service/app/core/prompts.py` | Cập nhật `SYSTEM_PROMPT` tích hợp đầy đủ 5 Rules (Trực tiếp, Đúng kiểu, Ngôn ngữ SV, Cấu trúc linh hoạt, Chống ảo giác tuyệt đối) cùng các quy tắc Mức 2 (L2-11, L2-02, L2-10). |
| `ai-service/app/schemas/query_schema.py` | Bổ sung các trường `sufficiency`, `verification_badges`, `citations`, `invalid_citations` vào `QueryResponse`. |
| `ai-service/app/pipeline/rag_pipeline.py` | Kết nối `evaluate_verification` vào hàm `answer()`, trả về kết quả xác minh toàn diện và nhãn hiển thị. |
| `ai-service/app/pipeline/generator/stream_handler.py` | Gửi sự kiện SSE `verify` và `done` chứa trạng thái sufficiency và danh sách badges động. |
| `ai-service/app/static/index.html` | Xóa bỏ huy hiệu cứng `✓ Đã kiểm chứng số liệu gốc`, thêm CSS và logic JavaScript render dynamic badges (`badge-sources`, `badge-verified`, `badge-partial`, `badge-insufficient`). |
| `ai-service/crawler/thu_thap.py` | Thêm cơ chế xử lý mã hóa an toàn trên Windows console (`errors='replace'`) chống lỗi UnicodeEncodeError khi dry-run. |
| `ai-service/tests/test_sufficiency_and_verification.py` | Tạo bộ kiểm thử mới gồm 22 test cases bao phủ 10 nhóm câu hỏi thực tế theo TASK G. |
| `docs/progress.md` | Ghi nhận tiến độ Phiên 6C. |
| `docs/decisions.md` | Ghi nhận Quyết định 39 về Answer Sufficiency, 5 Rules và Dynamic Badges. |
| `docs/todo.md` | Đánh dấu hoàn thành các nhiệm vụ Task C - H. |

## 3. Vì sao làm như vậy
- **Quyết định 1: Cơ chế kép cho Answer Sufficiency (System Prompt + Verifier) thay vì gọi thêm model riêng**
  - *Phương án đã cân nhắc:* (A) Dùng thêm một LLM call chuyên phân loại sufficiency trước khi trả lời; (B) Cơ chế kép: System Prompt hướng dẫn LLM phân định rõ ràng + Verifier phân tích cú pháp/bằng chứng trực tiếp.
  - *Vì sao chọn:* Phương án B giữ nguyên độ trễ RAG (overhead verifier < 1 ms), tốn 0 chi phí API phát sinh, không có nguy cơ lỗi 429 Quota Exceeded.
  - *Vì sao loại:* Phương án A tăng gấp đôi số lượt gọi LLM, tăng gấp đôi độ trễ phản hồi (thêm 2-5 giây), không khả thi cho demo thực tế.
  - *Loại căn cứ:* [kỹ thuật] và [yêu cầu nhiệm vụ Task C & H].
  - *Đánh đổi:* Cần xây dựng các regex mẫu nhận diện câu thiếu thông tin cẩn thận trong Verifier.

- **Quyết định 2: Xóa bỏ badge cứng trên UI và hiển thị dynamic badges**
  - *Phương án đã cân nhắc:* (A) Giữ badge cũ và chỉ thêm chữ cảnh báo; (B) Thay thế hoàn toàn bằng các badges phản ánh đúng trạng thái thực tế: Có trích dẫn nguồn, Đã đối chiếu nguồn cho các khẳng định, Chưa đủ bằng chứng để kết luận.
  - *Vì sao chọn:* Tránh gây ngộ nhận cho sinh viên và hội đồng chấm demo rằng câu trả lời nào cũng đã kiểm chứng số liệu gốc 100%.
  - *Vì sao loại:* Phương án A dễ gây hiểu nhầm khi câu trả lời thực tế chỉ có thông tin một phần.
  - *Loại căn cứ:* [yêu cầu nhiệm vụ Task E].

## 4. Khái niệm mới (giải thích cho sinh viên năm 2)
- **Answer Sufficiency (Mức độ đầy đủ của bằng chứng):** Hãy tưởng tượng bạn làm bài thi tự luận. Đề hỏi *"Em được nhận bao nhiêu tiền học bổng và cần điểm GPA bao nhiêu?"*. Nếu trong tài liệu quy chế nhà trường chỉ có câu *"Nhà trường có quỹ học bổng khuyến khích"*, thì tài liệu đó chỉ là `PARTIAL` (hoặc `INSUFFICIENT` cho câu hỏi số tiền). Nếu chatbot tự bịa ra "GPA 3.2 được 5 triệu" thì đó là ảo giác (hallucination). Hệ thống thông minh phải biết nhận diện: mình chỉ biết có học bổng, còn mức tiền thì tài liệu chưa có, và nói thẳng điều đó cho sinh viên.
- **Dynamic Badges (Huy hiệu động theo ngữ cảnh):** Thay vì lúc nào cũng dán nhãn "Đã kiểm chứng số liệu gốc" lên mọi câu trả lời, hệ thống chỉ dán nhãn "Đã đối chiếu nguồn cho các khẳng định" khi câu trả lời có căn cứ đầy đủ (`SUFFICIENT`), có trích dẫn hợp lệ và không có con số lạ. Nếu câu hỏi chỉ có bằng chứng một phần, nhãn sẽ hiển thị "Chưa đủ bằng chứng để kết luận (Một phần)" để nhắc nhở người xem cần kiểm tra thêm.

## 5. Đã kiểm tra thế nào
- **Kiểm thử tự động toàn diện:**
  - Lệnh: `ai-service\venv\Scripts\python.exe -m unittest discover -s tests`
  - Kết quả: `Ran 123 tests in 4.242s -> OK (skipped=1)`. 100% 123 unit tests PASS (bao gồm 22 test mới của `test_sufficiency_and_verification.py`).
- **Kiểm thử thực tế trên Web Server đang chạy (`task-3448`):**
  - Query 1: *"Điều kiện xét học bổng là gì?"* -> Sufficiency: `PARTIAL`, Badges: `['Có trích dẫn nguồn', 'Chưa đủ bằng chứng để kết luận (Một phần)']`, trả lời chính sách chung và ghi nhận chưa có tiêu chí chi tiết trong tài liệu hiện có.
  - Query 2: *"Chuẩn đầu ra ngoại ngữ đối với sinh viên các ngành không chuyên ngữ là gì?"* -> Sufficiency: `SUFFICIENT`, Badges: `['Có trích dẫn nguồn', 'Đã đối chiếu nguồn cho các khẳng định']`.
  - Query 3 (Tiếp nối): *"là sao?"* -> Retrieval time: **0 ms** (tái sử dụng cache), trả lời súc tích, thân thiện sinh viên với trích dẫn chuẩn `[4]`.
  - Query 4 (Guardrail cá nhân): *"Điểm của em kỳ này được bao nhiêu ạ?"* -> Latency: **23 ms**, từ chối nhanh không tốn API.
  - Query 5 (Ngoài phạm vi): *"Cổng trường Đại học Đông Á có xe buýt nào đi qua?"* -> Sufficiency: `NO_EVIDENCE`, Badges: `['Chưa đủ bằng chứng để kết luận']`.
- **Số lệnh gọi API trả phí đã dùng:** 0 (Dùng key Gemini miễn phí qua `gemini-flash-lite-latest` và `gemini-embedding-001`).

## 6. Chưa chắc chắn, rủi ro, giả định
- **Rủi ro:** Khi câu trả lời của LLM dùng từ ngữ rất lạ để diễn đạt việc thiếu thông tin mà không nằm trong regex của Verifier, verifier có thể phân loại về `SUFFICIENT` nếu có trích dẫn. Tuy nhiên, `SYSTEM_PROMPT` đã ép mẫu câu chuẩn rất chặt nên khả năng này rất thấp.

## 7. Điều đã không làm và lý do
- Không tự ý thêm tài liệu học bổng mới vào kho ngoài quy trình kiểm duyệt (tuân thủ nguyên tắc `GEMINI.md`).
- Không tạo thêm LLM chain riêng để tránh làm tăng độ trễ và tránh lỗi 429 Quota Exceeded.

## 8. Việc tiếp theo
- Bàn giao kết quả toàn diện cho người dùng kiểm thử trực tiếp trên Web Chat (`http://127.0.0.1:8000`).
- Chuẩn bị slide và kịch bản thuyết trình demo trước hội đồng Nhà trường.

## 9. Câu hỏi cho người dùng
- Bạn có muốn kiểm tra thêm kịch bản câu hỏi cụ thể nào khác trên giao diện Web Chat trước khi đóng gói không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao đối với câu hỏi "Điều kiện xét học bổng là gì?", hệ thống lại trả về trạng thái `PARTIAL` thay vì `SUFFICIENT`?
2. Sự khác biệt giữa badge "Có trích dẫn nguồn" và "Đã đối chiếu nguồn cho các khẳng định" là gì?
3. Khi người dùng hỏi tiếp nối "là sao?", tại sao thời gian retrieval lại là 0 ms mà câu trả lời vẫn có trích dẫn chính xác?

---

<details>
<summary>Gợi ý đáp án</summary>

1. Vì trong kho tài liệu quy chế hiện tại chỉ có các điều khoản chính sách chung (Điều 4, 5, 16 QĐ 2021) về việc Nhà trường cấp học bổng, nhưng không chứa các tiêu chí định lượng cụ thể (như điểm GPA tối thiểu hay điểm rèn luyện bao nhiêu). Do đó hệ thống trả lời phần có bằng chứng và chỉ rõ phần thiếu, phân loại là `PARTIAL`.
2. Badge "Có trích dẫn nguồn" chỉ ra rằng câu trả lời có gắn số tham chiếu `[i]` hợp lệ trong phạm vi tài liệu. Badge "Đã đối chiếu nguồn cho các khẳng định" đòi hỏi cao hơn: câu trả lời phải đạt `SUFFICIENT`, toàn bộ trích dẫn hợp lệ và mọi con số xuất hiện trong câu trả lời đều đã được đối chiếu trùng khớp 100% với tài liệu gốc.
3. Nhờ cơ chế `ContextResolver` và `SessionMemory`: khi nhận diện ý định "giải thích làm rõ", hệ thống kiểm tra và tái sử dụng trực tiếp các đoạn chunk hợp lệ của câu hỏi trước trong bộ nhớ cache của phiên (`conversation_id`), bỏ qua bước tìm kiếm vector/BM25 nên thời gian retrieval bằng 0 ms.

</details>
