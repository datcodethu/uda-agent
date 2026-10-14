# Kế hoạch Phiên 4C: Gỡ tài liệu không còn duyệt và thêm cảnh báo bất thường

**Ngày lập:** 2026-10-13  
**Phiên làm việc:** 4C  
**Trạng thái:** CHỜ DUYỆT (Artifact Review)  

---

## 1. Hiểu nhiệm vụ (Understanding)
- **Mục tiêu chính:**
  1. Thêm cờ `--prune` vào `scripts/ingest_approved.py`: so khớp danh sách tài liệu trong kho (`chunk_store.list_documents()`) với danh sách tài liệu được phê duyệt. Mặc định là dry-run (chỉ liệt kê tài liệu sẽ bị gỡ, số đoạn, lý do); chỉ gỡ thật khi có cả `--apply` và `--prune` (dùng `index_service.remove_document` và dựng lại BM25).
  2. Thêm kiểm tra bất thường (anomaly check) cho mỗi file được duyệt (chạy ở cả dry-run và apply): nếu tài liệu có từ 10 đoạn trở lên mà một cặp nhãn `(phan_van_ban, dieu)` chiếm > 50% số đoạn thì đánh dấu **NGHI NGỜ CẮT SAI** và **CHẶN** không nạp, trừ khi có cờ `--allow-anomaly`. Ngưỡng cấu hình thành hằng số dễ sửa (`ANOMALY_MIN_CHUNKS = 10`, `ANOMALY_RATIO_THRESHOLD = 0.50`).
  3. Thêm cờ `--status` in tình trạng kho: mỗi tài liệu một dòng gồm `doc_name`, số đoạn, `status`, `effective_date`; kiểm tra `chunk_id` có trùng trên toàn kho không (báo số lượng trùng, kỳ vọng 0), in tổng số tài liệu và tổng số đoạn. Chỉ in số liệu, không in nội dung quy chế.
  4. Đảm bảo giá trị `loai = huong_dan` hợp lệ trong bảng đăng ký nhưng KHÔNG được nạp vào kho quy chế; dry-run in lý do chặn cụ thể.
  5. Thêm bộ test toàn diện trong `tests/test_core.py` sử dụng dữ liệu giả lập và thư mục tạm.
  6. Ghi vào `docs/todo.md` hai việc để sau: bộ nhận đề mục thập phân (chỉ bật khi không có Điều thật) và bổ sung số trang vào metadata.
  7. Cuối phiên: chạy dry-run với `--prune` và `--status` trên kho thật, báo cáo số liệu (dry-run phải liệt kê file 2024 là tài liệu sẽ bị gỡ với 44 đoạn). **TUYỆT ĐỐI KHÔNG CHẠY `--apply --prune`** trên kho thật.
- **Ràng buộc cứng:**
  - KHÔNG gọi API (0 VND).
  - KHÔNG sửa `structural_chunker.py`.
  - KHÔNG sửa `docs_registry.csv` (người dùng tự sửa qua Excel).
  - KHÔNG sửa test cũ có từ trước (46 test PASS).
  - KHÔNG đổi model, ngưỡng hay config trong `config.py`.
  - KHÔNG in nội dung quy chế ra khung chat.

---

## 2. Bảng quyết định thiết kế (Design Decisions)

| Quyết định | Phương án đã cân nhắc | Vì sao chọn | Loại căn cứ |
|---|---|---|---|
| Cơ chế gỡ tài liệu (`--prune`) | A: Viết script riêng `prune_documents.py`<br>**B: Tích hợp cờ `--prune` vào `scripts/ingest_approved.py`** | Tập trung toàn bộ quy trình kiểm duyệt và đồng bộ kho quy chế tại một đầu mối duy nhất; bảng đăng ký `docs_registry.csv` là nguồn chân lý. | [tài liệu: yêu cầu phiên 4C] |
| Cơ chế xóa vector & chunk | A: Tự xóa thủ công từng bảng/file<br>**B: Dùng `index_service.remove_document(doc_name)`** | Hàm đã có sẵn cơ chế xóa Qdrant (`delete_document`), xóa chunk JSONL (`delete_document`), và tự động dựng lại BM25 (`bm25_index.rebuild()`). | [kỹ thuật] |
| Vị trí kiểm tra bất thường (Anomaly Check) | A: Kiểm tra sau khi nạp vào Qdrant<br>**B: Kiểm tra ngay sau khi cắt đoạn trong `run_ingest`** | Phát hiện lỗi sớm trước khi nạp vào DB; hoạt động đồng nhất trên cả dry-run và apply; ngăn chặn kịp thời dữ liệu bẩn. | [kỹ thuật] |
| Cấu trúc ngưỡng bất thường | A: Hardcode số 10 và 50% trong hàm<br>**B: Đặt hằng số cấp module `ANOMALY_MIN_CHUNKS = 10`, `ANOMALY_RATIO_THRESHOLD = 0.50`** | Dễ bảo trì, dễ điều chỉnh ngưỡng và dễ kiểm thử với các bộ dữ liệu khác nhau. | [tài liệu: yêu cầu phiên 4C] |
| Nguồn dữ liệu cho `--status` | A: Query trực tiếp từ Qdrant<br>**B: Đọc từ `chunk_store.load_all()`** | Kho JSONL là nguồn sự thật chứa đầy đủ metadata (`effective_date`, `status`, `doc_name`, `chunk_id`), không phụ thuộc Qdrant đang bật hay tắt. | [kỹ thuật] |

