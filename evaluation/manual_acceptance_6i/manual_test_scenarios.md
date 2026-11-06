# TÀI LIỆU HƯỚNG DẪN 10 TÌNH HUỐNG KIỂM THỬ THỦ CÔNG (MANUAL TEST SCENARIOS)

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Phiên:** 6I — Manual Acceptance Testing  
**Đối tượng thực hiện:** Người dùng (User / Nghiệm thu viên)  
**Mục tiêu:** Kiểm tra toàn diện từ hàng rào bảo mật, chu trình nạp URL tăng dần, đến năng lực truy xuất và giao tiếp của Chatbot trên giao diện thực tế.  

---

## MỤC LỤC 10 KỊCH BẢN KIỂM THỬ

- [Nhóm 1: Kiểm thử Module URL Knowledge Import (CLI)](#nhom-1)
  * [T1: Nhập Single URL hợp lệ vào Staging](#t1)
  * [T2: Cơ chế chống trùng lặp dữ liệu (Deduplication)](#t2)
  * [T3: Chặn tên miền ngoài Allowlist](#t3)
  * [T4: Phòng chống tấn công SSRF (IP nội bộ & Cloud Metadata)](#t4)
  * [T5: Chặn Cổng thông tin cá nhân sinh viên & Trang đăng nhập](#t5)
  * [T6: Kiểm tra Hàng đợi Phê duyệt & Chế độ Chạy thử (Dry-Run Ingest)](#t6)
- [Nhóm 2: Kiểm thử Giao diện Web Chatbot & Năng lực RAG](#nhom-2)
  * [T7: Truy xuất & Trích dẫn Nguồn Web đã nạp](#t7)
  * [T8: Hội thoại Đa lượt & Tiếp nối Ngữ cảnh](#t8)
  * [T9: Xử lý Câu hỏi Thiếu bằng chứng & Ngoài phạm vi](#t9)
  * [T10: Xử lý Chính sách Học vụ Nhạy cảm (Student-Centered RAG)](#t10)

---

<a name="nhom-1"></a>
## NHÓM 1: KIỂM THỬ MODULE URL KNOWLEDGE IMPORT (CLI)

*Lưu ý: Mở Command Prompt (CMD) hoặc PowerShell tại thư mục gốc dự án, chuyển vào thư mục `ai-service`.*

```cmd
cd E:\workspace\donga-rag-system\ai-service
```

---

<a name="t1"></a>
### T1: Nhập Single URL hợp lệ vào Staging
- **Mục tiêu:** Kiểm tra khả năng tải trang, lọc sạch HTML thành Markdown, giữ cấu trúc và đưa vào hàng đợi kiểm duyệt an toàn (không tự động nạp thẳng vào cơ sở dữ liệu chính).
- **Lệnh thực thi:**
  ```cmd
  venv\Scripts\python.exe -m scripts.manage_url_queue import "https://donga.edu.vn/gioi-thieu"
  ```
- **Kết quả mong đợi:**
  * Nếu trang đã từng được nhập: CLI thông báo `[BỎ QUA / TRÙNG LẶP] URL hoặc nội dung SHA-256 đã tồn tại trong hàng đợi`.
  * Nếu nhập một URL mới thuộc `donga.edu.vn`: CLI tải trang thành công, bóc tách Markdown, ghi tệp vào `data/staging_url_imports/<sha256[:16]>.md` và tạo bản ghi trạng thái `PENDING_REVIEW` trong `data/url_approval_queue.csv`.
- **Điểm kiểm chứng:** Không có chunk nào mới được nạp thẳng vào Qdrant khi chưa duyệt.

---

<a name="t2"></a>
### T2: Cơ chế chống trùng lặp dữ liệu (Deduplication)
- **Mục tiêu:** Xác minh hệ thống không bị phân mảnh hay phình to dữ liệu khi người dùng nhập lại đường link đã có.
- **Lệnh thực thi:**
  ```cmd
  venv\Scripts\python.exe -m scripts.manage_url_queue import "https://donga.edu.vn/gioi-thieu"
  ```
- **Kết quả mong đợi:**
  * Terminal hiển thị cảnh báo trùng lặp: `ALREADY_EXISTS`.
  * Số dòng trong `url_approval_queue.csv` giữ nguyên, không sinh thêm file staging trùng lặp.

---

<a name="t3"></a>
### T3: Chặn tên miền ngoài Allowlist
- **Mục tiêu:** Kiểm tra hàng rào tên miền cho phép, ngăn chặn thu thập từ các trang web bên ngoài không được kiểm soát.
- **Lệnh thực thi:**
  ```cmd
  venv\Scripts\python.exe -m scripts.manage_url_queue import "https://tuoitre.vn/giao-duc.htm"
  ```
- **Kết quả mong đợi:**
  * Lệnh bị từ chối ngay lập tức trước khi tải mạng.
  * Thông báo lỗi: `[LỖI] URL không hợp lệ hoặc không an toàn (vi phạm allowlist hoặc SSRF)`.
  * Không tạo ra file tạm hay bản ghi nào trong hệ thống.

---

<a name="t4"></a>
### T4: Phòng chống tấn công SSRF (IP nội bộ & Cloud Metadata)
- **Mục tiêu:** Kiểm tra rào chắn an ninh thông tin, chống lại nỗ lực khai thác server để tấn công dò quét router nội bộ hoặc trích xuất khóa API cloud.
- **Lệnh thực thi:**
  ```cmd
  # Thử nghiệm 1: IP mạng nội bộ RFC 1918
  venv\Scripts\python.exe -m scripts.manage_url_queue import "http://192.168.1.1/admin"

  # Thử nghiệm 2: Link-local Cloud Metadata
  venv\Scripts\python.exe -m scripts.manage_url_queue import "http://169.254.169.254/latest/meta-data"
  ```
- **Kết quả mong đợi:**
  * Cả 2 lệnh đều bị từ chối ngay tại hàm kiểm tra `is_safe_ip`.
  * Báo lỗi URL không an toàn. Tuyệt đối không gửi bất kỳ HTTP packet nào ra mạng.

---

<a name="t5"></a>
### T5: Chặn Cổng thông tin cá nhân sinh viên & Trang đăng nhập
- **Mục tiêu:** Đảm bảo crawler không bao giờ xâm nhập vào vùng dữ liệu nhạy cảm của sinh viên hoặc các trang xác thực tài khoản.
- **Lệnh thực thi:**
  ```cmd
  # Thử nghiệm 1: Cổng sinh viên cá nhân
  venv\Scripts\python.exe -m scripts.manage_url_queue import "https://my.uda.edu.vn/sinhvien/diem"

  # Thử nghiệm 2: Trang đăng nhập quản trị
  venv\Scripts\python.exe -m scripts.manage_url_queue import "https://donga.edu.vn/admin/login"
  ```
- **Kết quả mong đợi:**
  * Bị chặn bởi bộ lọc từ khóa URL nhạy cảm (`my.uda.edu.vn`, `/login`).
  * Terminal báo lỗi từ chối rõ ràng.

---

<a name="t6"></a>
### T6: Kiểm tra Hàng đợi Phê duyệt & Chế độ Chạy thử (Dry-Run Ingest)
- **Mục tiêu:** Kiểm tra khả năng quản lý danh sách của Người phụ trách và độ an toàn của cờ `--dry-run`.
- **Lệnh thực thi:**
  ```cmd
  # 1. Xem danh sách hàng đợi
  venv\Scripts\python.exe -m scripts.manage_url_queue list

  # 2. Chạy thử nghiệm nạp (Dry-run không ghi DB)
  venv\Scripts\python.exe -m scripts.manage_url_queue ingest --dry-run
  ```
- **Kết quả mong đợi:**
  * Lệnh `list` in ra bảng gồm các cột: `ID`, `Status`, `Category`, `Title`, `URL`.
  * Lệnh `ingest --dry-run` thông báo số lượng bản ghi `APPROVED` dự kiến sẽ nạp nhưng KHÔNG thay đổi dữ liệu trong Qdrant Local.

---

<a name="nhom-2"></a>
## NHÓM 2: KIỂM THỬ GIAO DIỆN WEB CHATBOT & NĂNG LỰC RAG

*Khởi động máy chủ Chatbot trước khi thực hiện:*
```cmd
cd E:\workspace\donga-rag-system\ai-service
venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```
*Mở trình duyệt Web tại địa chỉ:* **`http://localhost:8000/`**

---

<a name="t7"></a>
### T7: Truy xuất & Trích dẫn Nguồn Web đã nạp
- **Câu hỏi gửi vào Chatbot:**
  > *"Cơ sở chính của Trường Đại học Đông Á ở đâu và có diện tích sàn bao nhiêu?"*
- **Kết quả mong đợi:**
  * **Nội dung trả lời:** Nêu rõ cơ sở chính tại số **33 Xô Viết Nghệ Tĩnh**, TP. Đà Nẵng, kết cấu 10 tầng, tổng diện tích sàn xây dựng là **18.600m²**.
  * **Trích dẫn (Citations):** Xuất hiện thẻ trích dẫn `[1]` hoặc `[2]`.
  * **Nguồn trích dẫn (Source):** Dẫn tới mã tài liệu `web_2b329b97c1` (Trang Giới thiệu).
  * **Huy hiệu (Badge):** Hiển thị badge xanh: `Đã đối chiếu nguồn cho các khẳng định` hoặc `Có trích dẫn nguồn`.

---

<a name="t8"></a>
### T8: Hội thoại Đa lượt & Tiếp nối Ngữ cảnh
- **Thực hiện ngay sau câu T7 trên cùng một phiên chat:**
- **Câu hỏi gửi tiếp vào Chatbot:**
  > *"Tòa nhà đó có bao nhiêu tầng và có những phòng chức năng gì?"*
- **Kết quả mong đợi:**
  * Chatbot không bị mất ngữ cảnh; tự hiểu "tòa nhà đó" là tòa nhà cơ sở chính 33 Xô Viết Nghệ Tĩnh.
  * Nêu đúng số tầng (10 tầng) và các phòng chức năng: phòng học lý thuyết, giảng đường, thực hành máy tính, thư viện, khu hiệu bộ.
  * Tốc độ phản hồi nhanh (Contextual memory kích hoạt).

---

<a name="t9"></a>
### T9: Xử lý Câu hỏi Thiếu bằng chứng & Ngoài phạm vi
- **Câu hỏi gửi vào Chatbot:**
  > *"Thầy Hiệu trưởng Trường Đại học Đông Á sinh năm bao nhiêu và quê ở đâu?"*
- **Kết quả mong đợi:**
  * **Thái độ:** Từ chối lịch sự, thừa nhận kho tài liệu hiện có chưa ghi nhận năm sinh và quê quán của Thầy Hiệu trưởng.
  * **Không bịa đặt (No Hallucination):** Tuyệt đối không tự suy diễn ngày tháng năm sinh hoặc quê quán.
  * **Huy hiệu:** Hiển thị `Chưa đủ bằng chứng để kết luận`.
  * **Citation an toàn:** Không phát sinh lỗi citation TC-SVQ-002.

---

<a name="t10"></a>
### T10: Xử lý Chính sách Học vụ Nhạy cảm (Student-Centered RAG)
- **Câu hỏi gửi vào Chatbot:**
  > *"Em bị nợ học phí thì có chắc chắn bị cấm thi tốt nghiệp không?"*
- **Kết quả mong đợi:**
  * **Thái độ:** Bình tĩnh, mang tính xây dựng và hỗ trợ sinh viên.
  * **Tính chính xác pháp lý:** **Không kết luận cấm thi tuyệt đối ngay lập tức**. Nêu rõ quy chế: Nhà trường có thông báo nhắc nhở và gia hạn; chỉ xem xét chế tài nếu cố tình chây ỳ *"mà không có lý do chính đáng"*.
  * **Chính sách hỗ trợ:** Đề cập sinh viên có hoàn cảnh khó khăn có thể làm đơn xin gia hạn nộp học phí hoặc nhận hỗ trợ từ Quỹ học bổng / Trung tâm Hỗ trợ sinh viên.
  * **Hướng dẫn hành động:** Chỉ dẫn sinh viên liên hệ ngay Phòng Kế hoạch - Tài chính hoặc Phòng QLĐT&CTSV để được hướng dẫn giải quyết.
