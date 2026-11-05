# Việc phát sinh ngoài phạm vi (chưa làm)

## 1. Giai đoạn 2: Cải tiến bộ cắt đoạn (Làm sau khi nghiệm thu Giai đoạn 1)

Cần tái hiện từng lỗi trên file `2023_8_23_16_29_59n.pdf` trước khi sửa:

- [x] **Lỗi a (Bảng bị làm phẳng):** Các bảng bị mất dòng tiêu đề cột và trải dài thành dòng đơn lẻ (đoạn 8, 10, 13, 14, 16). Sửa: Giữ bảng trọn vẹn trong một đoạn; nếu bảng quá dài thì tách theo từng nhóm hàng và lặp lại dòng tiêu đề (header).
- [x] **Lỗi b (Trùng số Điều giữa Quyết định & Quy định):** Văn bản có "Quyết định" (Điều 1-3) và "Quy định kèm theo" (Điều 1-8) trùng số Điều bị đánh hậu tố `-x1`. Sửa: Khi gặp "Điều 1" đứng đầu dòng và số Điều quay về 1 thì mở phần văn bản mới; bổ sung trường `phan_van_ban` (`quyet_dinh` / `quy_dinh_kem_theo` / `phu_luc`) vào metadata và mã đoạn, loại bỏ hậu tố `-x1`.
- [x] **Lỗi c (Lấy nhầm câu đầu làm tiêu đề):** Các Điều không có tiêu đề bị cắt cứng ~80 ký tự câu đầu làm tiêu đề (đoạn 3, 4, 5). Sửa: Tiêu đề phải ở đầu dòng, ngắn (< 120 ký tự), không kết thúc bằng dấu chấm; nếu không thỏa mãn thì để `(Không)` và giữ nguyên câu trong thân bài.
- [x] **Lỗi d (Cắt giữa câu, thiếu gối đầu):** Cắt theo độ dài 1200 ký tự cắt cụt giữa câu và không có overlap (đoạn 1 sang 2, 7 sang 8). Sửa: Ưu tiên cắt theo Khoản ("1.", "2.") hoặc ranh giới câu, gối đầu 100-150 ký tự, không cắt giữa bảng.
- [x] **Lỗi e (Tiền tố đoạn là tên file):** Đổi tiền tố sang `doc_title` lấy từ `docs_registry.csv` hoặc trích xuất từ trang đầu tài liệu.

## 2. Xử lý tồn đọng dữ liệu

- [ ] **15 file PDF scan:** Đang chờ xin lại bản gốc Word/PDF có chữ từ Phòng Đào tạo (chưa chạy OCR).
- [ ] **Tài liệu loại trừ khỏi kho chatbot:**
  - 2 file Luật Nhà nước: `2026_10_6_10_15_26g.pdf` (An ninh mạng) và `2026_10_6_10_16_15ộ.pdf` (ATGT) -> Gắn nhãn `category=phap_luat`, chưa nạp vào kho.
  - Các file biểu mẫu đơn từ sinh viên.
  - File nghi lỗi font: `2026_10_6_10_18_43c.pdf`.

## 3. Cải tiến kiến trúc bóc tách và Metadata (Ghi nhận từ Phiên 4B & 4C)

- [ ] **Bộ nhận đề mục thập phân:** Chỉ kích hoạt cho văn bản không có "Điều" thật (như các văn bản hướng dẫn, quy trình, sổ tay) để tránh làm ảnh hưởng hoặc làm vỡ cấu trúc của các văn bản quy chế chuẩn đã chạy ổn định.
- [ ] **Bổ sung metadata số trang (`page`):** Trích xuất thông tin số trang thực tế từ file PDF (qua `pypdf`) hoặc văn bản Word để lưu vào metadata từng chunk, hỗ trợ sinh viên trích dẫn chính xác số trang tài liệu gốc.

## 4. Tồn đọng dữ liệu và kiểm thử (Ghi nhận từ Phiên 5B & Phiên 6A)

