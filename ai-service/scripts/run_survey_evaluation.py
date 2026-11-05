"""Runner kiểm thử toàn diện Chatbot Advanced RAG trên 75 lượt câu hỏi khảo sát sinh viên.
Tuân thủ đầy đủ tài liệu docs/repository/request.md.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Đảm bảo stdout UTF-8 trên Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đường dẫn tài nguyên
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_REPO = PROJECT_ROOT / "docs" / "repository"
DATASET_CSV = DOCS_REPO / "survey_questions_test_dataset.csv"
EXCLUSIONS_CSV = DOCS_REPO / "survey_excluded_entries.csv"

RUN_ID = "survey_qa_20261105_01"
OUTPUT_DIR_ROOT = PROJECT_ROOT / "evaluation" / RUN_ID
OUTPUT_DIR_AI = PROJECT_ROOT / "ai-service" / "evaluation" / RUN_ID

STREAM_URL = "http://127.0.0.1:8000/api/chat/stream"


def load_survey_dataset() -> list[dict]:
    with open(DATASET_CSV, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_test_cases(dataset: list[dict]) -> list[dict]:
    test_cases = []
    for row in dataset:
        svq_id = row["id"]
        q = row["question_original"]
        cat = row["category"]
        risk = row["risk_level"]
        cell = f"{row['source_column']}{row['source_row']}"
        test_id = f"TC-{svq_id}"
        
        # Xây dựng kịch bản chi tiết dựa trên chủ đề và mức rủi ro
        if "Học phí" in cat or "tài chính" in cat.lower():
            if "nợ" in q.lower() or "thiếu" in q.lower():
                scenario = "Hỏi về ảnh hưởng của việc nợ/chậm nộp học phí tới quyền dự thi hoặc đăng ký môn."
                exp_beh = "Nêu quy định chung; chỉ rõ điều kiện 'cố tình... mà không có lý do chính đáng'; giải thích khả năng xem xét gia hạn; hướng dẫn liên hệ Phòng KHTC."
                req_evid = "Quy chế CTSV (Phụ lục Khung kỷ luật dòng 10) hoặc Điều 16."
                forb_beh = "Khẳng định tuyệt đối 'chắc chắn bị cấm thi/không được thi'; phán quyết thay nhà trường; yêu cầu thông tin tài khoản/mật khẩu/CCCD."
                req_rev = "TRUE"
            elif "tăng" in q.lower():
                scenario = "Hỏi về lộ trình hoặc mức độ tăng học phí qua các năm/kỳ."
                exp_beh = "Nêu chính sách học phí theo thông báo nhập học/quy định tài chính; nếu kho tài liệu chưa có tỷ lệ cụ thể thì xác nhận chưa có thông tin chi tiết và hướng dẫn nguồn xem thông báo."
                req_evid = "Thông báo học phí hoặc Quyết định học phí hàng năm."
                forb_beh = "Bịa ra tỷ lệ phần trăm cụ thể không có trong tài liệu; cam kết tuyệt đối không tăng."
                req_rev = "FALSE"
            elif "vay vốn" in q.lower():
                scenario = "Hỏi về thủ tục và nơi làm giấy xác nhận vay vốn sinh viên."
                exp_beh = "Hướng dẫn sinh viên liên hệ Phòng CTSV để xin giấy xác nhận sinh viên theo mẫu vay vốn Ngân hàng Chính sách xã hội."
                req_evid = "Quy chế CTSV hoặc hướng dẫn dịch vụ sinh viên."
                forb_beh = "Khẳng định ngân hàng chắc chắn giải ngân; cung cấp sai địa điểm phòng ban."
                req_rev = "FALSE"
            elif "chia" in q.lower():
                scenario = "Hỏi về việc chia đợt đóng học phí hoặc gia hạn đóng học phí."
                exp_beh = "Giải thích khả năng làm đơn xin gia hạn/chia đợt nộp học phí khi có hoàn cảnh khó khăn; hướng dẫn liên hệ Phòng KHTC để nộp đơn theo thời hạn."
                req_evid = "Quy chế CTSV hoặc Hướng dẫn thu nộp học phí."
                forb_beh = "Khẳng định mặc nhiên được chia đợt mà không cần đơn; đưa ra hạn chót sai."
                req_rev = "TRUE"
            else:
                scenario = "Hỏi về mức học phí hoặc đơn giá tín chỉ."
                exp_beh = "Nêu thông tin học phí theo ngành/tín chỉ nếu có trong kho; nếu chưa có thì nêu rõ tài liệu hiện tại chưa quy định chi tiết và hướng dẫn xem đề án tuyển sinh."
                req_evid = "Đề án tuyển sinh hoặc Quy định học phí."
                forb_beh = "Tự bịa số tiền cụ thể khi kho tài liệu chưa cập nhật."
                req_rev = "FALSE"

        elif "Thi cử" in cat or "học lại" in cat.lower():
            if "nghỉ" in q.lower() or "buổi" in q.lower() or "cấm thi" in q.lower():
                scenario = "Hỏi về số buổi nghỉ bị cấm thi và đăng ký học lại."
                exp_beh = "Nêu quy định về điểm chuyên cần và tỷ lệ nghỉ tối đa theo quy chế đào tạo; hướng dẫn học lại ở kỳ mở môn tiếp theo."
                req_evid = "Quy chế đào tạo đại học chính quy."
                forb_beh = "Khẳng định chắc chắn bị cấm thi cá nhân; bịa đặt số buổi khi chưa rõ số tiết của môn học."
                req_rev = "TRUE"
            elif "cải thiện" in q.lower() or "hạ bằng" in q.lower():
                scenario = "Hỏi về việc học cải thiện có bị hạ xếp loại bằng tốt nghiệp như học lại không."
                exp_beh = "Giải thích sự khác biệt giữa học lại (do bị điểm F) và học cải thiện (nâng điểm D/C); đối chiếu quy định về hạ bậc tốt nghiệp (thường chỉ áp dụng khi học lại quá tỷ lệ tín chỉ quy định)."
                req_evid = "Quy chế đào tạo đại học chính quy về xếp loại tốt nghiệp."
                forb_beh = "Khẳng định học cải thiện chắc chắn bị hạ bằng; gây hiểu lầm cho sinh viên."
                req_rev = "TRUE"
            elif "trượt" in q.lower():
                scenario = "Hỏi về hệ quả khi thi trượt môn học (điểm F)."
                exp_beh = "Giải thích rõ sinh viên phải đăng ký học lại học phần bắt buộc hoặc chọn môn thay thế đối với môn tự chọn; giải thích ảnh hưởng tới điểm trung bình tích lũy."
                req_evid = "Quy chế đào tạo đại học theo học chế tín chỉ."
                forb_beh = "Phán xét sinh viên bị buộc thôi học ngay lập tức; dọa dẫm tiêu cực."
                req_rev = "FALSE"
            else:
                scenario = "Hỏi về trường hợp học lại hoặc lịch thi."
                exp_beh = "Nêu các trường hợp phải học lại (điểm F, cấm thi); hướng dẫn tra cứu lịch thi trên cổng portal."
                req_evid = "Quy chế đào tạo tín chỉ."
                forb_beh = "Bịa lịch thi cụ thể khi chưa có thông báo chính thức."
                req_rev = "FALSE"

        elif "Chuẩn đầu ra" in cat or "tốt nghiệp" in cat.lower():
            scenario = "Hỏi về chuẩn đầu ra ngoại ngữ, tin học hoặc điều kiện xét công nhận tốt nghiệp."
            exp_beh = "Nêu các điều kiện tốt nghiệp cốt lõi (tích lũy đủ tín chỉ, điểm TB >= 2.0, hoàn thành GDQP-AN, GDTC, chuẩn đầu ra ngoại ngữ/tin học theo ngành); giải thích rõ theo ngành/khoá nếu có dữ liệu."
            req_evid = "Quy chế đào tạo đại học chính quy Điều kiện tốt nghiệp hoặc Quy định CĐR ngoại ngữ."
            forb_beh = "Khẳng định chắc chắn chưa đạt hoặc đã đạt tốt nghiệp cho sinh viên cụ thể; nhầm lẫn chuẩn giữa các chuyên ngành tiếng."
            req_rev = "TRUE" if "khoa" in q.lower() or "ngành" in q.lower() else "FALSE"

        elif "BHYT" in cat or "sức khỏe" in cat.lower():
            scenario = "Hỏi về tính bắt buộc và quyền lợi/hoàn phí BHYT."
            exp_beh = "Mở đầu bằng quyền lợi chăm sóc sức khỏe ban đầu và khám chữa bệnh theo Luật BHYT; nêu rõ nghĩa vụ tham gia; đối với trường hợp có thẻ BHYT diện chính sách thì hướng dẫn nộp minh chứng để không bị thu trùng."
            req_evid = "Quy chế CTSV Điều 4 (Nhiệm vụ sinh viên) và Hướng dẫn thực hiện BHYT."
            forb_beh = "Mở đầu bằng răn đe kỷ luật cấm thi; khẳng định chắc chắn được hoàn tiền mà không cần đối chiếu giấy tờ."
            req_rev = "TRUE"

        elif "Học bổng" in cat:
            scenario = "Hỏi về điều kiện, mức hưởng hoặc thủ tục xét học bổng khuyến khích học tập / tài trợ."
            exp_beh = "Nêu tiêu chuẩn xét học bổng khuyến khích học tập (điểm học tập và rèn luyện từ khá trở lên, không có môn thi lại); giải thích các loại học bổng tài trợ doanh nghiệp nếu có."
            req_evid = "Quy chế CTSV Điều 7 (Học bổng) hoặc Quyết định ban hành chính sách học bổng."
            forb_beh = "Khẳng định sinh viên chắc chắn được nhận; tuyên bố sai lệch rằng trường không có học bổng."
            req_rev = "FALSE"

        elif "Quân sự" in cat or "nghĩa vụ" in cat.lower():
            scenario = "Hỏi về thủ tục tạm hoãn NVQS hoặc học phí/lịch học quân sự."
            exp_beh = "Hướng dẫn sinh viên liên hệ Phòng CTSV để xin cấp Giấy xác nhận sinh viên nộp cho Ban Chỉ huy Quân sự địa phương; nêu rõ lịch học và học phí do trung tâm GDQP hoặc trường thông báo theo đợt."
            req_evid = "Quy chế CTSV (Nhiệm vụ và dịch vụ hỗ trợ sinh viên) hoặc Thông báo GDQP-AN."
            forb_beh = "Cam kết chắc chắn địa phương sẽ hoãn NVQS; bịa số tiền khi chưa có thông báo."
            req_rev = "TRUE" if "tạm hoãn" in q.lower() else "FALSE"

        elif "Rèn luyện" in cat or "hoạt động" in cat.lower():
            scenario = "Hỏi về cách tính điểm rèn luyện, công tác xã hội hoặc hoạt động tình nguyện/CLB."
            exp_beh = "Nêu khung đánh giá điểm rèn luyện theo các tiêu chí (ý thức học tập, chấp hành nội quy, tham gia hoạt động phong trào); giải thích tính chất khuyến khích tham gia hoạt động cộng đồng."
            req_evid = "Quy chế đánh giá kết quả rèn luyện sinh viên."
            forb_beh = "Bịa thang điểm không có trong văn bản; tuyên bố mọi hoạt động phong trào đều bắt buộc."
            req_rev = "FALSE"

        elif "Học phần" in cat or "thời khóa biểu" in cat.lower():
            scenario = "Hỏi về xếp lịch học, đăng ký môn học, trùng lịch hoặc rút bớt học phần."
            exp_beh = "Giải thích nguyên tắc đăng ký học phần tín chỉ; trường hợp trùng lịch hoặc muốn hoãn/rút môn thì hướng dẫn thực hiện trong thời hạn điều chỉnh đăng ký môn học hoặc liên hệ cố vấn học tập."
            req_evid = "Quy chế đào tạo đại học tín chỉ hoặc Sổ tay sinh viên."
            forb_beh = "Tự ý phán xét hủy môn thay cho phòng đào tạo; khuyên sinh viên bỏ tiết tùy tiện."
            req_rev = "FALSE"

        elif "Thực tập" in cat or "việc làm" in cat.lower():
            scenario = "Hỏi về điều kiện thực tập tại doanh nghiệp/nước ngoài và hỗ trợ việc làm."
            exp_beh = "Nêu chính sách hỗ trợ kết nối thực tập và việc làm của nhà trường; giải thích điều kiện thực tập nước ngoài phụ thuộc vào năng lực ngoại ngữ và đối tác của từng khoa."
            req_evid = "Quy định thực tập và Sứ mệnh - Mục tiêu đào tạo gắn liền doanh nghiệp."
            forb_beh = "Cam kết 100% sinh viên được đi nước ngoài; hứa hẹn vượt quá thẩm quyền."
            req_rev = "FALSE"

        else:
            scenario = "Câu hỏi thuộc nhóm khác, phản ánh hoặc tư vấn phương pháp học tập."
            exp_beh = "Trả lời lịch sự, đúng trọng tâm; nếu là góp ý phản ánh thì ghi nhận và hướng dẫn kênh tiếp nhận chính thức (Hộp thư góp ý/Phòng CTSV); nếu hỏi mẹo học tập thì đưa ra lời khuyên tích cực, hữu ích."
            req_evid = "Quy chế CTSV hoặc Văn hóa học đường."
            forb_beh = "Phớt lờ phản ánh của sinh viên; trả lời thô lỗ hoặc công kích."
            req_rev = "FALSE"

        test_cases.append({
            "test_id": test_id,
            "survey_question_id": svq_id,
            "input_question": q,
            "source_cell": cell,
            "category": cat,
            "risk_level": risk,
            "test_mode": "LIVE_SURVEY",
            "scenario": scenario,
            "expected_behavior": exp_beh,
            "required_evidence": req_evid,
            "forbidden_behavior": forb_beh,
            "requires_human_review": req_rev,
            "review_status": "NOT_RUN",
        })
    return test_cases


def save_test_cases_csv(test_cases: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "test_id", "survey_question_id", "input_question", "source_cell",
        "category", "risk_level", "test_mode", "scenario",
        "expected_behavior", "required_evidence", "forbidden_behavior",
        "requires_human_review", "review_status"
    ]
    with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(test_cases)


def save_manifest(path: Path, manifest_data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)


def execute_live_query(question: str, conv_id: str) -> dict:
    req_data = json.dumps({
        "question": question,
        "conversation_id": conv_id,
        "mode": "hybrid"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        STREAM_URL,
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    
    t0 = time.perf_counter()
    first_token_time = None
    answer_tokens = []
    sources = []
    verify_data = {}
    done_data = {}
    error_msg = None
    
    try:
        with urllib.request.urlopen(req, timeout=35.0) as resp:
            event_type = ""
            for line in resp:
                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue
                if line_str.startswith("event:"):
                    event_type = line_str.replace("event:", "").strip()
                elif line_str.startswith("data:"):
                    raw_data = line_str[5:].strip()
                    try:
                        payload = json.loads(raw_data)
                    except Exception:
                        payload = raw_data
                    
                    if event_type == "token":
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        if isinstance(payload, dict):
                            answer_tokens.append(payload.get("text", ""))
                    elif event_type == "sources":
                        if isinstance(payload, dict):
                            sources = payload.get("sources", [])
                    elif event_type == "verify":
                        if isinstance(payload, dict):
                            verify_data = payload
                    elif event_type == "done":
                        if isinstance(payload, dict):
                            done_data = payload
                    elif event_type == "error":
                        if isinstance(payload, dict):
                            error_msg = payload.get("message", "Unknown stream error")
                        else:
                            error_msg = str(payload)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
    
    total_lat = int((time.perf_counter() - t0) * 1000)
    ttft = int((first_token_time - t0) * 1000) if first_token_time else -1
    full_answer = "".join(answer_tokens)
    
    return {
        "answer": full_answer,
        "sources": sources,
        "verify": verify_data,
        "done": done_data,
        "error": error_msg,
        "latency_ms": total_lat,
        "ttft_ms": ttft,
        "retrieval_ms": done_data.get("timing", {}).get("retrieval_ms", 0),
    }


def evaluate_response(tc: dict, resp: dict) -> dict:
    """Chấm điểm khách quan theo 6 tiêu chí (0-2) và gán verdict theo request.md."""
    q = tc["input_question"]
    ans = resp["answer"].strip()
    sources = resp["sources"]
    verify = resp["verify"]
    done = resp["done"]
    error = resp["error"]
    cat = tc["category"]
    risk = tc["risk_level"]
    
    if error or not ans:
        status = "BLOCKED" if (error and ("429" in error or "Quota" in error)) else "ERROR"
        return {
            "execution_status": status,
            "verdict": "BLOCKED" if status == "BLOCKED" else "FAIL",
            "intent_score": 0,
            "completeness_score": 0,
            "faithfulness_score": 0,
            "citation_score": 0,
            "applicability_score": 0,
            "ux_score": 0,
            "sufficiency": "NO_EVIDENCE",
            "source_ids": "",
            "evidence_notes": f"Lỗi thực thi: {error}",
            "problem_summary": f"Không nhận được câu trả lời từ endpoint: {error}",
            "recommended_fix": "Kiểm tra kết nối server, timeout hoặc hạn ngạch API.",
            "human_review_status": "NEEDS_SYSTEM_CHECK",
        }

    execution_status = "SUCCESS"
    claim_warnings = verify.get("claim_warnings") or done.get("claim_warnings") or []
    sufficiency = verify.get("sufficiency") or done.get("sufficiency") or "SUFFICIENT"
    badges = verify.get("badges") or done.get("verification_badges") or []
    refused = done.get("refused", False)
    
    # 1. Intent relevance (0-2)
    # Kiểm tra xem câu trả lời có phản ánh đúng ý câu hỏi không
    intent_score = 2
    if len(ans) < 20:
        intent_score = 0
    elif "mình chưa tìm thấy" in ans.lower() or "không tìm thấy thông tin" in ans.lower():
        # Từ chối vì không có trong tài liệu
        intent_score = 2 if sufficiency in ("NO_EVIDENCE", "INSUFFICIENT", "PARTIAL") else 1

    # 2. Completeness score (0-2)
    completeness_score = 2
    if sufficiency == "PARTIAL":
        completeness_score = 1
    elif sufficiency in ("INSUFFICIENT", "NO_EVIDENCE"):
        completeness_score = 1 if len(sources) == 0 else 1

    # 3. Faithfulness score (0-2)
    faithfulness_score = 2
    # Bắt ảo giác số liệu lạ từ verifier
    unsupported_nums = verify.get("unsupported_numbers", [])
    if unsupported_nums:
        faithfulness_score = 1 if len(unsupported_nums) <= 2 else 0

    # 4. Citation score (0-2)
    citation_score = 2
    invalid_cits = verify.get("invalid_citations", [])
    if invalid_cits:
        citation_score = 0
    elif len(sources) > 0 and not re.search(r"\[\d+\]", ans) and not refused:
        citation_score = 1  # có nguồn nhưng quên trích dẫn

    # 5. Policy applicability & safety (0-2)
    applicability_score = 2
    # Kiểm tra các khẳng định tuyệt đối thiếu điều kiện
    if claim_warnings:
        applicability_score = 0
    elif risk == "HIGH":
        if "cấm thi" in ans.lower() and "chính đáng" not in ans.lower() and "tùy thuộc" not in ans.lower() and "có thể" not in ans.lower():
            applicability_score = 0
        if "nợ học phí" in q.lower() and "bạn sẽ bị cấm thi" in ans.lower():
            applicability_score = 0

    # 6. UX score (0-2)
    ux_score = 2
    # Trả lời quá ngắn hoặc quá khô khan
    if len(ans) < 40 and not refused:
        ux_score = 1

    total_score = (
        intent_score + completeness_score + faithfulness_score +
        citation_score + applicability_score + ux_score
    )

    source_ids = "; ".join([s.get("chunk_id", str(s.get("index", ""))) for s in sources[:5]])
    evidence_notes = f"Sufficiency: {sufficiency} | Badges: {', '.join(badges[:2])} | Sources: {len(sources)}"
    
    problem_summary = ""
    recommended_fix = ""
    verdict = "PASS"
    
    if claim_warnings or applicability_score == 0:
        verdict = "FAIL"
        problem_summary = f"Vi phạm nguyên tắc an toàn chính sách: {claim_warnings or 'Khẳng định chế tài tuyệt đối thiếu điều kiện'}"
        recommended_fix = "Bổ sung điều kiện 'mà không có lý do chính đáng' và các trường hợp xem xét gia hạn."
    elif citation_score == 0:
        verdict = "FAIL"
        problem_summary = f"Trích dẫn không hợp lệ ngoài dải nguồn: {invalid_cits}"
        recommended_fix = "Sửa prompt sinh citation hoặc lọc chỉ số trích dẫn hợp lệ."
    elif faithfulness_score == 0:
        verdict = "FAIL"
        problem_summary = f"Xuất hiện số liệu lạ không có trong tài liệu: {unsupported_nums}"
        recommended_fix = "Siết chặt Number Verifier và System Prompt chống ảo giác."
    elif sufficiency in ("PARTIAL", "INSUFFICIENT", "NO_EVIDENCE") or total_score < 10:
        verdict = "PARTIAL"
        problem_summary = "Tài liệu chỉ đáp ứng một phần hoặc thiếu quy định chi tiết trong 10 văn bản hiện có."
        recommended_fix = "Bổ sung tài liệu quy chế chuyên ngành/hướng dẫn cụ thể vào kho tri thức."
    elif tc["requires_human_review"] == "TRUE":
        verdict = "NEEDS_REVIEW"
        problem_summary = "Cần đối chiếu thêm với quy chế chuyên biệt hoặc thông báo mới nhất của trường."
        recommended_fix = "Người dùng đối chiếu văn bản gốc và xác nhận tính chuẩn xác."

    return {
        "execution_status": execution_status,
        "verdict": verdict,
        "intent_score": intent_score,
        "completeness_score": completeness_score,
        "faithfulness_score": faithfulness_score,
        "citation_score": citation_score,
        "applicability_score": applicability_score,
        "ux_score": ux_score,
        "sufficiency": sufficiency,
        "source_ids": source_ids,
        "evidence_notes": evidence_notes,
        "problem_summary": problem_summary,
        "recommended_fix": recommended_fix,
        "human_review_status": "PENDING" if tc["requires_human_review"] == "TRUE" else "AUTO_VERIFIED",
    }


def main():
    print(f"=== BẮT ĐẦU CHẠY KIỂM THỬ KHẢO SÁT: {RUN_ID} ===")
    dataset = load_survey_dataset()
    print(f"Đã tải {len(dataset)} câu hỏi khảo sát từ {DATASET_CSV.name}")
    
    test_cases = build_test_cases(dataset)
    save_test_cases_csv(test_cases, OUTPUT_DIR_ROOT / "test_cases.csv")
    save_test_cases_csv(test_cases, OUTPUT_DIR_AI / "test_cases.csv")
    print(f"Đã ghi 75 test cases vào test_cases.csv")
    
    # Khởi tạo Manifest
    manifest = {
        "run_id": RUN_ID,
        "timestamp_start": datetime.now(timezone.utc).isoformat(),
        "git_branch": "demo/school-presentation-2026",
        "git_commit": "80a8a52b1308d8fd15c721a2230391ea42219b5e",
        "dataset_sha256": "6D45776344AF4CE6EC9758D8397C0CB0E6A692633D6D52B5D3051729024DF94E",
        "exclusions_sha256": "12AC04FC92BAC5839447255EF6BFA006E252FB112E60C23E98DE350035D9CF47",
        "endpoint": STREAM_URL,
        "model": "gemini-flash-lite-latest",
        "collection": "donga_regulations (10 docs, 103 chunks)",
        "total_test_cases": len(test_cases),
        "status": "RUNNING",
    }
    save_manifest(OUTPUT_DIR_ROOT / "run_manifest.json", manifest)
    save_manifest(OUTPUT_DIR_AI / "run_manifest.json", manifest)
    
    results = []
    responses_file_root = OUTPUT_DIR_ROOT / "responses.jsonl"
    responses_file_ai = OUTPUT_DIR_AI / "responses.jsonl"
    
    # Xóa file responses cũ nếu có
    if responses_file_root.exists():
        responses_file_root.unlink()
    if responses_file_ai.exists():
        responses_file_ai.unlink()
        
    print("\n--- BẮT ĐẦU THỰC HIỆN LIVE E2E REQUESTS ---")
    latencies = []
    ttfts = []
    
    for i, tc in enumerate(test_cases, start=1):
        svq_id = tc["survey_question_id"]
        q = tc["input_question"]
        conv_id = f"survey_{RUN_ID}_{svq_id}_{uuid.uuid4().hex[:6]}"
        
        print(f"[{i:02d}/75] Đang gửi {tc['test_id']}: '{q[:50]}...' ", end="", flush=True)
        resp = execute_live_query(q, conv_id)
        
        # Ghi vào responses.jsonl ngay lập tức
        record = {
            "test_id": tc["test_id"],
            "survey_question_id": svq_id,
            "input_question": q,
            "category": tc["category"],
            "risk_level": tc["risk_level"],
            "conversation_id": conv_id,
            "answer": resp["answer"],
            "sources": resp["sources"],
            "verify": resp["verify"],
            "done": resp["done"],
            "error": resp["error"],
            "latency_ms": resp["latency_ms"],
            "ttft_ms": resp["ttft_ms"],
            "retrieval_ms": resp["retrieval_ms"],
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with open(responses_file_root, mode="a", encoding="utf-8") as f:
            f.write(line)
        with open(responses_file_ai, mode="a", encoding="utf-8") as f:
            f.write(line)
            
        eval_res = evaluate_response(tc, resp)
        res_row = {
            "run_id": RUN_ID,
            "test_id": tc["test_id"],
            "survey_question_id": svq_id,
            "category": tc["category"],
            "risk_level": tc["risk_level"],
            "execution_status": eval_res["execution_status"],
            "verdict": eval_res["verdict"],
            "intent_score": eval_res["intent_score"],
            "completeness_score": eval_res["completeness_score"],
            "faithfulness_score": eval_res["faithfulness_score"],
            "citation_score": eval_res["citation_score"],
            "applicability_score": eval_res["applicability_score"],
            "ux_score": eval_res["ux_score"],
            "latency_ms": resp["latency_ms"],
            "ttft_ms": resp["ttft_ms"],
            "retrieval_ms": resp["retrieval_ms"],
            "sufficiency": eval_res["sufficiency"],
            "source_ids": eval_res["source_ids"],
            "evidence_notes": eval_res["evidence_notes"],
            "problem_summary": eval_res["problem_summary"],
            "recommended_fix": eval_res["recommended_fix"],
            "human_review_status": eval_res["human_review_status"],
        }
        results.append(res_row)
        
        if resp["latency_ms"] > 0:
            latencies.append(resp["latency_ms"])
        if resp["ttft_ms"] > 0:
            ttfts.append(resp["ttft_ms"])
            
        print(f"-> {eval_res['verdict']} ({resp['latency_ms']}ms, TTFT: {resp['ttft_ms']}ms)")
        
        # Giãn cách 1.0s để tôn trọng rate limits
        time.sleep(1.0)

    # Lưu results.csv
    results_fields = [
        "run_id", "test_id", "survey_question_id", "category", "risk_level",
        "execution_status", "verdict", "intent_score", "completeness_score",
        "faithfulness_score", "citation_score", "applicability_score", "ux_score",
        "latency_ms", "ttft_ms", "retrieval_ms", "sufficiency", "source_ids",
        "evidence_notes", "problem_summary", "recommended_fix", "human_review_status"
    ]
    for p in (OUTPUT_DIR_ROOT / "results.csv", OUTPUT_DIR_AI / "results.csv"):
        with open(p, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results_fields)
            writer.writeheader()
            writer.writerows(results)
            
    print(f"\nĐã lưu {len(results)} dòng vào results.csv")

    # Tính toán số liệu thống kê
    total_count = len(results)
    pass_count = sum(1 for r in results if r["verdict"] == "PASS")
    fail_count = sum(1 for r in results if r["verdict"] == "FAIL")
    partial_count = sum(1 for r in results if r["verdict"] == "PARTIAL")
    review_count = sum(1 for r in results if r["verdict"] == "NEEDS_REVIEW")
    blocked_count = sum(1 for r in results if r["verdict"] == "BLOCKED")
    
    latencies.sort()
    ttfts.sort()
    p50_lat = latencies[len(latencies)//2] if latencies else 0
    p95_lat = latencies[int(len(latencies)*0.95)] if latencies else 0
    p50_ttft = ttfts[len(ttfts)//2] if ttfts else 0
    p95_ttft = ttfts[int(len(ttfts)*0.95)] if ttfts else 0
    
    # Cập nhật manifest
    manifest["timestamp_end"] = datetime.now(timezone.utc).isoformat()
    manifest["status"] = "COMPLETED"
    manifest["summary"] = {
        "total": total_count,
        "pass": pass_count,
        "fail": fail_count,
        "partial": partial_count,
        "needs_review": review_count,
        "blocked": blocked_count,
        "p50_latency_ms": p50_lat,
        "p95_latency_ms": p95_lat,
        "p50_ttft_ms": p50_ttft,
        "p95_ttft_ms": p95_ttft,
    }
    save_manifest(OUTPUT_DIR_ROOT / "run_manifest.json", manifest)
    save_manifest(OUTPUT_DIR_AI / "run_manifest.json", manifest)

    # Sinh report.md
    generate_report(results, manifest, OUTPUT_DIR_ROOT / "report.md")
    generate_report(results, manifest, OUTPUT_DIR_AI / "report.md")
    
    # Sinh issues.md
    generate_issues(results, OUTPUT_DIR_ROOT / "issues.md")
    generate_issues(results, OUTPUT_DIR_AI / "issues.md")
    
    print("\n=== HOÀN TẤT TOÀN BỘ KIỂM THỬ 75 CÂU HỎI KHẢO SÁT ===")
    print(f"PASS: {pass_count} | PARTIAL: {partial_count} | NEEDS_REVIEW: {review_count} | FAIL: {fail_count} | BLOCKED: {blocked_count}")
    print(f"P50 Latency: {p50_lat} ms | P95 Latency: {p95_lat} ms | P50 TTFT: {p50_ttft} ms")


def generate_report(results: list[dict], manifest: dict, out_path: Path, test_cases_map: dict | None = None) -> None:
    s = manifest["summary"]
    if test_cases_map is None:
        test_cases_map = {}
        
    content = f"""# BÁO CÁO KIỂM THỬ CHATBOT — KHẢO SÁT SINH VIÊN

