# Kế hoạch Phiên 4A: Mở rộng kho quy chế – Nạp tài liệu Hướng dẫn học tập đại học (QĐ 2474/QĐ-ĐHĐA)

## 1. Mục tiêu và phạm vi

- **Mục tiêu:** Mở rộng tri thức của chatbot sang lĩnh vực phương pháp học tập, tín chỉ và đánh giá học phần tại Trường Đại học Đông Á bằng cách nạp văn bản quy chế thứ hai: `2024_11_14_14_26_46A.pdf` (Quyết định số 2474/QĐ-ĐHĐA-QLĐT ngày 14/11/2024).
- **Phạm vi dữ liệu:**
  - File nạp: `2024_11_14_14_26_46A.pdf` (41.661 ký tự, 44 đoạn cắt theo Chương/Điều hoàn chỉnh, 0 cảnh báo thứ tự Điều).
  - Kho sau khi nạp: 2 văn bản đã duyệt (21 đoạn của QĐ 1345 + 44 đoạn của QĐ 2474 = **65 đoạn**).
  - 53 file còn lại tiếp tục bị chặn an toàn theo bảng đăng ký `docs_registry.csv`.
- **Phạm vi mã nguồn:** Không thay đổi logic cốt lõi; chỉ cập nhật cờ duyệt trong `docs_registry.csv` và chạy kiểm thử qua `scripts.ingest_approved` cùng `scripts.ask`.

---

## 2. Dự toán chi phí API (Tuân thủ Quy tắc Chi phí)

| Thao tác | Số lượng | Lệnh gọi Embedding | Lệnh gọi LLM Chat | Tổng lượt gọi | Ghi chú |
|---|---|---|---|---|---|
| Dry-run kiểm tra bảng đăng ký | 1 lần | 0 | 0 | 0 | Miễn phí (chạy cục bộ) |
| Nạp 44 đoạn văn bản (`--apply`) | 44 đoạn | 1 batch (44 passages) | 0 | 1 | 1 lượt gọi embedding API |
| Hỏi thử câu 1 (Nội dung mới trong QĐ 2474) | 1 câu | 1 | 1 | 2 | Gemini Flash Latest |
| Hỏi thử câu 2 (Hỏi lại quy chế ngoại ngữ cũ) | 1 câu | 1 | 1 | 2 | Kiểm tra không mất mát dữ liệu cũ |
| Hỏi thử câu 3 (Câu hỏi ngoài phạm vi) | 1 câu | 1 | 1 | 2 | Kiểm tra duy trì cờ từ chối |
| **Tổng cộng dự kiến** | - | **4 lượt gọi** | **3 lượt gọi** | **~7 lượt gọi** | Rất thấp so với ngưỡng cảnh báo 50 |

---

## 3. Các bước triển khai chi tiết

### Bước 1: Cập nhật dòng phê duyệt trong `docs_registry.csv`
- Mở `ai-service/data/docs_registry.csv` và cập nhật dòng tương ứng với file `2024_11_14_14_26_46A.pdf`:
  - `da_duyet`: `true`
  - `loai`: `quy_che_truong`
  - `status`: `ACTIVE`
  - `public_or_internal`: `public`

### Bước 2: Chạy Dry-Run xác minh cổng nạp (Không gọi API)
- **Lệnh thực thi:**
  ```powershell
  cmd /c "set PYTHONUTF8=1&& venv\Scripts\python.exe -m scripts.ingest_approved"
  ```
- **Kết quả kỳ vọng:**
  - Danh sách "SẼ NẠP": Hiển thị đúng 2 file:
    1. `2023_8_23_16_29_59n.pdf` (21 đoạn, 17.551 ký tự)
    2. `2024_11_14_14_26_46A.pdf` (44 đoạn, ~41.661 ký tự)
  - Danh sách "BỊ CHẶN": Đúng 53 file còn lại kèm lý do rõ ràng.
  - Không ghi bất kỳ dữ liệu nào vào DB hay đĩa.

### Bước 3: Nạp kho thực tế (`--apply`)
- **Lệnh thực thi:**
  ```powershell
  cmd /c "set PYTHONUTF8=1&& venv\Scripts\python.exe -m scripts.ingest_approved --apply"
  ```
- **Kết quả kỳ vọng:**
  - Nạp thành công 2 file với tổng cộng **65 đoạn**.
  - File `ai-service/data/chunks.jsonl` có đúng 65 dòng JSON hợp lệ.
  - Collection `donga_regulations` trong Qdrant local được cập nhật đầy đủ 65 vector.

### Bước 4: Thực nghiệm kiểm thử hỏi đáp (`scripts.ask`)
Thực hiện 3 câu hỏi kiểm chứng trên chế độ `--mode hybrid`:

1. **Câu 1 (Kiểm chứng tài liệu mới – Phương pháp học tập & tín chỉ):**
   - *Câu hỏi:* `"Sinh viên cần chuẩn bị những gì trước khi lên lớp theo hướng dẫn học tập của trường?"`
   - *Kỳ vọng:* Hệ thống trích dẫn đúng các Điều trong QĐ 2474 (đọc tài liệu, chuẩn bị câu hỏi, xem đề cương học phần), trả lời rõ ràng, `TỪ CHỐI: False`.
2. **Câu 2 (Kiểm chứng không hồi quy – Quy chế ngoại ngữ đã nạp ở Phiên 3B):**
   - *Câu hỏi:* `"Chuẩn đầu ra ngoại ngữ đối với sinh viên các ngành không chuyên ngữ là gì?"`
   - *Kỳ vọng:* Hệ thống vẫn tìm đúng Điều 1, Điều 2 trong file QĐ 1345 cũ với điểm tương đồng cao, trả lời chuẩn xác.
3. **Câu 3 (Kiểm chứng cơ chế từ chối – Câu hỏi ngoài phạm vi cả 2 tài liệu):**
   - *Câu hỏi:* `"Điều kiện xét cấp học bổng khuyến khích học tập là gì?"`
   - *Kỳ vọng:* Hệ thống vẫn kích hoạt cờ từ chối `llm_refused` và trả lời mẫu từ chối do chưa có tài liệu học bổng trong kho.

### Bước 5: Chạy lại toàn bộ Unit Tests
- **Lệnh thực thi:**
  ```powershell
  cmd /c "venv\Scripts\python.exe -m unittest discover -s tests -v"
  ```
- **Kỳ vọng:** Toàn bộ 44/44 unit test tiếp tục PASS 100%.

### Bước 6: Tài liệu hóa và Nhật ký phiên
- Viết nhật ký `docs/journal/2026-10-13-phien-4a-nap-them-quy-che.md` theo đúng mẫu chuẩn.
- Cập nhật tiến độ tại `docs/progress.md`.
- Cập nhật các quyết định nếu có tại `docs/decisions.md`.

---

## 4. Ranh giới an toàn (Hard Barriers)
- Không đọc, in, hiển thị hay sửa đổi file `.env` và các khóa API.
- Không thực hiện các lệnh Git commit/push/branch (chỉ đưa gợi ý cho người dùng).
- Không chạy lệnh phá hủy thư mục hay xóa dữ liệu ngoài phạm vi.
