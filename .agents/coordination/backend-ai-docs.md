# Phiếu tác vụ backend-docs

- Agent: Codex trong phiên chat chuẩn bị Docker và tài liệu Backend–AI.
- Trạng thái: READY_FOR_REVIEW.
- Commit nền: `231d58c`, branch `demo/school-presentation-2026`.
- Mục tiêu: dự thảo hợp đồng Backend–AI và thiết lập quy ước tránh xung đột.
- File phụ trách:
  - `docs/backend-ai-contract.md`
  - `README.md` (liên kết contract)
  - `docs/journal/2026-11-05-backend-ai-contract.md`
  - `AGENTS.md`
  - `GEMINI.md` (chỉ thêm liên kết quy trình phối hợp)
  - `docs/agent-workflow.md` (chỉ thêm liên kết quy trình phối hợp)
  - `docs/multi-agent-workflow.md`
  - `.agents/coordination/backend-ai-docs.md`
  - `docs/journal/2026-11-05-multi-agent-setup.md`
- Tài nguyên ghi: chỉ các file tài liệu trên; không giữ lượt Git/index, không sử dụng
  port, kho vector, cache hoặc queue để ghi dữ liệu.
- Không nhận sửa: mã AI/prompt/indexer/import URL/crawler, kho v2, nhãn benchmark,
  các file progress/decisions/todo đang dirty từ tác vụ khác.
- Kiểm tra contract đã chạy: 1 request hợp schema, 3 payload SSE JSON hợp lệ và
  14 link mã nguồn tồn tại. Không gọi API trong lượt viết tài liệu/thiết lập phối hợp.
- Bàn giao: agent AI cần tự tạo phiếu đúng phạm vi, báo thay đổi API/schema qua phiếu
  riêng. Chưa có xác nhận agent kia đã đọc hoặc đồng ý quy tắc mới.
- Commit/push: tài liệu contract và thiết lập phối hợp chưa commit/push. Phần Docker
  đã push trước đó ở `231d58c`; không có thao tác Git đang giữ trong lượt này.
- Phạm vi này tiếp tục được dành cho review/bàn giao; agent khác cần trao đổi trước
  khi sửa cùng file. Không suy ra phiếu đã hết hiệu lực theo thời gian.
