# Quy ước tích hợp Backend Spring Boot và AI Service

Phiên bản tài liệu: **0.1 — dự thảo triển khai**, ngày 2026-11-05.
Đối chiếu working tree tại commit nền `231d58c`. Đây là tài liệu bàn giao, chưa
thay đổi mã, schema hay cấu hình runtime. Các thay đổi chưa commit khác trong
working tree không được xem là một bản phát hành đã bàn giao.

## 1. Cách đọc và phạm vi

- **[HIỆN CÓ]**: hành vi đã thấy trong mã nguồn hiện tại.
- **[QUY ƯỚC BACKEND]**: yêu cầu dành cho Spring Boot sắp triển khai; chưa có mã backend.
- **[CẦN BỔ SUNG]**: năng lực chưa có hoặc chưa đủ để bảo đảm; không tự giả định API hỗ trợ.

Tài liệu áp dụng cho hỏi đáp học vụ công khai. Tra điểm, công nợ cá nhân, đăng nhập
hệ thống đào tạo và gửi hồ sơ chưa nằm trong hợp đồng AI hiện tại.

Nguyên tắc: Backend quản lý người dùng và nghiệp vụ; AI Service quản lý xử lý RAG.
Backend không tự sinh quy định, viết lại kết luận AI hoặc thay bằng chứng truy xuất.

## 2. Phân công trách nhiệm

| Nội dung | Spring Boot | AI Service |
| --- | --- | --- |
| Xác thực | JWT/refresh token, quyền người dùng, quyền quản trị | Kiểm tra khóa nội bộ của service gọi |
| Hội thoại | Sở hữu phiên, lịch sử bền vững, thứ tự message | Phân giải ngữ cảnh, cache nguồn ngắn hạn |
| Hỏi đáp | Kiểm tra đầu vào, giới hạn tải, gọi HTTP và relay SSE | Chuẩn hóa, phân loại, retrieval, LLM, verifier |
| Dữ liệu tài liệu | File gốc, phê duyệt, metadata nghiệp vụ, phiên bản, audit | Trích xuất, chia chunk, Qdrant, JSONL và BM25 |
| Kết quả | Lưu answer/sources/cảnh báo, hiển thị qua frontend | Trả answer, nguồn, trạng thái bằng chứng |
| Lỗi/đo lường | Mã lỗi công khai, thời gian toàn trình, log đã lọc | Trạng thái/lỗi nội bộ và số đo pipeline hiện có |
| Phản hồi | Lưu feedback, cung cấp màn hình quản trị | Không tự coi feedback là đáp án chuẩn |

## 3. Địa chỉ, kết nối và xác thực

**[HIỆN CÓ]** Base path `/v1`. Khi cùng Docker network, địa chỉ dự kiến cho Backend
là `http://ai-service:8000`. Khi Backend chạy trên host và AI chạy bằng Compose dev:
`http://localhost:8000`, hoặc cổng `CHAT_PORT` đã cấu hình. `localhost` bên trong
container Backend là chính container đó, không phải AI Service.

| Method | Path | Cần `X-Internal-Key` | Mục đích |
| --- | --- | --- | --- |
| GET | `/v1/health` | Không | Kiểm tra ứng dụng/đếm tài liệu |
| POST | `/v1/query` | Có | Hỏi đáp JSON |
| POST | `/v1/query/stream` | Có | Hỏi đáp SSE |
| POST | `/v1/ingest` | Có | Nạp file multipart |
| GET | `/v1/ingest/documents` | Có | Danh sách tài liệu trong chỉ mục |
| DELETE | `/v1/ingest/documents/{doc_name}` | Có | Gỡ tài liệu |

**[QUY ƯỚC BACKEND]** Đặt base URL và khóa ở cấu hình môi trường; khóa phải khớp
`INTERNAL_API_KEY` phía AI. Không gửi khóa xuống trình duyệt, không dùng JWT sinh viên
làm khóa nội bộ, không ghi khóa vào log. Giữ AI và kho vector trong mạng nội bộ khi
triển khai hệ thống đầy đủ. Khóa hiện tại là khóa chung, chưa phân scope đọc/ghi;
Backend phải kiểm tra quyền admin trước mọi thao tác tài liệu.

