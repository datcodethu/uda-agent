"""Test các phần KHÔNG cần mạng/API. Chạy:  python -m unittest discover -s tests -v"""
import unittest
from pathlib import Path

from app.core.textutils import extract_text, slugify
from app.pipeline.generator.verifier import unsupported_numbers
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.pdf_loader import load_text
from app.pipeline.preprocessor.structural_chunker import (
    chunk_document, Chunk, extract_doc_title, check_article_order
)
from app.pipeline.query_transformation.abbreviation_mapper import expand_abbreviations, load_map
from app.pipeline.retrieval.fusion import rrf_fuse

SAMPLE = Path(__file__).resolve().parents[1] / "data" / "raw_documents" / "quy_che_mau_demo.txt"


class TestExtractText(unittest.TestCase):
    def test_blocks_with_signature(self):
        content = [{"type": "text", "text": "Xin chào", "extras": {"signature": "AAAA" * 100}}]
        self.assertEqual(extract_text(content), "Xin chào")

    def test_plain_string(self):
        self.assertEqual(extract_text("abc"), "abc")

    def test_none(self):
        self.assertEqual(extract_text(None), "")


class TestChunker(unittest.TestCase):
    def setUp(self):
        self.chunks = chunk_document(clean_text(SAMPLE.read_text(encoding="utf-8")), "Quy chế mẫu")

    def test_one_chunk_per_dieu(self):
        dieus = [c.dieu for c in self.chunks if c.dieu]
        self.assertEqual(dieus, [f"Điều {i}" for i in range(1, 8)])

    def test_chuong_and_title_carried(self):
        c3 = next(c for c in self.chunks if c.dieu == "Điều 3")
        self.assertTrue(c3.chuong.startswith("Chương II"))
        self.assertIn("HỌC PHÍ VÀ HỌC BỔNG", c3.chuong)
        self.assertEqual(c3.dieu_title, "Học phí")

    def test_header_in_text_and_content_kept(self):
        c2 = next(c for c in self.chunks if c.dieu == "Điều 2")
        self.assertTrue(c2.text.startswith("[Quy chế mẫu | Chương I"))
        self.assertIn("tối đa 25 tín chỉ", c2.text)

    def test_unique_ids(self):
        ids = [c.chunk_id for c in self.chunks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_long_article_is_split_with_header_each_part(self):
        body = "\n".join(f"{i}. " + ("nội dung rất dài " * 20) for i in range(1, 12))
        text = f"Điều 1. Quy định dài\n{body}"
        chunks = chunk_document(text, "Doc", max_chars=600, overlap=80)
        self.assertGreater(len(chunks), 2)
        for c in chunks:
            self.assertIn("Điều 1. Quy định dài", c.text.split("\n")[0])
            self.assertLessEqual(len(c.text), 800)

    def test_reference_inside_sentence_is_not_a_new_article(self):
        text = "Điều 1. A\nnội dung\nĐiều 5 của quy chế này quy định khác.\nĐiều 2. B\nnội dung b"
        dieus = [c.dieu for c in chunk_document(text, "D")]
        self.assertEqual(dieus, ["Điều 1", "Điều 2"])

    def test_dieu_regex_variants(self):
        text = (
            "Điều 1 - Học phí\nnội dung 1\n"
            "Điều 2 – Học bổng\nnội dung 2\n"
            "Điều 3 Khen thưởng\nnội dung 3\n"
            "ĐIỀU 4. KỶ LUẬT\nnội dung 4"
        )
        chunks = chunk_document(text, "DocVariants")
        dieus = [c.dieu for c in chunks]
        titles = [c.dieu_title for c in chunks]
        self.assertEqual(dieus, ["Điều 1", "Điều 2", "Điều 3", "Điều 4"])
        self.assertEqual(titles, ["Học phí", "Học bổng", "Khen thưởng", "KỶ LUẬT"])

    def test_default_status_is_active_uppercase(self):
        for c in self.chunks:
            self.assertEqual(c.status, "ACTIVE")

    def test_article_without_title_keeps_body_sentence(self):
        mock_text = (
            "Điều 1. Ban hành văn bản giả định này cho toàn bộ đơn vị áp dụng thử nghiệm.\n"
            "nghiệm thu kết quả trong năm học mới.\n"
            "Điều 2. Quyết định có hiệu lực thi hành kể từ ngày ký thông qua.\n"
            "Điều 3. Quy định thực tế\n"
            "1. Nội dung khoản 1."
        )
        chunks = chunk_document(mock_text, "MockDoc")
        c1 = next(c for c in chunks if c.dieu == "Điều 1")
        self.assertEqual(c1.dieu_title, "")
        self.assertIn("Ban hành văn bản giả định này cho toàn bộ đơn vị áp dụng thử nghiệm.", c1.text)
        c2 = next(c for c in chunks if c.dieu == "Điều 2")
        self.assertEqual(c2.dieu_title, "")
        self.assertIn("Quyết định có hiệu lực thi hành kể từ ngày ký thông qua.", c2.text)
        c3 = next(c for c in chunks if c.dieu == "Điều 3")
        self.assertEqual(c3.dieu_title, "Quy định thực tế")

    def test_decision_and_regulation_sections_no_x1_suffix(self):
        mock_text = (
            "QUYẾT ĐỊNH\n"
            "Về việc ban hành văn bản mẫu\n"
            "Điều 1. Ban hành quy định kèm theo văn bản này.\n"
            "Điều 2. Quyết định có hiệu lực từ ngày ký.\n"
            "QUY ĐỊNH BAN HÀNH KÈM THEO QUYẾT ĐỊNH\n"
            "Điều 1. Phạm vi áp dụng\n"
            "Nội dung quy định 1.\n"
            "Điều 2. Trách nhiệm thi hành\n"
            "Nội dung quy định 2."
        )
        chunks = chunk_document(mock_text, "Văn bản mẫu")
        dieus = [c for c in chunks if c.dieu]
        self.assertEqual(len(dieus), 4)
        for c in chunks:
            self.assertNotIn("-x", c.chunk_id)
        c_qd = [c for c in dieus if c.phan_van_ban == "quyet_dinh"]
        c_qdkt = [c for c in dieus if c.phan_van_ban == "quy_dinh_kem_theo"]
        self.assertEqual(len(c_qd), 2)
        self.assertEqual(len(c_qdkt), 2)
        self.assertTrue(c_qd[0].chunk_id.startswith("van-ban-mau-qd-d1-"))
        self.assertTrue(c_qdkt[0].chunk_id.startswith("van-ban-mau-qdkt-d1-"))

    def test_table_preserved_and_header_repeated_when_split(self):
        mock_table = [
            "| Mã HP | Tên học phần giả định | Số TC |",
            "|---|---|---|",
        ]
        for i in range(1, 15):
            mock_table.append(f"| HP{i} | Học phần mô phỏng số {i} | {i} |")
        text = "Điều 1. Khung chương trình\n" + "\n".join(mock_table)
        chunks = chunk_document(text, "DocTable", max_chars=350, overlap=50)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertIn("| Mã HP | Tên học phần giả định | Số TC |", c.text)

    def test_sentence_boundary_clean_overlap(self):
        sents = [f"Đây là câu văn hoàn chỉnh thứ {i} phục vụ kiểm thử." for i in range(1, 10)]
        text = "Điều 1. Quy định câu văn\n" + " ".join(sents)
        chunks = chunk_document(text, "DocSentence", max_chars=250, overlap=80)
        self.assertGreater(len(chunks), 1)
        for c in chunks[1:]:
            body_lines = c.text.split("\n")[1:]
            first_line = body_lines[0] if body_lines else ""
            self.assertTrue(first_line.startswith("Đây là câu văn"))

    def test_extract_doc_title(self):
        mock_decision = (
            "QUYẾT ĐỊNH\n"
            "Về việc ban hành Quy định mẫu kiểm thử sinh viên\n"
            "HIỆU TRƯỞNG\n"
            "Căn cứ..."
        )
        title = extract_doc_title(mock_decision, fallback="fallback_name")
        self.assertEqual(title, "Quy định mẫu kiểm thử sinh viên")

    def test_check_article_order_warnings(self):
        # 1. Hợp lệ có hậu tố chữ: Điều 1, Điều 2, Điều 2a, Điều 3 -> 0 cảnh báo
        valid_chunks = [
            Chunk(chunk_id="c1", doc_name="D", chuong="", dieu="Điều 1", dieu_title="", text="", part=1),
            Chunk(chunk_id="c2", doc_name="D", chuong="", dieu="Điều 2", dieu_title="", text="", part=1),
            Chunk(chunk_id="c3", doc_name="D", chuong="", dieu="Điều 2a", dieu_title="", text="", part=1),
            Chunk(chunk_id="c4", doc_name="D", chuong="", dieu="Điều 3", dieu_title="", text="", part=1),
        ]
        self.assertEqual(check_article_order(valid_chunks, "test_doc"), [])

        # 2. Nhảy số: Điều 1 sang Điều 3 -> cảnh báo NHẢY SỐ
        skipped_chunks = [
            Chunk(chunk_id="c1", doc_name="D", chuong="", dieu="Điều 1", dieu_title="", text="", part=1),
            Chunk(chunk_id="c2", doc_name="D", chuong="", dieu="Điều 3", dieu_title="", text="", part=1),
        ]
        w_skip = check_article_order(skipped_chunks, "test_doc")
        self.assertEqual(len(w_skip), 1)
        self.assertIn("NHẢY SỐ", w_skip[0])

        # 3. Trùng số: Điều 2 rồi lại Điều 2 -> cảnh báo TRÙNG SỐ
        dup_chunks = [
            Chunk(chunk_id="c1", doc_name="D", chuong="", dieu="Điều 2", dieu_title="", text="", part=1),
            Chunk(chunk_id="c2", doc_name="D", chuong="", dieu="Điều 2", dieu_title="", text="", part=1),
        ]
        w_dup = check_article_order(dup_chunks, "test_doc")
        self.assertEqual(len(w_dup), 1)
        self.assertIn("TRÙNG SỐ", w_dup[0])

        # 4. Giảm số: Điều 5 xuống Điều 3 -> cảnh báo GIẢM SỐ
        dec_chunks = [
            Chunk(chunk_id="c1", doc_name="D", chuong="", dieu="Điều 5", dieu_title="", text="", part=1),
            Chunk(chunk_id="c2", doc_name="D", chuong="", dieu="Điều 3", dieu_title="", text="", part=1),
        ]
        w_dec = check_article_order(dec_chunks, "test_doc")
        self.assertEqual(len(w_dec), 1)
        self.assertIn("GIẢM SỐ", w_dec[0])


class TestCleaner(unittest.TestCase):
    def test_nfc_normalization(self):
        decomposed = "Ho\u0323c phi\u0301"          # dạng tổ hợp (NFD)
        self.assertEqual(clean_text(decomposed), "Học phí")

    def test_remove_page_numbers_and_repeated_header(self):
        lines = []
        for p in range(5):
            lines += ["TRƯỜNG ĐẠI HỌC MẪU", f"Nội dung trang {p}", f"{p + 1}"]
        out = clean_text("\n".join(lines))
        self.assertNotIn("TRƯỜNG ĐẠI HỌC MẪU", out)
        self.assertIn("Nội dung trang 3", out)

    def test_keep_dieu_lines_even_if_repeated(self):
        out = clean_text("\n".join(["Điều 1. A"] * 5))
        self.assertEqual(out.count("Điều 1. A"), 5)


class TestAbbreviation(unittest.TestCase):
    def test_expand_appends_not_replaces(self):
        r = expand_abbreviations("đk hb và gpa", load_map())
        self.assertTrue(r.startswith("đk hb và gpa"))
        self.assertIn("học bổng", r)
        self.assertIn("điểm trung bình tích lũy", r)

    def test_no_abbrev_unchanged(self):
        self.assertEqual(expand_abbreviations("xin chào", {}), "xin chào")


class TestFusion(unittest.TestCase):
    def test_rrf_prefers_items_in_both_lists(self):
        fused = rrf_fuse([["a", "b", "c"], ["c", "a", "d"]])
        order = [x for x, _ in fused]
        self.assertEqual(order[0], "a")
        self.assertIn("d", order)


class TestVerifier(unittest.TestCase):
    CTX = ["Tối đa 25 tín chỉ. Học phí 1.500.000 đồng. Điểm từ 3,2 trở lên."]

    def test_all_supported(self):
        self.assertEqual(unsupported_numbers("Tối đa 25 tín chỉ [1], điểm 3,2 [1].", self.CTX), [])

    def test_detects_wrong_number(self):
        self.assertEqual(unsupported_numbers("Tối đa 30 tín chỉ [1].", self.CTX), ["30"])

    def test_thousand_separators_normalized(self):
        self.assertEqual(unsupported_numbers("Học phí 1.500.000 đồng.", self.CTX), [])

    def test_citation_markers_ignored(self):
        self.assertEqual(unsupported_numbers("Xem [7].", self.CTX), [])


class TestSlug(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slugify("Quy chế Đào tạo 2025"), "quy-che-dao-tao-2025")


class TestPdfLoader(unittest.TestCase):
    def test_load_text_from_txt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "sample_mock.txt"
            p.write_text("Dòng giả lập 1: Quy định chung.\nDòng giả lập 2: Nội dung thử nghiệm.", encoding="utf-8")
            res = load_text(p)
            self.assertIn("Dòng giả lập 1", res)
            self.assertIn("Dòng giả lập 2", res)


class TestIngestApproved(unittest.TestCase):
    """Kiểm tra cổng nạp theo bảng đăng ký docs_registry.csv (Phiên 3A)."""
    def setUp(self):
        import tempfile
        self._temp_dir = tempfile.TemporaryDirectory()
        self.raw_dir = Path(self._temp_dir.name) / "raw_documents"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.csv_path = Path(self._temp_dir.name) / "docs_registry.csv"

        # 1. File hợp lệ trên đĩa
        (self.raw_dir / "valid_doc.txt").write_text(
            "Điều 1. Quy chế đào tạo mẫu.\nNội dung chi tiết quy chế đào tạo.",
            encoding="utf-8"
        )
        # 2. File trên đĩa nhưng không đăng ký trong CSV
        (self.raw_dir / "unregistered_doc.txt").write_text("Tài liệu không đăng ký", encoding="utf-8")
        # 3. File da_duyet = false
        (self.raw_dir / "unapproved_doc.txt").write_text("Chưa duyệt", encoding="utf-8")
        # 4. File loai = phap_luat
        (self.raw_dir / "phap_luat_doc.txt").write_text("Luật nhà nước", encoding="utf-8")
        # 5. File status = EXPIRED
        (self.raw_dir / "expired_doc.txt").write_text("Hết hiệu lực", encoding="utf-8")

        # Viết bảng đăng ký giả lập có BOM (utf-8-sig)
        csv_content = (
            "doc_id,doc_title,doc_number,effective_date,status,loai,da_duyet,file,applies_to\n"
            "QC01,Quy chế đào tạo chính quy,123/QĐ-ĐHĐA,2025-01-01,ACTIVE,quy_che_truong,true,valid_doc.txt,ALL\n"
            "QC02,Văn bản chưa duyệt,,2025-01-01,ACTIVE,quy_che_truong,false,unapproved_doc.txt,ALL\n"
            "PL01,Luật an ninh mạng,24/2018/QH14,2019-01-01,ACTIVE,phap_luat,true,phap_luat_doc.txt,ALL\n"
            "QC03,Quy chế cũ hết hạn,50/QĐ-ĐHĐA,2020-01-01,EXPIRED,quy_che_truong,true,expired_doc.txt,ALL\n"
            "QC04,File ảo không có trên đĩa,99/QĐ,2025-01-01,ACTIVE,quy_che_truong,true,missing_file.txt,ALL\n"
        )
        self.csv_path.write_text(csv_content, encoding="utf-8-sig")

    def tearDown(self):
        self._temp_dir.cleanup()

    def test_filter_valid_approved_file_selected(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        approved, blocked = filter_approved_files(rows, self.raw_dir)
        approved_files = [x["file"] for x in approved]
        self.assertIn("valid_doc.txt", approved_files)
        self.assertEqual(len(approved), 1)

        # Kiểm tra metadata đi kèm
        item = approved[0]
        self.assertEqual(item["doc_id"], "QC01")
        self.assertEqual(item["doc_title"], "Quy chế đào tạo chính quy")
        self.assertEqual(item["doc_number"], "123/QĐ-ĐHĐA")
        self.assertEqual(item["effective_date"], "2025-01-01")
        self.assertEqual(item["category"], "quy_che_truong")
        self.assertEqual(item["applies_to"], "ALL")

    def test_filter_unregistered_file_blocked(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        _, blocked = filter_approved_files(rows, self.raw_dir)
        blocked_map = {x["file"]: x["reason"] for x in blocked}
        self.assertIn("unregistered_doc.txt", blocked_map)
        self.assertIn("không có trong bảng đăng ký", blocked_map["unregistered_doc.txt"])

    def test_filter_da_duyet_false_blocked(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        _, blocked = filter_approved_files(rows, self.raw_dir)
        blocked_map = {x["file"]: x["reason"] for x in blocked}
        self.assertIn("unapproved_doc.txt", blocked_map)
        self.assertIn("da_duyet != true", blocked_map["unapproved_doc.txt"])

    def test_filter_loai_phap_luat_blocked(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        _, blocked = filter_approved_files(rows, self.raw_dir)
        blocked_map = {x["file"]: x["reason"] for x in blocked}
        self.assertIn("phap_luat_doc.txt", blocked_map)
        self.assertIn("loai != quy_che_truong", blocked_map["phap_luat_doc.txt"])

    def test_filter_status_expired_blocked(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        _, blocked = filter_approved_files(rows, self.raw_dir)
        blocked_map = {x["file"]: x["reason"] for x in blocked}
        self.assertIn("expired_doc.txt", blocked_map)
        self.assertIn("status != ACTIVE", blocked_map["expired_doc.txt"])

    def test_filter_missing_file_on_disk_blocked(self):
        from scripts.ingest_approved import parse_registry, filter_approved_files
        rows = parse_registry(self.csv_path)
        _, blocked = filter_approved_files(rows, self.raw_dir)
        blocked_map = {x["file"]: x["reason"] for x in blocked}
        self.assertIn("missing_file.txt", blocked_map)
        self.assertIn("không tồn tại", blocked_map["missing_file.txt"])

    def test_dry_run_execution_no_db_write(self):
        from scripts.ingest_approved import run_ingest
        res = run_ingest(self.csv_path, self.raw_dir, apply=False)
        self.assertEqual(res["approved"], 1)
        self.assertGreaterEqual(res["blocked"], 5)
        self.assertGreater(res["total_chunks"], 0)
        self.assertGreater(res["total_chars"], 0)
        self.assertEqual(res["mode"], "dry-run")

    def test_rag_pipeline_sources_with_metadata(self):
        from app.pipeline.rag_pipeline import _sources
        sample_chunks = [
            {
                "chunk_id": "qd-d1-1",
                "doc_name": "quy_che_dao_tao",
                "chuong": "Chương I",
                "dieu": "Điều 1",
                "dense_score": 0.85,
                "text": "Sinh viên phải đăng ký học phần đúng hạn.",
                "effective_date": "2025-02-01",
                "doc_number": "123/QĐ-ĐHĐA",
            },
            {
                "chunk_id": "qd-d2-1",
                "doc_name": "quy_che_dao_tao",
                "chuong": "Chương I",
                "dieu": "Điều 2",
                "dense_score": 0.75,
                "text": "Thời gian đào tạo tối đa.",
            }
        ]
        sources = _sources(sample_chunks)
        self.assertEqual(len(sources), 2)
        self.assertEqual(sources[0]["effective_date"], "2025-02-01")
        self.assertEqual(sources[0]["doc_number"], "123/QĐ-ĐHĐA")
        self.assertNotIn("effective_date", sources[1])
        self.assertNotIn("doc_number", sources[1])

    def test_ingest_folder_prints_warning_and_exits(self):
        import io
        import contextlib
        from scripts.ingest_folder import main as ingest_folder_main

        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            ingest_folder_main(str(self.raw_dir))
        out = f.getvalue()
        self.assertIn("CẢNH BÁO", out)
        self.assertIn("ingest_approved.py", out)


if __name__ == "__main__":
    unittest.main()
