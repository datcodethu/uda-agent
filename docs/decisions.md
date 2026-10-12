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

