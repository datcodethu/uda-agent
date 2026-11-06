# Nhật ký 2026-11-05 – Phiên 6I: Manual Acceptance Testing & System Verification

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)

Chuẩn bị toàn diện hệ thống, kiểm toán độc lập bản ghi Phiên 6H, thiết kế 10 kịch bản kiểm thử kèm bảng checklist để Người phụ trách (User) có thể trực tiếp nghiệm thu thủ công tính năng nạp URL và Chatbot RAG mà không phụ thuộc vào kết quả tự động của Agent.

---

## 2. Đã làm gì

| File | Thay đổi |
|---|---|
| `evaluation/manual_acceptance_6i/audit_phien_6h_approval.md` | Báo cáo kiểm toán độc lập về bản ghi `URL-20261105-2B329B`, giải trình rõ nguyên nhân chuyển `INDEXED` là do Agent chạy thử nghiệm kỹ thuật và khẳng định thao tác này không thay thế thẩm quyền phê duyệt của con người. |
| `evaluation/manual_acceptance_6i/system_verification_report.md` | Báo cáo xác minh toàn diện hạ tầng: Git branch `demo/school-presentation-2026`, Qdrant Local 105 chunks (11 tài liệu), BM25 đồng bộ, cổng mạng 8000 sẵn sàng. |
| `evaluation/manual_acceptance_6i/manual_test_scenarios.md` | Tài liệu hướng dẫn 10 kịch bản kiểm thử thủ công chi tiết từng bước (lệnh CLI, câu hỏi Web Chat, kết quả mong đợi, điểm lưu ý). |
| `evaluation/manual_acceptance_6i/manual_acceptance_checklist.md` | Bảng checklist đánh dấu PASS/FAIL/BLOCKED kèm cột ghi chú thực tế cho Người nghiệm thu. |
| `evaluation/manual_acceptance_6i/limitations_and_unimplemented.md` | Báo cáo các hạn chế tồn đọng: chưa có Web UI nạp URL, 6 file DOCX chờ duyệt, giới hạn web SPA JavaScript. |
| `docs/progress.md` | Cập nhật tiến độ Phiên 6I (Sẵn sàng nghiệm thu). |
| `docs/todo.md` | Cập nhật danh mục công việc Phiên 6I và đề xuất kế hoạch Phiên 6J. |

---

## 3. Vì sao làm như vậy

### Khối 1: Kiểm toán và làm rõ nguồn gốc phê duyệt bản ghi Phiên 6H
- **Quyết định:** Viết báo cáo giải trình minh bạch rằng trạng thái `INDEXED` của `URL-20261105-2B329B` là do Agent tự chạy lệnh CLI kiểm thử tích hợp nội bộ trong Phiên 6H, không phải là sự phê duyệt chính thức của con người.
- **Phương án đã cân nhắc:** Coi như bản ghi đã được duyệt hợp lệ và bỏ qua.
- **Vì sao chọn:** Tuân thủ nguyên tắc quản trị tri thức NCKH và đạo đức AI: Agent không bao giờ được phép tự cấp quyền hoặc mạo danh con người để đưa dữ liệu vào kho chính thức.
- **Vì sao loại phương án còn lại:** Sẽ tạo ra tiền lệ xấu về việc AI tự tung tự tác sửa đổi cơ sở tri thức mà người quản trị không kiểm soát được.
- **Loại căn cứ:** [tài liệu: GEMINI.md, nguyên tắc Default-Deny & Approval Gate].
- **Đánh đổi:** Cần thêm tài liệu giải trình và phương án xử lý gỡ bỏ nếu người dùng yêu cầu.

