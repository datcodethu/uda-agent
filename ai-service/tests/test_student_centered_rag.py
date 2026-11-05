"""Bộ kiểm thử hồi quy cho Student-Centered RAG & Xử lý Chính sách Học vụ Nhạy cảm (TASK G).

Bao gồm:
1. Phân loại Ý định và Mức độ Rủi ro (Task A).
2. Kiểm chứng Khẳng định Claim-Level Verification (Task E).
3. 12 Test cases tình huống nhạy cảm (Task G):
   - T1: BHYT có quan trọng không?
   - T2: BHYT có bắt buộc không?
   - T3: Em đã có BHYT theo diện khác thì có phải đóng thêm không?
   - T4: Không đóng BHYT có bị cấm thi không?
   - T5: Chậm học phí có được thi không?
   - T6: Em còn nợ 5 triệu học phí thì sao?
   - T7: Em đã chuyển khoản nhưng hệ thống chưa cập nhật học phí.
   - T8: Em có thể xin gia hạn học phí không?
   - T9: Gia đình em khó khăn thì có chính sách hỗ trợ không?
   - T10: Không đủ điểm rèn luyện có ảnh hưởng học bổng không?
   - T11: Em bị cấm thi thì phải làm gì?
   - T12: Em có được tốt nghiệp nếu còn công nợ không?
"""
from __future__ import annotations

import unittest
from app.pipeline.generator.verifier import evaluate_verification, verify_claims
from app.pipeline.query_transformation.intent_classifier import (
    AcademicIntent,
    RiskLevel,
    classify_academic_intent_and_risk,
)


class TestIntentAndRiskClassification(unittest.TestCase):
    """Kiểm tra độ chính xác của bộ phân loại 8 ý định và 3 mức độ rủi ro (Task A)."""

    def test_benefit_intent(self):
        intent, risk = classify_academic_intent_and_risk("BHYT có quan trọng không?")
        self.assertEqual(intent, AcademicIntent.BENEFIT_EXPLANATION)
        self.assertEqual(risk, RiskLevel.LOW)

    def test_requirement_intent(self):
        intent, risk = classify_academic_intent_and_risk("BHYT có bắt buộc không?")
        self.assertEqual(intent, AcademicIntent.POLICY_REQUIREMENT)
        self.assertEqual(risk, RiskLevel.MEDIUM)

    def test_eligibility_intent(self):
        intent, risk = classify_academic_intent_and_risk("Chậm học phí có được thi không?")
        self.assertEqual(intent, AcademicIntent.ELIGIBILITY_CHECK)
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_consequence_intent(self):
        intent, risk = classify_academic_intent_and_risk("Không đóng BHYT có bị cấm thi không?")
        self.assertEqual(intent, AcademicIntent.ACADEMIC_CONSEQUENCE)
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_financial_difficulty_intent(self):
        intent, risk = classify_academic_intent_and_risk("Gia đình em khó khăn thì có chính sách hỗ trợ không?")
        self.assertEqual(intent, AcademicIntent.FINANCIAL_DIFFICULTY)
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_procedure_guidance_intent(self):
        intent, risk = classify_academic_intent_and_risk("Em đã chuyển khoản nhưng hệ thống chưa cập nhật học phí.")
        self.assertEqual(intent, AcademicIntent.PROCEDURE_GUIDANCE)
        self.assertEqual(risk, RiskLevel.HIGH)

    def test_personal_case_intent(self):
        intent, risk = classify_academic_intent_and_risk("Em còn nợ 5 triệu học phí thì sao?")
        self.assertEqual(intent, AcademicIntent.PERSONAL_CASE)
        self.assertEqual(risk, RiskLevel.HIGH)