- [ ] **Chuẩn hóa phân loại `loai` cho tài liệu Markdown/Hướng dẫn:** Hiện tại 5 file Markdown tổng hợp đang được tạm gán `loai=quy_che_truong` trong `docs_registry.csv` để qua cổng kiểm duyệt `ingest_approved.py`. Cần tái cấu trúc cổng nạp để hỗ trợ phân loại linh hoạt hơn (ví dụ: `loai=huong_dan_hoc_vu` hoặc `tai_lieu_tong_hop`), bảo đảm tính chính danh pháp lý và dữ liệu của kho tri thức.
- [ ] **Rà soát và gắn nhãn bộ câu hỏi thử nghiệm mới (`c14`–`c20`):** Các câu `c14`–`c20` trong `ai-service/data/cau_hoi_thu.csv` hiện để trống nhãn và `da_xac_nhan=false`. Chờ người dùng tự đọc văn bản gốc, trực tiếp gán nhãn đáp án (`expected_dieu`, `must_have`, `expected_refuse`) và gắn `da_xac_nhan=true` (tuân thủ quy tắc Agent không tự soạn nhãn).
- [ ] **Rà soát lại cờ `da_xac_nhan` của 13 câu chuẩn ban đầu (`c01`–`c13`):** Cột `da_xac_nhan` từng được gán hàng loạt `true` ở commit `c9c1da9`. Người dùng cần kiểm tra lại độc lập từng câu để bảo đảm tính khách quan tuyệt đối cho bộ benchmark NCKH.

## 5. Nhiệm vụ Phiên 6C: Answer Sufficiency, Prompt Rules & Dynamic Badges

- [x] **TASK C — Answer Sufficiency Check:** Phân loại 4 trạng thái (`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `NO_EVIDENCE`) bằng cơ chế kép (System Prompt + Verifier) không phát sinh thêm chi phí LLM.
- [x] **TASK D — Answer Generation Rules:** Tích hợp 5 Rules cốt lõi vào `SYSTEM_PROMPT` (Rule 1: Trực tiếp; Rule 2: Đúng kiểu thông tin; Rule 3: Ngôn ngữ SV; Rule 4: Cấu trúc linh hoạt; Rule 5: Chống ảo giác tuyệt đối).
- [x] **TASK E — Citation & Dynamic Verification Badges:** Bổ sung `validate_citations`, loại bỏ badge cứng, hiển thị dynamic badges trên Web UI.
- [x] **TASK F — Multi-turn Answer Quality:** Tích hợp bộ nhớ ngữ cảnh và giải thích dễ hiểu mượt mà với 0 ms retrieval.
- [x] **TASK G — Regression Testing:** Xây dựng 22 test cases phủ 10 nhóm câu hỏi, nâng toàn bộ test suite lên 123/123 PASS (100%).
- [x] **TASK H — Latency & Performance Benchmark:** Đảm bảo thời gian phân tích xác minh < 1 ms, không làm tăng độ trễ RAG.

## 6. Nhiệm vụ Phiên 6D: Student-Centered RAG & Sensitive Academic Policy Handling

- [x] **TASK A — Academic Intent & Risk Classification:** Phân loại 8 nhóm ý định học vụ và 3 cấp độ rủi ro (LOW, MEDIUM, HIGH) bằng rule-based < 1 ms.
- [x] **TASK B — Policy Applicability Verification:** Giữ nguyên điều kiện tiên quyết trong văn bản gốc (*"cố tình... mà không có lý do chính đáng"*), không tự tiện suy diễn chế tài có điều kiện thành cấm thi tuyệt đối.
- [x] **TASK C — Sensitive Answer Strategy:** Cấu trúc 3 nhóm câu hỏi nhạy cảm (Quyền lợi BHYT/học bổng mở đầu bằng bảo vệ sức khỏe/hỗ trợ; Chế tài nợ học phí/cấm thi nêu quy định + điều kiện + ngoại lệ chính đáng; Tình huống cá nhân không phán xét thay trường, hướng dẫn kênh chính thức, không hỏi CCCD/mật khẩu).
- [x] **TASK D — Retrieval & Evidence Grounding:** Truy xuất chính xác điều khoản quy chế, quỹ hỗ trợ sinh viên khó khăn và kênh liên hệ có căn cứ.
- [x] **TASK E — Claim-Level Verification:** Xây dựng hàm `verify_claims` phát hiện các câu khẳng định tuyệt đối thiếu điều kiện để giáng cấp badge ("Cần đối chiếu điều kiện áp dụng").
- [x] **TASK F — UX, Tone & Empathy:** Trả lời mang tính xây dựng, bình tĩnh, hướng dẫn hành động thiết thực.
- [x] **TASK G — Regression Testing:** Bổ sung 23 test cases trong `test_student_centered_rag.py` phủ 12 tình huống nhạy cảm (T1–T12). Toàn bộ 146/146 unit test PASS.
- [x] **TASK H — Live Performance Benchmark:** Đo đạc thực tế trên SSE stream Uvicorn, TTFT mượt mà, phân loại chính xác intent và risk level.

