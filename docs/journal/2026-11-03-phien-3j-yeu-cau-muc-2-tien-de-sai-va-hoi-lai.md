# Nhật ký 2026-11-03 – Phiên 3J: Triển khai các yêu cầu Mức 2 (L2-11: Tiền đề sai & L2-02/03: Điều kiện & Hỏi lại)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Nâng cấp năng lực xử lý câu hỏi của hệ thống theo chuẩn tài liệu `docs/require.md`: phát hiện và bác bỏ trực diện các câu hỏi gài tiền đề sai (L2-11), đồng thời nêu đủ điều kiện áp dụng và chủ động gợi ý hỏi lại khi sinh viên hỏi chung chung thiếu khóa/ngành (L2-02, L2-03).

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/app/core/prompts.py` | Nâng cấp `SYSTEM_PROMPT` bổ sung 3 quy tắc cốt lõi: Quy tắc 5 (Xử lý điều kiện & hỏi lại L2-02, L2-03), Quy tắc 6 (Xử lý tiền đề sai L2-11), Quy tắc 7 (Trả lời một phần L2-10) |
| `ai-service/tests/test_core.py` | Bổ sung lớp `TestLevel2Requirements` gồm 3 unit tests mới kiểm tra việc tuân thủ các quy tắc Mức 2 |
| `docs/decisions.md` | Ghi nhận quyết định Phiên 3J |
| `docs/progress.md` | Cập nhật tiến độ Phiên 3J |

## 3. Vì sao làm như vậy
- **Quyết định:** Đưa các chỉ dẫn bắt buộc vào `SYSTEM_PROMPT` với ngữ nghĩa chặt chẽ để mô hình không bị "dẫn dắt" bởi tiền đề sai của người hỏi.
- **Phương án đã cân nhắc:**
  1. Dùng quy tắc Regex hoặc phân loại riêng bằng model nhỏ để bắt tiền đề sai: Khó khả thi vì các câu hỏi tiền đề sai có thể diễn đạt bằng vô số cách khác nhau (khẩu ngữ, câu hỏi tu từ, so sánh).
  2. Bổ sung quy tắc vào Prompt hệ thống (System Prompt In-Context Alignment): LLM hiểu ngữ cảnh của cả câu hỏi và tài liệu tham khảo, dễ dàng phát hiện sự mâu thuẫn giữa giả định trong câu hỏi và điều khoản văn bản để đính chính.
- **Vì sao chọn:** Tận dụng tối đa khả năng suy luận ngữ nghĩa của `gemini-flash-lite-latest`, vừa giữ độ trễ thấp (< 1.5s), vừa không làm tăng độ phức tạp của pipeline.
- **Loại căn cứ:** [tài liệu: docs/require.md, Mục 3 - Mức 2] & [đo đạc thực nghiệm].

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Tiền đề sai (False Premise / Presupposition):** Là khi câu hỏi đã ngầm khẳng định một việc sai sự thật làm tiền đề, ví dụ: *"Tại sao hôm nay trời mưa to thế?"* trong khi ngoài trời đang nắng to. Nếu AI trả lời: *"Trời mưa là vì..."* thì AI đã bị lừa (ảo giác). Trợ lý đáng tin cậy phải nói ngay: *"Hôm nay trời không mưa, ngoài trời đang nắng."*
- **Active Clarification (Chủ động hỏi lại):** Khi người hỏi đưa thông tin không đủ để kết luận duy nhất, AI không được đoán mò mà phải phân nhánh rõ từng trường hợp và gợi ý người dùng bổ sung thông tin thiếu.

## 5. Đã kiểm tra thế nào
- **Thử nghiệm thực tế câu hỏi tiền đề sai:**
  - Câu hỏi: *"Tại sao sinh viên bị kỷ luật khiển trách vẫn được xét khen thưởng danh hiệu thi đua cá nhân theo năm học?"*
  - Kết quả trả lời thực tế: *"Giả định cho rằng sinh viên bị kỷ luật khiển trách vẫn được xét khen thưởng danh hiệu thi đua cá nhân là không đúng theo quy chế. Theo quy định, không xét khen thưởng đối với sinh viên bị kỷ luật hoặc có điểm kết thúc học phần trong năm học đó dưới mức trung bình [3]."*
  - Đánh giá: **ĐẠT XUẤT SẮC** — Bác bỏ giả định sai ngay từ đầu câu, trích dẫn chuẩn xác Điều 7 Quy chế CTSV `[3]`, không có số lạ (`unsupported_numbers = []`).
- **Thử nghiệm câu hỏi điều kiện nhiều nhánh (L2-02):**
  - Câu hỏi: *"Chuẩn đầu ra ngoại ngữ tiếng Anh đối với sinh viên bậc đại học là gì?"*
  - Kết quả: Nêu rõ điều kiện áp dụng: *"áp dụng cho sinh viên các ngành không chuyên ngữ bậc Đại học hệ chính quy từ khóa 2022 trở đi [1, 2]"*, liệt kê chi tiết các bảng điểm IELTS, TOEIC, B1.
- **Kiểm tra hồi quy Unit Test:**
  - Lệnh: `cmd /c "cd /d E:\workspace\donga-rag-system\ai-service && set PYTHONPATH=.&& set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả: `Ran 82 tests in 4.522s - OK` (100% PASS, tăng từ 79 lên 82 tests).
