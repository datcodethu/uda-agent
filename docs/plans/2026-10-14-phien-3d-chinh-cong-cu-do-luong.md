# Kế hoạch Phiên 3D: Chỉnh công cụ đo lường Benchmark

**Ngày lập:** 2026-10-14  
**Phiên làm việc:** 3D  
**Trạng thái:** ĐÃ DUYỆT (Người dùng duyệt Phương án A kèm 6 điều kiện thực thi)  

---

## 1. Hiểu nhiệm vụ (Understanding)
- **Mục tiêu:**
  1. Giải trình rõ ràng lý do `hybrid_retriever.py` được chỉnh sửa ở Phiên 3C, tóm tắt diff chi tiết, xác nhận kiểm tra tính tương đương và đề xuất hướng xử lý (giữ nguyên để đo thời gian hoặc hoàn lại nếu người dùng yêu cầu).
  2. Bổ sung tham số `--csv` trong `scripts/chay_cau_hoi_thu.py`, mặc định trỏ về `ai-service/data/cau_hoi_thu.csv` (có cơ chế tương thích nếu file mang tên `cau_hoi_thu_v2.csv`).
  3. Xử lý chuẩn xác chỉ số từ chối ở chế độ `--retrieval-only`: hiển thị `N/A` (cả trong bảng in và JSON `rate: null`), không hiển thị `0%` gây hiểu nhầm.
  4. Thu thập và in danh sách các cụm `must_have` bị THIẾU trong các đoạn truy xuất cho từng câu hỏi, hiển thị kèm `id` câu và danh sách `chunk_id` đã truy xuất; tuyệt đối chỉ in cụm ngắn và mã chunk, không in nội dung văn bản.
  5. Xuất thêm file CSV UTF-8 có BOM (`utf-8-sig`) tại thư mục `evaluation/benchmarks_result/` với 9 cột chuẩn để người dùng mở bằng Excel chấm tay (`id, nhom, cau_hoi, cau_tra_loi, nguon, bot_refused, tong_ms, cham_tay, ghi_chu`). Tuyệt đối không in câu trả lời ra khung chat.
  6. Viết bộ unit test mới toàn diện cho các tính năng trên bằng dữ liệu giả lập, không sửa test cũ.
- **Ràng buộc cứng:**
  - KHÔNG đổi logic RAG, KHÔNG gọi API trả phí (chỉ chạy `--retrieval-only` với mock/embedding có sẵn).
  - KHÔNG đổi model, ngưỡng, prompt hay cấu hình.
  - KHÔNG cài thêm thư viện mới, không dùng web, không đọc hay in `.env`.
  - KHÔNG in nội dung quy chế hoặc câu trả lời AI ra khung chat.
  - Chạy lệnh theo PowerShell 5.1, gọi trực tiếp `venv\Scripts\python.exe`, đặt `$env:PYTHONUTF8="1"`.
  - Dừng chờ người dùng duyệt kế hoạch trước khi chỉnh sửa mã nguồn.

---

## 2. Báo cáo giải trình về `hybrid_retriever.py`

### 2.1. Vì sao `hybrid_retriever.py` bị sửa ở Phiên 3C?
Ở Phiên 3C, mục (4) của yêu cầu giao việc nêu rõ:
> *"Thời gian chia nhỏ cho mỗi câu: embedding câu hỏi, Qdrant, BM25, LLM, tổng; nếu cần tách thời gian phải sửa app/pipeline/rag_pipeline.py thì chỉ ở mức đo thời gian và nêu trong kế hoạch."*

Trước Phiên 3C, hàm `hybrid_retriever.retrieve()` gọi trực tiếp `dense_search(expanded, settings.candidate_k)`. Bên trong hàm `dense_search`, việc gọi API `embed_query()` (mạng HTTPS sang Google AI Studio) và việc tìm kiếm vector trong CSDL cục bộ `client.query_points()` bị gộp chung làm một khối, khiến hệ thống không thể tách bạch được thời gian embedding câu hỏi (`embedding_ms`) và thời gian truy vấn vector (`qdrant_ms`).

Để đo đạc chính xác nút thắt thời gian (phân tích nguyên nhân độ trễ ~25s), `hybrid_retriever.py` đã được tách lệnh gọi `embed_query` và `dense_search_with_vector` ra hai bước độc lập để bấm giờ bằng `time.perf_counter()`.

