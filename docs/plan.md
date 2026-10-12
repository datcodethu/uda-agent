# Kế hoạch thiết kế hệ thống RAG hỏi đáp học vụ – ĐH Đông Á
**Ngày:** 8 thg 10, 2026 · **Tác giả:** @đạt

---

## 1. Tổng quan
**Mục tiêu một câu:** Xây một web chat để sinh viên Đại học Đông Á hỏi về học vụ bằng tiếng Việt tự nhiên và nhận câu trả lời đúng, có trích dẫn văn bản gốc của trường, kèm một web admin để phòng Đào tạo tự cập nhật tài liệu.

### 1.1 Bài toán
* Sinh viên hiện hỏi bạn bè, nhóm Zalo/Facebook hoặc Google. Thông tin dễ cũ, dễ sai, nhiều bạn "không biết hỏi ai".
* ChatGPT hay Gemini dùng riêng sẽ không biết quy chế của Đông Á và có thể bịa ra câu trả lời nghe rất hợp lý (gọi là ảo giác – hallucination).
* Chatbot theo kịch bản (rule-based) chỉ trả lời được những câu đã lập trình sẵn, sinh viên hỏi khác đi một chút là hỏng.

### 1.2 RAG là gì (giải thích đơn giản)
Hãy tưởng tượng một sinh viên đi thi được mở tài liệu. Bạn ấy không nhớ hết quy chế, nhưng khi gặp câu hỏi thì lật đúng trang cần thiết, đọc, rồi tự viết lại câu trả lời. RAG làm đúng như vậy:
* **Retrieval (truy xuất):** Từ câu hỏi, hệ thống tìm vài đoạn quy chế liên quan nhất trong kho tài liệu của trường.
* **Augmented (tăng cường):** Các đoạn tìm được được dán kèm vào câu hỏi gửi cho AI.
* **Generation (sinh):** AI chỉ được dựa vào các đoạn đó để viết câu trả lời, và nếu không thấy thông tin thì phải nói "không tìm thấy".

Nhờ vậy AI không cần học lại (fine-tune) mà vẫn trả lời đúng; khi quy chế đổi, chỉ cần tải tài liệu mới lên.

### 1.3 Phạm vi
| Trong phạm vi | Ngoài phạm vi (giai đoạn này) |
| :--- | :--- |
| Hỏi đáp quy chế, học phí, học bổng, chuẩn đầu ra, thủ tục, điểm rèn luyện, bảo hiểm y tế | Tra cứu điểm, lịch học, công nợ cá nhân của từng sinh viên (cần kết nối hệ thống quản lý đào tạo) |
| Nguồn: văn bản chính thức đã được phòng Đào tạo duyệt | Tư vấn học tập chung ("học CSDL thế nào"), chuyện ngoài trường |
| Web chat + web admin, tiếng Việt | App di động, Zalo/Messenger (để mở rộng sau) |

### 1.4 Sản phẩm đầu ra
* Web chat cho sinh viên (React + TypeScript).
* Web admin quản lý tài liệu, theo dõi câu hỏi, đánh giá câu trả lời.
* Backend Spring Boot + dịch vụ RAG + vector database.
* Báo cáo đánh giá định lượng mô hình RAG (độ chính xác, mức ảo giác) – đây là phần nghiên cứu khoa học cốt lõi, không chỉ là sản phẩm phần mềm.

---

## 2. Khảo sát sinh viên và điều rút ra cho thiết kế
Khảo sát có khoảng 50 phản hồi (49 dòng đọc được rõ; số dưới đây là gần đúng). Mẫu gồm sinh viên năm 1 (38/49), năm 3 (9), năm 2 (1), năm 4 (1); chủ yếu ngành CNTT và Ngôn ngữ Trung. Trong báo cáo cần nêu rõ mẫu khảo sát lệch về năm 1.

