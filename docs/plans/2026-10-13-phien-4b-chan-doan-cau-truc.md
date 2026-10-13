# Kế hoạch Phiên 4B: Chẩn đoán cấu trúc văn bản 2024_11_14_14_26_46A.pdf (QĐ 2474)

## A. Hiểu nhiệm vụ (Understanding)
- **Nhiệm vụ cốt lõi:** Viết công cụ phân tích cấu trúc văn bản `scripts/chan_doan_cau_truc.py` để chẩn đoán hiện tượng bất thường của file `2024_11_14_14_26_46A.pdf` (41/44 đoạn bị gán nhãn "Điều 3"), quét các mẫu đề mục tiềm năng trong văn bản gốc, viết unit test với dữ liệu giả lập, lập báo cáo chi tiết và đề xuất 3 phương án xử lý.
- **Ranh giới cứng phiên này:**
  - CHỈ phân tích và đề xuất; KHÔNG sửa đổi logic cắt đoạn trong `structural_chunker.py`.
  - KHÔNG sửa `ingest_approved.py`, `config.py`, `prompts.py` hay `docs_registry.csv`.
  - KHÔNG nạp, sửa hay gỡ bỏ dữ liệu trong kho; KHÔNG gọi API bên ngoài (0 VND).
  - TUYỆT ĐỐI KHÔNG in nội dung quy chế thật ra khung chat (chỉ in số lượng và ghi chi tiết vào file preview).
- **Phạm vi mã nguồn:** Duy nhất `ai-service/scripts/chan_doan_cau_truc.py` và `ai-service/tests/test_core.py`.

---

## B. Thiết kế kỹ thuật và Bảng quyết định

### 1. Bảng quyết định thiết kế

| Quyết định | Phương án đã cân nhắc | Vì sao chọn | Loại căn cứ |
|---|---|---|---|
| Tách logic chẩn đoán thành các hàm thuần (pure functions) | (A) Viết dồn toàn bộ trong khối `main()` của script; (B) Tách hàm thuần nhận dữ liệu và trả dict kết quả | Tách hàm thuần giúp viết Unit Test độc lập trong `tests/test_core.py` mà không phụ thuộc file thật trên đĩa hay I/O | [kỹ thuật: Clean Code & Unit Testing] |
| Đọc dữ liệu phân đoạn từ `chunks.jsonl` | (A) Truy vấn qua Qdrant vector DB; (B) Đọc trực tiếp `data/chunks.jsonl` | Đọc `chunks.jsonl` hoàn toàn không phụ thuộc mạng, không lo đụng độ file-lock của Qdrant local, tốc độ tức thì | [yêu cầu người dùng & kỹ thuật] |
| Lưu vết dòng tiêu đề vào file preview | (A) In toàn bộ ra terminal; (B) Ghi ra `ai-service/data/chunk_preview/chan_doan_<file>.txt` và chỉ in số liệu tổng hợp trong chat | Bảo vệ nguyên tắc bảo mật và chống tràn ngữ cảnh (chỉ in số liệu thống kê ra chat, chi tiết dòng lưu ra file trên đĩa) | [yêu cầu người dùng & bảo mật] |
| Mô phỏng dữ liệu test | (A) Dùng trích đoạn thật từ file 2474; (B) Tự viết văn bản giả lập ngắn gọn | Tuân thủ tuyệt đối quy tắc không dùng nguyên văn quy chế thật trong test, kiểm soát chính xác các ca biên | [yêu cầu người dùng] |

---

### 2. Thiết kế module `scripts/chan_doan_cau_truc.py`

Module gồm 3 khối chức năng chính:

1. **Khối phân tích chunks (`analyze_chunks_distribution`):**
   - Đọc `data/chunks.jsonl`.
   - Lọc các bản ghi khớp với `doc_name` hoặc `file` chỉ định (chuẩn hóa NFC, hỗ trợ có/không có đuôi `.pdf`).
   - Thống kê nhóm `(phan_van_ban, dieu)`:
     - Số lượng đoạn trong nhóm.
     - Tổng số ký tự trong nhóm.
     - Tỷ lệ phần trăm trên tổng số đoạn của văn bản.
   - Cảnh báo: Gắn cờ `[CẢNH BÁO BẤT THƯỜNG]` nếu có nhóm nhãn Điều chiếm `> 50%` tổng số đoạn của văn bản.

