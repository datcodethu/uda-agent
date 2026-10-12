# Kế hoạch Phiên 3B: Nạp thật tài liệu vào kho vector và hỏi thử nghiệm

## 1. Hiểu nhiệm vụ

- **Mục tiêu:** Kích hoạt nạp thật tài liệu đã duyệt `2023_8_23_16_29_59n.pdf` (Quyết định 1345/QĐ-ĐHĐA-QLĐT về Chuẩn đầu ra ngoại ngữ) vào cơ sở dữ liệu vector Qdrant và chỉ mục BM25 qua script `ingest_approved.py` với cờ `--apply`.
- **Nghiệm thu:** Xác minh tính toàn vẹn dữ liệu (file `chunks.jsonl`, vector collection Qdrant) và thực nghiệm hỏi đáp thực tế với script `ask.py` trên 3 chế độ tìm kiếm (`dense`, `bm25`, `hybrid`).
- **Giả định:** Người dùng đã cấu hình `GOOGLE_API_KEY` hợp lệ trong `ai-service\.env`, Qdrant chạy ở chế độ local tại `ai-service/data/qdrant_local/`.

---

## 2. Dự toán chi phí API (Tuân thủ Quy tắc Chi phí)

| Thao tác                                         | Số văn bản / câu hỏi      | Số lệnh gọi Embedding | Số lệnh gọi LLM Chat | Tổng lệnh gọi       |
| ------------------------------------------------ | ------------------------- | --------------------- | -------------------- | ------------------- |
| Khởi tạo collection Qdrant                       | 1 chuỗi kiểm tra số chiều | 1                     | 0                    | 1                   |
| Nạp 21 đoạn văn bản (batch 50)                   | 1 file (21 đoạn)          | 1 batch (21 passages) | 0                    | 1                   |
| Hỏi thử câu 1 (Chuẩn đầu ra tiếng Anh)           | 1 câu                     | 1                     | 1                    | 2                   |
| Hỏi thử câu 2 (Miễn học / chứng chỉ quốc tế)     | 1 câu                     | 1                     | 1                    | 2                   |
| Hỏi thử câu 3 (Ngoài phạm vi - kiểm tra từ chối) | 1 câu                     | 1                     | 1                    | 2                   |
| **Tổng cộng dự kiến**                            | -                         | **4 lượt gọi**        | **3 lượt gọi**       | **~7 lượt gọi API** |

> Tổng số lượt gọi API thực tế ước tính chỉ **khoảng 7 lượt gọi**, thấp hơn rất nhiều so với ngưỡng cảnh báo 50 lượt gọi của dự án, hoàn toàn an toàn và nằm trong hạn mức miễn phí.

---

## 3. Các bước triển khai chi tiết

### Bước 1: Nạp dữ liệu thật vào Qdrant & BM25

- **Lệnh thực thi:**
  ```powershell
  venv\Scripts\python.exe -m scripts.ingest_approved --apply
  ```
- **Kết quả kỳ vọng:**
  - Nạp thành công: `1 file` (`2023_8_23_16_29_59n.pdf`, 21 đoạn cắt, 17.551 ký tự).
  - Bị chặn: `54 file` còn lại (do `da_duyet = false`).
  - Dữ liệu phát sinh:
    - `ai-service/data/chunks.jsonl` được tạo mới với đúng 21 dòng JSON.
    - `ai-service/data/qdrant_local/` được khởi tạo và lưu trữ 21 vector điểm cùng payload metadata.

### Bước 2: Kiểm tra toàn vẹn dữ liệu trên đĩa

- Kiểm tra số lượng bản ghi trong `data/chunks.jsonl` (phải đúng 21 bản ghi).
- Kiểm tra cấu trúc metadata của từng chunk: bảo đảm chứa đầy đủ `doc_title`, `status="ACTIVE"`, và không bị ghi đè các trường cốt lõi.