### 2.1 Sinh viên hỏi những gì
| Chủ đề | Số người chọn (≈/49) | Ví dụ câu hỏi thật |
| :--- | :--- | :--- |
| Điều kiện tốt nghiệp, chuẩn đầu ra | 30 | "Ngoại ngữ tốt nghiệp cần chuẩn B mấy?", "IT chọn đầu ra tiếng Nhật cần N4 và B1 hay chỉ N4?" |
| Đăng ký học phần, lịch học | 23 | "Khi nào có lịch đăng ký học phần?", "Trùng lịch thì học môn nào trước?" |
| Điểm rèn luyện, công tác xã hội | 23 | "Cách cộng điểm rèn luyện cần làm gì?" |
| Quy chế thi, học lại, cải thiện điểm | 21 | "Học lại rơi vào các trường hợp nào?", "Học cải thiện nhiều có hạ bằng không?" |
| Thực tập, đồ án | 21 | "Thực tập ra sao?" |
| Học phí, miễn giảm | 16 | "Nợ học phí có được đăng ký môn/thi không?" (lặp lại 3 lần), "Học phí có thoại chia nhỏ không?" |
| Học bổng | 15 | "Điều kiện xét học bổng?" |
| Bảo hiểm y tế | 10 | "BHYT có bắt buộc không?", "Đã miễn BHYT ở quê có được hoàn không?" |
| Thủ tục hành chính | 9 | "Làm giấy vay vốn sinh viên ở đâu?" |

### 2.2 Sinh viên tìm câu trả lời ở đâu và lo ngại gì
* **Kênh hiện tại:** Bạn bè/anh chị (27), nhóm Zalo/Facebook (25), fanpage/website trường (23), Google (22); chỉ 11 người hỏi trực tiếp phòng Đào tạo/cố vấn; 8 người "không biết hỏi ai".
* **Thời điểm hỏi nhiều nhất:** Đầu kỳ (hơn nửa số người chỉ chọn đúng mục này), tiếp đến là đợt đăng ký học phần, trước kỳ thi và cuối kỳ.
* **Sẵn sàng dùng chatbot:** 21 "Có", 24 "Tùy trường hợp", chỉ 4 "Không".
* **Nơi muốn dùng:** Ứng dụng riêng (18), website trường (14), Zalo (8), Messenger (6).
* **Lo ngại chính:** Không hiểu câu hỏi của mình (36), thông tin cũ (32), trả lời sai (25), lộ thông tin cá nhân (23).

### 2.3 Điều cần rút ra cho thiết kế
* Ưu tiên nạp trước các nhóm tài liệu: chuẩn đầu ra/tốt nghiệp, quy chế đào tạo (học lại, cải thiện, cấm thi), điểm rèn luyện, học phí, học bổng, BHYT, thực tập.
* Lo "thông tin cũ" và "trả lời sai" $\rightarrow$ mỗi câu trả lời phải có nguồn + ngày hiệu lực của văn bản; admin có trạng thái hiệu lực/hết hiệu lực cho tài liệu.
* Lo "không hiểu câu hỏi" (chiếm nhiều nhất) $\rightarrow$ sinh viên viết ngắn, sai chính tả, viết tắt ("bhyt", "csdl", "IT", "N4") nên cần bước viết lại câu hỏi (query rewriting), từ điển viết tắt và nút gợi ý câu hỏi.
* Lo lộ thông tin cá nhân $\rightarrow$ không lưu mã sinh viên/họ tên trong log; cảnh báo khi người dùng nhập số điện thoại, CCCD, số tiền nợ cụ thể.
* Một số câu hỏi cần dữ liệu cá nhân ("em đóng trước 10 triệu, thiếu 9,2 triệu có được thi không"). RAG chỉ trả lời phần quy định chung; phần số liệu cá nhân cần hướng dẫn về cổng sinh viên hoặc mở rộng ở giai đoạn sau.
* Nhiều câu không thuộc học vụ ("làm sao học CSDL", "CLB khi nào phỏng vấn") $\rightarrow$ cần bước phân loại ý định và trả lời từ chối lịch sự khi ngoài phạm vi.
* Hiển thị tối ưu trên điện thoại: web phải responsive và kiến trúc backend tách lớp để sau này cắm thêm kênh Zalo/Messenger qua API.
* *Lưu ý:* Các câu hỏi thực tế được dùng làm cơ sở cho bộ kiểm thử ở mục 10.

---

