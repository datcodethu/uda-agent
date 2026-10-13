# Các quyết định đã chốt

| Ngày | Quyết định | Căn cứ | Ai chốt |
|---|---|---|---|
| 2026-10-10 | Môi trường hệ thống: Windows 11 (Build 10.0.26300.9550), Agent Shell: PowerShell 5.1 (5.1.26100.9549), Python venv: 3.12.4 | Kiểm tra hệ thống phiên 1 (docs/agent-workflow.md) | Agent & Người dùng |
| 2026-10-10 | Tài liệu quy chế thật được lưu trữ tại `ai-service\data\raw_documents\` | Thống nhất cấu trúc dữ liệu quy chế | Người dùng chốt |
| 2026-10-11 | Thống nhất cờ trạng thái `status` thành `ACTIVE` / `EXPIRED` (chữ in hoa) xuyên suốt 6 file nguồn | Khớp CSDL PostgreSQL (`documents.status`), `docs/ai-service.md` mục 4.5 và `plan.md` mục 5.1, 6.1 | Agent & Người dùng |
| 2026-10-11 | Mở rộng `DIEU_RE` hỗ trợ biến thể dấu phân cách (`-`, `–`, `—`) và tiêu đề không dấu chấm, bảo đảm loại trừ câu tham chiếu | `docs/ai-service.md` mục 4.3 | Agent & Người dùng |
| 2026-10-11 | Bỏ qua 15 file PDF scan và 31 file Word (.doc/.docx), không tự ý cài OCR, xuất preview chunks cho 9 PDF đọc được vào `data/chunk_preview/` | Chỉ đạo người dùng phiên Bước 3 & 4 | Người dùng chốt |
| 2026-10-11 | Chuyển đổi .doc sang .docx thực hiện ngoại tuyến 1 lần bằng Word COM (`win32com.client.DispatchEx`) trên Windows; hệ thống chính chạy đa nền tảng (Linux/Docker) qua `python-docx` không phụ thuộc Word | Độc lập nền tảng, sẵn sàng cho server/Docker | Người dùng chốt |
| 2026-10-11 | Cách chia sẻ file `.docx` đã chuyển đổi cho máy khác (commit vào git hay chia sẻ qua Google Drive): Chưa quyết định, chờ chủ dự án | Tránh phình to dung lượng git repo | Đang chờ chủ dự án |
| 2026-10-12 | Phân đoạn văn bản (`quyet_dinh`, `quy_dinh_kem_theo`, `phu_luc`) dựa vào tiêu đề phần hoặc số Điều quay về 1; định danh chunk dạng `{phan}-d{so}-{part}` thay vì hậu tố `-x1` | Tránh va chạm số Điều giữa QĐ và QĐKT; bảo toàn ngữ nghĩa nguồn | Agent & Người dùng duyệt |
| 2026-10-12 | Tiêu đề Điều chuẩn hóa: < 120 ký tự và không kết thúc bằng dấu chấm; nếu không đạt coi là Điều không tiêu đề `(Không)` và giữ nguyên câu trong thân bài | Tránh cắt cụt câu quy định pháp lý làm mất ngữ nghĩa hỏi đáp | Agent & Người dùng duyệt |
| 2026-10-12 | Cắt đoạn tôn trọng cấu trúc: ưu tiên tách theo Khoản/câu hoàn chỉnh, gối đầu 100-150 ký tự, cấm cắt ngang bảng và lặp lại header cột khi bảng phải tách đoạn | Giữ nguyên vẹn cấu trúc dữ liệu bảng và câu hỏi đáp | Agent & Người dùng duyệt |
| 2026-10-12 | Kiểm tra thứ tự Điều (nhảy số, trùng số, lùi số, chấp nhận hậu tố như 5a) ở dạng CẢNH BÁO MỀM, ghi ra `canh_bao_dieu.txt`, không chặn hay loại file | Tránh từ chối nhầm các văn bản có cấu trúc đặc biệt | Người dùng giao việc |
| 2026-10-12 | Cổng nạp kho theo bảng đăng ký `docs_registry.csv` (UTF-8 BOM `utf-8-sig`) theo nguyên tắc Default-Deny: chỉ nạp khi thỏa cả 3 điều kiện (`da_duyet=true`, `loai=quy_che_truong`, `status=ACTIVE`) và có file trên đĩa; mặc định `--dry-run` không ghi DB, chỉ nạp thật khi có `--apply`; vô hiệu hóa script cũ `ingest_folder.py` | Kiểm soát toàn vẹn dữ liệu kho văn bản, tránh nạp nhầm tài liệu hết hạn/ngoài luồng; an toàn chi phí API | Agent & Người dùng duyệt |
| 2026-10-12 | Siết chặt cổng nạp kho 3A theo 6 điều kiện duyệt: (1) Whitelist 6 khóa metadata ghi vào chunk, cấm đè 4 trường cốt lõi; (2) Điều kiện 4 `public_or_internal=public`, chặn `internal` trừ khi có `--allow-internal`; (3) Chỉ cột `loai` làm cổng chặn, bắt buộc đủ 5 cột cốt lõi; (4) Cột `file` chỉ là tên file, cấm thoát thư mục, so sánh Unicode NFC, chặn dòng trùng; (5) Lỗi đọc 1 file không dừng cả lượt; (6) Dry-run chỉ in số liệu không in nội dung, `sys.stdout.reconfigure` chỉ đặt trong `main()`. | Phê duyệt kế hoạch 3A kèm điều kiện của Người dùng | Người dùng chốt |
| 2026-10-12 | Cập nhật cấu hình mô hình chat mặc định sang `gemini-flash-latest` (hoặc `gemini-3.8-flash`) trong `config.py` và `.env.example` do Google AI Studio API v1beta không hỗ trợ `gemini-3-flash` (404) và đã ngừng cung cấp `gemini-2.5-flash` | Kiểm tra kết nối API thực tế tại Phiên 3B | Agent đề xuất & kiểm chứng |
| 2026-10-13 | Phê duyệt và nạp văn bản thứ hai `2024_11_14_14_26_46A.pdf` (QĐ số 2474/QĐ-ĐHĐA-QLĐT về Hướng dẫn phương pháp học tập đại học) vào kho vector; đồng thời điều chỉnh mô hình chat mặc định sang `gemini-3.1-flash-lite` để tối ưu hạn mức gọi API miễn phí hàng ngày (tránh lỗi 429) và rút ngắn thời gian phản hồi (~7s) | Kế hoạch Phiên 4A được Người dùng phê duyệt & kết quả thử nghiệm thực tế | Người dùng duyệt & Agent kiểm chứng |




