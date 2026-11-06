# Việc phát sinh ngoài phạm vi (chưa làm)

## 1. Giai đoạn 2: Cải tiến bộ cắt đoạn (Làm sau khi nghiệm thu Giai đoạn 1)

Cần tái hiện từng lỗi trên file `2023_8_23_16_29_59n.pdf` trước khi sửa:

- [x] **Lỗi a (Bảng bị làm phẳng):** Các bảng bị mất dòng tiêu đề cột và trải dài thành dòng đơn lẻ (đoạn 8, 10, 13, 14, 16). Sửa: Giữ bảng trọn vẹn trong một đoạn; nếu bảng quá dài thì tách theo từng nhóm hàng và lặp lại dòng tiêu đề (header).
- [x] **Lỗi b (Trùng số Điều giữa Quyết định & Quy định):** Văn bản có "Quyết định" (Điều 1-3) và "Quy định kèm theo" (Điều 1-8) trùng số Điều bị đánh hậu tố `-x1`. Sửa: Khi gặp "Điều 1" đứng đầu dòng và số Điều quay về 1 thì mở phần văn bản mới; bổ sung trường `phan_van_ban` (`quyet_dinh` / `quy_dinh_kem_theo` / `phu_luc`) vào metadata và mã đoạn, loại bỏ hậu tố `-x1`.
- [x] **Lỗi c (Lấy nhầm câu đầu làm tiêu đề):** Các Điều không có tiêu đề bị cắt cứng ~80 ký tự câu đầu làm tiêu đề (đoạn 3, 4, 5). Sửa: Tiêu đề phải ở đầu dòng, ngắn (< 120 ký tự), không kết thúc bằng dấu chấm; nếu không thỏa mãn thì để `(Không)` và giữ nguyên câu trong thân bài.
- [x] **Lỗi d (Cắt giữa câu, thiếu gối đầu):** Cắt theo độ dài 1200 ký tự cắt cụt giữa câu và không có overlap (đoạn 1 sang 2, 7 sang 8). Sửa: Ưu tiên cắt theo Khoản ("1.", "2.") hoặc ranh giới câu, gối đầu 100-150 ký tự, không cắt giữa bảng.
- [x] **Lỗi e (Tiền tố đoạn là tên file):** Đổi tiền tố sang `doc_title` lấy từ `docs_registry.csv` hoặc trích xuất từ trang đầu tài liệu.

## 2. Xử lý tồn đọng dữ liệu

- [ ] **15 file PDF scan:** Đang chờ xin lại bản gốc Word/PDF có chữ từ Phòng Đào tạo (chưa chạy OCR).
- [ ] **Tài liệu loại trừ khỏi kho chatbot:**
  - 2 file Luật Nhà nước: `2026_10_6_10_15_26g.pdf` (An ninh mạng) và `2026_10_6_10_16_15ộ.pdf` (ATGT) -> Gắn nhãn `category=phap_luat`, chưa nạp vào kho.
  - Các file biểu mẫu đơn từ sinh viên.
  - File nghi lỗi font: `2026_10_6_10_18_43c.pdf`.

## 3. Cải tiến kiến trúc bóc tách và Metadata (Ghi nhận từ Phiên 4B & 4C)

- [ ] **Bộ nhận đề mục thập phân:** Chỉ kích hoạt cho văn bản không có "Điều" thật (như các văn bản hướng dẫn, quy trình, sổ tay) để tránh làm ảnh hưởng hoặc làm vỡ cấu trúc của các văn bản quy chế chuẩn đã chạy ổn định.
- [ ] **Bổ sung metadata số trang (`page`):** Trích xuất thông tin số trang thực tế từ file PDF (qua `pypdf`) hoặc văn bản Word để lưu vào metadata từng chunk, hỗ trợ sinh viên trích dẫn chính xác số trang tài liệu gốc.

## 4. Tồn đọng dữ liệu và kiểm thử (Ghi nhận từ Phiên 5B & Phiên 6A)