**[HIỆN CÓ]** `/api/chat`, `/api/chat/stream`, `/` và `/chat` dành cho demo trực tiếp;
không dùng chúng làm đường tích hợp Spring Boot. Các endpoint chat demo không có
kiểm tra khóa nội bộ. CORS đang cho phép mọi origin.
**[CẦN BỔ SUNG]** Kiểm soát đường demo và CORS trước khi mở hệ thống ra Internet.

## 4. Quy ước dữ liệu chung

**[QUY ƯỚC BACKEND]** Trao đổi JSON UTF-8, tên trường `snake_case`. DTO Java ánh xạ
rõ tên trường; không đổi tên trên đường gọi AI. Cho phép trường response mới chưa
biết, nhưng kiểm tra các trường bắt buộc và giữ cảnh báo. Không dùng nhãn hiển thị
tiếng Việt làm enum nghiệp vụ. Null, danh sách rỗng và thiếu trường là các trường
hợp cần xử lý riêng; ví dụ `best_dense_score=null` không đồng nghĩa điểm bằng 0.

Client không được gửi system prompt, role `system`, model hoặc ngưỡng từ chối qua
API công khai. Backend chỉ chuyển các tham số được cho phép; không forward toàn bộ
JSON từ frontend sang AI Service.

## 5. Request hỏi đáp

**[HIỆN CÓ]** Cùng schema cho `/v1/query` và `/v1/query/stream`:

| Trường | Kiểu / mặc định | Quy tắc hiện tại |
| --- | --- | --- |
| `question` | string, bắt buộc | Dài 1–1000 ký tự; chưa chặn chuỗi chỉ có khoảng trắng |
| `history` | array, `[]` | Mỗi phần tử có `role=user/assistant`, `content` string |
| `conversation_id` | string hoặc null, mặc định null | AI chưa xác thực quyền sở hữu/định dạng UUID |
| `stream` | boolean, false | Có trong schema nhưng không điều khiển chế độ; endpoint quyết định |
| `mode` | `dense`, `bm25`, `hybrid`; mặc định hybrid | Thuật toán truy xuất |
| `top_k` | integer 1–20 hoặc null | Null dùng cấu hình AI; còn bị giới hạn bởi `max_context_chunks` |

Ví dụ request hợp lệ, chỉ minh họa giao thức:

```json
{
  "question": "Cho ví dụ",
  "conversation_id": "b05187b8-e946-4870-a134-fde7a9c52b1a",
  "history": [
    {"role": "user", "content": "Tôi muốn hiểu nội quy học đường."},
    {"role": "assistant", "content": "Bạn muốn tìm hiểu nội dung nào trong nội quy?"}
  ],
  "mode": "hybrid",
  "top_k": 5
}
```

**[QUY ƯỚC BACKEND]** Chặn câu hỏi trắng; giới hạn payload và cửa sổ history ở
Backend. Dùng `hybrid`, không truyền `top_k` nếu chưa có nhu cầu thử nghiệm đã thống
nhất. Không cho sinh viên tùy ý thay cấu hình thử nghiệm. Không giả định
`mode=bm25` hay `LLM_PROVIDER=mock` loại bỏ lời gọi embedding: mã hiện vẫn gọi
Gemini Embedding trong retrieval.

## 6. Response JSON và cách sử dụng

**[HIỆN CÓ]** `/v1/query` dùng `QueryResponse`:

| Trường | Kiểu | Ý nghĩa cho Backend |
| --- | --- | --- |
| `answer` | string | Nội dung trả lời, giữ nguyên |
| `refused`, `refuse_reason` | boolean, string | Kết quả xử lý nội dung, không phải lỗi HTTP |
| `conversation_id` | string/null | ID đã gửi; AI không tự tạo ở route này |
| `standalone_query` | string/null | Câu được chuẩn hóa/mở rộng; không bảo đảm luôn là câu viết lại độc lập |
| `sources` | array Source | Nguồn để đối chiếu trích dẫn |
| `unsupported_numbers` | array string | Số liệu verifier chưa tìm được căn cứ |
| `sufficiency` | enum | Một trong bốn trạng thái ở dưới |
| `verification_badges` | array string | Nhãn hiển thị do AI trả về |
| `citations`, `invalid_citations` | array integer | Chỉ số nguồn hợp lệ/ngoài phạm vi được phát hiện |
| `academic_intent`, `risk_level` | string/null | Phân loại bổ sung; có thể không có ở nhánh phản hồi nhanh |
| `claim_warnings` | array string | Cảnh báo kiểm chứng khẳng định |
| `best_dense_score` | number/null | Điểm vector, không phải xác suất trả lời đúng |
| `retrieval_ms`, `latency_ms` | integer | Số đo do AI trả; Backend đo thêm thời gian HTTP toàn trình |

