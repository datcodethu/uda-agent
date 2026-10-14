# Kế hoạch Phiên 3C: Công cụ Chat và Công cụ Chạy bộ câu hỏi thử

**Ngày lập:** 2026-10-14  
**Phiên làm việc:** 3C  
**Trạng thái:** ĐÃ DUYỆT (Người dùng duyệt kèm 6 điều kiện thực thi)  

---

## 1. Hiểu nhiệm vụ (Understanding)
- **Mục tiêu:**
  1. Xây dựng công cụ chat dòng lệnh `scripts/chat_cli.py`: tương tác hỏi đáp trong terminal, duy trì lịch sử 4 lượt gần nhất, hiển thị câu trả lời, nguồn trích dẫn (tên file, Điều, điểm số), cờ cảnh báo số lạ `unsupported_numbers`, lý do từ chối (nếu có), thời gian truy xuất và tổng thời gian. Gõ `/q` để thoát. Tự động gọi `bm25_index.rebuild()` khi khởi động. Không ghi câu hỏi/câu trả lời ra file. Thử nghiệm với `LLM_PROVIDER=mock`.
  2. Xây dựng công cụ đánh giá benchmark `scripts/chay_cau_hoi_thu.py`: đọc bộ câu hỏi kiểm thử từ `ai-service/data/cau_hoi_thu.csv` (UTF-8 BOM), lọc theo `--tap` (mặc định `dev`), bỏ qua câu hỏi rỗng. Hỗ trợ các tham số: `--mode` (`dense`, `bm25`, `hybrid`), `--retrieval-only` (không gọi LLM sinh chữ), `--max-calls` (dừng trước khi vượt hạn mức, mặc định 30).
  3. Đo lường chính xác các chỉ số:
     - Đo truy xuất: kiểm tra từng cụm trong `must_have` có nằm trong các chunk được truy xuất hay không (so sánh sau khi chuẩn hóa Unicode NFC và không phân biệt hoa thường).
     - Đo sinh câu trả lời: kiểm tra cụm `must_have` có nằm trong câu trả lời sinh ra hay không (chỉ khi không dùng `--retrieval-only`).
     - Tỷ lệ trúng Điều (`hit expected_dieu`): trúng nếu có ít nhất một đoạn truy xuất thuộc một trong các Điều kỳ vọng.
     - Tỷ lệ từ chối: đối chiếu giữa kỳ vọng (`expected_refuse`) và thực tế bot từ chối.
  4. Đo thời gian chi tiết (Timing Breakdown) cho mỗi câu: tách bạch thời gian embedding câu hỏi, Qdrant search, BM25 search, LLM generation, và tổng thời gian.
  5. Xuất kết quả chi tiết ra file JSON tại `ai-service/evaluation/benchmarks_result/` kèm cấu hình chạy (git commit, chat model, embedding model, top_k, candidate_k, min_dense_score, mode, tập, thời gian, số lần gọi API).
  6. Trong khung chat: chỉ in bảng tổng hợp theo từng nhóm câu hỏi (số câu, tỷ lệ must_have trong đoạn, tỷ lệ must_have trong câu trả lời, tỷ lệ hit Điều, tỷ lệ từ chối đúng/nhầm, thời gian trung bình). Tuyệt đối KHÔNG in nội dung quy chế, văn bản trích dẫn hay câu trả lời của AI ra chat.
  7. Viết bộ unit test toàn diện cho logic đánh giá bằng dữ liệu giả lập, không gọi API.
  8. Phân tích nguyên nhân khả dĩ của độ trễ ~25s quan sát được ở các phiên trước dựa trên số liệu đo đạc thực tế, không tự ý đổi cấu hình RAG.
- **Ràng buộc cứng:**
  - KHÔNG đổi logic RAG, KHÔNG đổi model, ngưỡng, prompt hay cấu hình.
  - KHÔNG cài thêm thư viện mới.
  - KHÔNG tự ghi hay sửa nhãn đáp án của bộ kiểm thử đánh giá.
  - KHÔNG gọi API trả phí quá 30 lượt (dự toán trước khi chạy).
  - Chỉ chạy `chay_cau_hoi_thu.py` ở chế độ `--retrieval-only` với `--mode hybrid`.

---

## 2. Bảng quyết định thiết kế (Design Decisions)

| Quyết định | Phương án đã cân nhắc | Vì sao chọn | Loại căn cứ |
|---|---|---|---|
| Tách đo thời gian chi tiết (Timing Breakdown) | A: Chỉ đo tổng thời gian truy xuất và tổng thời gian RAG.<br>**B: Bổ sung trường `timing` vào `hybrid_retriever.py`, `dense_search.py` và `rag_pipeline.py`** | Yêu cầu mục (4) đòi hỏi tách riêng thời gian: embedding câu hỏi, Qdrant, BM25, LLM. Cần tách ở tầng retrieval để phân tích chính xác nguyên nhân độ trễ ~25s. | [tài liệu: yêu cầu phiên 3C] |
| Tách embedding và Qdrant query | A: Sửa hàm `dense_search` nhận vector hoặc query.<br>**B: Thêm hàm `dense_search_with_vector(query_vector, ...)` trong `dense_search.py`** | Giữ nguyên 100% tính tương thích ngược của hàm `dense_search(query, ...)`, không làm ảnh hưởng các nơi đang gọi cũ. | [kỹ thuật] |
| Cơ chế quản lý bộ nhớ 4 lượt của `chat_cli` | A: Tự lưu text thô.<br>**B: Quản lý danh sách `history = [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]` cắt tối đa 4 lượt (8 messages)** | Khớp chuẩn format `history` mà `rag_pipeline.prepare` và `prompts.build_messages` đang tiêu thụ. | [kỹ thuật] |
| Xử lý cấu trúc file `data/cau_hoi_thu.csv` | A: Tự động ghi đè dữ liệu mới vào `cau_hoi_thu.csv`.<br>**B: Viết parser chuẩn theo 8 cột yêu cầu; nếu file thiếu cột thì báo lỗi rõ ràng; người dùng tự cung cấp dữ liệu đánh giá** | Tuân thủ tuyệt đối quy tắc cứng trong GEMINI.md: "Không bao giờ tự ghi hay sửa nhãn đáp án của bộ kiểm thử đánh giá". | [tài liệu: GEMINI.md] |
| So khớp chuỗi `must_have` | A: Dùng regex phức tạp.<br>**B: Chuẩn hóa `unicodedata.normalize("NFC", text).lower()` và kiểm tra chuỗi con `in`** | Nhẹ, chính xác cao cho tiếng Việt, xử lý triệt để khác biệt giữa Unicode tổ hợp và dựng sẵn. | [kỹ thuật] |