---

## 3. Danh sách file thay đổi

| STT | File | Hành động | Mục đích |
|---|---|---|---|
| 1 | `ai-service/scripts/ingest_approved.py` | Sửa | Thêm cờ `--prune`, `--status`, `--allow-anomaly`; hàm `check_chunking_anomaly`, `check_duplicate_chunk_ids`, `print_store_status`, `prune_unapproved_documents`. |
| 2 | `ai-service/tests/test_core.py` | Sửa | Thêm lớp `TestIngestPruneAndAnomaly` kiểm thử toàn diện bằng dữ liệu giả lập. |
| 3 | `docs/todo.md` | Sửa | Ghi 2 việc tồn đọng (bộ nhận đề mục thập phân và metadata số trang). |
| 4 | `docs/plans/2026-10-13-phien-4c-go-tai-lieu-va-canh-bao.md` | Tạo mới | Kế hoạch chi tiết của phiên 4C. |
| 5 | `docs/journal/2026-10-13-phien-4c-go-tai-lieu-va-canh-bao.md` | Tạo mới | Nhật ký phiên làm việc (tạo sau khi hoàn thành). |
| 6 | `docs/progress.md` & `docs/decisions.md` | Sửa | Cập nhật tiến độ và quyết định sau khi hoàn thành. |

---

## 4. Kế hoạch kiểm thử (Test Plan)

### A. Test tự động (Unit Test mới trong `tests/test_core.py`):
1. `test_anomaly_detection_blocks_file`: Chunk giả lập >= 10 đoạn có 1 nhãn chiếm > 50% bị chặn với thông báo "NGHI NGỜ CẮT SAI".
2. `test_normal_distribution_not_blocked`: Chunk giả lập phân bố đều không bị chặn.
3. `test_allow_anomaly_bypasses_block`: Cờ `--allow-anomaly` cho phép file bất thường vượt qua.
4. `test_duplicate_chunk_id_detected`: Phát hiện chính xác mã `chunk_id` trùng lặp trong dữ liệu giả lập.
5. `test_prune_dry_run_leaves_store_unchanged`: Dry-run prune liệt kê đúng tài liệu sẽ bị gỡ, không thay đổi file `chunks.jsonl`.
6. `test_prune_apply_removes_unapproved_doc`: Apply prune gỡ đúng tài liệu không còn duyệt, giữ nguyên tài liệu còn duyệt.
7. `test_loai_huong_dan_blocked_with_specific_reason`: Kiểm tra giá trị `loai=huong_dan` hợp lệ trong bảng nhưng bị chặn với lý do rõ ràng.

### B. Lệnh kiểm tra thực tế:
1. Chạy toàn bộ unit test:
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m unittest discover -s tests -v
   ```
2. Chạy dry-run `--prune` và `--status` trên kho thật:
   ```powershell
   $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.ingest_approved --prune --status
   ```
   *Kỳ vọng:*
   - Liệt kê file `2024_11_14_14_26_46A` là tài liệu sẽ bị gỡ với 44 đoạn.
   - Bảng status hiển thị đúng 2 tài liệu (65 đoạn) và 0 chunk trùng.

---

## 5. Rủi ro & Biện pháp phòng ngừa

| Rủi ro | Mức độ | Biện pháp phòng ngừa |
|---|---|---|
| Lỡ tay gỡ nhầm dữ liệu thật trong kho | Cao | Mặc định `--prune` chỉ chạy ở chế độ Dry-Run. Tuyệt đối không chạy `--apply --prune` trên kho thật trong phiên này (để người dùng tự chạy). |
| Bảng `docs_registry.csv` chưa được người dùng lưu | Trung bình | Nhắc nhở người dùng kiểm tra lưu file `docs_registry.csv` với `loai=huong_dan`. Trong mã nguồn, xử lý an toàn nếu cả 2 file đều còn duyệt thì anomaly check vẫn sẽ phát hiện và chặn file 2024. |
| Rebuild BM25 gặp lỗi khi gỡ tài liệu | Thấp | Sử dụng trực tiếp `index_service.remove_document` đã được kiểm thử ổn định ở các bước trước. |