2. **Khối quét đề mục văn bản gốc (`classify_heading_lines`):**
   - Đọc văn bản gốc qua `load_text(path)` và `clean_text(raw_text)`.
   - Tách từng dòng và đánh số dòng (1-indexed).
   - Phân loại các dòng có dấu hiệu là tiêu đề/đề mục thành 5 nhóm:
     1. `CHƯƠNG_ĐIỀU_MỤC_PHẦN`: Bắt đầu bằng `Chương`, `Điều`, `Mục`, `Phần` (không phân biệt hoa/thường).
     2. `SỐ_LA_MÃ`: Bắt đầu bằng chữ số La Mã (`I.`, `II.`, `III.`, `IV.`, `V.`...).
     3. `SỐ_THẬP_PHÂN`: Bắt đầu bằng số dạng `1.`, `1.1`, `2.3.1`...
     4. `CHỮ_CÁI`: Bắt đầu bằng chữ cái `A.`, `B.`, hoặc `a)`, `b)`...
     5. `CHỮ_HOA_TOÀN_BỘ`: Dòng viết hoa toàn bộ (uppercase), ngắn hơn 100 ký tự (loại trừ các dòng thuộc 4 nhóm trên).
   - Xuất file báo cáo chi tiết ra `data/chunk_preview/chan_doan_<tên_file>.txt` định dạng:
     `[Dòng {so_dong:4d}] [{kieu}] {80_ky_tu_dau}`.
   - Trả về số lượng dòng theo từng kiểu để in ra màn hình.

3. **Khối chẩn đoán ranh giới Quyết định ban hành:**
   - Xác định ranh giới giữa Quyết định ban hành (Điều 1, 2, 3) và phần tài liệu hướng dẫn đính kèm.
   - Đo chiều dài ký tự phần Quyết định ban hành.
   - Liệt kê các `chunk_id` có nhãn "Điều 3" nhưng thực chất thuộc phần hướng dẫn đính kèm.
   - Kiểm tra xem metadata của chunks có trường `page` (thông tin số trang) hay không.

---

### 3. Thiết kế Unit Test trong `tests/test_core.py`

Tạo lớp kiểm thử `TestStructureDiagnosis(unittest.TestCase)`:
- `test_analyze_chunks_distribution_flags_anomaly_above_50_percent`:
  - Tạo danh sách chunks giả lập (10 chunks, trong đó nhãn "Điều 3" chiếm 8 chunks = 80%).
  - Kiểm tra hàm phát hiện chính xác nhóm Điều 3 chiếm > 50% và gắn cờ cảnh báo.
- `test_classify_heading_lines_detects_all_patterns`:
  - Tạo chuỗi văn bản giả lập chứa đủ 5 mẫu đề mục:
    - `Phần 1. Tổng quan`
    - `I. Mục tiêu học tập`
    - `1.1. Phương pháp tự học`
    - `a) Đọc tài liệu trước khi lên lớp`
    - `HƯỚNG DẪN DÀNH CHO SINH VIÊN` (viết hoa ngắn)
    - Dòng thân bài thông thường dài hơn 100 ký tự hoặc chữ thường.
  - Kiểm tra hàm phân loại chính xác từng dòng vào đúng nhóm mà không bỏ sót.

---

## C. Kế hoạch triển khai từng bước

### Bước 1: Tạo kịch bản chẩn đoán `scripts/chan_doan_cau_truc.py`
- Cài đặt các hàm thuần:
  - `analyze_chunks_distribution(chunks, doc_name)`
  - `classify_heading_lines(text)`
  - `diagnose_document_structure(file_name, chunks_path, raw_dir, output_preview_dir)`
