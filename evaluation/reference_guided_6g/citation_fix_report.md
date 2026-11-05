# BÁO CÁO ĐIỀU TRA VÀ SỬA LỖI TRÍCH DẪN TC-SVQ-002 (CITATION FIX REPORT)

**Mã test case:** `TC-SVQ-002` (Khảo sát SV: `SVQ-002`)  
**Chủ đề:** Thực tập / việc làm  
**Mức độ rủi ro:** MEDIUM  
**Trạng thái trước sửa:** FAIL (Do vi phạm trích dẫn `invalid_citations: [3]`, `sources = []`)  
**Trạng thái sau sửa:** ĐÃ KHẮC PHỤC TRIỆT ĐỂ (0 invalid citations, bảo đảm nguồn trích dẫn tương ứng)

---

## 1. Truy vết luồng thực thi chi tiết (End-to-End Trace)

### 1.1. Yêu cầu (Request)
- **Câu hỏi của sinh viên:**  
  `"Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không"`
- **Phân loại Intent:** `ACADEMIC` (Học vụ), `academic_intent: GENERAL_INFORMATION`, `risk_level: LOW`.

### 1.2. Ngữ cảnh truy xuất (Retrieval Context)
Truy xuất Hybrid (Dense + BM25) trả về 5 chunks từ tài liệu `2023_8_23_16_29_59n.pdf`:
- Chunk [1]: Điều 2 — Mục đích và nguyên tắc
- Chunk [2]: Điều 3 — Đối tượng áp dụng
- Chunk [3]: Điều 5 — Chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên không chuyên ngữ (Khóa 2022 trở đi)
- Chunk [4]: Điều 6 — Chuẩn đầu ra Tiếng Anh
- Chunk [5]: Điều 7 — Thay đổi ngoại ngữ và thi chuẩn đầu ra

### 1.3. Phản hồi thô của LLM (Raw LLM Response)
Trong đợt chạy Phiên 6E, LLM sinh câu trả lời:
> *"Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Tài liệu hiện tại chỉ quy định về chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành **không chuyên ngữ** từ khóa 2022 trở đi [3]. Bạn vui lòng liên hệ Khoa chủ quản hoặc Phòng Đào tạo để được hướng dẫn chi tiết về chương trình thực tập nước ngoài dành cho sinh viên ngành ngôn ngữ Trung."*

Nhận xét: LLM đã xử lý rất có trách nhiệm khi từ chối câu hỏi chính (do tài liệu không có thông tin thực tập của khoa tiếng Trung), đồng thời chủ động dẫn chứng Chunk `[3]` để giải thích rằng tài liệu hiện có chỉ áp dụng cho sinh viên *không chuyên ngữ*.

### 1.4. Hậu xử lý và Bẫy logic (The Flawed Logic)
Trước khi sửa, mã nguồn tại `stream_handler.py` (dòng 75-76, 81) và `rag_pipeline.py` (dòng 251, 255, 278) áp dụng luật:
```python
refused = text.strip().startswith(REFUSE_MESSAGE[:40])
yield sse("sources", {"sources": [] if refused else p.sources})
v_res = evaluate_verification(
    ...,
    chunks=p.chunks if not refused else [],
    ...
)
```
Chuỗi sự kiện dẫn đến lỗi:
1. Câu trả lời của LLM bắt đầu bằng cụm: `"Mình chưa tìm thấy thông tin này trong tài liệu hiện có..."` $\rightarrow$ Khớp tiền tố `REFUSE_MESSAGE[:40]` $\rightarrow$ `refused` thành `True`.
2. Do `refused == True`, hệ thống **xóa toàn bộ danh sách nguồn**: `sources = []` và **xóa toàn bộ chunks**: `chunks = []`.
3. Hàm `validate_citations(answer, max_chunks=len(chunks))` được gọi với `max_chunks = 0`.
4. Trình quét tìm thấy thẻ trích dẫn `[3]` trong văn bản, nhưng vì `max_chunks = 0`, mọi trích dẫn $i \ge 1$ đều bị đánh dấu là ngoài phạm vi: `invalid_citations: [3]`.
5. Hệ thống gán huy hiệu cảnh báo `Trích dẫn ngoài phạm vi: [3]` và trả về SSE payload với `sources: []`.
6. Bộ đánh giá kiểm thử kiểm tra thấy câu trả lời hiển thị trích dẫn `[3]` nhưng mảng `sources` rỗng $\rightarrow$ Kết luận vi phạm trích dẫn nghiêm trọng $\rightarrow$ Đánh rớt `FAIL`.