### Bước 3: Thực nghiệm hỏi thử với `scripts/ask.py`

Chạy thử nghiệm 3 câu hỏi đại diện trên chế độ lai (`--mode hybrid`):

1. **Câu hỏi trực diện:**
   ```powershell
   venv\Scripts\python.exe -m scripts.ask "Chuẩn đầu ra ngoại ngữ đối với sinh viên các ngành không chuyên ngữ là gì?" --mode hybrid
   ```
   _Kỳ vọng:_ LLM trích xuất đúng Điều trong văn bản, trả lời chính xác bậc năng lực / chứng chỉ yêu cầu, có trích dẫn nguồn số hiệu văn bản và điểm vector cao.
2. **Câu hỏi chi tiết / tra cứu điều kiện:**
   ```powershell
   venv\Scripts\python.exe -m scripts.ask "Trường hợp nào sinh viên được miễn học các học phần tiếng Anh?" --mode hybrid
   ```
   _Kỳ vọng:_ LLM liệt kê đúng các trường hợp miễn học theo quy định.
3. **Câu hỏi ngoài phạm vi (Kiểm tra chống bịa đặt / Hallucination):**
   ```powershell
   venv\Scripts\python.exe -m scripts.ask "Điều kiện xét học bổng khuyến khích học tập là gì?" --mode hybrid
   ```
   _Kỳ vọng:_ Hệ thống báo `TỪ CHỐI : True` hoặc LLM trả lời rõ ràng là không tìm thấy thông tin trong tài liệu được cung cấp.

### Bước 4: So sánh nhanh 3 chế độ tìm kiếm

Chạy câu hỏi 1 trên cả 3 chế độ (`--mode dense`, `--mode bm25`, `--mode hybrid`) để so sánh điểm số và thời gian phản hồi.

### Bước 5: Ghi chép & Báo cáo

- Viết nhật ký `docs/journal/2026-10-12-phien-3b-nap-kho.md` theo mẫu chuẩn.
- Cập nhật tiến độ `docs/progress.md` và `docs/decisions.md`.
- Báo cáo kết quả 5 đề mục trong khung chat.

---

## 4. Bảng quyết định thiết kế

| Quyết định                                 | Phương án đã cân nhắc                                           | Vì sao chọn                                                                              | Loại căn cứ                              |
| ------------------------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| Nạp 1 file thẩm định trước thay vì toàn bộ | 1. Nạp tất cả 55 file; 2. Nạp 1 file đã kiểm duyệt (chọn)       | Tránh nạp tài liệu chưa qua kiểm duyệt học vụ, tiết kiệm hạn mức API, kiểm soát toàn vẹn | [tài liệu: docs/agent-workflow.md mục 8] |
| Kiểm tra đồng thời câu hỏi ngoài phạm vi   | 1. Chỉ hỏi câu có trong bài; 2. Hỏi cả câu ngoài phạm vi (chọn) | Xác minh tính năng chống ảo giác (Grounding) của prompt RAG trước khi mở rộng            | [kỹ thuật]                               |
| Lưu Qdrant local tại `data/qdrant_local`   | 1. Dùng Docker; 2. Dùng local file (chọn)                       | Đơn giản, không phụ thuộc Docker daemon trên máy Windows sinh viên                       | [tài liệu: docs/ai-service.md mục 5.3]   |

---

## 5. Rủi ro và biện pháp phòng ngừa

- **Rủi ro 1: Lỗi khóa API / Hết hạn mức (Quota Exceeded):**
  - _Biện pháp:_ Bắt lỗi chi tiết từ SDK Google GenAI, thông báo rõ ràng mã lỗi nếu quota bị chạm.
- **Rủi ro 2: Khóa Qdrant local khi có tiến trình khác đang mở:**
  - _Biện pháp:_ Đảm bảo không có server `uvicorn` hay tiến trình Python nào khác đang giữ lock thư mục `qdrant_local`.