`Source` JSON có `index`, `chunk_id`, `doc_name`, `chuong`, `dieu`, `score`, `snippet`.
`index` bắt đầu từ 1, tương ứng `[1]`, `[2]` trong câu trả lời; không sort lại nguồn
hay đổi số trích dẫn. `snippet` hiện chỉ lấy tối đa 240 ký tự, không phải toàn văn.
Không coi `chunk_id` là UUID: UUID điểm Qdrant là định danh khác.

**Lệch giữa JSON và SSE hiện có:** `_sources()` có thể thêm `effective_date` và
`doc_number`, SSE gửi trực tiếp, nhưng model `Source` chưa khai báo hai trường này
nên response JSON không bảo đảm giữ chúng. Hàm `answer()` còn tạo `timing` và
`intent`, nhưng `QueryResponse` chưa khai báo nên `/v1/query` không bảo đảm trả chúng.
Backend phải bám response model, không bám dict nội bộ.

| `sufficiency` | Ý nghĩa |
| --- | --- |
| `SUFFICIENT` | Cơ chế hiện tại đánh giá bằng chứng đủ cho câu trả lời |
| `PARTIAL` | Có thể trả lời một phần |
| `INSUFFICIENT` | Chưa đủ căn cứ để kết luận cụ thể |
| `NO_EVIDENCE` | Không có bằng chứng phù hợp theo cơ chế hiện tại |

**[QUY ƯỚC BACKEND]** Lưu nguyên các trường kiểm chứng, không biến `PARTIAL` thành
“đã xác minh hoàn toàn”. Không sinh badge “đã kiểm chứng” cố định. Đây là kết quả
heuristic kiểm chứng của AI, không bảo đảm mọi khẳng định đúng.

`refuse_reason` hiện có: `no_chunks`, `low_score`, `llm_refused`, `personal_data`,
`out_of_scope`, `ambiguous`, `clarify_no_context`; chuỗi rỗng khi không từ chối.
Không phân loại tất cả các giá trị này thành “thiếu tài liệu”. `faq` được nhắc trong
hướng dẫn cũ nhưng chưa có nhánh FAQ trong pipeline đang đọc.
Giá trị mới chưa biết phải được giữ lại để phân tích, không làm client sập.

## 7. Giao thức streaming SSE

**[HIỆN CÓ]** Gọi **POST** `/v1/query/stream` với JSON, nhận
`Content-Type: text/event-stream`. Mỗi sự kiện gồm `event: ...`, một dòng
`data: ...` chứa JSON, rồi một dòng trống. Đây không phải WebSocket và không phải
một response JSON duy nhất.

| Event | Payload | Xử lý ở Backend |
| --- | --- | --- |
| `token` | `text` string | Nối theo thứ tự, giữ nguyên khoảng trắng; chuyển tiếp sớm |
| `sources` | `sources` array | Gắn nguồn vào câu trả lời; có thể vắng ở nhánh từ chối sớm |
| `verify` | `unsupported_numbers`, `sufficiency`, `badges`, `citations`, `invalid_citations`, `claim_warnings` | Lưu kết quả kiểm chứng; `badges` ở đây tương ứng nhãn hiển thị |
| `done` | `refused`, `refuse_reason`, `timing`, `intent`, `academic_intent`, `risk_level`, `claim_warnings`, `sufficiency`, `verification_badges` | Kết thúc thành công ở tầng giao thức, kể cả AI từ chối nội dung |
| `error` | `message` string | Lỗi kỹ thuật; kết thúc lượt bị lỗi, không chờ `done` |

Ví dụ chuỗi sự kiện rút gọn, không phải đáp án học vụ tham chiếu:

```text
event: token
data: {"text":"Bạn có thể hỏi rõ hơn không?"}

event: verify
data: {"unsupported_numbers":[],"sufficiency":"NO_EVIDENCE","badges":["Chưa đủ bằng chứng để kết luận"],"citations":[],"invalid_citations":[],"claim_warnings":[]}

event: done
data: {"refused":true,"refuse_reason":"clarify_no_context","timing":{"retrieval_ms":0,"llm_ms":0,"total_ms":0},"intent":"clarify_no_context","academic_intent":null,"risk_level":"LOW","claim_warnings":[],"sufficiency":"NO_EVIDENCE","verification_badges":["Chưa đủ bằng chứng để kết luận"]}

```

Thứ tự thường gặp: `token* → sources → verify → done`; từ chối sớm:
`token → verify → done`; khi lỗi có thể là `token* → error` hoặc HTTP lỗi trước stream.
Client không được bắt buộc phải có `sources`, và phải chấp nhận token text tùy độ dài.

**[QUY ƯỚC BACKEND]** Parser phải tích lũy dữ liệu qua các network chunk: một chunk
TCP không tương đương một event và có thể chia giữa ký tự UTF-8. Không trim text,
không gom hết response rồi mới gửi. Tắt buffering trên đường relay/proxy tương ứng.
Nếu frontend dùng POST + JWT thì chọn client hỗ trợ đọc response stream của POST;
không giả định native EventSource gửi được body và Authorization theo cách đó.

Backend gắn stream với message/conversation đang gọi, vì các event hiện không chứa
`message_id`, `request_id` hoặc `conversation_id`. Không tìm ID trong event `done`.
Nếu có trường/event mở rộng chưa biết thì bỏ qua an toàn, vẫn yêu cầu `done` hoặc
`error` theo hợp đồng này để kết luận lượt đã hoàn tất.

**Giới hạn quan trọng:** SSE hiện không có heartbeat, event ID hay resume. `timing`
trong `done` lấy từ bước prepare, chưa cập nhật thời gian sinh LLM/toàn bộ streaming;
Backend không dùng nó làm độ trễ toàn trình. `done` được yield trước khi lưu session
RAM, nên không phải xác nhận lịch sử đã lưu bền vững hoặc cache đã sẵn sàng tuyệt đối.

## 8. Hội thoại, thứ tự và lưu trữ

**[QUY ƯỚC BACKEND]** Backend sinh UUID cho `conversation_id`, kiểm tra quyền sở hữu
với user hiện tại trước mỗi lượt. Không dùng MSSV/email làm ID. Không để frontend
tự chọn phiên của người khác; AI chưa thực hiện xác thực này.

Lấy history từ PostgreSQL của đúng hội thoại, theo thứ tự cũ → mới, chỉ đưa các lượt
đã hoàn tất; không thêm câu hỏi hiện tại vào history lần nữa. Chỉ gửi role user/assistant,
không lấy history do frontend gửi làm nguồn tin cậy. Cho phép tối đa một request AI
đang chạy trên mỗi hội thoại để tránh đảo thứ tự và ghi đè cache; giới hạn này phải
được thực hiện xuyên các instance Backend nếu có nhiều instance.

**[HIỆN CÓ]** History không rỗng trong request được ưu tiên hơn history RAM. Nếu gửi
`[]` thì AI có thể dùng history RAM cũ, không có nghĩa xóa ngữ cảnh. Pipeline mặc định
lấy `history_turns=4` **phần tử message**, tương đương tối đa 2 cặp user/assistant
đầy đủ, mặc dù tên cấu hình là “turns”. Store RAM giữ tối đa 6 cặp và TTL trượt 1800 giây.

Backend luôn gửi cửa sổ history phù hợp ngay cả khi cache AI còn sống. Sau restart,
có history vẫn không khôi phục được `last_chunks`/`last_topic` đầy đủ, vì chúng chưa
có trong request. Không cam kết fast-path tái sử dụng nguồn khi cache đã mất.

Đề xuất trạng thái message **ở Backend**, chưa phải enum của AI:

```text
PENDING → STREAMING → COMPLETED
                   → FAILED
                   → INTERRUPTED
```

