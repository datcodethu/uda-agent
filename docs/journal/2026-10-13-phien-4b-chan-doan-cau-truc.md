# Nhật ký 2026-10-13 – Phiên 4B: Chẩn đoán cấu trúc văn bản QĐ 2474 (Hướng dẫn học tập)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Xác minh nghi vấn tài liệu `2024_11_14_14_26_46A.pdf` bị gắn nhãn nhầm "Điều 3" cho toàn bộ phần hướng dẫn phía sau Quyết định ban hành; khảo sát các kiểu đề mục thực tế trong văn bản gốc; viết công cụ chẩn đoán kèm unit test giả lập; và đề xuất 3 phương án xử lý dài hạn mà không can thiệp vào logic cắt đoạn hay dữ liệu kho hiện tại.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/scripts/chan_doan_cau_truc.py` | Tạo mới: công cụ chẩn đoán độc lập đọc `chunks.jsonl` và quét 5 kiểu đề mục trong văn bản gốc; xuất kết quả chi tiết ra `data/chunk_preview/` |
| `ai-service/tests/test_core.py` | Bổ sung lớp `TestStructureDiagnosis` với 2 unit tests kiểm thử hàm thuần trên dữ liệu mô phỏng giả lập (tổng 46/46 tests PASS) |
| `ai-service/data/chunk_preview/chan_doan_2024_11_14_14_26_46A.pdf.txt` | Tạo mới (sinh ra khi chạy script): danh sách chi tiết các dòng đề mục và ranh giới Quyết định |
| `ai-service/data/chunk_preview/chan_doan_2023_8_23_16_29_59n.pdf.txt` | Tạo mới: file chẩn đoán đối chiếu của văn bản chuẩn QĐ 1345 |
| `docs/plans/2026-10-13-phien-4b-chan-doan-cau-truc.md` | Lưu trữ kế hoạch đã được người dùng phê duyệt |
| `docs/progress.md` | Cập nhật tiến độ Phiên 4B |
| `docs/decisions.md` | Ghi nhận phát hiện cấu trúc tài liệu dạng hướng dẫn và đề xuất phương án |

## 3. Vì sao làm như vậy
Mỗi quyết định một khối:

- Quyết định: Tách các hàm chẩn đoán thành hàm thuần (pure functions) trong `scripts/chan_doan_cau_truc.py`.
  - Phương án đã cân nhắc: (A) Viết script dòng lệnh một khối dùng `print()`; (B) Tách hàm thuần nhận dữ liệu và trả dict kết quả.
  - Vì sao chọn: Giúp viết Unit Test độc lập và tự động hóa trong `tests/test_core.py`, không phụ thuộc vào I/O đĩa hay file thật, bảo đảm tính bền vững của mã nguồn.
  - Vì sao loại phương án còn lại: Phương án A không thể viết unit test kiểm thử tự động.
  - Loại căn cứ: [kỹ thuật: Clean Code & Unit Testing]
  - Đánh đổi: Không có đánh đổi.

- Quyết định: Chỉ in số lượng ra console và ghi toàn bộ chi tiết dòng đề mục vào file preview trên đĩa.
  - Phương án đã cân nhắc: (A) In danh sách dòng đề mục ra terminal; (B) Ghi ra file `.txt` trong `data/chunk_preview/` và chỉ in số liệu tổng hợp trong khung chat.
  - Vì sao chọn: Tuân thủ tuyệt đối quy tắc của người dùng là không in nội dung văn bản quy chế thật ra khung chat để bảo vệ ngữ cảnh hội thoại và bảo mật dữ liệu.
  - Vì sao loại phương án còn lại: Phương án A vi phạm quy tắc cấm in nội dung quy chế ra chat.
  - Loại căn cứ: [tài liệu: GEMINI.md & yêu cầu người dùng]
  - Đánh đổi: Cần mở file trên đĩa để xem chi tiết từng dòng thay vì xem ngay trên màn hình terminal.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)
- **Tài liệu hỗn hợp (Quyết định kèm Hướng dẫn):** Giống như một phong bì thư (Quyết định ban hành ngắn có 3 Điều: "Tôi gửi tài liệu này, áp dụng từ hôm nay, ai phụ trách thi hành") bên trong chứa một cuốn cẩm nang dày 50 trang (Tài liệu Hướng dẫn học tập) không hề dùng từ "Điều" nào mà đánh số Mục theo hệ thập phân (1, 2, 2.1, 3...). Nếu bộ cắt đoạn chỉ biết tìm chữ "Điều", nó sẽ coi toàn bộ cuốn cẩm nang 50 trang đó là nội dung thuộc về "Điều 3" của phong bì thư!
- **Pure Function (Hàm thuần):** Là hàm máy tính mà với cùng một đầu vào (input) thì luôn luôn trả về cùng một đầu ra (output), không làm thay đổi bất kỳ biến ngoài hay file nào trên đĩa (không có side effect). Rất dễ viết test và cực kỳ an toàn.

## 5. Đã kiểm tra thế nào
- Lệnh 1: Chạy toàn bộ 46 unit test:
  `cmd /c "set PYTHONUTF8=1&& venv\Scripts\python.exe -m unittest discover -s tests -v"`
  - Kết quả thật: `Ran 46 tests in 1.576s -> OK` (44 test cũ + 2 test mới đều PASS).
