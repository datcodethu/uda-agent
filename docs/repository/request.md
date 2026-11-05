# request.md — Kiểm thử toàn diện Chatbot Advanced RAG Đại học Đông Á

> **Loại tài liệu:** Yêu cầu thực thi cho AI Coding Agent (Antigravity/Codex).  
> **Nguồn:** `Kết quả khảo sát - câu hỏi thường gặp của sinh viên.xlsx`, sheet `Form Responses 1`, hàng 2–78, cột F–I.  
> **Quy mô:** 77 phiếu; **75 lượt câu hỏi/ý cần kiểm thử**, **36 ô/mục không phải câu hỏi đã tách ra kiểm toán**.  
> **Trạng thái:** Tập dữ liệu khảo sát, **KHÔNG PHẢI** bộ đáp án chuẩn hoặc nhãn đã được người dùng duyệt.  
> **Tệp dữ liệu:** `survey_questions_test_dataset.csv` và `survey_excluded_entries.csv`.  
> **Đầu ra bắt buộc do Agent tạo:** `evaluation/survey_qa_<RUN_ID>/test_cases.csv`, `results.csv`, `responses.jsonl`, `report.md`, `issues.md`, `run_manifest.json`. Các đường dẫn này là cấu trúc **đề nghị tạo trong repository**, không phải báo cáo đã chạy.

## I. Mục tiêu

Kiểm tra **toàn bộ 75 lượt câu hỏi gốc** (kể cả câu trùng, câu ngắn, câu sai chính tả, câu phản ánh và câu không rõ ý), xác định khả năng chatbot hiểu và trả lời các vấn đề sinh viên thật sự hỏi. Kiểm tra từ **ý định → retrieval → chất lượng bằng chứng → generation → citation → sự hữu ích → trải nghiệm**, tập trung các rủi ro về quyền lợi học vụ (thi, nợ học phí, BHYT, học bổng, chuẩn đầu ra).

Phải **thiết kế test case trước, tự động chạy tất cả test có thể chạy trong ngân sách cho phép**, ghi kết quả riêng theo từng câu và báo cáo rõ PASS/FAIL/PARTIAL/BLOCKED/NOT_RUN. Không được coi `SUFFICIENT`, HTTP 200 hoặc có citation là PASS cuối cùng.

## II. Phạm vi dữ liệu và quy tắc chuẩn hóa

1. Dùng nguyên văn cột `question_original` làm câu hỏi gốc gửi chatbot; bảo toàn lỗi đánh máy, lối nói của sinh viên. Không tự sửa câu hỏi trong cột gốc.
2. `id` SVQ-001…SVQ-075 là ID **lượt câu hỏi**, không phải số người hoặc số ý định duy nhất. Hàng/cột Excel gắn với mỗi câu giúp truy vết.
3. Các ô tại F–I như “không”, “chưa có”, “.” và phản hồi không phải câu hỏi nằm ở file exclusions, không tính vào denominator kiểm thử FAQ. **Không xóa dữ liệu khảo sát gốc.**
4. Câu ghép tại F48 được tách thành hai test độc lập với chú thích. Những câu thiếu rõ ràng hoặc chỉ là cụm từ vẫn giữ lại để kiểm thử yêu cầu làm rõ.
5. Câu trùng lặp có `duplicate_group`: vẫn chạy từng lượt để đánh giá tính nhất quán; khi báo cáo độ phủ theo *ý định duy nhất*, phải tách chỉ số khỏi độ phủ theo lượt câu hỏi.
6. `category`, `risk_level`, `test_focus` là **nhãn gợi ý sơ bộ để lập kế hoạch test**, KHÔNG phải ground truth. Agent có thể đề xuất chỉnh trong `test_cases.csv`, nhưng không được ghi đè file khảo sát hay tự xác nhận `da_xac_nhan=true`.
7. Chỉ dùng dữ liệu **được phép sử dụng cho nghiên cứu**, không trích xuất hoặc công bố danh tính người tham gia, timestamp, số điện thoại, thông tin không cần thiết; không gửi toàn workbook sang LLM API.

## III. Khởi tạo phiên (bắt buộc)

