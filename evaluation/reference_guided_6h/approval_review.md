# BÁO CÁO THẨM ĐỊNH NGUỒN TRI THỨC VÀ HỒ SƠ PHÊ DUYỆT TÀI LIỆU (APPROVAL REVIEW)

**Thời điểm thẩm định:** Ngày 05 tháng 11 năm 2026  
**Nhánh Git:** `demo/school-presentation-2026`  
**Cơ chế tuân thủ:** Default-Deny & Approval Gate (Không tự ý đổi `da_duyet=true`)

---

## 1. TỔNG QUAN HỒ SƠ THẨM ĐỊNH

Tiến hành rà soát độc lập 7 tài liệu DOCX được phát hiện trong kho lưu trữ `raw_documents` và `doc_da_chuyen`. Toàn bộ 7 văn bản được đối chiếu với:
- Nguồn ban hành chính thức.
- Tình trạng hiệu lực pháp lý và văn bản sửa đổi thay thế.
- Đối tượng áp dụng và test cases hỗ trợ trong 75 câu khảo sát.
- Rà soát rủi ro thông tin định danh cá nhân (PII) và dữ liệu nội bộ.
- Khả năng tích hợp vào kho dữ liệu RAG phục vụ sinh viên.

---

## 2. BẢNG TỔNG HỢP KẾT QUẢ THẨM ĐỊNH 7 TÀI LIỆU DOCX

| # | Tên tệp | Loại tài liệu | Cơ quan ban hành | Hiệu lực & Ngày | Test cases hỗ trợ | Rà soát PII / Nội bộ | Căn cứ phê duyệt |
|---|---|---|---|---|---|---|:---:|
| 1 | `2023_8_16_8_1_8.docx` | Quy trình trực tuyến | Phòng QLĐT&CTSV | 16/08/2023 (Đang áp dụng) | TC-SVQ-008, 010, 051 | An toàn (Không có PII) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |
| 2 | `2021_9_8_16_1_12S.docx` | Biểu mẫu đơn hoãn NVQS | ĐH Đông Á | 08/09/2021 (Đang lưu hành) | TC-SVQ-010, 051 | An toàn (Biểu mẫu trống) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |
| 3 | `2021_11_6_16_42_11g.docx` | QĐ quy phạm pháp luật | Thủ tướng Chính phủ | 27/09/2007 (Hết hiệu lực phần mức vay) | TC-SVQ-008 | An toàn (Văn bản Nhà nước) | ⛔ **TẠM HOÃN** (Cần bản mới) |
| 4 | `2022_4_8_9_12_1c.docx` | Biểu mẫu đơn chuyển ngành | Phòng QLĐT&CTSV | 08/04/2022 (Đang lưu hành) | TC-SVQ-009, 018, 069 | An toàn (Biểu mẫu trống) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |
| 5 | `2021_12_11_15_52_19n.docx` | Biểu mẫu đơn rút học phần | Phòng QLĐT&CTSV | 11/12/2021 (Đang lưu hành) | TC-SVQ-023, 041, 062 | An toàn (Biểu mẫu trống) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |
| 6 | `2021_12_11_16_2_24n.docx` | Biểu mẫu đơn đổi lớp HP | Phòng QLĐT&CTSV | 11/12/2021 (Đang lưu hành) | TC-SVQ-021, 043 | An toàn (Biểu mẫu trống) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |
| 7 | `2022_11_1_14_11_12n.docx` | Biểu mẫu đơn xin vắng thi | Phòng QLĐT&CTSV | 01/11/2022 (Đang lưu hành) | TC-SVQ-004, 038 | An toàn (Biểu mẫu trống) | **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT** |

---

## 3. ĐÁNH GIÁ CHI TIẾT TỪNG VĂN BẢN