JSON HTTP thành công và hợp lệ, hoặc SSE nhận `done` hợp lệ → lưu kết quả rồi đánh
dấu COMPLETED. `refused=true` vẫn có thể COMPLETED. Nhận `error`/HTTP lỗi → FAILED;
EOF trước `done`/mất kết nối → INTERRUPTED. Không đưa answer dang dở vào history
cho lượt sau; có thể giữ bản nháp với trạng thái riêng để điều tra.

Backend lưu answer đã ghép, sources theo đúng index, các cảnh báo, sufficiency,
trạng thái nội dung và kỹ thuật riêng, mode/top_k đã dùng, thời gian Backend đo và
mã truy vết do Backend sinh. Không giữ transaction DB mở suốt thời gian gọi LLM.
AI chưa có API đọc lịch sử/xóa session: xóa hội thoại ở Backend không tự xóa RAM AI.
Sau khi xóa không tái sử dụng ID cũ; xóa ngay cache AI cần bổ sung endpoint riêng.

## 9. Lỗi, timeout, retry và giới hạn tải

| Tình huống hiện tại | Quy ước Backend |
| --- | --- |
| HTTP 401 | Lỗi cấu hình/xác thực giữa service; không tự yêu cầu sinh viên đăng nhập lại |
| HTTP 400 từ ingest | `status` không thuộc ACTIVE/EXPIRED; sửa đầu vào |
| HTTP 422 | Sai schema hoặc file không đọc/cắt được; không retry cùng payload tự động |
| HTTP 500/lỗi kết nối | Lỗi kỹ thuật, không kết luận kho không có quy định |
| HTTP 200 rồi `event:error` | Vẫn là lỗi; không chỉ kiểm tra HTTP status |
| AI/Gemini quá hạn ngạch | Có thể thành HTTP 500 ở prepare/JSON hoặc SSE error; chưa có cam kết HTTP 429 chuẩn hóa |
| JSON `refused=true`/SSE done với refused | Phản hồi nội dung, không phải lỗi hạ tầng |

Không parse chuỗi exception để làm mã lỗi nghiệp vụ lâu dài. Hiện `error.message`
có thể chứa chi tiết kỹ thuật; Backend trả thông báo công khai đã lọc và giữ mã truy
vết, không relay exception thô lên frontend. Error envelope có `code`, `request_id`
và phân loại retry là **[CẦN BỔ SUNG]** phía AI.

**[QUY ƯỚC BACKEND — cấu hình khởi điểm, cần đo lại]** Connect timeout 5 giây;
JSON response timeout 60 giây; SSE chờ response/sự kiện đầu và idle timeout 60 giây,
deadline toàn lượt 120 giây. Đây không phải SLA. Không đặt timeout đầu stream 3 giây
chỉ vì mục tiêu TTFT: retrieval thực hiện trước khi trả StreamingResponse. Timeout
Gemini 25 giây hiện tại không phải deadline tổng của pipeline. Ingest dùng timeout
riêng theo kích thước file và số chunk, không lấy deadline chat áp vào file lớn.

Chỉ health GET có thể retry tự động với backoff có giới hạn. Với query POST,
không tự retry khi đã gửi request mà chưa biết AI xử lý đến đâu; có thể tốn quota
và ghi thêm lượt RAM. Tuyệt đối không tự phát lại sau khi đã có token. Ingest/delete
cũng không có idempotency key hoặc transaction xuyên kho; retry phải qua kiểm tra
trạng thái và người vận hành. AI chưa hỗ trợ replay hoặc chống trùng request.

Backend cần hạn mức theo user/IP **và** hạn mức tổng/số request đồng thời, hàng đợi
có giới hạn và thông báo bận. Giá trị phải cấu hình theo quota thực tế, không hardcode
một con số Gemini chung. Hủy HTTP khi frontend ngắt không bảo đảm dừng ngay lời gọi
LLM đồng bộ; cần đo và bổ sung cơ chế hủy nếu cần.

## 10. Quản lý và đồng bộ tài liệu

**[HIỆN CÓ]** `POST /v1/ingest` dùng multipart, không dùng JSON/base64:

| Form field | Quy tắc |
| --- | --- |
| `file` | Bắt buộc; loader hiện hỗ trợ PDF có text, DOCX, TXT, MD |
| `doc_name` | Bắt buộc; định danh thay thế/xóa tài liệu trong chỉ mục |
| `status` | ACTIVE hoặc EXPIRED, mặc định ACTIVE |

