# Báo cáo Truy vết Chuyên sâu 10 Câu hỏi Trọng điểm (Before vs After)
## So sánh Đối chứng Pipeline Cải tiến vs Baseline v2 Cũ

**Ngày đánh giá:** 05/11/2026  
**Mô hình:** Gemini Flash Lite & Gemini Embedding 001  
**Kho dữ liệu:** `donga_kb_v2` (451 chunks)  

---

### 1. Bảng Tổng hợp Kết quả Before vs After

| Test ID | Chủ đề | Câu hỏi thực tế | Before (Verdict / Score / Suff) | After (Verdict / Score / Suff) | Faithfulness | Chunks mới kéo vào |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **TC-SVQ-001** | Học phí / tài chính | Em nợ học phí thì có được đăng ký môn kh... | PARTIAL (9đ, NO_EVIDENCE) | **PASS** (12đ, SUFFICIENT) | 100% | `src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1, src-v2-016-d0-3` |
| **TC-SVQ-010** | Học phí / tài chính | Em nợ học phí thì có được đăng ký thi kh... | PARTIAL (9đ, NO_EVIDENCE) | **PASS** (12đ, SUFFICIENT) | 100% | `src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1, src-v2-015-d0-3` |
| **TC-SVQ-028** | Học phí / tài chính | Hạn nộp học phí trễ nhất là trong bao lâ... | PASS (10đ, PARTIAL) | **PASS** (11đ, PARTIAL) | 100% | `src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1, src-v2-009-d14-4` |
| **TC-SVQ-050** | Học phí / tài chính | sang kì 2 thì học phí có thể chia ra đón... | PASS (11đ, PARTIAL) | **PASS** (12đ, SUFFICIENT) | 100% | `src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1, src-v2-009-d6-1` |
| **TC-SVQ-003** | Học bổng | Mức học bổng được nhận | PASS (11đ, PARTIAL) | **PASS** (11đ, PARTIAL) | 100% | `src-v2-016-d0-3, src-v2-009-d22-1` |
| **TC-SVQ-024** | Học bổng | Muốn đăng ký học bổng thì làm thế nào? | PASS (10đ, PARTIAL) | **PASS** (12đ, SUFFICIENT) | 100% | `src-v2-015-d0-3, src-v2-016-d0-3` |
| **TC-SVQ-033** | Học bổng | Điều kiện xét học bổng | PASS (10đ, PARTIAL) | **PASS** (11đ, PARTIAL) | 100% | `src-v2-009-d22-1, src-v2-009-d14-3` |
| **TC-SVQ-022** | BHYT / sức khỏe | em ở quê thuộc an toàn khu thì có miễn b... | PASS (10đ, PARTIAL) | **PASS** (10đ, PARTIAL) | 100% | `src-v2-011-trường_đại_học_đ244ng_á_trao_g-1, src-v2-009-d14-3` |
| **TC-SVQ-055** | Thi cử / học lại | Nghỉ bao nhiêu buổi là cấm thi vậy ạ | PASS (12đ, SUFFICIENT) | **PASS** (12đ, SUFFICIENT) | 100% | `src-v2-015-d0-6, src-v2-015-d0-10` |
| **TC-SVQ-009** | Chuẩn đầu ra / tốt nghiệp | Chuẩn đầu ra của ngành Ngôn ngữ Trung là... | PASS (10đ, PARTIAL) | **PASS** (10đ, PARTIAL) | 100% | `src-v2-018-chuẩn_đầu_ra_ngoại_ngữ-1, src-v2-018-chương_trình_đào_tạo_ngoại_ngữ-1` |

---

### 2. Chi tiết Từng Câu hỏi: Truy vết Chuỗi Question $\rightarrow$ Chunks $\rightarrow$ Answer $\rightarrow$ Claims

#### [1] TC-SVQ-001: Em nợ học phí thì có được đăng ký môn không ạ
- **Nhóm chủ đề:** Học phí / tài chính | **Ý định:** `ELIGIBILITY_CHECK` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PARTIAL (Điểm: 9/12, Sufficiency: `NO_EVIDENCE`)
- **Sau cải tiến:** **PASS** (Điểm: 12/12, Sufficiency: `SUFFICIENT`, Faithfulness: `100%`, Latency: `82421ms`)

