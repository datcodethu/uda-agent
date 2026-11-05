# BÁO CÁO PHÂN TÍCH LỖI SINH VĂN BẢN & TRÍCH DẪN — GENERATION FAILURES

> **Thời điểm:** 05/11/2026 | **Phiên:** 6F  
> **Tổng số trường hợp xác định:** 3 trường hợp (gồm 2 lỗi sinh văn bản và 1 lỗi trích dẫn)

---

## 1. Tổng quan Lỗi Sinh văn bản & Trích dẫn
- **Generation Failure:** Xảy ra khi Top-5 chunks trong context **đã chứa** thông tin liên quan, nhưng mô hình LLM tổng hợp quá ngắn gọn, bỏ sót các diện chính sách cụ thể hoặc đưa ra câu trả lời quá chung chung.
- **Citation Failure:** Xảy ra khi văn bản sinh ra chứa marker trích dẫn không có thật trong dải nguồn (`sources = []`), kích hoạt cảnh báo an toàn của bộ kiểm định Verifier.

---

## 2. Chi tiết các trường hợp

### Ca 1: TC-SVQ-002 (Lỗi Trích dẫn Sót Marker — CITATION_FAILURE)
- **Câu hỏi:** *"Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không"*
- **Câu trả lời thực tế của Chatbot:**
  > *"Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Tài liệu hiện tại chỉ quy định về chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành không chuyên ngữ từ khóa 2022 trở đi [3]. Bạn vui lòng liên hệ Khoa chủ quản hoặc Phòng Đào tạo..."*
- **Vấn đề phát hiện:**
  - Chatbot nhận diện đúng trạng thái `NO_EVIDENCE` và trả lời từ chối an toàn.
  - Pipeline đã chủ động đặt `sources = []` để tránh hiển thị nguồn giả mạo.
  - **Tuy nhiên**, trong câu từ chối mà LLM sinh ra vẫn còn sót lại ký tự `[3]`.
  - Bộ kiểm tra `CitationVerifier` phát hiện `invalid_citations: [3]` do chỉ số 3 nằm ngoài dải nguồn `[]` (dải rỗng).
- **Nguyên nhân gốc rễ:** Prompt yêu cầu LLM trích dẫn nguồn khi giải thích, khiến LLM quen tay chèn `[3]` ngay cả khi đang từ chối; hệ thống thiếu bước làm sạch hậu xử lý.
- **Đề xuất khắc phục:** Bổ sung 3 dòng code post-processing trong `stream_handler.py`: Nếu `sources` rỗng hoặc câu trả lời bắt đầu bằng từ chối, tự động loại bỏ mọi ký hiệu trích dẫn `\[\d+\]`.

### Ca 2: TC-SVQ-003 (Tóm tắt sơ sài chính sách học bổng — GENERATION_FAILURE)
- **Câu hỏi:** *"Mức học bổng được nhận"*
- **Context thực tế:** Đã truy xuất Điều 16 và Điều 5 Quy chế CTSV (`2021_8_5_8_33_34A`).
- **Câu trả lời của Chatbot:** Chỉ nêu chung chung: *"sinh viên được xét nhận học bổng khuyến khích học tập và học bổng tài trợ... chưa có quy định số tiền cụ thể"*.
- **Vấn đề:** Trong Điều 16 có nêu rõ các diện chính sách ưu tiên và quỹ hỗ trợ tài chính sinh viên khó khăn của nhà trường, nhưng LLM không tóm tắt các diện này để hướng dẫn sinh viên.

### Ca 3: TC-SVQ-013 (Bỏ sót các tiêu chí rèn luyện — GENERATION_FAILURE)
- **Câu hỏi:** *"cách để cộng điểm rèn luyện thì cần làm những gì"*
- **Context thực tế:** Đã truy xuất Điều 14 (Hoạt động tình nguyện, đoàn thể) và Điều 20 (Ban cán sự lớp) Quy chế CTSV.
- **Vấn đề:** Chatbot chỉ tập trung trả lời vào mỗi ban cán sự lớp được cộng điểm, bỏ sót toàn bộ các hình thức cộng điểm thông qua hoạt động tình nguyện, công tác xã hội được nêu tại Điều 14.

---

## 3. Bài học Rút ra cho Answer Generation
1. Khi câu trả lời là **từ chối do thiếu bằng chứng**, cấm sinh citation marker.
2. Khi context có nhiều điều khoản bổ trợ (như Điều 14 và Điều 20), prompt phải yêu cầu tổng hợp đa chiều theo gạch đầu dòng, tránh chỉ chọn một ý duy nhất để trả lời.