Response: `{"doc_name":"dev-guide.txt","chunks":1,"status":"ACTIVE"}`.
`chunks` là số chunk thực tế, không cố định 1. Nạp cùng `doc_name` thay bản trước.
`DELETE /v1/ingest/documents/{doc_name}` trả `doc_name`, `deleted_chunks`; tài liệu
không có trong kho cũng có thể trả thành công với 0, không cam kết HTTP 404.

**[QUY ƯỚC BACKEND]** Sinh `doc_name` ổn định dạng ASCII không có `/`, `\\` hoặc tên
đường dẫn; giữ mapping với ID tài liệu trong PostgreSQL, không dùng tên file upload
chưa kiểm soát làm định danh. Gọi delete bằng path segment đã URL encode. Không đưa
dữ liệu cá nhân vào tên tài liệu.

Phân biệt ba trạng thái: phê duyệt nội dung, hiệu lực ACTIVE/EXPIRED và tiến độ ingest
PROCESSING/READY/FAILED. Ba nhóm này không thay thế cho nhau. Chỉ người có quyền
phê duyệt mới cho tài liệu vào kho; endpoint ingest hiện không kiểm registry/`da_duyet`
như CLI `ingest_approved.py`. Không dùng upload là mặc nhiên được duyệt.

Upload API hiện không nhận `doc_id`, `version_no`, ngày hiệu lực, đối tượng áp dụng,
URL nguồn hay metadata mở rộng; tham số `meta` ở hàm Python không phải hợp đồng HTTP.
Chưa có PATCH trạng thái, API lấy file nguồn, API lấy full chunk, job ID/queue status
hoặc API import URL trong router `/v1` đã đăng ký. Các công cụ import/rebuild đang làm
trong working tree không được coi là API đã bàn giao.

**Rủi ro đồng bộ hiện có:** ingest xóa vector cũ → thay JSONL → upsert vector → rebuild
BM25. Nếu lỗi ở giữa thì kho có thể lệch; PostgreSQL cũng không nằm trong transaction
đó. Backend chỉ đặt READY sau khi nhận thành công, nhưng 200 chưa chứng minh chất lượng
tài liệu. Khi timeout/lỗi, đánh dấu chưa xác nhận/FAILED và đối soát cả vector, JSONL,
BM25; GET documents chỉ đọc JSONL nên không đủ chứng minh cả ba kho đồng bộ.

Trong bản đầu, serialize thao tác ingest/delete và thực hiện ở cửa sổ bảo trì không
nhận query mới; đợi các lượt đang chạy hoàn tất. Không ghi trực tiếp JSONL/Qdrant từ
Spring Boot. Chỉ kiểm tra nguồn cached theo tên/status hiện tại chưa phát hiện được
trường hợp thay nội dung cùng tên ACTIVE. Sau cập nhật phải có bước làm mất cache
AI đã kiểm soát, ví dụ restart một instance trong cửa sổ bảo trì; cơ chế invalidation
theo phiên bản là **[CẦN BỔ SUNG]**. Quy trình rollback cần bản sao nhất quán cả kho.

## 11. An toàn dữ liệu, nguồn và phiên bản

**[QUY ƯỚC BACKEND]** Lọc dữ liệu cá nhân không cần thiết ở cả question và history
trước khi gửi AI/lưu log; không làm mất điều kiện học vụ hay che mọi số tiền một cách
mù quáng. Tài liệu nội bộ/hạn chế truy cập chưa được hỗ trợ ACL theo user bởi API này,
nên không nạp chung vào kho công khai. Đặt thời hạn lưu và quyền xóa dữ liệu chat.

Lưu thông tin nguồn đủ truy vết, nhưng không biến `doc_name` thành link file tùy ý.
Link tải nguồn phải đi qua mapping và kiểm tra quyền của Backend. Source hiện thiếu
cam kết `version_no`, hash nội dung và trang; chưa đủ truy vết bản tài liệu bất biến.
Nếu cần lưu snapshot bằng chứng, chỉ lưu dữ liệu được phép và ghi rõ giới hạn trên.

Không xóa/sắp xếp lại cảnh báo, không sửa câu trả lời để làm badge đẹp hơn. Nội dung
AI và snippet là dữ liệu không tin cậy; frontend render an toàn, không thực thi HTML.