class TestClaimLevelVerification(unittest.TestCase):
    """Kiểm tra cơ chế Claim-Level Verification chống phát ngôn tuyệt đối (Task E)."""

    def test_unqualified_absolute_ban_flagged(self):
        bad_answer = "Không được. Bạn chắc chắn bị cấm thi [1]."
        res = verify_claims(bad_answer, contexts=["Điều 4 quy chế học vụ"])
        self.assertFalse(res["valid"])
        self.assertTrue(len(res["warnings"]) > 0)
        self.assertIn("Khẳng định tuyệt đối chưa nêu điều kiện kích hoạt", res["warnings"][0])

    def test_qualified_conditional_statement_passes(self):
        good_answer = (
            "Việc chậm nộp học phí có thể ảnh hưởng đến điều kiện dự thi nếu không có lý do chính đáng "
            "theo quy định của Nhà trường [1]. Bạn nên kiểm tra lại với Phòng Tài chính."
        )
        res = verify_claims(good_answer, contexts=["Quy chế công tác sinh viên"])
        self.assertTrue(res["valid"])
        self.assertEqual(res["warnings"], [])

    def test_ungrounded_heavy_sanctions_flagged(self):
        # Đoạn ngữ cảnh không có từ "buộc thôi học"
        context = ["Sinh viên bị cấm thi kết thúc học phần nếu vi phạm quy chế."]
        bad_answer = "Bạn sẽ bị buộc thôi học nếu vi phạm điều này [1]."
        res = verify_claims(bad_answer, contexts=context)
        self.assertFalse(res["valid"])
        self.assertTrue(any("buộc thôi học" in w for w in res["warnings"]))

    def test_badge_demoted_on_unqualified_claim(self):
        chunks = [{"text": "Sinh viên cố tình chậm nộp học phí mà không có lý do chính đáng sẽ bị cấm thi."}]
        bad_answer = "Bạn chắc chắn bị cấm thi [1]."
        eval_res = evaluate_verification("Chậm học phí có được thi không?", bad_answer, chunks)
        # Không được cấp nhãn "Đã đối chiếu nguồn cho các khẳng định"
        self.assertNotIn("Đã đối chiếu nguồn cho các khẳng định", eval_res["badges"])
        self.assertIn("Cần đối chiếu điều kiện áp dụng", eval_res["badges"])


