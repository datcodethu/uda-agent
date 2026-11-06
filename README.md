# Đông Á RAG — chạy bản chatbot demo bằng Docker

Bản hiện tại gồm AI Service FastAPI, trang Web Chat và Qdrant local. Spring Boot,
PostgreSQL và frontend React chưa được triển khai. Dev chỉ cần Git và Docker Compose;
không cần cài Python, Java hoặc Qdrant trên máy.

Dev làm Spring Boot đọc [quy ước tích hợp Backend ↔ AI Service](docs/backend-ai-contract.md)
trước khi viết client gọi API. Tài liệu phân biệt API hiện có và phần cần bổ sung.

## Chạy nhanh

1. Cài Git và Docker Desktop (Windows/macOS) hoặc Docker Engine + Compose plugin
   (Linux). Khởi động Docker, dùng Linux containers. Kiểm tra:

   ```text
   docker --version
   docker compose version
   docker info
   ```

2. Clone repository được người bàn giao cung cấp, checkout đúng branch/commit demo,
   rồi mở terminal ở thư mục chứa `docker-compose.yml`.

3. Sao chép file cấu hình mẫu ở **gốc repository**:

   PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

   CMD:

   ```bat
   copy .env.example .env
   ```

   Linux/macOS:

   ```sh
   cp .env.example .env
   ```

   Mở `.env` bằng editor, điền `GOOGLE_API_KEY` của dev và đổi `INTERNAL_API_KEY`
   thành chuỗi ngẫu nhiên riêng. Khóa Google cần quyền gọi embedding và model chat.
   Không đưa khóa vào Git, ảnh chụp hoặc log gửi cho người khác.
   Container không đọc `ai-service/.env` trên máy host.

4. Build và chạy:

   ```text
   docker compose config --quiet
   docker compose up --build -d --wait
   docker compose ps
   ```

   Lần đầu cần Internet để tải image/thư viện. Kết quả mong đợi: service `ai-service`
   ở trạng thái `healthy`. Nếu Compose chưa hỗ trợ `--wait`, bỏ cờ này và xem `ps`/logs.
   Dùng `config --quiet` để kiểm tra cấu hình mà không in các giá trị khóa đã điền.

5. Mở:

   - Chat: <http://localhost:8000/>
   - Swagger: <http://localhost:8000/docs>
   - Health: <http://localhost:8000/v1/health>

   Nhập một câu học vụ hoặc chọn gợi ý trên giao diện để thử trả lời, trích dẫn và SSE.
   Health chỉ xác nhận ứng dụng đã chạy và đọc được kho, chưa kiểm tra Gemini.

## Dữ liệu demo và volume

Compose mount **chỉ đọc** snapshot Git `ai-service/data/backup_pre_demo_20261104/`.
Lần chạy đầu, script sao chép cặp `chunks.jsonl` + `qdrant_local` sang named volume
`ai_storage`, kiểm tra các chunk khớp với payload vector rồi khởi động ứng dụng.
Snapshot này có 10 tài liệu / 103 chunks tại thời điểm bàn giao. Không nạp lại embedding
và không cần xin riêng các file PDF/DOCX gốc để hỏi trên kho demo.

Dữ liệu dev nạp/gỡ sau đó nằm trong volume; restart/rebuild không ghi đè bằng snapshot.
Thư mục dữ liệu đang dùng trực tiếp trên máy tác giả không bị mount vào container.
Chỉ chạy một container/một worker vì Qdrant local khóa kho theo tiến trình.
Snapshot không được đóng gói vào image: dev cần clone cả repository, không chỉ lấy image.

## Kiểm tra API và streaming

Trong Swagger, với API `/v1/query`, `/v1/query/stream`, `/v1/ingest`, nhập header
`x-internal-key` bằng giá trị `INTERNAL_API_KEY` đã đặt. JSON mẫu để hỏi:

```json
{
  "question": "Sinh viên phải tuân thủ nội quy học đường như thế nào?",
  "history": [],
  "conversation_id": "dev-test-001",
  "mode": "hybrid"
}
```

Để xem SSE qua terminal mà không cần đưa khóa nội bộ vào lệnh, gọi endpoint Web Demo:

```text
curl -N -X POST http://localhost:8000/api/chat/stream -H "Content-Type: application/json" -d "{\"question\":\"Xin chao\",\"conversation_id\":\"smoke-test\"}"
```

PowerShell dùng `curl.exe` thay cho `curl`. Câu chào dùng nhánh phản hồi nhanh, không
kiểm tra retrieval/Gemini. Mong đợi `event: token`, `event: verify`, `event: done`.
Để kiểm tra toàn bộ RAG, dùng câu hỏi học vụ trên Web Chat; luồng thông thường có thêm
`event: sources`. Thử tiếp “cho ví dụ” trong cùng cuộc trò chuyện.

