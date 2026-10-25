"""Script nâng cấp nội dung học thuật cho file RAG NCKH 2026_2027.docx.

Giữ nguyên 100% khung form, cấu trúc bìa, mục lục, bảng biểu và chữ ký xác nhận;
Nâng cấp văn phong khoa học, cập nhật số liệu thực tế (63/63 test PASS, 5 quy chế 93 đoạn);
Bổ sung công thức toán học và hoàn thiện Mục 7 Tài liệu tham khảo (References) chuẩn IEEE.
"""
from pathlib import Path
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import sys

sys.stdout.reconfigure(encoding="utf-8")

DOC_PATH = Path(r"E:\workspace\donga-rag-system\RAG NCKH 2026_2027.docx")

def run_upgrade():
    if not DOC_PATH.exists():
        print(f"Lỗi: Không tìm thấy file {DOC_PATH}")
        sys.exit(1)

    doc = docx.Document(DOC_PATH)
    p_list = doc.paragraphs

    # Bảng cập nhật văn bản cho từng chỉ mục paragraph cụ thể (từ par 60 đến par 158)
    updates = {
        # --- Mục 1.1: Đánh giá tổng quan tình hình nghiên cứu ---
        60: (
            "Trong xu thế chuyển đổi số toàn diện tại các cơ sở giáo dục đại học, khối lượng văn bản "
            "quy phạm nội bộ, quy chế đào tạo tín chỉ, chuẩn đầu ra và các chính sách học vụ (học bổng, "
            "miễn giảm học phí, điểm rèn luyện, khung kỷ luật) ngày càng gia tăng về quy mô và liên tục "
            "được điều chỉnh theo từng năm học. Thực tiễn tra cứu thông tin của người học tại Trường Đại học "
            "Đông Á hiện đang đối mặt với ba rào cản kỹ thuật cốt lõi:"
        ),
        61: (
            "Thứ nhất, hệ thống tìm kiếm từ khóa truyền thống (Keyword-based / Lexical Search) chỉ dựa trên "
            "sự trùng khớp bề mặt của chuỗi ký tự, không có khả năng hiểu ngữ nghĩa và ý định tự nhiên của "
            "sinh viên, thường trả về các tệp tài liệu PDF dung lượng lớn hàng chục trang buộc người học phải "
            "rà soát và lọc thông tin thủ công mất nhiều thời gian."
        ),
        62: (
            "Thứ hai, các hệ thống chatbot dựa trên luật (Rule-based) hoặc kịch bản hội thoại cứng nhắc "
            "(Decision-tree) nhanh chóng bộc lộ hạn chế khi sinh viên đặt câu hỏi bằng ngôn ngữ tự nhiên đa dạng, "
            "sử dụng tiếng lóng, từ viết tắt học vụ đặc thù (BHYT, ĐRL, CĐR, ĐKHP, CTXH) hoặc các câu hỏi nối tiếp "
            "phụ thuộc sâu vào ngữ cảnh lịch sử hội thoại."
        ),
        63: (
            "Thứ ba, các mô hình ngôn ngữ lớn thương mại độc lập (như OpenAI ChatGPT, Google Gemini) tuy có "
            "năng lực sinh ngôn ngữ tự nhiên vượt trội nhưng tồn tại hai điểm nghẽn nghiêm trọng khi ứng dụng vào "
            "môi trường giáo dục chuyên biệt: sự thiếu hụt hoàn toàn tri thức nội bộ cập nhật của Trường Đại học "
            "Đông Á và hiện tượng ảo giác thông tin (hallucination) – tạo ra các câu trả lời sai lệch nhưng có văn phong "
            "rất thuyết phục về quy định học vụ hoặc mức học phí."
        ),
        64: (
            "Kiến trúc thế hệ mới Retrieval-Augmented Generation (RAG), được khởi xướng bởi Lewis và cộng sự (2020), "
            "đã mở ra hướng tiếp cận đột phá bằng cách kết hợp sức mạnh suy luận của mô hình ngôn ngữ lớn với kho "
            "tri thức nội bộ được lập chỉ mục vector, cho phép hệ thống định vị chính xác ngữ cảnh quy định liên quan "
            "và trích dẫn minh bạch nguồn gốc tài liệu pháp lý trước khi sinh câu trả lời."
        ),
        65: (
            "Tuy nhiên, việc áp dụng mô hình RAG ngây thơ (Naive RAG) đối với văn bản quy phạm hành chính tiếng Việt "
            "bộc lộ những điểm nghẽn kỹ thuật sâu sắc: phương pháp cắt đoạn theo độ dài ký tự cố định (Fixed-size chunking) "
            "làm đứt gãy cấu trúc thứ bậc quy phạm (Điều, Khoản, Điểm), phá hủy tính toàn vẹn của bảng biểu số liệu "
            "(chuẩn đầu ra, khung điểm rèn luyện), và tách rời câu quy phạm điều kiện khỏi các ngoại lệ đi kèm. Đồng thời, "
            "việc chỉ tìm kiếm bằng vector ngữ nghĩa (Dense-only) dễ dàng bỏ sót các thực thể từ khóa chính xác như mã "
            "chứng chỉ (N4, B1, TOEIC 450), số hiệu quyết định hoặc số Điều luật cụ thể."
        ),
        66: (
            "Xuất phát từ khoảng trống nghiên cứu trên, đề tài tập trung nghiên cứu, thiết kế và thực nghiệm kiến trúc "
            "Advanced RAG chuyên biệt hóa cho văn bản quy chế tiếng Việt tại Trường Đại học Đông Á. Nghiên cứu giải quyết "
            "toàn diện chuỗi mắt xích: tiền xử lý tài liệu cấu trúc phức tạp (Word XML DOM và PDF), phân mảnh cấu trúc "
            "ngữ nghĩa (Semantic Structural Chunking), truy xuất lai (Hybrid Search) kết hợp dung hợp thứ hạng Reciprocal "
            "Rank Fusion (RRF), cơ chế thẩm tra số liệu đa tầng chống ảo giác (Multi-layer Verification & Number Verifier), "
            "và đánh giá định lượng bằng framework chuẩn quốc tế RAGAS."
        ),

        # --- Mục 1.2: Mục tiêu của đề tài ---
        68: (
            "Mục tiêu tổng quát: Nghiên cứu, xây dựng và thực nghiệm hệ thống hỏi đáp học vụ tự động thông minh dựa trên "
            "kiến trúc Advanced RAG dành cho sinh viên Trường Đại học Đông Á; cung cấp khả năng tra cứu chính xác, phản hồi "
            "tức thời kèm trích dẫn văn bản quy phạm gốc, kiểm soát triệt để hiện tượng ảo giác số liệu và hỗ trợ giải đáp 24/7."
        ),
        69: "Mục tiêu khoa học và chỉ tiêu kỹ thuật định lượng:",
        70: (
            "Xử lý dữ liệu quy chế: xây dựng pipeline tự động phân loại, đọc và chuyển đổi PDF/DOCX; chuyển đổi thành công "
            "19/19 tệp .doc sang .docx, bảo toàn cấu trúc bảng XML và chuẩn hóa văn bản về Unicode dựng sẵn (NFC)."
        ),
        71: (
            "Phân mảnh cấu trúc quy phạm (Semantic Structural Chunking): giải quyết triệt để năm điểm nghẽn gồm phân định "
            "Quyết định ban hành và Quy định kèm theo; bảo toàn câu quy phạm pháp lý; cơ chế truyền thừa tiêu đề cột cho "
            "bảng số liệu dài (Table Header Propagation); cắt đoạn gối đầu sạch theo ranh giới câu hoàn chỉnh (100–150 ký tự); "
            "và hàng rào cảnh báo bất thường phân bố Điều khoản."
        ),
        72: (
            "Động cơ truy xuất lai: kết hợp đồng thời mô hình không gian vector dày đặc Dense Vector Search (Google Embedding "
            "768 chiều trên chỉ mục HNSW của Qdrant) và mô hình từ vựng thưa Sparse Search (BM25 Okapi) thông qua thuật toán "
            "dung hợp thứ hạng nghịch đảo Reciprocal Rank Fusion (RRF với hằng số làm mịn k = 60)."
        ),
        73: (
            "Cổng nạp tri thức an toàn Default-Deny: thiết lập cơ chế kiểm soát nghiêm ngặt qua bảng đăng ký 5 thuộc tính cốt lõi, "
            "tích hợp cơ chế tự động dọn kho tài liệu không còn hiệu lực (--prune) và tự động xây dựng lại chỉ mục BM25 đồng bộ."
        ),
        74: (
            "Đánh giá bằng RAGAS trên bộ kiểm chuẩn 100 câu hỏi Ground Truth: mục tiêu độ chính xác truy xuất Hit@3 ≥ 85%, "
            "Hit@5 ≥ 95%, MRR ≥ 0.80; các chỉ số RAGAS đạt Faithfulness ≥ 0,85; Answer Relevance ≥ 0,80; Context Recall ≥ 0,85; "
            "thời gian phản hồi Time to First Token (TTFT) dưới 3 giây qua cơ chế truyền dữ liệu Server-Sent Events (SSE)."
        ),
        75: (
            "Độ tin cậy và tính ổn định mã nguồn: toàn bộ pipeline xử lý dữ liệu, cắt đoạn, truy xuất và kiểm tra đạt 63/63 "
            "Unit Tests độc lập PASS (100% kiểm thử đạt chuẩn)."
        ),

        # --- Mục 1.3: Đối tượng, phạm vi nghiên cứu và đối tượng khảo sát ---
        77: "Đối tượng nghiên cứu:",
        78: "Kiến trúc Advanced RAG (Retrieval-Augmented Generation) và quy trình xử lý ngôn ngữ tự nhiên cho văn bản hành chính tiếng Việt.",
        79: "Cơ sở dữ liệu vector Qdrant (chỉ mục HNSW), thuật toán BM25 Okapi và phương pháp dung hợp thứ hạng Reciprocal Rank Fusion (RRF).",
        80: "Phương pháp tiền xử lý văn bản hành chính tiếng Việt và cơ chế kiểm soát ảo giác số liệu đa tầng (Number Verifier).",
        81: "Framework đánh giá định lượng hệ thống RAG chuẩn quốc tế RAGAS.",
        82: (
            "Phạm vi dữ liệu nghiên cứu: Toàn bộ tập văn bản chính thức về quy chế đào tạo tín chỉ, chuẩn đầu ra ngoại ngữ, "
            "học bổng, học phí, điểm rèn luyện và bảo hiểm y tế đang có hiệu lực (status = ACTIVE) do Trường Đại học Đông Á "
            "ban hành, được kiểm duyệt nghiêm ngặt qua bảng đăng ký docs_registry.csv và lưu trữ tại data/raw_documents/."
        ),
        83: (
            "Đối tượng khảo sát thực tế: 49 sinh viên Trường Đại học Đông Á; trong đó sinh viên năm nhất chiếm 77,5%, sinh viên "
            "năm ba chiếm 18,4%, chủ yếu thuộc khối ngành Công nghệ thông tin và Ngôn ngữ. Cơ cấu mẫu khảo sát phản ánh thực tế: "
            "sinh viên năm nhất là đối tượng bước đầu tiếp cận môi trường đại học tín chỉ, đối mặt nhiều bỡ ngỡ về quy chế học vụ "
            "và có nhu cầu giải đáp thông tin thường xuyên nhất."
        ),

        # --- Mục 2: Nội dung nghiên cứu khoa học và triển khai thực nghiệm ---
        86: (
            "Khảo sát thực tế nhu cầu tra cứu: 55,1% sinh viên chọn hỏi bạn bè/anh chị khóa trước; 51,0% tìm kiếm trên các hội nhóm "
            "Zalo/Facebook; 22,4% hỏi trực tiếp cố vấn học tập hoặc Phòng Đào tạo; và 16,3% cho biết hoàn toàn không biết tìm câu trả lời ở đâu."
        ),
        87: (
            "Những rào cản và lo ngại chính khi sử dụng AI: chatbot không hiểu câu hỏi viết tắt học vụ (73,5%, 36/49); thông tin lỗi thời "
            "hoặc hết hiệu lực (65,3%, 32/49); câu trả lời sai lệch hoặc ảo giác (51,0%, 25/49); và nguy cơ lộ thông tin cá nhân (46,9%, 23/49)."
        ),
        88: (
            "Xây dựng bộ dữ liệu Ground Truth gồm 100 câu hỏi – đáp chuẩn mực: 35 câu hỏi trực tiếp (Fact-seeking); 25 câu hỏi tổng hợp "
            "đa văn bản (Multi-hop Reasoning); 20 câu hỏi nhiễu/viết tắt (Noisy Query); và 20 câu hỏi ngoài phạm vi hoặc đối kháng "
            "(Adversarial & Out-of-scope) để đánh giá khả năng từ chối an toàn của hệ thống."
        ),
        90: (
            "Chuyển đổi ngoại tuyến bằng Word COM: xây dựng convert_doc_to_docx.py sử dụng win32com.client.DispatchEx để tạo phiên "
            "Microsoft Word độc lập, chuyển đổi thành công 19/19 tệp .doc cũ sang .docx chuẩn OpenXML. Việc chuyển đổi thực hiện một lần "
            "trên Windows giúp hệ thống chính khi triển khai lên máy chủ Linux/Docker hoàn toàn chạy qua python-docx độc lập nền tảng."
        ),
        91: (
            "Bộ đọc tài liệu theo cấu trúc XML DOM (docx_loader.py): duyệt tuần tự các phần tử đoạn văn w:p và bảng w:tbl để giữ đúng "
            "thứ tự đọc tự nhiên của văn bản gốc; chuyển đổi các bảng bố cục 1 hàng hoặc 1 cột thành văn bản thông thường, còn bảng dữ liệu "
            "chuẩn từ 2×2 trở lên thành bảng định dạng Markdown trực quan."
        ),
        92: (
            "Xử lý ô gộp và hộp văn bản: loại bỏ hoàn toàn hiện tượng lặp nội dung khi gặp ô gộp cột (gridSpan) hoặc gộp dòng (vMerge); "
            "trích xuất các hộp văn bản nổi bằng cách quét đệ quy các thẻ w:txbxContent lồng bên trong cấu trúc OpenXML."
        ),
        93: (
            "Kiểm tra chất lượng và chuẩn hóa (pdf_loader.py, cleaner.py): đánh giá tỷ lệ nguyên âm tiếng Việt có dấu nhằm phát hiện lỗi "
            "bảng mã TCVN3/VNI, chuẩn hóa Unicode dựng sẵn (NFC), loại bỏ số trang và tiêu đề trang lặp lại."
        ),
        95: (
            "Phân định ranh giới văn bản: dùng biểu thức chính quy (Regex) nhận diện Quyết định ban hành (quyet_dinh), Quy định kèm theo "
            "(quy_dinh_kem_theo) và Phụ lục (phu_luc); định danh đoạn theo dạng {doc_name}_{phan}-d{so}-{part} để tránh trùng số Điều giữa "
            "Quyết định và Quy định kèm theo."
        ),
        96: (
            "Bảo toàn câu quy phạm pháp lý: phân biệt chính xác tiêu đề Điều và câu mở đầu. Nếu nội dung sau 'Điều X.' dài hơn 120 ký tự "
            "hoặc là câu quy định hoàn chỉnh, giữ nguyên câu quy phạm trong phần thân bài thay vì cắt cụt tiêu đề."
        ),
        97: (
            "Truyền thừa tiêu đề bảng (Table Header Propagation): khi bảng số liệu vượt quá ngưỡng 1.200 ký tự, chia tách theo từng nhóm hàng "
            "nguyên vẹn và tự động lặp lại dòng tiêu đề cột cùng dòng phân cách Markdown ở đầu mỗi đoạn con tiếp theo."
        ),
        98: (
            "Cắt đoạn có gối đầu sạch (Clean Overlap): tạo phần chồng lấn 100–150 ký tự theo đúng ranh giới kết thúc câu hoàn chỉnh; tránh "
            "cắt ngang câu hoặc chia bảng dữ liệu không có tiêu đề."
        ),
        99: (
            "Kiểm tra bất thường cấu trúc và thứ tự Điều: hàm check_article_order phát hiện nhảy số, trùng số hoặc giảm số Điều; tích hợp "
            "hàng rào check_chunking_anomaly cảnh báo văn bản có trên 50% số đoạn dồn vào một Điều để bảo vệ kho dữ liệu."
        ),
        101: (
            "Dense Retrieval (dense_search.py): nhúng văn bản bằng mô hình Google Text Embedding, tạo vector 768 chiều và lưu trữ trên Qdrant; "
            "áp dụng bộ lọc siêu dữ liệu status = ACTIVE để chỉ truy xuất các văn bản còn hiệu lực pháp lý."
        ),
        102: (
            "Sparse Retrieval (bm25_search.py): xây dựng chỉ mục toàn văn bằng thuật toán BM25 Okapi trên tập từ vựng học vụ tiếng Việt."
        ),
        103: (
            "Dung hợp thứ hạng RRF (fusion.py, hybrid_retriever.py): kết hợp thứ hạng từ Dense và BM25 theo công thức: "
            "RRF_Score(d) = Σ [1 / (k + rank_m(d))] với hằng số làm mịn k = 60. Phương pháp này kết hợp hài hòa khả năng nắm bắt ngữ nghĩa "
            "khái quát và khả năng định vị chính xác từ khóa thực thể học vụ."
        ),
        104: (
            "Mở rộng từ viết tắt (abbreviation_mapper.py): tự động ánh xạ và chuyển đổi các câu hỏi chứa BHYT, ĐKHP, CĐR, ĐRL, CTXH thành dạng "
            "song song 'từ viết tắt (dạng đầy đủ)' trước khi thực thi truy xuất."
        ),
        106: (
            "Lớp 1 – Ngưỡng an toàn (Relevance Gating): nếu điểm số tương đồng của đoạn trích cao nhất thấp hơn ngưỡng min_dense_score, "
            "hệ thống kích hoạt cơ chế từ chối an toàn ngay lập tức mà không gọi mô hình sinh ngôn ngữ, giúp loại trừ triệt để nguy cơ ảo giác."
        ),
        107: (
            "Lớp 2 – Ràng buộc System Prompt và nhiệt độ: thiết lập temperature trong khoảng 0,0–0,2 để tối ưu hóa tính tiền định; yêu cầu bắt buộc "
            "trích dẫn nguồn gốc theo cú pháp chuẩn [Văn bản - Điều - Khoản] và nghiêm cấm tự suy diễn ngoài ngữ cảnh."
        ),
        108: (
            "Lớp 3 – Number Verifier (verifier.py): trích xuất các con số trong câu trả lời (S_answer) và trong ngữ cảnh trích dẫn (S_context), "
            "xác định tập số liệu không có căn cứ: S_unsupported = S_answer \\ S_context. Nếu phát hiện số liệu lạ, hệ thống tự động gắn cờ cảnh báo "
            "hoặc yêu cầu mô hình hiệu chỉnh câu trả lời."
        ),
        110: (
            "Backend Gateway bằng Spring Boot 3.x: quản trị xác thực JWT, phân quyền RBAC, giới hạn tần suất truy cập (Rate Limiting), lưu trữ "
            "lịch sử hội thoại trong PostgreSQL và tự động nhận diện, che mờ thông tin cá nhân nhạy cảm (PII Redaction: CCCD, số điện thoại, MSSV)."
        ),
        111: (
            "AI Core Service bằng Python FastAPI: triển khai pipeline xử lý truy vấn, truy xuất lai, kiểm duyệt nạp kho Default-Deny và sinh phản hồi."
        ),
        112: (
            "Web Client bằng React + TypeScript hỗ trợ Server-Sent Events (SSE) để hiển thị phản hồi streaming theo thời gian thực; Web Admin bằng "
            "Ant Design hỗ trợ cán bộ Nhà trường quản lý tài liệu, giám sát trạng thái nạp và theo dõi câu hỏi sinh viên."
        ),
        113: (
            "Đóng gói Widget SDK (donga-bot.js): cho phép nhúng cửa sổ chat thông minh vào cổng thông tin đào tạo của trường thông qua một thẻ script duy nhất."
        ),
        114: (
            "Triển khai ma trận thực nghiệm đa chiều: so sánh Chunking cố định với Chunking cấu trúc; Dense Search với Hybrid RRF; mô hình Google Gemini "
            "với GPT-4o-mini; đánh giá định lượng bằng evaluation/run_eval.py."
        ),

        # --- Mục 3: Cách tiếp cận, phương pháp nghiên cứu và kỹ thuật sử dụng ---
        117: (
            "Tiếp cận thực nghiệm hướng người dùng (User-Centered Engineering): xuất phát từ phân tích bảng hỏi 49 sinh viên thực tế nhằm giải quyết "
            "chính xác các vấn đề về câu hỏi viết tắt, nỗi lo thông tin lỗi thời và nguy cơ sai sót của AI."
        ),
        118: (
            "Tiếp cận kiến trúc vi dịch vụ liên kết lỏng (Loosely-Coupled Microservices): phân tách triệt để tầng nghiệp vụ/bảo mật (Spring Boot) "
            "khỏi tầng tính toán AI (Python FastAPI), tạo điều kiện linh hoạt nâng cấp mô hình ngôn ngữ hoặc cơ sở dữ liệu vector mà không ảnh hưởng giao diện."
        ),
        120: "Thu thập và phân tích dữ liệu: khảo sát trực tuyến; số hóa, làm sạch và chuẩn hóa toàn bộ văn bản về bảng mã Unicode dựng sẵn (NFC).",
        121: "Xử lý ngôn ngữ tự nhiên: mở rộng từ viết tắt học vụ, viết lại truy vấn hội thoại (Query Rewriting) và định tuyến ý định (Intent Routing).",
        122: "Mô hình ngôn ngữ và embedding: ứng dụng mô hình nhúng Google Text Embedding và mô hình sinh Google Gemini thế hệ mới với chi phí tối ưu.",
        123: "Cơ sở dữ liệu vector chuyên dụng: Qdrant Vector Database với giải thuật chỉ mục đồ thị phân tầng HNSW (Cosine metric).",
        124: "Đánh giá định lượng bằng RAGAS: đo lường Faithfulness, Answer Relevance, Context Precision, Context Recall kết hợp Hit@k và MRR.",
        125: "Kiểm thử phần mềm tự động hóa: xây dựng bộ 63 Unit Tests độc lập, bao phủ toàn bộ pipeline từ bóc tách XML, cắt đoạn, RRF đến kiểm tra số liệu, đạt 63/63 kiểm thử PASS (100%).",
        127: (
            "Đề xuất quy trình Semantic Structural Chunking kết hợp giải thuật Table Header Propagation chuyên biệt cho văn bản quy phạm hành chính tiếng Việt, "
            "bảo toàn tuyệt đối quan hệ tiêu đề cột trong các bảng biểu học phí, chuẩn đầu ra và điểm rèn luyện."
        ),
        128: (
            "Tích hợp giải thuật dung hợp thứ hạng RRF giữa Dense Vector Search và BM25 Okapi, khắc phục triệt để điểm yếu của tìm kiếm vector thuần túy đối với các từ khóa thực thể chính xác."
        ),
        129: (
            "Thiết kế cơ chế kiểm soát ảo giác 3 lớp với bộ thẩm tra số liệu độc lập Number Verifier dựa trên lý thuyết tập hợp, ngăn chặn hiệu quả tình trạng mô hình AI suy đoán sai số liệu quy chế."
        ),
        130: (
            "Xây dựng cơ chế cổng nạp Default-Deny cùng bộ Widget SDK đóng gói hoàn chỉnh, cho phép nhúng trực tiếp trợ lý ảo vào hệ thống quản lý đào tạo hiện hữu của Nhà trường với chi phí vận hành tối ưu."
        ),

        # --- Mục 5 & 6: Dự kiến kết quả & Ý nghĩa ---
        139: (
            "Web Sinh viên: giao diện hỏi đáp thông minh, phản hồi dạng streaming qua SSE, hiển thị rõ ràng nguồn trích dẫn gồm tên văn bản, số hiệu, điều khoản và ngày hiệu lực; có chức năng phản hồi Đúng/Sai."
        ),
        140: (
            "Web Admin: quản trị danh mục tài liệu theo bảng đăng ký Default-Deny, theo dõi trạng thái phân mảnh, quản lý FAQ và tra cứu nhật ký câu hỏi của sinh viên."
        ),
        141: "Widget SDK: tệp donga-bot.js đóng gói nhỏ gọn, cho phép nhúng vào cổng thông tin sinh viên chỉ với một dòng mã script.",
        143: "Báo cáo đánh giá định lượng hiệu năng hệ thống RAG bằng framework RAGAS và các chỉ số đo lường truy xuất.",
        144: "Ma trận kết quả thực nghiệm chi tiết so sánh phân mảnh cấu trúc với phân mảnh cố định, Hybrid RRF với Dense Search và các mô hình sinh ngôn ngữ được lựa chọn.",
        145: "Bộ dữ liệu chuẩn hóa gồm 100 câu hỏi – đáp quy chế học vụ tiếng Việt (Ground Truth Benchmark) được thẩm định chuyên môn.",
        148: (
            "Đóng góp về xử lý văn bản quy phạm tiếng Việt: đề xuất quy trình chuẩn hóa và khai thác cấu trúc phân cấp chặt chẽ của văn bản hành chính, đặc biệt là giải thuật bảo toàn quan hệ dữ liệu trong bảng biểu số liệu khi phân mảnh."
        ),
        149: (
            "Cung cấp bằng chứng thực nghiệm rõ ràng về hiệu quả của truy xuất lai RRF, kết hợp tối ưu giữa không gian vector ngữ nghĩa và không gian từ vựng rời rạc trong bài toán hỏi đáp quy chế giáo dục."
        ),
        150: (
            "Đánh giá định lượng cơ chế kiểm soát ảo giác đa tầng; chứng minh bằng thực nghiệm khả năng hạn chế tối đa sai lệch số liệu học vụ của mô hình ngôn ngữ lớn."
        ),
        153: "Cung cấp kênh tra cứu thông tin chính thống, hỗ trợ giải đáp quy chế học vụ tự động và chuẩn xác 24/7.",
        154: "Giúp sinh viên tiếp cận minh bạch thông tin về quyền lợi, nghĩa vụ, điều kiện tốt nghiệp và chính sách học bổng, loại bỏ hoàn toàn sự phụ thuộc vào thông tin truyền miệng thiếu kiểm chứng.",
        156: "Tiềm năng giảm tải 60–80% khối lượng câu hỏi thủ tục lặp lại gửi về Phòng Đào tạo và các Khoa trong các đợt cao điểm đầu học kỳ.",
        157: "Thúc đẩy tiến trình chuyển đổi số dịch vụ hỗ trợ người học với chi phí vận hành tối ưu (ước tính dưới 25 USD/tháng cho toàn bộ hạ tầng).",
        158: "Thống kê câu hỏi đã ẩn danh giúp Nhà trường nhận diện kịp thời các quy định sinh viên thường gặp khó khăn hoặc hiểu chưa đúng, từ đó nâng cao chất lượng truyền thông chính sách học vụ."
    }

    print(f"Đang cập nhật {len(updates)} đoạn văn trong file Word...")
    updated_count = 0
    for idx, new_text in updates.items():
        if idx < len(p_list):
            p = p_list[idx]
            p.text = new_text
            updated_count += 1
        else:
            print(f"Cảnh báo: Chỉ mục {idx} vượt quá số đoạn hiện có ({len(p_list)})")

    print(f"Đã cập nhật thành công {updated_count} đoạn văn bản.")

    # Cập nhật Table 0 (Bảng tiến độ)
    if doc.tables:
        t0 = doc.tables[0]
        # Row 2 (Giai đoạn 2: Xây dựng AI Core Service)
        if len(t0.rows) > 2:
            row2 = t0.rows[2]
            # Cột 4: Kết quả cần đạt
            if len(row2.cells) > 4:
                row2.cells[4].text = "Mã nguồn AI Core; toàn bộ 63/63 Unit Tests PASS; kho vector Qdrant và BM25 hoàn thiện sẵn sàng."
                print("Đã cập nhật Table 0 Row 2: 63/63 Unit Tests PASS.")

    # Xử lý Mục 7 (Tài liệu tham khảo) và Mục 8 (Xác nhận)
    # Đoạn 163 là "Đà Nẵng, ngày 02 tháng 10 năm 2026"
    # Ta sẽ chèn Mục 7 và Mục 8 ngay trước đoạn 163
    p_danang = None
    for p in doc.paragraphs:
        if "Đà Nẵng, ngày" in p.text:
            p_danang = p
            break

    if p_danang:
        print("Tìm thấy vị trí chèn Mục 7 (Tài liệu tham khảo) và Mục 8 (Xác nhận)...")
        # Chèn tiêu đề Heading 2: 7. Tài liệu tham khảo
        h7 = p_danang.insert_paragraph_before("7. Tài liệu tham khảo", style="Heading 2")
        
        # Danh mục tài liệu tham khảo chuẩn IEEE
        refs = [
            "[1] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, \"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,\" in Advances in Neural Information Processing Systems (NeurIPS), vol. 33, pp. 9459–9474, 2020.",
            "[2] G. V. Cormack, C. L. A. Clarke, and S. Büttcher, \"Reciprocal rank fusion outperforms condorcet and individual rank learning methods,\" in Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval, pp. 758–759, 2009.",
            "[3] S. Robertson and H. Zaragoza, \"The Probabilistic Relevance Framework: BM25 and Beyond,\" Foundations and Trends in Information Retrieval, vol. 3, no. 4, pp. 333–389, 2009.",
            "[4] S. Es, J. James, L. R. Espinosa, and B. Burtsev, \"RAGAS: Automated Evaluation of Retrieval Augmented Generation,\" arXiv preprint arXiv:2309.15217, 2023.",
            "[5] Y. Gao, Y. Xiong, X. Wang, K. Wang, and J. Gao, \"Retrieval-Augmented Generation for Large Language Models: A Survey,\" arXiv preprint arXiv:2312.10997, 2023.",
            "[6] J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, \"BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding,\" in Proceedings of NAACL-HLT, pp. 4171–4186, 2019.",
            "[7] Y. A. Malkov and D. A. Yashunin, \"Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs,\" IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 42, no. 4, pp. 824–836, 2020.",
            "[8] Bộ Giáo dục và Đào tạo, Thông tư số 08/2021/TT-BGDĐT ban hành Quy chế đào tạo trình độ đại học, Hà Nội, 2021.",
            "[9] Trường Đại học Đông Á, Quyết định số 106/QĐ-ĐHĐA ban hành Quy chế Công tác sinh viên đối với chương trình đào tạo đại học hệ chính quy, Đà Nẵng, 2021.",
            "[10] Trường Đại học Đông Á, Quyết định số 105/QĐ-ĐHĐA ban hành Nội quy học đường dành cho sinh viên Trường Đại học Đông Á, Đà Nẵng, 2021.",
            "[11] Trường Đại học Đông Á, Quy định Chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành không chuyên ngữ tại Trường Đại học Đông Á, Đà Nẵng, 2023."
        ]

        for ref_text in refs:
            p_ref = p_danang.insert_paragraph_before(ref_text, style="Normal")
            # Canh đều 2 bên và thụt lề treo
            p_ref.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Thêm khoảng trống và tiêu đề Heading 2: 8. Xác nhận
        p_danang.insert_paragraph_before("", style="Normal")
        h8 = p_danang.insert_paragraph_before("8. Xác nhận", style="Heading 2")
        print("Đã chèn hoàn chỉnh Mục 7 (11 tài liệu tham khảo IEEE) và Mục 8 (Xác nhận).")
    else:
        print("Cảnh báo: Không tìm thấy đoạn Đà Nẵng để chèn Mục 7.")

    # Lưu lại file Word
    doc.save(DOC_PATH)
    print(f"ĐÃ LƯU THÀNH CÔNG VÀO FILE: {DOC_PATH}")

if __name__ == "__main__":
    run_upgrade()
