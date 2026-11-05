# BÁO CÁO KIỂM THỬ CHATBOT — KHẢO SÁT SINH VIÊN

> **Phiên chạy:** `survey_qa_20261105_01`  
> **Thời điểm hoàn thành:** `2026-11-05T03:36:42.375598+00:00`  
> **Trạng thái:** **ĐÃ CHẠY HOÀN TẤT TRÊN LIVE SERVER**

---

## 1. Thông tin phiên chạy
- **Run ID:** `survey_qa_20261105_01`
- **Thời điểm bắt đầu:** `2026-11-05T03:26:12.952936+00:00`
- **Branch / Git SHA:** `demo/school-presentation-2026` / `80a8a52b1308d8fd15c721a2230391ea42219b5e`
- **Dataset SHA-256:** `6D45776344AF4CE6EC9758D8397C0CB0E6A692633D6D52B5D3051729024DF94E`
- **Exclusions SHA-256:** `12AC04FC92BAC5839447255EF6BFA006E252FB112E60C23E98DE350035D9CF47`
- **Model / Qdrant collection:** `gemini-flash-lite-latest` / `donga_regulations (10 docs, 103 chunks)`
- **Endpoint kiểm thử:** `http://127.0.0.1:8000/api/chat/stream`
- **Người kiểm duyệt:** AI Coding Agent & Sinh viên NCKH
- **Cấu hình / Quota:** Concurrency = 1, delay = 1.0s/req, 75 live stream requests

---

## 2. Tổng quan kết quả thực thi
| Chỉ số | Kết quả | Tỷ lệ (%) |
|---|---|---|
| **Tổng số câu hỏi khảo sát** | **75** | 100.0% |
| **Số test cases đã tạo** | **75** | 100.0% |
| **Live executed thành công** | **75** | 100.0% |
| **PASS (Chuẩn xác, đủ căn cứ)** | **18** | **24.0%** |
| **PARTIAL (Đúng một phần, thiếu chi tiết)** | **51** | **68.0%** |
| **NEEDS_REVIEW (Cần đối chiếu văn bản)** | **5** | **6.7%** |
| **FAIL (Lỗi quy chế / trích dẫn / an toàn)** | **1** | **1.3%** |
| **BLOCKED (Hết quota / lỗi hệ thống)** | **0** | **0.0%** |
| **Unit tests hệ thống** | **146 / 146 PASS** | 100.0% (1 skipped) |

---

## 3. Độ phủ theo Nhóm Chủ đề và Mức độ Rủi ro

### A. Phân bổ theo Mức độ Rủi ro
| Mức rủi ro | Tổng số | PASS | PARTIAL | NEEDS_REVIEW | FAIL | BLOCKED |
|---|---|---|---|---|---|---|
| **HIGH** | 15 | 2 | 11 | 2 | 0 | 0 |
| **MEDIUM** | 37 | 8 | 25 | 3 | 1 | 0 |
| **LOW** | 23 | 8 | 15 | 0 | 0 | 0 |

### B. Phân bổ theo Nhóm Chủ đề
| Nhóm chủ đề | Tổng số | PASS | PARTIAL | NEEDS_REVIEW | FAIL |
|---|---|---|---|---|---|
| BHYT / sức khỏe | 2 | 0 | 1 | 1 | 0 |
| Chuẩn đầu ra / tốt nghiệp | 10 | 6 | 2 | 2 | 0 |
| Học bổng | 9 | 3 | 6 | 0 | 0 |
| Học phí / tài chính | 10 | 0 | 9 | 1 | 0 |
| Học phần / thời khóa biểu | 11 | 4 | 7 | 0 | 0 |
| Khác / cần phân loại | 3 | 0 | 3 | 0 | 0 |
| Phản ánh / công bằng | 1 | 0 | 1 | 0 | 0 |
| Quân sự / nghĩa vụ | 8 | 0 | 8 | 0 | 0 |
| Rèn luyện / hoạt động | 9 | 1 | 8 | 0 | 0 |
| Thi cử / học lại | 7 | 3 | 3 | 1 | 0 |
| Thủ tục hành chính | 2 | 0 | 2 | 0 | 0 |
| Thực tập / việc làm | 3 | 1 | 1 | 0 | 1 |

---

## 4. Hiệu năng & Tốc độ Phản hồi
- **Cỡ mẫu thực đo:** 75 câu hỏi trực tiếp qua SSE streaming.
- **P50 Total Latency:** `2375 ms` (~2.38s)
- **P95 Total Latency:** `13648 ms` (~13.65s)
- **P50 Time-to-First-Token (TTFT):** `1740 ms` (~1.74s)
- **P95 Time-to-First-Token (TTFT):** `13506 ms` (~13.51s)

---

## 5. Phân tích lỗi nghiêm trọng (Failures & Vulnerabilities)
| Case | Câu hỏi nguyên văn | Vấn đề phát hiện | Chứng cứ / Sources | Root Cause | Đề xuất sửa |
|---|---|---|---|---|---|
| `TC-SVQ-002` | Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không | Trích dẫn không hợp lệ ngoài dải nguồn: [3] | Sufficiency: NO_EVIDENCE | Badges: Chưa đủ bằng chứng để kết luận, Trích dẫn ngoài phạm vi: [3] | Sources: 0 | POLICY / VERIFIER | Sửa prompt sinh citation hoặc lọc chỉ số trích dẫn hợp lệ. |

---

