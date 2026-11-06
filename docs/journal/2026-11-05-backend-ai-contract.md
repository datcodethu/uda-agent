# Nhật ký 2026-11-05 — Quy ước Backend và AI Service

## Mục tiêu

Viết tài liệu để dev Spring Boot triển khai client đúng với FastAPI đang có và biết
những năng lực còn thiếu, tránh hiểu bản thiết kế tổng thể là API đã triển khai.

## Đã làm và lý do

- Tạo `docs/backend-ai-contract.md` bản 0.1: trách nhiệm, xác thực, schema, SSE,
  session, trạng thái message, lỗi/retry, đồng bộ tài liệu và checklist nghiệm thu.
- Thêm liên kết từ `README.md` để dev tìm thấy tài liệu khi clone dự án.
- Chọn ghi rõ ba nhóm hiện có / quy ước Backend / cần bổ sung thay vì sửa schema
  ngay. Phạm vi người dùng giao là viết bộ quy tắc, chưa yêu cầu triển khai backend.
- Đọc routes, schemas, pipeline, verifier, session, loader, security, health và
  tài liệu thiết kế. Ghi giới hạn JSON/SSE khác nhau, telemetry stream chưa đầy đủ,
  cache nguồn chưa nhận biết phiên bản và ingest chưa nguyên tử.
- Đối chiếu working tree trên commit nền `231d58c`; không đưa các công cụ URL import
  và rebuild đang làm dở vào danh sách endpoint đã bàn giao.

## Kiểm tra

- Đọc ví dụ request từ Markdown, validate bằng `QueryRequest`: 1 ví dụ hợp lệ.
- Parse JSON của 3 payload SSE minh họa: hợp lệ.
- Kiểm tra 14 liên kết tài liệu/mã nguồn trong contract: đều tồn tại.
- Validate ví dụ ingest bằng `IngestResponse`: hợp lệ.
- `git diff --check -- README.md docs/backend-ai-contract.md`: không có lỗi
  whitespace; có cảnh báo chuẩn hóa LF/CRLF ở README.
- Không gọi API, không chạy benchmark/unit test vì chỉ thay đổi tài liệu; kiểm tra
  schema ở trên không khởi tạo model hay truy vấn kho vector.

## Giới hạn và bước tiếp theo

Bản 0.1 cần hai người phụ trách Backend/AI review trước khi coi là hợp đồng phát hành.
Timeout khởi điểm, hạn mức, lưu trữ chat và phiên bản tài liệu là đề xuất cần chốt,
không phải cấu hình đã triển khai hay SLA đã kiểm chứng. Chưa thay đổi mã/API, chưa
commit/push tài liệu phiên này; giữ nguyên các thay đổi khác trong working tree.

## Ba câu tự kiểm tra

1. Vì sao HTTP 200 chưa đủ kết luận stream thành công?
2. Vì sao `history=[]` không có nghĩa bắt đầu lại hội thoại?
3. Vì sao không đặt READY ngay sau khi Backend lưu file upload?

<details>
<summary>Gợi ý đáp án</summary>

1. Stream có thể phát error hoặc đứt trước done.
2. AI dùng history RAM nếu request không có history không rỗng.
3. File chưa chắc được duyệt hoặc lập chỉ mục thành công; ba kho chỉ mục còn có
   thể lệch nếu ingest lỗi giữa chừng.

</details>