### 1. Tệp `2023_8_16_8_1_8.docx`
- **Tên văn bản:** Hướng dẫn quy trình đăng ký cấp giấy xác nhận sinh viên trực tuyến để hưởng các chế độ theo quy định.
- **Đường dẫn:** `ai-service/data/raw_documents/2023_8_16_8_1_8.docx`
- **SHA-256:** `6b340f080cdba429e9d0bafc19f0d9161f4df53bb1b34bf31d7c5f601f3373ec`
- **Nội dung chính:**
  * Giải quyết cấp giấy online trong 72 giờ (không tính Chủ nhật).
  * Quy trình 4 bước: (1) Đăng nhập `my.uda.edu.vn`; (2) Cập nhật hồ sơ cá nhân; (3) Chọn mục Đăng ký cấp giấy; (4) Nhận kết quả trực tiếp hoặc bưu điện.
  * Các loại giấy xác nhận: Tạm hoãn NVQS, Vay vốn ngân hàng chính sách, Giảm trừ gia cảnh thuế TNCN, Bổ túc hồ sơ cá nhân.
- **Rà soát PII & Dữ liệu nội bộ:** Hoàn toàn an toàn. Không có tên, số điện thoại hay email cá nhân của chuyên viên.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**. Đây là tài liệu cốt lõi giúp giải quyết các câu hỏi về thủ tục hành chính trực tuyến (TC-SVQ-008, TC-SVQ-010, TC-SVQ-051).

---

### 2. Tệp `2021_9_8_16_1_12S.docx`
- **Tên văn bản:** Đơn xin xác nhận về việc sinh viên nam trong độ tuổi NVQS để xin tạm hoãn gọi nhập ngũ thời bình.
- **Đường dẫn:** `ai-service/data/doc_da_chuyen/2021_9_8_16_1_12S.docx`
- **SHA-256:** `9a580958f5021d99da2a246c2e00e213d5aef96073812e8a869a1459746e6ee9`
- **Nội dung chính:** Biểu mẫu hành chính dành cho sinh viên nam làm đơn xin giấy hoãn nghĩa vụ quân sự.
- **Rà soát PII:** Là biểu mẫu trống điền thông tin, không chứa dữ liệu cá nhân.
- **Văn bản liên quan:** Kết hợp với Hướng dẫn online 2023 ở tệp 1.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**.

---

### 3. Tệp `2021_11_6_16_42_11g.docx`
- **Tên văn bản:** Quyết định số 157/2007/QĐ-TTg về tín dụng đối với học sinh, sinh viên.
- **Đường dẫn:** `ai-service/data/doc_da_chuyen/2021_11_6_16_42_11g.docx`
- **SHA-256:** `4d6186220cc4b37d492ac04bca6d1ecb6db609f59a7a7ac278d04a02bc0394b1`
- **Vấn đề pháp lý trọng yếu:** Văn bản gốc ban hành năm 2007 quy định mức vay tối đa 800.000 đồng/tháng/HSSV. Mức vay này đã được sửa đổi qua nhiều thời kỳ và gần đây nhất là **Quyết định số 05/2022/QĐ-TTg ngày 23/03/2022 nâng mức vay lên 4.000.000 đồng/tháng/HSSV**.
- **Rủi ro nếu nạp:** Chatbot sẽ trích dẫn nhầm số tiền cũ 800.000đ/tháng, gây hiểu lầm nghiêm trọng cho sinh viên diện vay vốn chính sách.
- **Quyết định xử lý theo chỉ đạo Phiên 6H:** ⛔ **TẠM HOÃN** văn bản này khỏi kho thông tin hiện hành cho đến khi kiểm tra và thu thập được văn bản thay thế (QĐ 05/2022/QĐ-TTg).

---

