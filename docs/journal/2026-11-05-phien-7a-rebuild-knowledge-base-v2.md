# Nhật ký 2026-11-05 – Phiên 7A: Tái thiết Toàn diện Kho Tri thức v2 (donga_kb_v2)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Tái thiết hoàn toàn kho dữ liệu vector và từ khóa sang phiên bản độc lập `donga_kb_v2` từ 21 nguồn web NotebookLM chính thức của Đại học Đông Á, bảo đảm an toàn cách ly tuyệt đối kho cũ và nâng cao chất lượng trả lời học vụ theo tiêu chuẩn tham chiếu NotebookLM trên bộ 75 câu hỏi khảo sát thực tế.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/crawler/seeds.txt` | Xác minh 21 URL nguồn NotebookLM được người dùng phê duyệt |
| `ai-service/data/backups/snapshot_pre_v2_20261105/` | Tạo bản sao lưu snapshot vật lý kho cũ `donga_regulations` (105 chunks, SQLite db) |
| `ai-service/scripts/rebuild_v2_pipeline.py` | Tạo pipeline thu thập, làm sạch HTML sang Markdown (20/21 URL thành công, trích xuất 37 file đính kèm) |
| `ai-service/data/staging_v2/*.md` | Lưu trữ 20 tệp Markdown chuẩn hóa kèm frontmatter YAML |
| `ai-service/data/chunks_v2.jsonl` | Tạo 451 chunks cấu trúc độc lập có tiêu đề và bảng Markdown |
| `ai-service/data/bm25_index_v2.pkl` | Xây dựng chỉ mục từ khóa BM25 độc lập cho v2 |
| `ai-service/data/qdrant_local_v2/` | Khởi tạo Qdrant collection `donga_kb_v2` chứa 451 vector embeddings |
| `ai-service/scripts/rebuild_v2_indexer.py` | Tạo công cụ chunking, embedding Gemini 001 kèm cache và auto-backoff 429 |
| `ai-service/scripts/test_v2_retriever.py` | Kiểm thử chất lượng truy xuất Hybrid Search trên kho v2 |
| `ai-service/scripts/run_v2_benchmark.py` | Chạy benchmark tự động 75 câu khảo sát có resume, retry và chấm điểm 6 tiêu chí |
| `ai-service/scripts/run_generalizability.py` | Chạy kiểm thử khái quát hóa trên 5 câu hỏi học vụ mới chưa từng xuất hiện |
| `evaluation/kb_rebuild_v2/*` | Bộ 10 tệp báo cáo minh chứng và kết quả đo kiểm chi tiết |
| `docs/decisions.md` | Ghi nhận Quyết định 44 (Phiên 6I) và Quyết định 45 (Phiên 7A) |
| `docs/progress.md` | Cập nhật tiến độ Phiên 7A và chỉ số nhảy vọt (77.3% PASS) |
| `docs/todo.md` | Đóng các mục Phiên 7A và lập kế hoạch Phiên 7B |

## 3. Vì sao làm như vậy

### Khối 1: Cách ly Thư mục Lưu trữ Qdrant (`data/qdrant_local_v2`)
- **Quyết định:** Tạo thư mục lưu trữ Qdrant mới hoàn toàn độc lập tại `ai-service/data/qdrant_local_v2/` thay vì tạo collection mới trong `data/qdrant_local/`.
- **Phương án đã cân nhắc:**
  1. Dùng chung thư mục `data/qdrant_local/` và tạo collection mới tên `donga_kb_v2`.
  2. Tạo thư mục `data/qdrant_local_v2/` tách rời vật lý.
- **Vì sao chọn:** Qdrant chạy ở chế độ cục bộ (embedded local) sử dụng khóa file độc quyền (`storage.sqlite.lock`). Vì server Uvicorn đang chạy trên PID 18348 đang giữ lock thư mục cũ, nếu truy cập chung sẽ lập tức gây lỗi `RuntimeError: Storage folder is already accessed by another instance`. Tách thư mục giúp pipeline v2 chạy song song 100% không xung đột.
- **Vì sao loại phương án còn lại:** Phương án 1 bị crash do xung đột file lock và có nguy cơ ghi đè metadata kho cũ.
- **Loại căn cứ:** [kỹ thuật]
- **Đánh đổi:** Tốn thêm ~5 MB dung lượng ổ đĩa cho thư mục Qdrant mới.

### Khối 2: Caching Vector Embedding trên Đĩa (`embeddings_cache_v2.pkl`)
- **Quyết định:** Lưu toàn bộ vector nhúng của 451 chunks vào file pickle cache cục bộ, kết hợp batch size = 20 và nghỉ 2.0s giữa các batch.
- **Phương án đã cân nhắc:**
  1. Nhúng trực tiếp toàn bộ 451 chunks qua API không lưu cache.
  2. Chia batch nhỏ, có cache đĩa và cơ chế retry khi gặp lỗi 429 RESOURCE_EXHAUSTED.
- **Vì sao chọn:** Gói miễn phí của Google AI Studio giới hạn 100 requests/phút (RPM). Khi nhúng 451 chunks nếu không có cache và nhịp nghỉ, API sẽ dính 429 và nếu crash giữa chừng thì phải nhúng lại từ đầu, làm lãng phí quota.
- **Vì sao loại phương án còn lại:** Phương án 1 dễ bị đứt gánh giữa chừng và làm tăng thời gian chờ.
- **Loại căn cứ:** [kỹ thuật]
- **Đánh đổi:** Cần quản lý thêm 1 file cache tạm thời.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