class TestTwelveSensitiveScenarios(unittest.TestCase):
    """Kiểm thử hồi quy 12 tình huống nhạy cảm theo TASK G."""

    # T1: BHYT có quan trọng không?
    def test_t1_bhyt_importance_benefit_first(self):
        intent, risk = classify_academic_intent_and_risk("BHYT có quan trọng không?")
        self.assertEqual(intent, AcademicIntent.BENEFIT_EXPLANATION)
        self.assertEqual(risk, RiskLevel.LOW)
        # Giả lập câu trả lời chuẩn: ưu tiên giải thích lợi ích, không đe dọa chế tài
        good_ans = (
            "Bảo hiểm y tế (BHYT) rất quan trọng đối với sinh viên [1]. Tham gia BHYT giúp bạn được chi trả "
            "phần lớn chi phí khám chữa bệnh, chăm sóc sức khỏe ban đầu tại trường và bảo vệ tài chính khi gặp sự cố sức khỏe [1]."
        )
        self.assertNotIn("cấm thi", good_ans)
        self.assertNotIn("kỷ luật", good_ans)
        v = evaluate_verification("BHYT có quan trọng không?", good_ans, [{"text": "Quy định về BHYT sinh viên"}])
        self.assertEqual(v["sufficiency"], "SUFFICIENT")
        self.assertTrue(v["claim_valid"])

    # T2: BHYT có bắt buộc không?
    def test_t2_bhyt_requirement(self):
        intent, risk = classify_academic_intent_and_risk("BHYT có bắt buộc không?")
        self.assertEqual(intent, AcademicIntent.POLICY_REQUIREMENT)
        good_ans = (
            "Theo quy định của Luật Bảo hiểm y tế và Quy chế công tác sinh viên của Trường Đại học Đông Á, "
            "tham gia BHYT là nghĩa vụ bắt buộc của mọi sinh viên [1]."
        )
        v = evaluate_verification("BHYT có bắt buộc không?", good_ans, [{"text": "Điều 4: Đóng học phí, BHYT đầy đủ"}])
        self.assertEqual(v["sufficiency"], "SUFFICIENT")

    # T3: Đã có BHYT theo diện khác
    def test_t3_bhyt_already_covered(self):
        intent, risk = classify_academic_intent_and_risk("Em đã có BHYT theo diện khác thì có phải đóng thêm không?")
        self.assertEqual(intent, AcademicIntent.ELIGIBILITY_CHECK)
        good_ans = (
            "Nếu bạn đã có thẻ BHYT theo diện chính sách (như thân nhân quân nhân, hộ nghèo, vùng an toàn khu), "
            "bạn không phải đóng trùng BHYT tại trường [1]. Bạn cần nộp bản sao thẻ BHYT còn hạn cho Nhà trường để được đối soát."
        )
        v = evaluate_verification("Có phải đóng thêm không?", good_ans, [{"text": "Quy định BHYT đối soát thẻ"}])
        self.assertTrue(v["claim_valid"])

    # T4: Không đóng BHYT có bị cấm thi không?
    def test_t4_bhyt_consequence_preserves_condition(self):
        intent, risk = classify_academic_intent_and_risk("Không đóng BHYT có bị cấm thi không?")
        self.assertEqual(intent, AcademicIntent.ACADEMIC_CONSEQUENCE)
        self.assertEqual(risk, RiskLevel.HIGH)
        # Bắt buộc phải có điều kiện: không có lý do chính đáng
        good_ans = (
            "Theo Khung kỷ luật của Nhà trường, hành vi cố tình không nộp BHYT mà không có lý do chính đáng "
            "có thể bị trừ điểm rèn luyện và xem xét cấm thi kết thúc học phần [1]. Bạn nên liên hệ Nhà trường để được hướng dẫn."
        )
        self.assertIn("không có lý do chính đáng", good_ans)
        v = evaluate_verification("Không đóng BHYT có bị cấm thi?", good_ans, [{"text": "Phụ lục khung kỷ luật"}])
        self.assertTrue(v["claim_valid"])

    # T5: Chậm học phí có được thi không?
    def test_t5_tuition_delay_not_absolute_ban(self):
        intent, risk = classify_academic_intent_and_risk("Chậm học phí có được thi không?")
        self.assertEqual(intent, AcademicIntent.ELIGIBILITY_CHECK)
        good_ans = (
            "Việc chậm đóng học phí có thể ảnh hưởng đến điều kiện dự thi nếu không có lý do chính đáng [1]. "
            "Tuy nhiên, nếu bạn có lý do khách quan, bạn nên làm đơn trình bày hoặc liên hệ ngay Phòng Kế toán - Tài chính "
            "để được xem xét trước khi danh sách thi được chốt chính thức."
        )
        v = evaluate_verification("Chậm học phí có được thi?", good_ans, [{"text": "Phụ lục khung kỷ luật"}])
        self.assertTrue(v["claim_valid"])
        self.assertIn("Đã đối chiếu nguồn cho các khẳng định", v["badges"])

    # T6: Em còn nợ 5 triệu học phí thì sao?
    def test_t6_personal_debt_no_personal_judgment(self):
        intent, risk = classify_academic_intent_and_risk("Em còn nợ 5 triệu học phí thì sao?")
        self.assertEqual(intent, AcademicIntent.PERSONAL_CASE)
        good_ans = (
            "Quy chế của trường quy định sinh viên có trách nhiệm hoàn thành học phí đúng hạn [1]. "
            "Tuy nhiên chatbot không thể tra cứu công nợ cụ thể hay danh sách thi cá nhân của bạn. "
            "Bạn hãy kiểm tra Cổng thông tin đào tạo và liên hệ Phòng Tài chính để hoàn tất công nợ hoặc xin hướng dẫn giải quyết."
        )
        self.assertNotIn("chắc chắn bị cấm thi", good_ans)
        v = evaluate_verification("Nợ 5 triệu?", good_ans, [{"text": "Đóng học phí đúng thời hạn"}])
        self.assertTrue(v["claim_valid"])

    # T7: Đã chuyển khoản nhưng hệ thống chưa cập nhật
    def test_t7_transfer_not_updated_keep_calm(self):
        intent, risk = classify_academic_intent_and_risk("Em đã chuyển khoản nhưng hệ thống chưa cập nhật học phí.")
        self.assertEqual(intent, AcademicIntent.PROCEDURE_GUIDANCE)
        good_ans = (
            "Hệ thống có thể mất từ 1 đến 2 ngày làm việc để đối soát giao dịch ngân hàng [1]. "
            "Bạn hãy lưu lại biên lai hoặc ảnh chụp sao kê chuyển khoản thành công, sau đó liên hệ hoặc mang đến Phòng Kế toán - Tài chính "
            "để được đối soát và cập nhật trạng thái học phí."
        )
        v = evaluate_verification("Chuyển khoản chưa cập nhật", good_ans, [{"text": "Thủ tục đóng học phí"}])
        self.assertTrue(v["claim_valid"])

    # T8: Xin gia hạn học phí
    def test_t8_tuition_extension_guidance(self):
        intent, risk = classify_academic_intent_and_risk("Em có thể xin gia hạn học phí không?")
        self.assertEqual(intent, AcademicIntent.FINANCIAL_DIFFICULTY)
        good_ans = (
            "Nếu gặp khó khăn tài chính đột xuất, bạn có thể làm đơn xin gia hạn nộp học phí có xác nhận lý do chính đáng "
            "để gửi lên Nhà trường xem xét giải quyết theo quy định [1]. Hãy nộp đơn trước thời hạn chốt học phí."
        )
        v = evaluate_verification("Xin gia hạn học phí?", good_ans, [{"text": "Quy định xem xét gia hạn"}])
        self.assertTrue(v["claim_valid"])

    # T9: Gia đình khó khăn có chính sách hỗ trợ không?
    def test_t9_financial_support_policies(self):
        intent, risk = classify_academic_intent_and_risk("Gia đình em khó khăn thì có chính sách hỗ trợ không?")
        self.assertEqual(intent, AcademicIntent.FINANCIAL_DIFFICULTY)
        good_ans = (
            "Nhà trường có các chính sách hỗ trợ tài chính như: phối hợp với các nhà hảo tâm trao học bổng tài trợ "
            "cho sinh viên có hoàn cảnh gia đình khó khăn [1], và triển khai dịch vụ công tác xã hội giúp đỡ sinh viên diện chính sách [2]."
        )
        v = evaluate_verification("Chính sách hỗ trợ khó khăn", good_ans, [
            {"text": "Điều 16: Học bổng tài trợ sinh viên khó khăn"},
            {"text": "Điều 16: Dịch vụ công tác xã hội giúp đỡ sinh viên"}
        ])
        self.assertEqual(v["sufficiency"], "SUFFICIENT")
        self.assertTrue(v["claim_valid"])

    # T10: Không đủ điểm rèn luyện có ảnh hưởng học bổng không?
    def test_t10_drl_affects_scholarship(self):
        intent, risk = classify_academic_intent_and_risk("Không đủ điểm rèn luyện có ảnh hưởng học bổng không?")
        self.assertEqual(intent, AcademicIntent.ACADEMIC_CONSEQUENCE)
        good_ans = (
            "Điểm rèn luyện có ảnh hưởng đến việc xét khen thưởng và học bổng theo quy chế sinh viên [1]. "
            "Tuy nhiên, tài liệu quy chế hiện có chưa quy định chi tiết mức điểm rèn luyện tối thiểu cho từng loại học bổng."
        )
        v = evaluate_verification("Điểm rèn luyện ảnh hưởng học bổng?", good_ans, [{"text": "Điều 5: Xét nhận học bổng"}])
        self.assertEqual(v["sufficiency"], "PARTIAL")

    # T11: Bị cấm thi thì phải làm gì?
    def test_t11_banned_from_exam_procedure(self):
        intent, risk = classify_academic_intent_and_risk("Em bị cấm thi thì phải làm gì?")
        self.assertEqual(intent, AcademicIntent.PROCEDURE_GUIDANCE)
        good_ans = (
            "Nếu bị cấm thi một học phần, bạn phải đăng ký học lại học phần đó ở học kỳ tiếp theo có mở lớp "
            "theo quy chế đào tạo của Nhà trường [1]. Hãy theo dõi lịch mở lớp trên Cổng đào tạo để đăng ký kịp thời."
        )
        self.assertNotIn("chắc chắn bị đuổi", good_ans)
        v = evaluate_verification("Bị cấm thi phải làm gì?", good_ans, [{"text": "Điều 14: Đăng ký học lại"}])
        self.assertEqual(v["sufficiency"], "SUFFICIENT")

    # T12: Tốt nghiệp khi còn công nợ
    def test_t12_graduation_with_debt(self):
        intent, risk = classify_academic_intent_and_risk("Em có được tốt nghiệp nếu còn công nợ không?")
        self.assertEqual(intent, AcademicIntent.ACADEMIC_CONSEQUENCE)
        good_ans = (
            "Sinh viên đủ điều kiện công nhận tốt nghiệp sẽ được cấp bằng và giải quyết các thủ tục hành chính liên quan [1]. "
            "Tuy nhiên, để nhận bằng tốt nghiệp chính thức, bạn cần hoàn thành đầy đủ nghĩa vụ học phí và công nợ với Nhà trường. "
            "Bạn nên kiểm tra tình trạng công nợ trên Cổng thông tin đào tạo trước đợt xét tốt nghiệp."
        )
        v = evaluate_verification("Tốt nghiệp còn công nợ?", good_ans, [{"text": "Điều 5: Cấp bằng tốt nghiệp"}])
        self.assertTrue(v["claim_valid"])


if __name__ == "__main__":
    unittest.main()
