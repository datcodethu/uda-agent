# Nhật ký 2026-11-03 – Phiên 5A: Công cụ thu thập dữ liệu ngoại tuyến Crawl4AI

## 1. Mục tiêu
Xây dựng công cụ cào dữ liệu web trường Đại học Đông Á hoạt động ngoại tuyến, tách biệt độc lập bằng môi trường ảo riêng, tuân thủ nghiêm ngặt danh sách tên miền được phép (allowlist), trần cứng an toàn, định dạng bảng kê manifest/links đính kèm và kiểm tra robots.txt trước khi thu thập.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/crawler/requirements-crawler.txt` | Tạo mới khai báo thư viện `crawl4ai` (cài đặt thành công bản 0.9.5). |
| `ai-service/crawler/README.md` | Tạo tài liệu hướng dẫn cơ chế hoạt động, các trần cứng an toàn và cú pháp chạy lệnh (`--dry-run`, `--apply`). |
| `ai-service/crawler/thu_thap.py` | Tạo mã nguồn công cụ thu thập với chế độ BFS, lọc allowlist chặt chẽ, kiểm tra robots.txt, chuẩn hóa Unicode NFC, khử trùng theo SHA-256, nhận diện link tài liệu đính kèm và xuất manifest có BOM. |
| `ai-service/tests/test_crawler.py` | Tạo bộ kiểm thử gồm 11 unit tests offline và 1 integration test với máy chủ mock nội bộ (`--test-local`). |

## 3. Vì sao làm như vậy
- Quyết định: Tạo môi trường ảo riêng tại `ai-service\crawler\venv` và file `requirements-crawler.txt` riêng biệt, không cài vào `ai-service\venv`.
  - Phương án đã cân nhắc: Cài chung crawl4ai vào `ai-service\requirements.txt`.
  - Vì sao chọn: Crawl4AI kéo theo các gói đồ sộ như Playwright, Chromium binary, Scipy, Tokenizers,... có thể gây xung đột dependency (Pydantic, httpx, Anyio) với hệ thống RAG phục vụ chatbot chính.
  - Vì sao loại phương án còn lại: Nguy cơ làm hỏng môi trường đang chạy ổn định của AI service.
  - Loại căn cứ: [kỹ thuật] và chỉ đạo rõ ràng từ người dùng trong yêu cầu phiên 5A.
  - Đánh đổi: Tốn thêm khoảng 500MB dung lượng đĩa cho venv độc lập của crawler.

- Quyết định: Mặc định bật chế độ `--dry-run` (chỉ kiểm tra robots.txt, hợp lệ domain và ước tính thời gian; không tải trang, không ghi đĩa). Chỉ cào thật khi có cờ `--apply`.
  - Phương án đã cân nhắc: Cho phép cào tự động ngay khi chạy lệnh.
  - Vì sao chọn: Đảm bảo người dùng luôn có cơ hội rà soát danh sách URL dự kiến và tỷ lệ URL bị chặn trước khi tải dữ liệu thực tế.
  - Vì sao loại phương án còn lại: Nguy cơ cào nhầm hoặc vi phạm quy định web nếu file cấu hình có sai sót.
  - Loại căn cứ: [kỹ thuật] bảo vệ an toàn mạng trường.

- Quyết định: Phân loại sơ bộ `loai_nghi_ngo` bằng đếm dòng bắt đầu bằng "Điều" (>= 3 dòng ghi `co_cau_truc_dieu`, ngược lại `khac`) và chỉ ghi link tệp đính kèm (`.pdf`, `.docx`,...) vào `links_dinh_kem.csv` mà không tải tệp.
  - Phương án đã cân nhắc: Tự động tải luôn các tệp PDF/Docx hoặc dùng LLM để phân loại nội dung.
  - Vì sao chọn: Tuân thủ tuyệt đối quy tắc "không gọi API trả phí", "không dùng tính năng trích xuất bằng LLM của Crawl4AI", giữ quyền phê duyệt cho người dùng.
  - Vì sao loại phương án còn lại: Tải tệp tự động làm nặng kho lưu trữ và nguy cơ dính mã độc từ tệp lạ.
  - Loại căn cứ: [tài liệu: yêu cầu phiên 5A]

## 4. Khái niệm mới
- **Subdomain Boundary Attack (Tấn công ranh giới tên miền phụ):** Kẻ xấu có thể đăng ký tên miền như `donga.edu.vn.attacker.com` để lừa các đoạn code kiểm tra kiểu `if "donga.edu.vn" in url:`. Để phòng ngừa, crawler phải bóc tách hostname chính xác và kiểm tra hoặc `host == "donga.edu.vn"` hoặc `host.endswith(".donga.edu.vn")`.
- **Dry-run (Chạy thử không ghi vết):** Một chế độ chạy kiểm thử toàn bộ logic và quy tắc (như kiểm tra robots.txt, duyệt cây link, tính dung lượng ước tính) nhưng hoàn toàn không gửi tải thực sự đến máy chủ đích và không tạo file trên đĩa cứng, giúp phát hiện lỗi cấu hình từ sớm.

## 5. Đã kiểm tra thế nào
- Lệnh 1 (Test offline + Integration cục bộ trên venv crawler):
  `cmd /c "set PYTHONUTF8=1&& ai-service\crawler\venv\Scripts\python.exe -m unittest ai-service\tests\test_crawler.py -v"`
- Kết quả thật:
  `Ran 12 tests in 9.374s -> OK` (100% 12 test pass, gồm kiểm thử allowlist, scheme, hard ceilings, hash dedup, prompt injection safe, và cào thật 3 trang local mock server).
- Lệnh 2 (Test toàn bộ hệ thống gốc trong venv ai-service):
  `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
