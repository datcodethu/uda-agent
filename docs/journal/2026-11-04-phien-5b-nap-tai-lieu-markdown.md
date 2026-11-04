# Nhật ký 2026-11-04 – Phiên 5B: Nạp 5 tài liệu Markdown và hoàn tất cào 15 URL

## 1. Mục tiêu
Hoàn tất thu thập dữ liệu từ 15 trang web của trường bằng Crawl4AI và nạp 5 tài liệu tổng hợp quy định sinh viên dạng Markdown (`crawl_staging_MD`) vào kho tri thức RAG của hệ thống, giúp chatbot giải quyết các vấn đề thực tiễn: đăng ký học lại/thi lại, đăng ký học phần năm nhất, xử lý mất thẻ xe, mượn sách thư viện và trang phục thi.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/crawler/seeds.txt` | Loại bỏ URL ngoài allowlist (`luatminhkhue.vn`) và làm sạch ký tự gạch đầu dòng Markdown `* `. |
| `ai-service/crawler/thu_thap.py` | Cập nhật hàm `load_lines` tự động strip markdown bullets (`*`, `-`, `+`, `1.`) để tăng tính chịu lỗi. |
| `ai-service/data/raw_documents/*.md` | Sao chép 5 file Markdown tổng hợp từ `crawl_staging_MD` sang `raw_documents/`. |
| `ai-service/app/pipeline/preprocessor/pdf_loader.py` | Bổ sung nhánh đọc file `.md` (đọc văn bản UTF-8 tương tự `.txt`). |
| `ai-service/app/pipeline/preprocessor/structural_chunker.py` | Cập nhật `extract_doc_title` tự động nhận diện tiêu đề cấp 1 (`# `) của Markdown làm ngữ cảnh chunk. |
| `ai-service/data/docs_registry.csv` | Đăng ký 5 văn bản mới với đầy đủ trạng thái kiểm duyệt (`da_duyet=true`, `quy_che_truong`, `ACTIVE`, `public`). |
| `ai-service/data/chunks.jsonl` & Qdrant | Nạp thành công 10 chunks mới từ 5 văn bản Markdown, nâng quy mô kho lên 10 tài liệu (103 chunks), 0 trùng lặp `chunk_id`. Tự động xây dựng lại chỉ mục BM25. |

## 3. Vì sao làm như vậy
- Quyết định: Cập nhật `pdf_loader.py` hỗ trợ `.md` và `structural_chunker.py` nhận diện tiêu đề `# ` Markdown thay vì viết parser riêng biệt.
  - Phương án đã cân nhắc: Viết một pipeline nạp Markdown hoàn toàn tách biệt.
  - Vì sao chọn: Tái sử dụng trọn vẹn hạ tầng xử lý văn bản, quy tắc cắt đoạn gối đầu và bảo vệ bảng biểu của hệ thống RAG hiện có; giữ vững tính thống nhất và không làm phức tạp hóa kiến trúc.
  - Loại căn cứ: [kỹ thuật]
  - Đánh đổi: File Markdown không có cấu trúc "Điều" sẽ được chia thành các đoạn `d0-1`, `d0-2`; nhưng do độ dài mỗi file chỉ ~1.500 ký tự nên ngữ cảnh được bảo toàn nguyên vẹn.

- Quyết định: Sao chép 5 file vào `raw_documents/` và đăng ký trong `docs_registry.csv` trước khi nạp qua `ingest_approved.py`.
  - Phương án đã cân nhắc: Nạp trực tiếp từ `crawl_staging_MD`.
  - Vì sao chọn: Tuân thủ nghiêm ngặt nguyên tắc Single Source of Truth và cổng kiểm duyệt Default-Deny đã chốt ở Phiên 3A.

## 4. Khái niệm mới
- **Markdown Context Extraction (Trích xuất ngữ cảnh Markdown):** Trong tài liệu phi quy phạm pháp luật (không có số Điều/Khoản), việc bóc tách dòng tiêu đề cấp 1 (`# `) đóng vai trò then chốt để tạo tiền tố ngữ cảnh (Header) cho mỗi đoạn chunk: `[Tên tài liệu | Nội dung]`, giúp bộ tìm kiếm Dense (Vector) và BM25 định vị chính xác chủ đề khi người dùng hỏi.

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Cào dữ liệu web thật từ 15 seed URLs):
  `cmd /c "set PYTHONUTF8=1&& ai-service\crawler\venv\Scripts\python.exe ai-service\crawler\thu_thap.py --apply --max-pages 30 --max-depth 1"`
  - Kết quả: Cào thành công 30 trang mới, phát hiện 38 link đính kèm, 2 trang nhận diện `co_cau_truc_dieu`.
- Lệnh 2 (Kiểm duyệt kho quy chế):
  `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONPATH=.&& venv\Scripts\python.exe -m scripts.ingest_approved --status"`
  - Kết quả: Tổng số 10 tài liệu, 103 đoạn (chunks), 0 mã trùng lặp `chunk_id`.
- Lệnh 3 (Kiểm thử đơn vị hồi quy):
  `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả: `Ran 94 tests in 4.068s -> OK (skipped=1)`.
- Lệnh 4 (Hỏi thử nghiệm thực tế 3 câu hỏi):
  - Câu hỏi về ĐK học phần năm nhất HK1: Trả lời chính xác trường xếp sẵn, trích dẫn `[Bao_cao_nghien_cuu_Dang_ky_hoc_phan_nam_nhat]` (score: 0.7574).
  - Câu hỏi về mất thẻ xe: Trả lời 4 bước chi tiết (báo bảo vệ, đối soát giấy tờ, check camera, lập biên bản), trích dẫn `[Bao_cao_nghien_cuu_Mat_the_xe_sinh_vien]` (score: 0.7992).
  - Câu hỏi về trang phục thi: Trả lời đủ áo sơ mi logo trường, váy qua gối, dép quai hậu/giày, trích dẫn kết hợp tài liệu mới và Điều 3 Nội quy học đường (score: 0.7689).

## 6. Chưa chắc chắn, rủi ro, giả định
- 5 file Markdown là các tài liệu tổng hợp nội bộ do người dùng biên soạn. Cần tiếp tục đối chiếu với các quyết định ban hành văn bản chính thức của trường khi có thông báo mới.

## 7. Điều đã không làm và lý do
- Không tự ý commit Git (tuân thủ quy định để người dùng tự kiểm tra và commit).

## 8. Việc tiếp theo
- Người dùng kiểm tra các câu trả lời trên giao diện Web Chat Demo tại `http://localhost:8000/`.
- Rà soát các tài liệu đính kèm phát hiện trong `ai-service/data/crawl_staging/links_dinh_kem.csv`.

## 9. Câu hỏi cho người dùng
- Bạn có muốn kiểm tra thêm chủ đề nào trong 5 tài liệu mới nạp trên giao diện Web Chat không?
