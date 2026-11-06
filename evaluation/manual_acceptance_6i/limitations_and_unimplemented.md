# BÁO CÁO CÁC HẠN CHẾ VÀ TỒN ĐỌNG KỸ THUẬT (LIMITATIONS & UNIMPLEMENTED)

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Phiên:** 6I — Manual Acceptance Testing  
**Mục tiêu:** Báo cáo trung thực, khách quan các giới hạn kỹ thuật của hệ thống ở thời điểm hiện tại, ngăn chặn việc tuyên bố "Demo Ready" một cách vội vã khi chưa hoàn thiện các mắt xích phụ trợ.  

---

## 1. DANH SÁCH CÁC HẠN CHẾ HIỆN TẠI

### 1.1. Chưa có Giao diện Đồ họa (Web UI) cho Quản trị viên Nạp & Duyệt URL
- **Hiện trạng:** Tính năng URL Import, Hàng đợi phê duyệt (Approval Queue), và Nạp tăng dần (Incremental Ingestion) hiện tại mới chỉ được cung cấp qua giao diện dòng lệnh CLI ([`scripts/manage_url_queue.py`](file:///E:/workspace/donga-rag-system/ai-service/scripts/manage_url_queue.py)).
- **Ảnh hưởng:** Người quản trị không am hiểu kỹ thuật dòng lệnh sẽ khó thao tác. Để đạt trải nghiệm "giống NotebookLM hoàn toàn", cần xây dựng thêm tab quản trị trên Web UI với form nhập URL và danh sách chờ duyệt trực quan kèm nút bấm "Duyệt" / "Từ chối".

### 1.2. Hạn chế với các Trang Web Render bằng JavaScript Client-Side (SPA)
- **Hiện trạng:** Bộ thu thập trong [`url_importer.py`](file:///E:/workspace/donga-rag-system/ai-service/app/pipeline/importer/url_importer.py) sử dụng `urllib.request` để fetch HTML tĩnh nhanh, nhẹ và ổn định (thời gian phản hồi < 0.5s, không tốn RAM).
- **Hạn chế:** Nếu website trường sử dụng Single-Page Application (SPA) render bằng JavaScript phía trình duyệt (React/Vue/Next.js), `urllib` sẽ không thể render nội dung động.
- **Giải pháp khắc phục:** Khi gặp các trang web SPA phức tạp, cần chuyển hướng sang module Crawl4AI với Playwright Chromium headless đã được xây dựng độc lập tại `ai-service/crawler/venv`.

### 1.3. Kho Tri thức vẫn còn Khoảng trống do 6 Tài liệu DOCX Chưa Duyệt
- **Hiện trạng:** Trong Phiên 6G và 6H, hệ thống đã kiểm toán độc lập 7 tài liệu DOCX và xác nhận có **6 tài liệu đủ điều kiện phê duyệt** (hướng dẫn xin giấy NVQS online, đơn chuyển ngành, đơn rút môn, đơn xin vắng thi). Tuy nhiên, các tài liệu này hiện vẫn nằm ở hàng đợi chờ duyệt, chưa được nạp vào kho chính.
- **Ảnh hưởng:** Các câu hỏi liên quan đến thủ tục nộp đơn trực tiếp, mẫu đơn hoãn nghĩa vụ quân sự hay thời hạn giải quyết (72h) vẫn chưa thể đạt trạng thái trả lời đầy đủ (vẫn ở mức PARTIAL hoặc thừa nhận thiếu thông tin).

### 1.4. Chưa Tự động Kích hoạt Pipeline Tải Tệp Đính kèm (.pdf/.docx)
- **Hiện trạng:** Bộ bóc tách HTML đã có tính năng phát hiện liên kết tệp đính kèm (`attachment_links`). Tuy nhiên, hệ thống mới chỉ dừng lại ở việc lưu danh sách URL tệp đính kèm vào metadata, chưa tự động tải về hay kích hoạt loader PDF/Word để nạp sâu vào kho.
- **Lý do kỹ thuật:** Việc tự động tải tệp nhị phân từ bên ngoài tiềm ẩn rủi ro mã độc hoặc tệp quá lớn; cần quy trình kiểm định an toàn bổ sung.

### 1.5. Giới hạn Khóa Tệp (Lock Contention) của Cơ sở Dữ liệu Cục bộ
- **Hiện trạng:** Qdrant Local và `chunks.jsonl` hoạt động dạng tệp cục bộ (Local File-based).
- **Lưu ý:** Khi máy chủ Uvicorn đang chạy và xử lý đồng thời nhiều kết nối, nếu người quản trị chạy lệnh `ingest` ở một tiến trình terminal khác, có thể xảy ra tranh chấp quyền ghi file (`file lock contention`). Khuyến nghị chạy lệnh ingest khi hệ thống không trong trạng thái tải nặng.

---

## 2. KẾT LUẬN VỀ TRẠNG THÁI "DEMO READY"

> [!WARNING]
> **Hệ thống ĐẠT YÊU CẦU DEMO KỸ THUẬT (Technical Demo Ready)** cho:
> 1. Giao diện Web Chatbot hỏi đáp 10 quy chế đào tạo cốt lõi.
> 2. Cơ chế nạp tăng dần qua CLI và trả lời câu hỏi về cơ sở vật chất / giới thiệu trường có trích dẫn nguồn web.
> 3. Cơ chế xử lý tiền đề sai, đa lượt và chính sách học vụ nhạy cảm.
> 
> **TUY NHIÊN, CHƯA ĐẠT YÊU CẦU DEMO TOÀN DIỆN CHO NGƯỜI DÙNG CUỐI (Full End-User Demo Ready)** vì:
> 1. Quản trị viên chưa có Web UI để tự dán link và bấm nút duyệt trực quan.
> 2. 6 tài liệu học vụ quan trọng chưa được nạp chính thức, dẫn đến một số câu hỏi thủ tục thực tế sinh viên hay hỏi vẫn bị thiếu thông tin.

---

## 3. LỘ TRÌNH ĐỀ XUẤT CHO PHIÊN TIẾP THEO (PHIÊN 6J)

1. **Xây dựng Web UI Admin Tab:** Thêm giao diện quản trị URL Import trên Web Chat để loại bỏ hoàn toàn sự phụ thuộc vào CLI.
2. **Nạp 6 Tài liệu DOCX Học vụ:** Người phụ trách ký duyệt chính thức để đưa 6 biểu mẫu học vụ vào Qdrant, nâng tỷ lệ câu trả lời hoàn thiện lên trên 55%.
3. **Re-benchmark Toàn diện:** Chạy lại 75 câu khảo sát để đo lường sự tăng trưởng của các chỉ số NCKH.