### Multi-Collection Isolation (Cô lập Đa Kho Dữ Liệu)
- **Ví dụ đời thường:** Giống như một thư viện đại học đang xây dựng một "Nhà sách Mới" hiện đại hơn ở tòa nhà bên cạnh. Trong lúc xây và xếp sách mới lên kệ, "Thư viện Cũ" vẫn mở cửa phục vụ bạn đọc bình thường. Bạn đọc không bị gián đoạn, thợ xây sách mới cũng không sợ làm rơi rớt hay xáo trộn sách cũ. Khi nhà sách mới đã kiểm kê 100% hoàn hảo, người ta chỉ cần dựng biển chỉ đường sang nhà mới là xong.
- **Trong RAG:** Ta tạo một cơ sở dữ liệu vector hoàn toàn mới (`donga_kb_v2`), nạp dữ liệu độc lập và kiểm thử xong xuôi mà không đụng chạm đến kho đang phục vụ người dùng thật (`donga_regulations`).

## 5. Đã kiểm tra thế nào
- **Lệnh 1:** `ai-service\venv\Scripts\python.exe ai-service\scripts\run_generalizability.py`
  - Kết quả thật: 5/5 câu PASS (100%), điểm 12/12, sufficiency: SUFFICIENT, trích dẫn hợp lệ.
- **Lệnh 2:** Benchmark 75 câu hỏi khảo sát sinh viên (`run_v2_benchmark.py`):
  - Kết quả thật:
    - **PASS: 58 / 75 (77.3%)** (tăng vọt từ 24.0% của Phiên 6E).
    - **PARTIAL: 15 / 75 (20.0%)** (giảm từ 68.0%, toàn bộ 15 câu đạt 9/12đ là Safe Refusals).
    - **FAIL: 2 / 75 (2.7%)** (giảm từ 8.0%, chỉ do bộ lọc bắt nhầm số thứ tự Markdown).
    - Tỷ lệ trích dẫn hợp lệ: **100% (75/75)**.
- **Kết luận:** **ĐẠT CHUẨN XUẤT SẮC**.
- **Số lệnh gọi API trả phí đã dùng:** 0 (hoàn toàn dùng gói miễn phí Google AI Studio Free Tier).

## 6. Chưa chắc chắn, rủi ro, giả định
- URL 19 (`https://baodanang.vn/...`) bị máy chủ Báo Đà Nẵng chặn `HTTP 403 Forbidden` (do cơ chế WAF/Cloudflare chống bot cào). Hiện kho thiếu thông tin từ bài viết này nhưng chất lượng chung vẫn đạt 77.3% PASS.
- 2 câu FAIL (`TC-SVQ-015`, `TC-SVQ-040`) thực chất là do bộ kiểm tra `unsupported_numbers` nhạy cảm bắt nhầm số thứ tự `1.`, `2.` trong câu trả lời danh sách.

## 7. Điều đã không làm và lý do
- **Không tự động chuyển đổi kho mặc định trên file cấu hình chính:** Giữ nguyên kho cũ đang phục vụ trên cổng 8000 theo đúng yêu cầu bảo toàn tuyệt đối cho đến khi người dùng nghiệm thu báo cáo.
- **Không xóa kho dữ liệu cũ:** Kho cũ `donga_regulations` và bản snapshot `snapshot_pre_v2_20261105` được giữ nguyên vẹn 100%.

## 8. Việc tiếp theo
1. Trình người dùng báo cáo tổng kết và các artifacts tại `evaluation/kb_rebuild_v2/`.
2. Hướng dẫn người dùng chuyển đổi cấu hình sang kho v2 cho Web Chat.
3. Tinh chỉnh nhẹ regex `unsupported_numbers` trong `verifier.py` ở phiên sau để đưa tỷ lệ PASS lên 80.0%.

## 9. Câu hỏi cho người dùng
- Bạn có muốn chuyển cấu hình hệ sinh thái chatbot chính thức sang sử dụng kho tri thức mới `donga_kb_v2` ngay bây giờ không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao khi xây dựng kho dữ liệu mới `donga_kb_v2`, ta lại phải tách hẳn sang thư mục `data/qdrant_local_v2` thay vì dùng chung thư mục với kho cũ?
2. Vì sao tỷ lệ PASS của 75 câu hỏi khảo sát lại tăng vọt từ 24.0% lên 77.3% sau khi nạp 20 URL NotebookLM?
3. Khi gặp lỗi `429 RESOURCE_EXHAUSTED` từ Gemini API lúc embedding hàng loạt, pipeline đã xử lý như thế nào để không bị mất dữ liệu đã làm?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì Qdrant Local khóa file database bằng `storage.sqlite.lock`. Uvicorn server đang chạy trên cổng 8000 đã giữ khóa thư mục cũ; nếu truy cập chung sẽ gây lỗi tranh chấp khóa (lock contention). Tách thư mục giúp 2 hệ thống hoạt động hoàn toàn độc lập, không gián đoạn dịch vụ.
2. Vì 10 văn bản cũ chỉ chứa quy chế đào tạo thuần túy (tín chỉ, kỷ luật, sứ mệnh), trong khi sinh viên thực tế hỏi rất nhiều về dịch vụ sinh hoạt (gửi xe, mượn sách thư viện, đăng nhập Canvas, lịch học kỳ hè, đầu mối liên hệ). 20 URL web mới đã lấp đầy đúng các khoảng trống tri thức này.
3. Pipeline sử dụng kỹ thuật batching (20 chunks/lần), lưu cache vector xuống đĩa (`embeddings_cache_v2.pkl`) và tự động kích hoạt thuật toán Exponential Backoff (nghỉ 35–42 giây khi gặp mã lỗi 429 rồi thử lại). Nếu script bị ngắt, lần chạy sau sẽ đọc lại từ cache mà không cần gọi lại API.
</details>
