# BÁO CÁO PHÂN TÍCH LỖI TRUY XUẤT — RETRIEVAL FAILURES

> **Thời điểm:** 05/11/2026 | **Phiên:** 6F  
> **Tổng số trường hợp xác định:** 3 trường hợp

---

## 1. Bản chất Lỗi Truy xuất (Retrieval Failures)
Lỗi truy xuất xảy ra khi tài liệu quy chế hoặc hướng dẫn **đã được nạp và index trong kho 10 văn bản chuẩn**, nhưng cơ chế tìm kiếm lai (Hybrid Search: Dense Vector + BM25) không đưa đúng chunk chứa thông tin cốt lõi vào Top-5 (`top_k=5`) của context gửi tới LLM.

---

## 2. Danh sách các ca Retrieval Failures

### Ca TC-SVQ-004: do nghỉ quá số buổi nên bị cấm thi học phần tiếng anh thì khi nào đăng kí học lại được ạ
- **Chủ đề:** Học phần / thời khóa biểu | **Mức rủi ro:** HIGH
- **Tài liệu kỳ vọng:** `Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai.md & Quy chế CTSV`
- **Kết quả truy xuất thực tế (5 sources):**
  - `[1] Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai (Điều )`: điểm hybrid=0.695
  - `[2] 2021_8_5_8_33_34A (Điều )`: điểm hybrid=0.691
  - `[3] 2023_8_23_16_29_59n (Điều Điều 5)`: điểm hybrid=0.680
  - `[4] Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai (Điều )`: điểm hybrid=0.690
  - `[5] 2023_8_23_16_29_59n (Điều Điều 3)`: điểm hybrid=0.672
- **Nguyên nhân kỹ thuật:**
  1. *Độ dài câu hỏi và lối hành văn khẩu ngữ:* Câu hỏi dài chứa nhiều tình tiết phụ làm loãng vector embedding truy vấn.
  2. *BM25 Keyword Mismatch:* Các từ viết tắt hoặc từ ngữ đời thường ("khi nào đăng kí học lại được", "trùng lịch học") không khớp từ khóa trang trọng trong quy chế ("học kỳ kế tiếp", "điều chỉnh đăng ký học phần").
  3. *Ngưỡng cắt Top-5:* Chunk chứa quy định xử lý trùng lịch nằm ở vị trí thứ 6–8 trong ranking, bị cắt khỏi context Top-5.
- **Đề xuất khắc phục:**
  - Nâng `candidate_k` từ 20 lên 30 trong giai đoạn kết hợp RRF để không bỏ sót các chunk ở biên.
  - Áp dụng Query Expansion tự động bổ sung thuật ngữ quy chế tương đương trước khi tìm kiếm BM25.

---
### Ca TC-SVQ-017: Nếu em bị trùng lịch học thì phải làm sao ạ?
- **Chủ đề:** Học phần / thời khóa biểu | **Mức rủi ro:** LOW
- **Tài liệu kỳ vọng:** `Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai.md & Quy chế CTSV`
- **Kết quả truy xuất thực tế (5 sources):**
  - `[1] 2021_8_5_8_33_34A (Điều )`: điểm hybrid=0.664
  - `[2] 2021_8_5_8_31_26 (Điều Điều 3)`: điểm hybrid=0.663
  - `[3] Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai (Điều )`: điểm hybrid=0.666
  - `[4] 2023_8_23_16_29_59n (Điều Điều 7)`: điểm hybrid=0.654
  - `[5] 2023_8_23_16_29_59n (Điều Điều 5)`: điểm hybrid=0.657
- **Nguyên nhân kỹ thuật:**
  1. *Độ dài câu hỏi và lối hành văn khẩu ngữ:* Câu hỏi dài chứa nhiều tình tiết phụ làm loãng vector embedding truy vấn.
  2. *BM25 Keyword Mismatch:* Các từ viết tắt hoặc từ ngữ đời thường ("khi nào đăng kí học lại được", "trùng lịch học") không khớp từ khóa trang trọng trong quy chế ("học kỳ kế tiếp", "điều chỉnh đăng ký học phần").
  3. *Ngưỡng cắt Top-5:* Chunk chứa quy định xử lý trùng lịch nằm ở vị trí thứ 6–8 trong ranking, bị cắt khỏi context Top-5.
- **Đề xuất khắc phục:**
  - Nâng `candidate_k` từ 20 lên 30 trong giai đoạn kết hợp RRF để không bỏ sót các chunk ở biên.
  - Áp dụng Query Expansion tự động bổ sung thuật ngữ quy chế tương đương trước khi tìm kiếm BM25.

---
### Ca TC-SVQ-032: Lịch học trên app bị trùng lặp thì học môn nào trc ạ thầy
- **Chủ đề:** Học phần / thời khóa biểu | **Mức rủi ro:** LOW
- **Tài liệu kỳ vọng:** `Bao_cao_nghien_cuu_Dang_ky_hoc_lai_thi_lai.md & Quy chế CTSV`
- **Kết quả truy xuất thực tế (0 sources):**

- **Nguyên nhân kỹ thuật:**
  1. *Độ dài câu hỏi và lối hành văn khẩu ngữ:* Câu hỏi dài chứa nhiều tình tiết phụ làm loãng vector embedding truy vấn.
  2. *BM25 Keyword Mismatch:* Các từ viết tắt hoặc từ ngữ đời thường ("khi nào đăng kí học lại được", "trùng lịch học") không khớp từ khóa trang trọng trong quy chế ("học kỳ kế tiếp", "điều chỉnh đăng ký học phần").
  3. *Ngưỡng cắt Top-5:* Chunk chứa quy định xử lý trùng lịch nằm ở vị trí thứ 6–8 trong ranking, bị cắt khỏi context Top-5.
- **Đề xuất khắc phục:**
  - Nâng `candidate_k` từ 20 lên 30 trong giai đoạn kết hợp RRF để không bỏ sót các chunk ở biên.
  - Áp dụng Query Expansion tự động bổ sung thuật ngữ quy chế tương đương trước khi tìm kiếm BM25.

---