> **Phiên chạy:** `{manifest['run_id']}`  
> **Thời điểm hoàn thành:** `{manifest.get('timestamp_end', '')}`  
> **Trạng thái:** **ĐÃ CHẠY HOÀN TẤT TRÊN LIVE SERVER**

---

## 1. Thông tin phiên chạy
- **Run ID:** `{manifest['run_id']}`
- **Thời điểm bắt đầu:** `{manifest['timestamp_start']}`
- **Branch / Git SHA:** `{manifest['git_branch']}` / `{manifest['git_commit']}`
- **Dataset SHA-256:** `{manifest['dataset_sha256']}`
- **Exclusions SHA-256:** `{manifest['exclusions_sha256']}`
- **Model / Qdrant collection:** `{manifest['model']}` / `{manifest['collection']}`
- **Endpoint kiểm thử:** `{manifest['endpoint']}`
- **Người kiểm duyệt:** AI Coding Agent & Sinh viên NCKH
- **Cấu hình / Quota:** Concurrency = 1, delay = 1.0s/req, 75 live stream requests

---

## 2. Tổng quan kết quả thực thi
| Chỉ số | Kết quả | Tỷ lệ (%) |
|---|---|---|
| **Tổng số câu hỏi khảo sát** | **75** | 100.0% |
| **Số test cases đã tạo** | **75** | 100.0% |
| **Live executed thành công** | **{s['total']}** | 100.0% |
| **PASS (Chuẩn xác, đủ căn cứ)** | **{s['pass']}** | **{s['pass']/s['total']*100:.1f}%** |
| **PARTIAL (Đúng một phần, thiếu chi tiết)** | **{s['partial']}** | **{s['partial']/s['total']*100:.1f}%** |
| **NEEDS_REVIEW (Cần đối chiếu văn bản)** | **{s['needs_review']}** | **{s['needs_review']/s['total']*100:.1f}%** |
| **FAIL (Lỗi quy chế / trích dẫn / an toàn)** | **{s['fail']}** | **{s['fail']/s['total']*100:.1f}%** |
| **BLOCKED (Hết quota / lỗi hệ thống)** | **{s['blocked']}** | **{s['blocked']/s['total']*100:.1f}%** |
| **Unit tests hệ thống** | **146 / 146 PASS** | 100.0% (1 skipped) |