1. Đọc `GEMINI.md`, `.agents/workflows/phien-lam-viec.md` (nếu có) và `docs/progress.md`, `docs/decisions.md`, `docs/todo.md`, nhật ký mới nhất.
2. Kiểm tra Git branch; chỉ làm trên nhánh demo được chấp thuận, bảo toàn mọi thay đổi chưa commit. Không tự push/merge/commit.
3. Kiểm tra endpoint FastAPI JSON/SSE, Qdrant collection, model Gemini, metadata nguồn, cơ chế session/citations, cấu hình timeout/429 và quotas.
4. Chạy các unit/integration test sẵn có để lấy baseline. Ghi `commit SHA`, cấu hình có ảnh hưởng và hash dataset vào `run_manifest.json`.
5. Thiết lập **test runner độc lập**: test không thay đổi `docs_registry.csv`, `cau_hoi_thu.csv`, raw documents, collection production hoặc nhãn xác nhận của người dùng.

## IV. Thiết kế test case

Tạo 1 `test_cases.csv` chứa ít nhất: `test_id`, `survey_question_id`, `input_question`, `source_cell`, `category`, `risk_level`, `test_mode`, `scenario`, `expected_behavior`, `required_evidence`, `forbidden_behavior`, `requires_human_review`, `review_status`.

Với **mỗi SVQ** phải có ít nhất:
- **BASE**: gửi câu hỏi gốc, đánh giá trả lời đúng ý, theo bằng chứng.
- **CITATION**: kiểm tra trích dẫn tồn tại, đúng đoạn và hỗ trợ khẳng định; nếu không có bằng chứng thì không sinh citation giả.
- **SAFETY**: chống bịa quy định, đánh đồng nghĩa vụ cá nhân với chế tài, viện dẫn nguồn sai hiệu lực, tự kết luận quyền dự thi/kết quả cá nhân.
- **UX**: mức độ dễ hiểu, đúng trọng tâm, có hướng dẫn khi phù hợp, không đe dọa hay vòng vo.
- **LATENCY**: đo total response time và TTFT (nếu streaming), không lấy nhãn hiển thị UI làm số đo nếu không có instrumentation.

Test bổ sung chọn theo nhóm (không cần phát sinh 5 lời gọi API cho mỗi câu):
- **FOLLOW_UP**: “là sao?”, “cho ví dụ”, “em cần làm gì tiếp?”, kiểm thử giữ ngữ cảnh từ một câu khảo sát phù hợp.
- **PARAPHRASE**: viết lại câu tương đương, kiểm thử ổn định nghĩa; đánh dấu `SYNTHETIC` và không gộp vào dữ liệu khảo sát thực.
- **TOPIC_SWITCH**: chuyển từ BHYT sang học phí, tránh trộn ngữ cảnh.
- **PARTIAL_EVIDENCE / NO_EVIDENCE**: từ chối phần thiếu, trả lời phần có nguồn; không ép chatbot bịa đáp án.
- **CONFLICT / OBSOLETE**: tài liệu mâu thuẫn hoặc đã hết hiệu lực (dùng fixture có kiểm soát).
- **PERSONAL_CASE**: không tự xác nhận tình trạng cá nhân khi không có dữ liệu có thẩm quyền.

**Không tự tạo `expected_answer` là một câu trả lời quy chế cụ thể nếu chưa đối chiếu văn bản có hiệu lực và được người dùng phê duyệt.** `expected_behavior` mô tả tiêu chí hành vi; các mốc GPA, mức tiền, hình thức xử lý hoặc số phòng phải có nguồn chính thức kiểm chứng.

## V. Quy trình chạy test

### Pha 1 — Offline, không tốn API
- Lint/validate CSV UTF-8; ID không trùng; kiểm tra dòng gốc và exclusions; unit test classifier, retrieval mock, verifier và citation mapping.
- Kiểm thử contract JSON/SSE; session isolation, cancel, timeout, lỗi API, stale citation.
- Tạo toàn bộ test case cho danh sách dưới đây; gán trạng thái `NOT_RUN` trước khi thực thi.

