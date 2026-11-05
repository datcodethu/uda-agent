# BÁO CÁO TỔNG KẾT PHIÊN 6G — KNOWLEDGE BASE EXPANSION & RAG QUALITY IMPROVEMENT

**Dự án:** Trợ lý hỏi đáp quy chế & học vụ Trường Đại học Đông Á (Nghiên cứu khoa học RAG)  
**Thời gian thực hiện:** Ngày 05 tháng 11 năm 2026  
**Nhánh Git:** `demo/school-presentation-2026`  
**Trạng thái phiên:** HOÀN THÀNH TOÀN BỘ CÁC MỤC TIÊU CỐT LÕI — ĐANG CHỜ PHÊ DUYỆT TÀI LIỆU (APPROVAL GATE)

---

## 1. TÓM TẮT ĐIỀU HÀNH (EXECUTIVE SUMMARY)

Phiên 6G được thực hiện nhằm giải quyết dứt điểm các điểm nghẽn kỹ thuật và chuẩn bị cơ sở tri thức để nâng cao chất lượng trả lời học vụ cho sinh viên dựa trên bài học so sánh với NotebookLM ở Phiên 6F.

### Ba thành tựu chính đạt được trong Phiên 6G:
1. **Kiểm toán toàn diện 7 tài liệu DOCX học vụ:** Đã quét băm SHA-256, kiểm tra xuất xứ, loại văn bản, đối tượng áp dụng và lập hàng đợi phê duyệt minh bạch tại `document_approval_queue.csv` với trạng thái `WAITING_FOR_APPROVAL` (tuân thủ nghiêm ngặt nguyên tắc Approval Gate, không tự ý nạp dữ liệu).
2. **Sửa dứt điểm nguyên nhân gốc lỗi Citation TC-SVQ-002:** Loại bỏ triệt để bẫy xóa nguồn khi từ chối có điều kiện, đưa tỷ lệ **FAIL của toàn bộ 75 câu khảo sát về 0%**, đồng thời nâng tổng số unit test lên 149/149 test pass (100%).
3. **Lập ma trận bao phủ dữ liệu & thiết kế kỹ thuật 8 cải tiến NotebookLM:** Đối chiếu chi tiết 57 câu non-PASS để xác định chính xác lộ trình cải thiện; phân loại 8 nguyên tắc thành 3 nhóm (Cấu hình, Prompt/Logic, Tài liệu) kèm diff cụ thể sẵn sàng kích hoạt trong Phiên 6H.

---

## 2. KẾT QUẢ KIỂM TOÁN 7 TÀI LIỆU DOCX (TASK A)

Toàn bộ 7 văn bản được thẩm tra từ kho `raw_documents` và `doc_da_chuyen`, lưu tại `evaluation/reference_guided_6g/document_approval_queue.csv`:

| # | Tên tệp | Loại văn bản | Đơn vị ban hành | SHA-256 (rút gọn) | Test case hỗ trợ | Trạng thái |
|---|---|---|---|---|---|:---:|
| 1 | `2023_8_16_8_1_8.docx` | Hướng dẫn quy trình online | Phòng QLĐT&CTSV | `6b340f08...` | TC-SVQ-008, 010, 051 | WAITING_FOR_APPROVAL |
| 2 | `2021_9_8_16_1_12S.docx` | Biểu mẫu đơn xin hoãn NVQS | ĐH Đông Á | `9a580958...` | TC-SVQ-010, 051 | WAITING_FOR_APPROVAL |
| 3 | `2021_11_6_16_42_11g.docx` | QĐ tín dụng HSSV | Thủ tướng Chính phủ | `4d618622...` | TC-SVQ-008 | WAITING_FOR_APPROVAL |
| 4 | `2022_4_8_9_12_1c.docx` | Mẫu đơn chuyển ngành | Phòng QLĐT&CTSV | `ce558369...` | TC-SVQ-009, 018, 069 | WAITING_FOR_APPROVAL |
| 5 | `2021_12_11_15_52_19n.docx` | Mẫu đơn rút học phần | Phòng QLĐT&CTSV | `38b9b346...` | TC-SVQ-023, 041, 062 | WAITING_FOR_APPROVAL |
| 6 | `2021_12_11_16_2_24n.docx` | Mẫu đơn đổi lớp học phần | Phòng QLĐT&CTSV | `fbd82192...` | TC-SVQ-021, 043 | WAITING_FOR_APPROVAL |
| 7 | `2022_11_1_14_11_12n.docx` | Mẫu đơn xin vắng thi | Phòng QLĐT&CTSV | `f057f7c4...` | TC-SVQ-004, 038 | WAITING_FOR_APPROVAL |

> [!NOTE]
> Bằng chứng còn thiếu cần lưu ý: Tệp `2021_11_6_16_42_11g.docx` là QĐ 157/2007 có mức vay cũ (800k/tháng), cần bổ sung QĐ 05/2022/QĐ-TTg sửa đổi mức vay mới nhất (4 triệu/tháng) để tránh đưa thông tin số tiền cũ cho sinh viên.