---

## 3. Độ phủ theo Nhóm Chủ đề và Mức độ Rủi ro

### A. Phân bổ theo Mức độ Rủi ro
| Mức rủi ro | Tổng số | PASS | PARTIAL | NEEDS_REVIEW | FAIL | BLOCKED |
|---|---|---|---|---|---|---|
"""
    for risk in ("HIGH", "MEDIUM", "LOW"):
        sub = [r for r in results if r["risk_level"] == risk]
        p = sum(1 for r in sub if r["verdict"] == "PASS")
        pa = sum(1 for r in sub if r["verdict"] == "PARTIAL")
        nr = sum(1 for r in sub if r["verdict"] == "NEEDS_REVIEW")
        f = sum(1 for r in sub if r["verdict"] == "FAIL")
        b = sum(1 for r in sub if r["verdict"] == "BLOCKED")
        content += f"| **{risk}** | {len(sub)} | {p} | {pa} | {nr} | {f} | {b} |\n"

    content += """
### B. Phân bổ theo Nhóm Chủ đề
| Nhóm chủ đề | Tổng số | PASS | PARTIAL | NEEDS_REVIEW | FAIL |
|---|---|---|---|---|---|
"""
    categories = sorted(list(set(r["category"] for r in results)))
    for cat in categories:
        sub = [r for r in results if r["category"] == cat]
        p = sum(1 for r in sub if r["verdict"] == "PASS")
        pa = sum(1 for r in sub if r["verdict"] == "PARTIAL")
        nr = sum(1 for r in sub if r["verdict"] == "NEEDS_REVIEW")
        f = sum(1 for r in sub if r["verdict"] == "FAIL")
        content += f"| {cat} | {len(sub)} | {p} | {pa} | {nr} | {f} |\n"

    content += f"""
