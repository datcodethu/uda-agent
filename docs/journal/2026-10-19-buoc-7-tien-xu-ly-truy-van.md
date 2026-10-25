# Nhật ký 2026-10-19 – Bước 7: Tiền xử lý câu hỏi sinh viên (Từ viết tắt & Bộ phân loại ý định)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Triển khai bộ tiền xử lý câu hỏi sinh viên (Bước 7 trong `docs/ai-service.md`): mở rộng từ điển từ viết tắt có/không dấu và xây dựng bộ phân loại ý định thông minh (`intent_classifier.py`) kèm Fast-path Guardrail để trả lời ngay lập tức các câu hỏi riêng tư, chào hỏi hoặc mơ hồ, tiết kiệm 100% chi phí API.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/data/seed/abbreviations_seed.json` | Mở rộng bổ sung 25 từ viết tắt thực tế thu thập từ khảo sát sinh viên ĐH Đông Á và quy chế trường (bổ sung: `sv`, `hb`, `hp`, `drl`, `đrl`, `dkhp`, `đkhp`, `cdr`, `cđr`, `ctdt`, `ctđt`, `cntt`, `it`, `csdl`, `ctxh`, `ctsv`, `qldt`, `bgh`, `tkb`, `nckh`...). |
| `ai-service/app/pipeline/query_transformation/intent_classifier.py` | Tạo mới module phân loại 4 nhóm ý định: `ACADEMIC`, `PERSONAL`, `OUT_OF_SCOPE`, `AMBIGUOUS` dựa trên bộ luật Regex tối ưu và kiểm tra độ dài câu. |
| `ai-service/app/core/prompts.py` | Bổ sung 3 mẫu phản hồi chuẩn (`PERSONAL_REPLY`, `OUT_OF_SCOPE_REPLY`, `AMBIGUOUS_REPLY`) hỗ trợ Fast-path Guardrail. |
| `ai-service/app/pipeline/rag_pipeline.py` | Tích hợp `classify()` vào `prepare()` và `answer()`: nếu câu hỏi thuộc nhóm dữ liệu cá nhân, chào hỏi hoặc mơ hồ thì từ chối ngay lập tức (`refused=True`), phản hồi trong 0 ms mà không gọi embedding, vector search hay LLM. |
| `ai-service/tests/test_core.py` | Bổ sung 9 unit test mới: mở rộng `TestAbbreviation` (từ viết tắt mới và dạng không dấu), thêm `TestIntentClassifier` (4 nhóm ý định) và `TestRagPipelineFastPath` (kiểm tra đường truyền tắt). Tổng số test nâng lên **72/72 PASS**. |
| `docs/decisions.md` | Ghi nhận quyết định triển khai Bước 7 và kết quả kiểm thử. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Bước 7 (Mục 7.1 & 7.3). |
| `docs/journal/2026-10-19-buoc-7-tien-xu-ly-truy-van.md` | Viết nhật ký khoa học chi tiết phiên làm việc theo mẫu chuẩn `_mau.md`. |

## 3. Vì sao làm như vậy
- **Quyết định 1: Hỗ trợ cả hai dạng viết tắt có dấu và không dấu trong từ điển**
  - Phương án đã cân nhắc: Chỉ hỗ trợ dạng chuẩn có dấu (`đrl`, `đkhp`, `cđr`) hoặc hỗ trợ thêm cả dạng không dấu (`drl`, `dkhp`, `cdr`).
  - Vì sao chọn: Thống kê từ khảo sát sinh viên ĐH Đông Á cho thấy khi chat trên điện thoại hoặc máy tính, sinh viên thường xuyên gõ không dấu (`drl`, `dkhp`, `cdr`). Hỗ trợ cả hai dạng giúp mở rộng truy vấn đồng đều cho mọi thói quen gõ của sinh viên.
  - Vì sao loại phương án còn lại: Nếu chỉ hỗ trợ có dấu, hệ thống sẽ bỏ lỡ rất nhiều câu hỏi thực tế của sinh viên.
  - Loại căn cứ: [tài liệu: `ai-service/data/khao_sat_goc.csv`] & [kỹ thuật].
  - Đánh đổi: File từ điển có thêm vài dòng nhưng kích thước vẫn cực nhẹ (< 1KB).

- **Quyết định 2: Dùng bộ luật Regex (Rule-based) thay vì gọi LLM để phân loại ý định ở bước đầu**
  - Phương án đã cân nhắc: Gọi LLM (như Gemini Flash) với prompt phân loại ý định hoặc dùng biểu thức chính quy (Regex).
  - Vì sao chọn: Quy tắc trong `docs/ai-service.md` mục 7.3 nhấn mạnh mục tiêu tốc độ và chi phí: phân loại bằng luật chạy chỉ mất < 1 ms, hoàn toàn miễn phí, độc lập với mạng internet và không tốn token/quota API hàng ngày.
  - Vì sao loại phương án còn lại: Gọi LLM cho mỗi câu hỏi chỉ để phân loại sẽ làm tăng độ trễ thêm 500-1.500 ms và tiêu tốn quota API không cần thiết.
  - Loại căn cứ: [tài liệu: `docs/ai-service.md`, mục 7.3] & [kỹ thuật].
  - Đánh đổi: Bộ luật Regex cần được bao quát kỹ lưỡng các mẫu câu thông dụng. Các câu hỏi ngoài phạm vi phức tạp hơn sẽ được bảo vệ bởi tầng kiểm tra ngưỡng điểm tương đồng (min_dense_score) ở bước sau.