## 3. Yêu cầu hệ thống
### 3.1 Tác nhân hệ thống
* **Sinh viên:** Hỏi đáp, xem lại lịch sử chat, đánh giá câu trả lời (Đúng/Sai).
* **Cán bộ phòng Đào tạo (Admin):** Tải/sửa/gỡ tài liệu, duyệt văn bản, xem thống kê câu hỏi, xử lý câu hỏi AI trả lời kém.
* **Quản trị viên hệ thống (Super Admin):** Quản lý tài khoản admin, cấu hình mô hình AI, xem log hệ thống.
* **Hệ thống AI (Tác nhân phụ):** Nhận câu hỏi + ngữ cảnh, truy xuất dữ liệu và sinh câu trả lời.

### 3.2 Use Case chính
* **UC1 - Hỏi đáp học vụ:** SV gõ câu hỏi $\rightarrow$ nhận câu trả lời kèm nguồn trích dẫn.
* **UC2 - Hỏi tiếp theo ngữ cảnh:** Xử lý hội thoại tiếp nối ("còn học bổng thì sao?").
* **UC3 - Đánh giá câu trả lời:** Đánh dấu Đúng/Sai kèm lý do nhằm cải thiện hệ thống.
* **UC4 - Quản lý lịch sử chat:** Xem lại hoặc xóa cuộc trò chuyện.
* **UC5 - Quản lý tài liệu:** Admin tải PDF/DOCX lên, hệ thống cắt đoạn, nhúng vector và lưu trữ; quản lý hiệu lực.
* **UC6 - Theo dõi câu hỏi:** Admin xem câu hỏi phổ biến, câu AI trả lời "không tìm thấy", câu bị gắn cờ sai.
* **UC7 - Bổ sung câu trả lời chuẩn (FAQ):** Admin tạo FAQ ưu tiên cho câu hỏi mà AI trả lời chưa chuẩn.
* **UC8 - Quản trị tài khoản:** Đăng nhập, phân quyền quản trị.

### 3.3 Yêu cầu chức năng
* **Web Sinh viên:** Khung chat hỗ trợ streaming text (SSE); hiển thị nguồn trích dẫn (văn bản, điều, khoản, ngày hiệu lực); nút phản hồi Đúng/Sai; gợi ý câu hỏi phổ biến; phản hồi lịch sự khi ngoài phạm vi; quản lý lịch sử trò chuyện.
* **Web Admin:** Quản lý tài liệu (tải lên, theo dõi trạng thái `PROCESSING`, `READY`, `FAILED`, gắn nhãn hiệu lực); Dashboard phân tích tần suất câu hỏi, tỉ lệ câu trả lời thành công / không tìm thấy; Quản lý kho FAQ chuẩn; Quản trị người dùng và phân quyền.

### 3.4 Yêu cầu phi chức năng
* **Tốc độ:** Chữ đầu tiên hiện ra (Time to First Token) dưới 3 giây; hoàn tất câu trả lời dưới 10 giây.
* **Độ chính xác:** Chỉ số Faithfulness $\ge 0.85$ trên bộ kiểm thử chuẩn.
* **Khả dụng:** Chịu tải đồng thời tối thiểu 100 người dùng; sẵn sàng trong đợt cao điểm đầu kỳ.
* **Bảo mật:** Mật khẩu mã hóa BCrypt, cơ chế JWT kèm Refresh Token, kiểm soát truy cập theo vai trò (RBAC), không lưu dữ liệu PII nhạy cảm.
* **Giao diện:** Tương thích di động (Mobile Responsive), chạy mượt mà trên Chrome, Safari, Edge, Firefox.
* **Khả năng mở rộng:** Kiến trúc lỏng (loosely coupled), dễ thay thế LLM/Vector DB; sẵn sàng tích hợp API đa kênh.
* **Chi phí:** Tối ưu chi phí API trên mỗi 1.000 truy vấn.

---

## 4. Kiến trúc tổng thể
Hệ thống chia làm 4 tầng độc lập:
1. **Presentation Layer:** Web Chat & Web Admin (React + TypeScript).
2. **Business API Layer:** Backend Spring Boot (Gateway, Auth, Logging, Orchestration).
3. **AI Core Service:** Python FastAPI (LangChain/LlamaIndex, RAG pipeline, Query rewriting).
4. **Data Layer:** PostgreSQL (dữ liệu nghiệp vụ) và Qdrant (Vector Database).