- Kết quả thật:
  `Ran 94 tests in 6.711s -> OK (skipped=1)` (Tất cả test core cũ chạy mượt mà, integration test crawl4ai tự động skip khi ở ngoài venv crawler).
- Số lệnh gọi API trả phí đã dùng: 0 (Đúng cam kết không gọi API trả phí).

## 6. Chưa chắc chắn, rủi ro, giả định
- Do người dùng chưa tạo file `ai-service/crawler/allowlist.txt` và `ai-service/crawler/seeds.txt`, lệnh dry-run trên seeds thật sẽ chạy ngay khi người dùng đưa 2 file này vào thư mục `ai-service/crawler/`.

## 7. Điều đã không làm và lý do
- Không tải trực tiếp các tệp `.pdf`, `.docx` về đĩa mà chỉ liệt kê địa chỉ vào `links_dinh_kem.csv` để người dùng thẩm định thủ công.
- Không tích hợp crawler vào luồng chatbot của `app/` (crawler là công cụ độc lập ngoại tuyến).
- Không tự ý commit git (tuân thủ quy tắc người dùng tự commit).

## 8. Việc tiếp theo
- Người dùng tạo `ai-service/crawler/allowlist.txt` và `ai-service/crawler/seeds.txt`.
- Người dùng chạy lệnh dry-run để kiểm tra danh sách URL dự kiến:
  `ai-service\crawler\venv\Scripts\python.exe ai-service\crawler\thu_thap.py --dry-run`
- Sau khi kiểm tra đạt, người dùng chạy `--apply` để cào các trang trường vào thư mục tạm `ai-service/data/crawl_staging/`.

## 9. Câu hỏi cho người dùng
- Hiện tại danh sách hạt giống (`seeds.txt`) của bạn dự kiến gồm các trang nào (Cổng thông tin đào tạo, trang sinh viên hay trang chủ)? Bạn đã sẵn sàng đưa vào chưa?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao crawler phải so khớp `host.endswith(".donga.edu.vn")` thay vì chỉ dùng `if "donga.edu.vn" in url`?
2. Chế độ `--dry-run` khác gì so với `--apply`?
3. Tại sao Crawl4AI và Playwright phải được cài đặt trong một môi trường ảo riêng biệt (`ai-service\crawler\venv`)?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Để chặn tên miền giả dạng (spoofing). Nếu chỉ kiểm tra `"donga.edu.vn" in url`, kẻ xấu dùng tên miền `donga.edu.vn.scam.com` vẫn sẽ lọt qua lưới lọc.
2. `--dry-run` chỉ đọc robots.txt và kiểm tra URL theo danh sách, in thống kê dự kiến và không tải trang hay ghi bất kỳ file nào xuống ổ đĩa. `--apply` mới thực sự khởi động trình duyệt và lưu văn bản markdown sạch vào staging.
3. Để cô lập các thư viện nặng (Playwright, Scipy, Tokenizers) và tránh xung đột phiên bản (như Pydantic, httpx) với môi trường dịch vụ AI chính đang chạy ổn định.

</details>