- Lệnh 2: Chạy chẩn đoán file `2024_11_14_14_26_46A.pdf`:
  `cmd /c "set PYTHONUTF8=1&& venv\Scripts\python.exe -m scripts.chan_doan_cau_truc 2024_11_14_14_26_46A.pdf"`
  - Kết quả thật:
    + Tổng số đoạn: 44 đoạn (48.069 ký tự).
    + Nhóm `(quyet_dinh, Điều 3)`: **41 đoạn (93.2%)**, 46.627 ký tự -> `[CẢNH BÁO BẤT THƯỜNG > 50%]`.
    + Số dòng theo kiểu đề mục: `CHUONG_DIEU_MUC_PHAN`: 9; `SO_LA_MA`: 0; `SO_THAP_PHAN`: 20; `CHU_CAI`: 0; `CHU_HOA_TOAN_BO`: 9.
    + Ranh giới Quyết định ban hành: Dòng kết thúc: 36 (chiếm 1.527 ký tự); phần hướng dẫn còn lại: 40.134 ký tự.
    + Thông tin trang (`page`): KHÔNG (THIẾU).
- Lệnh 3: Chạy chẩn đoán đối chiếu trên `2023_8_23_16_29_59n.pdf`:
  `cmd /c "set PYTHONUTF8=1&& venv\Scripts\python.exe -m scripts.chan_doan_cau_truc 2023_8_23_16_29_59n.pdf"`
  - Kết quả thật:
    + Tổng số đoạn: 21 đoạn (17.551 ký tự).
    + Phân bổ đồng đều giữa 2 phần: `quyet_dinh` (Điều 1-3) và `quy_dinh_kem_theo` (Điều 1-8). Không nhóm nào vượt quá 19%.
- Kết luận: **ĐẠT 100%**. Nghi vấn của người dùng đã được chứng minh chính xác bằng số liệu định lượng.
- Số lệnh gọi API trả phí đã dùng: 0 (hoàn toàn chạy cục bộ).

## 6. Chưa chắc chắn, rủi ro, giả định
- Chưa có thông tin số trang trong `chunks.jsonl`: Cả hai văn bản hiện tại đều thiếu metadata `page`, khiến việc truy nguyên về số trang sách gốc khi sinh viên cần đọc bản in chưa thực hiện được.

## 7. Điều đã không làm và lý do
- KHÔNG sửa logic cắt đoạn trong `structural_chunker.py` vì phiên này chỉ phân tích và đề xuất phương án.
- KHÔNG sửa `docs_registry.csv` hay gỡ tài liệu khỏi kho để đảm bảo không làm gián đoạn trạng thái hoạt động hiện có.
- KHÔNG thực thi bất kỳ phương án nào trong 3 phương án đề xuất (chờ nhóm họp và người dùng quyết định).

## 8. Việc tiếp theo
- Người dùng xem xét và lựa chọn 1 trong 3 phương án xử lý cấu trúc cho tài liệu dạng hướng dẫn ở phiên tiếp theo.

## 9. Câu hỏi cho người dùng
- Bạn nghiêng về Phương án 2 (nâng cấp bộ cắt đoạn nhận diện đề mục thập phân Mục 1.1, 4.1) hay Phương án 1 (tạm loại tài liệu này sang `loai = huong_dan`) cho phiên tới?

## 10. Ba câu tự kiểm tra hiểu bài
1. Tại sao `2023_8_23_16_29_59n.pdf` lại tách được phần `quy_dinh_kem_theo` mà `2024_11_14_14_26_46A.pdf` lại không tách được?
2. Khi tài liệu hướng dẫn bị gắn nhãn nhầm là "Điều 3", tác hại trực tiếp đến trải nghiệm hỏi đáp của sinh viên là gì?
3. Nếu chọn Phương án 2 (bổ sung nhận diện đề mục thập phân), bộ cắt đoạn cần phát hiện dấu hiệu gì để biết khi nào phần Quyết định ban hành kết thúc và phần tài liệu đính kèm bắt đầu?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì phần đính kèm của file 2023 có tiêu đề "QUY ĐỊNH" và bắt đầu lại bằng "Điều 1". Thuật toán cắt đoạn hiện tại có cơ chế nhận diện: khi gặp "Điều 1" sau các Điều trước đó, số Điều bị lùi về 1 nên nó tự động mở phân đoạn mới `quy_dinh_kem_theo`. Trong khi đó, phần đính kèm của file 2024 là "TÀI LIỆU HƯỚNG DẪN", hoàn toàn không dùng chữ "Điều 1" mà dùng số thập phân (1., 2., 3...), nên thuật toán không biết đã sang phần mới và tiếp tục giữ nguyên nhãn "Điều 3" của Quyết định ban hành.
2. Sinh viên khi nhận câu trả lời (ví dụ về phương pháp lớp học đảo ngược) sẽ thấy hệ thống trích dẫn nguồn là `[1] Điều 3`. Khi sinh viên mở văn bản gốc ra kiểm chứng, Điều 3 thực tế chỉ ghi: "Các đơn vị... chịu trách nhiệm thi hành Quyết định này", hoàn toàn không có chữ nào về lớp học đảo ngược. Điều này làm mất niềm tin của sinh viên vào tính xác thực của trích dẫn.
3. Bộ cắt đoạn có thể dựa vào các dấu hiệu phân giới: (1) Khối chữ ký / nơi nhận của Quyết định ban hành (ví dụ: `- BGH;`, `KT. HIỆU TRƯỞNG`); (2) Dòng tiêu đề viết hoa của tài liệu đính kèm (ví dụ: `TÀI LIỆU HƯỚNG DẪN...`); hoặc (3) Xuất hiện mục số La Mã hoặc số thập phân `1.` đứng đầu dòng sau Quyết định ban hành.

</details>