Sinh viên kết nối qua Backend Spring Boot, không gọi trực tiếp vào AI Service hay Vector DB.

### 4.1 Lựa chọn công nghệ
| Thành phần | Lựa chọn | Lý do |
| :--- | :--- | :--- |
| **Frontend** | React + TypeScript + Ant Design | Đồng bộ thuyết minh, Ant Design cung cấp đầy đủ UI components cho Admin |
| **Backend** | Spring Boot (Java) | Bảo mật tốt, quản lý phiên và phân quyền mạnh mẽ, thiết kế RESTful chuẩn |
| **AI Service** | Python (FastAPI) + LangChain | Hệ sinh thái AI/NLP phong phú, tối ưu tốt nhất cho các công cụ đánh giá (RAGAS) |
| **Vector DB** | Qdrant (hoặc ChromaDB / pgvector) | Khả năng lọc payload/metadata nhanh, hỗ trợ Hybrid Search tốt, đóng gói Docker nhẹ |
| **RDBMS** | PostgreSQL | Bền vững, quan hệ bảng chặt chẽ, hỗ trợ JSONB |
| **Embedding** | Multilingual Model (OpenAI / bge-m3) | Khả năng hiểu ngữ nghĩa tiếng Việt học vụ tốt |
| **LLM** | Gemini Flash / OpenAI GPT-4o-mini | Cân bằng hoàn hảo giữa chi phí thấp, độ trễ nhỏ và chất lượng sinh tiếng Việt |

---

## 5. Thiết kế Pipeline RAG
Hệ thống vận hành với 2 luồng độc lập: **Luồng A (Nạp tài liệu)** và **Luồng B (Truy xuất & Sinh câu trả lời)**.

### 5.1 Nạp tài liệu (Luồng A)
* **Thu thập:** Các văn bản chính thức có số hiệu và ngày ban hành (Quy chế đào tạo, chuẩn đầu ra, học bổng, học phí, BHYT).
* **Trích xuất:** Đọc file PDF/DOCX văn bản số. Trường hợp PDF scan phải qua OCR tiếng Việt có hậu kiểm soát lỗi chính tả. Loại bỏ header, footer, số trang lặp.
* **Cắt đoạn (Chunking):** Cắt theo cấu trúc ngữ nghĩa (Chương $\rightarrow$ Điều $\rightarrow$ Khoản). Nếu điều quá dài, tiếp tục chia nhỏ theo khoản nhưng luôn giữ tiêu đề của Điều ở đầu đoạn text.
* **Metadata gắn kèm:** `doc_id`, `doc_title`, `doc_number`, `article`, `issued_date`, `effective_date`, `status` (`ACTIVE`/`EXPIRED`), `category`, `applies_to`.
* **Embedding & Indexing:** Chuyển đổi văn bản thành vector và đẩy vào Qdrant cùng metadata. Khi tài liệu hết hiệu lực, chỉ cần cập nhật cờ `status = EXPIRED` thay vì xóa vector.

### 5.2 Xử lý và viết lại câu hỏi (Luồng B - Bước 1)
* **Chuẩn hóa & mở rộng từ viết tắt:** Dùng bảng từ điển (BHYT $\rightarrow$ Bảo hiểm y tế, CSDL $\rightarrow$ Cơ sở dữ liệu, CNTT $\rightarrow$ Công nghệ thông tin,...).
* **Ghép ngữ cảnh hội thoại:** Chuyển câu hỏi phụ thuộc ngữ cảnh thành câu hỏi độc lập.
* **Phân loại ý định (Intent Routing):**
  * *Học vụ:* Chuyển tiếp vào pipeline truy xuất.
  * *Dữ liệu cá nhân (điểm, nợ tiền cụ thể):* Hướng dẫn sinh viên truy cập Cổng thông tin đào tạo.
  * *Ngoài phạm vi (chuyện ngoài lề, kết bạn, tán gẫu):* Phản hồi từ chối lịch sự.
  * *Câu hỏi quá mơ hồ:* Hỏi lại để làm rõ phạm vi.

