# Quy trình làm việc của agent (Antigravity, CMD)

File này là quy trình chi tiết. GEMINI.md chỉ giữ phần cốt lõi, workflow `/phien-lam-viec` tóm tắt các bước A đến F.
Biến theo phiên (bước nào, dữ liệu nào) đặt trong tin nhắn giao việc, không đặt trong GEMINI.md.

## 1. Đầu mỗi phiên
1. Đọc GEMINI.md, docs/progress.md, docs/decisions.md.
2. Phiên đầu tiên: chạy `echo %COMSPEC%`, `ver`, `venv\Scripts\python.exe --version`, ghi kết quả vào docs/decisions.md.
   Nếu `echo %COMSPEC%` in nguyên chữ `%COMSPEC%` thì terminal không phải CMD: dừng lại và báo tôi.

## 2. Phạm vi và file ghi chép
Mã và dữ liệu: chỉ sửa trong phạm vi bước được giao.
Các file ghi chép sau luôn được phép tạo hoặc cập nhật, **không tính là ngoài phạm vi**:
docs/journal/, docs/plans/, docs/progress.md, docs/decisions.md, docs/todo.md.
Cuối phiên liệt kê mọi file đã đổi.

## 3. Test
- Test do chính bạn tạo trong phiên này: được sửa khi sai, ghi lý do vào nhật ký.
- Test hoặc dữ liệu có từ trước, và mọi thứ trong evaluation/test_datasets/: không sửa. Nếu nghi sai, báo kèm bằng
  chứng và đề xuất cách sửa rồi chờ tôi duyệt.
- Không hạ ngưỡng, không xóa assert để cho test pass.

## 4. Thư viện mới
Chỉ được đề xuất trong kế hoạch bước B. Sau khi tôi duyệt mới cài, rồi thêm vào requirements.txt (ghim phiên bản
đã cài) và ghi vào docs/decisions.md.

## 5. Trích dẫn căn cứ
Chỉ trích những phần bạn đã mở đọc trong phiên này, ghi theo tên file và tên tiêu đề (số mục dễ đổi nên không dựa
vào số). Không có căn cứ trong tài liệu thì ghi "giả định của agent" và nêu lý do. Không đoán tên model, hàm, tham số
thư viện: kiểm tra bằng `venv\Scripts\python.exe -m pip show <tên>`, `--help` hoặc tài liệu chính thức.

## 6. Git
Được chạy các lệnh chỉ đọc: `git status`, `git diff`, `git log`, `git show`.
Không chạy: commit, push, tạo hoặc chuyển nhánh, merge, rebase, reset, stash, checkout file.
Cuối phiên đưa danh sách file đã đổi và gợi ý nội dung commit để tôi tự commit.

## 7. Toàn vẹn thí nghiệm (quan trọng cho báo cáo khoa học)
1. **Chia tập một lần, trước lần đánh giá đầu tiên.** Mỗi câu trong bộ kiểm thử có trường `"split"` là `"dev"` hoặc
   `"test"`. Gợi ý khoảng 60 dev, 40 test, chia phân tầng theo bốn nhóm câu hỏi. Chia xong không đổi.
2. **Mọi việc chỉnh tham số chỉ dựa trên tập dev:** prompt, ngưỡng, regex cắt đoạn, chunk size, top_k, bảng viết tắt.
3. **Tập test chỉ chạy cho kết quả cuối**, mỗi cấu hình đã chốt một lần. Không chỉnh gì sau khi xem kết quả test.
   Nếu buộc phải chỉnh, ghi rõ trong nhật ký và coi tập test đã bị lộ.
4. **Ghi cấu hình mỗi lần chạy:** git commit hiện tại, ngày giờ, tên model chat và embedding, nhiệt độ, chiến lược và
   kích thước cắt đoạn, top_k, candidate_k, MIN_DENSE_SCORE, mode, tên collection, tên và phiên bản file dữ liệu kiểm
   thử, tập (dev hoặc test), số câu, phiên bản các thư viện chính.
5. Mô hình ngôn ngữ không hoàn toàn xác định ngay cả khi nhiệt độ bằng 0. Với cấu hình cuối, chạy lặp ba lần nếu
   ngân sách cho phép và báo cả mức dao động.