### 4. Tệp `2022_4_8_9_12_1c.docx`
- **Tên văn bản:** Đơn xin chuyển ngành học.
- **Đường dẫn:** `ai-service/data/raw_documents/2022_4_8_9_12_1c.docx`
- **SHA-256:** `ce558369f4f03ce75d3f70ad4f687f19543c04e5004a5c8390c2d385e17b70b8`
- **Nội dung chính:** Mẫu đơn chuyển ngành quy định rõ luồng xử lý: Ý kiến Khoa đang học $\rightarrow$ Ý kiến Khoa chuyển đến $\rightarrow$ Phòng QLĐT&CTSV.
- **Rà soát PII:** Biểu mẫu trống, an toàn.
- **Hỗ trợ:** TC-SVQ-009, TC-SVQ-018, TC-SVQ-069.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**.

---

### 5. Tệp `2021_12_11_15_52_19n.docx`
- **Tên văn bản:** Đơn đề nghị rút học phần.
- **Đường dẫn:** `ai-service/data/raw_documents/2021_12_11_15_52_19n.docx`
- **SHA-256:** `38b9b346b4c21f3e3cb4b04bcc8aac615c28bd5faa658ca1043497ef5c81c765`
- **Nội dung chính:** Thủ tục xin rút bớt học phần đã đăng ký có ý kiến xác nhận của Cố vấn học tập (CVHT) và Giảng viên phụ trách.
- **Rà soát PII:** Biểu mẫu trống, an toàn.
- **Hỗ trợ:** TC-SVQ-023, TC-SVQ-041, TC-SVQ-062.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**.

---

### 6. Tệp `2021_12_11_16_2_24n.docx`
- **Tên văn bản:** Đơn đề nghị chuyển lớp học phần.
- **Đường dẫn:** `ai-service/data/raw_documents/2021_12_11_16_2_24n.docx`
- **SHA-256:** `fbd82192d7bb52dc72f68f0d5693cd3f72484ad80534833ac1db35f8d7802285`
- **Nội dung chính:** Mẫu đơn chuyển lớp học phần do trùng lịch hoặc điều chỉnh kế hoạch học tập cá nhân.
- **Rà soát PII:** Biểu mẫu trống, an toàn.
- **Hỗ trợ:** TC-SVQ-021, TC-SVQ-043.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**.

---

### 7. Tệp `2022_11_1_14_11_12n.docx`
- **Tên văn bản:** Đơn xin phép vắng thi học phần.
- **Đường dẫn:** `ai-service/data/raw_documents/2022_11_1_14_11_12n.docx`
- **SHA-256:** `f057f7c448a7a86049e07c8d349328ce09f5fb6b5d9a75fa9bd8b5f6424c8ca4`
- **Nội dung chính:** Thủ tục xin vắng thi vì lý do chính đáng (tai nạn, bệnh tật bất khả kháng kèm minh chứng) và cam kết đăng ký thi lại chậm nhất trong vòng 1 học kỳ.
- **Rà soát PII:** Biểu mẫu trống, an toàn.
- **Hỗ trợ:** TC-SVQ-004, TC-SVQ-038.
- **Kết luận:** **ĐỦ ĐIỀU KIỆN TRÌNH DUYỆT**.

---

## 4. KHUYẾN NGHỊ VÀ HÀNG RÀO PHÊ DUYỆT (APPROVAL GATE STATUS)

1. **6 tài liệu ĐỦ ĐIỀU KIỆN:** (1) Hướng dẫn cấp giấy online; (2) Mẫu đơn hoãn NVQS; (3) Mẫu đơn chuyển ngành; (4) Mẫu đơn rút học phần; (5) Mẫu đơn chuyển lớp; (6) Mẫu đơn vắng thi.  
   $\rightarrow$ **Trạng thái:** Duy trì `WAITING_FOR_APPROVAL` trong `docs_registry.csv`. Đợi lệnh phê duyệt của Người phụ trách trước khi nạp.
2. **1 tài liệu TẠM HOÃN:** QĐ 157/2007 về tín dụng HSSV.  
   $\rightarrow$ **Trạng thái:** `SUSPENDED_PENDING_UPDATE`. Tuyệt đối không nạp cho đến khi có văn bản QĐ 05/2022/QĐ-TTg thay thế.
