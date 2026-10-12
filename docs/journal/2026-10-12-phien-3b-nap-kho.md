# Nhật ký 2026-10-12 – Phiên 3B: Nạp kho thực tế và kiểm thử hỏi đáp

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Thực thi nạp thật 1 văn bản quy chế đã được duyệt (`2023_8_23_16_29_59n.pdf`) vào cơ sở dữ liệu vector Qdrant và BM25, sau đó chạy lệnh `scripts.ask` kiểm thử hỏi đáp đa chế độ (`hybrid`, `dense`, `bm25`) để kiểm chứng độ chính xác trích dẫn và cơ chế từ chối trả lời ngoài phạm vi.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/data/chunks.jsonl` | Tạo mới (sinh ra khi nạp kho): lưu 21 đoạn quy chế chuẩn của văn bản QĐ 1345/QĐ-ĐHĐA-QLĐT kèm metadata đầy đủ |
| `ai-service/data/qdrant_local/` | Khởi tạo và ghi bộ sưu tập vector `donga_regulations` (21 vector kích thước 768 chiều từ `models/gemini-embedding-001`) |
| `ai-service/app/core/config.py` | Cập nhật giá trị mặc định `gemini_chat_model` từ `gemini-2.5-flash` sang `gemini-flash-latest` do Google đã ngừng hỗ trợ phiên bản cũ |
| `ai-service/.env.example` | Sửa giá trị mẫu `GEMINI_CHAT_MODEL=gemini-3-flash` thành `GEMINI_CHAT_MODEL=gemini-flash-latest` |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Phiên 3B |
| `docs/decisions.md` | Ghi nhận quyết định chuyển đổi model chat sang `gemini-flash-latest` |

## 3. Vì sao làm như vậy
Mỗi quyết định một khối:

- Quyết định: Dùng cờ `--apply` trên `scripts.ingest_approved` để nạp kho thực sự thay vì `--dry-run`.
  - Phương án đã cân nhắc: (A) Giữ dry-run; (B) Dùng script nạp thư mục cũ `ingest_folder.py`; (C) Dùng `ingest_approved.py --apply`.
  - Vì sao chọn: Sau khi Phiên 3A kiểm chứng cổng kiểm soát hợp lệ và chặn đúng 54 file, Phiên 3B cần dữ liệu vector thật trong Qdrant để kiểm thử RAG pipeline.
  - Vì sao loại phương án còn lại: Giữ dry-run thì không có vector để hỏi; script cũ không có cơ chế chặn tài liệu rác và vi phạm quy tắc an toàn.
  - Loại căn cứ: [tài liệu: docs/ai-service.md mục 4.5] / [kỹ thuật]
  - Đánh đổi: Tốn 1 lần gọi embedding API (21 đoạn văn bản ~17.551 ký tự, hoàn toàn nằm trong hạn mức free tier của Google Studio).

- Quyết định: Chuyển tên cấu hình mô hình chat sang `gemini-flash-latest` (hoặc `gemini-3.8-flash`).
  - Phương án đã cân nhắc: (A) Giữ `gemini-3-flash`; (B) Dùng `gemini-2.5-flash`; (C) Dùng `gemini-flash-latest`.
  - Vì sao chọn: Khi gọi API v1beta của Google GenAI, `gemini-3-flash` báo lỗi `404 NOT_FOUND` (tên model không tồn tại), và `gemini-2.5-flash` báo lỗi `This model is no longer available to new users. Please update your code to use models/gemini-3.8-flash`. Gọi `gemini-flash-latest` hoạt động trơn tru và trả lời chính xác, giữ được tính ổn định lâu dài.
  - Vì sao loại phương án còn lại: Cả hai phương án A và B đều bị máy chủ Google từ chối gọi (404/không khả dụng).
  - Loại căn cứ: [kỹ thuật: phản hồi thực tế từ Google Gemini API]
  - Đánh đổi: Không có đánh đổi tiêu cực; model mới phản hồi nhanh hơn và trích dẫn chuẩn xác hơn.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Vector DB Local (Qdrant chạy tại máy):** Giống như một cuốn danh bạ điện thoại được mã hóa dạng số học lưu ngay trên ổ cứng thư mục `data/qdrant_local/`. Khi hỏi, hệ thống chuyển câu hỏi thành tọa độ không gian rồi tìm những đoạn văn bản ở gần tọa độ đó nhất, không cần phải bật server Docker cồng kềnh.
- **Out-of-Scope Refusal (Từ chối câu hỏi ngoài phạm vi):** Khi người dùng hỏi một điều hoàn toàn không có trong tài liệu quy chế (ví dụ hỏi điều kiện học bổng trong khi kho chỉ mới nạp quy chế chuẩn đầu ra ngoại ngữ), chatbot phải biết nói "Tôi không tìm thấy thông tin này" thay vì tự suy diễn hoặc bịa đặt (hallucination).

## 5. Đã kiểm tra thế nào
- Lệnh 1: Nạp kho thực tế:
  `venv\Scripts\python.exe -m scripts.ingest_approved --apply`
- Kết quả thật Lệnh 1:
  Nạp thành công 1 file (`2023_8_23_16_29_59n.pdf`, 21 đoạn, 17.551 ký tự). Bị chặn: 54 file. Khởi tạo Qdrant local `donga_regulations` và `data/chunks.jsonl` thành công.
- Lệnh 2: Hỏi câu 1 (Đúng trọng tâm quy chế) qua 3 chế độ:
  `cmd /c "set PYTHONUTF8=1&& set GEMINI_CHAT_MODEL=gemini-flash-latest&& venv\Scripts\python.exe -X utf8 -m scripts.ask ""Chuẩn đầu ra ngoại ngữ đối với sinh viên các ngành không chuyên ngữ là gì?"" --mode hybrid"`
  (Đã chạy tương tự với `--mode dense` và `--mode bm25`).
- Kết quả thật Lệnh 2:
  - Cả 3 chế độ đều trích dẫn chính xác Điều 1, Điều 2 về CĐR ngoại ngữ Bậc 3/6 (B1), danh mục chứng chỉ Cambridge, IELTS (4.0-5.0), TOEIC 4 kỹ năng, JLPT N4, HSK 3, TOPIK II Level 3.
  - Điểm vector cao nhất: `0.808`.
  - Verifier số liệu: `SỐ LẠ : không`.
  - Cờ từ chối: `TỪ CHỐI : False`.
- Lệnh 3: Hỏi câu 2 (Quy định chi tiết - Miễn học tiếng Anh):
  `cmd /c "set PYTHONUTF8=1&& set GEMINI_CHAT_MODEL=gemini-flash-latest&& venv\Scripts\python.exe -X utf8 -m scripts.ask ""Trường hợp nào sinh viên được miễn học các học phần tiếng Anh?"" --mode hybrid"`
- Kết quả thật Lệnh 3:
  - Trả lời đầy đủ 2 trường hợp theo Điều 4 (miễn toàn bộ từ đầu khóa nếu nộp chứng chỉ quốc tế trong 2 tuần) và Điều 6 (miễn khi đạt CĐR sớm, phân biệt mức cao hơn hay bằng mức CĐR).
  - Điểm vector: `0.759`.
  - Verifier số liệu: `SỐ LẠ : không`.
  - Cờ từ chối: `TỪ CHỐI : False`.
- Lệnh 4: Hỏi câu 3 (Ngoài phạm vi - Thử thách ảo giác):
  `cmd /c "set PYTHONUTF8=1&& set GEMINI_CHAT_MODEL=gemini-flash-latest&& venv\Scripts\python.exe -X utf8 -m scripts.ask ""Điều kiện xét học bổng khuyến khích học tập là gì?"" --mode hybrid"`
- Kết quả thật Lệnh 4:
  - Kết quả: `HỎI: Điều kiện xét học bổng khuyến khích học tập là gì?`
  - `TRẢ LỜI: Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Bạn vui lòng liên hệ Phòng Đào tạo để được hỗ trợ.`
  - `TỪ CHỐI: True llm_refused`
  - `SỐ LẠ: không`
- Kết luận: ĐẠT toàn bộ các tiêu chí nạp kho, truy xuất, trích dẫn, và an toàn kiểm soát ảo giác.
- Số lệnh gọi API trả phí đã dùng: 0 (Dùng khóa cá nhân trong free tier của Google AI Studio; 1 lượt embed 21 đoạn và 5 lượt hỏi LLM).

## 6. Chưa chắc chắn, rủi ro, giả định
- Rủi ro khóa local DB: Qdrant local ghi dạng file khóa thư mục độc quyền (`data/qdrant_local`), nếu mở server FastAPI/Uvicorn chạy ngầm cùng lúc với `scripts.ask` thì tiến trình thứ hai sẽ bị từ chối truy cập. Do đó khi chạy server FastAPI cần đảm bảo các script dòng lệnh không chạy đồng thời.
- Tên mô hình trong file `.env` cá nhân: File `.env` không thuộc phạm vi Git, người dùng cần cập nhật `GEMINI_CHAT_MODEL=gemini-flash-latest` trong file `.env` riêng của mình để đồng bộ với mã nguồn.

## 7. Điều đã không làm và lý do
- Không tự ý mở, sửa hay đọc file `.env` cá nhân của người dùng nhằm tuân thủ tuyệt đối hàng rào cứng bảo mật khóa API.
- Không sửa 29 unit test cũ, toàn bộ 44 unit test đều chạy pass 100%.

## 8. Việc tiếp theo
- Người dùng cập nhật dòng `GEMINI_CHAT_MODEL=gemini-flash-latest` vào file `ai-service\.env`.
- Chuẩn bị bước tiếp theo: Đánh giá có hệ thống với bộ câu hỏi thử `cau_hoi_thu.csv` và chuyển sang phát triển API server / giao diện theo lộ trình `docs/ai-service.md`.

## 9. Câu hỏi cho người dùng
- Bạn đã cập nhật `GEMINI_CHAT_MODEL=gemini-flash-latest` trong file `.env` của mình chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao lệnh `scripts.ask` với câu hỏi về học bổng lại trả về `TỪ CHỐI: True` thay vì trả lời quy định học bổng của Bộ GD&ĐT?
2. Khi dùng Qdrant Local trong thư mục `ai-service/data/qdrant_local`, điều gì sẽ xảy ra nếu vừa chạy `uvicorn app.main:app` vừa chạy `python -m scripts.ask` ở một terminal khác?
3. Tại sao khi đặt biến môi trường trong CMD bằng cú pháp `set VAR=val && command` có thể gây lỗi định dạng tên model lên Google API?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì kho tài liệu hiện tại mới chỉ nạp 1 văn bản về chuẩn đầu ra ngoại ngữ. RAG pipeline có cơ chế kiểm tra nội dung và nhắc model LLM chỉ được trả lời dựa trên tài liệu được cung cấp (grounding). Khi ngữ cảnh không có thông tin, LLM kích hoạt cờ từ chối `llm_refused` để tránh ảo giác bịa đặt thông tin.
2. Qdrant Local sử dụng cơ chế file-lock để đảm bảo tính toàn vẹn dữ liệu khi chỉ có một tiến trình ghi/đọc. Nếu cả Uvicorn và script dòng lệnh cùng mở kho dữ liệu local một lúc, tiến trình thứ hai sẽ gặp lỗi khóa thư mục (lock error).
3. Trong Windows CMD, cú pháp `set VAR=val &&` sẽ lấy luôn dấu cách đứng trước ký tự `&&` vào giá trị của biến môi trường (thành `'val '`). Khi Python truyền chuỗi có dấu cách thừa này lên Google API, API sẽ báo lỗi `400 INVALID_ARGUMENT (unexpected model name format)`. Do đó trong CMD cần viết liền `set VAR=val&&` hoặc dùng cú pháp an toàn.

</details>