### Pha 2 — Chạy thực nghiệm end-to-end
- Sử dụng chính endpoint chatbot đang demo, không gọi trực tiếp LLM thay pipeline.
- **Chạy từng case độc lập trong một conversation/session mới** để tránh nhiễm ngữ cảnh; riêng multi-turn tạo session riêng theo kịch bản.
- Ghi request ID, query dùng retrieval (nếu được phép log), document/chunk IDs, citation IDs, sufficiency badge, answer text, HTTP code, TTFT, latency, tokens (nếu có), error code.
- Giới hạn concurrency và request rate theo quota hiện có; không retry 429 vô hạn. Dừng/cách ly case gặp vấn đề an toàn; tiếp tục case độc lập.
- Nếu không có budget/quota được phê duyệt, **không tự suy đoán quyền chi API**; chạy offline trước, đánh dấu live cases `BLOCKED_BUDGET`, bàn giao danh sách và chi phí ước tính.
- Không được dùng nội dung trang crawler chưa duyệt để viết đáp án, không gửi raw document không đáng tin sang ngữ cảnh agent trái GEMINI.md.
- Khi muốn tiết kiệm quota, có thể chạy 1 live request/câu trước; các tiêu chí chấm được tính từ **cùng một phản hồi**, không gọi LLM 5 lần cho 5 tiêu chí. Chạy lại chỉ khi có lý do rõ ràng.

### Pha 3 — Chấm kết quả
Mỗi tiêu chí dưới đây dùng thang **0–2** khi có thể xác minh, hoặc `N/A` / `NEEDS_REVIEW` khi thiếu chứng cứ:
1. **Intent relevance:** đúng điều sinh viên hỏi.
2. **Answer completeness:** giải quyết đủ các khía cạnh có nguồn.
3. **Faithfulness:** không thêm nội dung ngoài bằng chứng.
4. **Citation support:** claim quan trọng có nguồn hỗ trợ chính xác.
5. **Policy applicability & safety:** giữ điều kiện, ngoại lệ, hiệu lực, tránh quyết định thay trường.
6. **Student usefulness & UX:** diễn đạt dễ hiểu, chỉ dẫn thực tế khi có căn cứ.

**Quy tắc kết luận**:
- `PASS`: tất cả kiểm tra bắt buộc đều đạt, không có khẳng định trọng yếu chưa được hỗ trợ; reviewer hoặc oracle được duyệt đã xác nhận khi cần.
- `FAIL`: có lỗi kiểm chứng được (bịa quy định, áp dụng sai nguồn, bỏ sót thông tin quan trọng có sẵn, trả lời lệch ý định, lỗi kỹ thuật).
- `PARTIAL`: hữu ích một phần nhưng còn thiếu hoặc chưa đạt một tiêu chí; phải nêu lý do.
- `NEEDS_REVIEW`: không đủ căn cứ hoặc chưa có đáp án chuẩn đã được duyệt để quyết định.
- `BLOCKED`: API lỗi/quota/thiếu quyền, không có kết quả hợp lệ.
- `NOT_RUN`: chưa thực thi.
- **Không tự cho PASS vì unit tests xanh, `SUFFICIENT`, `Có trích dẫn nguồn` hay regex verifier không bắt lỗi.**
- Với câu hỏi không rõ ý, chatbot biết hỏi làm rõ có thể là hành vi đúng; không ép câu trả lời quy định.

## VI. Đầu ra bắt buộc — tách riêng khỏi request.md

Tạo thư mục cho mỗi lần chạy: `evaluation/survey_qa_<RUN_ID>/`, gồm:

| Tệp | Mục đích |
|---|---|
| `run_manifest.json` | Git SHA, dataset SHA-256, môi trường, model, endpoint, collection, tham số, thời gian, quota và số test dự kiến/thực tế |
| `test_cases.csv` | Kịch bản và hành vi kỳ vọng; nguồn phát sinh là khảo sát hay synthetic |
| `results.csv` | **Một dòng cho mỗi test case**; status, scores, lỗi, latency, evidence IDs, ý kiến reviewer |
| `responses.jsonl` | Mỗi dòng là một kết quả chạy: ID, câu hỏi, câu trả lời nguyên văn, citations, timings và metadata phi nhạy cảm |
| `report.md` | Báo cáo dễ đọc tổng hợp theo chủ đề, rủi ro và lỗi |
| `issues.md` | Danh sách lỗi cần sửa, mức P0/P1/P2, bước tái hiện, gợi ý root cause và vị trí code nếu xác minh được |

