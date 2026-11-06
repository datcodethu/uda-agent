# Báo cáo Vấn đề Tồn đọng & Phân tích Chi tiết (Issues & Gap Analysis)
## Đợt Tái thiết Kho Tri thức v2 (`donga_kb_v2`)

**Ngày lập:** 05/11/2026  
**Thư mục lưu trữ:** `evaluation/kb_rebuild_v2/`

---

### 1. Phân tích 15 Trường hợp Đạt một phần (PARTIAL - 20.0%)

Tất cả 15 trường hợp PARTIAL trong đợt đánh giá đều đạt **9/12 điểm**. 
Đây là các trường hợp hệ thống phản hồi theo cơ chế **Từ chối an toàn có căn cứ (Safe Informative Refusal)**: hệ thống xác nhận tài liệu hiện hành chưa có số liệu cá nhân hoặc quy định cụ thể, không bịa đặt thông tin và hướng dẫn đúng phòng ban đầu mối.

| Test ID | Câu hỏi của sinh viên | Trạng thái bằng chứng | Phản hồi của Chatbot & Lý do là PARTIAL |
| :--- | :--- | :---: | :--- |
| **TC-SVQ-001** | Em nợ học phí thì có được đăng ký môn không ạ | `NO_EVIDENCE` | Nêu rõ tài liệu nộp học phí chưa có điều khoản cấm đăng ký môn, hướng dẫn liên hệ P. Kế toán/Đào tạo. |
| **TC-SVQ-002** | Sinh viên khoa ngôn ngữ trung chuyên ngành tiếng trung thương mại có cần đi thực tập không | `NO_EVIDENCE` | Xác nhận tài liệu hiện có là quy chế chung, chưa có chương trình khung cụ thể của ngành Ngôn ngữ Trung. |
| **TC-SVQ-010** | Em nợ học phí thì có được đăng ký thi không ạ | `NO_EVIDENCE` | Trả lời trung thực tài liệu chưa ghi nhận chế tài cấm thi do nợ học phí, khuyến nghị tra cứu cổng cá nhân. |
| **TC-SVQ-013** | Cách để cộng điểm rèn luyện thì cần làm những gì | `NO_EVIDENCE` | Thiếu văn bản "Quy chế đánh giá rèn luyện sinh viên" (hiện đang nằm trong hàng đợi văn bản Word DOCX). |
| **TC-SVQ-017** | Nếu em bị trùng lịch học thì phải làm sao ạ? | `NO_EVIDENCE` | Thiếu quy trình hủy/đổi lớp học phần khi trùng lịch (thuộc nghiệp vụ phần mềm Đăng ký tín chỉ trực tuyến). |
| **TC-SVQ-029** | Làm thế nào để học các môn trở nên nhanh và dễ hiểu | `NO_EVIDENCE` | Câu hỏi mang tính tư vấn phương pháp học tập cá nhân, ngoài phạm vi các văn bản quy chế hành chính. |
| **TC-SVQ-038** | Em nợ học phí thì có được đăng ký môn không ạ | `INSUFFICIENT` | Tương tự TC-SVQ-001, cung cấp số điện thoại Phòng Kế toán xử lý công nợ. |
| **TC-SVQ-041** | Làm thế nào để học tốt môn csdl | `INSUFFICIENT` | Câu hỏi hỏi mẹo học môn Cơ sở dữ liệu (ngoài phạm vi quy chế chung). |
| **TC-SVQ-045** | Em có thể đăng kí làm tình nguyện viên ở trường bằng cách nào | `NO_EVIDENCE` | Thiếu thông báo tuyển Cộng tác viên của Đoàn TN - Hội SV trường (thường thay đổi theo từng sự kiện/học kỳ). |
| **TC-SVQ-048** | Nếu tăng thì tăng tầm bao nhiêu ạ? (học phí) | `INSUFFICIENT` | Tài liệu không có biên độ tăng học phí cụ thể cho từng năm học. |
| **TC-SVQ-051** | Em muốn tham gia clb nm clb giới hạn thành viên thì có cách nào vào không | `INSUFFICIENT` | Quy định tuyển thành viên phụ thuộc Ban chủ nhiệm từng CLB, không có trong quy chế cấp trường. |
| **TC-SVQ-058** | Khi nào đi quân sự | `NO_EVIDENCE` | Lịch học Giáo dục Quốc phòng thay đổi theo từng khóa và thông báo của Trung tâm GDQP. |
| **TC-SVQ-059** | Một tín chỉ bao nhiêu tiền | `INSUFFICIENT` | Bảng đơn giá học phí theo ngành nằm trong các quyết định thu học phí chi tiết (chưa được nạp công khai trên web). |
| **TC-SVQ-065** | Điểm rèn luyện được tính ntn | `INSUFFICIENT` | Tương tự TC-SVQ-013, thiếu barem chấm điểm rèn luyện chi tiết 100 điểm. |
| **TC-SVQ-075** | Em muốn đăng ký học lái xe mô tô để lấy bằng A1 thì trường có tổ chức không | `NO_EVIDENCE` | Trường không có văn bản đào tạo sát hạch lái xe mô tô A1 trong danh mục quy chế. |

