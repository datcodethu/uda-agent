# BÁO CÁO XÁC MINH HỆ THỐNG VÀ TRẠNG THÁI HẠ TẦNG (SYSTEM VERIFICATION REPORT)

**Dự án:** Trợ lý hỏi đáp quy chế Đại học Đông Á (Advanced RAG)  
**Phiên:** 6I — Manual Acceptance Testing  
**Thời điểm xác minh:** Ngày 05 tháng 11 năm 2026  
**Môi trường:** Windows 11, Python venv tại `ai-service\venv`  

---

## 1. XÁC MINH NHÁNH GIT VÀ MÃ NGUỒN

| Hạng mục | Hiện trạng thực tế | Đánh giá |
|---|---|:---:|
| **Nhánh Git hiện tại** | `demo/school-presentation-2026` | ✅ Chuẩn xác |
| **Tính độc lập nhánh** | Nhánh demo cách ly hoàn toàn với nhánh `main` và các nhánh feature | ✅ An toàn |
| **Trạng thái Working Tree** | Đã cấu hình và phát triển đầy đủ các module Phiên 6H | ✅ Sẵn sàng |
| **Quy tắc commit/push** | Chưa tự ý commit, chưa push lên remote repo; Người dùng toàn quyền kiểm soát | ✅ Tuân thủ GEMINI.md |

---

## 2. XÁC MINH KHO DỮ LIỆU VECTOR & CHỈ MỤC TÌM KIẾM

### 2.1. Qdrant Local Vector Database
- **Đường dẫn vật lý:** `E:\workspace\donga-rag-system\ai-service\data\qdrant_local`
- **Tên Collection:** `donga_regulations`
- **Trạng thái lưu trữ:** Sẵn sàng đọc/ghi độc lập qua `QdrantClient(path=...)`.
- **Tổng số Points / Vectors:** 105 points (chuẩn hóa chiều dài embedding 768 chiều từ Gemini Embedding).

### 2.2. Kho Chunks JSONL & Chỉ mục BM25
- **Tệp Chunks nguồn:** `ai-service/data/chunks.jsonl`
- **Tổng số tài liệu:** 11 văn bản
- **Tổng số Chunks:** 105 chunks
- **Tệp chỉ mục BM25:** `ai-service/data/bm25_index.pkl` (Đồng bộ 100% với 105 chunks trong JSONL).

### 2.3. Chi tiết Phân bố 11 Tài liệu trong Kho:
1. `2021_8_5_8_31_26` (Nội quy học đường): 9 chunks
2. `2021_8_5_8_33_34A` (Quy chế Công tác sinh viên): 53 chunks
3. `2023_8_23_16_29_59n` (Quy chế đào tạo chính quy): 21 chunks
4. `2023_8_29_8_50_20c` (Sứ mệnh, Tầm nhìn, Triết lý giáo dục): 5 chunks
5. `2023_8_29_8_51_2A` (Giá trị cốt lõi, Đặc điểm nhận diện): 5 chunks
6. `Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai`: 2 chunks
7. `Bao_cao_nghien_cuu_Dang_ky_hoc_phan_nam_nhat`: 2 chunks
8. `Bao_cao_nghien_cuu_Mat_the_xe_sinh_vien`: 2 chunks
9. `Bao_cao_nghien_cuu_Muon_sach_Thu_vien`: 2 chunks
10. `Bao_cao_nghien_cuu_Trang_phuc_khi_di_thi`: 2 chunks
11. `web_2b329b97c1` (Trang web Giới thiệu ĐH Đông Á): 2 chunks

---

## 3. XÁC MINH HÀNG ĐỢI NẠP URL (URL APPROVAL QUEUE)

- **Tệp quản lý:** `ai-service/data/url_approval_queue.csv`
- **Thư mục Staging Markdown:** `ai-service/data/staging_url_imports/`
- **Hiện trạng:**
  * Có 1 tệp staging: `2b329b97c189971f.md` (1.367 ký tự).
  * Có 1 bản ghi: `URL-20261105-2B329B` (trạng thái `INDEXED`).
  * 0 tệp tạm thời rác tồn đọng.

---

## 4. XÁC MINH HẠ TẦNG MẠNG VÀ CỔNG DỊCH VỤ

- **Cổng dịch vụ Chatbot:** Cổng `8000` (hiện đang rảnh, sẵn sàng để Người dùng khởi động máy chủ Uvicorn).
- **Giao diện Web Chatbot:** Tự chứa hoàn toàn tại `ai-service/app/static/index.html` (CSS/JS thuần, không phụ thuộc CDN bên ngoài).
- **Endpoints chính:**
  * `GET /`: Giao diện Web Chatbot dành cho người dùng.
  * `POST /api/chat/stream`: SSE Streaming Endpoint phục vụ trả lời theo thời gian thực.
  * `POST /api/chat`: Non-streaming API trả lời toàn bộ một lần.
  * `GET /health`: Kiểm tra trạng thái máy chủ.

---

## 5. KẾT LUẬN XÁC MINH

Hệ thống đang ở trạng thái kỹ thuật ổn định, toàn bộ dữ liệu vector và chỉ mục từ khóa khớp nhau 100%. Không phát hiện xung đột dữ liệu hay tiến trình chiếm giữ cổng. Đủ điều kiện để tiến hành nghiệm thu thủ công.
