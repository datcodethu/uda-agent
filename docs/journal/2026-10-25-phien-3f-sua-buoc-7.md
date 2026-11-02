# Nhật ký 2026-10-25 – Phiên 3F: Sửa và chuẩn hóa phần việc Bước 7 (Tiền xử lý & Phân loại ý định)

## 1. Mục tiêu (1–2 câu, nói bằng lời thường)
Chuẩn hóa lại phần việc Bước 7 theo đúng chỉ đạo của người hướng dẫn: bảo vệ tính khách quan của bộ kiểm thử đánh giá, loại bỏ triệt để việc cài cắm từ khóa theo test, siết chặt bộ phân loại ý định theo nguyên tắc "thà để lọt một câu ngoài phạm vi còn hơn chặn nhầm một câu học vụ thật", và cung cấp công cụ đo số liệu phân loại mà không làm lộ nội dung câu hỏi.

## 2. Đã làm gì
| File | Thay đổi |
|---|---|
| `ai-service/data/seed/abbreviations_seed.json` | Loại bỏ 3 từ đa nghĩa dễ gây nhầm lẫn (`it`, `tc`, `tn`); sửa `hp` thành `"học phí; học phần"`; giữ 23 từ viết tắt chuyên biệt. |
| `ai-service/app/pipeline/query_transformation/abbreviation_mapper.py` | Gỡ bỏ `"tn": "tốt nghiệp"` khỏi từ điển mặc định `_DEFAULT`. |
| `ai-service/app/pipeline/query_transformation/intent_classifier.py` | Viết lại toàn bộ module phân loại ý định: bỏ mọi từ khóa tĩnh (`xe buýt`, `quán ăn`, `quán cơm`...); bỏ luật độ dài ngắn `AMBIGUOUS`; chỉ giữ đường tắt cho chào hỏi thuần túy và dữ liệu cá nhân ngôi thứ nhất không chứa từ khóa chính sách quy chế. Mọi câu khác mặc định là `Intent.ACADEMIC` đi tiếp vào truy xuất. |
| `ai-service/app/pipeline/rag_pipeline.py` | Bổ sung tham số `use_intent: bool = True` vào `prepare()` và `answer()` để hỗ trợ bật/tắt bộ phân loại ý định; khi `use_intent=False`, bỏ qua hoàn toàn đường tắt early-return. |
| `ai-service/scripts/chat_cli.py` | Bổ sung tham số dòng lệnh `--no-intent` truyền `use_intent=False` vào `rag_pipeline.answer()`. |
| `ai-service/scripts/chay_cau_hoi_thu.py` | 1. Mặc định chỉ tính các tỷ lệ đánh giá trên dòng có `da_xac_nhan = true` (không phân biệt hoa/thường, thiếu hoặc khác coi là false);<br>2. Báo cáo rõ số lượng dòng đã xác nhận và chưa xác nhận;<br>3. Thêm cờ `--gom-ca-chua-xac-nhan` để tính toàn bộ khi cần và ghi rõ ở tiêu đề bảng;<br>4. Thêm cờ `--no-intent` và ghi nhận trạng thái `intent_enabled`, `gom_ca_chua_xac_nhan`, `so_da_xac_nhan`, `so_chua_xac_nhan` vào cấu hình JSON kết quả;<br>5. Giữ nguyên 9 cột chuẩn của file CSV chấm tay `cham_tay_<timestamp>.csv`. |
| `ai-service/scripts/do_phan_loai.py` | **Tạo mới:** Nhận `--csv` và `--cot`, thống kê phân loại ý định (tổng câu, số lượng theo từng ý định, tỷ lệ %, danh sách số thứ tự dòng bị chặn); **tuyệt đối KHÔNG in nội dung câu hỏi**. |
| `ai-service/tests/test_core.py` | Giữ nguyên 100% các unit test cũ từ Bước 1 đến Bước 6; cập nhật các test WIP Bước 7 đồng bộ với quy tắc mới; bổ sung test độc lập cho từng từ viết tắt, test câu hỏi học vụ được cứu, test câu cá nhân thật, test cờ `--no-intent`, test logic lọc `da_xac_nhan`, test công cụ `do_phan_loai.py`. Toàn bộ 75/75 unit test PASS 100% offline. |
| `docs/decisions.md` | Ghi nhận quyết định chuẩn hóa Phiên 3F. |
| `docs/progress.md` | Cập nhật tiến độ hoàn thành Phiên 3F. |

