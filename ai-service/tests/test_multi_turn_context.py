"""Bộ kiểm thử tự động cho Multi-turn Conversation & Contextual RAG (Nhiệm vụ 6).

Đạt chuẩn:
- 100% Offline, sử dụng mock LLM (0 gọi API trả phí).
- Phủ đủ 7 kịch bản bắt buộc theo yêu cầu nhiệm vụ.
"""
import unittest
from unittest.mock import patch, MagicMock

from app.pipeline import rag_pipeline
from app.pipeline.memory.session_memory import session_memory, SessionData
from app.pipeline.query_transformation.context_resolver import resolve_context


class TestMultiTurnContextRAG(unittest.TestCase):
    def setUp(self):
        # Làm sạch bộ nhớ session trước mỗi test
        session_memory.clear_all()

    def tearDown(self):
        session_memory.clear_all()

    def test_1_follow_up_clarification_la_sao(self):
        """Test 1: User hỏi chuẩn ngoại ngữ -> hỏi 'là sao?' -> giải thích đúng ngữ cảnh B1, không từ chối."""
        cid = "conv_test_1"
        chunks_turn_1 = [
            {
                "chunk_id": "2023-8-23-16-29-59n-qd-d1-1",
                "doc_name": "2023_8_23_16_29_59n",
                "chuong": "",
                "dieu": "Điều 1",
                "text": "Chuẩn đầu ra ngoại ngữ bậc Đại học áp dụng Bậc 3/6 Khung ngoại ngữ Việt Nam hoặc B1 CEFR.",
                "status": "ACTIVE",
                "dense_score": 0.88,
            }
        ]
        # Giả lập lượt 1 đã lưu vào memory
        session_memory.save_turn(
            conversation_id=cid,
            question="Chuẩn đầu ra ngoại ngữ ngành không chuyên ngữ là gì?",
            answer="Chuẩn đầu ra ngoại ngữ áp dụng Bậc 3/6 hoặc B1 CEFR [1].",
            chunks=chunks_turn_1,
            sources=[{"chunk_id": chunks_turn_1[0]["chunk_id"], "doc_name": "2023_8_23_16_29_59n"}],
            topic="Chuẩn đầu ra ngoại ngữ ngành không chuyên ngữ là gì?",
        )

        with patch("app.pipeline.rag_pipeline.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.generate.return_value = (
                "B1 (Bậc 3/6) nghĩa là bạn cần có khả năng giao tiếp ngoại ngữ ở mức trung cấp [1]."
            )
            mock_get_llm.return_value = mock_llm

            # Lượt 2: User hỏi 'là sao?'
            res = rag_pipeline.answer(
                question="là sao?",
                conversation_id=cid,
                mode="hybrid",
            )

            self.assertFalse(res["refused"], "Không được từ chối khi hỏi 'là sao?' có ngữ cảnh")
            self.assertEqual(len(res["sources"]), 1)
            self.assertEqual(res["sources"][0]["doc_name"], "2023_8_23_16_29_59n")
            self.assertIn("B1", res["answer"])
            self.assertEqual(res["retrieval_ms"], 0, "Phải tái sử dụng cache, 0 ms retrieval")

    def test_2_example_request(self):
        """Test 2: User: 'B1 là gì?' -> 'cho ví dụ' -> Đưa ví dụ phù hợp B1."""
        cid = "conv_test_2"
        chunks_b1 = [
            {
                "chunk_id": "2023-8-23-16-29-59n-qd-d6-1",
                "doc_name": "2023_8_23_16_29_59n",
                "chuong": "",
                "dieu": "Điều 6",
                "text": "Chứng chỉ tương đương B1 gồm TOEIC 450, IELTS 4.5, TOEFL iBT 42 hoặc VSTEP Bậc 3.",
                "status": "ACTIVE",
                "dense_score": 0.85,
            }
        ]
        session_memory.save_turn(
            conversation_id=cid,
            question="B1 là gì?",
            answer="B1 là trình độ ngoại ngữ bậc 3 theo khung năng lực 6 bậc [1].",
            chunks=chunks_b1,
            sources=[{"chunk_id": chunks_b1[0]["chunk_id"], "doc_name": "2023_8_23_16_29_59n"}],
            topic="B1 là gì?",
        )

        with patch("app.pipeline.rag_pipeline.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_llm.generate.return_value = "Ví dụ bạn có thể thi lấy chứng chỉ TOEIC 450 điểm hoặc IELTS 4.5 [1]."
            mock_get_llm.return_value = mock_llm

            res = rag_pipeline.answer(
                question="cho ví dụ",
                conversation_id=cid,
                mode="hybrid",
            )

            self.assertFalse(res["refused"])
            self.assertEqual(len(res["sources"]), 1)
            self.assertIn("TOEIC", res["answer"])

    def test_3_continuation_partial_tuition(self):
        """Test 3: 'Em nợ học phí thì có được thi không?' -> 'vậy nếu đóng một phần thì sao?' -> Standalone query."""
        cid = "conv_test_3"
        session_memory.save_turn(
            conversation_id=cid,
            question="Em nợ học phí thì có được thi không?",
            answer="Sinh viên phải hoàn thành nghĩa vụ học phí trước khi dự thi.",
            chunks=[{"chunk_id": "c1", "doc_name": "2021_8_5_8_33_34A", "text": "Học phí", "status": "ACTIVE"}],
            topic="Em nợ học phí thì có được thi không?",
        )

        with patch("app.pipeline.rag_pipeline.retrieve") as mock_retrieve:
            mock_retrieve.return_value = {
                "chunks": [{"chunk_id": "c1", "doc_name": "2021_8_5_8_33_34A", "text": "Học phí", "status": "ACTIVE", "dense_score": 0.85}],
                "best_dense_score": 0.85,
                "expanded_query": "Em nợ học phí nếu đóng một phần thì có được dự thi không?",
                "timing": {"retrieval_ms": 10},
            }
            prep = rag_pipeline.prepare(
                question="vậy nếu đóng một phần thì sao?",
                conversation_id=cid,
                mode="hybrid",
            )

        standalone = prep.extra.get("expanded_query", "")
        self.assertIn("học phí", standalone.lower())
        self.assertIn("đóng một phần", standalone.lower())
        self.assertEqual(prep.extra.get("context_action"), "REWRITE_AND_RETRIEVE")

    def test_4_topic_switching(self):
        """Test 4: User hỏi ngoại ngữ -> chuyển sang hỏi học bổng -> Nhận diện NEW_TOPIC."""
        cid = "conv_test_4"
        session_memory.save_turn(
            conversation_id=cid,
            question="Chuẩn đầu ra ngoại ngữ ngành không chuyên ngữ là gì?",
            answer="Chuẩn ngoại ngữ là Bậc 3/6.",
            chunks=[{"chunk_id": "c_nn", "doc_name": "2023_8_23_16_29_59n", "text": "Ngoại ngữ", "status": "ACTIVE"}],
            topic="Chuẩn đầu ra ngoại ngữ ngành không chuyên ngữ là gì?",
        )

        with patch("app.pipeline.rag_pipeline.retrieve") as mock_retrieve:
            mock_retrieve.return_value = {
                "chunks": [{"chunk_id": "c_hb", "doc_name": "2021_8_5_8_33_34A", "text": "Học bổng", "status": "ACTIVE", "dense_score": 0.88}],
                "best_dense_score": 0.88,
                "expanded_query": "Điều kiện để được xét học bổng là gì?",
                "timing": {"retrieval_ms": 10},
            }
            prep = rag_pipeline.prepare(
                question="Điều kiện để được xét học bổng là gì?",
                conversation_id=cid,
                mode="hybrid",
            )

        self.assertEqual(prep.extra.get("context_action"), "NEW_TOPIC")
        # Không được mang từ khóa ngoại ngữ vào expanded_query
        self.assertNotIn("ngoại ngữ", prep.extra.get("expanded_query", "").lower())

    def test_5_isolation_between_conversation_ids(self):
        """Test 5: Hai conversation_id khác nhau -> Không rò rỉ lịch sử hay tài liệu."""
        cid_a = "conv_user_A"
        cid_b = "conv_user_B"

        session_memory.save_turn(
            conversation_id=cid_a,
            question="Mất thẻ xe ở trường thì làm thế nào?",
            answer="Báo bảo vệ và xuất trình giấy tờ xe.",
            chunks=[{"chunk_id": "cx", "doc_name": "Bao_cao_nghien_cuu_Mat_the_xe_sinh_vien", "status": "ACTIVE", "text": "Thẻ xe"}],
            topic="Mất thẻ xe",
        )

        # conv_b chưa có lịch sử, hỏi 'là sao?' -> Phải kích hoạt CLARIFY_NO_CONTEXT
        prep_b = rag_pipeline.prepare(
            question="là sao?",
            conversation_id=cid_b,
        )

        self.assertTrue(prep_b.refused)
        self.assertEqual(prep_b.refuse_reason, "clarify_no_context")
        self.assertEqual(len(prep_b.sources), 0, "conv_B không được rò rỉ sources của conv_A")

    def test_6_revoked_or_inactive_source_not_reused(self):
        """Test 6: Tài liệu ở lượt trước chuyển sang trạng thái không hợp lệ -> Không tái sử dụng."""
        cid = "conv_test_6"
        expired_chunks = [
            {
                "chunk_id": "old_c1",
                "doc_name": "tai_lieu_da_bi_go",
                "text": "Nội dung cũ",
                "status": "EXPIRED",
            }
        ]
        session_memory.save_turn(
            conversation_id=cid,
            question="Quy định cũ là gì?",
            answer="Quy định cũ trả lời.",
            chunks=expired_chunks,
            topic="Quy định cũ",
        )

        # Giả lập validate_cached_sources phát hiện tài liệu không hợp lệ
        with patch.object(session_memory, "validate_cached_sources", return_value=(False, [])):
            with patch("app.pipeline.rag_pipeline.retrieve") as mock_retrieve:
                mock_retrieve.return_value = {
                    "chunks": [],
                    "best_dense_score": None,
                    "expanded_query": "Quy định cũ là gì?",
                    "timing": {"retrieval_ms": 10},
                }
                prep = rag_pipeline.prepare(
                    question="là sao?",
                    conversation_id=cid,
                    mode="hybrid",
                )

            # Vì nguồn bị thu hồi, hệ thống KHÔNG tái sử dụng cache cũ
            self.assertFalse(prep.extra.get("reused_cache", False))
            self.assertNotIn("old_c1", [c["chunk_id"] for c in prep.chunks])

    def test_7_clarify_without_history(self):
        """Test 7: User: 'là sao?' khi lịch sử rỗng -> Hỏi người dùng muốn giải thích quy định nào."""
        # Không có history, không có conversation_id
        res = rag_pipeline.answer(
            question="là sao?",
            history=[],
            conversation_id=None,
        )

        self.assertTrue(res["refused"])
        self.assertEqual(res["refuse_reason"], "clarify_no_context")
        self.assertIn("giải thích hoặc làm rõ", res["answer"])
        self.assertEqual(len(res["sources"]), 0)


if __name__ == "__main__":
    unittest.main()
