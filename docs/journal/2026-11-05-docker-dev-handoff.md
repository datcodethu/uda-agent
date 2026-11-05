# Nhật ký 2026-11-05 — Đóng gói bản demo để dev khác chạy thử

## 1. Mục tiêu

Dev nhận repository có thể chạy chatbot bằng Docker Compose, sử dụng kho demo đã
có mà không phải cài Python hoặc nạp lại embedding.

## 2. Đã làm gì

| File | Thay đổi |
| --- | --- |
| `docker-compose.yml` | Một AI Service, healthcheck, cổng localhost, named volume và snapshot mount chỉ đọc. |
| `.env.example` | Cấu hình mẫu riêng ở gốc repo; không chứa khóa thật. |
| `ai-service/Dockerfile` | Thêm scripts/tests, đường dẫn storage và lệnh khởi tạo trước Uvicorn. |
| `ai-service/.dockerignore` | Chỉ cho mã nguồn và seed từ viết tắt vào build context. |
| `ai-service/scripts/docker_start.py` | Copy snapshot vào volume trống, đối chiếu ID/payload vector với JSONL; từ chối ghi đè dữ liệu chưa rõ trạng thái. |
| `ai-service/tests/test_docker_start.py` | Kiểm tra seed thật, restart không ghi đè và từ chối volume thiếu dữ liệu. |
| `README.md`, `ai-service/README.md` | Hướng dẫn setup, chạy, thử API/SSE, nhóm test, logs, restart/reset, mock và xử lý lỗi. |

## 3. Vì sao làm như vậy

- Chọn Qdrant local giống bản demo hiện tại, thay vì dựng Qdrant server ngay: dùng
  được cặp dữ liệu snapshot đã có trong Git, không phải gọi API để nhúng lại 103 chunks.
  Đánh đổi: chỉ chạy một instance/worker; không phải cấu hình production.
- Dùng named volume riêng thay vì mount kho đang làm việc của tác giả: dev có thể
  nạp/gỡ tài liệu thử nghiệm mà không thay đổi bản snapshot nguồn.
- Tách file cấu hình Compose ở gốc; không copy hay đọc file `.env` hiện có để bàn giao.
- Không thay đổi hợp đồng API, thuật toán RAG, model mặc định hoặc test có từ trước.
- Căn cứ: `docs/plan.md` (kiến trúc), `docs/ai-service.md` (đóng gói Docker), mã hiện tại
  và tài liệu chính thức Docker được dẫn trong README. Đây là bản dev chạy standalone,
  trước giai đoạn ghép Spring Boot.

## 4. Khái niệm

Image giống bộ cài; container là phiên bản đang chạy; volume là nơi giữ kho tài liệu
sau khi container bị tạo lại. Volume này không giữ session chat đang nằm trong RAM.

## 5. Kiểm tra thực tế

- `python -m unittest tests.test_docker_start -v`: 3/3 PASS; seed thật xác nhận
  103 chunks và khởi động lại không ghi đè thay đổi của dev.
- `python -m unittest discover -s tests -v`: chạy 159 test, OK, skipped=1.
  Suite hiện có một test benchmark phát sinh Gemini Embedding HTTP 200; vì vậy
  không quảng bá toàn bộ suite là offline. Có ít nhất 1 lời gọi API embedding được
  quan sát trong log, không chạy batch ingest hay benchmark trả lời bằng LLM.
- Thử nhóm test ghi trong README ở thư mục tạm, chỉ sao chép nội dung tương ứng image,
  không có `.env`, đặt Google key rỗng: 28 test, OK, skipped=1. Test snapshot thật
  được skip vì không copy snapshot vào image.
- Thử thêm nhóm hội thoại nhiều lượt trong thư mục trống dữ liệu đã lộ hai test phụ
  thuộc kho máy tác giả. Không sửa các test đó; README không đưa nhóm này vào lệnh
  kiểm thử offline trên image.
- Smoke test bằng TestClient trong thư mục tạm, seed vào kho tạm, chặn mạng bên ngoài:
  health=10 tài liệu; UI=200; query thiếu khóa=401; câu chào SSE có `done`, không `error`.
- Parse YAML bằng PyYAML, kiểm tra đường dẫn snapshot và cấu hình volume: OK.
- `git diff --check`: không có lỗi whitespace tại lần kiểm tra; có cảnh báo LF/CRLF.
- Docker CLI không có trên máy (`docker` không được nhận diện). Chưa chạy được
  `docker compose config`, build image hoặc chạy Linux container. Các kiểm tra Python
  dùng venv hiện có (Python 3.12); image khai báo Python 3.11, cần xác nhận trên Docker.

## 6. Giới hạn và việc tiếp theo

Dev có Docker cần chạy các bước README, kiểm tra `healthy` rồi hỏi một câu học vụ với
khóa riêng để xác nhận cả Gemini Embedding và chat. Health/câu chào không xác nhận
kết nối Gemini. Dependencies hiện tiếp tục dùng `requirements.txt` của dự án, chưa
có lockfile tái lập toàn bộ phiên bản.

Không commit/push, không sửa các thay đổi khác đã có trong working tree. Người dùng
cần đưa các file bàn giao lên branch chia sẻ để dev khác clone được.

## 7. Ba câu tự kiểm tra

1. Vì sao restart container không mất tài liệu nhưng vẫn mất lịch sử chat?
2. Vì sao `LLM_PROVIDER=mock` vẫn có thể dùng hạn ngạch Google?
3. Khi nào snapshot demo được copy lại?

<details>
<summary>Gợi ý đáp án</summary>

1. Tài liệu nằm trong volume; session chat nằm trong RAM.
2. Mock chỉ thay phần sinh câu trả lời; embedding vẫn gọi Gemini.
3. Chỉ khi storage chưa được khởi tạo và chưa có dữ liệu đích, ví dụ sau khi dev chủ động reset volume.

</details>