### 5.3 Truy xuất ngữ cảnh (Luồng B - Bước 2)
* **Tìm kiếm lai (Hybrid Search):** Kết hợp Vector Search (ngữ nghĩa) và BM25 (từ khóa chính xác như "N4", "B1", "Điều 15").
* **Lọc Metadata:** Lọc nghiêm ngặt các đoạn có `status = ACTIVE` và phù hợp với khóa/ngành sinh viên đang hỏi.
* **Khớp FAQ chuẩn:** Kiểm tra câu hỏi với bảng FAQ của Admin; nếu độ tương đồng vượt ngưỡng $\ge 0.92$, dùng ngay câu trả lời mẫu mà không cần chạy qua LLM.
* **Ngưỡng chấm điểm (Score Threshold):** Nếu điểm liên quan của các đoạn trích xuất thấp hơn ngưỡng quy định, chuyển ngay sang kịch bản "Không tìm thấy".

### 5.4 Prompting và Kiểm soát ảo giác (Luồng B - Bước 3)
* **Cấu hình tham số LLM:** Đặt `temperature` trong khoảng $0.0 - 0.2$ để câu trả lời bám sát ngữ cảnh, giảm tính sáng tạo tự do.
* **System Prompt:** Bắt buộc AI trích dẫn văn bản, nêu rõ Điều/Khoản; cấm tự suy diễn, cấm tự ý tính toán/làm tròn các con số học phí hoặc thang điểm.
* **Cơ chế từ chối:** Nếu ngữ cảnh cung cấp không chứa thông tin trả lời, mô hình phải xuất ra câu thông báo mặc định hướng dẫn liên hệ phòng Đào tạo.

---

## 6. Thiết kế Cơ sở dữ liệu
Hệ thống sử dụng mô hình lưu trữ kép (Hybrid Storage): PostgreSQL quản lý dữ liệu nghiệp vụ quan hệ và Qdrant quản lý dữ liệu không gian vector.

### 6.1 PostgreSQL
* `users` (`id`, `email`, `password_hash`, `role`, `created_at`, `is_active`)
* `conversations` (`id`, `user_id`, `title`, `created_at`)
* `messages` (`id`, `conversation_id`, `role`, `content`, `status`, `latency_ms`, `created_at`)
* `message_sources` (`id`, `message_id`, `chunk_id`, `score`)
* `feedback` (`id`, `message_id`, `is_helpful`, `reason`, `created_at`)
* `documents` (`id`, `title`, `doc_number`, `category`, `issued_date`, `effective_date`, `status`, `applies_to`, `file_path`, `uploaded_by`)
* `document_versions` (`id`, `document_id`, `version_no`, `file_hash`, `ingest_status`, `ingested_at`)
* `faq_entries` (`id`, `question`, `answer`, `source_document_id`, `is_active`)
* `abbreviations` (`id`, `short_form`, `full_form`)
* `audit_logs` (`id`, `actor_id`, `action`, `target`, `created_at`)

### 6.2 Vector Database (Qdrant Schema)
* **ID:** `chunk_id` (UUID)
* **Vector:** Kích thước tương ứng với mô hình nhúng (ví dụ: 1536 đối với OpenAI, 1024 đối với bge-m3).
* **Payload:** `doc_id`, `version_no`, `text`, `doc_title`, `doc_number`, `article`, `page`, `category`, `applies_to`, `effective_date`, `status`.

---

## 7. Thiết kế API và Luồng xử lý
### 7.1 Luồng xử lý một câu hỏi
1. Web client gửi câu hỏi kèm Access Token qua POST API.
2. Spring Boot xác thực token, kiểm tra Rate Limit, ghi bản ghi câu hỏi vào bảng `messages`.
3. Spring Boot đóng gói câu hỏi cùng 2-3 lượt chat gần nhất rồi gọi sang AI Service (FastAPI).
4. FastAPI thực hiện chuẩn hóa viết tắt, kiểm tra FAQ, thực hiện Hybrid Search trên Qdrant.
5. Nếu tìm thấy ngữ cảnh hợp lệ: FastAPI gọi LLM theo định dạng streaming và chuyển tiếp dữ liệu về Spring Boot.
6. Spring Boot đẩy dữ liệu theo dạng Server-Sent Events (SSE) về Web Client để hiển thị text dạng gõ chữ.
7. Khi streaming kết thúc: Lưu toàn bộ câu trả lời, độ trễ và nguồn trích dẫn vào database.