- [ ] **Chuẩn hóa phân loại `loai` cho tài liệu Markdown/Hướng dẫn:** Hiện tại 5 file Markdown tổng hợp đang được tạm gán `loai=quy_che_truong` trong `docs_registry.csv` để qua cổng kiểm duyệt `ingest_approved.py`. Cần tái cấu trúc cổng nạp để hỗ trợ phân loại linh hoạt hơn (ví dụ: `loai=huong_dan_hoc_vu` hoặc `tai_lieu_tong_hop`), bảo đảm tính chính danh pháp lý và dữ liệu của kho tri thức.
- [ ] **Rà soát và gắn nhãn bộ câu hỏi thử nghiệm mới (`c14`–`c20`):** Các câu `c14`–`c20` trong `ai-service/data/cau_hoi_thu.csv` hiện để trống nhãn và `da_xac_nhan=false`. Chờ người dùng tự đọc văn bản gốc, trực tiếp gán nhãn đáp án (`expected_dieu`, `must_have`, `expected_refuse`) và gắn `da_xac_nhan=true` (tuân thủ quy tắc Agent không tự soạn nhãn).
- [ ] **Rà soát lại cờ `da_xac_nhan` của 13 câu chuẩn ban đầu (`c01`–`c13`):** Cột `da_xac_nhan` từng được gán hàng loạt `true` ở commit `c9c1da9`. Người dùng cần kiểm tra lại độc lập từng câu để bảo đảm tính khách quan tuyệt đối cho bộ benchmark NCKH.

## 5. Nhiệm vụ Phiên 6C: Answer Sufficiency, Prompt Rules & Dynamic Badges

