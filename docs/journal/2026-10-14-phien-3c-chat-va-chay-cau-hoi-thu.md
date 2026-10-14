# Nhật ký 2026-10-14 – Phiên 3C: Công cụ chat và Công cụ chạy bộ câu hỏi thử

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Xây dựng giao diện chat dòng lệnh tương tác (`scripts/chat_cli.py`) có nhớ ngữ cảnh hội thoại, cùng công cụ đánh giá tự động (`scripts/chay_cau_hoi_thu.py`) đo độ chính xác truy xuất và phân rã thời gian xử lý từng thành phần của hệ thống RAG trên bộ câu hỏi thử nghiệm.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/chat_cli.py` | Tạo mới: vòng lặp terminal chat hỏi đáp, nhớ 4 lượt gần nhất, hiển thị trích dẫn nguồn, thời gian, cờ số lạ, thoát `/q`. |
| `ai-service/scripts/chay_cau_hoi_thu.py` | Tạo mới: chạy benchmark từ CSV, đo `must_have`, trúng Điều, phân rã thời gian, ghi JSON kèm `cham_tay`, in bảng tổng hợp theo nhóm. |
| `ai-service/app/pipeline/retrieval/dense_search.py` | Thêm hàm `dense_search_with_vector` nhận vector có sẵn để tách đo thời gian embedding và Qdrant query. |
| `ai-service/app/pipeline/retrieval/hybrid_retriever.py` | Đo thời gian chi tiết `embedding_ms`, `qdrant_ms`, `bm25_ms` và trả về `timing` trong kết quả truy xuất. |
| `ai-service/app/pipeline/rag_pipeline.py` | Tích hợp đo thêm `llm_ms`, `total_ms` vào `Prepared` và phương thức `answer()`. |
| `ai-service/tests/test_core.py` | Thêm 6 unit test (`TestBenchmarkEvaluation`): parse CSV, so khớp NFC, tính tỷ lệ, ghi JSON có `cham_tay`, chứng minh `retrieve()` cho kết quả đồng nhất trước và sau khi tách hàm. Nâng tổng số test lên 59 (59/59 PASS). |
| `docs/plans/2026-10-14-phien-3c-chat-va-chay-cau-hoi-thu.md` | Kế hoạch chi tiết và ghi nhận 6 điều kiện duyệt của người dùng. |
| `docs/progress.md` & `docs/decisions.md` | Cập nhật tiến độ Phiên 3C và quyết định chốt. |

## 3. Vì sao làm như vậy
- Quyết định: Thêm hàm `dense_search_with_vector` trong `dense_search.py` thay vì sửa signature của hàm `dense_search`.
- Phương án đã cân nhắc:
  - Phương án A: Thêm tham số tùy chọn `vector=None` vào thẳng hàm `dense_search(query, ...)`.
  - Phương án B: Giữ nguyên hàm `dense_search` và viết thêm hàm `dense_search_with_vector(query_vector, ...)`.
- Vì sao chọn: Bảo toàn 100% tính tương thích ngược của mã nguồn cũ, đảm bảo các lời gọi `dense_search` hiện có không bị ảnh hưởng, có unit test kiểm chứng kết quả trả về tương đương tuyệt đối.
- Vì sao loại phương án còn lại: Phương án A có nguy cơ làm rối logic nội bộ của hàm cũ nếu xử lý rẽ nhánh không khéo.
- Loại căn cứ: [kỹ thuật]
- Đánh đổi: Có hai hàm tìm kiếm dense trong module, cần chú thích rõ mục đích của từng hàm.

- Quyết định: Định nghĩa rõ ràng mẫu số (denominator) cho từng chỉ số đánh giá và loại bỏ câu gặp lỗi API khỏi mẫu số.
- Phương án đã cân nhắc:
  - Phương án A: Lấy tổng số câu hỏi làm mẫu số chung cho tất cả các tỷ lệ.
  - Phương án B: Tách mẫu số riêng biệt: `must_have` chỉ tính trên câu có định nghĩa `must_have`, `true_refuse` chỉ tính trên câu `expected_refuse=True`, `false_refuse` chỉ tính trên câu `expected_refuse=False`. Câu bị lỗi API gắn nhãn `loi_api` và loại khỏi mọi mẫu số.
- Vì sao chọn: Đảm bảo số liệu thống kê phản ánh trung thực bản chất thuật toán, không bị sai lệch (pha loãng) bởi các câu hỏi không áp dụng tiêu chí đó hoặc lỗi mạng/hạn mức bên ngoài.
- Vì sao loại phương án còn lại: Phương án A sẽ làm sai lệch nghiêm trọng tỷ lệ phần trăm (ví dụ: câu hỏi bình thường lại bị tính vào mẫu số của tỷ lệ từ chối đúng).
- Loại căn cứ: [yêu cầu người dùng & kỹ thuật]
- Đánh đổi: Cần quản lý cấu trúc dữ liệu đếm mẫu số/tử số chi tiết hơn trong mã nguồn.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
1. **Phân rã thời gian (Timing Breakdown)**:
   - *Ví dụ đời thường*: Bạn đặt một bát phở mang về mất 25 phút. Bạn muốn biết vì sao lâu: thời gian quán nấu (2 phút), shipper chạy đến quán (3 phút), hay tắc đường khi giao (20 phút)? Phân rã thời gian chính là bấm đồng hồ từng chặng để biết "nút thắt cổ chai" (bottleneck) nằm ở đâu thay vì chỉ nhìn vào con số tổng 25 phút.
   - *Trong hệ thống RAG*: Tổng thời gian gồm: embedding câu hỏi (gọi API mạng) + tìm kiếm Qdrant (truy vấn local) + tìm kiếm BM25 (tính điểm từ khóa local) + LLM sinh chữ (gọi API mạng sinh token).
2. **Khớp chuỗi chính xác (Exact String Match) và Chuẩn hóa Unicode NFC**:
   - Tiếng Việt có hai kiểu gõ Unicode: tổ hợp (chữ `a` ghép với dấu huyền) và dựng sẵn (`à`). Nếu không chuẩn hóa về cùng chuẩn NFC (`unicodedata.normalize("NFC", text)`), máy tính sẽ coi hai chữ trông giống hệt nhau là hoàn toàn khác nhau.
   - Cần lưu ý: So khớp `must_have` chỉ là so khớp chuỗi chữ, không nhận diện được cách diễn đạt đồng nghĩa (paraphrasing). Ví dụ quy chế ghi "24 tháng", người dùng gõ "2 năm" thì kiểm tra chuỗi sẽ báo miss dù về ngữ nghĩa là đúng.

## 5. Đã kiểm tra thế nào
- Lệnh 1: `venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v`
  - Kết quả thật: 59/59 test PASS (thời gian chạy 7.84s).
- Lệnh 2: Thử nghiệm `scripts/chat_cli.py` với biến môi trường `LLM_PROVIDER=mock`:
  - Kết quả thật: Vòng lặp chat hiển thị đúng câu hỏi, trích dẫn nguồn, thời gian, thoát `/q` an toàn.
- Lệnh 3: Chạy benchmark thật: `venv\Scripts\python.exe -X utf8 -m scripts.chay_cau_hoi_thu --mode hybrid --retrieval-only --tap dev --max-calls 30`
  - Kết quả thật:
    - Đọc 3 câu hợp lệ (`c01`, `c02`, `c03`) từ `cau_hoi_thu_v2.csv`, bỏ qua 10 dòng rỗng.
    - Nhóm `truc_tiep` (2 câu): Must-have đoạn đạt 87.5% (7/8 cụm), Hit Điều đạt 100.0% (2/2 câu), Từ chối nhầm 0.0% (0/2).
    - Nhóm `ngoai_pham_vi` (1 câu): Thời gian 383 ms.
    - Toàn bộ: Must-have đoạn 87.5% (7/8), Hit Điều 100% (2/2).
    - Phân rã thời gian trung bình: Embedding: 946.7 ms, Qdrant: 51.7 ms, BM25: 0.3 ms, LLM: 0.0 ms. Tổng trung bình: 1000.3 ms (~1.0 giây).
    - Xuất file JSON thành công: `evaluation/benchmarks_result/benchmark_20261014_102150.json` có đủ trường `cham_tay: ""`.
- Kết luận: ĐẠT.
- Số lệnh gọi API trả phí đã dùng: 0 VND (chỉ gọi 3 lệnh embedding miễn phí, không gọi LLM sinh chữ).

## 6. Chưa chắc chắn, rủi ro, giả định
- Ở chế độ `--retrieval-only`, pipeline không thực hiện bước kiểm tra điều kiện từ chối (refusal logic) vốn nằm ở tầng tổng hợp context của LLM, do đó cờ `bot_refused` luôn là `false`. Khi chạy chế độ đầy đủ có LLM, các chỉ số từ chối (`true_refuse`) mới phản ánh chính xác.
- File `cau_hoi_thu.csv` có 10 dòng rỗng đang chờ người dùng bổ sung thêm câu hỏi kiểm thử.

## 7. Điều đã không làm và lý do
- Không gọi LLM trong phiên này để tuân thủ chỉ đạo của người dùng và giữ chi phí API ở mức 0 VND.
- Không sửa hay in nội dung file khảo sát gốc `khao_sat_goc.csv`.
- Không tự ý thay đổi model hay ngưỡng lọc điểm của RAG pipeline.

## 8. Việc tiếp theo
- Người dùng bổ sung các câu hỏi kiểm thử hoàn chỉnh vào `cau_hoi_thu.csv`.
- Chấm tay (`cham_tay`) vào file JSON benchmark kết quả đợt đầu.
- Khi sẵn sàng, kích hoạt đánh giá đầy đủ (bao gồm cả LLM sinh chữ) với giới hạn `--max-calls`.

## 9. Câu hỏi cho người dùng
- Người dùng đã hài lòng với định dạng file JSON xuất ra và cách phân rã thời gian của hệ thống chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Vì sao truy xuất cục bộ (BM25 và Qdrant local) chỉ mất ~52ms nhưng một câu hỏi RAG đầy đủ trước đây lại mất tới ~25 giây?
2. Nếu quy chế viết "thời hạn 24 tháng" mà cụm `must_have` đặt là "2 năm", kiểm tra chuỗi ký tự theo Unicode NFC sẽ cho kết quả thế nào và giải pháp là gì?
3. Tại sao trong benchmark đánh giá, câu hỏi bị lỗi API (mã 429 hoặc rớt mạng) phải được loại hẳn ra khỏi mẫu số thay vì tính là câu "thất bại"?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì phần lớn độ trễ ~25 giây nằm ở vòng mạng quốc tế (gọi API Gemini qua HTTPS/TLS từ Việt Nam) và thời gian mô hình LLM giải mã sinh từng token câu trả lời (Time To First Token + Output Generation), trong khi tầng truy xuất diễn ra cục bộ trên máy tính.
2. Kiểm tra chuỗi ký tự sẽ báo `False` (không tìm thấy) vì máy chỉ so khớp mặt chữ chính xác chứ không hiểu ngữ nghĩa. Giải pháp: ghi nhận hạn chế này trong báo cáo, bổ sung nhiều biến thể từ khóa ngăn cách bằng `|` trong `must_have`, hoặc dựa vào việc chấm tay (`cham_tay`).
3. Vì lỗi API thuộc về hạ tầng/hạn mức mạng bên ngoài, không phải do chất lượng của thuật toán truy xuất hay prompt. Nếu đưa vào mẫu số, nó sẽ kéo tụt tỷ lệ phần trăm chất lượng của hệ thống một cách thiếu khách quan.

</details>