---

## 3. Danh sách file thay đổi

| STT | File | Hành động | Mục đích |
|---|---|---|---|
| 1 | `ai-service/scripts/chat_cli.py` | Tạo mới | Vòng lặp chat terminal, nhớ 4 lượt, hiển thị nguồn, thời gian, unsupported_numbers, thoát `/q`. |
| 2 | `ai-service/scripts/chay_cau_hoi_thu.py` | Tạo mới | Chạy bộ benchmark từ CSV, đo `must_have` (retrieval/answer), hit Điều, tỷ lệ từ chối, xuất JSON và in bảng tổng hợp. |
| 3 | `ai-service/app/pipeline/retrieval/dense_search.py` | Sửa | Thêm hàm `dense_search_with_vector` phục vụ tách đo thời gian embedding vs Qdrant. |
| 4 | `ai-service/app/pipeline/retrieval/hybrid_retriever.py` | Sửa | Đo thời gian chi tiết embedding_ms, qdrant_ms, bm25_ms và trả về trong kết quả `retrieve`. |
| 5 | `ai-service/app/pipeline/rag_pipeline.py` | Sửa | Bổ sung `timing` vào `Prepared` và `answer()` (đo thêm `llm_ms`, `total_ms`). |
| 6 | `ai-service/tests/test_core.py` | Sửa | Thêm lớp test `TestBenchmarkEvaluation` kiểm thử toàn diện bằng dữ liệu giả lập. |
| 7 | `docs/plans/2026-10-14-phien-3c-chat-va-chay-cau-hoi-thu.md` | Tạo mới | Kế hoạch chi tiết Phiên 3C. |
| 8 | `docs/journal/2026-10-14-phien-3c-chat-va-chay-cau-hoi-thu.md` | Tạo mới | Nhật ký phiên làm việc. |
| 9 | `docs/progress.md` & `docs/decisions.md` | Sửa | Cập nhật tiến độ và quyết định. |

---

## 4. Kế hoạch kiểm thử (Test Plan)

### A. Unit Tests mới trong `tests/test_core.py`:
1. `test_parse_cau_hoi_thu_csv_and_filter_tap`: Đọc CSV mẫu giả lập, lọc đúng tập `dev`, bỏ qua các dòng rỗng và đếm đúng số dòng bỏ qua.
2. `test_must_have_matching_nfc_and_case_insensitive`: Đối chiếu cụm từ khóa `must_have` chính xác kể cả khi văn bản dùng Unicode tổ hợp vs dựng sẵn hoặc chữ hoa/chữ thường.
3. `test_expected_dieu_hit_detection`: Phát hiện trúng Điều khi ít nhất một chunk trích xuất thuộc Điều kỳ vọng (hỗ trợ nhiều Điều ngăn cách bằng `|`).
4. `test_refusal_matching_metrics`: Tính đúng tỷ lệ từ chối đúng (True Refuse) và từ chối nhầm (False Refuse).
5. `test_export_benchmark_json_structure`: Kiểm tra file JSON xuất ra chứa đầy đủ các trường cấu hình (git commit, models, top_k, timing breakdown...).

### B. Lệnh kiểm tra thực tế:
1. Chạy 53 unit test cũ + các test mới:
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m unittest discover -s tests -v
   ```
2. Thử nghiệm `chat_cli.py` với Mock LLM (0 VND):
   ```powershell
   $env:PYTHONUTF8="1"; $env:LLM_PROVIDER="mock"; venv\Scripts\python.exe -m scripts.chat_cli
   ```
   (Nhập câu hỏi thử, kiểm tra thông tin in ra, gõ `/q` thoát).
3. Chạy `chay_cau_hoi_thu.py` với `--retrieval-only` trên kho thật:
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.chay_cau_hoi_thu --mode hybrid --retrieval-only --tap dev --max-calls 30
   ```

---

## 5. Rủi ro & Điểm cần lưu ý

1. **Tệp `data/cau_hoi_thu.csv` trên đĩa**: Hiện tại file này đang chứa bảng kết quả khảo sát biểu mẫu (55 dòng) chứ chưa có cấu trúc các cột benchmark (`id, nhom, cau_hoi, expected_dieu, must_have, expected_refuse, tap, ghi_chu`).
   - *Biện pháp:* Script sẽ kiểm tra cấu trúc cột và báo lỗi rõ ràng nếu thiếu cột. Khi người dùng cung cấp file câu hỏi kiểm thử đúng định dạng, script sẽ đọc và chạy ngay.
2. **Hạn mức API**: Chế độ `--retrieval-only` chỉ gọi API embedding cho mỗi câu hỏi (0 gọi LLM chat). Với 10-20 câu kiểm thử, số lệnh gọi sẽ $\le 20 < 30$, hoàn toàn miễn phí và an toàn.
