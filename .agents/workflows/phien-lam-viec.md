---
description: Chạy một phiên làm việc theo quy trình A đến F của dự án (gõ /phien-lam-viec rồi ghi bước cần làm)
---
# Phiên làm việc theo quy trình

Phạm vi phiên này là phần tôi ghi ngay sau lệnh (ví dụ "Bước 3 và 4 của docs/ai-service.md").
Nếu tôi chưa ghi phạm vi, hãy hỏi lại trước khi làm bất cứ việc gì.

## Chuẩn bị
1. Đọc GEMINI.md, docs/progress.md, docs/decisions.md và docs/agent-workflow.md.
2. Đọc docs/plan.md và docs/cau-truc-du-an.md nếu chưa đọc trong phiên này.
3. Với docs/ai-service.md, chỉ đọc các phần có tiêu đề: "Đọc trước khi bắt đầu", "Các quyết định cần
   thống nhất trước khi code", phần của bước được giao (tiêu đề bắt đầu bằng "Bước N."), "Lỗi thường gặp",
   "Danh sách kiểm tra hoàn thành". Tìm theo tiêu đề, không theo số thứ tự mục.

## Quy trình
A. **Hiểu.** Viết 5 đến 10 dòng: nhiệm vụ là gì, giả định, câu hỏi còn mở. Thiếu thông tin quan trọng thì hỏi trước.

B. **Kế hoạch.** Tạo Implementation Plan gồm: file sẽ tạo hoặc sửa, test sẽ thêm, lệnh kiểm tra, rủi ro,
   thư viện mới (nếu có, kèm tên, phiên bản, lý do), và bảng quyết định thiết kế với các cột: Quyết định,
   Phương án đã cân nhắc, Vì sao chọn, Loại căn cứ ([tài liệu: file, tiêu đề] / [kỹ thuật] / [giả định của agent]).
   Ghi lý do ngay lúc quyết định, không viết bù sau.
   **Dừng ở bước duyệt kế hoạch (Artifact Review) và chờ tôi duyệt.** Nếu đang ở chế độ Fast, hãy viết kế hoạch
   trong khung chat và chờ tôi trả lời "duyệt".

C. **Làm.** Từng bước nhỏ. Viết hoặc cập nhật test cùng lúc với mã, chạy lại sau mỗi bước nhỏ.

D. **Kiểm tra.** Chạy đúng các lệnh ghi trong bước tương ứng của ai-service.md. Dán kết quả thật. Phân biệt
   "đã chạy và thấy kết quả" với "chưa chạy được vì lý do X".

E. **Ghi chép.** Tạo docs/journal/YYYY-MM-DD-ten-buoc.md theo docs/journal/_mau.md. Cập nhật docs/progress.md
   và docs/decisions.md. File nhật ký phải nằm trong repo, artifact của Antigravity không thay thế nó.

F. **Báo cáo cuối** trong khung chat, đúng năm đề mục: 1) Kết quả, 2) Kiểm tra (lệnh và kết quả thật),
   3) Điểm chưa chắc (tối đa 5 gạch), 4) Cần tôi quyết (tối đa 3 gạch), 5) File đã đổi và gợi ý nội dung commit.
   Phần văn xuôi tối đa 15 dòng. Kết quả lệnh và danh sách file không tính vào 15 dòng.

## Khi không có người trả lời
Không sửa mã. Lưu kế hoạch vào docs/plans/YYYY-MM-DD-ten-buoc.md, đặt trạng thái "CHỜ DUYỆT" trong
docs/progress.md, rồi kết thúc phiên.