### 2.2. Tóm tắt Diff của `hybrid_retriever.py`
Toàn bộ thay đổi gồm đúng 15 dòng code thuần bấm giờ:
- Thêm `import time`.
- Tách khối tìm kiếm dense:
  ```python
  # 1. Đo thời gian nhúng vector (Gemini Embedding)
  t_emb_0 = time.perf_counter()
  query_vector = embed_query(expanded)
  emb_ms = int((time.perf_counter() - t_emb_0) * 1000)

  # 2. Đo thời gian tìm kiếm vector trong Qdrant
  t_qdrant_0 = time.perf_counter()
  dense = dense_search_with_vector(query_vector, settings.candidate_k)
  qdrant_ms = int((time.perf_counter() - t_qdrant_0) * 1000)

  # 3. Đo thời gian tìm kiếm BM25
  t_bm25_0 = time.perf_counter()
  bm25 = bm25_index.search(expanded, settings.candidate_k) if mode in ("bm25", "hybrid") else []
  bm25_ms = int((time.perf_counter() - t_bm25_0) * 1000)
  ```
- Gắn thêm trường `"timing": {"embedding_ms": emb_ms, "qdrant_ms": qdrant_ms, "bm25_ms": bm25_ms}` vào dictionary kết quả trả về.
- **Cam kết:** Toàn bộ thuật toán xếp hạng, công thức dung hợp RRF, thứ tự và điểm số các chunk hoàn toàn KHÔNG bị thay đổi bất kỳ ký tự nào.

### 2.3. Xác nhận kiểm tra tương đương
Unit test `test_retrieve_same_chunks_and_scores_with_dense_search_with_vector` trong `tests/test_core.py` đã kiểm tra và chứng minh thực nghiệm:
Hàm `retrieve(..., mode="dense")` trả về đúng số lượng chunk, đúng từng `chunk_id` theo đúng thứ tự và điểm số `rank_score` trùng khớp tuyệt đối với `dense_search()` cũ.

### 2.4. Đề xuất
- **Phương án A (Khuyến nghị giữ nguyên):** Giữ nguyên thay đổi hiện tại của `hybrid_retriever.py`. Mã nguồn sạch sẽ, không ảnh hưởng logic RAG, và cung cấp số liệu phân rã thời gian chính xác cho người dùng.
- **Phương án B (Hoàn lại nếu người dùng yêu cầu):** Hoàn lại `hybrid_retriever.py` về nguyên bản 35 dòng. Khi đó, `retrieve()` sẽ chỉ trả về `chunks, best_dense_score, expanded_query`, và hệ thống benchmark sẽ chỉ đo được tổng thời gian truy xuất `retrieval_ms` (không tách được `embedding_ms` và `qdrant_ms`).

---

## 3. Bảng quyết định thiết kế (Design Decisions)

| Quyết định | Phương án đã cân nhắc | Vì sao chọn | Loại căn cứ |
|---|---|---|---|
| Xử lý tham số `--csv` và đường dẫn file | A: Bắt buộc file phải tên `cau_hoi_thu.csv`.<br>**B: Mặc định là `cau_hoi_thu.csv`, nếu chưa có thì kiểm tra fallback sang `cau_hoi_thu_v2.csv`; nhận tham số `--csv <path>` tùy ý** | Linh hoạt tối đa cho người dùng khi đổi tên file trên Windows hoặc chỉ định các bộ dữ liệu khác nhau. | [tài liệu: yêu cầu phiên 3D] |
| Hiển thị chỉ số từ chối ở `--retrieval-only` | A: Vẫn hiển thị `0.0% (0/N)`.<br>**B: Đặt `rate = None` trong JSON và in `N/A` trong bảng** | Ở chế độ retrieval-only, hệ thống chưa chạy LLM nên không thể đo từ chối. Hiển thị 0% gây hiểu lầm là bot từ chối sai hoặc trượt. | [tài liệu: yêu cầu phiên 3D] |
| Định dạng danh sách `must_have` bị thiếu | A: Ghi trong một dòng dài trong JSON.<br>**B: Ghi trường `missing_must_have` trong từng câu ở JSON, và in bảng riêng hiển thị ID câu, danh sách cụm thiếu, danh sách chunk_id truy xuất** | Dễ quan sát ngay trên terminal, chỉ hiển thị cụm ngắn và mã chunk, tuân thủ tuyệt đối quy tắc không in văn bản đoạn ra chat. | [kỹ thuật & quy tắc dự án] |
| Xuất file CSV UTF-8 BOM cho Excel | A: Dùng encoding UTF-8 thông thường.<br>**B: Dùng encoding `utf-8-sig` (UTF-8 có BOM), đầy đủ 9 cột yêu cầu, cột `cham_tay` để trống** | Excel trên Windows khi mở UTF-8 không có BOM sẽ bị lỗi font tiếng Việt. `utf-8-sig` giúp Excel tự động nhận diện tiếng Việt có dấu hoàn hảo. | [kỹ thuật] |

