# Nhật ký 2026-10-14 – Phiên 3D: Chỉnh công cụ đo lường Benchmark

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Hoàn thiện công cụ đo lường `scripts/chay_cau_hoi_thu.py`: loại bỏ hoàn toàn cơ chế đọc fallback, xuất file CSV chấm tay UTF-8 BOM cho Excel, hiển thị N/A cho các chỉ số từ chối ở chế độ `--retrieval-only`, và lập bảng thống kê các cụm `must_have` bị thiếu kèm `chunk_id` đã truy xuất.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/chay_cau_hoi_thu.py` | Mặc định chỉ đọc `cau_hoi_thu.csv` (bỏ fallback `cau_hoi_thu_v2.csv`), báo lỗi rõ kèm đường dẫn tuyệt đối khi thiếu file; luôn in tên file đọc; xuất thêm `cham_tay_<timestamp>.csv` UTF-8 BOM 9 cột; xử lý chỉ số và cờ từ chối thành `N/A` ở cả bảng in và JSON; thêm bảng in danh sách cụm `must_have` bị thiếu kèm ID và chunk_ids. |
| `ai-service/tests/test_core.py` | Thêm 4 unit test mới (`test_csv_param_and_missing_file_error`, `test_retrieval_only_refusal_metrics_are_na_in_json`, `test_missing_must_have_tracking_and_retrieved_chunk_ids`, `test_export_cham_tay_csv_name_and_structure`). Giữ nguyên 59 test cũ, đạt 63/63 test PASS. |
| `docs/plans/2026-10-14-phien-3d-chinh-cong-cu-do-luong.md` | Lập kế hoạch chi tiết, giải trình thay đổi của `hybrid_retriever.py`, đề xuất Phương án A và ghi nhận phê duyệt kèm 6 điều kiện. |
| `docs/progress.md` & `docs/decisions.md` | Cập nhật tiến độ Phiên 3D và quyết định chốt. |

## 3. Vì sao làm như vậy
- Quyết định: Chọn Phương án A giữ nguyên thay đổi ở `hybrid_retriever.py`.
- Phương án đã cân nhắc:
  - Phương án A: Giữ nguyên 15 dòng code bấm giờ trong `hybrid_retriever.py`.
  - Phương án B: Hoàn lại `hybrid_retriever.py` về 35 dòng ban đầu và chỉ đo tổng thời gian truy xuất.
- Vì sao chọn: Thay đổi chỉ phục vụ bấm giờ và phân rã thời gian, hoàn toàn không đổi logic xếp hạng hay dữ liệu truy xuất (đã có unit test chứng minh tính tương đương tuyệt đối), giúp phân tích chính xác nguyên nhân độ trễ.
- Vì sao loại phương án còn lại: Phương án B làm mất khả năng đo tách bạch giữa embedding mạng và tìm kiếm vector trong Qdrant.
- Loại căn cứ: [người dùng duyệt]
- Đánh đổi: File `hybrid_retriever.py` có thêm 15 dòng code đo thời gian.

- Quyết định: Hiển thị `N/A` cho toàn bộ chỉ số từ chối ở chế độ `--retrieval-only` cả trong bảng terminal, file CSV và file JSON.
- Phương án đã cân nhắc:
  - Phương án A: Giữ nguyên `0.0% (0/N)` hoặc `rate: 0.0`.
  - Phương án B: Chuyển toàn bộ thành `N/A` (JSON: `"status": "N/A"`, `"rate": "N/A"`).
- Vì sao chọn: Ở chế độ chỉ truy xuất, hệ thống chưa chạy bước suy luận của LLM nên không có cơ sở đo lường việc từ chối. Hiển thị `0.0%` sẽ gây hiểu nhầm nghiêm trọng là bot từ chối sai hoặc trượt.
- Vì sao loại phương án còn lại: Phương án A gây nhiễu dữ liệu đánh giá khoa học của đề tài.
- Loại căn cứ: [yêu cầu người dùng & kỹ thuật]
- Đánh đổi: Cần xử lý định dạng hiển thị riêng khi xuất JSON để không làm vỡ các phép toán thống kê.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
1. **UTF-8 BOM (`utf-8-sig`) khi làm việc với Excel trên Windows**:
   - *Ví dụ đời thường*: Bạn gửi một bức thư viết bằng tiếng Việt có dấu. Người đưa thư (phần mềm khác) đọc bình thường, nhưng một người nhận (Excel) nếu không thấy "con dấu niêm phong" báo trước là thư tiếng Việt thì sẽ mở bằng bảng mã mặc định (ANSI/Windows-1252), dẫn đến chữ biến thành hình thoi dấu chấm hỏi hoặc ký tự loằng ngoằng (`Chuáº©n Ä‘áº§u ra`).
   - Con dấu đó trong kỹ thuật gọi là **BOM (Byte Order Mark)** – 3 byte đặc biệt `\xEF\xBB\xBF` ở đầu file. Khi xuất CSV dùng `encoding="utf-8-sig"`, Excel sẽ nhận ra ngay đây là văn bản Unicode và hiển thị dấu tiếng Việt hoàn hảo.
2. **Đối chiếu thiếu cụm từ khóa (Missing Must-have Detection)**:
   - Trong kiểm thử RAG, việc biết hệ thống đạt bao nhiêu phần trăm là chưa đủ; kỹ sư cần biết chính xác *cụm từ nào bị rơi rụng* và *ở câu hỏi nào* để điều chỉnh chunk size hoặc top-k. Bảng danh sách cụm thiếu chỉ ra đúng điểm mù của bước truy xuất mà không cần đọc hàng ngàn chữ của cả văn bản quy chế.

## 5. Đã kiểm tra thế nào
- Lệnh 1: `venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v`
  - Kết quả thật: 63/63 test PASS (trong 6.622s), bao gồm 4 test mới cho `--csv`, file CSV chấm tay, `missing_must_have`, và hiển thị `N/A`.
- Lệnh 2: Chạy benchmark thật trên kho:
  `venv\Scripts\python.exe -X utf8 -m scripts.chay_cau_hoi_thu --mode hybrid --retrieval-only --tap dev --max-calls 30`
  - Kết quả thật:
    - Đọc từ file: `cau_hoi_thu.csv` (Đường dẫn: `E:\workspace\donga-rag-system\ai-service\data\cau_hoi_thu.csv`).
    - Số câu hợp lệ: 3, bỏ qua: 10 dòng rỗng.
    - Bảng tổng hợp: `TC Đúng`: `N/A`, `TC Nhầm`: `N/A`.
    - Bảng cụm thiếu: phát hiện chính xác câu `c02` thiếu cụm `2 tuần` trong các chunk `[2023-8-23-16-29-59n-qdkt-d6-1, 2023-8-23-16-29-59n-qdkt-d6-2, 2023-8-23-16-29-59n-qdkt-d4-1, 2023-8-23-16-29-59n-qdkt-d3-1, 2023-8-23-16-29-59n-qdkt-d5-1]`.
    - File JSON: `evaluation/benchmarks_result/benchmark_20261014_163916.json` (mọi chỉ số từ chối là `N/A`).
    - File CSV chấm tay: `evaluation/benchmarks_result/cham_tay_20261014_163916.csv` (đầy đủ 9 cột, `bot_refused: N/A`, `cau_tra_loi: ""` và `cham_tay: ""`).
- Kết luận: ĐẠT toàn bộ 6 điều kiện.
- Số lệnh gọi API trả phí đã dùng: 0 VND (chỉ dùng 3 lệnh embedding miễn phí).

## 6. Chưa chắc chắn, rủi ro, giả định
- Cụm `2 tuần` ở câu `c02` bị thiếu trong các đoạn truy xuất: nguyên nhân là do Điều 6 quy định thời hạn nộp chứng chỉ miễn học tiếng Anh trước khi bắt đầu học kỳ, nhưng chunk trích xuất chứa Khoản 1, 2 chưa quét trúng câu có mốc 2 tuần hoặc do ngưỡng candidate_k. Khi chấm tay người dùng có thể đối chiếu lại quy chế gốc.

## 7. Điều đã không làm và lý do
- Không có bất kỳ cơ chế đọc fallback nào sang `cau_hoi_thu_v2.csv` theo lệnh của người dùng.
- Không đọc, sửa hay in file khảo sát gốc `khao_sat_goc.csv`.
- Không gọi LLM sinh câu trả lời trong phiên này.

## 8. Việc tiếp theo
- Người dùng mở file `cham_tay_<timestamp>.csv` bằng Excel để kiểm tra và điền cột `cham_tay`.
- Bổ sung thêm các câu hỏi vào `cau_hoi_thu.csv` cho các tài liệu quy chế tiếp theo.

## 9. Câu hỏi cho người dùng
- Bạn đã mở thử file `cham_tay_20261014_163916.csv` trong Excel chưa, tiếng Việt hiển thị đã chuẩn chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao file CSV mở bằng Excel trên Windows hay bị lỗi font tiếng Việt nếu không có BOM, trong khi mở bằng VS Code lại đọc bình thường?
2. Vì sao ở chế độ `--retrieval-only`, việc ghi nhận tỷ lệ từ chối là `0%` lại bị coi là sai lệch về mặt phương pháp luận nghiên cứu?
3. Nếu muốn chạy benchmark với một file câu hỏi kiểm thử khác nằm ở thư mục bất kỳ, ta sẽ dùng câu lệnh thế nào?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì VS Code mặc định tự động nhận diện UTF-8, còn Excel trên Windows theo mặc định mở CSV bằng bảng mã hệ thống (ANSI/Windows-1252) trừ khi file có 3 byte BOM (`\xEF\xBB\xBF`) báo hiệu rõ ràng là UTF-8.
2. Vì từ chối là quyết định của bước suy luận LLM (dựa vào prompt và context). Ở chế độ chỉ truy xuất, LLM chưa hề chạy nên bot chưa bao giờ đưa ra quyết định từ chối. Ghi 0% làm người đọc tưởng rằng bot đã cố trả lời nhưng từ chối sai.
3. Dùng tham số `--csv <đường_dẫn>`, ví dụ: `venv\Scripts\python.exe -X utf8 -m scripts.chay_cau_hoi_thu --csv đường\dẫn\file.csv --mode hybrid --retrieval-only`.

</details>