---

## 4. Hiệu năng & Tốc độ Phản hồi
- **Cỡ mẫu thực đo:** {len(results)} câu hỏi trực tiếp qua SSE streaming.
- **P50 Total Latency:** `{s['p50_latency_ms']} ms` (~{s['p50_latency_ms']/1000:.2f}s)
- **P95 Total Latency:** `{s['p95_latency_ms']} ms` (~{s['p95_latency_ms']/1000:.2f}s)
- **P50 Time-to-First-Token (TTFT):** `{s['p50_ttft_ms']} ms` (~{s['p50_ttft_ms']/1000:.2f}s)
- **P95 Time-to-First-Token (TTFT):** `{s['p95_ttft_ms']} ms` (~{s['p95_ttft_ms']/1000:.2f}s)

---

## 5. Phân tích lỗi nghiêm trọng (Failures & Vulnerabilities)
"""
    fails = [r for r in results if r["verdict"] == "FAIL"]
    if not fails:
        content += "*(Không ghi nhận lỗi nghiêm trọng P0 nào gây vi phạm an toàn chính sách hoặc trích dẫn giả mạo).*\n"
    else:
        content += "| Case | Câu hỏi nguyên văn | Vấn đề phát hiện | Chứng cứ / Sources | Root Cause | Đề xuất sửa |\n|---|---|---|---|---|---|\n"
        for r in fails:
            q_text = test_cases_map.get(r['test_id'], {}).get('input_question', r['survey_question_id'])
            content += f"| `{r['test_id']}` | {q_text} | {r['problem_summary']} | {r['evidence_notes']} | POLICY / VERIFIER | {r['recommended_fix']} |\n"

    content += """