---

### 2. Phân tích 2 Trường hợp Không đạt (FAIL - 2.7%)

Cả 2 trường hợp này đều có câu trả lời chính xác, trích dẫn chuẩn và đủ ý, nhưng bị đánh rớt (FAIL) do **bộ kiểm tra tự động phát hiện số liệu nhạy cảm (sensitive numbers check)**:

1. **`TC-SVQ-015`:** "Em còn thắc mắc về đầu ra ạ và ra trường trường có tạo điều kiện việc làm ko ạ"
   - *Điểm số trước khi trừ:* 10/12.
   - *Nguyên nhân FAIL:* Bộ kiểm tra `unsupported_numbers` phát hiện chuỗi số `["1", "2"]`.
   - *Phân tích kỹ thuật:* LLM trình bày câu trả lời bằng Markdown có đánh số thứ tự đầu mục (`**1. Hỗ trợ việc làm**`, `**2. Chuẩn đầu ra ngoại ngữ**`). Do các đoạn chunk trích xuất không chứa chữ số `1` và `2` ở dạng độc lập, hàm regex `_NUM_RE = re.compile(r"\d[\d.,]*")` đã bắt nhầm số thứ tự đầu mục thành "con số không có căn cứ trong tài liệu".

2. **`TC-SVQ-040`:** "em có thắc mắc là học phi đi quân sự là bao tiền"
   - *Điểm số trước khi trừ:* 9/12.
   - *Nguyên nhân FAIL:* Tương tự `TC-SVQ-015`, phát hiện `unsupported_numbers: ["1", "2"]` do LLM đánh số các lưu ý liên hệ.
   
> [!NOTE]  
> **Khuyến nghị kỹ thuật:** Cập nhật hàm `unsupported_numbers` trong `verifier.py` ở các phiên bảo trì tiếp theo để bỏ qua các số thứ tự đầu mục trong Markdown dạng `r"^\s*(?:\d+\.|\*\*\d+\.\*\*)"` nhằm tránh bắt nhầm định dạng danh sách.

---

### 3. Vấn đề Thu thập Nguồn Web (Crawler Issue)

- **URL 19 (`https://baodanang.vn/...`):**
  - *Mô tả:* Bài báo *"Đại học Đông Á bảo đảm chất lượng đào tạo và hỗ trợ việc làm cho sinh viên"*.
  - *Hiện tượng:* Máy chủ Báo Đà Nẵng trả về HTTP `403 Forbidden` (chặn User-Agent hoặc kích hoạt Cloudflare Bot Protection).
  - *Xử lý an toàn:* Pipeline crawler đã tự động ghi nhận lỗi vào `crawl_results.csv` với trạng thái `FAILED (HTTP 403)`, không làm gián đoạn hay đổ vỡ quá trình thu thập 20 URL còn lại.
  - *Khắc phục:* Có thể bổ sung nội dung bài báo này thông qua bản sao lưu nội bộ hoặc văn bản tổng hợp của Trung tâm Truyền thông nhà trường nếu cần thiết.

---

### 4. Kết luận & Hướng giải quyết cho các Khoảng trống dữ liệu

1. **Về Điểm rèn luyện & Biểu mẫu sinh viên (4 câu):** Có thể giải quyết triệt để khi cấp thẩm quyền phê duyệt nạp 7 tệp Word DOCX trong hàng đợi (`document_approval_queue.csv`).
2. **Về Học phí chi tiết & Lịch thi cá nhân:** Đây là thông tin mang tính cá thể hóa, cần tích hợp API cổng thông tin sinh viên `my.uda.edu.vn` có xác thực JWT/OAuth2 thay vì nạp tĩnh vào RAG công khai.
