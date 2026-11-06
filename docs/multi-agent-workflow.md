# Làm việc với nhiều agent mà không ghi đè công việc

## 1. Phạm vi áp dụng

Repository hiện có ít nhất hai luồng việc: tài liệu Backend–AI và phát triển AI/kho
tri thức. Các agent đang dùng chung thư mục, branch, Git index và môi trường Python.
Hai cửa sổ chat không tạo ra hai working tree độc lập.

Cơ chế dưới đây là quy ước phối hợp; chưa có chương trình cưỡng chế khóa file hoặc
Git. Chỉ có hiệu lực khi cả hai agent đã đọc và tuân thủ. Người dùng chuyển thông
báo cho agent ngoài phiên chat này; agent ở đây không tự gửi tin nhắn qua dịch vụ ngoài.

## 2. Phiếu nhận việc theo từng tác vụ

Mỗi tác vụ dùng một file Markdown riêng trong `.agents/coordination/`. Không dùng
một bảng chung mà cả hai agent cùng ghi. Tên gợi ý: `backend-ai-docs.md`, `ai-kb-v2.md`.
Chỉ agent phụ trách cập nhật phiếu của mình.

Thông tin bắt buộc:

```text
Agent / tác vụ:
Trạng thái: ACTIVE | READY_FOR_REVIEW | HANDED_OFF | DONE
Commit nền:
Mục tiêu:
Danh sách file được sửa (ghi cụ thể):
Tài nguyên cần ghi: Git index, venv, Qdrant, JSONL, cache, port, output...
Phần không nhận sửa:
Kiểm tra đã chạy và tác động:
Yêu cầu phối hợp / phần bàn giao:
Commit / push:
```

Đọc phiếu khác trước khi nhận file. Không tự nhận cả thư mục nếu bên kia đang sửa
file trong đó. Nhận phạm vi mới xong phải đọc lại để phát hiện hai bên vừa nhận cùng
lúc. Khi trùng, hai bên chưa sửa phần trùng cho đến khi thống nhất bên phụ trách.
Quy trình này giảm xung đột nhưng không cung cấp tính nguyên tử như khóa thực.

Nếu agent khác chưa có phiếu, các file đang dirty/untracked không rõ nguồn được
coi là đang do tác vụ khác sử dụng. Có thể đọc để tìm hiểu, không ghi đè/di chuyển/xóa.
Không tạo phiếu ACTIVE thay mặt agent kia hoặc khẳng định nó đã đồng ý.

## 3. Các file chung

- `README.md`: tại thời điểm thiết lập, `backend-docs` đang có thay đổi thêm liên kết
  contract. Agent khác gửi phần cần thêm qua phiếu bàn giao; không cùng sửa README.
- `docs/progress.md`, `docs/decisions.md`, `docs/todo.md`: đang có thay đổi từ luồng
  khác. `backend-docs` không sửa các file này trong lượt hiện tại. Ghi nhật ký riêng.
- `AGENTS.md`, `GEMINI.md`, `docs/agent-workflow.md`: thay đổi quy tắc chung phải
  được ghi rõ và thông báo cho hai bên. Không sửa lại âm thầm trong khi bên kia làm việc.
- `docs/backend-ai-contract.md`: `backend-docs` phụ trách. Agent AI ghi đề xuất thay
  đổi ở phiếu của mình; không sửa contract và implementation cùng lúc mà không bàn giao.
- Schema, route, prompt, indexer, dữ liệu, test: agent phụ trách implementation nhận
  chính xác phạm vi của mình qua phiếu; tài liệu không mặc nhiên cấp quyền sửa mã.

## 4. Quy trình Git ở working tree chung

Không có commit song song an toàn chỉ bằng cách mỗi agent dùng `git add` riêng:
Git index vẫn dùng chung. `.git/index.lock` chỉ bảo vệ từng lệnh, không bảo vệ toàn
bộ khoảng từ stage đến commit. Cần có một người/agent phụ trách lượt Git và xác nhận
bên kia không thao tác index trong khoảng đó.

1. Người dùng giao rõ ai thực hiện commit/push và phần nào được đưa lên.
2. Kiểm tra `git status`, `git diff --cached --name-only` trước stage. Nếu index có
   thay đổi ngoài phần giao thì dừng thao tác Git, bàn giao với người đang stage.
