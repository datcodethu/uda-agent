donga-rag-system/
├── .github/ # CI/CD workflows (GitHub Actions)
│ └── workflows/
│ ├── deploy-frontend.yml
│ ├── deploy-backend.yml
│ └── deploy-ai-service.yml
├── docker-compose.yml # Khởi chạy toàn bộ hệ thống (Dev / Staging)
├── docker-compose.prod.yml # Cấu hình production
├── .env.example # Mẫu biến môi trường chung
├── README.md # Tài liệu hướng dẫn setup dự án
│
│ # =========================================================================
│ # 1. FRONTEND: Web Chat SV, Web Admin & SDK Nhúng (React + TypeScript)
│ # =========================================================================
├── frontend/
│ ├── package.json
│ ├── tsconfig.json
│ ├── vite.config.ts
│ ├── public/
│ │ ├── favicon.ico
│ │ └── donga-logo.png
│ └── src/
│ ├── assets/ # Ảnh, icons, fonts tĩnh
│ ├── components/ # Các component dùng chung (UI primitives)
│ │ ├── common/ # Button, Input, Modal, LoadingSpin
│ │ └── feedback/ # Nút Đúng/Sai, form lý do đánh giá
│ │
│ │ # Module 1: Web Chat dành cho Sinh viên
│ ├── apps/student-chat/
│ │ ├── components/ # MessageBubble, SourceBadge, SuggestedChips
│ │ ├── hooks/ # useChatStream.ts (xử lý SSE), useSpeechToText.ts
│ │ ├── pages/ # ChatScreen.tsx, HistoryScreen.tsx
│ │ └── styles/
│ │
│ │ # Module 2: Web Quản trị (Admin Đào tạo & Kỹ thuật)
│ ├── apps/admin-portal/
│ │ ├── components/ # DocUploadDropzone, ChunkViewerModal
│ │ ├── pages/
│ │ │ ├── DashboardPage.tsx # Thống kê câu hỏi, tỷ lệ đúng/sai
│ │ │ ├── DocumentManage.tsx # CRUD tài liệu, trigger nạp lại
│ │ │ ├── ReviewFailed.tsx # Rà soát câu AI trả lời "không tìm thấy"
│ │ │ ├── FaqManage.tsx # Quản trị câu trả lời chuẩn
│ │ │ └── PlaygroundPage.tsx # Test prompt & điểm truy xuất
│ │
│ │ # Module 3: WIDGET SDK (Quan trọng: Phục vụ nhúng vào Web trường)
│ ├── widget-sdk/ # Đóng gói thành file `donga-bot.js` độc lập
│ │ ├── index.ts # Entry point tạo bong bóng chat góc màn hình
│ │ └── embed-wrapper.tsx # Iframe hoặc shadow DOM tránh xung đột CSS
│ │
│ ├── services/ # Tầng gọi API Backend (Axios Client)
│ │ ├── api.client.ts # Cấu hình interceptors, gắn JWT token
│ │ ├── auth.service.ts
│ │ ├── chat.service.ts # Quản lý SSE stream
│ │ └── document.service.ts
│ ├── types/ # Định nghĩa TypeScript interfaces (DTO)
│ │ ├── chat.d.ts
│ │ ├── document.d.ts
│ │ └── user.d.ts
│ └── utils/ # Helper format ngày tháng, regex lọc nhạy cảm
│
│ # =========================================================================
│ # 2. BACKEND GATEWAY: Nghiệp vụ, Bảo mật & Tích hợp (Spring Boot)
│ # =========================================================================
├── backend/
│ ├── pom.xml (hoặc build.gradle)
│ ├── Dockerfile
│ └── src/
│ └── main/
│ ├── java/vn/edu/donga/rag/
│ │ ├── RagApplication.java
│ │ │
│ │ ├── config/ # Cấu hình hệ thống
│ │ │ ├── SecurityConfig.java # Spring Security, CORS, JWT Filter
│ │ │ ├── WebClientConfig.java # Cấu hình gọi AI FastAPI qua WebClient
│ │ │ └── RateLimitConfig.java # Chống spam câu hỏi theo IP/User
│ │ │
│ │ │ # Tầng CONTROLLER: Nhận request và phân phối
│ │ ├── controller/
│ │ │ ├── auth/ # Login, Register, Refresh Token
│ │ │ ├── student/ # ChatController (SSE endpoint), HistoryController
│ │ │ ├── admin/ # DocumentAdminController, DashboardController
│ │ │ │
│ │ │ │ # Các Controller phục vụ mở rộng trong tương lai
│ │ │ ├── mobile/ # MobileChatController (Format tối ưu cho App)
│ │ │ └── webhook/ # ZaloWebhookController, MessengerWebhookController
│ │ │
│ │ ├── service/ # Xử lý Logic nghiệp vụ
│ │ │ ├── AuthService.java
│ │ │ ├── ChatSessionService.java # Lưu trữ ngữ cảnh, kiểm tra hạn mức
│ │ │ ├── DocumentService.java # Quản lý metadata, file upload lên server
│ │ │ ├── MaskingService.java # Regex che số CCCD, SĐT, MSSV trước khi lưu
│ │ │ └── client/
│ │ │ └── AiServiceClient.java # Client giao tiếp HTTP/SSE với Python AI
│ │ │
│ │ ├── repository/ # Spring Data JPA interfaces
│ │ │ ├── UserRepository.java
│ │ │ ├── ConversationRepository.java
│ │ │ ├── MessageRepository.java
│ │ │ ├── DocumentRepository.java
│ │ │ └── FaqRepository.java
│ │ │
│ │ ├── entity/ # JPA Entities map với PostgreSQL
│ │ │ ├── User.java
│ │ │ ├── Conversation.java
│ │ │ ├── Message.java
│ │ │ ├── MessageSource.java
│ │ │ ├── Document.java
│ │ │ └── FaqEntry.java
│ │ │
│ │ ├── dto/ # Data Transfer Objects (Request/Response)
│ │ │ ├── request/ # ChatQueryRequest, FeedbackRequest, DocUploadRequest
│ │ │ └── response/ # ChatStreamChunkResponse, SourceDetailResponse
│ │ │
│ │ └── security/ # JWT Token Provider, UserDetailsService
│ │
│ └── resources/
│ ├── application.yml # Cấu hình DB, Port, Secret Keys
│ ├── application-prod.yml
│ └── db/migration/ # Flyway SQL Scripts định nghĩa bảng ban đầu
│ ├── V1**init_schema.sql
│ └── V2**add_faq_and_abbreviations.sql
│
│ # =========================================================================
│ # 3. AI SERVICE: Core RAG Pipeline & Evaluation (Python / FastAPI)
│ # =========================================================================
├── ai-service/
│ ├── requirements.txt
│ ├── Dockerfile
│ ├── .env.example # Chứa OPENAI_API_KEY, GEMINI_API_KEY, QDRANT_URL
│ │
│ ├── app/
│ │ ├── main.py # Entry point FastAPI, đăng ký routers
│ │ ├── core/ # Cấu hình AI engine
│ │ │ ├── config.py # Load biến môi trường, model hyperparameters
│ │ │ └── prompts.py # System prompt, prompt rewriting, prompt chống ảo giác
│ │ │
│ │ ├── api/ # API routes nội bộ (Chỉ mở cho Spring Boot gọi)
│ │ │ ├── v1/
│ │ │ │ ├── ingest_routes.py # Nhận file/text -> cắt đoạn -> Vector DB
│ │ │ │ ├── query_routes.py # Nhận query -> Rewrite -> Retrieve -> Stream LLM
│ │ │ │ └── health_routes.py
│ │ │
│ │ ├── pipeline/ # Cốt lõi của RAG Logic
│ │ │ ├── preprocessor/ # Xử lý văn bản đầu vào
│ │ │ │ ├── pdf_loader.py # Đọc PDF văn bản chuẩn & OCR với PDF scan
│ │ │ │ ├── structural_chunker.py # Cắt đoạn theo Chương/Điều/Khoản
│ │ │ │ └── cleaner.py # Lọc bỏ header, footer, số trang thừa
│ │ │ │
│ │ │ ├── query_transformation/ # Xử lý câu hỏi của SV
│ │ │ │ ├── abbreviation_mapper.py # Giải mã từ viết tắt (BHYT, IT, N4,...)
│ │ │ │ ├── intent_classifier.py # Phân loại: Học vụ / Cần tra cứu cá nhân / Ngoài luồng
│ │ │ │ └── query_rewriter.py # Ghép lịch sử để tạo câu hỏi độc lập
│ │ │ │
│ │ │ ├── retrieval/ # Tìm kiếm dữ liệu
│ │ │ │ ├── dense_search.py # Tìm kiếm Vector (Qdrant client)
│ │ │ │ ├── bm25_search.py # Tìm kiếm từ khóa chính xác
│ │ │ │ └── hybrid_retriever.py # Kết hợp Vector + BM25 + Lọc Metadata còn hiệu lực
│ │ │ │
│ │ │ └── generator/ # Sinh câu trả lời
│ │ │ ├── llm_adapter.py # Giao diện chuẩn gọi OpenAI / Gemini / Local LLM
│ │ │ └── stream_handler.py # Xử lý SSE generator trả token về Spring Boot
│ │ │
│ │ └── schemas/ # Pydantic Schemas validate dữ liệu vào/ra
│ │ ├── query_schema.py
│ │ └── ingest_schema.py
│ │
│ │ # Phần nghiên cứu khoa học: Đánh giá mô hình độc lập
│ └── evaluation/
│ ├── test_datasets/ # File JSON/CSV chứa 100 câu hỏi test (Ground Truth)
│ │ ├── academic_regulations.json
│ │ └── adversarial_test.json # Câu hỏi lừa, câu ngoài phạm vi
│ ├── ragas_evaluator.py # Chạy test tự động: Faithfulness, Precision, Recall
│ └── benchmarks_result/ # Lưu log kết quả các lần thí nghiệm Chunk size/LLM
│
│ # =========================================================================
│ # 4. KHO VĂN BẢN GỐC & DỮ LIỆU ĐỊNH NGHĨA (Storage & Seed Data)
│ # =========================================================================
└── data/
├── raw_documents/ # Nơi lưu file PDF quy chế thực tế phòng Đào tạo cấp
│ ├── quy_che_dao_tao_2025.pdf
│ └── chuan_dau_ra_cntt.pdf
└── seed/ # Dữ liệu khởi tạo ban đầu cho Postgres
├── abbreviations_seed.json # Bảng từ viết tắt ban đầu
└── admin_init.sql # Tài khoản super-admin khởi tạo