**Câu trả lời CŨ (Trước):**
> Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Bạn vui lòng liên hệ Phòng Đào tạo để được hỗ trợ.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Quy định hiện hành của Nhà trường không có điều khoản cấm sinh viên nợ học phí tham gia đăng ký học phần mới. 
> 
> **1. Các giải pháp và biểu mẫu hỗ trợ học phí:**
> Khi gặp khó khăn về tài chính, sinh viên hoàn toàn có thể chủ động sử dụng các biểu mẫu hỗ trợ chính thức của Nhà trường để được xem xét giải quyết, bao gồm:
> - Mẫu đơn xin hỗ trợ học phí dành cho sinh viên [1].
> - Đơn xin gia hạn đóng học phí [1].
> - Giấy nhờ đóng học phí (kiêm xác nhận đủ điều kiện dự thi kết thúc học phần) [1].
> - Giấy nhờ chi (kiêm phiếu yêu cầu đóng học phí và BHYT) [1].
> 
> **2. Hướng dẫn hành động:**
> - **Bước 1:** Chủ động kiểm tra nghĩa vụ tài chính và theo dõi thông báo học phí trên Cổng thông tin sinh viên (`my.uda.edu.vn`) [2].
> - **Bước 2:** Nếu cần gia hạn hoặc hỗ trợ, bạn hãy làm đơn theo các biểu mẫu tài vụ của Nhà trường [1].
> - **Bước 3:** Liên hệ trực tiếp với **Phòng Tài chính Kế toán (P.201)** hoặc Thầy Nguyễn Hồng Định (Phụ trách giải đáp các vấn đề liên quan đến học phí) để được hướng dẫn chi tiết thủ tục xử lý công nợ [3], [7].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Các giải pháp và biểu mẫu hỗ trợ học phí:**
Khi gặp khó khăn về tài chính, sinh viên hoàn toàn có th*
- [x] *- Đơn xin gia hạn đóng học phí [1].*
- [x] *- Giấy nhờ đóng học phí (kiêm xác nhận đủ điều kiện dự thi kết thúc học phần) [1].*

**Nguồn sử dụng:** `[1] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[2] src-v2-009-d7-3`, `[3] src-v2-015-d0-3`, `[4] src-v2-011-d0-1`

---

#### [2] TC-SVQ-010: Em nợ học phí thì có được đăng ký thi không ạ
- **Nhóm chủ đề:** Học phí / tài chính | **Ý định:** `ELIGIBILITY_CHECK` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PARTIAL (Điểm: 9/12, Sufficiency: `NO_EVIDENCE`)
- **Sau cải tiến:** **PASS** (Điểm: 12/12, Sufficiency: `SUFFICIENT`, Faithfulness: `100%`, Latency: `24438ms`)

**Câu trả lời CŨ (Trước):**
> Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Bạn vui lòng liên hệ Phòng Đào tạo để được hỗ trợ.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Quy định hiện hành của Nhà trường không cấm sinh viên tham gia dự thi khi còn nợ học phí, trừ trường hợp sinh viên cố tình chậm nộp hoặc không nộp mà không có lý do chính đáng.
> 
> Để đảm bảo quyền lợi dự thi kết thúc học phần khi chưa hoàn thành nghĩa vụ tài chính, bạn có thể thực hiện các biểu mẫu hỗ trợ sau:
> - Sử dụng **"Giấy nhờ đóng học phí (kiêm xác nhận đủ điều kiện dự thi kết thúc học phần)"** hoặc làm **"Đơn xin gia hạn đóng học phí"** để được xem xét giải quyết [1].
> - Nếu cần hỗ trợ chi phí, bạn có thể tham khảo **"Mẫu đơn xin hỗ trợ HP dành cho Anh/Chị/Em học tại trường"** hoặc **"Đơn đề nghị miễn giảm tiền học phí học lại"** [1].
> 
> **Hướng dẫn hành động tiếp theo:**
> 1. Bạn hãy kiểm tra lại trạng thái học phí của mình trên Cổng thông tin sinh viên (`my.uda.edu.vn`) [6].
> 2. Nộp các biểu mẫu xin gia hạn hoặc giấy nhờ đóng học phí tại **Phòng Tài chính Kế toán (Phòng 201)** để được xác nhận điều kiện dự thi [1], [5].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Để đảm bảo quyền lợi dự thi kết thúc học phần khi chưa hoàn thành nghĩa vụ tài chính, bạn có thể thự*
- [x] *- Nếu cần hỗ trợ chi phí, bạn có thể tham khảo **"Mẫu đơn xin hỗ trợ HP dành cho Anh/Chị/Em học tại *
- [x] *Bạn hãy kiểm tra lại trạng thái học phí của mình trên Cổng thông tin sinh viên (`my.uda.edu.vn`) [6]*

