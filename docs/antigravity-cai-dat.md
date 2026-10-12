# Cài đặt Antigravity cho dự án (làm một lần)

Phần lớn nội dung dưới đây lấy từ tài liệu chính thức của Antigravity và các bài hướng dẫn bên thứ ba. Giao diện và
tên mục có thể khác theo phiên bản, nên mỗi mục có cách tự kiểm tra. Cái gì chưa chắc thì ghi rõ.

## 1. Đặt file quy tắc
- `GEMINI.md` ở thư mục gốc dự án: chắc chắn được đọc. Phiên bản IDE từ 1.20.5 còn đọc cả `AGENTS.md`, nhưng tài liệu
  chưa nêu thứ tự ưu tiên khi có cả hai file ở cùng chỗ, nên **chỉ dùng một file**.
- Workflow `/phien-lam-viec` nằm ở `.agents\workflows\phien-lam-viec.md`. Thư mục `.agents` (số nhiều) là mặc định hiện
  tại, `.agent` (số ít) vẫn được đọc ở dự án cũ. Nếu gõ `/` mà không thấy workflow, thử đổi tên thư mục thành `.agent`.
- Mỗi file rule hoặc workflow giới hạn **12.000 ký tự**. File rule không dùng `@tên-file` để nhúng tài liệu lớn, vì
  nội dung nhúng sẽ tốn ngữ cảnh mỗi lần.
- Thêm `.agents\` vào git (chia sẻ cho cả nhóm). Không đưa khóa API vào các file này.

## 2. Cài đặt agent (Settings, mục Agent)
| Cài đặt | Giá trị khuyên dùng | Vì sao |
|---|---|---|
| Chế độ làm việc | **Planning** | Agent lập Implementation Plan và Task List trước khi sửa mã. Chế độ Fast bỏ qua bước lập kế hoạch |
| Artifact Review Policy | **Request Review** | Khi có kế hoạch hoặc bản sửa, agent dừng và chờ bạn duyệt. Bạn có thể ghi chú trực tiếp vào kế hoạch rồi mới duyệt. Đây là hàng rào do phần mềm thực thi cho quy tắc "dừng sau kế hoạch" |
| Terminal Command Auto Execution | **Request Review** (bản UI cũ gọi là Off) | Lệnh không nằm trong Allow List phải được bạn duyệt |
| Agent Non-Workspace File Access | **Tắt** (mặc định) | Agent chỉ đụng được file trong thư mục dự án |

Không dùng "Always Proceed" cho terminal khi đang làm quen. Deny List chỉ phát huy tác dụng ở chế độ tự chạy lệnh.

## 3. Danh sách lệnh (Allow List và Deny List)
**Allow List** (lệnh chạy không cần hỏi, chỉ nên là lệnh chỉ đọc hoặc an toàn):
```
git status
git diff
git log
dir
venv\Scripts\python.exe --version
venv\Scripts\python.exe -m unittest
venv\Scripts\python.exe -m pip show
```
**Deny List** (chỉ có tác dụng nếu bạn bật tự chạy lệnh): `git push`, `git reset --hard`, `git clean`, `rmdir /s`,
`rd /s`, `del /s`, `del /f`, `format`, `reg delete`.

**Chưa chắc:** tôi chưa tìm thấy tài liệu nói Allow List khớp theo tiền tố hay khớp chính xác, và cách xử lý các lệnh
nối nhau. Hãy tự thử một lần: bảo agent chạy `git status & echo kiemtra`. Nếu nó chạy luôn không hỏi thì Allow List có thể bị
lách bằng cách nối lệnh, khi đó đừng thêm lệnh nào nguy hiểm vào Allow List.

## 4. Terminal mặc định là CMD
Trong Antigravity (nền VS Code): `Ctrl+Shift+P`, gõ `Terminal: Select Default Profile`, chọn `Command Prompt`. Kiểm tra
bằng cách bảo agent chạy `echo %COMSPEC%`: kết quả phải là đường dẫn tới `cmd.exe`. Tôi chưa xác nhận agent luôn dùng
đúng profile mặc định này trong mọi phiên bản, nên hãy kiểm tra.

Đặt UTF-8 một lần cho mọi terminal mở sau đó: `setx PYTHONUTF8 1`, rồi đóng và mở lại terminal.

## 5. Khóa API
- Đặt khóa thành biến môi trường người dùng, không ghi vào `.env`:
  ```
  setx GOOGLE_API_KEY "dán-khóa-ở-đây"
  setx INTERNAL_API_KEY "chuỗi-ngẫu-nhiên-dài"
  ```
  Rồi mở terminal mới. Biến môi trường được ưu tiên hơn `.env` (cấu hình của AI Service đọc cả hai), nên file `.env`
  chỉ cần các giá trị không bí mật. Ghi `.env` vào `.gitignore`.
- **Giới hạn:** `setx` lưu khóa dạng chữ thường trong thông tin người dùng của Windows, đủ cho môi trường phát triển
  nhưng không phải kho bảo mật. Agent vẫn có thể in khóa nếu bạn duyệt một lệnh như `set` hoặc `echo %GOOGLE_API_KEY%`,
  vì vậy **đọc kỹ từng lệnh trước khi bấm duyệt**. Đừng gõ khóa trong khung chat.

## 6. Thử các "cổng chặn" trước khi tin tưởng
1. Giao một việc nhỏ ở chế độ Planning, xem agent có dừng ở kế hoạch và chờ duyệt không.
2. Bảo agent chạy một lệnh nằm trong Allow List (`git status`) và một lệnh ngoài danh sách (ví dụ `type GEMINI.md`):
   lệnh đầu chạy ngay, lệnh sau phải hỏi.
3. Thử lệnh nối ở mục 3.
4. Nếu bất kỳ cổng nào không dừng như mong đợi, thêm nhắc nhở vào GEMINI.md và đừng giao việc dài cho agent cho tới
   khi hiểu rõ nguyên nhân.

## 7. Nếu bạn dùng Antigravity CLI (lệnh `agy`) thay cho IDE
Các nguồn tôi đọc (bên thứ ba, chưa đối chiếu tài liệu chính thức) mô tả quyền được khai báo trong
`%USERPROFILE%\.gemini\antigravity-cli\settings.json` với ba danh sách allow, ask, deny, thứ tự ưu tiên deny > ask >
allow. Ví dụ tham khảo, cần kiểm tra cú pháp với tài liệu hiện hành:
```json
{
  "permissions": {
    "deny": ["command(git push)", "command(git reset --hard)", "command(rmdir /s)", "command(del /s)"],
    "ask": ["command(*)"]
  }
}
```

## 8. `.gitignore` gợi ý
```
.env
ai-service/venv/
ai-service/data/qdrant_local/
ai-service/data/chunks*.jsonl
ai-service/data/cache/
__pycache__/
```
