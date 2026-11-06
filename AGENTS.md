# Quy tắc phối hợp agent trong repository

Đọc [GEMINI.md](GEMINI.md) để hiểu dự án và
[docs/multi-agent-workflow.md](docs/multi-agent-workflow.md) trước khi thao tác.
Chỉ dẫn trực tiếp của người dùng có ưu tiên cao hơn các quy tắc mặc định ở đây.

## Khi có nhiều agent cùng hoạt động

1. Chạy `git status --short`, đọc các phiếu trong `.agents/coordination/` trước khi
   sửa file. Không xem thay đổi chưa commit là của mình. Không tự dọn working tree.
2. Tạo một phiếu riêng cho tác vụ, ghi tên agent, mục tiêu, file được sửa, tài nguyên
   cần ghi, commit nền và trạng thái. Đọc lại các phiếu để kiểm tra trùng phạm vi.
3. Một file chỉ có một agent phụ trách sửa tại một thời điểm, kể cả README, journal,
   progress, decisions, todo, cấu hình và test. Khi trùng phạm vi, tiếp tục việc độc
   lập và bàn giao phần cần sửa; không tự ghi đè thay đổi của agent khác.
4. Phiếu là thỏa thuận phối hợp, không phải khóa hệ điều hành. Agent chưa đọc/ghi
   phiếu được coi là chưa tham gia cơ chế. Không tự suy ra file đã rảnh vì phiếu cũ
   hoặc thời gian chờ đã hết; cần thông báo bàn giao rõ ràng.
5. Không `git add .`, `git add -A`, `git commit -a`, stash, restore/checkout file,
   reset, clean, đổi branch hoặc thao tác làm thay đổi hàng loạt working tree chung.
6. Commit/push chỉ khi người dùng giao rõ. Chỉ một agent thực hiện chuỗi stage →
   kiểm tra staged diff → commit → push → xác nhận remote tại một thời điểm.
   Dùng danh sách đường dẫn cụ thể; nếu index đã có file ngoài phạm vi thì không
   commit hoặc unstage hộ agent khác. Thống nhất lượt thao tác Git trước khi bắt đầu.
7. Đọc/sửa hợp đồng API, schema hoặc cấu hình dùng chung phải phối hợp với bên còn
   lại. Khi nguồn đang thay đổi, ghi rõ tài liệu là dự thảo, commit nền và phần chưa
   được xác nhận; không tuyên bố đã chốt hợp đồng phát hành.
8. Không chạy ingest, rebuild, prune hoặc đánh giá có ghi vào cùng kho Qdrant/JSONL/
   cache/output của tác vụ khác. Muốn test riêng phải chỉ định đầy đủ đường dẫn và
   collection riêng; đổi một biến không đủ tách tất cả tài nguyên. Không chạy suite
   tổng hoặc lệnh có khả năng gọi API khi chưa kiểm tra tác động.
9. Không cài/nâng cấp package trong venv chung khi agent khác đang dùng. Không mở,
   in, commit khóa hoặc `.env`. Không sửa nhãn benchmark có sẵn.
10. Kết thúc bằng phiếu bàn giao: file đã sửa, kiểm tra thực tế, hạn chế, trạng thái
    review, commit/push nếu có. Không tự đánh dấu công việc của agent khác hoàn tất.

Trong lượt thiết lập này, agent `backend-docs` chỉ phụ trách tài liệu Backend–AI và
các file thiết lập phối hợp được liệt kê trong phiếu của mình. Những thay đổi AI,
URL import, crawler và kho v2 hiện có được giữ nguyên cho tác vụ khác.
