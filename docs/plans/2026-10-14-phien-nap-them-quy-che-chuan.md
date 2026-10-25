# Kế hoạch Phiên làm việc: Rà soát & Nạp thêm Quy chế chuẩn vào Kho RAG

**Ngày lập:** 2026-10-14  
**Trạng thái:** HOÀN THÀNH (ĐỢT 1 & ĐỢT 2)  

---

## 1. Hiểu nhiệm vụ (Understanding)
- **Mục tiêu:** Mở rộng tri thức của kho quy chế RAG (hiện chỉ có 1 văn bản 21 đoạn về chuẩn đầu ra ngoại ngữ).
- **Kết quả rà soát thực tế toàn bộ kho dữ liệu:**
  1. **Nhóm 23 file PDF trong `raw_documents/`:**
     - **1 file đã nạp:** `2023_8_23_16_29_59n.pdf` (Chuẩn đầu ra ngoại ngữ, 21 đoạn, 17.551 ký tự - ACTIVE).
     - **2 file PDF quy chế chuẩn đọc tốt, sẵn sàng nạp:**
       - `2023_8_29_8_50_20c.pdf`: Quyết định ban hành “Sứ mệnh, Tầm nhìn, Triết lý giáo dục và Mục tiêu giáo dục” của Trường Đại học Đông Á (5 đoạn, 2.821 ký tự).
       - `2023_8_29_8_51_2A.pdf`: Quyết định ban hành “Đặc điểm nhận diện - Giá trị cốt lõi” của con người Trường Đại học Đông Á (5 đoạn, 2.753 ký tự).
     - **1 file hướng dẫn bị chặn do bất thường:** `2024_11_14_14_26_46A.pdf` (QĐ 2474 phương pháp học tập, 44 đoạn, nhãn Điều 3 chiếm 93.2% - đang hoãn chờ bộ nhận đề mục thập phân).
     - **15 file PDF scan ảnh:** Đang chờ xin lại bản gốc từ Phòng Đào tạo (chưa chạy OCR).
     - **4 file loại trừ:** 2 file Luật Nhà nước (An ninh mạng, ATGT), 1 file lỗi font bảng mã (`2026_10_6_10_18_43c.pdf`), 1 file biểu mẫu đơn phúc khảo (`2026_7_8_17_19_23o.pdf`).
  2. **Nhóm văn bản Quy chế Word (rất quan trọng đối với sinh viên):**
     - Đã chuyển đổi sang `.docx` tại `doc_da_chuyen/`:
       - `2021_8_5_8_33_34A.docx` (37.134 ký tự, **53 đoạn**): **Quy chế công tác sinh viên đối với chương trình đào tạo đại học hệ chính quy** (QĐ số 106/QĐ-ĐHĐA). Đã kiểm thử cắt đoạn: phân đoạn `quyet_dinh` & `quy_dinh_kem_theo` cực kỳ chuẩn xác, không có cảnh báo bất thường!
       - `2021_8_5_8_31_26.docx` (6.313 ký tự, **9 đoạn**): **Nội quy học đường dành cho sinh viên** (QĐ số 105/QĐ-ĐHĐA). Đã kiểm thử cắt đoạn: 9 đoạn chuẩn xác, phân bố nhãn bình thường.
     - Hiện trạng: Trong `docs_registry.csv` đang ghi tên đuôi `.doc` và nằm ở `doc_da_chuyen/`.

---

## 2. Đề xuất kế hoạch nạp theo 2 đợt

### Đợt 1 (Nạp ngay các file PDF chuẩn sẵn có trong `raw_documents/`):
- **Tài liệu nạp:**
  1. `2023_8_29_8_50_20c.pdf` (5 đoạn, 2.821 ký tự)
  2. `2023_8_29_8_51_2A.pdf` (5 đoạn, 2.753 ký tự)
- **Các bước thực hiện:**
  1. Cập nhật `da_duyet=true` cho 2 dòng này trong `ai-service/data/docs_registry.csv`.
  2. Chạy dry-run kiểm tra:
     ```powershell
     $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.ingest_approved --status
     ```
     Kỳ vọng: Tổng số file được duyệt là 3 (gồm file cũ 2023 chuẩn đầu ra ngoại ngữ + 2 file mới, tổng ~31 đoạn).
  3. Dừng chờ bạn duyệt kết quả dry-run trước khi chạy `--apply`.
  4. Sau khi duyệt, chạy nạp thật:
     ```powershell
     $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.ingest_approved --apply --status
     ```
  5. Đánh giá kiểm thử hỏi đáp thử nghiệm không suy giảm chất lượng truy xuất.

### Đợt 2 (ĐÃ HOÀN THÀNH):
- **Tài liệu đã nạp:**
  1. `2021_8_5_8_33_34A.docx` (Quy chế CTSV, 53 đoạn, 47.334 ký tự)
  2. `2021_8_5_8_31_26.docx` (Nội quy học đường, 9 đoạn, 7.344 ký tự)
- **Kết quả thực tế:**
  - Đã sao chép 2 file `.docx` từ `doc_da_chuyen/` sang `raw_documents/`.
  - Đã cập nhật dòng trong `docs_registry.csv` thành `.docx` và `da_duyet=true`.
  - Đã chạy nạp thật `--apply --status`:
    - Tổng toàn kho: 5 tài liệu, 93 đoạn, 78.821 ký tự.
    - 52 file bị chặn an toàn.
    - 0 trùng lặp `chunk_id`.
    - Tự động xây dựng lại BM25.
    - Gọi 62 lệnh embedding thành công.
    - Toàn bộ 63/63 unit test PASS.


---

## 3. Bảng quyết định thiết kế (Design Decisions)

| Quyết định | Phương án cân nhắc | Vì sao chọn | Loại căn cứ |
|---|---|---|---|
| Ưu tiên nạp trước 2 PDF chuẩn ĐH Đông Á | A: Nạp cả Word và PDF cùng lúc.<br>**B: Nạp 2 file PDF chuẩn trước (Đợt 1), sau đó nạp file Word Quy chế CTSV (Đợt 2)** | 2 file PDF đã nằm sẵn trong `raw_documents`, cấu trúc nhỏ gọn (mỗi file 5 đoạn), kiểm chứng nhanh, an toàn tuyệt đối. | [kỹ thuật] |
| Xử lý file Word Quy chế CTSV (37.134 ký tự) | A: Bỏ qua vì là file Word.<br>**B: Dùng bản `.docx` đã chuyển đổi trong `doc_da_chuyen`, đưa vào `raw_documents`** | Đây là quy chế nòng cốt nhất về sinh viên (quyền lợi, học bổng, kỷ luật...), có giá trị hỏi đáp thực tế cao nhất. | [thực tế dữ liệu] |

---

## 4. Dự toán chi phí & Lệnh kiểm tra
- **Số lệnh gọi API:**
  - Dry-run: **0 VND** (không gọi API).
  - Nạp thật Đợt 1: Gọi đúng 10 lệnh embedding (5 đoạn + 5 đoạn = 10 đoạn). Hoàn toàn nằm trong hạn mức miễn phí hàng ngày của Gemini Embedding.
