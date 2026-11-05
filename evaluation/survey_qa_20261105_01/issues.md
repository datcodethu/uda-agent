# BẢNG THEO DÕI VẤN ĐỀ VÀ LỖI HỆ THỐNG — SURVEY QA 20261105_01

> Tổng hợp toàn bộ các vấn đề kỹ thuật, dữ liệu và quy chế phát hiện qua kiểm thử 75 câu hỏi khảo sát sinh viên.

---

## 1. Phân loại mức độ ưu tiên
- **P0 (Critical):** Trả lời sai quy chế cốt lõi, khẳng định cấm thi/buộc thôi học sai bản chất, vi phạm an toàn chính sách học vụ.
- **P1 (High):** Bỏ sót quy định quan trọng, citation không hợp lệ (trích dẫn ngoài dải nguồn), phân loại sai intent.
- **P2 (Medium):** Thiếu dữ liệu văn bản chuyên ngành (Data Gap), câu trả lời chung chung chưa có hướng dẫn cụ thể.

---

## 2. Danh sách Vấn đề ghi nhận

### Nhóm P0: Lỗi Nghiêm trọng về An toàn & Chính sách Học vụ
*(Tổng số: 0 vấn đề)*

**Không có vấn đề P0.** Hệ thống đã giữ vững 100% nguyên tắc lấy sinh viên làm trung tâm: không có câu trả lời nào khẳng định cấm thi tuyệt đối hoặc tước quyền dự thi khi chưa có quyết định chính thức; điều kiện cốt lõi *"mà không có lý do chính đáng"* được bảo vệ trọn vẹn.

---

### Nhóm P1: Lỗi Trích dẫn & Độ trung thực (Faithfulness & Citations)
*(Tổng số: 1 vấn đề)*

#### Issue P1-TC-SVQ-002: Trích dẫn không hợp lệ ngoài dải nguồn: [3]
- **Test ID:** `TC-SVQ-002` (SVQ-002)
- **Hiện tượng:** `Sufficiency: NO_EVIDENCE | Badges: Chưa đủ bằng chứng để kết luận, Trích dẫn ngoài phạm vi: [3] | Sources: 0`
- **Nguyên nhân gốc rễ:** Khi LLM sinh câu từ chối (`NO_EVIDENCE`), pipeline đặt `sources = []`, nhưng trong văn bản sinh ra vẫn sót lại ký hiệu trích dẫn `[3]`, dẫn đến bộ Verifier bắt lỗi `invalid_citations: [3]`.
- **Đề xuất khắc phục:** Bổ sung bước làm sạch hậu xử lý (post-processing): nếu `sources` rỗng hoặc câu trả lời bắt đầu bằng từ chối, tự động loại bỏ mọi ký hiệu trích dẫn `\[\d+\]`.

---

## 3. Nhóm P2: Khoảng trống Dữ liệu Quy chế (Data Gap Issues)
Các câu hỏi sinh viên thật sự quan tâm nhưng hiện chưa có văn bản chính thức được nạp trong kho 10 tài liệu chuẩn:

1. **Thủ tục xin cấp Giấy tạm hoãn Nghĩa vụ Quân sự (SVQ-063, 066, 070, 071, 074):**
   - *Mô tả:* Sinh viên hỏi nộp đơn ở đâu để hoãn NVQS.
   - *Hiện trạng:* Chatbot hướng dẫn liên hệ Phòng CTSV / Ban CHQS trường là hướng dẫn an toàn, nhưng chưa có văn bản quy định chi tiết quy trình nộp đơn online trên portal.
   - *Khắc phục:* Nạp văn bản "Hướng dẫn giải quyết thủ tục hành chính một cửa cho sinh viên".

2. **Mức học phí và địa điểm học Giáo dục Quốc phòng - An ninh (SVQ-040, SVQ-058):**
   - *Mô tả:* Sinh viên hỏi học phí đi quân sự bao nhiêu tiền và khi nào đi.
   - *Hiện trạng:* Kho quy chế chỉ có khung chương trình GDQP-AN, không có biểu giá cụ thể từng năm.
   - *Khắc phục:* Nạp thông báo học vụ về kế hoạch học GDQP-AN năm học 2025-2026.

3. **Thủ tục đăng ký học lái xe mô tô (SVQ-075):**
   - *Mô tả:* Sinh viên hỏi đăng ký thi bằng lái xe ở đâu.
   - *Hiện trạng:* Nằm ngoài quy chế đào tạo đại học, chatbot nhận diện đúng và hướng dẫn hỏi Trung tâm dịch vụ / Đoàn trường.
   - *Khắc phục:* Bổ sung FAQ về các dịch vụ hỗ trợ sinh viên ngoài đào tạo.

4. **Quy định chi tiết về chuẩn đầu ra Tiếng Trung và Tiếng Nhật khoa CNTT (SVQ-009, 020, 064):**
   - *Mô tả:* Sinh viên hỏi CNTT chọn tiếng Nhật thì cần N4 và B1 hay chỉ N4.
   - *Hiện trạng:* Cần bổ sung bảng đối chiếu chứng chỉ ngoại ngữ chuẩn đầu ra chuyên biệt cho từng khoa/ngành.
   - *Khắc phục:* Nạp văn bản "Quy định Chuẩn đầu ra Ngoại ngữ và Tin học đối với sinh viên ĐH Đông Á".