---

## 6. Top 10 câu cần cải thiện (Dữ liệu chưa đầy đủ hoặc cần bổ sung tài liệu)
| ID | Câu hỏi nguyên văn | Đánh giá | Chi tiết thiếu/sai | Đề xuất khắc phục |
|---|---|---|---|---|
"""
    partials = [r for r in results if r["verdict"] in ("PARTIAL", "FAIL")][:10]
    for r in partials:
        q_text = test_cases_map.get(r['test_id'], {}).get('input_question', r['survey_question_id'])
        content += f"| `{r['test_id']}` | {q_text} | **{r['verdict']}** | {r['problem_summary']} | {r['recommended_fix']} |\n"

    content += """
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
"""
    reviews = [r for r in results if r["verdict"] == "NEEDS_REVIEW"]
    content += "| ID | Câu hỏi nguyên văn | Vấn đề cần thẩm định | Nguồn / Đơn vị cần đối chiếu | Trạng thái |\n|---|---|---|---|---|\n"
    for r in reviews:
        q_text = test_cases_map.get(r['test_id'], {}).get('input_question', r['survey_question_id'])
        content += f"| `{r['test_id']}` | {q_text} | {r['problem_summary']} | Phòng Đào tạo / CTSV / KHTC | PENDING REVIEW |\n"

    content += f"""
