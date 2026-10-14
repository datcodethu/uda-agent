# Nhật ký 2026-10-13 – Phiên 4C: Gỡ tài liệu không còn duyệt và thêm cảnh báo bất thường

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Bổ sung tính năng dọn kho (`--prune`) để phát hiện và gỡ các văn bản không còn được duyệt ra khỏi kho vector/BM25, đồng thời xây dựng hàng rào cảnh báo tự động chặn các văn bản bị nghi ngờ cắt sai cấu trúc (>50% số đoạn dồn vào 1 Điều).

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/ingest_approved.py` | Bổ sung cờ `--prune`, `--status`, `--allow-anomaly`; tích hợp hàm `check_chunking_anomaly`, `check_duplicate_chunk_ids`, `print_store_status`, `prune_unapproved_documents`. |
| `ai-service/tests/test_core.py` | Thêm lớp `TestIngestPruneAndAnomaly` với 7 unit test (53/53 test PASS). |
| `docs/todo.md` | Ghi nhận 2 việc để sau: bộ nhận đề mục thập phân và metadata số trang. |
| `docs/plans/2026-10-13-phien-4c-go-tai-lieu-va-canh-bao.md` | Kế hoạch chi tiết của Phiên 4C. |
| `docs/progress.md` & `docs/decisions.md` | Cập nhật tiến độ Phiên 4C và quyết định chốt cơ chế gỡ / cảnh báo. |

## 3. Vì sao làm như vậy
- Quyết định: Tích hợp `--prune` và anomaly check vào ngay `scripts/ingest_approved.py`.
- Phương án đã cân nhắc: Viết script dọn dẹp riêng `prune_documents.py`.
- Vì sao chọn: Cổng nạp `ingest_approved.py` là nơi quản lý toàn bộ vòng đời của văn bản (từ duyệt, cắt, nạp đến gỡ). Tập trung tại một file giúp đồng nhất nguồn chân lý từ `docs_registry.csv`.
- Vì sao loại phương án còn lại: Script riêng dễ gây phân tán logic kiểm tra điều kiện phê duyệt và rủi ro lệch đồng bộ giữa kho và bảng đăng ký.
- Loại căn cứ: [tài liệu: yêu cầu phiên 4C] & [kỹ thuật]
- Đánh đổi: File `ingest_approved.py` dài thêm ~150 dòng mã nhưng bảo đảm tính toàn vẹn 100%.

- Quyết định: Đặt ngưỡng bất thường `ANOMALY_MIN_CHUNKS = 10` và `ANOMALY_RATIO_THRESHOLD = 0.50`.
- Phương án đã cân nhắc: Hardcode số liệu bên trong hàm cắt đoạn.
- Vì sao chọn: Khai báo hằng số module giúp kiểm thử dễ dàng, dễ bảo trì và có thể tinh chỉnh trong tương lai khi có tài liệu đặc thù.
- Loại căn cứ: [kỹ thuật]

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Pruning (Cắt tỉa/Dọn kho):** Giống như việc bạn dọn tủ sách. Danh sách sách được phép trưng bày là bảng đăng ký. Khi một cuốn sách bị loại khỏi danh mục duyệt (hoặc hết hạn), lệnh prune sẽ tìm những cuốn đang nằm trên giá nhưng không có trong danh mục để hạ xuống (xóa vector trong Qdrant và xóa khỏi file JSONL).
- **Anomaly Detection (Phát hiện bất thường dữ liệu):** Giống như một cái cân kiểm tra tại dây chuyền đóng gói. Nếu một gói kẹo có 44 chiếc mà 41 chiếc kẹo dồn hết vào một ngăn duy nhất (>50%), máy sẽ báo còi nghi ngờ đóng gói sai và dừng dây chuyền, thay vì tiếp tục chuyển vào kho.

## 5. Đã kiểm tra thế nào
- Lệnh:
  ```powershell
  $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m unittest discover -s tests -v
  $env:PYTHONUTF8="1"; venv\Scripts\python.exe -m scripts.ingest_approved --prune --status
  ```
- Kết quả thật (dán):
  - Chạy unittest: `Ran 53 tests in 2.951s -> OK`.
  - Chạy dry-run `--prune --status`:
    - `[DANH SÁCH FILE ĐƯỢC PHÊ DUYỆT]`: 2023 nạp được (21 đoạn); 2024 bị `[CHẶN - NGHI NGỜ CẮT SAI]` do Điều 3 chiếm 93.2%.
    - `DANH SÁCH TÀI LIỆU SẼ BỊ GỠ (DRY-RUN --prune) (1 tài liệu)`: `[SẼ GỠ] 2024_11_14_14_26_46A: 44 đoạn`.
    - `TÌNH TRẠNG KHO VĂN BẢN QUY CHẾ`: Tổng số tài liệu: 2, Tổng số đoạn: 65, Trùng chunk_id: 0.
- Kết luận: ĐẠT.
- Số lệnh gọi API trả phí đã dùng: 0 lệnh (0 VND).

## 6. Chưa chắc chắn, rủi ro, giả định
- Giả định: File `docs_registry.csv` trên máy người dùng sẽ được cập nhật cột `loai = huong_dan`. Hiện tại ngay cả khi chưa đổi cột, hàng rào `check_chunking_anomaly` vẫn bắt đúng và chặn an toàn file 2024.

## 7. Điều đã không làm và lý do
- Tuyệt đối không chạy `--apply --prune` trên kho thật: Để người dùng tự chạy theo đúng quy tắc an toàn dữ liệu.
- Không sửa `structural_chunker.py`: Phạm vi phiên chỉ là gỡ và chặn bất thường.

## 8. Việc tiếp theo
- Người dùng kiểm tra lưu file `docs_registry.csv` và chạy lệnh gỡ thật:
  `venv\Scripts\python.exe -m scripts.ingest_approved --apply --prune`
- Triển khai bộ nhận đề mục thập phân ở các phiên sau.

## 9. Câu hỏi cho người dùng
- Bạn có muốn tự chạy lệnh gỡ `--apply --prune` ngay bây giờ hay cần kiểm tra thêm điều gì khác?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao cơ chế prune cần đối chiếu với `chunk_store.list_documents()` thay vì chỉ đọc danh sách file trên ổ đĩa?
2. Tại sao hàng rào Anomaly Check lại yêu cầu `min_chunks >= 10` thay vì kiểm tra mọi văn bản?
3. Nếu một văn bản bị gỡ bằng `remove_document`, hệ thống tìm kiếm BM25 có tự động cập nhật không?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì kho vector và BM25 chỉ chứa các tài liệu đã từng được nạp (`chunks.jsonl`), nhiều file trên đĩa chưa từng được nạp nên không thể "gỡ" khỏi kho.
2. Với các văn bản rất ngắn (dưới 10 đoạn, ví dụ chỉ có 2-3 Điều ngắn), việc một Điều chiếm trên 50% số đoạn là hoàn toàn bình thường (ví dụ văn bản có 2 đoạn thì 1 đoạn đã là 50%), chỉ khi văn bản dài mà tỷ lệ dồn quá cao mới là bất thường cắt sai.
3. Có. Hàm `remove_document` trong `index_service.py` tự động gọi `bm25_index.rebuild()` ngay sau khi xóa vector và chunk JSONL.

</details>