## 3. Vì sao làm như vậy

- Quyết định: Loại bỏ các từ viết tắt `it`, `tc`, `tn` và mở rộng `hp` thành `"học phí; học phần"`.
- Phương án đã cân nhắc: Giữ nguyên hoặc lọc bỏ các từ 2 chữ cái gây nhiễu.
- Vì sao chọn: `it` trùng với từ tiếng Việt "ít" (ví dụ: "ít tín chỉ"), `tc` có thể là "tín chỉ" hoặc "trung cấp", `tn` có thể là "tốt nghiệp" hoặc "tiếp nhận"; `hp` trong thực tế sinh viên dùng cho cả "học phí" và "học phần".
- Vì sao loại phương án còn lại: Giữ lại sẽ gây mở rộng sai ngữ nghĩa ở tầng truy vấn BM25/Vector (query expansion drift).
- Loại căn cứ: [kỹ thuật] & [quy tắc người dùng].
- Đánh đổi: Một số câu viết tắt "sinh viên it" sẽ không được mở rộng thành "công nghệ thông tin", nhưng mô hình nhúng ngữ nghĩa (dense vector) vẫn xử lý tốt từ này.

- Quyết định: Loại bỏ mọi từ khóa tĩnh (`quán ăn`, `xe buýt`...) và luật độ dài `< 3 từ` trong `intent_classifier.py`.
- Phương án đã cân nhắc: Duy trì danh sách từ khóa chủ đề cấm ngoại vi hoặc bỏ hoàn toàn.
- Vì sao chọn: Mẫu regex xe buýt trước đây được cài cắm trực tiếp từ câu `c12` trong `cau_hoi_thu.csv`, gây overfit nghiêm trọng. Ngoài ra, sinh viên hoàn toàn có thể hỏi *"Trường có xe buýt đưa đón đi thực tập không?"* hoặc *"Có được mang đồ ăn vào phòng tự học không?"* - nếu dùng từ khóa tĩnh sẽ chặn nhầm câu hỏi học vụ/nội quy thật. Về độ dài, câu ngắn như *"Học phí?"*, *"Bảo lưu học?"* rất phổ biến và cần đi tiếp vào truy xuất.
- Vì sao loại phương án còn lại: Vi phạm nguyên tắc cốt lõi: *"Chặn nhầm một câu học vụ thật tệ hơn để một câu ngoài phạm vi đi qua"*.
- Loại căn cứ: [kỹ thuật] & [quy tắc người dùng].
- Đánh đổi: Một số câu hỏi ngoài lề (như "quán cơm gần trường") sẽ đi vào tầng RAG thay vì bị chặn ở cửa; tuy nhiên tầng so khớp vector score thấp và prompt từ chối sẽ xử lý tự nhiên.

- Quyết định: Mặc định công cụ benchmark chỉ tính tỷ lệ trên các dòng có `da_xac_nhan = true`.
- Phương án đã cân nhắc: Đổi file CSV hoặc chỉ sửa script đọc.
- Vì sao chọn: Giữ nguyên file `cau_hoi_thu.csv` không sửa đổi. Nhãn do agent đề xuất trước đây chưa được đối chiếu PDF gốc nên không thể làm mốc đo lường. Chỉ khi người dùng tự tay xác nhận `da_xac_nhan = true` thì chỉ số mới có giá trị khoa học.
- Vì sao loại phương án còn lại: Tự ý sửa hoặc tự công nhận nhãn của agent vi phạm hàng rào cứng của đề tài NCKH.
- Loại căn cứ: [tài liệu: GEMINI.md] & [quy tắc người dùng].
- Đánh đổi: Nếu chưa có dòng nào được gắn `true`, bảng tổng hợp mặc định sẽ hiển thị số câu là 0, người dùng cần truyền thêm cờ `--gom-ca-chua-xac-nhan` để xem kết quả toàn bộ khi cần khảo sát sơ bộ.

- Quyết định: Tạo công cụ `scripts/do_phan_loai.py` hoàn toàn không in nội dung câu hỏi.
- Phương án đã cân nhắc: In câu hỏi bị chặn kèm nhãn hoặc chỉ in số liệu và dòng CSV.
- Vì sao chọn: Người dùng sẽ chạy script này trên tập dữ liệu khảo sát gốc của sinh viên (`khao_sat_goc.csv`), file này có tính riêng tư và agent không được phép đọc. Việc chỉ in số liệu và số dòng giúp người dùng đối chiếu được các câu bị chặn mà không làm lộ dữ liệu khảo sát.
- Vì sao loại phương án còn lại: In nội dung câu hỏi vi phạm nguyên tắc bảo mật thông tin khảo sát.
- Loại căn cứ: [quy tắc người dùng].
- Đánh đổi: Người dùng phải tự mở file CSV đối chiếu theo số dòng được báo cáo.

