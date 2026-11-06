# Nhật ký 2026-11-05 — Thiết lập phối hợp hai agent

## Mục tiêu và thay đổi

Tránh hai agent sửa cùng file, commit lẫn công việc hoặc ghi vào cùng kho dữ liệu.
Thêm `AGENTS.md`, `docs/multi-agent-workflow.md` và phiếu riêng
`.agents/coordination/backend-ai-docs.md`. Thêm liên kết ở `GEMINI.md` và
`docs/agent-workflow.md` để cả Codex và luồng Antigravity/Gemini dễ tìm thấy quy tắc.

## Quyết định

Dùng phân công theo file và phiếu riêng để áp dụng ngay, giữ nguyên working tree
đang dirty. Không tạo worktree/đổi branch/di chuyển file khi công việc khác đang
chạy. Về sau tách worktree cho tác vụ mới để có file/index riêng.
Phiếu không phải khóa OS: cần cả hai agent đọc và đồng ý; chưa có xác nhận bên kia.
Không tự tạo phiếu hoặc tuyên bố trạng thái thay agent khác.

## Kiểm tra và giới hạn

Kiểm tra status ban đầu xác nhận thay đổi AI/import URL/crawler/kho v2 và file ghi
chép chung đang tồn tại. Không sửa các file đó. Chỉ thêm/sửa tài liệu điều phối trong
phạm vi phiếu; không chạy test toàn dự án, API, ingest hoặc rebuild dữ liệu.
Không stage/commit/push ở lượt này. Quy ước cần người dùng chuyển cho agent đang chạy,
vì file mới không tự làm agent đó đọc lại và không cưỡng chế khóa.

## Ba câu tự kiểm tra

1. Vì sao hai agent cùng branch vẫn có thể commit nhầm file của nhau?
2. Vì sao không dùng một phiếu chung để cả hai cùng sửa?
3. Vì sao worktree riêng vẫn cần đường dẫn dữ liệu riêng?

<details>
<summary>Gợi ý đáp án</summary>

1. Cùng working tree dùng chung Git index; commit lấy nội dung đã stage chung.
2. Chính phiếu chung lại trở thành điểm xung đột ghi.
3. Database, cache, port và thư mục ngoài worktree có thể vẫn là tài nguyên chung.

</details>