- **Số lệnh gọi API trả phí đã dùng:** 2 lệnh gọi test suy luận thực tế.

## 6. Chưa chắc chắn, rủi ro, giả định
- Đối với những câu hỏi phức tạp kết hợp từ nhiều văn bản xung đột hiệu lực (L2-06, L2-07), cần tiếp tục nạp thêm các văn bản sửa đổi bổ sung để kiểm nghiệm khả năng phân giải mâu thuẫn thời gian.

## 7. Điều đã không làm và lý do
- Chưa làm Mức 4 (tích hợp API Cổng đào tạo xem điểm sinh viên) vì nằm ngoài phạm vi trọng tâm đề tài NCKH quy chế công khai theo `docs/require.md`.

## 8. Việc tiếp theo
- Thiết kế thí nghiệm so sánh đối chứng (Ablation Study) phục vụ bài báo/thuyết minh NCKH theo Mục 6 của `docs/require.md`.

## 9. Câu hỏi cho người dùng
- Bạn có muốn thử nghiệm thêm câu hỏi "gài bẫy" hoặc câu hỏi tình huống nào khác trên Web Chat để đối chiếu không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao một mô hình RAG nếu không có quy tắc L2-11 lại rất dễ bị ảo giác khi gặp câu hỏi dạng "Tại sao sinh viên bị cảnh cáo vẫn được học bổng?"?
2. Khi câu hỏi thiếu thông tin về khóa/ngành của sinh viên, hệ thống xử lý theo L2-02 như thế nào để không vi phạm quy chế?
3. Bằng chứng nào chứng minh câu trả lời phản thực nghiệm của hệ thống không hề bịa đặt?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì bản chất mô hình ngôn ngữ luôn cố gắng tạo ra câu trả lời hợp lý tiếp nối ngữ cảnh của prompt. Nếu người dùng đưa ra một giả định sai trong câu hỏi, mô hình có khuynh hướng "đồng tình" và tìm mọi cách giải thích cho giả định sai đó.
2. Hệ thống nêu rõ điều kiện áp dụng cho từng nhánh ngành/khóa có trong tài liệu và gợi ý người hỏi cung cấp thêm thông tin cụ thể (khóa, ngành, hệ) để đối chiếu chính xác.
3. Câu trả lời bác bỏ trực diện, trích dẫn nguồn số [3] trỏ thẳng vào Điều 7 Quy chế CTSV trong kho, và qua bộ lọc `unsupported_numbers` không ghi nhận bất kỳ số liệu lạ nào ngoài văn bản.

</details>