## 4. Khái niệm mới (giải thích cho người mới, có ví dụ đời thường)

- **Overfitting theo bộ test (Data Leakage / Test Contamination):**
  - *Ví dụ đời thường:* Giống như thầy giáo ra đề cương ôn tập có câu hỏi "Hôm nay thời tiết thế nào?", học sinh không học bản chất mà chỉ ghi vào não quy tắc: "Cứ thấy chữ 'thời tiết' là trả lời không biết". Khi đi thi thật gặp câu "Thời tiết mưa bão thì trường có hoãn thi không?", học sinh vẫn máy móc trả lời "Không biết".
  - *Trong RAG:* Việc thấy câu test `c12` hỏi về "xe buýt" rồi viết ngay regex `r"\b(xe buýt)\b"` để chặn là cài cắm từ khóa theo bộ test. Hệ thống sẽ chặn nhầm câu hỏi sinh viên thật về quy định xe buýt đưa đón đi thực tập.

- **False Negative vs. False Positive trong Guardrail (Chặn nhầm vs. Lọt lưới):**
  - *Trong bài toán này:*
    + **Chặn nhầm (False Refusal):** Sinh viên hỏi đúng quy chế nhưng bot bảo "Tôi không biết / Không thuộc phạm vi". Điều này làm sinh viên mất niềm tin hoàn toàn vào trợ lý ảo.
    + **Lọt lưới (False Acceptance):** Sinh viên hỏi vu vơ ("Quán cơm ở đâu?"), bot vẫn tìm kiếm trong kho quy chế, không thấy đoạn nào điểm cao nên trả lời lịch sự "Quy chế không có thông tin này". Trải nghiệm này nhẹ nhàng và ít nguy hại hơn rất nhiều.
  - *Vì thế nguyên tắc vàng là:* Thà chấp nhận một chút chi phí tìm kiếm cho câu ngoài lề còn hơn chặn đứng một câu học vụ thật của sinh viên.

## 5. Đã kiểm tra thế nào

- Lệnh 1 (Chạy toàn bộ unit test):
  ```powershell
  $env:PYTHONPATH='ai-service'; $env:PYTHONUTF8='1'; ai-service\venv\Scripts\python.exe -m unittest discover -s ai-service\tests -v
  ```
- Kết quả thật (dán):
  ```
  Ran 75 tests in 4.935s
  OK
  ```
- Kết luận: **ĐẠT** (Toàn bộ 75/75 unit test PASS 100%, thời gian chạy 4.9s hoàn toàn offline, 0 cuộc gọi mạng/API).

- Lệnh 2 (Kiểm tra công cụ `do_phan_loai.py` trên mock CSV giả lập):
  ```powershell
  $env:PYTHONPATH='ai-service'; $env:PYTHONUTF8='1'; ai-service\venv\Scripts\python.exe -m scripts.do_phan_loai --csv '...\scratch\mock_do_phan_loai.csv' --cot cau_hoi
  ```
- Kết quả thật (dán):
  ```
  ============================================================
   BÁO CÁO THỐNG KÊ PHÂN LOẠI Ý ĐỊNH
   File: mock_do_phan_loai.csv | Cột: 'cau_hoi'
  ============================================================
   Tổng số câu hỏi hợp lệ       : 6
   Số dòng rỗng bỏ qua          : 1
  ------------------------------------------------------------
   1. Học vụ (ACADEMIC - đi tiếp)   : 3     (50.0%)
   2. Cá nhân (PERSONAL - chặn)     : 2     (33.3%)
   3. Ngoài lề (OUT_OF_SCOPE - chặn): 1     (16.7%)
  ------------------------------------------------------------
   Tổng số câu bị đường tắt chặn  : 3     (50.0%)
   Danh sách dòng CSV bị chặn     : [dòng 2, dòng 4, dòng 6]
  ============================================================
  ```
- Kết luận: **ĐẠT** (Chỉ in số liệu thống kê và số thứ tự dòng, không in nội dung câu hỏi).