**Nguồn sử dụng:** `[1] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[2] src-v2-015-d0-10`, `[3] src-v2-015-d0-13`, `[4] src-v2-009-d7-3`

---

#### [3] TC-SVQ-028: Hạn nộp học phí trễ nhất là trong bao lâu và xem ở đâu ạ?
- **Nhóm chủ đề:** Học phí / tài chính | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PASS (Điểm: 10/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 11/12, Sufficiency: `PARTIAL`, Faithfulness: `100%`, Latency: `3201ms`)

**Câu trả lời CŨ (Trước):**
> Mình chưa tìm thấy thông tin cụ thể về thời hạn nộp học phí trễ nhất trong tài liệu hiện có. Bạn vui lòng liên hệ trực tiếp Phòng Tài chính Kế toán (Phòng 201) hoặc qua số điện thoại hỗ trợ học phí để được hướng dẫn chính xác [1], [2]. 
> 
> Để kiểm tra thông tin học phí của cá nhân, bạn có thể truy cập vào Cổng thông tin sinh viên tại website **my.uda.edu.vn**.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Hiện tại, tài liệu của Nhà trường chưa quy định cụ thể về thời hạn (hạn chót) nộp học phí [1], [2]. 
> 
> Để kiểm tra thông tin chi tiết về học phí và các khoản nộp, bạn có thể thực hiện theo các bước sau:
> - **Kênh tra cứu:** Bạn truy cập vào cổng thông tin sinh viên tại website **my.uda.edu.vn** [5] hoặc liên hệ trực tiếp với **Phòng Tài chính Kế toán (Phòng P.201)** để được hỗ trợ chính xác [1], [3].
> - **Bộ phận phụ trách giải đáp học phí:** Thầy Nguyễn Hồng Định (SĐT: 0905142404) hoặc Phòng Tài chính Kế toán [1], [3].
> 
> Ngoài ra, nếu gặp khó khăn về tài chính, Nhà trường có hỗ trợ các biểu mẫu liên quan như *Đơn xin gia hạn đóng học phí* hoặc *Giấy nhờ đóng học phí (kiêm xác nhận đủ điều kiện dự thi kết thúc học phần)* để bạn tải về và làm thủ tục giải quyết [2].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Hiện tại, tài liệu của Nhà trường chưa quy định cụ thể về thời hạn (hạn chót) nộp học phí [1], [2].*
- [x] *Để kiểm tra thông tin chi tiết về học phí và các khoản nộp, bạn có thể thực hiện theo các bước sau:
*
- [x] *- **Bộ phận phụ trách giải đáp học phí:** Thầy Nguyễn Hồng Định (SĐT: 0905142404) hoặc Phòng Tài chí*

**Nguồn sử dụng:** `[1] src-v2-015-d0-3`, `[2] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[3] src-v2-016-d0-3`, `[4] src-v2-001-dịch_vụ_lưu_h224nh_t224i_liệu-3`

---

#### [4] TC-SVQ-050: sang kì 2 thì học phí có thể chia ra đóng được ko ạ
- **Nhóm chủ đề:** Học phí / tài chính | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PASS (Điểm: 11/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 12/12, Sufficiency: `SUFFICIENT`, Faithfulness: `100%`, Latency: `6511ms`)