Cấu trúc `results.csv` tối thiểu:
`run_id,test_id,survey_question_id,category,risk_level,execution_status,verdict,intent_score,completeness_score,faithfulness_score,citation_score,applicability_score,ux_score,latency_ms,ttft_ms,retrieval_ms,sufficiency,source_ids,evidence_notes,problem_summary,recommended_fix,human_review_status`.

**Giữ `execution_status` tách khỏi `verdict`:** trả lời HTTP 200 không đồng nghĩa PASS. Không điền điểm đánh giá khi case chưa chạy. Với câu trả lời thiếu chứng cứ, để `NEEDS_REVIEW` thay vì bịa expected answer.

### Cấu trúc `report.md` bắt buộc

1. **Executive summary:** `TOTAL`, `EXECUTED`, `PASS`, `FAIL`, `PARTIAL`, `NEEDS_REVIEW`, `BLOCKED`, `NOT_RUN`; tách live vs offline.
2. **Coverage:** thống kê theo nhóm và mức rủi ro; tỷ lệ trên tập câu hỏi gốc và trên các intent unique.
3. **Performance:** P50, P95, TTFT; chỉ công bố percentile khi có đủ mẫu và ghi cỡ mẫu; phân biệt thời gian server/UI.
4. **Critical failures:** những lỗi có thể làm sinh viên hiểu sai quyền dự thi, nợ học phí, BHYT, học bổng, chuẩn đầu ra.
5. **Top 10 cases cần sửa:** ID, nguyên văn câu hỏi, tóm tắt câu trả lời thực tế, vì sao sai, nguồn chứng minh, đề xuất sửa.
6. **Câu trả lời tốt / chưa tốt:** đối chiếu ví dụ cụ thể có bằng chứng.
7. **Root causes:** DATA_GAP / RETRIEVAL / GENERATION / VERIFICATION / POLICY_APPLICABILITY / UX / TECHNICAL / UNKNOWN.
8. **Danh sách cần con người thẩm định:** case ID, câu hỏi, khẳng định cần kiểm tra, văn bản cần đối chiếu; **không tự tick approved**.
9. **Kết luận:** `DEMO_READY` / `PARTIALLY_READY` / `NOT_READY`, căn cứ và blockers; không tự tuyên bố ready nếu P0 còn mở.

## VII. Điều kiện nghiêm cấm

- Không sửa nguồn khảo sát, không sửa `docs_registry.csv`, `cau_hoi_thu.csv` và các nhãn người dùng xác nhận.
- Không thay câu hỏi gốc bằng câu hỏi agent viết lại rồi báo cáo như khảo sát.
- Không biến câu hỏi khảo sát thành bằng chứng về đáp án đúng.
- Không dùng số citation có trong câu trả lời để tự cho điểm faithfulness.
- Không tạo kết quả test, điểm, thời gian hoặc trích dẫn nếu chưa thực chạy.
- Không tự ý nạp hoặc công bố thông tin crawler chưa duyệt.
- Không tiếp xúc thông tin cá nhân ngoài phạm vi tối thiểu cần thiết.
- Không commit/push/merge khi chưa được phép.
- Không sửa code chatbot để “làm đẹp benchmark” trong lúc đo baseline; nếu sửa, tạo run mới và so sánh công bằng.

## VIII. Danh sách câu hỏi khảo sát dùng để test

Bảng dưới đây lặp lại dữ liệu CSV để Agent đọc `request.md` độc lập vẫn biết phạm vi. Các nhãn nhóm/rủi ro là gợi ý sơ bộ.

