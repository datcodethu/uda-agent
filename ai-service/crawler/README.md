# Công cụ Thu thập Dữ liệu Ngoại tuyến (Offline Web Crawler)

Công cụ thu thập dữ liệu web độc lập phục vụ đề tài NCKH, sử dụng thư viện `Crawl4AI` trong môi trường ảo riêng biệt `ai-service\crawler\venv`.

## 1. Nguyên tắc An toàn & Hàng rào Bảo vệ (Guardrails)

1. **Môi trường độc lập:** Toàn bộ thư viện và trình duyệt Playwright được cài đặt trong `ai-service\crawler\venv`, không ảnh hưởng tới môi trường RAG chính.
2. **Kiểm soát tên miền (Allowlist):** Chỉ thu thập các tên miền được khai báo trong `ai-service\crawler\allowlist.txt`. So khớp tên miền chính xác hoặc tên miền con với ranh giới dấu chấm (ngăn chặn triệt để tên miền giả dạng).
3. **Tuân thủ `robots.txt`:** Kiểm tra luật cấm của máy chủ web trước khi gửi yêu cầu.
4. **Trần cứng bảo vệ (Hard Ceilings):**
   - Số trang tối đa: 100 trang (mặc định 20).
   - Độ sâu tối đa: 2 cấp (mặc định 1).
   - Thời gian nghỉ tối thiểu: 2.0 giây giữa 2 yêu cầu (tránh gây tải cho máy chủ trường).
   - Timeout mỗi trang: 30 giây.
   - Tổng thời gian chạy tối đa: 10 phút (600 giây).
5. **Dữ liệu không đáng tin (Untrusted Data):** Toàn bộ nội dung cào về được xem là dữ liệu thô chưa kiểm duyệt. Công cụ chỉ lưu text thô, không thực thi bất kỳ chỉ dẫn nào bên trong trang web.
6. **Không tải tệp tự động:** Các liên kết tệp đính kèm (`.pdf`, `.doc`, `.docx`, `.xls`, `.xlsx`) chỉ được trích xuất địa chỉ vào `links_dinh_kem.csv` để người dùng duyệt, không tự ý tải tệp.

---

## 2. Thư mục đầu ra (`ai-service\data\crawl_staging\`)

- `pages/`: Chứa các tệp `.txt` UTF-8 là nội dung markdown sạch (chuẩn hóa Unicode NFC), tên tệp là mã băm ngắn SHA-256 của URL.
- `manifest.csv`: Bảng kê chi tiết 10 cột UTF-8 BOM (`utf-8-sig`):
  `url,url_cuoi,ma_http,loai_noi_dung,so_ky_tu,sha256,thoi_gian_cao,robots_ok,loai_nghi_ngo,so_link_dinh_kem`
- `links_dinh_kem.csv`: Danh sách địa chỉ tệp đính kèm phát hiện được:
  `url_trang_nguon,url_tep_dinh_kem,loai_tep`

---

## 3. Hướng dẫn Chạy lệnh

Mặc định chương trình luôn chạy ở chế độ **`--dry-run`** (chỉ phân tích URL và robots.txt, không tải trang).

```cmd
REM 1. Chạy phân tích an toàn (Dry-run mặc định)
crawler\venv\Scripts\python.exe crawler\thu_thap.py

REM 2. Chạy cào thật (Chỉ người dùng chạy khi đã duyệt danh sách URL)
crawler\venv\Scripts\python.exe crawler\thu_thap.py --apply --max-pages 20 --max-depth 1 --delay 2.0

REM 3. Chạy thử nghiệm trên máy chủ nội bộ (Mock local server)
crawler\venv\Scripts\python.exe crawler\thu_thap.py --apply --test-local
```