---

## 4. Danh sách file thay đổi

| STT | File | Hành động | Mục đích |
|---|---|---|---|
| 1 | `ai-service/scripts/chay_cau_hoi_thu.py` | Sửa | Thêm `--csv`, hiển thị `N/A` từ chối khi retrieval-only, ghi nhận cụm thiếu `missing_must_have`, xuất CSV UTF-8 BOM 9 cột, in bảng cụm thiếu. |
| 2 | `ai-service/tests/test_core.py` | Sửa | Thêm lớp/hàm test mới kiểm tra: `--csv`, `N/A` từ chối, `missing_must_have`, và định dạng file CSV UTF-8 BOM. Không sửa test cũ. |
| 3 | `ai-service/app/pipeline/retrieval/hybrid_retriever.py` | Giữ nguyên (hoặc Hoàn lại) | Chờ người dùng quyết định duyệt giữ nguyên để đo thời gian hay hoàn lại. |
| 4 | `docs/plans/2026-10-14-phien-3d-chinh-cong-cu-do-luong.md` | Tạo mới | Kế hoạch chi tiết Phiên 3D. |
| 5 | `docs/journal/2026-10-14-phien-3d-chinh-cong-cu-do-luong.md` | Tạo mới | Nhật ký làm việc sau khi thực thi xong. |
| 6 | `docs/progress.md` & `docs/decisions.md` | Sửa | Cập nhật tiến độ và quyết định sau khi hoàn thành. |

---

## 5. Kế hoạch kiểm thử (Test Plan)

### A. Unit Tests mới trong `tests/test_core.py`:
1. `test_retrieval_only_refusal_metrics_are_na`: Kiểm chứng khi `retrieval_only=True`, cả `true_refuse` và `false_refuse` đều có `rate=None`, hiển thị `N/A`.
2. `test_missing_must_have_tracking`: Kiểm chứng phát hiện chính xác danh sách cụm `missing_must_have` khi đoạn văn bản trích xuất không chứa cụm đó, lưu kèm `retrieved_chunk_ids`.
3. `test_export_benchmark_csv_format_and_bom`: Kiểm chứng xuất file CSV UTF-8 BOM (`utf-8-sig`) chứa đúng 9 cột (`id, nhom, cau_hoi, cau_tra_loi, nguon, bot_refused, tong_ms, cham_tay, ghi_chu`), `cham_tay` để trống `""`, không lỗi font.
4. `test_parse_args_csv_param`: Kiểm chứng tham số `--csv` nhận đúng file tùy chỉnh và giá trị mặc định.

### B. Kiểm thử thực tế qua lệnh PowerShell:
1. Chạy toàn bộ unit test (kỳ vọng 63/63 PASS):
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m unittest discover -s tests -v
   ```
2. Chạy thử nghiệm benchmark `--retrieval-only`:
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.chay_cau_hoi_thu --mode hybrid --retrieval-only --tap dev --max-calls 30
   ```
3. Kiểm tra file kết quả JSON và CSV xuất ra trong `ai-service/evaluation/benchmarks_result/`.

---

## 6. Rủi ro & Biện pháp phòng ngừa

1. **Tên file trên đĩa (`cau_hoi_thu.csv` vs `cau_hoi_thu_v2.csv`)**: Trên đĩa hiện đang có file `cau_hoi_thu_v2.csv` (1444 bytes).
   - *Biện pháp:* Script sẽ kiểm tra nếu `cau_hoi_thu.csv` tồn tại thì dùng, nếu không có sẽ tự động dùng `cau_hoi_thu_v2.csv`, hoặc nhận đường dẫn từ cờ `--csv`.
2. **Ký tự đặc biệt trong cột `nguon` của CSV**: Định dạng `{chunk_id}|{Dieu}|{score}` có thể chứa dấu chấm phẩy hoặc dấu phẩy.
   - *Biện pháp:* Dùng module chuẩn `csv.writer` / `csv.DictWriter` của Python để tự động bọc dấu ngoặc kép (`"..."`) an toàn theo chuẩn RFC 4180.