### 7.2 Danh mục API chính (Backend Spring Boot)
* `POST /api/auth/login`, `/register`, `/refresh`: Xác thực tài khoản.
* `POST /api/conversations`: Tạo phiên trò chuyện mới.
* `GET /api/conversations`: Lấy danh sách lịch sử hội thoại của người dùng.
* `POST /api/conversations/{id}/messages`: Gửi câu hỏi và nhận SSE stream.
* `POST /api/messages/{id}/feedback`: Gửi đánh giá Đúng/Sai.
* `POST /api/admin/documents`: Tải lên tài liệu mới (Multipart).
* `PATCH /api/admin/documents/{id}/status`: Cập nhật trạng thái hiệu lực tài liệu.
* `GET /api/admin/stats/overview`: Thống kê tổng quan lượt hỏi, tỉ lệ phản hồi.
* `CRUD /api/admin/faq`: Quản lý danh mục câu hỏi - trả lời chuẩn.

---

## 8. Thiết kế Giao diện (UI/UX)
* **Trải nghiệm di động làm trung tâm (Mobile-First):** Thiết kế tối ưu cho tỷ lệ màn hình điện thoại; menu lịch sử dạng drawer trượt gọn gàng.
* **Giao diện Chat trực quan:** Hiển thị khối trích dẫn nguồn văn bản rõ ràng phía dưới câu trả lời, có kèm nhãn ngày hiệu lực để sinh viên an tâm.
* **Hỗ trợ gõ lệnh nhanh:** Gợi ý danh sách câu hỏi thường gặp ở màn hình chào mừng.
* **Bảng điều khiển Admin chuyên biệt:** Sử dụng thư viện Ant Design để quản lý bảng biểu tài liệu, bộ lọc trạng thái màu sắc (`PROCESSING` - Vàng, `READY` - Xanh, `EXPIRED` - Xám) và màn hình Playground để cán bộ đào tạo kiểm thử truy xuất ngữ cảnh thực tế.

---

## 9. Bảo mật và Quyền riêng tư
* **Che giấu dữ liệu nhạy cảm (PII Redaction):** Áp dụng Regex lọc và thay thế thông tin cá nhân (CCCD, SĐT, Email, Mã sinh viên) thành chuỗi ký tự ẩn `***` trước khi gửi sang LLM và trước khi ghi log database.
* **Chống Prompt Injection:** Phân tách rõ ràng giữa System Prompt, Context và User Prompt; đặt bộ lọc chặn các lệnh thao túng mô hình (như "Bỏ qua các chỉ dẫn trước đó").
* **Bảo vệ hạ tầng:** Toàn bộ API công khai sử dụng HTTPS, xác thực JWT, cấu hình CORS nghiêm ngặt; AI Service và Vector DB đặt trong mạng nội bộ (Internal Docker Network).

---

## 10. Kế hoạch kiểm thử và Đánh giá hệ thống RAG

### 10.1 Xây dựng tập dữ liệu kiểm thử (Test Dataset)
Xây dựng bộ dữ liệu đối chuẩn gồm 100 câu hỏi Ground Truth dựa trên các câu hỏi thực tế thu được từ khảo sát, chia làm 4 nhóm:
1. **Hỏi trực tiếp (Fact-seeking) - 35 câu:** Thông tin nằm trọn trong một điều khoản (chuẩn đầu ra B1/N4, địa điểm nộp giấy tờ).
2. **Hỏi tổng hợp/suy luận (Multi-hop) - 25 câu:** Cần kết hợp thông tin từ 2 văn bản hoặc 2 điều khoản trở lên (ví dụ: vừa bị cảnh cáo học tập vừa nợ học phí thì xử lý ra sao).
3. **Câu hỏi viết tắt, sai ngữ pháp (Noisy Query) - 20 câu:** Chứa các từ viết tắt, tiếng lóng của sinh viên ("bhyt", "đk môn", "cải thiện điểm").
4. **Câu hỏi ngoài phạm vi / Dữ liệu rác (Adversarial & Out-of-scope) - 20 câu:** Câu hỏi không có trong quy chế hoặc hỏi bí kíp học tập, tán gẫu.