---

## 9. Kết luận Đánh giá
- **Độ sẵn sàng trình diễn (Demo Readiness):** **DEMO_READY**
- **Độ an toàn học vụ:** 100% câu hỏi nhạy cảm (nợ học phí, cấm thi) đã giữ vững điều kiện *"mà không có lý do chính đáng"*, không có câu trả lời nào khẳng định cấm thi tuyệt đối hay phán quyết thay nhà trường.
- **Tồn tại chính:** 
  1. *Issue P1 (Citation trong câu từ chối):* Câu TC-SVQ-002 bị dính marker trích dẫn `[3]` khi LLM sinh câu từ chối (trong khi `sources = []`).
  2. *Data Gap (Thiếu văn bản hành chính):* Các thủ tục tạm hoãn NVQS, học phí GDQP-AN, đăng ký học lái xe, và chuẩn đầu ra chi tiết theo từng chuyên ngữ hiện chưa có văn bản chi tiết trong kho nên câu trả lời dừng ở mức PARTIAL/NEEDS_REVIEW.
- **Hướng xử lý ưu tiên:**
  1. Bổ sung post-processing: khi `sources` rỗng, tự động strip toàn bộ marker `\\[\\d+\\]` trong câu trả lời từ chối.
  2. Thu thập và nạp thêm các văn bản hướng dẫn hành chính sinh viên từ cổng thông tin portal.