- **Quyết định 3: Thiết lập cơ chế Fast-path Guardrail ngay đầu hàm `prepare()`**
  - Phương án đã cân nhắc: Chờ chạy xong truy xuất tài liệu rồi mới quyết định từ chối hay chặn ngay từ đầu hàm `prepare()`.
  - Vì sao chọn: Nếu sinh viên hỏi *"Điểm của em kỳ này bao nhiêu?"* hoặc *"Xin chào bot"*, việc gọi nhúng vector rồi tìm kiếm trong kho quy chế là lãng phí tài nguyên và có nguy cơ trả lời sai (hallucination) do ép gượng dữ liệu quy chế vào câu hỏi cá nhân. Chặn ngay đầu luồng giúp trả lời tức thì (< 1 ms), an toàn tuyệt đối về dữ liệu cá nhân.
  - Loại căn cứ: [kỹ thuật] & [tài liệu: `docs/plan.md`, mục 5.2].
  - Đánh đổi: Cần thêm 3 câu phản hồi chuẩn vào `prompts.py`.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Fast-path Guardrail (Đường truyền tắt bảo vệ):**
  - *Ví dụ đời thường:* Giống như bảo vệ ở cổng tòa nhà: khi một người đến hỏi "Phòng vệ sinh ở đâu?" hoặc "Tôi muốn tìm gặp giám đốc cá nhân", bảo vệ trả lời ngay tại cửa hoặc chỉ sang bàn lễ tân hướng dẫn đăng nhập, chứ không cần gọi điện bắt cả phòng hành chính trên tầng 10 phải lục tìm hồ sơ.
  - *Trong RAG:* Khi phát hiện câu hỏi thuộc loại không cần truy xuất tri thức (như chào hỏi, hỏi thông tin cá nhân mà bot không được phép giữ), hệ thống chuyển hướng sang "đường truyền tắt", trả về câu phản hồi định hướng ngay lập tức mà không tiêu tốn tài nguyên tìm kiếm vector hay gọi trí tuệ nhân tạo.
- **Query Transformation (Biến đổi truy vấn):**
  - *Ví dụ:* Bạn đi chợ hỏi mua "rau dấp cá", người bán quen gọi là "diếp cá", nếu bảng danh mục hàng hóa của quầy hàng ghi cả hai tên thì việc tìm kiếm sẽ không bao giờ bị trượt.
  - *Trong RAG:* Trước khi đưa câu hỏi vào bộ tìm kiếm, hệ thống biến đổi nhẹ câu hỏi (ví dụ mở rộng từ viết tắt: `sv` -> `sv (sinh viên)`). Nhờ vậy, cả từ khóa gốc và từ ngữ pháp lý chuẩn đều cùng xuất hiện trong câu truy vấn, giúp bộ máy tìm kiếm (cả BM25 và Vector) đạt độ chính xác cao nhất.

## 5. Đã kiểm tra thế nào
- **Kiểm thử đơn vị:**
  - Lệnh: `venv\Scripts\python.exe -m unittest discover -s tests -v`
  - Kết quả: `Ran 72 tests in 6.138s - OK`. Toàn bộ 72/72 test đều PASS.
- **Kiểm thử lại Benchmark thực nghiệm:**
  - Lệnh: `venv\Scripts\python.exe -m scripts.chay_cau_hoi_thu --retrieval-only --mode hybrid`
  - Kết quả thật:
```
==========================================================================================
 BẢNG TỔNG HỢP KẾT QUẢ ĐÁNH GIÁ BENCHMARK THEO NHÓM
==========================================================================================
Nhóm câu hỏi       | Số câu | MH Đoạn        | MH Trả lời     | Hit Điều       | TC Đúng        | TC Nhầm        | TG TB
------------------------------------------------------------------------------------------
chen_lenh          | 1      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 2061 ms
dien_dat_khac      | 1      | 66.7% (2/3)    | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 416 ms
gan_pham_vi        | 2      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 1766 ms
khong_dau          | 1      | 75.0% (3/4)    | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 748 ms
ngoai_pham_vi      | 1      | N/A            | N/A (retrieval) | N/A            | N/A            | N/A            | 0 ms
tong_hop           | 1      | 100.0% (3/3)   | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 464 ms
truc_tiep          | 5      | 100.0% (18/18) | N/A (retrieval) | 100.0% (5/5)   | N/A            | N/A            | 822 ms
viet_tat           | 1      | 100.0% (2/2)   | N/A (retrieval) | 100.0% (1/1)   | N/A            | N/A            | 702 ms
------------------------------------------------------------------------------------------
TỔNG CỘNG          | 13     | 93.3% (28/30)  | N/A (retrieval) | 100.0% (9/9)   | N/A            | N/A            | 926 ms
==========================================================================================
```
- **Kết luận:** **ĐẠT**.
  - Câu `c12` (ngoài phạm vi - hỏi tuyến xe buýt) được Fast-path xử lý hoàn hảo với **TG TB = 0 ms**, không tiêu tốn embedding hay vector search.
  - Toàn bộ chỉ số truy xuất: **100% (9/9) Hit Điều** và **93.3% (28/30) must-have** được duy trì tuyệt đối.
