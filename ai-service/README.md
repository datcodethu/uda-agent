# AI Service (RAG) - Trợ lý hỏi đáp quy chế

## 1. Cài đặt (Windows PowerShell)
```
cd ai-service
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # rồi mở .env, điền GOOGLE_API_KEY và đổi INTERNAL_API_KEY
```
Cần Python 3.10 trở lên. Dùng đúng tên model Gemini mà `rag_engine.py` hiện tại của bạn đang chạy được.

## 2. Test phần không cần mạng (làm trước tiên)
```
python -m unittest discover -s tests -v
```

## 3. Nạp tài liệu và hỏi thử bằng dòng lệnh
Đặt quy chế (.pdf có chữ hoặc .txt) vào `data/raw_documents/`, rồi:
```
python -m scripts.ingest_folder
python -m scripts.ask "Nợ học phí có đăng ký môn được không?"
```
LƯU Ý: Qdrant local chỉ cho 1 tiến trình dùng cùng lúc -> TẮT server trước khi chạy ingest_folder.
Muốn vừa chạy server vừa nạp: dùng API /v1/ingest, hoặc chạy Qdrant bằng Docker rồi đặt QDRANT_URL=http://localhost:6333.

## 4. Chạy server
```
uvicorn app.main:app --reload --port 8000
```
Mở http://localhost:8000/docs để thử API (nhấn Authorize/thêm header X-Internal-Key).
- POST /v1/ingest            (form: file, doc_name, status)
- GET  /v1/ingest/documents
- DELETE /v1/ingest/documents/{doc_name}
- POST /v1/query             -> JSON một lần
- POST /v1/query/stream      -> SSE: event token / sources / verify / done / error
- GET  /v1/health

## 5. Đánh giá (phần nghiên cứu)
```
python -m evaluation.run_eval --mode dense  --top-k 5
python -m evaluation.run_eval --mode bm25   --top-k 5
python -m evaluation.run_eval --mode hybrid --top-k 5
python -m evaluation.run_eval --mode hybrid --with-llm
```
Kết quả JSON lưu trong `evaluation/benchmarks_result/`. Phần truy xuất không gọi LLM nên chạy thoải mái.
Chọn MIN_DENSE_SCORE: so `avg_best_score_answerable` với `avg_best_score_out_of_scope`, đặt ngưỡng nằm giữa, rồi chạy lại.

## 6. Thay dữ liệu mẫu
`data/raw_documents/quy_che_mau_demo.txt` và hai file trong `evaluation/test_datasets/` là DỮ LIỆU GIẢ LẬP.
Thay bằng quy chế thật và câu hỏi thật từ form khảo sát (ghi `expected_dieu` đúng theo văn bản thật).

## Trạng thái kiểm thử
- Đã chạy: 20 unit test cho chunker, cleaner, viết tắt, RRF, kiểm chứng số liệu, tách chữ từ khối Gemini.
- CHƯA chạy với Gemini/Qdrant thật (nơi tạo ra file này không có mạng): dense_search, llm_adapter, API, run_eval, ragas_evaluator.
  Lỗi đầu tiên có thể gặp ở tên model hoặc tham số task_type của embedding -> sửa trong .env / dense_search.py.