### Khối 2: Thiết kế 10 kịch bản bao phủ từ an toàn mạng đến trải nghiệm sinh viên
- **Quyết định:** Chia 10 kịch bản thành 2 nhóm: Nhóm 1 kiểm tra CLI/Bảo mật (T1–T6: allowlist, SSRF, cổng cá nhân, deduplication, dry-run) và Nhóm 2 kiểm tra Web Chatbot/RAG (T7–T10: truy xuất nguồn web, đa lượt tiếp nối, câu hỏi thiếu bằng chứng, chính sách nhạy cảm).
- **Phương án đã cân nhắc:** Chỉ đưa ra vài câu hỏi chat thông thường.
- **Vì sao chọn:** Một hệ thống RAG phục vụ môi trường giáo dục không chỉ cần trả lời hay mà phải có "hàng rào an toàn" vững chắc trước các cuộc tấn công mạng và nguy cơ rò rỉ dữ liệu sinh viên.
- **Vì sao loại phương án còn lại:** Chỉ kiểm tra bề nổi sẽ bỏ sót các lỗ hổng SSRF hoặc lỗi rò rỉ dữ liệu cá nhân.
- **Loại căn cứ:** [kỹ thuật: Tiêu chuẩn OWASP Top 10 & Quy chế bảo vệ dữ liệu cá nhân].
- **Đánh đổi:** Người nghiệm thu cần dành khoảng 10–15 phút để chạy thử cả lệnh terminal và giao diện chat.

### Khối 3: Thừa nhận trung thực các hạn chế chưa hoàn thành
- **Quyết định:** Lập văn bản riêng `limitations_and_unimplemented.md` nêu rõ các điểm yếu: chưa có Web UI nạp link, 6 file DOCX chưa nạp, không cào được web SPA thuần JS.
- **Phương án đã cân nhắc:** Tuyên bố hệ thống đã hoàn toàn sẵn sàng bàn giao (DEMO READY).
- **Vì sao chọn:** Sự trung thực trong NCKH là tối thượng. Tuyên bố hoàn hảo khi còn hạn chế sẽ khiến nhóm nghiên cứu gặp sự cố bất ngờ khi demo trước hội đồng.
- **Vì sao loại phương án còn lại:** Tuyên bố sai sự thật vi phạm nguyên tắc cốt lõi của GEMINI.md ("Không bịa kết quả").
- **Loại căn cứ:** [tài liệu: GEMINI.md mục 3].
- **Đánh đổi:** Có thể khiến hệ thống trông chưa hoàn hảo 100%, nhưng mang lại độ tin cậy và lộ trình nâng cấp rõ ràng.

---

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

### 1. Manual Acceptance Testing (Nghiệm thu thủ công) là gì?
- **Ví dụ đời thường:** Giống như khi bạn mua một chiếc xe máy mới. Mặc dù nhà máy đã chạy thử nghiệm tự động bằng máy móc (Unit test), bạn vẫn phải tự mình ngồi lên xe, đề máy, bóp phanh, bật đèn xi-nhan và chạy thử một vòng xem cảm giác lái thực tế có êm ái và an toàn như cam kết hay không.
- **Trong hệ thống:** Mặc dù máy tính đã chạy 159 bài unit test tự động và đều báo "PASS", người phụ trách vẫn cần tự tay gõ lệnh nạp link và tự tay hỏi chatbot các câu hỏi hóc búa để cảm nhận trực tiếp xem câu trả lời có tự nhiên, chính xác và có trích dẫn đúng nguồn hay không.

### 2. Lock Contention (Tranh chấp khóa tệp) là gì?
- **Ví dụ đời thường:** Giống như một cuốn sổ nhật ký chỉ có một chiếc bút duy nhất đặt cạnh. Nếu bạn đang cầm bút viết dở một trang nhật ký (Uvicorn đang đọc/ghi Qdrant), người khác chạy vào giật chiếc bút để ghi thêm một dòng (lệnh ingest chạy song song), cả hai người sẽ bị va vào nhau và không ai viết được gì (xảy ra lỗi khóa).
- **Trong hệ thống:** Vì hệ thống đang dùng Qdrant Local và file JSONL lưu trên ổ đĩa nội bộ, nếu chạy đồng thời nhiều tiến trình nặng cùng ghi vào một file, hệ điều hành Windows sẽ khóa file đó lại. Vì vậy, ta nên chạy nạp dữ liệu tuần tự khi server đang rảnh.

---

## 5. Đã kiểm tra thế nào

- **Kiểm tra trạng thái cổng mạng 8000:**
  * Lệnh: `Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue`
  * Kết quả: Cổng 8000 hoàn toàn rảnh rỗi, không bị tiến trình nào chiếm dụng.
- **Kiểm tra kho vector Qdrant Local:**
  * Lệnh: Kiểm tra trực tiếp qua `load_all()` và `list_documents()`.
  * Kết quả: Tổng cộng 105 chunks, 11 documents (10 tài liệu cốt lõi = 103 chunks, 1 tài liệu web = 2 chunks).