6. Mô hình giám khảo (ví dụ khi chấm bằng RAGAS): ghi rõ tên. Nếu được, dùng mô hình khác mô hình sinh câu trả lời.
7. Không xóa kết quả chạy xấu. Lưu mọi lần chạy trong evaluation\benchmarks_result\.
8. Chỉ có khoảng 40 câu test nên khoảng tin cậy rộng: báo "số câu đúng trên tổng số câu", không chỉ phần trăm.

## 8. Chi phí API
1. Ưu tiên cách miễn phí: đánh giá truy xuất (`run_eval` không có `--with-llm`) và `LLM_PROVIDER=mock`.
2. Trước mọi lần chạy hàng loạt gọi API trả phí (`--with-llm`, RAGAS, nạp embedding lớn): tính số lệnh gọi
   (số câu x số lệnh gọi mỗi câu x số cấu hình), báo cho tôi. Từ 50 lệnh gọi trở lên thì chờ tôi đồng ý.
   (Ngưỡng 50 là gợi ý ban đầu, sửa theo hạn mức thật.)
3. Thứ tự chạy: mock, rồi 5 đến 10 câu mẫu, rồi toàn bộ.
4. Dùng cache theo mã băm (model + prompt) trong data\cache\ (đã gitignore) cho các lần chạy lặp.
5. Ghi số lệnh gọi thực tế vào nhật ký.

## 9. CMD và tiếng Việt
- **Gọi Python bằng đường dẫn đầy đủ trong venv:** `venv\Scripts\python.exe -m ...`. Agent có thể mở terminal mới cho
  mỗi lệnh nên việc "đã kích hoạt venv" không đáng tin. Cách này tránh lỗi `No module named ...`.
- Nối lệnh: `lệnh1 && lệnh2` (chạy lệnh 2 nếu lệnh 1 thành công). Dấu `;` **không** nối lệnh trong CMD.
- Đặt biến môi trường cho cửa sổ hiện tại: `set "TEN=giatri"` (bắt buộc có dấu ngoặc kép bao quanh, nếu không
  `set TEN=a && lệnh` sẽ thêm dấu cách thừa vào cuối giá trị). Xóa biến: `set TEN=`.
- UTF-8: đặt một lần `setx PYTHONUTF8 1` rồi mở terminal mới. Mỗi phiên có thể thêm `chcp 65001 >nul`.
- Trong mã luôn đọc và ghi file với `encoding="utf-8"`.
- Chỉ dấu `"` là dấu trích dẫn. Lệnh `python -c "..."` dài dễ hỏng: lưu thành file .py rồi chạy.
- Xuống dòng khi gõ lệnh dài dùng `^` ở cuối dòng. Ghi chú dùng dòng `REM ...`, không dùng `#` cuối dòng lệnh.
- `curl` trong CMD là `curl.exe` có sẵn của Windows 10 trở lên. Trong file `.bat`, ký tự `%` phải viết `%%`.
- Tìm chữ trong file: `findstr /s /n /i "chữ" *.py`. Xem file: `type tenfile`. Thư mục hiện tại: `%cd%`.
- Không chạy bare `set` hay `echo %TEN_KHOA%`: lệnh in ra toàn bộ biến môi trường, gồm cả khóa API.

## 10. Nhật ký và báo cáo cuối
**Nhật ký** (docs/journal/..., tối đa khoảng một trang): tiếng Việt dễ hiểu. Khái niệm mới giải thích bằng ví dụ đời
thường trước khi dùng thuật ngữ. Mỗi quyết định thiết kế ghi: phương án đã cân nhắc, lý do chọn, lý do loại, đánh đổi,
loại căn cứ. Chi tiết dài để ở chú thích mã hoặc docs/decisions.md. Cuối nhật ký có ba câu tự kiểm tra, **đáp án đặt
trong khối gập ở cuối file** để tôi tự nghĩ trước.

**Báo cáo cuối trong khung chat**: năm đề mục cố định như trong workflow `/phien-lam-viec`.

## 11. Mẫu tin nhắn giao việc (gõ trong ô chat của Antigravity)
```
/phien-lam-viec Bước 3 và Bước 4 của docs/ai-service.md (đọc, làm sạch, cắt đoạn theo Điều).
Dữ liệu: data\raw_documents\ (tài liệu thật). Có người, hỏi được.
Ràng buộc riêng phiên này: Qdrant local, LLM_PROVIDER=mock, không gọi API trả phí.
```