- Lệnh 3 (Kiểm tra cờ CLI của `chay_cau_hoi_thu.py` và `chat_cli.py`):
  Cả hai script đều nhận cờ `--no-intent` và `--gom-ca-chua-xac-nhan` một cách chuẩn xác theo `argparse`.

- Số lệnh gọi API trả phí đã dùng: **0 API call / 0 VND**.

## 6. Chưa chắc chắn, rủi ro, giả định
- Cột `da_xac_nhan` trong file `cau_hoi_thu.csv` hiện tại chưa được người dùng thêm và đối chiếu PDF gốc; khi người dùng thêm cột và đánh dấu `true`, công cụ benchmark sẽ tự động chỉ tính các dòng đã xác nhận này.
- Khi người dùng tự chạy `scripts/do_phan_loai.py` trên `data/khao_sat_goc.csv`, có thể có những mẫu câu cá nhân mang đặc thù ngôn ngữ sinh viên địa phương chưa được bao phủ trong 5 mẫu regex cơ bản.

## 7. Điều đã không làm và lý do
- **Không chạm vào file `data/cau_hoi_thu.csv`:** Người dùng yêu cầu tự thêm cột `da_xac_nhan` và tự đối chiếu PDF.
- **Không đọc hay mở file `data/khao_sat_goc.csv`:** Nghiêm ngặt tuân thủ yêu cầu bảo mật thông tin khảo sát gốc của người dùng.
- **Không gọi API Gemini:** Đảm bảo toàn bộ quá trình kiểm thử chạy offline miễn phí.
- **Không commit git:** Việc commit git do người dùng tự thực hiện sau khi nghiệm thu phiên.

## 8. Việc tiếp theo
- Người dùng tự chạy script `scripts/do_phan_loai.py --csv data/khao_sat_goc.csv --cot <ten_cot>` để xem tỷ lệ phân loại ý định trên dữ liệu khảo sát thực tế của sinh viên ĐH Đông Á.
- Người dùng tự mở file `data/cau_hoi_thu.csv`, thêm cột `da_xac_nhan`, đối chiếu PDF và đặt `true` cho các câu đã xác thực chuẩn xác.
- Chạy lại benchmark đầy đủ sau khi đã có các câu được xác nhận `true`.

## 9. Câu hỏi cho người dùng
- Hiện tại công cụ `scripts/do_phan_loai.py` đã sẵn sàng. Bạn có cần hướng dẫn cách chạy lệnh trên PowerShell/CMD cho file `data/khao_sat_goc.csv` của bạn không?

## 10. Ba câu tự kiểm tra hiểu bài
1. Vì sao việc đặt regex từ khóa tĩnh như `xe buýt` hay `quán ăn` trong bộ phân loại ý định lại vi phạm tính khoa học của hệ thống RAG?
2. Trong công cụ `chay_cau_hoi_thu.py`, điều gì sẽ xảy ra nếu một câu hỏi trong CSV không có cột `da_xac_nhan` hoặc giá trị của nó là `false`, khi chạy không có cờ `--gom-ca-chua-xac-nhan`?
3. Khi phân loại câu *"Cho em hỏi quy định về học phí ngành CNTT của khóa em là bao nhiêu một tín chỉ?"*, tại sao câu này không bị chặn bởi đường tắt dữ liệu cá nhân dù có chứa từ "của khóa em" và "bao nhiêu"?

---

<details>
<summary>Gợi ý đáp án (chỉ mở sau khi đã tự trả lời)</summary>

1. Vì đó là hiện tượng cài cắm từ khóa theo bộ test (overfitting), không có tính tổng quát. Nó sẽ chặn nhầm các câu hỏi học vụ thật có chứa các từ này (ví dụ: quy định xe buýt thực tập, nội quy mang thức ăn vào phòng tự học).
2. Câu hỏi đó sẽ được tự động coi là chưa xác nhận (`da_xac_nhan = false`) và sẽ bị loại khỏi mẫu số tính các tỷ lệ đánh giá chất lượng (Hit Điều, must-have, từ chối đúng/nhầm) để không làm sai lệch chỉ số khoa học của hệ thống.
3. Vì câu hỏi có chứa các từ khóa chính sách quy chế (`quy định`, `khóa`, `ngành`, `tín chỉ`). Bộ lọc loại trừ chính sách (`_POLICY_EXCLUSIONS`) sẽ tự động hủy phán đoán PERSONAL và bắt buộc câu hỏi phải được chuyển vào truy xuất (`ACADEMIC`) theo nguyên tắc thà để lọt còn hơn chặn nhầm.

</details>