- Cài đặt khối `main()` nhận đối số từ CLI.

### Bước 2: Bổ sung Unit Tests vào `tests/test_core.py`
- Thêm lớp `TestStructureDiagnosis` với dữ liệu mô phỏng giả lập.
- Chạy kiểm thử:
  ```powershell
  $env:PYTHONUTF8="1"
  venv\Scripts\python.exe -m unittest discover -s tests -v
  ```
- Kỳ vọng: 44 test cũ + 2 test mới = **46/46 test PASS**.

### Bước 3: Chạy chẩn đoán trên file `2024_11_14_14_26_46A.pdf`
- Lệnh thực thi:
  ```powershell
  $env:PYTHONUTF8="1"
  venv\Scripts\python.exe -m scripts.chan_doan_cau_truc 2024_11_14_14_26_46A.pdf
  ```
- Kiểm tra file kết quả tại `ai-service/data/chunk_preview/chan_doan_2024_11_14_14_26_46A.pdf.txt`.
- Thu thập số liệu thống kê đề mục.

### Bước 4: Chạy đối chiếu trên file chuẩn `2023_8_23_16_29_59n.pdf`
- Lệnh thực thi:
  ```powershell
  $env:PYTHONUTF8="1"
  venv\Scripts\python.exe -m scripts.chan_doan_cau_truc 2023_8_23_16_29_59n.pdf
  ```
- Kiểm tra file kết quả tại `ai-service/data/chunk_preview/chan_doan_2023_8_23_16_29_59n.pdf.txt`.
- So sánh tỷ lệ phân bổ các Điều của văn bản chuẩn (QĐ 1345) với văn bản bất thường (QĐ 2474).

### Bước 5: Báo cáo phân tích và Đề xuất 3 phương án xử lý
Tổng hợp báo cáo với 4 nội dung trọng tâm:
1. Danh sách `chunk_id` bị gán sai nhãn Điều 3 và số dòng bắt đầu trong văn bản gốc.
2. Dung lượng phần Quyết định ban hành vs phần Tài liệu hướng dẫn.
3. Nhận xét về thông tin trang (page) trong dữ liệu hiện tại.
4. Đánh giá chi tiết 3 phương án xử lý (Ưu, nhược, tác động trích dẫn lên sinh viên, việc cần sửa):
   - **Phương án 1:** Loại khỏi kho quy chế (`loai = huong_dan`).
   - **Phương án 2:** Bổ sung bộ nhận diện đề mục phân cấp đa tầng (gắn nhãn Mục/Phần thay cho Điều).
   - **Phương án 3:** Cắt theo độ dài cố định kèm tiền tố tên văn bản (Fixed Chunking).

### Bước 6: Hoàn thiện Nhật ký và Tiến độ
- Viết nhật ký `docs/journal/2026-10-13-phien-4b-chan-doan-cau-truc.md` theo mẫu `_mau.md`.
- Cập nhật tiến độ tại `docs/progress.md` và `docs/decisions.md`.
- Báo cáo cuối phiên với 5 đề mục chuẩn theo quy trình.

---

## D. Rủi ro và Biện pháp kiểm soát
1. **Rủi ro lộ nội dung quy chế ra màn hình:**
   - *Kiểm soát:* Script chỉ in số lượng và bảng thống kê tổng hợp. Mọi chuỗi ký tự tiêu đề đều được ghi trực tiếp vào file `.txt` trong thư mục `chunk_preview/`.
2. **Rủi ro chạm vào dữ liệu kho thật:**
   - *Kiểm soát:* Script chỉ mở `chunks.jsonl` ở chế độ đọc (`r`), không mở kết nối ghi hay xóa bất kỳ file nào.
3. **Rủi ro sai lệch mã hóa tiếng Việt trên Windows:**
   - *Kiểm soát:* Sử dụng đường dẫn tuyệt đối/venv trực tiếp `venv\Scripts\python.exe`, cấu hình `$env:PYTHONUTF8="1"` và `encoding="utf-8"` cho mọi thao tác đọc/ghi file.