- **Kiểm tra trạng thái Git:**
  * Lệnh: `git status`
  * Kết quả: Nhánh `demo/school-presentation-2026`, working tree sạch sẽ đối với các file mã nguồn chính.
- **Số lệnh gọi API trả phí đã dùng:** 0 lệnh (hoàn toàn kiểm tra cấu hình và tài liệu ngoại tuyến).

---

## 6. Chưa chắc chắn, rủi ro, giả định

- **Giả định về kết nối mạng khi Người dùng test:** Giả định máy của bạn có kết nối Internet bình thường để kiểm tra lệnh nạp URL từ `donga.edu.vn`. Nếu mạng bị ngắt, lệnh import URL sẽ báo lỗi mạng (nhưng các kịch bản test SSRF, Allowlist, và Web Chatbot nội bộ vẫn chạy 100% bình thường).
- **Trình duyệt khuyến nghị:** Khuyến nghị dùng Google Chrome, Microsoft Edge hoặc Firefox trên máy tính để giao diện Web Chatbot hiển thị tối ưu nhất.

---

## 7. Điều đã không làm và lý do

- **Không tự ý chạy Uvicorn trong background:** Để bạn có toàn quyền mở cửa sổ terminal riêng, trực tiếp quan sát các dòng log in ra theo thời gian thực khi chatbot phản hồi.
- **Không tự ý sửa trạng thái bản ghi Phiên 6H:** Giữ nguyên dữ liệu để bạn tự thẩm định và quyết định phê duyệt hoặc hoàn nguyên.
- **Không tự ý commit/push mã nguồn:** Người dùng tự thực hiện theo quy tắc an toàn.

---

## 8. Việc tiếp theo

1. Bàn giao hệ thống cho Người phụ trách bắt đầu kiểm thử theo tài liệu [`manual_test_scenarios.md`](file:///E:/workspace/donga-rag-system/evaluation/manual_acceptance_6i/manual_test_scenarios.md).
2. Người phụ trách ghi nhận kết quả vào [`manual_acceptance_checklist.md`](file:///E:/workspace/donga-rag-system/evaluation/manual_acceptance_6i/manual_acceptance_checklist.md).
3. Sau khi nghiệm thu xong, chuyển sang Phiên 6J để phát triển Web UI quản trị URL và nạp 6 tài liệu DOCX học vụ.

---

## 9. Câu hỏi cho người dùng

1. Khi bạn bắt đầu test, bạn có cần hỗ trợ giữ nguyên server chạy nền hay bạn muốn tự tay mở terminal gõ lệnh chạy Uvicorn để theo dõi log?
2. Sau khi nghiệm thu câu T7 và T8, bạn có muốn giữ lại trang web Giới thiệu trường (`web_2b329b97c1`) trong kho chính thức không?

---

## 10. Ba câu tự kiểm tra hiểu bài

1. Vì sao việc Agent tự chạy lệnh `approve` trong Phiên 6H không được coi là sự phê duyệt hợp lệ?
2. Kịch bản T4 kiểm tra điều gì và tại sao nó lại quan trọng đối với an toàn thông tin của máy chủ?
3. Tại sao hệ thống chưa thể tuyên bố "Demo Ready" hoàn toàn cho người dùng cuối dù các bài unit test đều đạt 100%?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì theo nguyên tắc phân quyền và đạo đức AI trong NCKH, quyền phê duyệt tri thức đưa vào kho chính thức là đặc quyền thuộc về con người (Chủ nhiệm đề tài / Nhà trường); mọi hành vi của Agent chỉ là kiểm thử kỹ thuật nội bộ, không có tư cách pháp lý đại diện cho người dùng.
2. Kịch bản T4 kiểm tra khả năng phòng chống tấn công SSRF (Server-Side Request Forgery). Nó cực kỳ quan trọng vì nếu không có chốt chặn này, kẻ xấu có thể lợi dụng chatbot để dò quét các thiết bị mạng nội bộ của trường hoặc đánh cắp thông tin bí mật từ dịch vụ cloud.
3. Vì hệ thống vẫn còn các hạn chế tồn đọng: quản trị viên chưa có giao diện web để dán link và duyệt trực quan (phải dùng dòng lệnh CLI), và 6 tài liệu học vụ quan trọng về biểu mẫu sinh viên vẫn đang ở hàng đợi chưa nạp.

</details>