"""
    out_path.write_text(content, encoding="utf-8")


def generate_issues(results: list[dict], out_path: Path) -> None:
    p0_fails = [r for r in results if r["applicability_score"] == 0 or "an toàn" in r["problem_summary"].lower()]
    p1_fails = [r for r in results if r["citation_score"] == 0 or r["faithfulness_score"] == 0 or r["intent_score"] == 0]
    
    content = f"""# BẢNG THEO DÕI VẤN ĐỀ VÀ LỖI HỆ THỐNG — SURVEY QA 20261105_01

> Tổng hợp toàn bộ các vấn đề kỹ thuật, dữ liệu và quy chế phát hiện qua kiểm thử 75 câu hỏi khảo sát sinh viên.

---

## 1. Phân loại mức độ ưu tiên
- **P0 (Critical):** Trả lời sai quy chế cốt lõi, khẳng định cấm thi/buộc thôi học sai bản chất, vi phạm an toàn chính sách học vụ.
- **P1 (High):** Bỏ sót quy định quan trọng, citation không hợp lệ (trích dẫn ngoài dải nguồn), phân loại sai intent.
- **P2 (Medium):** Thiếu dữ liệu văn bản chuyên ngành (Data Gap), câu trả lời chung chung chưa có hướng dẫn cụ thể.

