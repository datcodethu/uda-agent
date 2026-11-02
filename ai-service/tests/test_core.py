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

    def test_expanded_seed_abbreviations(self):
        """Kiểm tra các từ viết tắt mới bổ sung từ khảo sát sinh viên ĐH Đông Á."""
        m = load_map()
        r1 = expand_abbreviations("sinh viên cntt học môn csdl và tham gia ctxh", m)
        self.assertIn("công nghệ thông tin", r1)
        self.assertIn("cơ sở dữ liệu", r1)
        self.assertIn("công tác xã hội", r1)

        r2 = expand_abbreviations("sv hỏi về bgh và qldt hay ctsv", m)
        self.assertIn("sinh viên", r2)
        self.assertIn("ban giám hiệu", r2)
        self.assertIn("quản lý đào tạo", r2)
        self.assertIn("công tác sinh viên", r2)

    def test_unaccented_abbreviations_support(self):
        """Kiểm tra hỗ trợ từ viết tắt không dấu thông dụng (drl, dkhp, cdr, ctdt)."""
        m = load_map()
        r = expand_abbreviations("drl và dkhp cùng cdr ctdt", m)
        self.assertIn("điểm rèn luyện", r)
        self.assertIn("đăng ký học phần", r)
        self.assertIn("chuẩn đầu ra", r)
        self.assertIn("chương trình đào tạo", r)

    def test_seed_abbreviations_each_word(self):
        """Kiểm tra mở rộng chính xác từng từ trong abbreviations_seed.json và các từ bị loại bỏ."""
        import json
        from app.core.config import BASE_DIR
        seed_path = BASE_DIR / "data" / "seed" / "abbreviations_seed.json"
        with seed_path.open("r", encoding="utf-8") as f:
            seed_data = json.load(f)

        m = load_map()
        # 1. Kiểm tra 22 từ trong seed đều có trong map
        self.assertEqual(len(seed_data), 23)
        for k, v in seed_data.items():
            self.assertIn(k, m, f"Từ {k} phải có trong mapping")
            self.assertEqual(m[k], v)

        # 2. Kiểm tra từ hp mở rộng thành 'học phí; học phần'
        self.assertEqual(m["hp"], "học phí; học phần")
        r_hp = expand_abbreviations("nộp tiền hp kỳ 1", m)
        self.assertIn("học phí; học phần", r_hp)

        # 3. Kiểm tra các từ đa nghĩa đã loại bỏ (it, tc, tn) không bị mở rộng
        r_removed = expand_abbreviations("sinh viên it học tc tn", m)
        words = r_removed.split(" ")
        self.assertEqual(words[2], "it")
        self.assertEqual(words[4], "tc")
        self.assertEqual(words[5], "tn")


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

        # Viết bảng đăng ký giả lập có BOM (utf-8-sig) đủ 5 cột bắt buộc
        csv_content = (
            "doc_id,doc_title,doc_number,effective_date,status,loai,da_duyet,file,applies_to,public_or_internal\n"
            "QC01,Quy chế đào tạo chính quy,123/QĐ-ĐHĐA,2025-01-01,ACTIVE,quy_che_truong,true,valid_doc.txt,ALL,public\n"
            "QC02,Văn bản chưa duyệt,,2025-01-01,ACTIVE,quy_che_truong,false,unapproved_doc.txt,ALL,public\n"
            "PL01,Luật an ninh mạng,24/2018/QH14,2019-01-01,ACTIVE,phap_luat,true,phap_luat_doc.txt,ALL,public\n"
            "QC03,Quy chế cũ hết hạn,50/QĐ-ĐHĐA,2020-01-01,EXPIRED,quy_che_truong,true,expired_doc.txt,ALL,public\n"
            "QC04,File ảo không có trên đĩa,99/QĐ,2025-01-01,ACTIVE,quy_che_truong,true,missing_file.txt,ALL,public\n"
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
        self.assertEqual(item["public_or_internal"], "public")

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

    def test_filter_path_traversal_blocked(self):
        """(4) Cột file chỉ là tên file: chặn nếu chứa /, \\ hoặc .."""
        from scripts.ingest_approved import filter_approved_files
        malicious_rows = [
            {"file": "../secret.txt", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "public"},
            {"file": "..\\secret.txt", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "public"},
            {"file": "sub/secret.txt", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "public"},
        ]
        approved, blocked = filter_approved_files(malicious_rows, self.raw_dir)
        self.assertEqual(len(approved), 0)
        self.assertGreaterEqual(len(blocked), 3)
        for b in blocked:
            if b["file"] in ["../secret.txt", "..\\secret.txt", "sub/secret.txt"]:
                self.assertIn("không hợp lệ", b["reason"])

    def test_filter_duplicate_file_rows_blocked(self):
        """(4) File xuất hiện ở hai dòng thì chặn cả hai dòng."""
        from scripts.ingest_approved import filter_approved_files
        dup_rows = [
            {"file": "valid_doc.txt", "doc_id": "D1", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "public"},
            {"file": "valid_doc.txt", "doc_id": "D2", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "public"},
        ]
        approved, blocked = filter_approved_files(dup_rows, self.raw_dir)
        self.assertEqual(len(approved), 0)
        blocked_valid = [b for b in blocked if b["file"] == "valid_doc.txt"]
        self.assertEqual(len(blocked_valid), 2)
        for b in blocked_valid:
            self.assertIn("dòng trùng lặp", b["reason"])

    def test_filter_public_or_internal_gating(self):
        """(2) public_or_internal = public; dòng internal bị chặn trừ khi có cờ --allow-internal."""
        from scripts.ingest_approved import filter_approved_files
        rows = [
            {"file": "valid_doc.txt", "da_duyet": "true", "loai": "quy_che_truong", "status": "ACTIVE", "public_or_internal": "internal"}
        ]
        # Mặc định (allow_internal=False): bị chặn
        approved, blocked = filter_approved_files(rows, self.raw_dir, allow_internal=False)
        self.assertEqual(len(approved), 0)
        self.assertIn("allow-internal", blocked[0]["reason"])

        # Khi bật allow_internal=True: được duyệt
        approved, blocked = filter_approved_files(rows, self.raw_dir, allow_internal=True)
        self.assertEqual(len(approved), 1)

    def test_missing_required_column_raises_value_error(self):
        """(3) Thiếu một trong các cột file, da_duyet, loai, status, public_or_internal thì dừng và báo lỗi rõ."""
        from scripts.ingest_approved import parse_registry
        bad_csv = self.raw_dir / "bad.csv"
        # Thiếu cột public_or_internal
        bad_csv.write_text("file,da_duyet,loai,status\nvalid_doc.txt,true,quy_che_truong,ACTIVE\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            parse_registry(bad_csv)
        self.assertIn("public_or_internal", str(ctx.exception))

    def test_file_read_error_recorded_in_blocked(self):
        """(5) Lỗi đọc một file không làm dừng cả lượt, ghi vào danh sách bị chặn kèm lý do."""
        from scripts.ingest_approved import run_ingest
        # Tạo một file hỏng giả lập không đọc được
        broken_file = self.raw_dir / "broken.txt"
        broken_file.write_text("dummy", encoding="utf-8")
        bad_csv = self.raw_dir / "with_broken.csv"
        bad_csv.write_text(
            "file,da_duyet,loai,status,public_or_internal\n"
            "broken.txt,true,quy_che_truong,ACTIVE,public\n"
            "valid_doc.txt,true,quy_che_truong,ACTIVE,public\n",
            encoding="utf-8"
        )
        from unittest.mock import patch
        orig_load = __import__("app.pipeline.preprocessor.pdf_loader", fromlist=["load_text"]).load_text

        def mock_load(p):
            if "broken.txt" in str(p):
                raise IOError("Không thể giải mã file hỏng")
            return orig_load(p)

        with patch("scripts.ingest_approved.load_text", side_effect=mock_load):
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                res = run_ingest(bad_csv, self.raw_dir, apply=False)
            self.assertEqual(res["approved"], 1)  # valid_doc.txt vẫn được duyệt
            self.assertGreaterEqual(res["blocked"], 1)  # broken.txt bị chuyển sang blocked

    def test_index_document_metadata_whitelist_and_protection(self):
        """(1) Chỉ cho phép các khóa metadata whitelist ghi vào đoạn; không ghi đè chunk_id, text, doc_name, status."""
        from app.pipeline.index_service import index_document
        from unittest.mock import patch

        meta = {
            "doc_id": "TEST_DOC_1",
            "doc_title": "Tiêu đề kiểm thử",
            "doc_number": "999/QĐ",
            "effective_date": "2026-01-01",
            "category": "quy_che_truong",
            "applies_to": "ALL",
            # Các khóa không được phép ghi đè hoặc ngoài whitelist
            "chunk_id": "malicious_chunk_id",
            "text": "malicious_text",
            "doc_name": "malicious_doc_name",
            "status": "EXPIRED",
            "hack_field": "hacked_value",
        }

        with patch("app.pipeline.retrieval.chunk_store.replace_document") as mock_replace, \
             patch("app.pipeline.retrieval.dense_search.delete_document"), \
             patch("app.pipeline.retrieval.dense_search.upsert_chunks"), \
             patch("app.pipeline.retrieval.bm25_search.bm25_index.rebuild"):
            index_document(
                doc_name="test_whitelist",
                text="Điều 1. Nội dung kiểm thử whitelist.",
                status="ACTIVE",
                meta=meta,
            )
            saved_chunks = mock_replace.call_args[0][1]
            self.assertGreater(len(saved_chunks), 0)
            c = saved_chunks[0]
            # Metadata hợp lệ được gắn
            self.assertEqual(c["doc_id"], "TEST_DOC_1")
            self.assertEqual(c["doc_number"], "999/QĐ")
            self.assertEqual(c["effective_date"], "2026-01-01")
            # Trường cốt lõi KHÔNG bị ghi đè
            self.assertNotEqual(c["chunk_id"], "malicious_chunk_id")
            self.assertNotEqual(c["text"], "malicious_text")
            self.assertEqual(c["doc_name"], "test_whitelist")
            self.assertEqual(c["status"], "ACTIVE")
            # Trường ngoài whitelist KHÔNG được lưu vào chunk
            self.assertNotIn("hack_field", c)

    def test_dry_run_execution_no_db_write(self):
        from scripts.ingest_approved import run_ingest
        import io
        import contextlib
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
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


class TestStructureDiagnosis(unittest.TestCase):
    """Kiểm thử thuần cho công cụ chẩn đoán cấu trúc văn bản (Phiên 4B)."""

    def test_analyze_chunks_distribution_detects_anomaly(self):
        from scripts.chan_doan_cau_truc import analyze_chunks_distribution

        # Dữ liệu mô phỏng giả lập: 10 chunks, trong đó nhóm 'Điều 3' chiếm 7 chunks (70% > 50%)
        mock_chunks = [
            {"chunk_id": "doc-d1-1", "doc_name": "mock_doc", "phan_van_ban": "quyet_dinh", "dieu": "Điều 1", "text": "Nội dung 1"},
            {"chunk_id": "doc-d2-1", "doc_name": "mock_doc", "phan_van_ban": "quyet_dinh", "dieu": "Điều 2", "text": "Nội dung 2"},
            {"chunk_id": "doc-d0-1", "doc_name": "mock_doc", "phan_van_ban": "quyet_dinh", "dieu": "(không)", "text": "Nội dung mở đầu"},
        ]
        # Thêm 7 chunk Điều 3
        for i in range(1, 8):
            mock_chunks.append({
                "chunk_id": f"doc-d3-{i}",
                "doc_name": "mock_doc",
                "phan_van_ban": "quyet_dinh",
                "dieu": "Điều 3",
                "text": f"Nội dung điều 3 phần {i} rất dài...",
            })

        res = analyze_chunks_distribution(mock_chunks, target_doc="mock_doc")
        self.assertEqual(res["total_chunks"], 10)
        self.assertEqual(len(res["anomalies"]), 1)
        anomaly = res["anomalies"][0]
        self.assertEqual(anomaly["dieu"], "Điều 3")
        self.assertEqual(anomaly["count"], 7)
        self.assertEqual(anomaly["pct_chunks"], 70.0)
        self.assertTrue(anomaly["is_anomaly"])

    def test_classify_heading_lines_detects_patterns(self):
        from scripts.chan_doan_cau_truc import classify_heading_lines

        # Văn bản giả lập tự viết mô phỏng các kiểu tiêu đề đề mục
        mock_text = """
TÀI LIỆU HƯỚNG DẪN MÔ PHỎNG

Phần I. TỔNG QUAN
Điều 1. Phạm vi áp dụng
Mục 2. Phương pháp tiếp cận

I. MỤC TIÊU CỐT LÕI
II. ĐẶC ĐIỂM CHÍNH

1. Khái niệm chung
1.1. Chuẩn bị trước giờ học
2.3.1. Phương pháp tự học nâng cao

A. Yêu cầu đối với học viên
a) Đọc kỹ đề cương môn học
b) Làm bài tập trước khi đến lớp

HƯỚNG DẪN THỰC HÀNH CHI TIẾT

Đây là một đoạn văn bản thân bài thông thường không phải là tiêu đề và có độ dài trung bình.
Đoạn văn này tiếp tục diễn giải chi tiết các quy định mà không có ký tự đánh số ở đầu câu.
"""
        res = classify_heading_lines(mock_text)

        # Kiểm tra nhận diện đủ 5 nhóm
        self.assertGreaterEqual(len(res["CHUONG_DIEU_MUC_PHAN"]), 3)  # Phần I, Điều 1, Mục 2
        self.assertGreaterEqual(len(res["SO_LA_MA"]), 2)              # I., II.
        self.assertGreaterEqual(len(res["SO_THAP_PHAN"]), 3)          # 1., 1.1., 2.3.1.
        self.assertGreaterEqual(len(res["CHU_CAI"]), 3)               # A., a), b)
        self.assertGreaterEqual(len(res["CHU_HOA_TOAN_BO"]), 2)       # TÀI LIỆU HƯỚNG DẪN MÔ PHỎNG, HƯỚNG DẪN THỰC HÀNH CHI TIẾT

        # Kiểm tra các dòng thông thường không bị nhận nhầm vào tiêu đề
        all_lines = [item["prefix_80"] for cat in res.values() for item in cat]
        self.assertFalse(any("Đây là một đoạn văn bản thân bài" in line for line in all_lines))


class TestIngestPruneAndAnomaly(unittest.TestCase):
    """Kiểm thử cơ chế cảnh báo bất thường cắt đoạn, kiểm tra trùng mã và prune tài liệu (Phiên 4C)."""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_detection_blocks_file(self):
        """Cảnh báo bất thường chặn văn bản giả lập có một nhãn chiếm > 50% số đoạn (khi >= 10 đoạn)."""
        from scripts.ingest_approved import check_chunking_anomaly

        # Giả lập 12 đoạn, trong đó Điều 3 chiếm 8 đoạn (8/12 = 66.7% > 50%)
        mock_chunks = [
            {"phan_van_ban": "quyet_dinh", "dieu": "Điều 1"},
            {"phan_van_ban": "quyet_dinh", "dieu": "Điều 2"},
            {"phan_van_ban": "quyet_dinh", "dieu": "(không)"},
            {"phan_van_ban": "quyet_dinh", "dieu": "Điều 4"},
        ]
        for _ in range(8):
            mock_chunks.append({"phan_van_ban": "quyet_dinh", "dieu": "Điều 3"})

        is_anomaly, msg, detail = check_chunking_anomaly(mock_chunks)
        self.assertTrue(is_anomaly)
        self.assertIn("NGHI NGỜ CẮT SAI", msg)
        self.assertIsNotNone(detail)
        self.assertEqual(detail["dieu"], "Điều 3")
        self.assertAlmostEqual(detail["ratio"], 8 / 12, places=2)

    def test_normal_distribution_not_blocked(self):
        """Văn bản bình thường phân bố đều không bị đánh dấu bất thường."""
        from scripts.ingest_approved import check_chunking_anomaly

        # Giả lập 10 đoạn chia đều cho 5 Điều (mỗi Điều 20% <= 50%)
        mock_chunks = []
        for d in range(1, 6):
            mock_chunks.append({"phan_van_ban": "quy_dinh_kem_theo", "dieu": f"Điều {d}"})
            mock_chunks.append({"phan_van_ban": "quy_dinh_kem_theo", "dieu": f"Điều {d}"})

        is_anomaly, msg, detail = check_chunking_anomaly(mock_chunks)
        self.assertFalse(is_anomaly)
        self.assertEqual(msg, "")
        self.assertIsNone(detail)

    def test_allow_anomaly_bypasses_block(self):
        """Cờ --allow-anomaly cho phép văn bản có dấu hiệu bất thường vượt qua vòng chặn."""
        from scripts.ingest_approved import run_ingest
        from unittest.mock import patch
        import io
        import contextlib

        raw_dir = self.test_dir / "raw"
        raw_dir.mkdir()
        doc_path = raw_dir / "mock_skewed.txt"
        doc_path.write_text("Điều 1. Mở đầu\nĐiều 3. Dài...\n", encoding="utf-8")

        csv_path = self.test_dir / "registry.csv"
        csv_path.write_text(
            "file,da_duyet,loai,status,public_or_internal\n"
            "mock_skewed.txt,true,quy_che_truong,ACTIVE,public\n",
            encoding="utf-8"
        )

        from app.pipeline.preprocessor.structural_chunker import Chunk

        # Mock chunk_document trả về 12 chunks lệch
        skewed_chunks = [
            Chunk(chunk_id="d1-1", doc_name="mock_skewed", chuong="", dieu="Điều 1", dieu_title="", text="t1", phan_van_ban="quyet_dinh"),
            Chunk(chunk_id="d2-1", doc_name="mock_skewed", chuong="", dieu="Điều 2", dieu_title="", text="t2", phan_van_ban="quyet_dinh"),
        ]
        for i in range(10):
            skewed_chunks.append(
                Chunk(chunk_id=f"d3-{i}", doc_name="mock_skewed", chuong="", dieu="Điều 3", dieu_title="", text=f"t3_{i}", phan_van_ban="quyet_dinh")
            )

        with patch("scripts.ingest_approved.chunk_document", return_value=skewed_chunks):
            # 1. Chạy mặc định không có allow_anomaly: BỊ CHẶN
            f1 = io.StringIO()
            with contextlib.redirect_stdout(f1):
                res1 = run_ingest(csv_path, raw_dir, apply=False, allow_anomaly=False)
            self.assertEqual(res1["approved"], 0)
            self.assertEqual(res1["blocked"], 1)

            # 2. Chạy với allow_anomaly=True: ĐƯỢC PHÉP QUA
            f2 = io.StringIO()
            with contextlib.redirect_stdout(f2):
                res2 = run_ingest(csv_path, raw_dir, apply=False, allow_anomaly=True)
            self.assertEqual(res2["approved"], 1)
            self.assertEqual(res2["blocked"], 0)

    def test_duplicate_chunk_id_detected(self):
        """Kiểm tra phát hiện trùng lặp chunk_id trên toàn kho."""
        from scripts.ingest_approved import check_duplicate_chunk_ids

        # Dữ liệu giả lập có 2 chunk trùng chunk_id 'qc-d1-1'
        mock_chunks = [
            {"chunk_id": "qc-d1-1", "doc_name": "doc1"},
            {"chunk_id": "qc-d1-2", "doc_name": "doc1"},
            {"chunk_id": "qc-d1-1", "doc_name": "doc2"},  # TRÙNG
            {"chunk_id": "qc-d2-1", "doc_name": "doc1"},
        ]
        num_dups, dup_dict = check_duplicate_chunk_ids(mock_chunks)
        self.assertEqual(num_dups, 1)
        self.assertIn("qc-d1-1", dup_dict)
        self.assertEqual(dup_dict["qc-d1-1"], 2)

        # Dữ liệu không trùng
        unique_chunks = [
            {"chunk_id": "c1", "doc_name": "doc1"},
            {"chunk_id": "c2", "doc_name": "doc1"},
        ]
        num_zero, _ = check_duplicate_chunk_ids(unique_chunks)
        self.assertEqual(num_zero, 0)

    def test_prune_dry_run_leaves_store_unchanged(self):
        """Chế độ dry-run liệt kê đúng tài liệu sẽ bị gỡ mà không làm thay đổi kho chunks.jsonl."""
        import json
        import io
        import contextlib
        from unittest.mock import patch
        from scripts.ingest_approved import prune_unapproved_documents

        chunks_file = self.test_dir / "chunks.jsonl"
        init_chunks = [
            {"chunk_id": "k1", "doc_name": "doc_approved", "text": "text1", "status": "ACTIVE"},
            {"chunk_id": "k2", "doc_name": "doc_approved", "text": "text2", "status": "ACTIVE"},
            {"chunk_id": "r1", "doc_name": "doc_unapproved", "text": "text3", "status": "ACTIVE"},
        ]
        chunks_file.write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in init_chunks) + "\n",
            encoding="utf-8"
        )

        with patch("app.pipeline.retrieval.chunk_store._path", return_value=chunks_file):
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                pruned = prune_unapproved_documents(
                    approved_doc_names={"doc_approved"},
                    registry_rows=[],
                    blocked_list=[],
                    apply=False,
                )
            self.assertEqual(len(pruned), 1)
            self.assertEqual(pruned[0]["doc_name"], "doc_unapproved")
            self.assertEqual(pruned[0]["chunks"], 1)

            # Đảm bảo kho trên đĩa vẫn còn nguyên 3 chunks (chưa bị gỡ)
            lines_after = [l for l in chunks_file.read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertEqual(len(lines_after), 3)

    def test_prune_apply_removes_unapproved_doc(self):
        """Chế độ apply gỡ đúng tài liệu không còn duyệt và giữ nguyên tài liệu còn duyệt."""
        import json
        import io
        import contextlib
        from unittest.mock import patch
        from scripts.ingest_approved import prune_unapproved_documents

        chunks_file = self.test_dir / "chunks.jsonl"
        init_chunks = [
            {"chunk_id": "k1", "doc_name": "doc_approved", "text": "text1", "status": "ACTIVE"},
            {"chunk_id": "k2", "doc_name": "doc_approved", "text": "text2", "status": "ACTIVE"},
            {"chunk_id": "r1", "doc_name": "doc_unapproved", "text": "text3", "status": "ACTIVE"},
        ]
        chunks_file.write_text(
            "\n".join(json.dumps(c, ensure_ascii=False) for c in init_chunks) + "\n",
            encoding="utf-8"
        )

        with patch("app.pipeline.retrieval.chunk_store._path", return_value=chunks_file), \
             patch("app.pipeline.retrieval.dense_search.delete_document") as mock_dense_del, \
             patch("app.pipeline.retrieval.bm25_search.bm25_index.rebuild") as mock_bm25_reb:
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                pruned = prune_unapproved_documents(
                    approved_doc_names={"doc_approved"},
                    registry_rows=[],
                    blocked_list=[],
                    apply=True,
                )
            self.assertEqual(len(pruned), 1)
            self.assertEqual(pruned[0]["doc_name"], "doc_unapproved")
            mock_dense_del.assert_called_with("doc_unapproved")
            mock_bm25_reb.assert_called()

            # Đảm bảo kho trên đĩa chỉ còn 2 chunks của doc_approved
            lines_after = [json.loads(l) for l in chunks_file.read_text(encoding="utf-8").splitlines() if l.strip()]
            self.assertEqual(len(lines_after), 2)
            self.assertTrue(all(c["doc_name"] == "doc_approved" for c in lines_after))

    def test_loai_huong_dan_blocked_with_specific_reason(self):
        """Giá trị loai=huong_dan hợp lệ trong bảng nhưng bị cổng nạp chặn với lý do cụ thể."""
        from scripts.ingest_approved import filter_approved_files

        raw_dir = self.test_dir / "raw"
        raw_dir.mkdir()
        (raw_dir / "hd.pdf").write_text("dummy", encoding="utf-8")

        rows = [
            {"file": "hd.pdf", "da_duyet": "true", "loai": "huong_dan", "status": "ACTIVE", "public_or_internal": "public"}
        ]
        approved, blocked = filter_approved_files(rows, raw_dir)
        self.assertEqual(len(approved), 0)
        self.assertEqual(len(blocked), 1)
        self.assertIn("loai != quy_che_truong", blocked[0]["reason"])
        self.assertIn("huong_dan", blocked[0]["reason"])


class TestBenchmarkEvaluation(unittest.TestCase):
    """Kiểm thử bộ công cụ đánh giá benchmark cau_hoi_thu (Phiên 3C)."""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_retrieve_same_chunks_and_scores_with_dense_search_with_vector(self):
        """Chứng minh retrieve() cho cùng chunk_id và điểm số trước và sau khi tách dense_search_with_vector."""
        from unittest.mock import patch, MagicMock
        from app.pipeline.retrieval import hybrid_retriever, dense_search

        fake_vector = [0.1, 0.2, 0.3]
        fake_points = [
            MagicMock(payload={"chunk_id": "c1", "doc_name": "d1", "dieu": "Điều 1", "text": "t1"}, score=0.88),
            MagicMock(payload={"chunk_id": "c2", "doc_name": "d1", "dieu": "Điều 2", "text": "t2"}, score=0.77),
        ]

        with patch("app.pipeline.retrieval.dense_search.embed_query", return_value=fake_vector), \
             patch("app.pipeline.retrieval.dense_search.ensure_collection"), \
             patch("app.pipeline.retrieval.dense_search.get_client") as mock_client, \
             patch("app.pipeline.retrieval.bm25_search.bm25_index.search", return_value=[]):

            mock_client.return_value.query_points.return_value = MagicMock(points=fake_points)

            # 1. Gọi trực tiếp dense_search truyền thống
            res_dense = dense_search.dense_search("câu hỏi", top_k=2)

            # 2. Gọi qua retrieve() (đã dùng dense_search_with_vector bên trong)
            res_retrieve = hybrid_retriever.retrieve("câu hỏi", mode="dense", top_k=2)

            self.assertEqual(len(res_dense), len(res_retrieve["chunks"]))
            for d_item, r_item in zip(res_dense, res_retrieve["chunks"]):
                self.assertEqual(d_item["chunk_id"], r_item["chunk_id"])
                self.assertAlmostEqual(d_item["dense_score"], r_item["rank_score"], places=4)
            # Kiểm tra trường timing được ghi nhận
            self.assertIn("timing", res_retrieve)
            self.assertIn("embedding_ms", res_retrieve["timing"])
            self.assertIn("qdrant_ms", res_retrieve["timing"])

    def test_parse_cau_hoi_thu_csv_and_skip_empty(self):
        """Đọc CSV câu hỏi kiểm thử, lọc theo tập và đếm đúng số dòng bị bỏ qua do rỗng."""
        from scripts.chay_cau_hoi_thu import parse_cau_hoi_thu_csv

        csv_content = (
            "id,nhom,cau_hoi,expected_dieu,must_have,expected_refuse,tap,ghi_chu\n"
            "q1,chuan_dau_ra,Hỏi câu 1,Điều 1,B1|N4,false,dev,ghi chu 1\n"
            "q2,ngoai_pham_vi,Hỏi câu 2,,,true,dev,\n"
            "q3,chuan_dau_ra,Hỏi câu 3,Điều 2,TOEIC,false,test,khác tập\n"
            "q4,chuan_dau_ra,,Điều 1,,false,dev,câu hỏi rỗng 1\n"
            "q5,chuan_dau_ra,   ,Điều 2,,false,dev,câu hỏi rỗng 2\n"
        )
        csv_file = self.test_dir / "test_questions.csv"
        csv_file.write_text(csv_content, encoding="utf-8-sig")

        # 1. Lọc theo tap="dev"
        dev_questions, skipped_empty = parse_cau_hoi_thu_csv(csv_file, tap="dev")
        self.assertEqual(len(dev_questions), 2)
        self.assertEqual(skipped_empty, 2)
        self.assertEqual(dev_questions[0]["id"], "q1")
        self.assertEqual(dev_questions[1]["id"], "q2")

        # 2. Lọc theo tap="all"
        all_questions, skipped_empty_all = parse_cau_hoi_thu_csv(csv_file, tap="all")
        self.assertEqual(len(all_questions), 3)
        self.assertEqual(skipped_empty_all, 2)

    def test_must_have_matching_nfc_and_case_insensitive(self):
        """So khớp cụm must_have theo Unicode NFC và không phân biệt chữ hoa/thường."""
        from scripts.chay_cau_hoi_thu import evaluate_single_question
        from unittest.mock import patch, MagicMock

        # Giả lập 2 chunk chứa "chuẩn B1" và "toeic 450"
        mock_chunks = [
            {"chunk_id": "c1", "dieu": "Điều 1", "dense_score": 0.8, "text": "Sinh viên phải đạt chuẩn b1 ngoại ngữ."},
            {"chunk_id": "c2", "dieu": "Điều 2", "dense_score": 0.7, "text": "Hoặc tương đương TOEIC 450 điểm."},
        ]
        mock_prepared = MagicMock(
            chunks=mock_chunks,
            sources=mock_chunks,
            refused=False,
            refuse_reason="",
            timing={"retrieval_ms": 100}
        )

        q = {
            "id": "q1",
            "nhom": "chuan_dau_ra",
            "cau_hoi": "Chuẩn đầu ra là gì?",
            "expected_dieu": "Điều 1|Điều 2",
            "must_have": "Chuẩn B1|TOEIC 450|Tiếng Nhật N4",
            "expected_refuse": "false",
            "tap": "dev",
        }

        with patch("app.pipeline.rag_pipeline.prepare", return_value=mock_prepared):
            res = evaluate_single_question(q, mode="hybrid", retrieval_only=True)
            self.assertFalse(res["error"])
            mh_eval = res["must_have_eval"]
            self.assertEqual(len(mh_eval), 3)
            # "Chuẩn B1" có trong c1 -> True
            self.assertTrue(mh_eval[0]["in_retrieval"])
            # "TOEIC 450" có trong c2 -> True
            self.assertTrue(mh_eval[1]["in_retrieval"])
            # "Tiếng Nhật N4" không có -> False
            self.assertFalse(mh_eval[2]["in_retrieval"])
            # Hit Điều 1/Điều 2 -> True
            self.assertTrue(res["hit_expected_dieu"])
            # expected_refuse=false, bot_refused=false -> false_refusal=False
            self.assertFalse(res["false_refusal"])

    def test_expected_dieu_hit_and_miss(self):
        """Kiểm tra phát hiện hit Điều khi có chunk phù hợp và miss khi không có."""
        from scripts.chay_cau_hoi_thu import evaluate_single_question
        from unittest.mock import patch, MagicMock

        mock_chunks = [{"chunk_id": "c1", "dieu": "Điều 5", "dense_score": 0.8, "text": "Phúc khảo điểm"}]
        mock_prepared = MagicMock(chunks=mock_chunks, sources=mock_chunks, refused=False, refuse_reason="", timing={})

        with patch("app.pipeline.rag_pipeline.prepare", return_value=mock_prepared):
            # Hit Điều 5
            q_hit = {"id": "q1", "nhom": "thi", "cau_hoi": "Hỏi", "expected_dieu": "Điều 4|Điều 5", "expected_refuse": "false"}
            res_hit = evaluate_single_question(q_hit, mode="hybrid", retrieval_only=True)
            self.assertTrue(res_hit["hit_expected_dieu"])

            # Miss Điều 1
            q_miss = {"id": "q2", "nhom": "thi", "cau_hoi": "Hỏi", "expected_dieu": "Điều 1", "expected_refuse": "false"}
            res_miss = evaluate_single_question(q_miss, mode="hybrid", retrieval_only=True)
            self.assertFalse(res_miss["hit_expected_dieu"])

    def test_compute_benchmark_summary_denominators_and_rates(self):
        """Kiểm tra mẫu số và các tỷ lệ tính toán: loại trừ câu lỗi API, tính đúng mẫu số của must_have, Điều, từ chối."""
        from scripts.chay_cau_hoi_thu import compute_benchmark_summary

        mock_results = [
            # Câu 1: nhom 'chuan', có 2 cụm must_have (1 trúng, 1 trượt), expected_dieu trúng, expected_refuse=False, bot không từ chối
            {
                "id": "q1", "nhom": "chuan", "cau_hoi": "c1", "error": False,
                "must_have_eval": [{"phrase": "p1", "in_retrieval": True, "in_answer": False}, {"phrase": "p2", "in_retrieval": False, "in_answer": False}],
                "hit_expected_dieu": True, "expected_refuse": False, "true_refusal": False, "false_refusal": False,
                "timing": {"total_ms": 100, "embedding_ms": 20, "qdrant_ms": 30, "bm25_ms": 10, "llm_ms": 0}
            },
            # Câu 2: nhom 'ngoai', không có must_have, không có expected_dieu, expected_refuse=True, bot từ chối đúng
            {
                "id": "q2", "nhom": "ngoai", "cau_hoi": "c2", "error": False,
                "must_have_eval": [],
                "hit_expected_dieu": None, "expected_refuse": True, "true_refusal": True, "false_refusal": False,
                "timing": {"total_ms": 80, "embedding_ms": 20, "qdrant_ms": 30, "bm25_ms": 10, "llm_ms": 0}
            },
            # Câu 3: nhom 'chuan', có 1 cụm must_have trúng, expected_dieu trượt, expected_refuse=False, bot từ chối nhầm
            {
                "id": "q3", "nhom": "chuan", "cau_hoi": "c3", "error": False,
                "must_have_eval": [{"phrase": "p3", "in_retrieval": True, "in_answer": False}],
                "hit_expected_dieu": False, "expected_refuse": False, "true_refusal": False, "false_refusal": True,
                "timing": {"total_ms": 90, "embedding_ms": 20, "qdrant_ms": 30, "bm25_ms": 10, "llm_ms": 0}
            },
            # Câu 4: Bị lỗi API -> Phải bị loại khỏi toàn bộ mẫu số
            {
                "id": "q4", "nhom": "chuan", "cau_hoi": "c4", "error": True, "loi_api": "429 Resource exhausted",
                "must_have_eval": [], "hit_expected_dieu": False, "expected_refuse": False,
                "true_refusal": False, "false_refusal": False, "timing": {}
            }
        ]

        summary = compute_benchmark_summary(mock_results, retrieval_only=True)

        self.assertEqual(summary["total_evaluated"], 3)
        self.assertEqual(summary["total_api_errors"], 1)

        ov = summary["overall"]
        # must_have: Tổng 3 cụm (q1 có 2, q3 có 1), có 2 trúng -> 2/3 = 66.7%
        self.assertEqual(ov["must_have_retrieval"]["denom"], 3)
        self.assertEqual(ov["must_have_retrieval"]["num"], 2)
        self.assertAlmostEqual(ov["must_have_retrieval"]["rate"], 2 / 3, places=2)

        # hit Điều: q1 (hit=True), q3 (hit=False) -> mẫu số 2, trúng 1 -> 1/2 = 50%
        self.assertEqual(ov["hit_expected_dieu"]["denom"], 2)
        self.assertEqual(ov["hit_expected_dieu"]["num"], 1)
        self.assertEqual(ov["hit_expected_dieu"]["rate"], 0.5)

        # Từ chối đúng: chỉ q2 (expected_refuse=True) -> mẫu số 1, trúng 1 -> 1/1 = 100%
        self.assertEqual(ov["true_refuse"]["denom"], 1)
        self.assertEqual(ov["true_refuse"]["num"], 1)
        self.assertEqual(ov["true_refuse"]["rate"], 1.0)

        # Từ chối nhầm: q1, q3 (expected_refuse=False) -> mẫu số 2, có q3 từ chối nhầm -> 1/2 = 50%
        self.assertEqual(ov["false_refuse"]["denom"], 2)
        self.assertEqual(ov["false_refuse"]["num"], 1)
        self.assertEqual(ov["false_refuse"]["rate"], 0.5)

    def test_export_benchmark_json_has_cham_tay_and_config(self):
        """File JSON xuất ra có đầy đủ cấu hình và cột trống cham_tay cho mỗi câu hỏi."""
        from scripts.chay_cau_hoi_thu import export_benchmark_json
        import json

        mock_results = [
            {"id": "q1", "nhom": "chuan", "cau_hoi": "c1", "cham_tay": "", "error": False}
        ]
        mock_summary = {"overall": {"count": 1}}

        out_file = export_benchmark_json(
            results=mock_results,
            summary=mock_summary,
            mode="hybrid",
            tap="dev",
            retrieval_only=True,
            actual_api_calls=1,
            output_dir=self.test_dir
        )
        self.assertTrue(out_file.exists())

        data = json.loads(out_file.read_text(encoding="utf-8"))
        self.assertIn("config", data)
        self.assertEqual(data["config"]["mode"], "hybrid")
        self.assertEqual(data["config"]["tap"], "dev")
        self.assertTrue(data["config"]["retrieval_only"])
        self.assertIn("cham_tay", data["results"][0])
        self.assertEqual(data["results"][0]["cham_tay"], "")

    def test_csv_param_and_missing_file_error(self):
        """Kiểm tra tham số --csv và báo lỗi rõ ràng kèm đường dẫn khi file không tồn tại."""
        from scripts.chay_cau_hoi_thu import default_csv_path, parse_cau_hoi_thu_csv
        from pathlib import Path

        # 1. default_csv_path trỏ về cau_hoi_thu.csv
        p_def = default_csv_path()
        self.assertEqual(p_def.name, "cau_hoi_thu.csv")

        # 2. File không tồn tại -> raise FileNotFoundError kèm đường dẫn đã thử
        fake_path = self.test_dir / "file_chua_he_co_12345.csv"
        with self.assertRaises(FileNotFoundError) as ctx:
            parse_cau_hoi_thu_csv(fake_path, tap="dev")
        self.assertIn(str(fake_path.resolve()), str(ctx.exception))

    def test_retrieval_only_refusal_metrics_are_na_in_json(self):
        """Ở chế độ retrieval-only, mọi chỉ số và cờ từ chối trong file JSON phải là N/A, không phải 0 hay false."""
        from scripts.chay_cau_hoi_thu import export_benchmark_json, format_rate
        import json

        mock_results = [
            {"id": "q1", "nhom": "ngoai", "cau_hoi": "c1", "cham_tay": "", "error": False, "bot_refused": False, "true_refusal": False, "false_refusal": False}
        ]
        mock_summary = {
            "by_group": {
                "ngoai": {
                    "count": 1,
                    "true_refuse": {"num": 0, "denom": 1, "rate": 0.0},
                    "false_refuse": {"num": 0, "denom": 1, "rate": 0.0},
                }
            },
            "overall": {
                "count": 1,
                "true_refuse": {"num": 0, "denom": 1, "rate": 0.0},
                "false_refuse": {"num": 0, "denom": 1, "rate": 0.0},
            }
        }

        out_file = export_benchmark_json(
            results=mock_results,
            summary=mock_summary,
            mode="hybrid",
            tap="dev",
            retrieval_only=True,
            actual_api_calls=1,
            output_dir=self.test_dir,
            timestamp_str="20261014_999999"
        )

        data = json.loads(out_file.read_text(encoding="utf-8"))
        # Trong JSON, các chỉ số từ chối phải là N/A
        ov = data["summary"]["overall"]
        self.assertEqual(ov["true_refuse"]["rate"], "N/A")
        self.assertEqual(ov["false_refuse"]["rate"], "N/A")
        # Kết quả câu hỏi cũng là N/A
        r0 = data["results"][0]
        self.assertEqual(r0["bot_refused"], "N/A")
        self.assertEqual(r0["true_refusal"], "N/A")
        self.assertEqual(r0["false_refusal"], "N/A")

        # format_rate hiển thị N/A
        self.assertEqual(format_rate(ov["true_refuse"]), "N/A")
        self.assertEqual(format_rate(ov["false_refuse"]), "N/A")

    def test_missing_must_have_tracking_and_retrieved_chunk_ids(self):
        """Ghi nhận chính xác các cụm must_have bị thiếu kèm id câu và chunk_id đã truy xuất."""
        from scripts.chay_cau_hoi_thu import evaluate_single_question
        from unittest.mock import patch, MagicMock

        mock_chunks = [
            {"chunk_id": "chunk-01", "dieu": "Điều 1", "dense_score": 0.8, "text": "Sinh viên chuẩn tiếng Anh B1."},
        ]
        mock_prepared = MagicMock(chunks=mock_chunks, sources=mock_chunks, refused=False, refuse_reason="", timing={})

        q = {
            "id": "c99",
            "nhom": "truc_tiep",
            "cau_hoi": "Hỏi chuẩn đầu ra",
            "expected_dieu": "Điều 1",
            "must_have": "tiếng Anh B1|TOEIC 500|HSK 3",
            "expected_refuse": "false",
            "tap": "dev",
        }

        with patch("app.pipeline.rag_pipeline.prepare", return_value=mock_prepared):
            res = evaluate_single_question(q, mode="hybrid", retrieval_only=True)
            self.assertEqual(res["id"], "c99")
            # Cụm thiếu: 'TOEIC 500' và 'HSK 3'
            self.assertEqual(res["missing_must_have"], ["TOEIC 500", "HSK 3"])
            # Chunk IDs đã truy xuất
            self.assertEqual(res["retrieved_chunk_ids"], ["chunk-01"])

    def test_export_cham_tay_csv_name_and_structure(self):
        """Xuất file CSV chấm tay cham_tay_<timestamp>.csv UTF-8 BOM đủ 9 cột để mở bằng Excel."""
        from scripts.chay_cau_hoi_thu import export_benchmark_csv_cham_tay
        import csv

        mock_results = [
            {
                "id": "c01",
                "nhom": "truc_tiep",
                "cau_hoi": "Câu hỏi test 1",
                "answer": "Không dùng khi retrieval_only",
                "retrieved_chunks": [
                    {"chunk_id": "cid-01", "dieu": "Điều 1", "score": 0.8523},
                    {"chunk_id": "cid-02", "dieu": "Điều 2", "score": 0.7654},
                ],
                "bot_refused": False,
                "timing": {"total_ms": 1250},
                "ghi_chu": "ghi chú mẫu"
            }
        ]

        out_csv = export_benchmark_csv_cham_tay(
            results=mock_results,
            output_dir=self.test_dir,
            retrieval_only=True,
            timestamp_str="20261014_112233"
        )
        self.assertTrue(out_csv.exists())
        self.assertEqual(out_csv.name, "cham_tay_20261014_112233.csv")

        # Kiểm tra UTF-8 BOM
        raw_bytes = out_csv.read_bytes()
        self.assertTrue(raw_bytes.startswith(b"\xef\xbb\xbf"))

        # Đọc bằng csv.DictReader utf-8-sig
        with out_csv.open("r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            expected_cols = ["id", "nhom", "cau_hoi", "cau_tra_loi", "nguon", "bot_refused", "tong_ms", "cham_tay", "ghi_chu"]
            self.assertEqual(reader.fieldnames, expected_cols)

            rows = list(reader)
            self.assertEqual(len(rows), 1)
            r = rows[0]
            self.assertEqual(r["id"], "c01")
            self.assertEqual(r["nhom"], "truc_tiep")
            self.assertEqual(r["cau_hoi"], "Câu hỏi test 1")
            self.assertEqual(r["cau_tra_loi"], "")  # retrieval_only để trống
            self.assertIn("cid-01|Điều 1|0.8523", r["nguon"])
            self.assertIn("cid-02|Điều 2|0.7654", r["nguon"])
            self.assertEqual(r["bot_refused"], "N/A")  # retrieval_only đặt N/A
            self.assertEqual(r["tong_ms"], "1250")
            self.assertEqual(r["cham_tay"], "")  # để trống cho người dùng chấm

class TestIntentClassifier(unittest.TestCase):
    """Kiểm thử bộ phân loại ý định IntentClassifier (Phiên 3F - chuẩn hóa)."""

    def test_classify_personal_data_questions(self):
        from app.pipeline.query_transformation.intent_classifier import Intent, classify

        # Các câu tra cứu dữ liệu cá nhân thật (có đại từ ngôi 1 + cụm tra cứu, KHÔNG chứa từ khóa chính sách)
        personal_queries = [
            "Điểm của em kỳ này bao nhiêu ạ?",
            "Em còn nợ bao nhiêu tiền học phí?",
            "cho em xem điểm của em",
            "Xem tra cứu điểm cá nhân",
            "Mã sinh viên IDSV: 123456 tra cứu học phí",
            "Điểm thi của mình kỳ vừa rồi là bao nhiêu?",
        ]
        for q in personal_queries:
            self.assertEqual(classify(q), Intent.PERSONAL, f"Câu này phải là PERSONAL: {q}")

    def test_classify_out_of_scope_pure_greetings(self):
        from app.pipeline.query_transformation.intent_classifier import Intent, classify

        # Chào hỏi thuần túy
        oos_queries = [
            "xin chào bot",
            "hello",
            "Chào bạn!",
            "hi",
            "alo",
            "xin chào",
            "Chào thầy cô ạ",
        ]
        for q in oos_queries:
            self.assertEqual(classify(q), Intent.OUT_OF_SCOPE, f"Câu này phải là OUT_OF_SCOPE: {q}")

    def test_classify_rescued_academic_queries(self):
        from app.pipeline.query_transformation.intent_classifier import Intent, classify

        # 1. Câu hỏi ngắn không bị chặn AMBIGUOUS (đã bỏ luật độ dài)
        short_queries = [
            "",
            "   ",
            "học bổng",
            "học phí",
            "điểm",
            "bảo lưu",
        ]
        for q in short_queries:
            self.assertEqual(classify(q), Intent.ACADEMIC, f"Câu ngắn phải là ACADEMIC: {q}")

        # 2. Câu hỏi chủ đề không bị regex tĩnh chặn (đã bỏ regex quán ăn, xe buýt)
        topic_queries = [
            "Cổng trường có tuyến xe buýt nào đi qua không?",
            "Quán cơm gần trường ở đâu ngon?",
            "Sinh viên có được mang thức ăn từ quán ăn vào phòng tự học không?",
            "Trường có xe buýt đưa đón sinh viên đi thực tập không?",
        ]
        for q in topic_queries:
            self.assertEqual(classify(q), Intent.ACADEMIC, f"Câu hỏi chủ đề phải là ACADEMIC: {q}")

        # 3. Câu hỏi có đại từ ngôi thứ nhất nhưng chứa từ khóa chính sách (chính sách giải cứu)
        policy_queries = [
            "Học phí ngành CNTT khóa 2024 của em là bao nhiêu một tín chỉ?",
            "Lịch học quân sự của khoa em khi nào bắt đầu?",
            "Cho em biết điểm rèn luyện bao nhiêu thì đạt loại xuất sắc?",
            "Cho em biết điểm chuẩn tiếng Anh đầu ra có quy định như thế nào?",
            "Em muốn bảo lưu học phần thì cần đáp ứng điều kiện gì?",
            "Sinh viên năm 2 như em cần hoàn thành bao nhiêu tín chỉ để được xét học bổng?",
        ]
        for q in policy_queries:
            self.assertEqual(classify(q), Intent.ACADEMIC, f"Câu có từ khóa chính sách phải là ACADEMIC: {q}")

    def test_classify_academic_questions(self):
        from app.pipeline.query_transformation.intent_classifier import Intent, classify

        academic_queries = [
            "Chuẩn đầu ra ngoại ngữ của trường là gì?",
            "Em nợ học phí thì có được đăng ký môn không ạ?",
            "Trường hợp nào sinh viên được miễn học phần tiếng Anh?",
            "Quy định về trang phục sinh viên vào các ngày thứ Ba?",
            "Tiêu chuẩn để sinh viên được xét khen thưởng cuối năm?",
        ]
        for q in academic_queries:
            self.assertEqual(classify(q), Intent.ACADEMIC, f"Câu này phải là ACADEMIC: {q}")


class TestRagPipelineFastPath(unittest.TestCase):
    """Kiểm thử đường truyền tắt (Fast-path) trong rag_pipeline khi gặp câu hỏi không phải học vụ."""

    def test_personal_question_fast_path_in_prepare_and_answer(self):
        from app.pipeline.rag_pipeline import prepare, answer
        from app.core.prompts import PERSONAL_REPLY

        q = "Điểm của em kỳ này được bao nhiêu ạ?"
        p = prepare(q)
        self.assertTrue(p.refused)
        self.assertEqual(p.refuse_reason, "personal_data")
        self.assertEqual(len(p.chunks), 0)
        self.assertEqual(len(p.sources), 0)
        self.assertEqual(p.timing["embedding_ms"], 0)
        self.assertEqual(p.timing["qdrant_ms"], 0)

        ans = answer(q)
        self.assertTrue(ans["refused"])
        self.assertEqual(ans["refuse_reason"], "personal_data")
        self.assertEqual(ans["answer"], PERSONAL_REPLY)
        self.assertEqual(len(ans["sources"]), 0)
        self.assertEqual(ans["timing"]["llm_ms"], 0)

    def test_out_of_scope_smalltalk_fast_path(self):
        from app.pipeline.rag_pipeline import answer
        from app.core.prompts import OUT_OF_SCOPE_REPLY

        ans = answer("Xin chào bot!")
        self.assertTrue(ans["refused"])
        self.assertEqual(ans["refuse_reason"], "out_of_scope")
        self.assertEqual(ans["answer"], OUT_OF_SCOPE_REPLY)
        self.assertEqual(len(ans["sources"]), 0)

    def test_rag_pipeline_no_intent_flag(self):
        from unittest.mock import patch
        from app.pipeline.rag_pipeline import prepare

        # Khi tắt bộ phân loại ý định (use_intent=False), câu chào hỏi không bị chặn bởi intent early-return
        with patch("app.pipeline.rag_pipeline.retrieve", return_value={"chunks": [], "best_dense_score": None, "expanded_query": "Xin chào bot!", "timing": {}}):
            p = prepare("Xin chào bot!", use_intent=False)
            self.assertNotEqual(p.refuse_reason, "out_of_scope")


class TestBenchmarkEvaluationDaXacNhan(unittest.TestCase):
    """Kiểm thử logic lọc da_xac_nhan trong công cụ đánh giá benchmark."""

    def test_compute_benchmark_summary_filtering(self):
        from scripts.chay_cau_hoi_thu import compute_benchmark_summary

        mock_results = [
            {
                "id": "c01",
                "nhom": "truc_tiep",
                "cau_hoi": "Câu hỏi đã xác nhận",
                "da_xac_nhan": True,
                "hit_expected_dieu": True,
                "expected_refuse": False,
                "false_refusal": False,
                "true_refusal": False,
                "must_have_eval": [{"phrase": "p1", "in_retrieval": True, "in_answer": False}],
                "timing": {"total_ms": 100},
                "error": False,
            },
            {
                "id": "c02",
                "nhom": "truc_tiep",
                "cau_hoi": "Câu hỏi chưa xác nhận",
                "da_xac_nhan": False,
                "hit_expected_dieu": False,
                "expected_refuse": False,
                "false_refusal": False,
                "true_refusal": False,
                "must_have_eval": [{"phrase": "p2", "in_retrieval": False, "in_answer": False}],
                "timing": {"total_ms": 120},
                "error": False,
            },
        ]

        # 1. Mặc định: gom_ca_chua_xac_nhan = False -> chỉ tính câu đã xác nhận (c01)
        s_default = compute_benchmark_summary(mock_results, retrieval_only=True, gom_ca_chua_xac_nhan=False)
        self.assertEqual(s_default["overall"]["count"], 1)
        self.assertEqual(s_default["overall"]["hit_expected_dieu"]["num"], 1)
        self.assertEqual(s_default["overall"]["hit_expected_dieu"]["denom"], 1)
        self.assertEqual(s_default["overall"]["hit_expected_dieu"]["rate"], 1.0)
        self.assertFalse(s_default["gom_ca_chua_xac_nhan"])

        # 2. Cờ gom_ca_chua_xac_nhan = True -> tính trên cả 2 câu
        s_gom = compute_benchmark_summary(mock_results, retrieval_only=True, gom_ca_chua_xac_nhan=True)
        self.assertEqual(s_gom["overall"]["count"], 2)
        self.assertEqual(s_gom["overall"]["hit_expected_dieu"]["num"], 1)
        self.assertEqual(s_gom["overall"]["hit_expected_dieu"]["denom"], 2)
        self.assertEqual(s_gom["overall"]["hit_expected_dieu"]["rate"], 0.5)
        self.assertTrue(s_gom["gom_ca_chua_xac_nhan"])


class TestDoPhanLoaiScript(unittest.TestCase):
    """Kiểm thử script scripts/do_phan_loai.py trên dữ liệu CSV giả lập nội bộ."""

    def test_analyze_classification_on_mock_csv(self):
        import csv
        import tempfile
        from pathlib import Path
        from scripts.do_phan_loai import analyze_classification

        with tempfile.TemporaryDirectory() as tmpdir:
            csv_file = Path(tmpdir) / "mock_questions.csv"
            with csv_file.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["id", "noi_dung_cau_hoi"])
                writer.writerow(["1", "Xin chào bot"])
                writer.writerow(["2", "Học phí ngành CNTT khóa 2024 của em là bao nhiêu?"])
                writer.writerow(["3", "Điểm của em kỳ này được bao nhiêu ạ?"])
                writer.writerow(["4", "Bảo lưu học phần"])
                writer.writerow(["5", "   "])

            stats = analyze_classification(csv_file, col_name="noi_dung_cau_hoi")
            self.assertEqual(stats["total_valid"], 4)
            self.assertEqual(stats["skipped_empty"], 1)
            self.assertEqual(stats["academic"], 2)
            self.assertEqual(stats["personal"], 1)
            self.assertEqual(stats["out_of_scope"], 1)
            self.assertEqual(stats["total_blocked"], 2)
            self.assertEqual(stats["blocked_csv_lines"], [2, 4])


class TestWebChatAndStreaming(unittest.TestCase):
    """Kiểm thử giao diện Web Chat và logic streaming phản hồi SSE (Phiên 3G)."""

    def test_stream_answer_custom_refusal_for_personal_data(self):
        from app.pipeline.rag_pipeline import Prepared
        from app.pipeline.generator.stream_handler import stream_answer
        from app.core.prompts import PERSONAL_REPLY

        p = Prepared(
            question="Điểm của em kỳ này bao nhiêu?",
            refused=True,
            refuse_reason="personal_data",
            messages=[],
            chunks=[],
            sources=[],
            best_dense_score=None,
            retrieval_ms=0,
            extra={"intent": "personal_data"},
            timing={"total_ms": 0},
        )
        events = list(stream_answer(p))
        joined = "".join(events)
        self.assertIn("event: token", joined)
        self.assertIn(PERSONAL_REPLY, joined)
        self.assertIn("event: done", joined)
        self.assertIn('"refuse_reason": "personal_data"', joined)

    def test_stream_answer_custom_refusal_for_out_of_scope(self):
        from app.pipeline.rag_pipeline import Prepared
        from app.pipeline.generator.stream_handler import stream_answer
        from app.core.prompts import OUT_OF_SCOPE_REPLY

        p = Prepared(
            question="Xin chào bot!",
            refused=True,
            refuse_reason="out_of_scope",
            messages=[],
            chunks=[],
            sources=[],
            best_dense_score=None,
            retrieval_ms=0,
            extra={"intent": "out_of_scope"},
            timing={"total_ms": 0},
        )
        events = list(stream_answer(p))
        joined = "".join(events)
        self.assertIn("event: token", joined)
        self.assertIn(OUT_OF_SCOPE_REPLY, joined)

    def test_web_routes_html_page_delivered(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        res_root = client.get("/")
        self.assertEqual(res_root.status_code, 200)
        self.assertIn("Trợ lý Hỏi đáp Quy chế", res_root.text)
        self.assertIn("text/html", res_root.headers.get("content-type", ""))

        res_chat = client.get("/chat")
        self.assertEqual(res_chat.status_code, 200)
        self.assertIn("Kho: 5 Quy chế", res_chat.text)

    def test_web_routes_api_chat_stream_response(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)
        # Test câu chào hỏi bị từ chối qua fast-path
        payload = {
            "question": "Xin chào bot!",
            "mode": "hybrid",
            "use_intent": True
        }
        res = client.post("/api/chat/stream", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/event-stream", res.headers.get("content-type", ""))
        self.assertIn("event: token", res.text)
        self.assertIn("event: done", res.text)


if __name__ == "__main__":
    unittest.main()