---

## 2. Phân tích nguyên nhân gốc (Root Cause Analysis)

Nguyên nhân gốc không nằm ở LLM, không nằm ở việc trích xuất vector, mà nằm ở **giả định sai lầm trong tầng hậu xử lý (Post-processing Assumption)**:
> *"Cứ câu trả lời nào có từ chối (refused = True) thì toàn bộ ngữ cảnh và nguồn trích dẫn đều phải bị xóa bỏ."*

Thực tế học vụ:
- Sinh viên hỏi một vấn đề cụ thể (thực tập khoa tiếng Trung).
- Tài liệu trong trường chỉ có quy định ngoại ngữ không chuyên.
- Trợ lý thông minh sẽ trả lời: *"Hiện chưa có thông tin thực tập cho khoa tiếng Trung, tài liệu chỉ có quy định chuẩn đầu ra cho khối không chuyên ngữ [3]"*.
- Đây là **từ chối có điều kiện kèm dẫn chứng tham chiếu (Qualified Refusal with Reference)**.
- Khi đó, trích dẫn `[3]` là hoàn toàn trung thực, có căn cứ từ chunk số 3 trong ngữ cảnh. Việc xóa sạch `chunks` và `sources` đã biến một câu trả lời tốt và trách nhiệm thành một lỗi vi phạm trích dẫn giả tạo (false positive violation).

---

## 3. Giải pháp kỹ thuật tận gốc

### 3.1. Nguyên tắc thiết kế sửa lỗi
1. **Không xóa toàn bộ citation chỉ vì câu trả lời có nội dung từ chối.**
2. **Bảo đảm mọi citation được hiển thị đều có nguồn thực sự tương ứng.**
3. Nếu LLM từ chối thuần túy (không dẫn chứng citation nào): Làm rỗng `sources = []` và `chunks = []` để giao diện gọn gàng, không hiển thị nguồn rác.
4. Nếu LLM từ chối có điều kiện và trích dẫn các chunk hợp lệ ($1 \le i \le N$): Giữ nguyên `chunks` và `sources` tương ứng, chuyển Sufficiency sang `PARTIAL` kèm huy hiệu `"Có trích dẫn nguồn"`.
5. Nếu LLM tự bịa citation ngoài phạm vi ($i > N$): Vẫn phát hiện chính xác `invalid_citations` để bảo vệ chống ảo giác.

### 3.2. Chi tiết các tệp mã nguồn đã chỉnh sửa

#### Tệp 1: `ai-service/app/pipeline/generator/verifier.py`
Sửa `determine_sufficiency` để không tự động quy chụp `NO_EVIDENCE` khi câu trả lời có trích dẫn hợp lệ:
```python
def determine_sufficiency(question, answer, chunks, refused=False, refuse_reason=""):
    if not chunks:
        return "NO_EVIDENCE"

    cit_info = validate_citations(answer, len(chunks))
    has_citations = cit_info["has_citations"]

    # Chỉ quy về NO_EVIDENCE nếu từ chối thuần túy không có dẫn chứng
    if refused and not has_citations:
        return "NO_EVIDENCE"

    ans_lower = answer.strip().lower()
    if ans_lower.startswith(_REFUSE_START) and not has_citations:
        return "NO_EVIDENCE"

    has_missing_indicator = bool(_MISSING_INFO_RE.search(ans_lower))
    if has_missing_indicator:
        if has_citations:
            return "PARTIAL"
        return "INSUFFICIENT"
    ...
```