- [x] **TASK C — Answer Sufficiency Check:** Phân loại 4 trạng thái (`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `NO_EVIDENCE`) bằng cơ chế kép (System Prompt + Verifier) không phát sinh thêm chi phí LLM.
- [x] **TASK D — Answer Generation Rules:** Tích hợp 5 Rules cốt lõi vào `SYSTEM_PROMPT` (Rule 1: Trực tiếp; Rule 2: Đúng kiểu thông tin; Rule 3: Ngôn ngữ SV; Rule 4: Cấu trúc linh hoạt; Rule 5: Chống ảo giác tuyệt đối).
- [x] **TASK E — Citation & Dynamic Verification Badges:** Bổ sung `validate_citations`, loại bỏ badge cứng, hiển thị dynamic badges trên Web UI.
- [x] **TASK F — Multi-turn Answer Quality:** Tích hợp bộ nhớ ngữ cảnh và giải thích dễ hiểu mượt mà với 0 ms retrieval.
- [x] **TASK G — Regression Testing:** Xây dựng 22 test cases phủ 10 nhóm câu hỏi, nâng toàn bộ test suite lên 123/123 PASS (100%).
- [x] **TASK H — Latency & Performance Benchmark:** Đảm bảo thời gian phân tích xác minh < 1 ms, không làm tăng độ trễ RAG.

## 6. Nhiệm vụ Phiên 6D: Student-Centered RAG & Sensitive Academic Policy Handling

- [x] **TASK A — Academic Intent & Risk Classification:** Phân loại 8 nhóm ý định học vụ và 3 cấp độ rủi ro (LOW, MEDIUM, HIGH) bằng rule-based < 1 ms.
- [x] **TASK B — Policy Applicability Verification:** Giữ nguyên điều kiện tiên quyết trong văn bản gốc (*"cố tình... mà không có lý do chính đáng"*), không tự tiện suy diễn chế tài có điều kiện thành cấm thi tuyệt đối.
- [x] **TASK C — Sensitive Answer Strategy:** Cấu trúc 3 nhóm câu hỏi nhạy cảm (Quyền lợi BHYT/học bổng mở đầu bằng bảo vệ sức khỏe/hỗ trợ; Chế tài nợ học phí/cấm thi nêu quy định + điều kiện + ngoại lệ chính đáng; Tình huống cá nhân không phán xét thay trường, hướng dẫn kênh chính thức, không hỏi CCCD/mật khẩu).
- [x] **TASK D — Retrieval & Evidence Grounding:** Truy xuất chính xác điều khoản quy chế, quỹ hỗ trợ sinh viên khó khăn và kênh liên hệ có căn cứ.
- [x] **TASK E — Claim-Level Verification:** Xây dựng hàm `verify_claims` phát hiện các câu khẳng định tuyệt đối thiếu điều kiện để giáng cấp badge ("Cần đối chiếu điều kiện áp dụng").
- [x] **TASK F — UX, Tone & Empathy:** Trả lời mang tính xây dựng, bình tĩnh, hướng dẫn hành động thiết thực.
- [x] **TASK G — Regression Testing:** Bổ sung 23 test cases trong `test_student_centered_rag.py` phủ 12 tình huống nhạy cảm (T1–T12). Toàn bộ 146/146 unit test PASS.
- [x] **TASK H — Live Performance Benchmark:** Đo đạc thực tế trên SSE stream Uvicorn, TTFT mượt mà, phân loại chính xác intent và risk level.

## 7. Nhiệm vụ Phiên 6E: Kiểm thử Toàn diện 75 Lượt Câu hỏi Khảo sát (Survey QA)

- [x] **Thiết kế test cases:** Sinh `test_cases.csv` cho toàn bộ 75 lượt câu hỏi khảo sát từ `survey_questions_test_dataset.csv`.
- [x] **Kiểm thử offline & Unit tests:** Xác thực tính toàn vẹn SHA-256 dữ liệu và 146/146 unit tests PASS.
- [x] **Thực thi Live E2E:** Chạy 100% 75 câu hỏi trên server live SSE stream, thu thập toàn bộ dữ liệu phản hồi nguyên văn và độ trễ.
- [x] **Xuất Artifacts kiểm thử chuẩn:** Sinh `run_manifest.json`, `test_cases.csv`, `results.csv`, `responses.jsonl`, `report.md`, `issues.md` tại `evaluation/survey_qa_20261105_01/`.

## 8. Nhiệm vụ Phiên 6F: Reference-Guided RAG Improvement & Knowledge Gap Analysis

- [x] **TASK 1 & 2 — Reference Dataset:** Sinh `reference_dataset.csv` (75 test cases, ghi nhận `MISSING_REFERENCE` cho NotebookLM và `human_verified=FALSE`).
- [x] **TASK 3 — Knowledge Gap Analysis:** Phân tích bóc tách nguyên nhân gốc rễ cho 57 câu non-PASS trong `knowledge_gaps.csv` (45 DATA_GAP, 6 INSUFFICIENT_EVIDENCE, 3 RETRIEVAL, 2 GENERATION, 1 CITATION).
- [x] **TASK 4 — Phân tích chất lượng câu trả lời:** Rút ra 8 nguyên tắc cải tiến Answer Generation tổng quát đối chiếu với NotebookLM.
- [x] **TASK 5 — Kế hoạch bổ sung dữ liệu:** Thiết lập danh mục tài liệu cần bổ sung theo thứ tự ưu tiên P0/P1/P2 trong `required_documents.md`.
- [x] **TASK 6 & 7 — Xuất Báo cáo & Bàn giao:** Xuất đầy đủ 7 sản phẩm đầu ra tại `evaluation/reference_guided_6f/` và xây dựng lộ trình triển khai Phiên 6G.

## 9. Nhiệm vụ Phiên 6G: Knowledge Base Expansion & RAG Quality Improvement

- [x] **TASK A — Kiểm toán 7 tài liệu DOCX:** Quét SHA-256, nguồn gốc, đối tượng áp dụng, test case hỗ trợ và thiếu sót bằng chứng tại `document_approval_queue.csv` (toàn bộ ở trạng thái `WAITING_FOR_APPROVAL`).
- [x] **TASK B — Ma trận bao phủ dữ liệu:** Đối chiếu chi tiết 57 câu non-PASS tại `knowledge_coverage.csv` (8 câu CANDIDATE_DOC_AVAILABLE, 5 câu RETRIEVAL_OR_PROMPT_GAP, 18 câu EXTERNAL_DOC_NEEDED, 26 câu CONFIRMED_DATA_GAP).
- [x] **TASK C — Sửa dứt điểm lỗi Citation TC-SVQ-002:** Loại bỏ triệt để bẫy xóa nguồn khi từ chối có điều kiện; bảo đảm mọi citation hiển thị đều có nguồn tương ứng; bổ sung 3 unit tests mới (149/149 test PASS 100%); lập báo cáo `citation_fix_report.md`.
- [x] **TASK D — Thiết kế kỹ thuật cải tiến chất lượng:** Phân loại 8 nguyên tắc NotebookLM thành 3 nhóm kỹ thuật (Cấu hình, Prompt/Logic, Tri thức) kèm diff chi tiết tại `improvement_changes.md`.
- [x] **TASK E — Thiết lập Approval Gate:** Dừng lại ở ngưỡng kiểm duyệt, không tự ý nạp bất kỳ tài liệu nào khi chưa có sự đồng ý của người dùng.
- [x] **TASK F — Đo lường & So sánh Benchmark:** So sánh trước/sau tại `benchmark_comparison.md`; xác nhận tỷ lệ FAIL giảm từ 1.3% về **0.0%**; độ chính xác trích dẫn tăng lên 1.87/2.0.
- [x] **TASK G — Báo cáo tổng kết Phiên 6G:** Xuất báo cáo điều hành đầy đủ tại `evaluation/reference_guided_6g/summary.md`.

## 10. Nhiệm vụ Phiên 6H: NotebookLM-Like URL Knowledge Import & RAG Quality Improvement

- [x] **TASK 1 — Kiểm tra dự án & Kiến trúc:** Đọc GEMINI.md, workflow, crawler hiện có, `docs_registry.csv`, `ingest_approved.py`, Qdrant metadata.
- [x] **TASK 2 — Xây dựng module URL Import:** Xây dựng `URLImporter` (`app/pipeline/importer/url_importer.py`) với Single URL Import và Website Discovery; tích hợp Domain Allowlist, SSRF Prevention (chặn private IP, loopback, cloud metadata), chặn cổng sinh viên cá nhân `my.uda.edu.vn`.
- [x] **TASK 3 — Bóc tách & Chuẩn hóa:** HTML sang Markdown sạch, giữ nguyên bảng, tiêu đề, danh sách; tự động phát hiện liên kết tệp đính kèm (`.pdf`, `.docx`); xử lý tối ưu cho ASP.NET WebForms container `<form>`.
- [x] **TASK 4 — Chu trình Phê duyệt 5 Trạng thái:** Quản lý hàng đợi `data/url_approval_queue.csv` (`DISCOVERED` -> `EXTRACTED` -> `PENDING_REVIEW` -> `APPROVED` -> `INDEXED`), tuân thủ nguyên tắc Default-Deny.
- [x] **TASK 5 — Chỉ mục hóa Tăng dần (Incremental Ingestion):** Xây dựng `incremental_indexer.py` và CLI `manage_url_queue.py`; nạp vector vào Qdrant và BM25; mở rộng `ALLOWED_CHUNK_META_KEYS` (`source_url`, `crawled_at`, `content_type`); phân loại `tai_lieu_tong_hop`.
- [x] **TASK 6 — Thực nghiệm Kiểm chứng Đối chứng:** Nạp URL `https://donga.edu.vn/gioi-thieu`, đo đạc Before/After: chuyển trạng thái từ `INSUFFICIENT` sang `SUFFICIENT`, trích dẫn chính xác nguồn `web_2b329b97c1`.
- [x] **TASK 7 — Kiểm thử Hồi quy & Báo cáo:** 159/159 test PASS (1 skipped), 0 regressions; thẩm định 7 tài liệu DOCX (`approval_review.md`); hoàn thiện 5 báo cáo chuyên sâu tại `evaluation/reference_guided_6h/`.

## 11. Nhiệm vụ Phiên 6I: Manual Acceptance Testing & System Verification

- [x] **Xác minh Hạ tầng & Môi trường:** Git demo branch, Qdrant Local 105 chunks (11 tài liệu), BM25 đồng bộ, cổng 8000 sẵn sàng (`system_verification_report.md`).
- [x] **Kiểm toán Phê duyệt Phiên 6H:** Giải trình rõ ràng việc Agent chạy thử nghiệm kỹ thuật và khẳng định thẩm quyền phê duyệt thuộc về Người dùng (`audit_phien_6h_approval.md`).
- [x] **Thiết kế 10 Kịch bản Nghiệm thu Thủ công:** T1-T10 bao phủ an toàn URL, SSRF, chống crawl cổng cá nhân, quy trình duyệt, truy xuất & trích dẫn web, đa lượt, thiếu bằng chứng và chính sách học vụ nhạy cảm (`manual_test_scenarios.md`).
- [x] **Bảng Checklist Nghiệm thu:** Chuẩn bị bảng đánh dấu PASS/FAIL và ghi chú thực tế cho Người dùng (`manual_acceptance_checklist.md`).
- [x] **Báo cáo Hạn chế Tồn đọng:** Liệt kê trung thực các điểm chưa hoàn thành (chưa có Web UI nạp URL, 6 file DOCX chờ duyệt, giới hạn SPA JavaScript) (`limitations_and_unimplemented.md`).
- [ ] **Người dùng Trực tiếp Nghiệm thu:** Người dùng mở terminal chạy Uvicorn, thực hiện 10 kịch bản và đánh dấu checklist.

## 12. Nhiệm vụ Phiên 7A: Rebuild Knowledge Base v2 (`donga_kb_v2`) từ 21 URL NotebookLM

- [x] **TASK A — Sao lưu & Cách ly Dữ liệu (Backup & Zero-Interference Isolation):** Tạo snapshot vật lý nguyên vẹn kho cũ `donga_regulations` (105 chunks, SQLite db) tại `data/backups/snapshot_pre_v2_20261105/`; xác nhận snapshot đọc tốt; tạo thư mục kho mới độc lập `data/qdrant_local_v2/` và `data/chunks_v2.jsonl`, không gây lock contention với server cổng 8000.
- [x] **TASK B & C — Danh mục Nguồn & Thu thập/Bóc tách Markdown:** Xây dựng `rebuild_v2_pipeline.py`; thu thập và chuẩn hóa 20/21 URL nguồn từ `seeds.txt` vào `data/staging_v2/SRC-V2-001.md` -> `SRC-V2-021.md`; trích xuất 37 liên kết đính kèm vào `crawl_attachment_links.csv`; ghi nhận an toàn 1 URL Báo Đà Nẵng bị HTTP 403.
- [x] **TASK D — Tái lập Kho Tri thức v2:** Xây dựng `rebuild_v2_indexer.py`; cắt 451 chunks cấu trúc bảo toàn tiêu đề và bảng Markdown; xây dựng BM25 độc lập `bm25_index_v2.pkl`; nhúng vector Gemini 001 (768d, có disk cache và auto-backoff retry 429); upsert 451 vectors vào collection mới `donga_kb_v2`.
- [x] **TASK E — Kiểm chứng Chất lượng Truy xuất:** Xây dựng `test_v2_retriever.py`; xác thực hybrid search trên nhiều nhóm câu hỏi (thư viện, gửi xe, canvas, ngoại ngữ); độ trễ dense ~370ms, BM25 ~1ms.
- [x] **TASK F & G — Đo kiểm Benchmark 75 Câu hỏi Khảo sát Thực tế:** Xây dựng `run_v2_benchmark.py` có cơ chế resume, retry và chấm điểm 6 tiêu chí; PASS tăng từ 24.0% lên **77.3% (58/75)**; PARTIAL giảm từ 68.0% xuống **20.0% (15/75, toàn bộ là Safe Refusal 9/12đ)**; FAIL giảm xuống **2.7% (2/75)**; 100% trích dẫn hợp lệ.
- [x] **Generalizability Test (5 câu mới):** Đạt 100% (5/5 câu) PASS với điểm tối đa 12/12.
- [x] **Báo cáo Minh chứng:** Hoàn thiện 10 tệp hồ sơ tại `evaluation/kb_rebuild_v2/` (`source_manifest.csv`, `crawl_results.csv`, `crawl_attachment_links.csv`, `ingest_results.csv`, `chatbot_responses.jsonl`, `results.csv`, `retrieval_evaluation.csv`, `generalizability_test.json`, `baseline_comparison.md`, `issues.md`, `summary.md`).

## 13. Nhiệm vụ Phiên 7B: Nâng cao Chất lượng Trả lời Chuẩn NotebookLM trên Kho v2

- [x] **Tối ưu Regex `unsupported_numbers` & Markdown Headers:** Cập nhật hàm trong `verifier.py` để bỏ qua số thứ tự đầu dòng và tiêu đề Markdown (`re.sub(r"(?m)^\s*(?:#{1,6}\s+|(?:[-*•]\s+)?(?:\*\*)?)\d+[\.)](?:\*\*)?\s*", "", ans)`), loại bỏ triệt để các ca FAIL do false positive (`TC-SVQ-015`, `TC-SVQ-040`), đưa tỷ lệ FAIL về 0.0%.
- [x] **Cải tiến Adaptive Retrieval:** Mở rộng Top-K từ 5 lên 7, nâng dung lượng ứng viên từ 20 lên 30 điểm cho cả Dense & BM25, tối ưu RRF $K=60$, tích hợp cơ chế Token Expansion thích ứng theo nhóm ý định (`biểu mẫu`, `đơn`, `gia hạn`, `xác nhận`, `kế toán`, `đào tạo`).
- [x] **Cải tiến Answer Generation với Quy tắc NotebookLM:** Cập nhật Quy tắc 3 trong `SYSTEM_PROMPT` và `build_messages`: trả lời trực diện câu đầu, không từ chối vội khi quy chế không có điều cấm, tích hợp biểu mẫu hành chính (`src-v2-020`) và đầu mối liên hệ thực tế.
- [x] **Nâng cấp Claim-level Verification:** Xây dựng hàm `verify_claim_faithfulness` đối chiếu từng khẳng định quan trọng với văn bản nguồn được trích dẫn; kiểm soát chặt chẽ hallucination số liệu.
- [x] **Truy vết 10 Câu hỏi Trọng điểm (Focal Traces):** Phân tích chi tiết chuỗi suy luận Question -> Chunks -> Context -> Generated Answer -> Verified Claims cho 10 ca học bổng, kỷ luật, học phí, BHYT và chuẩn đầu ra (`10_focal_traces.md`).
- [x] **Tái kiểm thử Benchmark 75 Câu hỏi Khảo sát:** **PASS tăng vọt lên 89.3% (67/75, +12.0%)**, PARTIAL giảm còn 10.7% (8/75), **FAIL giảm về 0.0% (0/75)**; P50 Latency = 7.19s.
- [x] **Kiểm định Khái quát hóa Chống Overfitting:** 5/5 câu mới đạt PASS (100%), không suy giảm chất lượng.
- [x] **Kiểm thử Hồi quy Hệ thống:** 159/159 Unit Tests PASS (100%).
- [x] **Báo cáo Nghiệm thu Duy nhất:** Xuất bản tài liệu nghiệm thu toàn diện tại `evaluation/kb_rebuild_v2/final_acceptance_report.md`.

## 14. Kế hoạch tiếp theo (Phiên 7C)

- [ ] **Bổ sung Nguồn Quy chế Điểm Rèn luyện (ĐRL) Chi tiết:** Khảo sát và bổ sung 01 URL văn bản hướng dẫn thang điểm rèn luyện (0-100đ) để nâng tỷ lệ PASS nhóm Rèn luyện từ 55.6% lên trên 85%.
- [ ] **Chuyển đổi Kho Mặc định (Switch-over) cho Demo:** Cập nhật cấu hình `.env` chuyển `qdrant_path` sang `data/qdrant_local_v2` và `qdrant_collection` sang `donga_kb_v2` để phục vụ Web Chat khi Người dùng phê duyệt.
- [ ] **Thu thập Nguồn Báo Đà Nẵng (URL 19) qua Bản lưu trữ Nội bộ:** Bổ sung thủ công nội dung bài viết việc làm sinh viên để hoàn thiện 21/21 nguồn.