- **Số lệnh gọi API trả phí đã dùng:** 0 lượt gọi API trả phí cho quá trình phát triển Bước 7; 12 lệnh embedding khi chạy benchmark kiểm chứng (an toàn trong giới hạn 30).

## 6. Chưa chắc chắn, rủi ro, giả định
- Bộ luật Regex hiện tại tập trung vào các mẫu câu tiếng Việt thông dụng nhất của sinh viên. Có thể có một số cách diễn đạt khẩu ngữ rất lạ chưa nằm trong danh sách pattern, khi đó hệ thống sẽ xem như câu hỏi học vụ thông thường và để tầng Vector + Ngưỡng từ chối xử lý tiếp.

## 7. Điều đã không làm và lý do
- Chưa làm module viết lại câu hỏi hỏi dồn (`query_rewriter.py` - Bước 7.2) vì bước này cần gọi thêm một lượt LLM sinh chữ, làm tăng thời gian phản hồi (chữ đầu tiên > 3s). Nên dành bước này thử nghiệm sau khi nối với giao diện chat đa lượt.

## 8. Việc tiếp theo
1. **Bước 8 hoặc Bước 9 trong `docs/ai-service.md`**:
   - Khớp câu hỏi thường gặp FAQ (`faq_matcher.py`) hoặc hoàn thiện module sinh văn bản LLM adapter và verifier kiểm chứng số liệu.
2. Thử nghiệm hỏi đáp tương tác trực tiếp qua terminal bằng `scripts/chat_cli.py` với các câu hỏi thực tế có từ viết tắt và câu hỏi cá nhân.

## 9. Câu hỏi cho người dùng
- Bạn có muốn chúng ta chạy thử nghiệm hỏi đáp trực tiếp một vài câu hỏi qua `scripts/chat_cli.py` (để kiểm tra xem câu hỏi viết tắt, câu hỏi cá nhân và câu hỏi quy chế phản hồi thực tế ra sao) hay chuyển sang bước tiếp theo trong tài liệu `docs/ai-service.md`?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao hàm `expand_abbreviations()` lại chọn cách *thêm* từ đầy đủ vào cuối câu (trong dấu ngoặc đơn) thay vì *thay thế* trực tiếp từ viết tắt trong câu hỏi?
2. Tại sao câu hỏi: *"Em nợ học phí thì có được đăng ký môn không ạ?"* lại được phân loại là `ACADEMIC` (học vụ) chứ không bị phân loại nhầm thành `PERSONAL` (dữ liệu cá nhân)?
3. Lợi ích lớn nhất của cơ chế Fast-path Guardrail khi sinh viên nhập câu hỏi như *"Điểm của em kỳ này mấy?"* hoặc *"Xin chào bot"* là gì?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì trong nhiều văn bản quy chế chính thức của nhà trường, bản thân văn bản đôi khi cũng sử dụng chính từ viết tắt đó (ví dụ "chuẩn B1", "khoa CNTT", "chứng chỉ TOEIC"). Nếu ta thay thế hoàn toàn từ gốc, bộ tìm kiếm BM25 (so khớp từ khóa chính xác) có thể bị trượt nếu văn bản chỉ có từ viết tắt mà không có từ đầy đủ. Giữ cả hai dạng trong câu hỏi giúp cả BM25 lẫn Vector search bắt trúng trong mọi trường hợp.
2. Vì câu hỏi này hỏi về **quy định/chính sách chung** của nhà trường (sinh viên nợ học phí thì quy chế có cho phép đăng ký môn học hay không). Câu hỏi không chứa các từ khóa tra cứu số liệu nợ cụ thể của bản thân (như "nợ bao nhiêu tiền", "thiếu mấy triệu"). Do đó, đây là câu hỏi học vụ cần được đưa vào kho quy chế để giải đáp.
3. Lợi ích lớn nhất là: (1) Phản hồi siêu tốc ngay lập tức (< 1 ms); (2) Tiết kiệm 100% quota và chi phí gọi Gemini/Qdrant; (3) Ngăn chặn triệt để tình trạng ảo giác (hallucination) khi chatbot cố tình lục tìm quy chế để bịa ra điểm số của sinh viên.

</details>