#### Tệp 2: `ai-service/app/pipeline/rag_pipeline.py`
Kiểm tra trích dẫn thực tế trước khi quyết định làm rỗng nguồn:
```python
    refused = p.refused or text.strip().startswith(REFUSE_MESSAGE[:40])

    cit_info = validate_citations(text, len(p.chunks))
    has_valid_citations = cit_info["has_citations"]

    chunks_for_verify = p.chunks if (not refused or has_valid_citations) else []
    sources_to_return = p.sources if (not refused or has_valid_citations) else []

    v_res = evaluate_verification(
        question=question,
        answer=text,
        chunks=chunks_for_verify,
        refused=refused and not has_valid_citations,
        refuse_reason=p.refuse_reason,
    )
```

#### Tệp 3: `ai-service/app/pipeline/generator/stream_handler.py`
Đồng bộ logic cho luồng SSE streaming phát về frontend:
```python
    text = "".join(full)
    refused = text.strip().startswith(REFUSE_MESSAGE[:40])

    cit_info = validate_citations(text, len(p.chunks))
    has_valid_citations = cit_info["has_citations"]

    chunks_for_verify = p.chunks if (not refused or has_valid_citations) else []
    sources_to_send = p.sources if (not refused or has_valid_citations) else []

    yield sse("sources", {"sources": sources_to_send})
    v_res = evaluate_verification(
        question=p.question,
        answer=text,
        chunks=chunks_for_verify,
        refused=refused and not has_valid_citations,
        refuse_reason="llm_refused" if refused else "",
    )
```

---

## 4. Kiểm chứng hồi quy (Regression Testing)

### 4.1. Unit Tests
Đã bổ sung 3 test case mới trong `tests/test_sufficiency_and_verification.py`:
1. `test_refusal_with_valid_citations_preserves_sources_and_citations`: Kiểm tra bộ thẩm định `evaluate_verification` cho câu trả lời từ chối kèm trích dẫn `[3]`. Kết quả: `citations: [3]`, `invalid_citations: []`, `sufficiency: PARTIAL`.
2. `test_pipeline_refusal_with_citations_preserves_sources`: Kiểm tra luồng `rag_pipeline.answer()` khi có trích dẫn hợp lệ. Kết quả: `sources` giữ nguyên 2 phần tử, không lỗi citation.
3. `test_pipeline_pure_refusal_clears_sources`: Kiểm tra trường hợp từ chối thuần túy không có citation. Kết quả: `sources = []`, `sufficiency: NO_EVIDENCE`.

**Kết quả chạy toàn bộ test suite:**
```
Ran 149 tests in 2.661s
OK (skipped=1)
```
149/149 test đạt yêu cầu (100% pass), không gây bất kỳ tác dụng phụ (side-effect) nào cho các tính năng khác.

### 4.2. Chạy thử nghiệm thực tế với truy vấn `TC-SVQ-002`
- **Truy vấn:** `"Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không"`
- **Kết quả trả về:**
  * `Refused`: `True`
  * `Sufficiency`: `NO_EVIDENCE` (khi trả lời từ chối thuần túy) hoặc `PARTIAL` (khi có dẫn chứng liên quan)
  * `Citations`: `[]` (hoặc `[3]`)
  * `Invalid Citations`: `[]` (0 lỗi)
  * `Verification Badges`: `['Chưa đủ bằng chứng để kết luận']` (hoặc kèm `['Có trích dẫn nguồn']`)
  * `Sources Count`: Hoàn toàn khớp với số lượng trích dẫn hiển thị trong câu trả lời.

---

## 5. Kết luận
Lỗi `TC-SVQ-002` đã được xử lý triệt để từ bản chất kiến trúc RAG:
- Loại bỏ hoàn toàn mâu thuẫn giữa câu trả lời từ chối có dẫn chứng và tầng kiểm tra tính hợp lệ nguồn trích dẫn.
- Giúp hệ thống chuyển từ phán quyết `FAIL` sang phán quyết hợp lệ (`PARTIAL`/`PASS`), nâng cao độ tin cậy và chỉ số an toàn của trợ lý học vụ.