3. Stage bằng đường dẫn cụ thể. Kiểm tra `git diff --cached --name-only`,
   `git diff --cached --check` và nội dung staged trước khi commit.
4. Không đưa file của bên kia vào commit, kể cả file mới chưa được theo dõi.
5. Push branch đã thống nhất, không force push. Nếu remote thay đổi thì kiểm tra
   và báo hướng xử lý; không tự pull/rebase/merge trong working tree chung đang dirty.
6. Ghi hash commit, branch và kết quả xác nhận remote vào phiếu; kết thúc lượt Git.

Quyền push phần Docker ở phiên trước không được mặc nhiên hiểu là quyền đưa mọi
thay đổi đang làm dở lên GitHub. Không sửa `.gitignore` để giấu thay đổi của người khác.

## 5. Dữ liệu, môi trường và kiểm thử

Trước lệnh có ghi dữ liệu, liệt kê các tài nguyên nó sử dụng. Qdrant local, JSONL,
BM25, embedding cache, queue phê duyệt URL và báo cáo benchmark có thể nằm ở các
đường dẫn khác nhau. Kiểm tra mã/cấu hình thay vì chỉ đổi tên collection rồi cho rằng
đã tách kho. Không mở tiến trình khác vào cùng Qdrant local đang bị khóa.

Ưu tiên thư mục tạm/venv hoặc container riêng cho test. Nếu phải dùng venv chung,
không cài package hay thay phiên bản trong lúc bên kia chạy. Port dịch vụ cũng phải
khác nhau khi mở nhiều server. Khi sửa tài liệu chỉ validate ví dụ/link; không cần
chạy lại toàn bộ pipeline, rebuild dữ liệu hoặc suite tổng trên kho đang biến động.

Trước ingest/rebuild/benchmark có API, báo tác động và ngân sách theo quy tắc dự án.
`LLM_PROVIDER=mock` không tự bảo đảm offline. Không dừng process, xóa file `.lock`,
khôi phục snapshot hoặc prune kho của agent khác để làm test của mình chạy được.

## 6. Đồng bộ hợp đồng Backend–AI

Contract 0.1 là dự thảo đối chiếu mã đã đọc. Khi agent AI thay đổi API/schema:

1. Agent AI ghi endpoint/trường/hành vi thay đổi và commit hoặc trạng thái uncommitted
   vào phiếu riêng; nêu có phá tương thích hay không.
2. Agent phụ trách contract đọc lại phần implementation liên quan và cập nhật tài liệu.
3. Hai bên kiểm tra JSON và SSE riêng; không giả định response JSON trùng dict nội bộ.
4. Chỉ ghi “đã chốt” khi bản implementation tương ứng đã được xác nhận để bàn giao.

Không dùng nội dung khảo sát/test chuẩn làm cơ sở tự chỉnh luật hoặc tạo nhãn đáp án.

## 7. Tách working tree cho các tác vụ mới

Nếu tiếp tục phát triển song song thường xuyên, nên dùng **mỗi agent một Git
worktree và branch riêng** để tách file và index. Worktree vẫn có thể chia sẻ một
số tài nguyên ngoài Git; cần venv, dữ liệu, port và output riêng khi chạy.

Không chuyển hoặc di chuyển working tree đang dirty hiện tại để áp dụng ngay.
Trước hết bàn giao các thay đổi theo từng tác vụ, xác định base commit rồi mới tạo
worktree theo phạm vi được người dùng giao. Cơ chế nhận file ở trên áp dụng ngay
trong thời gian hai agent vẫn dùng chung thư mục.

## 8. Thông báo để agent đang chạy đọc lại

Người dùng có thể chuyển nguyên nội dung sau sang cửa sổ agent còn lại:

> Dự án đang có hai agent cùng dùng working tree. Hãy đọc lại AGENTS.md và
> docs/multi-agent-workflow.md. Tạo phiếu riêng trong .agents/coordination/ cho đúng
> phạm vi bạn đang làm. Agent backend-docs phụ trách contract Backend–AI, README và
> các file thiết lập phối hợp đã ghi trong phiếu của nó. Giữ nguyên các file đó;
> không stage/commit/push hoặc ghi kho dữ liệu chung đồng thời khi chưa thống nhất
> lượt thao tác. Ghi đề xuất thay đổi API vào phiếu để bàn giao cập nhật contract.