Điểm nhấn giải quyết bài toán tích hợp Web trường & Mobile App sau này:
Thư mục frontend/src/widget-sdk/:

Đây là một build target riêng biệt. Khi chạy lệnh đóng gói, nó xuất ra một file script duy nhất (ví dụ: donga-bot.js).

Đội IT quản trị website chính của Đại học Đông Á chỉ cần dán một dòng thẻ <script src="[https://rag.donga.edu.vn/donga-bot.js](https://rag.donga.edu.vn/donga-bot.js)"></script> vào trang web trường là cửa sổ chat tự động xuất hiện ở góc phải màn hình mà không cần can thiệp vào mã nguồn web của trường.

Thư mục backend/.../controller/mobile/:

Khi nhóm phát triển Mobile App (ví dụ dùng Flutter), app sẽ không gọi trực tiếp vào Python AI mà gọi qua các API được thiết kế riêng ở cụm controller này (tối ưu hóa payload JSON gọn hơn, hỗ trợ push notification khi có cập nhật quy chế mới).

Thư mục backend/.../controller/webhook/:

Sau này tích hợp Zalo Official Account hoặc Messenger, webhook từ Zalo/Meta sẽ bắn trực tiếp vào đây. Spring Boot đóng vai trò xác thực chữ ký bảo mật, parse tin nhắn từ định dạng của Zalo/Facebook thành định dạng chuẩn rồi chuyển cho AI Service xử lý.

Phân tách hoàn toàn Spring Boot và AI Service:

Spring Boot gánh toàn bộ tải từ các kênh (Web, App, Zalo), bảo mật dữ liệu, rate limit, kiểm tra quyền truy cập.

AI Service thuần túy là một "công cụ tính toán" (pure microservice), tập trung tối đa tài nguyên RAM/CPU cho việc tính toán embedding và stream LLM. Khi trường cần đổi sang LLM nội bộ hoặc nâng cấp vector DB, code của Web và Mobile App hoàn toàn không bị ảnh hưởng.
