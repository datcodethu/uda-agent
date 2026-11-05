# KẾ HOẠCH CẢI TIẾN ANSWER GENERATION & RAG PIPELINE — IMPROVEMENT PLAN

> **Mục tiêu:** Rút ra các nguyên tắc tổng quát nâng cao chất lượng câu trả lời và độ tin cậy của chatbot dựa trên phân tích đối chiếu với NotebookLM.  
> **Nguyên tắc cốt lõi:** Không hardcode 75 câu trả lời; nâng cao năng lực tổng quát của hệ thống.

---

## 1. Tám Điểm Cốt lõi Học tập từ Mô hình Tham chiếu NotebookLM

1. **Cấu trúc Câu trả lời Trực diện (Direct Answering Structure):**
   - *Hạn chế của chatbot hiện tại:* Thường mở đầu bằng một câu dài trích tên văn bản pháp lý hoặc khẳng định "mình chưa tìm thấy".
   - *Nguyên tắc cải tiến:* Câu đầu tiên đi thẳng vào câu trả lời cốt lõi (Có / Không / Được / Cần thỏa mãn các điều kiện sau), sau đó mới trình bày căn cứ và các bước hành động.

2. **Phân loại Điều kiện Bằng Gạch đầu dòng Rõ ràng (Structured Conditions):**
   - *Hạn chế:* Chatbot viết thành đoạn văn liền dòng làm sinh viên khó quét thông tin nhanh.
   - *Nguyên tắc:* Phân tách rõ ràng:
     - `Điều kiện bắt buộc:` ...
     - `Đối tượng áp dụng:` ...
     - `Trường hợp ngoại lệ (có lý do chính đáng):` ...

3. **Quy trình Hành động Từng bước (Actionable Step-by-Step Guidance):**
   - Thay vì chỉ trích dẫn luật "sinh viên được quyền xin chuyển ngành", câu trả lời cần nêu rõ quy trình:
     - *Bước 1:* Tải mẫu đơn tại Cổng thông tin sinh viên hoặc nhận tại Phòng Đào tạo.
     - *Bước 2:* Xin ý kiến xác nhận của Khoa chủ quản.
     - *Bước 3:* Nộp về Bộ phận Một cửa Phòng Quản lý Đào tạo trong thời hạn thông báo.

4. **Chỉ dẫn Đầu mối Liên hệ Hợp lệ & Đầy đủ (Contact Channels):**
   - Với mọi câu hỏi thiếu thông tin hoặc cần làm thủ tục cá nhân, luôn ghi rõ tên đơn vị phụ trách kèm kênh hỗ trợ:
     - Thủ tục học vụ, lịch thi, chuyển ngành: **Phòng Quản lý Đào tạo** (Tầng 2).
     - Giấy xác nhận tạm hoãn NVQS, vay vốn, điểm rèn luyện: **Phòng Công tác sinh viên**.
     - Nợ học phí, biên lai, gia hạn đóng tiền: **Phòng Kế hoạch - Tài chính**.

5. **Loại bỏ Hoàn toàn Citation Marker trong Câu Từ chối (Post-processing Guardrail):**
   - Khi câu trả lời mang tính từ chối (`NO_EVIDENCE`), bộ lọc hậu xử lý phải tự động loại bỏ mọi marker `[1]`, `[2]`, `[3]` để không gây hiểu nhầm và không kích hoạt lỗi `invalid_citations`.

6. **Giữ Vững Thái độ Thấu cảm & Tôn trọng Sinh viên (Empathetic Tone):**
   - Tuyệt đối không dùng văn phong đe dọa kỷ luật ngay câu đầu.
   - Trấn an sinh viên trong các tình huống nhạy cảm (thiếu học phí, thi trượt, chậm nộp BHYT).

7. **Tổng hợp Đa nguồn Linh hoạt (Multi-source Synthesis):**
   - Kết hợp cả quy chế khung của trường và hướng dẫn thực hành của phòng ban để tạo câu trả lời vừa chuẩn pháp lý vừa hữu ích thực tiễn.

8. **Đề xuất Câu hỏi Gợi ý Tiếp nối Hợp lý (Contextual Next Steps):**
   - Sau khi trả lời, gợi ý 1–2 câu hỏi tiếp theo mà sinh viên thường cần biết (ví dụ: sau khi hỏi điều kiện dự thi, gợi ý sinh viên hỏi về thủ tục làm đơn xin phép vắng thi có lý do chính đáng).

---

## 2. Lộ trình Triển khai Đề xuất cho Phiên 6G

| Đợt | Nội dung công việc | Mục tiêu đạt được |
|---|---|---|
| **Đợt 1** | Vá lỗi kỹ thuật P1 trong `stream_handler.py` (loại bỏ citation marker thừa khi refusal) | Xóa bỏ 100% lỗi FAIL, đưa tỷ lệ lỗi kỹ thuật về 0% |
| **Đợt 2** | Thẩm định và nạp 2 tài liệu P0 cốt lõi: `2023_8_16_8_1_8.docx` (Thủ tục NVQS, Vay vốn) và Biểu mẫu chuyển ngành/rút môn qua cổng `ingest_approved.py` | Chuyển dịch ngay lập tức **22 câu hỏi PARTIAL sang PASS** |
| **Đợt 3** | Nâng cấp Prompt Answer Generation theo 8 nguyên tắc trực diện, có quy trình và đầu mối liên hệ | Tối ưu trải nghiệm sinh viên và cấu trúc câu trả lời |
| **Đợt 4** | Chạy lại kiểm thử toàn diện trên 75 câu khảo sát để ghi nhận mức độ cải thiện | Đo lường tỷ lệ PASS nhảy vọt từ 24% lên trên 55% |