## 12. Checklist nghiệm thu tích hợp

Các kịch bản dưới đây là test giao thức, không tạo nhãn đáp án cho bộ đánh giá NCKH.

- [ ] Thiếu/sai khóa nội bộ nhận 401; khóa không xuất hiện trong response frontend/log.
- [ ] User A không gọi, xem lịch sử hay feedback message thuộc user B.
- [ ] Request đúng schema; chặn câu trắng/quá dài, role system và tham số không cho phép.
- [ ] JSON giữ đủ answer/sources/cảnh báo; null và enum mới không làm DTO lỗi bất ngờ.
- [ ] SSE parser xử lý event bị cắt qua nhiều chunk, dấu tiếng Việt và nhiều event cùng chunk.
- [ ] Từ chối sớm không có sources vẫn hoàn tất; error sau token không bị đánh COMPLETED.
- [ ] EOF trước done, timeout, mất mạng và người dùng đóng tab được ghi trạng thái riêng.
- [ ] Nguồn theo đúng index; không gắn badge cố định; refused có trích dẫn vẫn giữ nguồn được trả.
- [ ] Hai hội thoại không lẫn dữ liệu; request nối tiếp được serialize trong từng hội thoại.
- [ ] Sau restart AI, Backend gửi lại history và không cam kết tái sử dụng cache cũ.
- [ ] Không tự retry POST khi kết quả xử lý chưa rõ; user gửi lặp không tạo hai lượt ngoài ý muốn.
- [ ] Tài liệu chưa duyệt không đến ingest; lỗi nạp không bị đánh READY; update/gỡ làm mất cache cũ.
- [ ] Chứng minh health OK không đồng nghĩa Gemini/Qdrant đều sẵn sàng cho query.

## 13. Thứ tự triển khai và các việc cần chốt

1. Backend dựng AiServiceClient cho JSON + SSE và kiểm tra khóa bằng API thực tế.
2. Thêm quyền sở hữu hội thoại, lưu message, chuyển trạng thái lỗi và lưu nguồn.
3. Thêm giới hạn tải, lọc log, timeout, xử lý ngắt stream và feedback.
4. Bổ sung quản trị tài liệu sau khi thống nhất identity/version, đồng bộ kho và cache.

Các mở rộng AI cần kế hoạch riêng: response source nhất quán JSON/SSE, mã lỗi có cấu
trúc, request/message ID, telemetry streaming đúng, quản lý phiên từ xa, định danh
phiên bản và invalidation, ingest có kiểm soát/khôi phục. Không thêm các trường/endpoint
này vào DTO bắt buộc trước khi AI thực sự hỗ trợ.

Đây là bản 0.1 để hai bên review. Trước khi triển khai cần chốt: chính sách xác thực
sinh viên/khách, thời hạn lưu chat, hạn mức và deadline đo thực tế, kích thước file,
định danh phiên bản và cách xử lý bảo trì kho. Trong lúc chờ có thể làm client chat
theo đúng API hiện có. Thay đổi phá vỡ hợp đồng phải được thống nhất, cập nhật tài liệu,
kiểm tra tương thích trước khi phát hành; không sửa ý nghĩa `/v1` âm thầm.

## 14. Căn cứ trong repository

- [Thiết kế kiến trúc và nghiệp vụ](plan.md).
- [Hướng dẫn bàn giao AI, Bước 15](ai-service.md).
- [Query schema](../ai-service/app/schemas/query_schema.py).
- [Query routes](../ai-service/app/api/v1/query_routes.py).
- [SSE handler](../ai-service/app/pipeline/generator/stream_handler.py).
- [RAG pipeline và nguồn](../ai-service/app/pipeline/rag_pipeline.py).
- [Session memory](../ai-service/app/pipeline/memory/session_memory.py).
- [Ingest routes](../ai-service/app/api/v1/ingest_routes.py), [schema](../ai-service/app/schemas/ingest_schema.py), [index service](../ai-service/app/pipeline/index_service.py).
- [Loader tài liệu](../ai-service/app/pipeline/preprocessor/pdf_loader.py).
- [Xác thực nội bộ](../ai-service/app/core/security.py), [main/router registration](../ai-service/app/main.py), [health](../ai-service/app/api/v1/health_routes.py).