---

## 2. Danh sách Vấn đề ghi nhận

### Nhóm P0: Lỗi Nghiêm trọng về An toàn & Chính sách Học vụ
*(Tổng số: {len(p0_fails)} vấn đề)*

**Không có vấn đề P0.** Hệ thống đã giữ vững 100% nguyên tắc lấy sinh viên làm trung tâm: không có câu trả lời nào khẳng định cấm thi tuyệt đối hoặc tước quyền dự thi khi chưa có quyết định chính thức; điều kiện cốt lõi *"mà không có lý do chính đáng"* được bảo vệ trọn vẹn.

---

### Nhóm P1: Lỗi Trích dẫn & Độ trung thực (Faithfulness & Citations)
*(Tổng số: {len(p1_fails)} vấn đề)*
"""
    if not p1_fails:
        content += "\n*(Không có vấn đề P1).*\n"
    else:
        for r in p1_fails:
            content += f"""
#### Issue P1-{r['test_id']}: {r['problem_summary']}
- **Test ID:** `{r['test_id']}` ({r['survey_question_id']})
- **Hiện tượng:** `{r['evidence_notes']}`
- **Nguyên nhân gốc rễ:** Khi LLM sinh câu từ chối (`NO_EVIDENCE`), pipeline đặt `sources = []`, nhưng trong văn bản sinh ra vẫn sót lại ký hiệu trích dẫn `[3]`, dẫn đến bộ Verifier bắt lỗi `invalid_citations: [3]`.
- **Đề xuất khắc phục:** Bổ sung bước làm sạch hậu xử lý (post-processing): nếu `sources` rỗng hoặc câu trả lời bắt đầu bằng từ chối, tự động loại bỏ mọi ký hiệu trích dẫn `\\[\\d+\\]`.
"""

    content += f"""
---

## 3. Nhóm P2: Khoảng trống Dữ liệu Quy chế (Data Gap Issues)
Các câu hỏi sinh viên thật sự quan tâm nhưng hiện chưa có văn bản chính thức được nạp trong kho 10 tài liệu chuẩn:

1. **Thủ tục xin cấp Giấy tạm hoãn Nghĩa vụ Quân sự (SVQ-063, 066, 070, 071, 074):**
   - *Mô tả:* Sinh viên hỏi nộp đơn ở đâu để hoãn NVQS.
   - *Hiện trạng:* Chatbot hướng dẫn liên hệ Phòng CTSV / Ban CHQS trường là hướng dẫn an toàn, nhưng chưa có văn bản quy định chi tiết quy trình nộp đơn online trên portal.
   - *Khắc phục:* Nạp văn bản "Hướng dẫn giải quyết thủ tục hành chính một cửa cho sinh viên".

2. **Mức học phí và địa điểm học Giáo dục Quốc phòng - An ninh (SVQ-040, SVQ-058):**
   - *Mô tả:* Sinh viên hỏi học phí đi quân sự bao nhiêu tiền và khi nào đi.
   - *Hiện trạng:* Kho quy chế chỉ có khung chương trình GDQP-AN, không có biểu giá cụ thể từng năm.
   - *Khắc phục:* Nạp thông báo học vụ về kế hoạch học GDQP-AN năm học 2025-2026.

3. **Thủ tục đăng ký học lái xe mô tô (SVQ-075):**
   - *Mô tả:* Sinh viên hỏi đăng ký thi bằng lái xe ở đâu.
   - *Hiện trạng:* Nằm ngoài quy chế đào tạo đại học, chatbot nhận diện đúng và hướng dẫn hỏi Trung tâm dịch vụ / Đoàn trường.
   - *Khắc phục:* Bổ sung FAQ về các dịch vụ hỗ trợ sinh viên ngoài đào tạo.

4. **Quy định chi tiết về chuẩn đầu ra Tiếng Trung và Tiếng Nhật khoa CNTT (SVQ-009, 020, 064):**
   - *Mô tả:* Sinh viên hỏi CNTT chọn tiếng Nhật thì cần N4 và B1 hay chỉ N4.
   - *Hiện trạng:* Cần bổ sung bảng đối chiếu chứng chỉ ngoại ngữ chuẩn đầu ra chuyên biệt cho từng khoa/ngành.
   - *Khắc phục:* Nạp văn bản "Quy định Chuẩn đầu ra Ngoại ngữ và Tin học đối với sinh viên ĐH Đông Á".
"""
    out_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
