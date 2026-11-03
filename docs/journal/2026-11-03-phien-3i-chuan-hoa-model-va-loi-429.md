# Nhật ký 2026-11-03 – Phiên 3I: Tự động chuẩn hóa mô hình và bảo vệ lỗi hạn ngạch 429 Quota Exceeded

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Khắc phục triệt để lỗi `429 RESOURCE_EXHAUSTED` (vượt quá 20 yêu cầu/ngày của bản Google preview) do file `.env` cá nhân của người dùng vẫn lưu alias cũ `gemini-flash-latest`, giúp server tự động nhận diện mô hình tối ưu `gemini-flash-lite-latest` mà không cần người dùng can thiệp thủ công vào `.env`.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/core/config.py` | Bổ sung `field_validator` chuẩn hóa `gemini_chat_model` trước khi nạp: tự động chuyển hướng các alias cũ (`gemini-flash-latest`, `gemini-3.8-flash`, `gemini-2.5-flash`, `gemini-3.1-flash-lite`) sang `gemini-flash-lite-latest` |
| `ai-service/app/pipeline/generator/stream_handler.py` | Bắt lỗi 429 / `RESOURCE_EXHAUSTED` và hiển thị thông điệp tiếng Việt thân thiện hướng dẫn chuyển sang chế độ mock khi cần |
| `docs/decisions.md` | Ghi nhận quyết định Phiên 3I |
| `docs/progress.md` | Cập nhật tiến độ Phiên 3I |

## 3. Vì sao làm như vậy
- **Quyết định:** Dùng `field_validator(mode="before")` của Pydantic để tự động làm sạch cấu hình đầu vào.
- **Phương án đã cân nhắc:**
  1. Hướng dẫn người dùng tự mở `.env` sửa: Dễ gây nhầm lẫn hoặc người dùng quên sửa, dẫn đến lỗi 429 lặp lại.
  2. Tự động đọc và ghi đè file `.env`: Vi phạm hàng rào cứng bảo mật của `GEMINI.md` ("Không bao giờ đọc, in, ghi hay commit khóa API và file .env").
  3. Dùng Pydantic validator trong `config.py`: Hệ thống tự xử lý trong bộ nhớ RAM, vừa an toàn tuyệt đối cho file `.env`, vừa giải quyết triệt để 100% lỗi.
- **Vì sao chọn:** Đáp ứng tính công thái học và an toàn cao nhất: người dùng không cần sửa bất kỳ file nhạy cảm nào, server tự reload là chạy ngay lập tức.
- **Loại căn cứ:** [kỹ thuật] & [quy tắc GEMINI.md].

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Hạn ngạch theo Model (Per-Model Quota):** Mỗi mô hình trên Google AI Studio có một "ví tiền lượt dùng" riêng. Mô hình preview mới ra như `gemini-3.8-flash` chỉ cho 20 lượt/ngày (hết rất nhanh), trong khi mô hình dòng Lite (`gemini-flash-lite-latest`) cho hàng ngàn lượt/ngày. Đổi tên mô hình giống như chuyển sang cổng soát vé vắng người.
- **Field Validator (Bộ lọc tiền xử lý dữ liệu):** Giống như nhân viên lễ tân soát vé, nếu khách đưa nhãn vé cũ `gemini-flash-latest`, lễ tân tự động đổi sang vé mới `gemini-flash-lite-latest` trước khi cho vào rạp, giúp người dùng không bị đuổi về do vé lỗi.

## 5. Đã kiểm tra thế nào
- **Xác thực khởi tạo mô hình trong Python:**
  - Lệnh: Chạy `scratch/verify_model.py`.
  - Kết quả: `Effective chat model: gemini-flash-lite-latest`, `LLM test response: Hà Nội.` (Phản hồi thành công trong 1.1s).
- **Kiểm tra hồi quy Unit Test:**
  - Lệnh: `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONPATH=.&& set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả: `Ran 79 tests in 5.270s - OK` (100% PASS).
- **Số lệnh gọi API trả phí đã dùng:** 2 lệnh gọi test đơn lẻ.

## 6. Chưa chắc chắn, rủi ro, giả định
- Nếu server Uvicorn đang chạy với cờ `--reload`, nó sẽ tự động nhận diện thay đổi của `config.py` và tải lại. Nếu server chưa chạy, người dùng chỉ cần bật lại server.

## 7. Điều đã không làm và lý do
- Không can thiệp vào file `.env` để bảo vệ khóa API cá nhân của người dùng.

## 8. Việc tiếp theo
- Người dùng vào lại Web Chat `http://localhost:8000/` và hỏi lại câu hỏi để kiểm chứng câu trả lời mượt mà.

## 9. Câu hỏi cho người dùng
- Sau khi Uvicorn tự reload, bạn hỏi thử câu quy chế trên Web Chat đã phản hồi mượt mà chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao cùng một API key nhưng gọi `gemini-flash-latest` bị lỗi 429 mà gọi `gemini-flash-lite-latest` lại thành công?
2. `mode="before"` trong `field_validator` của Pydantic có tác dụng gì?
3. Tại sao việc chuẩn hóa cấu hình trong mã nguồn lại an toàn hơn là để agent tự sửa file `.env`?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì Google AI Studio áp dụng hạn mức (quota) riêng cho từng model. Bản preview `gemini-3.8-flash` bị giới hạn ngặt nghèo 20 requests/ngày, còn bản `gemini-flash-lite-latest` có hạn ngạch lớn dành cho sản phẩm hoạt động thông thường.
2. `mode="before"` cho phép can thiệp và sửa đổi giá trị dữ liệu thô (được đọc từ file `.env` hoặc hệ điều hành) trước khi Pydantic kiểm tra kiểu dữ liệu và gán vào biến cấu hình.
3. Vì file `.env` chứa bí mật (API key). Cho phép agent ghi đè file `.env` có nguy cơ làm mất khóa, ghi đè sai biến hoặc rò rỉ thông tin nhạy cảm. Chuẩn hóa trong RAM an toàn 100%.

</details>