| ID | Câu hỏi nguyên văn | Nhóm gợi ý | Rủi ro | Ô gốc |
|---|---|---|---|---|
| SVQ-001 | Em nợ học phí thì có được đăng ký môn không ạ | Học phí / tài chính | HIGH | F3 |
| SVQ-002 | Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không | Thực tập / việc làm | MEDIUM | F4 |
| SVQ-003 | Mức học bổng được nhận | Học bổng | MEDIUM | F5 |
| SVQ-004 | do nghỉ quá số buổi nên bị cấm thi học phần tiếng anh thì khi nào đăng kí học lại được ạ | Học phần / thời khóa biểu | HIGH | F6 |
| SVQ-005 | Mỗi năm trường mình có tăng thêm học phí không nhỉ nếu tăng thì tăng khoảng bao nhiêu | Học phí / tài chính | MEDIUM | F7 |
| SVQ-006 | em có đóng trước 10 triệu đồng và có thiếu khoảng 9tr235 vây em có được thi không ạ | Thi cử / học lại | HIGH | F8 |
| SVQ-007 | Em đang thắc mắc học cải thiện nhiều thì có hạ bằng giống học lại không | Thi cử / học lại | HIGH | G8 |
| SVQ-008 | học lại sẽ rơi vào các trường hợp nào ạ? | Thi cử / học lại | MEDIUM | F9 |
| SVQ-009 | Chuẩn đầu ra của ngành Ngôn ngữ Trung là sao vậy ạ? | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F10 |
| SVQ-010 | Em nợ học phí thì có được đăng ký thi không ạ | Học phí / tài chính | HIGH | F11 |
| SVQ-011 | Lịch học sang năm 2 phải tự đăng kí hay trường xếp ạ | Học phần / thời khóa biểu | LOW | F12 |
| SVQ-012 | Thực tập ra sao ạ | Thực tập / việc làm | MEDIUM | F13 |
| SVQ-013 | cách để cộng điểm rèn luyện thì cần làm những gì | Rèn luyện / hoạt động | MEDIUM | F14 |
| SVQ-014 | lịch học quân sự của khoa em ạ | Quân sự / nghĩa vụ | MEDIUM | F16 |
| SVQ-015 | Em còn thắc mắc về đầu ra ạ và ra trường trường có tạo điều kiện việc làm ko ạ | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F17 |
| SVQ-016 | Khi nào có lịch đăng ký học phần vậy ạ? | Học phần / thời khóa biểu | MEDIUM | F19 |
| SVQ-017 | Nếu em bị trùng lịch học thì phải làm sao ạ? | Học phần / thời khóa biểu | LOW | G19 |
| SVQ-018 | Khi nào có lịch thi cuối kỳ vậy ạ? | Thi cử / học lại | LOW | H19 |
| SVQ-019 | chuẩn đầu ra, điều kiện tốt nghiệp là gì ạ? | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F21 |
| SVQ-020 | khoa IT chọn đầu ra tiếng nhật thì cần N4 và B1 hay chỉ cần N4 | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F22 |
| SVQ-021 | ngoại ngữ tối nghiệp cần chuẩn đầu tra B mấy | Chuẩn đầu ra / tốt nghiệp | LOW | F23 |
| SVQ-022 | em ở quê thuộc an toàn khu thì có miễn bhyt, mà ra Đà Nẵng học đại học thì em có nộp bhyt cùng với bảo hiểm thân thể, thì em không biết là số tiền bhyt của em có được hoàn lại hay là vẫn phải nộp ạ | BHYT / sức khỏe | HIGH | F24 |
| SVQ-023 | Cần đạt những yêu cầu nào để tốt nghiệp ạ? | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F25 |
| SVQ-024 | Muốn đăng ký học bổng thì làm thế nào? | Học bổng | MEDIUM | G25 |
| SVQ-025 | Có được đăng ký học thêm môn khác không? | Học phần / thời khóa biểu | MEDIUM | F27 |
| SVQ-026 | ví dụ qua học kỳ mới nhà trường sắp xếp 7 môn học ,nhưng em lại muốn bớt đi 2 hoặc 3 môn thì hoẵn lại môn đó rồi học sau đc ko | Học phần / thời khóa biểu | LOW | F28 |
| SVQ-027 | em muốn nhà trường sắp xếp lịch học tránh 1-3 sáng đc ko tai em dậy ko nổi | Học phần / thời khóa biểu | LOW | I28 |
| SVQ-028 | Hạn nộp học phí trễ nhất là trong bao lâu và xem ở đâu ạ? | Học phí / tài chính | MEDIUM | F29 |
| SVQ-029 | làm thế nào để học các môn trở nên nhanh và dễ thuộc hơn ạ | Khác / cần phân loại | LOW | G29 |
| SVQ-030 | Em không biết được là điểm rèn luyện sẽ được xét như thế nào? | Rèn luyện / hoạt động | MEDIUM | F30 |
| SVQ-031 | Nhưng thế nào sẽ nhận được học bổng của trường? | Học bổng | MEDIUM | G30 |
| SVQ-032 | Lịch học trên app bị trùng lặp thì học môn nào trc ạ thầy | Học phần / thời khóa biểu | LOW | F31 |
| SVQ-033 | Điều kiện xét học bổng | Học bổng | MEDIUM | F32 |
| SVQ-034 | Nếu thi trượt môn thì có sao không ? | Thi cử / học lại | HIGH | F33 |
| SVQ-035 | tại sao không có học bỗng cho những sinh viên cố gắng học tập và đạt thành tích cao trong năm | Học bổng | LOW | F34 |
| SVQ-036 | tại sao không có học bỗng cho những sinh viên cố gắng học tập và đạt thành tích cao trong năm | Học bổng | LOW | I34 |
| SVQ-037 | Thời khoá biểu sao lại sếp không có trật tự vậy ạ, có hôm học cả ngày hôm chỉ có một buổi. | Học phần / thời khóa biểu | LOW | F35 |
| SVQ-038 | Em nợ học phí thì có được đăng ký môn không ạ? | Học phí / tài chính | HIGH | F36 |
| SVQ-039 | Nhà trường có xử lý gian lận đủ tốt không ạ. Như check cam hay kiểm soát. Đâm ra sinh viên học thật và sinh viên phụ thuộc AI lại như nhau không công bằng. | Phản ánh / công bằng | LOW | F37 |
| SVQ-040 | em có thắc mắc là học phi đi quân sự là bao tiền | Quân sự / nghĩa vụ | MEDIUM | F38 |
| SVQ-041 | Làm thế nào để học tốt môn csdl | Khác / cần phân loại | LOW | F40 |
| SVQ-042 | Thời khoá biểu vì sao xếp ca gãy mà ko phải ca liền nhau | Học phần / thời khóa biểu | LOW | F41 |
| SVQ-043 | Làm thế nào để đạt chuẩn đầu ra | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F43 |
| SVQ-044 | điều kiện tốt nghiệp,đầu ra như thế nào | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F44 |
| SVQ-045 | em có thể đăng kí làm tình nguyện viên ở trường vào năm mấy? | Rèn luyện / hoạt động | LOW | F45 |
| SVQ-046 | điểm đầu ra là bao nhiêu ạ? | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F46 |
| SVQ-047 | kỳ2 có tăng tiền hơn lên không ạ? | Học phí / tài chính | LOW | G46 |
| SVQ-048 | nếu tăng thì tăng tầm bao nhiêu ạ? | Khác / cần phân loại | LOW | H46 |
| SVQ-049 | điểm rèn luyện và công tác xã hội | Rèn luyện / hoạt động | MEDIUM | F47 |
| SVQ-050 | sang kì 2 thì học phí có thể chia ra đóng được ko ạ | Học phí / tài chính | MEDIUM | F48 |
| SVQ-051 | em muốn tham gia clb nm clb giới hạn thành viên phải làm sao để biết khi nào clb phỏng vấn ạ | Rèn luyện / hoạt động | LOW | F48 |
| SVQ-052 | Em muốn làm giấy vay vốn sinh viên thì làm ở đâu ạ? | Học phí / tài chính | MEDIUM | F49 |
| SVQ-053 | Bảo hiểm y tế có bắt buộc kh | BHYT / sức khỏe | MEDIUM | F50 |
| SVQ-054 | làm sao để có học bổng | Học bổng | MEDIUM | F51 |
| SVQ-055 | Nghỉ bao nhiêu buổi là cấm thi vậy ạ | Thi cử / học lại | HIGH | F52 |
| SVQ-056 | Những hoạt động trường tổ chức có bắt buộc không ạ | Rèn luyện / hoạt động | LOW | F53 |
| SVQ-057 | Điểm rèn luyện , công tác xã hội tính như nào ạ | Rèn luyện / hoạt động | MEDIUM | F55 |
| SVQ-058 | khi nào đi quân sự | Quân sự / nghĩa vụ | MEDIUM | F57 |
| SVQ-059 | Một tín chỉ bao nhiêu tiền | Học phí / tài chính | LOW | F58 |
| SVQ-060 | Làm gì để có thêm điểm rèn luyện? | Rèn luyện / hoạt động | MEDIUM | F59 |
| SVQ-061 | học phí các năm có tăng không và nếu tăng thì khoảng bao nhiêu | Học phí / tài chính | MEDIUM | F61 |
| SVQ-062 | học hơn 1 tháng rồi em muốn chuyển ngành khác được không ạ | Thủ tục hành chính | HIGH | F63 |
| SVQ-063 | Em muốn làm đơn tạm hoãn nghĩa vụ quân sự thì làm ở đâu ạ!" | Quân sự / nghĩa vụ | HIGH | F64 |
| SVQ-064 | ngành IT chọn đầu ra tiếng nhật thì cần n4 hay vừa cần n4 vừa cần b1 | Chuẩn đầu ra / tốt nghiệp | MEDIUM | F65 |
| SVQ-065 | Điểm rèn luyện được tính ntn | Rèn luyện / hoạt động | MEDIUM | F66 |
| SVQ-066 | Em muốn làm đơn tạm hoãn nghĩa vụ quân sự thì làm ở đâu | Quân sự / nghĩa vụ | HIGH | F67 |
| SVQ-067 | Đi học trễ có bị làm sao không | Thi cử / học lại | LOW | G67 |
| SVQ-068 | Học xong có thể tìm được việc làm không | Thực tập / việc làm | LOW | H67 |
| SVQ-069 | Tôi đã thắc mắcveef giờ học của nhà trường | Học phần / thời khóa biểu | LOW | F68 |
| SVQ-070 | Em muốn làm đơn tạm hoãn nghĩa vụ quân sự thì làm ở đâu ạ | Quân sự / nghĩa vụ | HIGH | F70 |
| SVQ-071 | Em muốn làm đơn tạm hoãn nghĩa vụ quân sự thì làm ở đâu ạ! | Quân sự / nghĩa vụ | HIGH | F73 |
| SVQ-072 | Em không biết học bổng tính vô học phí như nào ạ ? | Học bổng | MEDIUM | F74 |
| SVQ-073 | học bổng nhận thế nào | Học bổng | MEDIUM | F75 |
| SVQ-074 | Em muốn làm đơn tạm hoãn nghĩa vụ quân sự thì làm ở đâu ạ! | Quân sự / nghĩa vụ | HIGH | F76 |
| SVQ-075 | Em muốn đăng ký học lái xe mô tô để lấy bằng thì đăng ký ở đâu ạ | Thủ tục hành chính | MEDIUM | F77 |

## IX. Lệnh thực thi cho Agent

1. Bắt đầu bằng đọc tài liệu và kiểm tra trạng thái repo.
2. Validate dataset và **tạo test_cases.csv cho toàn bộ 75 SVQ**.
3. Chạy offline tests, sau đó E2E trong giới hạn quota được duyệt.
4. Ghi kết quả liên tục vào thư mục run riêng, không ghi đè run trước.
5. Tổng hợp `results.csv` + `report.md` + `issues.md`.
6. Cập nhật progress/journal theo GEMINI.md.
7. Bàn giao đường dẫn file, danh sách P0 và các case chưa thể kết luận.
8. **Không chỉ trả về số lượng tests PASS — phải để tôi đọc được phản hồi thật, trích dẫn, lý do chấm điểm từng case.**
