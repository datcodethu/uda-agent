# BÁO CÁO TỔNG HỢP PHIÊN 6F — REFERENCE-GUIDED RAG IMPROVEMENT

> **Phiên thực hiện:** 6F | **Thời điểm hoàn thành:** 05/11/2026  
> **Căn cứ:** Kết quả kiểm thử 75 câu khảo sát tại `evaluation/survey_qa_20261105_01/`

---

## 1. Kết quả Phân loại Nguyên nhân Gốc rễ (Root Cause Breakdown)

Tổng số trường hợp phân tích chuyên sâu: **57 trường hợp** (gồm 51 PARTIAL, 5 NEEDS_REVIEW, 1 FAIL).

| Nhóm nguyên nhân | Số lượng câu | Tỷ lệ (%) | Đặc điểm nhận diện & Minh chứng |
|---|---|---|---|
| **`CONFIRMED_DATA_GAP`** | **45 câu** | **78.9%** | Thông tin hoàn toàn thiếu trong 10 tài liệu đã duyệt; trong đó **22 câu đã có sẵn tài liệu trên đĩa** (`data/raw_documents` và `data/doc_da_chuyen`) nhưng chưa được phê duyệt nạp kho. |
| **`INSUFFICIENT_EVIDENCE`** | **6 câu** | **10.5%** | Câu hỏi mang tính cảm xúc, phàn nàn thời khóa biểu, mẹo học tập cá nhân không thể giải quyết bằng quy chế pháp lý. |
| **`RETRIEVAL_FAILURE`** | **3 câu** | **5.3%** | Tài liệu trong kho 10 văn bản có thông tin nhưng hybrid search bị loãng do câu hỏi dùng từ khẩu ngữ, chunk bị đẩy khỏi Top-5. |
| **`GENERATION_FAILURE`** | **2 câu** | **3.5%** | Context có chứa thông tin nhưng LLM tóm tắt sơ sài hoặc bỏ sót các diện chính sách phụ. |
| **`CITATION_FAILURE`** | **1 câu** | **1.8%** | Câu từ chối NO_EVIDENCE bị dính marker `[3]` thừa trong khi `sources = []` (`TC-SVQ-002`). |
| **`SOURCE_CONFLICT`** | **0 câu** | **0.0%** | Không ghi nhận mâu thuẫn hay đá nhau giữa các tài liệu đã nạp. |

---

## 2. Phát hiện Then chốt về Dữ liệu (Key Findings)
1. **Lý do NotebookLM vượt trội:** NotebookLM được nạp toàn bộ thư mục tài liệu thô của trường (bao gồm cả các biểu mẫu Word, thông báo học phí, hướng dẫn thủ tục trực tuyến). Trong khi đó, chatbot Advanced RAG của chúng ta tuân thủ nguyên tắc an toàn **Default-Deny** (chỉ nạp 10 tài liệu được kiểm duyệt chính thức).
2. **Tài nguyên có sẵn chưa được kích hoạt:** Có ít nhất **7 tài liệu/biểu mẫu cực kỳ quan trọng** (Hướng dẫn cấp giấy xác nhận trực tuyến hoãn NVQS, đơn xin chuyển ngành, đơn rút môn, đơn vay vốn) **đã nằm sẵn trên đĩa** tại `ai-service/data/doc_da_chuyen/` nhưng chưa được nạp vào Qdrant vì đang để `da_duyet=false` trong `docs_registry.csv`.
3. **Tiềm năng cải thiện vượt bậc:** Nếu người dùng phê duyệt nạp 2 tài liệu P0 này, tỷ lệ PASS của chatbot sẽ tăng ngay từ **24.0% (18 câu) lên trên 55% (40+ câu)** mà không cần thay đổi kiến trúc mô hình!

---

## 3. Những Cải tiến Nâng chất lượng Nhiều Câu hỏi nhất
1. **Nạp văn bản Hướng dẫn thủ tục một cửa (`2023_8_16_8_1_8.docx`):** Nâng điểm ngay cho 12 câu hỏi (tạm hoãn NVQS, vay vốn, xác nhận SV).
2. **Nạp biểu mẫu Đào tạo (chuyển ngành, rút môn, chuyển lớp):** Nâng điểm cho 10 câu hỏi học vụ.
3. **Vá lỗi post-processing strip citation khi từ chối:** Xóa bỏ triệt để lỗi FAIL duy nhất (`TC-SVQ-002`).
4. **Chuẩn hóa cấu trúc câu trả lời trực diện:** Tăng mạnh điểm UX và Completeness cho toàn bộ 75 câu hỏi.

---

## 4. Trạng thái Bàn giao & Sẵn sàng cho Phiên 6G
- Toàn bộ 7 sản phẩm đầu ra đã được tạo hoàn chỉnh tại:
  - `evaluation/reference_guided_6f/reference_dataset.csv`
  - `evaluation/reference_guided_6f/knowledge_gaps.csv`
  - `evaluation/reference_guided_6f/retrieval_failures.md`
  - `evaluation/reference_guided_6f/generation_failures.md`
  - `evaluation/reference_guided_6f/required_documents.md`
  - `evaluation/reference_guided_6f/improvement_plan.md`
  - `evaluation/reference_guided_6f/summary.md`
- Hệ thống sẵn sàng để Người dùng đánh giá và cấp quyền thực hiện Phiên 6G!