### 10.2 Bộ chỉ số đánh giá chuyên sâu (RAG Metrics)
Sử dụng framework **RAGAS** để tự động hóa quá trình chấm điểm:
* **Faithfulness (Độ trung thực):** Đánh giá xem tất cả các luận điểm trong câu trả lời có được suy ra từ Context đã truy xuất hay không (chống ảo giác). Mục tiêu: $\ge 0.85$.
* **Answer Relevance (Độ liên quan):** Đo lường mức độ khớp giữa câu trả lời và câu hỏi của sinh viên. Mục tiêu: $\ge 0.80$.
* **Context Precision (Độ chuẩn xác của truy xuất):** Tỷ lệ các đoạn văn bản thực sự chứa câu trả lời nằm ở các vị trí xếp hạng đầu tiên. Mục tiêu: $\ge 0.80$.
* **Context Recall (Độ bao phủ của truy xuất):** Tỷ lệ thông tin cần thiết đã được hệ thống tìm kiếm đầy đủ từ tài liệu gốc. Mục tiêu: $\ge 0.85$.

### 10.3 Ma trận thí nghiệm tối ưu hóa
| Thí nghiệm | Cấu hình A (Baseline) | Cấu hình B (Cải tiến) | Mục tiêu kiểm chứng |
| :--- | :--- | :--- | :--- |
| **Kỹ thuật cắt đoạn (Chunking)** | Cắt cố định (500 tokens, overlap 50) | Cắt theo ngữ nghĩa Điều/Khoản văn bản | Đánh giá độ trọn vẹn của ngữ cảnh và Context Recall |
| **Chiến lược tìm kiếm** | Dense Vector Search đơn thuần | Hybrid Search (Dense + BM25) | Đánh giá khả năng tìm chính xác các từ khóa số hiệu, mã chứng chỉ |
| **Mô hình ngôn ngữ lớn** | Google Gemini Flash | OpenAI GPT-4o-mini | So sánh độ trễ (Latency), chi phí và điểm Faithfulness |

### 10.4 Kiểm thử người dùng và Chịu tải (UAT & Performance)
* **Tải đồng thời:** Dùng công cụ k6/JMeter giả lập 100 kết nối đồng thời trong 15 phút, theo dõi tỉ lệ lỗi (Error Rate $< 1\%$) và mức tiêu hao CPU/RAM của server.
* **UAT (User Acceptance Testing):** Cho 10 sinh viên và 2 cán bộ thuộc phòng Đào tạo thao tác trực tiếp trên giao diện thử nghiệm; đo lường tỷ lệ sinh viên hài lòng qua nút đánh giá Đúng/Sai.

---

## 11. Kế hoạch triển khai và Hạ tầng

### 11.1 Kiến trúc triển khai hạ tầng
* **Giao diện Client:** Build tĩnh và lưu trữ trên các nền tảng phân phối biên (Vercel / Cloudflare Pages) nhằm tối ưu tốc độ tải trang cho sinh viên.
* **Hệ thống Server (VPS):** Cấu hình máy chủ ảo Ubuntu (khuyến nghị tối thiểu: 4 vCPU, 8GB RAM).
* **Docker hóa toàn diện (Containerization):** Sử dụng `docker-compose` để điều phối:
  * Container 1: `spring-boot-backend` (Cổng 8080).
  * Container 2: `fastapi-ai-service` (Cổng 8000 nội bộ).
  * Container 3: `qdrant-vector-db` (Cổng 6333 nội bộ).
  * Container 4: `postgresql` (Cổng 5432 nội bộ).
  * Container 5: `nginx-reverse-proxy` (Cổng 80/443 SSL Certbot).