**Câu trả lời CŨ (Trước):**
> Trong tài liệu hiện có chưa quy định chi tiết về việc học phí học kỳ 2 có được chia ra đóng thành nhiều đợt hay không. 
> 
> Để được giải đáp chính xác về các phương thức đóng học phí hoặc các chính sách hỗ trợ tài chính, bạn vui lòng liên hệ:
> - **Phòng Tài chính Kế toán (Phòng 201)** để được tư vấn trực tiếp về thủ tục và lịch nộp học phí [1], [2].
> - Hoặc liên hệ qua số điện thoại phụ trách giải đáp các vấn đề liên quan đến học phí [1], [2].

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Việc đóng học phí có thể được chia ra hoặc gia hạn theo nguyện vọng của sinh viên [3]. 
> 
> Khi có nhu cầu gia hạn hoặc chia nhỏ thời gian đóng học phí, sinh viên cần thực hiện theo các bước hỗ trợ của Nhà trường:
> 
> * **Hồ sơ cần chuẩn bị:** Sinh viên tải và điền thông tin vào **Đơn xin gia hạn đóng học phí** hoặc sử dụng **Giấy nhờ đóng học phí (kiêm xác nhận đủ điều kiện dự thi kết thúc học phần)** có sẵn trên hệ thống biểu mẫu của Nhà trường [3].
> * **Đầu mối liên hệ giải đáp và hướng dẫn:** Thầy Nguyễn Hồng Định (Phụ trách giải đáp các vấn đề liên quan đến học phí) hoặc Phòng Tài chính Kế toán (Phòng 201) [1], [2].
> 
> **Hướng dẫn hành động tiếp theo:** Bạn có thể liên hệ trực tiếp với Phòng Tài chính Kế toán (Phòng 201) hoặc gặp thầy phụ trách học phí để được hướng dẫn cụ thể thủ tục làm đơn gia hạn phù hợp với hoàn cảnh cá nhân [1], [2], [3].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Việc đóng học phí có thể được chia ra hoặc gia hạn theo nguyện vọng của sinh viên [3].*
- [x] ** **Hồ sơ cần chuẩn bị:** Sinh viên tải và điền thông tin vào **Đơn xin gia hạn đóng học phí** hoặc *
- [x] ** **Đầu mối liên hệ giải đáp và hướng dẫn:** Thầy Nguyễn Hồng Định (Phụ trách giải đáp các vấn đề li*

**Nguồn sử dụng:** `[1] src-v2-016-d0-3`, `[2] src-v2-015-d0-3`, `[3] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[4] src-v2-015-d0-13`

---

#### [5] TC-SVQ-003: Mức học bổng được nhận
- **Nhóm chủ đề:** Học bổng | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `LOW`
- **Trước cải tiến:** PASS (Điểm: 11/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 11/12, Sufficiency: `PARTIAL`, Faithfulness: `100%`, Latency: `88912ms`)

**Câu trả lời CŨ (Trước):**
> Trong tài liệu hiện có chỉ đề cập chính sách chung về học bổng Hoa Anh Đào 2026 dành cho khóa K26 [1], chưa có quy định chi tiết về số tiền hoặc mức học bổng cụ thể. 
> 
> Để biết thêm thông tin chi tiết về mức học bổng và thủ tục nhận, bạn vui lòng liên hệ:
> - **Phòng Tài chính Kế toán (Phòng 201)** hoặc bộ phận phụ trách Học bổng, khen thưởng (Cô Trần Thị Ni Na) để được hướng dẫn trực tiếp [4].

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Trong các tài liệu hiện có của Nhà trường chỉ đề cập thông tin chung về việc có nhiều suất học bổng giá trị cho khóa K26 [6] và chương trình trao gần 17 tỷ đồng học bổng cho tân sinh viên [7], nhưng chưa có quy định chi tiết về mức tiền hoặc giá trị cụ thể của từng loại học bổng. 
> 
> Để biết chính xác mức học bổng bạn có thể nhận được, vui lòng liên hệ trực tiếp với các đơn vị phụ trách để được hỗ trợ:
> - **Phòng Tài chính Kế toán (P.201):** Hỗ trợ về việc nhận học bổng, khen thưởng [2], [3].
> - **Đầu mối phụ trách học bổng:** Bạn có thể liên hệ qua các kênh thông tin chính thức hoặc cổng thông tin sinh viên của Nhà trường để được giải đáp chi tiết [2], [3].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Trong các tài liệu hiện có của Nhà trường chỉ đề cập thông tin chung về việc có nhiều suất học bổng *
- [x] *Để biết chính xác mức học bổng bạn có thể nhận được, vui lòng liên hệ trực tiếp với các đơn vị phụ t*
- [x] *- **Đầu mối phụ trách học bổng:** Bạn có thể liên hệ qua các kênh thông tin chính thức hoặc cổng thô*

**Nguồn sử dụng:** `[1] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[2] src-v2-015-d0-3`, `[3] src-v2-016-d0-3`, `[4] src-v2-009-d22-1`

---

#### [6] TC-SVQ-024: Muốn đăng ký học bổng thì làm thế nào?
- **Nhóm chủ đề:** Học bổng | **Ý định:** `PROCEDURE_GUIDANCE` | **Rủi ro:** `MEDIUM`
- **Trước cải tiến:** PASS (Điểm: 10/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 12/12, Sufficiency: `SUFFICIENT`, Faithfulness: `100%`, Latency: `18397ms`)

**Câu trả lời CŨ (Trước):**
> Trong tài liệu hiện có chỉ đề cập đến chính sách chung về học bổng (như học bổng dành cho tân sinh viên phân hiệu Đắk Lắk [1], học bổng K26 [3]) nhưng chưa có quy định chi tiết về quy trình hoặc thủ tục đăng ký cụ thể. 
> 
> Bạn vui lòng liên hệ trực tiếp với Phòng Công tác sinh viên hoặc bộ phận tuyển sinh của Nhà trường để được hướng dẫn chi tiết về điều kiện và cách thức đăng ký học bổng.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Để đăng ký học bổng, sinh viên có thể thực hiện theo các bước hướng dẫn và liên hệ bộ phận phụ trách sau đây:
> 
> * **Quyền lợi & Hướng dẫn hành động:** 
>   - Sinh viên có nhu cầu nộp hồ sơ, thắc mắc về học bổng hoặc cần cấp giấy xác nhận liên quan có thể liên hệ trực tiếp với **Cô Trần Thị Ni Na** (phụ trách học bổng, khen thưởng, hỗ trợ học phí) [2], [3].
>   - Ngoài ra, sinh viên có thể tra cứu thêm các thông tin chi tiết, biểu mẫu hoặc thông báo tuyển sinh, học bổng trực tuyến tại mục "Học bổng - Học phí" hoặc "Tra cứu trực tuyến" trên cổng thông tin chính thức của Nhà trường [4].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *- Sinh viên có nhu cầu nộp hồ sơ, thắc mắc về học bổng hoặc cần cấp giấy xác nhận liên quan có thể l*
- [x] *- Ngoài ra, sinh viên có thể tra cứu thêm các thông tin chi tiết, biểu mẫu hoặc thông báo tuyển sinh*

**Nguồn sử dụng:** `[1] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[2] src-v2-015-d0-3`, `[3] src-v2-016-d0-3`, `[4] src-v2-021-d0-1-x1`

---

#### [7] TC-SVQ-033: Điều kiện xét học bổng
- **Nhóm chủ đề:** Học bổng | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `LOW`
- **Trước cải tiến:** PASS (Điểm: 10/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 11/12, Sufficiency: `PARTIAL`, Faithfulness: `100%`, Latency: `66242ms`)

**Câu trả lời CŨ (Trước):**
> Trong tài liệu hiện có chỉ đề cập chính sách chung về học bổng (như quỹ học bổng năm 2026 và Học bổng Hoa Anh Đào cho khóa K26) [1], [5], chưa có quy định chi tiết về các tiêu chí cụ thể để xét học bổng [3]. 
> 
> Bạn vui lòng liên hệ trực tiếp với Phòng Tuyển sinh hoặc Phòng Công tác sinh viên qua số điện thoại 0236 351 9929 để được hướng dẫn chi tiết về điều kiện và thủ tục xét học bổng [1], [2].

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Trong tài liệu hiện có chỉ đề cập chính sách chung và các biểu mẫu, quy trình liên quan đến học phí và học bổng, chưa có quy định chi tiết về các tiêu chí và điều kiện cụ thể để xét học bổng [1]. 
> 
> Để được hướng dẫn chi tiết và chính xác về điều kiện xét học bổng, bạn vui lòng liên hệ các bộ phận đầu mối phụ trách sau:
> - **Phòng Tài chính Kế toán (P.201)**: Hỗ trợ về việc nhận học bổng và các khoản phí [5], [7].
> - **Cán bộ phụ trách học bổng, khen thưởng (Cô Trần Thị Ni Na)**: Hỗ trợ giải đáp các thủ tục về học bổng và khen thưởng [5], [7].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Trong tài liệu hiện có chỉ đề cập chính sách chung và các biểu mẫu, quy trình liên quan đến học phí *
- [x] *Để được hướng dẫn chi tiết và chính xác về điều kiện xét học bổng, bạn vui lòng liên hệ các bộ phận *
- [x] *- **Cán bộ phụ trách học bổng, khen thưởng (Cô Trần Thị Ni Na)**: Hỗ trợ giải đáp các thủ tục về học*

**Nguồn sử dụng:** `[1] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[2] src-v2-009-d22-1`, `[3] src-v2-009-d14-3`, `[4] src-v2-009-d14-4`

---

#### [8] TC-SVQ-022: em ở quê thuộc an toàn khu thì có miễn bhyt, mà ra Đà Nẵng học đại học thì em có nộp bhyt cùng với bảo hiểm thân thể, thì em không biết là số tiền bhyt của em có được hoàn lại hay là vẫn phải nộp ạ
- **Nhóm chủ đề:** BHYT / sức khỏe | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PASS (Điểm: 10/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 10/12, Sufficiency: `PARTIAL`, Faithfulness: `100%`, Latency: `13395ms`)

**Câu trả lời CŨ (Trước):**
> Trong tài liệu hiện có chỉ đề cập các biểu mẫu liên quan đến học phí và bảo hiểm y tế (như Giấy nhờ chi kiêm phiếu yêu cầu đóng học phí và BHYT) [1], cũng như thông tin liên hệ của phụ trách bộ phận Bảo hiểm y tế [2], [3], chưa có quy định chi tiết về trường hợp miễn giảm BHYT cho sinh viên ở vùng an toàn khu hoặc thủ tục hoàn lại số tiền BHYT đã nộp.
> 
> Để được giải đáp chính xác về trường hợp của bạn, bạn vui lòng liên hệ trực tiếp với Thầy **Phạm Ngọc Kề** (Phụ trách Bảo hiểm y tế/Bảo hiểm thân thể) qua số điện thoại **0905094118** [2], [3] hoặc liên hệ **Phòng Tài chính Kế toán (Phòng 201)** để được hỗ trợ kiểm tra chi tiết công nợ và các khoản thu.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Sinh viên thuộc vùng an toàn khu khi tham gia học tập tại trường vẫn cần đóng BHYT theo quy định chung, và Nhà trường có hỗ trợ quy trình, biểu mẫu liên quan đến việc thu nộp bảo hiểm qua Phòng Tài chính Kế toán và đầu mối phụ trách [1], [2]. 
> 
> Quy chế hiện hành của Nhà trường chưa quy định chi tiết về việc hoàn lại tiền BHYT đối với trường hợp sinh viên ở vùng an toàn khu [1], [2], [3]. 
> 
> Để được hướng dẫn chính xác về trường hợp của bạn (có được miễn, giảm hay hoàn lại tiền BHYT hay không), bạn vui lòng liên hệ trực tiếp với **Thầy Phạm Ngọc Kề** (Phụ trách Bảo hiểm y tế/Bảo hiểm thân thể) qua số điện thoại **0905094118** [1] hoặc liên hệ **Phòng Tài chính Kế toán (Phòng 201)** để được hỗ trợ kiểm tra chi tiết [1].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Sinh viên thuộc vùng an toàn khu khi tham gia học tập tại trường vẫn cần đóng BHYT theo quy định chu*
- [x] *Quy chế hiện hành của Nhà trường chưa quy định chi tiết về việc hoàn lại tiền BHYT đối với trường hợ*
- [x] *Để được hướng dẫn chính xác về trường hợp của bạn (có được miễn, giảm hay hoàn lại tiền BHYT hay khô*

**Nguồn sử dụng:** `[1] src-v2-016-d0-3`, `[2] src-v2-020-biểu_mẫu_-_học_bổng_học_ph237-1`, `[3] src-v2-015-d0-4`, `[4] src-v2-014-d0-1`

---

#### [9] TC-SVQ-055: Nghỉ bao nhiêu buổi là cấm thi vậy ạ
- **Nhóm chủ đề:** Thi cử / học lại | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `HIGH`
- **Trước cải tiến:** PASS (Điểm: 12/12, Sufficiency: `SUFFICIENT`)
- **Sau cải tiến:** **PASS** (Điểm: 12/12, Sufficiency: `SUFFICIENT`, Faithfulness: `100%`, Latency: `11195ms`)

**Câu trả lời CŨ (Trước):**
> Trong quy chế hiện hành của Nhà trường, không có quy định cụ thể về số buổi nghỉ học dẫn đến việc bị "cấm thi". 
> 
> Thay vào đó, các quy định liên quan đến việc vắng mặt trong buổi thi, kiểm tra và nghỉ học được áp dụng như sau:
> 
> * **Về việc vắng mặt thi hoặc kiểm tra:** Sinh viên vắng mặt trong buổi thi hoặc kiểm tra đánh giá mà không có lý do chính đáng sẽ nhận điểm 0 [3]. Trường hợp vắng mặt có lý do chính đáng sẽ được dự thi hoặc kiểm tra đánh giá ở một đợt khác và được tính điểm lần đầu [3].
> * **Về quy định nghỉ học chung:** 
>   - Khi nghỉ học, sinh viên phải có đơn xin phép do Trưởng khoa ký (hoặc do Thầy Cô phụ trách ký cho phép tại các cơ sở khác) [1], [2].
>   - Sinh viên tự ý nghỉ học 2 buổi/1 tuần hoặc 8 buổi/1 tháng sẽ bị cố vấn học tập thông tin về gia đình [1], [2].
>   - Sinh viên nghỉ liên tục từ 01 tháng trở lên hoặc không tham gia kiểm tra giữa học phần thì khoa sẽ thông báo về gia đình [1], [2].
> 
> **Hướng dẫn hành động:**
> Khi có việc cần vắng mặt hoặc gặp các vấn đề về lịch học, lịch thi, bạn cần chủ động liên hệ với **Cố vấn học tập** hoặc **Văn phòng Khoa** để được hướng dẫn làm đơn xin phép đúng quy định.

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Quy chế hiện hành của Nhà trường không quy định mức số buổi nghỉ học cụ thể dẫn đến việc "cấm thi", tuy nhiên có các quy định rõ về việc theo dõi chuyên cần và xử lý khi sinh viên nghỉ học như sau [1]:
> 
> * **Quy định về xin phép nghỉ:** Khi nghỉ học, sinh viên phải có đơn xin phép do Trưởng khoa ký (hoặc Thầy Cô phụ trách tại các cơ sở khác ký cho phép) [1]. 
> * **Mức độ nghỉ học và thông báo về gia đình:** 
>   - Tự ý nghỉ học **2 buổi/1 tuần** hoặc **8 buổi/1 tháng**: Cố vấn học tập sẽ thông tin về gia đình [1].
>   - Nghỉ liên tục **từ 01 tháng trở lên** hoặc **không tham gia kiểm tra giữa học phần**: Khoa sẽ thông báo về gia đình [1].
> 
> **Hướng dẫn hành động:**
> Để đảm bảo quyền lợi học tập và dự thi, bạn cần chú ý tham gia đầy đủ các buổi học, đi học đúng giờ và tuân thủ các quy định về kiểm tra giữa học phần [1]. Nếu có việc cá nhân cần nghỉ học dài hạn hoặc bảo lưu, bạn có thể tham khảo thủ tục xin nghỉ học tạm thời tại Khoa (Giáo vụ Khoa) hoặc liên hệ **Phòng Quản lý đào tạo & Công tác sinh viên (P.201)** để được hướng dẫn chi tiết hồ sơ và biểu mẫu [3], [5].

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Quy chế hiện hành của Nhà trường không quy định mức số buổi nghỉ học cụ thể dẫn đến việc "cấm thi", *
- [x] ** **Quy định về xin phép nghỉ:** Khi nghỉ học, sinh viên phải có đơn xin phép do Trưởng khoa ký (hoặ*
- [x] *- Tự ý nghỉ học **2 buổi/1 tuần** hoặc **8 buổi/1 tháng**: Cố vấn học tập sẽ thông tin về gia đình [*

**Nguồn sử dụng:** `[1] src-v2-008-d3-4`, `[2] src-v2-007-d0-4`, `[3] src-v2-015-d0-6`, `[4] src-v2-015-d0-10`

---

#### [10] TC-SVQ-009: Chuẩn đầu ra của ngành Ngôn ngữ Trung là sao vậy ạ?
- **Nhóm chủ đề:** Chuẩn đầu ra / tốt nghiệp | **Ý định:** `GENERAL_INFORMATION` | **Rủi ro:** `LOW`
- **Trước cải tiến:** PASS (Điểm: 10/12, Sufficiency: `PARTIAL`)
- **Sau cải tiến:** **PASS** (Điểm: 10/12, Sufficiency: `PARTIAL`, Faithfulness: `100%`, Latency: `33646ms`)

**Câu trả lời CŨ (Trước):**
> Mình chưa tìm thấy thông tin cụ thể về chuẩn đầu ra dành riêng cho ngành Ngôn ngữ Trung trong tài liệu hiện có (tài liệu chỉ quy định về chuẩn đầu ra ngoại ngữ áp dụng cho sinh viên không chuyên ngữ khóa 2024) [1]. 
> 
> Để nắm chính xác chuẩn đầu ra của ngành Ngôn ngữ Trung (thuộc khối chuyên ngữ), bạn vui lòng liên hệ Văn phòng Khoa hoặc Phòng Quản lý Đào tạo để được hướng dẫn chi tiết nhé!

**Câu trả lời MỚI (Sau - Grounded & NotebookLM Standard):**
> Sinh viên bậc Đại học hệ chính quy từ khóa 2024 trở đi tại Trường Đại học Đông Á khi tốt nghiệp cần đạt chuẩn đầu ra ngoại ngữ chung với năng lực tương đương Bậc 3/6 theo Khung năng lực ngoại ngữ 6 bậc dùng cho Việt Nam hoặc bậc B1 theo Khung tham chiếu về năng lực ngoại ngữ chung Châu Âu (CEFR) [6]. 
> 
> *Lưu ý:* Tài liệu hiện tại quy định cụ thể về chuẩn đầu ra ngoại ngữ áp dụng cho **sinh viên không chuyên ngữ** khóa 2024 (ví dụ: với tiếng Trung là đạt chứng chỉ HSK 3 hoặc qua kỳ thi chuẩn đầu ra của Nhà trường) [1, 3]. Hiện chưa có thông tin chi tiết riêng về chuẩn đầu ra chuyên sâu dành riêng cho ngành chuyên ngành Ngôn ngữ Trung trong tài liệu này. 
> 
> **Hướng dẫn hành động:**
> Bạn vui lòng liên hệ trực tiếp với **Văn phòng Khoa** quản lý ngành hoặc **Phòng Quản lý đào tạo** để được cung cấp thông tin chính xác nhất về chương trình và chuẩn đầu ra của chuyên ngành Ngôn ngữ Trung.

**Khẳng định đã được kiểm chứng (Verified Claims):**
- [x] *Sinh viên bậc Đại học hệ chính quy từ khóa 2024 trở đi tại Trường Đại học Đông Á khi tốt nghiệp cần *

**Nguồn sử dụng:** `[1] src-v2-018-các_chứng_chỉ_ngoại_ngữ_quốc_t-1`, `[2] src-v2-018-sinh_viên_đạt_chứng_chỉ_quốc_t-1`, `[3] src-v2-018-dkiện_xét_đạt_chuẩn_đầu_ra_ngo-1`, `[4] src-v2-018-chung_kết_h249ng_biện_tiếng_tr-1`

---