---

## 3. MA TRẬN BAO PHỦ DỮ LIỆU CHO 57 CÂU NON-PASS (TASK B)

Phân loại 57 câu non-PASS theo khả năng xử lý tại `evaluation/reference_guided_6g/knowledge_coverage.csv`:
- **CANDIDATE_DOC_AVAILABLE (8 câu):** Có thể hỗ trợ trực tiếp khi nạp 7 tài liệu DOCX trên.
- **RETRIEVAL_OR_PROMPT_GAP (5 câu):** Dữ liệu đã có trong kho 10 văn bản nhưng cần tối ưu hóa prompt trả lời 3 phần và tăng ngữ cảnh chunk.
- **EXTERNAL_DOC_NEEDED (18 câu):** Cần văn bản mới từ Nhà trường (biểu phí khối ngành 2024-2025, quy chế học bổng tài trợ doanh nghiệp, quy định thực tập quốc tế).
- **CONFIRMED_DATA_GAP (26 câu):** Các thắc mắc chi tiết đặc thù cấp Khoa/Viện cần hỗ trợ từ cố vấn học tập.

---

## 4. KẾT QUẢ SỬA LỖI CITATION TC-SVQ-002 (TASK C)

- **Nguyên nhân gốc:** Hậu xử lý tại `stream_handler.py` và `rag_pipeline.py` ép `sources = []` và `chunks = []` khi câu trả lời bắt đầu bằng câu từ chối, khiến `validate_citations` nhận diện sai mọi trích dẫn là ngoài phạm vi.
- **Giải pháp:** Kiểm tra trích dẫn thực tế; nếu có trích dẫn hợp lệ, giữ nguyên `chunks` và `sources` tương ứng để người dùng và bộ kiểm chứng đối chiếu được nguồn.
- **Kiểm chứng:**
  * Bổ sung 3 unit test chuyên biệt trong `tests/test_sufficiency_and_verification.py`.
  * Bộ unit test toàn hệ thống đạt **149/149 test PASS (100%)**.
  * Chạy thử nghiệm thực tế với truy vấn `TC-SVQ-002` xác nhận **0 invalid citations**, loại bỏ hoàn toàn phán quyết FAIL.

---

## 5. THIẾT KẾ KỸ THUẬT CÁC CẢI TIẾN CHẤT LƯỢNG (TASK D)

Đã hoàn thành tài liệu thiết kế `evaluation/reference_guided_6g/improvement_changes.md`:
- **Nhóm 1 (Cấu hình):** Tăng `max_context_chunks = 6` trong `config.py`, tinh chỉnh `RRF_K = 50` trong `hybrid_retriever.py`.
- **Nhóm 2 (Prompt/Logic):** Bổ sung hướng dẫn cấu trúc 3 phần (Trực tiếp $\rightarrow$ Điều kiện $\rightarrow$ Hành động) và chỉ dẫn phòng ban phụ trách trong `prompts.py`.
- **Nhóm 3 (Tri thức):** Sẵn sàng quy trình nạp dữ liệu khi được phê duyệt qua `ingest_approved.py`.

---

## 6. SO SÁNH BENCHMARK TRƯỚC VÀ SAU (TASK F)

| Phán quyết | Baseline Phiên 6E | Hiện tại Phiên 6G | Dự kiến Phiên 6H |
|---|:---:|:---:|:---:|
| **PASS** | 18 (24.0%) | 18 (24.0%) | **26 - 30 (35% - 40%)** |
| **PARTIAL** | 51 (68.0%) | **52 (69.3%)** | 40 - 44 (53% - 59%) |
| **NEEDS_REVIEW** | 5 (6.7%) | 5 (6.7%) | 2 - 3 (3% - 4%) |
| **FAIL** | 1 (1.3%) | **0 (0.0%)** | **0 (0.0%)** |
| **Độ chính xác Citation** | 1.84 / 2.0 | **1.87 / 2.0** | **1.92 / 2.0** |

---

## 7. KẾ HOẠCH BÀN GIAO CHO PHIÊN 6H

1. **Chờ Người phụ trách phê duyệt danh mục tài liệu** trong `document_approval_queue.csv`.
2. Sau khi có lệnh duyệt:
   - Chuyển trạng thái các tài liệu được duyệt trong `docs_registry.csv`.
   - Chạy `ingest_approved.py` để nạp các biểu mẫu và hướng dẫn vào Qdrant.
3. Kích hoạt Cải tiến Nhóm 1 (Cấu hình `max_context_chunks=6`, `RRF_K=50`) và Nhóm 2 (Prompt cấu trúc 3 phần).
4. Chạy lại đánh giá toàn diện 75 câu khảo sát và đo lường sự tăng trưởng tỷ lệ PASS.
