"""Bộ kiểm thử hồi quy cho Answer Sufficiency, Answer Generation Rules, và Verification Badges.

Bao gồm 10 nhóm test case theo yêu cầu TASK G:
- G1: Điều kiện xét học bổng (Chính sách chung, thiếu số liệu/tiêu chí chi tiết).
- G2: Nợ học phí và quyền dự thi.
- G3: Chuẩn đầu ra ngoại ngữ.
- G4: Điều kiện tốt nghiệp.
- G5: Đăng ký học lại.
- G6: Thời khóa biểu.
- G7: Câu hỏi không có tài liệu (NO_EVIDENCE).
- G8: Câu hỏi bằng chứng một phần (PARTIAL).
- G9: Câu hỏi tiếp nối ("là sao?", "giải thích dễ hiểu hơn").
- G10: Câu hỏi chuyển chủ đề.
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from app.core.prompts import REFUSE_MESSAGE
from app.pipeline.generator.verifier import (
    determine_sufficiency,
    evaluate_verification,
    unsupported_numbers,
    validate_citations,
)
from app.pipeline.query_transformation.context_resolver import resolve_context
from app.pipeline.rag_pipeline import answer, prepare


class TestCitationAndNumberVerification(unittest.TestCase):
    """Kiểm tra chức năng xác minh trích dẫn và số liệu (Task E)."""

    def test_validate_citations_valid_range(self):
        answer_text = "Sinh viên phải đạt chuẩn đầu ra B1 [1] và nộp chứng chỉ trước đợt xét tốt nghiệp [2]."
        res = validate_citations(answer_text, max_chunks=3)
        self.assertTrue(res["has_citations"])
        self.assertTrue(res["citations_valid"])
        self.assertEqual(res["citations"], [1, 2])
        self.assertEqual(res["invalid_citations"], [])

    def test_validate_citations_out_of_range(self):
        answer_text = "Theo quy định [1], mức học phí được tính theo [5]."
        res = validate_citations(answer_text, max_chunks=2)
        self.assertTrue(res["has_citations"])
        self.assertFalse(res["citations_valid"])
        self.assertIn(5, res["invalid_citations"])

    def test_unsupported_numbers_detection(self):
        context = ["Mức học bổng khuyến khích loại giỏi là 5.000.000 đồng/học kỳ."]
        # LLM viết sai con số thành 10.000.000
        answer_text = "Học bổng loại giỏi là 10.000.000 đồng [1]."
        bad = unsupported_numbers(answer_text, context)
        self.assertIn("10000000", [b.replace(".", "") for b in bad])

    def test_unsupported_numbers_matches_valid(self):
        context = ["Sinh viên phải tích lũy tối thiểu 120 tín chỉ để tốt nghiệp."]
        answer_text = "Bạn cần tích lũy tối thiểu 120 tín chỉ [1]."
        bad = unsupported_numbers(answer_text, context)
        self.assertEqual(bad, [])

    def test_refusal_with_valid_citations_preserves_sources_and_citations(self):
        """Kiểm tra trường hợp TC-SVQ-002: Từ chối có điều kiện kèm trích dẫn ngữ cảnh [3]."""
        chunks = [
            {"text": "Đoạn 1", "doc_name": "Doc 1"},
            {"text": "Đoạn 2", "doc_name": "Doc 2"},
            {"text": "Chuẩn đầu ra ngoại ngữ không chuyên ngữ từ khóa 2022 trở đi áp dụng theo quy định.", "doc_name": "2023_8_23_16_29_59n"},
        ]
        ans_text = (
            "Mình chưa tìm thấy thông tin này trong tài liệu hiện có. "
            "Tài liệu hiện tại chỉ quy định về chuẩn đầu ra và việc học ngoại ngữ đối với sinh viên các ngành không chuyên ngữ từ khóa 2022 trở đi [3]. "
            "Bạn vui lòng liên hệ Khoa chủ quản để được hướng dẫn."
        )
        res = evaluate_verification(
            question="Sinh viên khoa ngôn ngữ trung có đi thực tập nước ngoài không?",
            answer=ans_text,
            chunks=chunks,
            refused=False,
        )
        self.assertEqual(res["citations"], [3])
        self.assertEqual(res["invalid_citations"], [])
        self.assertTrue(res["citations_valid"])
        self.assertEqual(res["sufficiency"], "PARTIAL")
        self.assertIn("Có trích dẫn nguồn", res["badges"])
        for b in res["badges"]:
            self.assertNotIn("Trích dẫn ngoài phạm vi", b)


class TestAnswerSufficiencyClassification(unittest.TestCase):
    """Kiểm tra phân loại 4 trạng thái Answer Sufficiency (Task C)."""

    def test_sufficiency_no_evidence_when_refused(self):
        state = determine_sufficiency(
            question="Cổng trường có những xe buýt nào?",
            answer=REFUSE_MESSAGE,
            chunks=[],
            refused=True,
            refuse_reason="out_of_scope",
        )
        self.assertEqual(state, "NO_EVIDENCE")

    def test_sufficiency_no_evidence_starts_with_refusal(self):
        state = determine_sufficiency(
            question="Xe buýt",
            answer="Mình chưa tìm thấy thông tin này trong tài liệu hiện có. Bạn vui lòng...",
            chunks=[{"text": "Đoạn không liên quan"}],
            refused=False,
        )
        self.assertEqual(state, "NO_EVIDENCE")

    def test_sufficiency_partial_when_acknowledging_missing_info(self):
        question = "Điều kiện xét học bổng và mức tiền cụ thể là bao nhiêu?"
        answer_text = (
            "Nhà trường có chính sách cấp học bổng khuyến khích học tập cho sinh viên [1]. "
            "Tuy nhiên, tài liệu quy chế hiện có chưa quy định chi tiết về mức tiền cụ thể."
        )
        chunks = [{"text": "Sinh viên được xét cấp học bổng khuyến khích theo quy chế."}]
        state = determine_sufficiency(question, answer_text, chunks)
        self.assertEqual(state, "PARTIAL")

    def test_sufficiency_insufficient_when_no_concrete_details(self):
        question = "Điểm rèn luyện tối thiểu để nhận học bổng là mấy?"
        answer_text = (
            "Trong tài liệu hiện có chỉ đề cập chính sách chung về học bổng, "
            "chưa có quy định chi tiết về tiêu chí điểm rèn luyện cụ thể."
        )
        chunks = [{"text": "Sinh viên được hưởng quyền lợi học bổng theo quy định chung."}]
        state = determine_sufficiency(question, answer_text, chunks)
        self.assertEqual(state, "INSUFFICIENT")

    def test_sufficiency_sufficient_with_valid_citations(self):
        question = "Chuẩn đầu ra tiếng Anh đối với ngành không chuyên ngữ là gì?"
        answer_text = "Sinh viên các ngành không chuyên ngữ phải đạt chuẩn đầu ra ngoại ngữ Bậc 3/6 (B1) [1]."
        chunks = [{"text": "Chuẩn đầu ra ngoại ngữ đối với ngành không chuyên là Bậc 3/6 tương đương B1."}]
        state = determine_sufficiency(question, answer_text, chunks)
        self.assertEqual(state, "SUFFICIENT")


class TestDynamicVerificationBadges(unittest.TestCase):
    """Kiểm tra sinh nhãn hiển thị động theo Task E (loại bỏ badge cứng)."""

    def test_badges_sufficient_answer(self):
        chunks = [{"text": "Sinh viên đạt 120 tín chỉ được xét tốt nghiệp."}]
        res = evaluate_verification(
            question="Điều kiện tốt nghiệp?",
            answer="Sinh viên cần tích lũy tối thiểu 120 tín chỉ [1].",
            chunks=chunks,
        )
        self.assertEqual(res["sufficiency"], "SUFFICIENT")
        self.assertIn("Có trích dẫn nguồn", res["badges"])
        self.assertIn("Đã đối chiếu nguồn cho các khẳng định", res["badges"])
        self.assertNotIn("Chưa đủ bằng chứng để kết luận", res["badges"])

    def test_badges_partial_answer(self):
        chunks = [{"text": "Nhà trường có quỹ học bổng khuyến khích học tập."}]
        res = evaluate_verification(
            question="Mức học bổng và điều kiện nhận?",
            answer=(
                "Nhà trường cấp học bổng khuyến khích học tập [1]. "
                "Tuy nhiên, tài liệu quy chế hiện có chưa quy định chi tiết về mức học bổng cụ thể."
            ),
            chunks=chunks,
        )
        self.assertEqual(res["sufficiency"], "PARTIAL")
        self.assertIn("Có trích dẫn nguồn", res["badges"])
        self.assertIn("Chưa đủ bằng chứng để kết luận (Một phần)", res["badges"])
        self.assertNotIn("Đã đối chiếu nguồn cho các khẳng định", res["badges"])

    def test_badges_no_evidence_answer(self):
        res = evaluate_verification(
            question="Hỏi ngoài lề",
            answer=REFUSE_MESSAGE,
            chunks=[],
            refused=True,
        )
        self.assertEqual(res["sufficiency"], "NO_EVIDENCE")
        self.assertIn("Chưa đủ bằng chứng để kết luận", res["badges"])
        self.assertNotIn("Có trích dẫn nguồn", res["badges"])
        self.assertNotIn("Đã đối chiếu nguồn cho các khẳng định", res["badges"])


class TestRegression10Groups(unittest.TestCase):
    """Kiểm thử hồi quy 10 nhóm câu hỏi yêu cầu trong TASK G."""

    # G1: Điều kiện xét học bổng
    def test_g1_scholarship_general_policy(self):
        chunks = [{
            "text": "Điều 16: Nhà trường phối hợp các tổ chức lập quỹ học bổng tài trợ cho sinh viên xuất sắc, khó khăn.",
            "doc_name": "2021_8_5_8_33_34A",
        }]
        ans_text = (
            "Nhà trường có các quỹ học bổng tài trợ cho sinh viên xuất sắc hoặc có hoàn cảnh khó khăn [1]. "
            "Tuy nhiên, tài liệu quy chế hiện có chưa quy định chi tiết về mức điểm GPA hay mức tiền cụ thể."
        )
        v = evaluate_verification("Điều kiện xét học bổng?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "PARTIAL")
        self.assertIn("Có trích dẫn nguồn", v["badges"])

    # G2: Nợ học phí và quyền dự thi
    def test_g2_tuition_debt_exam(self):
        chunks = [{
            "text": "Điều 10: Sinh viên chưa hoàn thành nghĩa vụ học phí đúng hạn sẽ không có tên trong danh sách dự thi kết thúc học phần.",
            "doc_name": "QĐ Học phí",
        }]
        ans_text = "Bạn không được dự thi nếu còn nợ học phí quá thời hạn quy định [1]."
        v = evaluate_verification("Em nợ học phí thì có được dự thi không?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "SUFFICIENT")
        self.assertTrue(v["citations_valid"])
        self.assertIn("Đã đối chiếu nguồn cho các khẳng định", v["badges"])

    # G3: Chuẩn đầu ra ngoại ngữ
    def test_g3_language_exit_requirement(self):
        chunks = [{
            "text": "Điều 4: Sinh viên các ngành không chuyên ngữ phải đạt chuẩn đầu ra ngoại ngữ Bậc 3/6 theo Khung năng lực ngoại ngữ Việt Nam (tương đương B1 CEFR).",
            "doc_name": "2023_8_23_16_29_59n",
        }]
        ans_text = "Chuẩn đầu ra ngoại ngữ là Bậc 3/6 (tương đương B1 CEFR) [1]."
        v = evaluate_verification("Chuẩn đầu ra tiếng Anh ngành không chuyên là gì?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "SUFFICIENT")
        self.assertIn("Có trích dẫn nguồn", v["badges"])
        self.assertIn("Đã đối chiếu nguồn cho các khẳng định", v["badges"])

    # G4: Điều kiện tốt nghiệp
    def test_g4_graduation_conditions(self):
        chunks = [{
            "text": "Điều 25: Điều kiện tốt nghiệp: tích lũy đủ số tín chỉ, điểm trung bình tích lũy từ 2.0 trở lên, đạt chuẩn đầu ra ngoại ngữ và tin học, không bị truy cứu trách nhiệm hình sự.",
            "doc_name": "Quy chế đào tạo",
        }]
        ans_text = (
            "Để tốt nghiệp, bạn cần đáp ứng các điều kiện sau: tích lũy đủ số tín chỉ, "
            "điểm GPA từ 2.0 trở lên, hoàn thành chuẩn đầu ra ngoại ngữ và tin học [1]."
        )
        v = evaluate_verification("Điều kiện tốt nghiệp là gì?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "SUFFICIENT")
        self.assertEqual(v["unsupported_numbers"], [])

    # G5: Đăng ký học lại
    def test_g5_re_enrollment(self):
        chunks = [{
            "text": "Điều 14: Sinh viên bị điểm F hoặc bị cấm thi phải đăng ký học lại học phần đó ở học kỳ tiếp theo có mở lớp.",
            "doc_name": "Quy chế đào tạo",
        }]
        ans_text = "Bạn có thể đăng ký học lại ở học kỳ tiếp theo ngay khi có lớp mở học phần đó [1]."
        v = evaluate_verification("Bị cấm thi thì khi nào được học lại?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "SUFFICIENT")

    # G6: Thời khóa biểu
    def test_g6_schedule_registration(self):
        chunks = [{
            "text": "Điều 8: Từ năm thứ hai, sinh viên tự đăng ký thời khóa biểu các học phần theo lộ trình kế hoạch học tập cá nhân.",
            "doc_name": "Quy chế đào tạo",
        }]
        ans_text = "Sinh viên năm 2 phải tự đăng ký thời khóa biểu theo kế hoạch mở lớp của Nhà trường [1]."
        v = evaluate_verification("Lịch học năm 2 tự đăng ký hay trường sắp xếp?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "SUFFICIENT")

    # G7: Câu hỏi không có tài liệu (NO_EVIDENCE)
    def test_g7_no_evidence_out_of_scope(self):
        v = evaluate_verification(
            question="Cổng trường Đại học Đông Á có xe buýt nào đi qua?",
            answer=REFUSE_MESSAGE,
            chunks=[],
            refused=True,
            refuse_reason="out_of_scope",
        )
        self.assertEqual(v["sufficiency"], "NO_EVIDENCE")
        self.assertIn("Chưa đủ bằng chứng để kết luận", v["badges"])

    # G8: Câu hỏi bằng chứng một phần (PARTIAL)
    def test_g8_partial_evidence_question(self):
        chunks = [{
            "text": "Điều 12: Sinh viên được tạm hoãn tiến độ học tập tối đa 2 học kỳ chính vì lý do cá nhân.",
            "doc_name": "Quy chế đào tạo",
        }]
        ans_text = (
            "Bạn được tạm hoãn tối đa 2 học kỳ chính [1]. "
            "Tuy nhiên, tài liệu quy chế hiện có chưa quy định chi tiết về thủ tục bảo lưu đối với trường hợp du học tự túc."
        )
        v = evaluate_verification("Được hoãn mấy kỳ và thủ tục du học tự túc?", ans_text, chunks)
        self.assertEqual(v["sufficiency"], "PARTIAL")
        self.assertIn("Chưa đủ bằng chứng để kết luận (Một phần)", v["badges"])

    # G9: Câu hỏi tiếp nối
    def test_g9_follow_up_explanation(self):
        history = [
            {"role": "user", "content": "Chuẩn đầu ra ngoại ngữ là gì?"},
            {"role": "assistant", "content": "Chuẩn đầu ra là Bậc 3/6 hoặc B1 CEFR [1]."},
        ]
        res = resolve_context("là sao?", history=history, last_topic="Chuẩn đầu ra ngoại ngữ")
        self.assertEqual(res.action, "REEXPLAIN")

    # G10: Câu hỏi chuyển chủ đề
    def test_g10_topic_switch(self):
        history = [
            {"role": "user", "content": "Điều kiện xét học bổng là gì?"},
            {"role": "assistant", "content": "Nhà trường có quỹ học bổng theo quy định [1]."},
        ]
        res = resolve_context("Chuẩn đầu ra ngoại ngữ để tốt nghiệp là gì?", history=history, last_topic="Điều kiện xét học bổng")
        self.assertEqual(res.action, "NEW_TOPIC")

    @patch("app.pipeline.rag_pipeline.get_llm")
    @patch("app.pipeline.rag_pipeline.retrieve")
    def test_pipeline_refusal_with_citations_preserves_sources(self, mock_retrieve, mock_get_llm):
        """TC-SVQ-002: Khi LLM từ chối nhưng có trích dẫn [2], pipeline phải giữ sources và không báo lỗi citation."""
        mock_retrieve.return_value = {
            "chunks": [
                {"chunk_id": "c1", "doc_name": "Quy chế A", "dieu": "Điều 1", "score": 0.8, "text": "Quy định chung", "chuong": ""},
                {"chunk_id": "c2", "doc_name": "Quy chế B", "dieu": "Điều 2", "score": 0.7, "text": "Chuẩn đầu ra", "chuong": ""},
            ],
            "best_dense_score": 0.8,
            "expanded_query": "Sinh viên chuyên ngành X có được đi thực tập không?",
            "timing": {"retrieval_ms": 15},
        }
        mock_llm = MagicMock()
        mock_llm.generate.return_value = (
            "Mình chưa tìm thấy thông tin này trong tài liệu hiện có. "
            "Tài liệu hiện tại chỉ quy định về chuẩn đầu ra chung [2]. "
            "Bạn vui lòng liên hệ Khoa để được hỗ trợ."
        )
        mock_get_llm.return_value = mock_llm

        res = answer("Sinh viên chuyên ngành X có được đi thực tập không?")
        self.assertTrue(res["refused"])
        self.assertEqual(len(res["sources"]), 2)
        self.assertEqual(res["citations"], [2])
        self.assertEqual(res["invalid_citations"], [])
        self.assertEqual(res["sufficiency"], "PARTIAL")

    @patch("app.pipeline.rag_pipeline.get_llm")
    @patch("app.pipeline.rag_pipeline.retrieve")
    def test_pipeline_pure_refusal_clears_sources(self, mock_retrieve, mock_get_llm):
        """Khi LLM từ chối thuần túy không có citation, sources phải được làm rỗng."""
        mock_retrieve.return_value = {
            "chunks": [
                {"chunk_id": "c1", "doc_name": "Quy chế A", "dieu": "Điều 1", "score": 0.8, "text": "Quy định chung", "chuong": ""},
            ],
            "best_dense_score": 0.8,
            "expanded_query": "Câu hỏi ngoài phạm vi không có thông tin?",
            "timing": {"retrieval_ms": 15},
        }
        mock_llm = MagicMock()
        mock_llm.generate.return_value = (
            "Mình chưa tìm thấy thông tin này trong tài liệu hiện có. "
            "Bạn vui lòng liên hệ Phòng Đào tạo."
        )
        mock_get_llm.return_value = mock_llm

        res = answer("Câu hỏi ngoài phạm vi không có thông tin?")
        self.assertTrue(res["refused"])
        self.assertEqual(res["sources"], [])
        self.assertEqual(res["citations"], [])
        self.assertEqual(res["invalid_citations"], [])
        self.assertEqual(res["sufficiency"], "NO_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