### 11.2 Tiến độ thực hiện (Dự kiến 16 tuần)
* **Tuần 1 - 4:** Thu thập tài liệu học vụ, làm sạch dữ liệu văn bản. Khảo sát sinh viên, hoàn thiện tài liệu phân tích thiết kế. Cấu hình Docker và Database.
* **Tuần 5 - 8:** Xây dựng module AI Service (Python): Parser tài liệu, chunking, tạo vector embedding, thiết kế pipeline tìm kiếm lai. Dựng khung Spring Boot API.
* **Tuần 9 - 12:** Lập trình Frontend React + Web Admin Ant Design. Tích hợp giao tiếp SSE Streaming giữa Backend và Client. Chạy bộ đánh giá RAGAS.
* **Tuần 13 - 14:** Tối ưu hóa prompt, tinh chỉnh ngưỡng score threshold dựa trên lỗi thực tế. Chạy thử nghiệm diện hẹp (UAT).
* **Tuần 15 - 16:** Đóng gói triển khai lên VPS, hoàn thiện báo cáo khoa học và chuẩn bị slide bảo vệ đồ án.

---

## 12. Dự toán chi phí vận hành ước tính
Hệ thống được thiết kế theo tiêu chí tối ưu hóa chi phí cho môi trường giáo dục:

| Khoản mục | Tài nguyên đề xuất | Chi phí ước tính / tháng | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Máy chủ Cloud (VPS)** | VPS DigitalOcean / Hetzner (4 Core, 8GB RAM) | ~ $12 - $15 | Đảm bảo chạy mượt cụm Docker Backend, AI Service và DB |
| **Lưu trữ Frontend** | Cloudflare Pages / Vercel Hobby | $0 (Miễn phí) | Băng thông CDN miễn phí không giới hạn |
| **LLM Inference API** | Gemini Flash / GPT-4o-mini | ~ $3 - $7 | Tính trên lưu lượng ~15.000 câu hỏi/tháng |
| **Vector Embedding API**| `text-embedding-3-small` / mô hình mã nguồn mở | ~ $0.5 - $1 | Chỉ tốn phí khi nạp văn bản mới hoặc cập nhật |
| **Tên miền** | Subdomain trường (`ask.donga.edu.vn`) | $0 (Nội bộ) | Xin cấp từ Trung tâm Thông tin - Thư viện trường |
| **Tổng chi phí** | | **Dưới $25 / tháng** | Rất khả thi để nhà trường hoặc Khoa duy trì lâu dài |

---

## 13. Tổng kết và Hướng phát triển

### 13.1 Tổng kết đề tài
Đề tài giải quyết bài toán tra cứu thông tin học vụ mang tính cấp thiết của sinh viên Đại học Đông Á. Bằng cách phối hợp giữa kỹ thuật RAG tiên tiến và quy trình kiểm duyệt tài liệu từ phòng Đào tạo, hệ thống đã triệt tiêu vấn đề ảo giác của AI, cung cấp nguồn trích dẫn pháp lý rõ ràng, đồng thời tạo ra một quy trình quản trị tài liệu trực quan, dễ dùng cho cán bộ nghiệp vụ.

### 13.2 Hướng phát triển tương lai
* **Tích hợp cổng thông tin sinh viên (SIS Integration):** Nâng cấp hệ thống theo hướng **Agentic RAG / Tool Calling**, cấp quyền cho AI truy vấn API bảo mật để trả lời dữ liệu cá nhân hóa (điểm thi, số tiền công nợ cụ thể của sinh viên sau khi đăng nhập SSO).
* **Mở rộng kênh kết nối:** Tích hợp Webhook kết nối trực tiếp vào Zalo Official Account và Facebook Messenger của nhà trường để sinh viên không cần truy cập web mà vẫn hỏi đáp được.
* **Phát hiện tâm lý người học:** Tích hợp mô hình phân tích cảm xúc (Sentiment Analysis) trong các câu hỏi để tự động phát hiện các sinh viên gặp khó khăn, áp lực học tập hoặc bức xúc thủ tục, từ đó chuyển tiếp cảnh báo đến Cố vấn học tập kịp thời.