Chạy nhóm test khởi tạo Docker và kiểm chứng câu trả lời bên
trong image bằng container tạm, không mount kho dev và không nạp file chứa khóa:

```text
docker build -t donga-rag-tests ./ai-service
docker run --rm -e LLM_PROVIDER=mock donga-rag-tests python -m unittest tests.test_docker_start tests.test_sufficiency_and_verification -v
```

Test snapshot thật được skip trong image vì snapshot chỉ được mount khi chạy Compose.
Khởi động bằng Compose sẽ kiểm tra snapshot thật trước khi chạy server.
Đây là nhóm regression test, không phải toàn bộ suite. Một test benchmark cũ trong
`test_core.py` vẫn có thể gọi Gemini Embedding khi chạy toàn bộ suite; một số test
hội thoại nhiều lượt còn phụ thuộc kho dữ liệu trên máy tác giả. Không coi
`LLM_PROVIDER=mock` là hàng rào chặn mọi kết nối mạng.

## Mock và hạn ngạch

- `LLM_PROVIDER=gemini`: thử câu trả lời thật, cần Internet và khóa Google hợp lệ.
- `LLM_PROVIDER=mock`: giả lập phần sinh câu trả lời. **Retrieval vẫn gọi Gemini
  Embedding**, kể cả chọn BM25 trong bản mã hiện tại; không phải chế độ RAG offline.
- Không có khóa vẫn có thể mở UI, xem health và thử câu chào. Câu hỏi học vụ sẽ lỗi
  khi gọi embedding. Không xem việc UI mở được là đã kiểm tra toàn bộ chatbot.
- Khởi tạo snapshot và unit test không gọi API; hỏi học vụ sẽ dùng hạn ngạch embedding
  và, nếu chọn Gemini, cả model chat. Hạn ngạch tùy tài khoản/model.

## Lệnh thường dùng

```text
docker compose logs --tail=100 -f ai-service
docker compose stop
docker compose start
docker compose down
docker compose up --build -d --wait
```

`down` gỡ container nhưng giữ volume. Sau khi đổi `.env`, chạy
`docker compose up -d --force-recreate --wait`; `restart` không cập nhật environment.
Lịch sử hội thoại vẫn nằm trong RAM và mất khi container được tạo lại/khởi động lại,
hoặc hết TTL 30 phút; volume giữ kho tài liệu, không giữ session chat.

Muốn **xóa toàn bộ dữ liệu dev trong volume và phục hồi snapshot ban đầu**, chỉ khi
đã chấp nhận mất các tài liệu vừa nạp/gỡ:

```text
docker compose down --volumes
docker compose up -d --wait
```

## Xử lý lỗi

| Hiện tượng | Cách xử lý |
| --- | --- |
| Không nhận lệnh `docker` / không kết nối daemon | Cài, khởi động Docker Desktop; kiểm tra `docker info`. |
| Port 8000 đã dùng | Đổi `CHAT_PORT=8001` trong `.env`, tạo lại container và mở `localhost:8001`. |
| Thiếu `INTERNAL_API_KEY` | Tạo `.env` tại gốc repo và điền khóa; file trong `ai-service/` không dùng cho Compose này. |
| Không tìm thấy bind source snapshot | Kiểm tra clone đầy đủ, đúng branch và có `backup_pre_demo_20261104/qdrant_local/meta.json`. |
| Snapshot không khớp / volume chưa khởi tạo đủ | Xem log; giữ bản sao dữ liệu dev nếu cần, rồi chủ động reset volume theo hướng dẫn trên. Không chép một nửa snapshot. |
| Health OK nhưng chat báo lỗi API | Kiểm tra khóa, model, kết nối mạng và hạn ngạch Google; xem sự kiện `error`/logs. |
| 401 ở `/v1/*` | Header `X-Internal-Key` phải khớp `.env`; tạo lại container sau khi đổi khóa. |
| Qdrant báo khóa bởi tiến trình khác | Chỉ chạy một instance và không chạy script truy cập cùng kho khi server đang dùng kho. |

Compose mặc định chỉ mở cổng trên `127.0.0.1` cho dev test. Web demo chưa có đăng nhập
và `/api/chat/*` không yêu cầu khóa nội bộ; đây chưa phải cấu hình public production.

Căn cứ cấu hình: [Docker Compose environment interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/),
[Docker volumes](https://docs.docker.com/engine/storage/volumes/),
[Docker build context và .dockerignore](https://docs.docker.com/build/concepts/context/#dockerignore-files).