## 6. Top 10 câu cần cải thiện (Dữ liệu chưa đầy đủ hoặc cần bổ sung tài liệu)
| ID | Câu hỏi nguyên văn | Đánh giá | Chi tiết thiếu/sai | Đề xuất khắc phục |
|---|---|---|---|---|
| `TC-SVQ-001` | Em nợ học phí thì có được đăng ký môn không ạ | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-002` | Sinh viên khoa ngôn ngữ trung chuyên ngành giảng dạy thì có đi thực tập nước ngoài không | **FAIL** | Trích dẫn không hợp lệ ngoài dải nguồn: [3] | Sửa prompt sinh citation hoặc lọc chỉ số trích dẫn hợp lệ. |
| `TC-SVQ-003` | Mức học bổng được nhận | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-004` | do nghỉ quá số buổi nên bị cấm thi học phần tiếng anh thì khi nào đăng kí học lại được ạ | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-005` | Mỗi năm trường mình có tăng thêm học phí không nhỉ nếu tăng thì tăng khoảng bao nhiêu | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-007` | Em đang thắc mắc học cải thiện nhiều thì có hạ bằng giống học lại không | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-009` | Chuẩn đầu ra của ngành Ngôn ngữ Trung là sao vậy ạ? | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-012` | Thực tập ra sao ạ | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-013` | cách để cộng điểm rèn luyện thì cần làm những gì | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |
| `TC-SVQ-014` | lịch học quân sự của khoa em ạ | **PARTIAL** | Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có. | Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức. |

---

## 7. Ví dụ các câu trả lời tốt tiêu biểu
Các câu hỏi đạt điểm cao (11-12/12), thể hiện sự kết hợp giữa trích dẫn chính xác, bảo toàn điều kiện quy chế và thái độ thấu cảm:
1. **TC-SVQ-006 (Đóng trước 10 triệu còn thiếu 9.2 triệu, có được thi không):** Không khẳng định cấm thi tuyệt đối; nêu rõ điều kiện 'cố tình... mà không có lý do chính đáng'; giải thích việc chưa nộp đủ học phí có thể ảnh hưởng điều kiện dự thi nhưng cần kiểm tra danh sách chính thức và liên hệ Phòng KHTC để xin gia hạn nếu có hoàn cảnh.
2. **TC-SVQ-019 (Chuẩn đầu ra, điều kiện tốt nghiệp là gì):** Nêu đầy đủ các điều kiện tốt nghiệp cốt lõi (tích lũy tín chỉ, điểm TB >= 2.0, hoàn thành GDQP-AN, GDTC, chuẩn đầu ra ngoại ngữ/tin học) kèm trích dẫn văn bản quy chế đào tạo tín chỉ.
3. **TC-SVQ-022 (BHYT diện an toàn khu & hoàn tiền):** Không mở đầu dọa kỷ luật; giải thích rõ quyền lợi an sinh xã hội chăm sóc sức khỏe, hướng dẫn nộp minh chứng thẻ BHYT địa phương cho Phòng CTSV để đối soát tránh thu trùng.
4. **TC-SVQ-034 (Nếu thi trượt môn thì có sao không):** Trả lời trực diện, giải thích bình tĩnh về việc đăng ký học lại môn bắt buộc hoặc chọn môn thay thế, ảnh hưởng tới điểm trung bình tích lũy, không phán xét tiêu cực.

---

## 8. Danh sách cần con người thẩm định (Human Review Required)
Các tình huống liên quan đến thủ tục chuyên ngành hoặc văn bản ngoài 10 quy chế cốt lõi cần đối chiếu thêm:
| ID | Câu hỏi nguyên văn | Vấn đề cần thẩm định | Nguồn / Đơn vị cần đối chiếu | Trạng thái |
|---|---|---|---|---|
| `TC-SVQ-010` | Em nợ học phí thì có được đăng ký thi không ạ | Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường. | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |
| `TC-SVQ-020` | khoa IT chọn đầu ra tiếng nhật thì cần N4 và B1 hay chỉ cần N4 | Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường. | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |
| `TC-SVQ-053` | Bảo hiểm y tế có bắt buộc kh | Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường. | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |
| `TC-SVQ-055` | Nghỉ bao nhiêu buổi là cấm thi vậy ạ | Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường. | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |
| `TC-SVQ-064` | ngành IT chọn đầu ra tiếng nhật thì cần n4 hay vừa cần n4 vừa cần b1 | Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường. | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |

---

## 9. Kết luận Đánh giá
- **Độ sẵn sàng trình diễn (Demo Readiness):** **DEMO_READY**
- **Độ an toàn học vụ:** 100% câu hỏi nhạy cảm (nợ học phí, cấm thi) đã giữ vững điều kiện *"mà không có lý do chính đáng"*, không có câu trả lời nào khẳng định cấm thi tuyệt đối hay phán quyết thay nhà trường.
- **Tồn tại chính:** 
  1. *Issue P1 (Citation trong câu từ chối):* Câu TC-SVQ-002 bị dính marker trích dẫn `[3]` khi LLM sinh câu từ chối (trong khi `sources = []`).
  2. *Data Gap (Thiếu văn bản hành chính):* Các thủ tục tạm hoãn NVQS, học phí GDQP-AN, đăng ký học lái xe, và chuẩn đầu ra chi tiết theo từng chuyên ngữ hiện chưa có văn bản chi tiết trong kho nên câu trả lời dừng ở mức PARTIAL/NEEDS_REVIEW.
- **Hướng xử lý ưu tiên:**
  1. Bổ sung post-processing: khi `sources` rỗng, tự động strip toàn bộ marker `\[\d+\]` trong câu trả lời từ chối.
  2. Thu thập và nạp thêm các văn bản hướng dẫn hành chính sinh viên từ cổng thông tin portal.
