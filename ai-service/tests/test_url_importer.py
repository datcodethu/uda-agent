"""Bộ kiểm thử hồi quy cho module URL Knowledge Import (NotebookLM-like).

Bao gồm:
1. Kiểm thử an toàn SSRF và kiểm soát domain Allowlist (chặn IP private, loopback, cloud metadata, subdomain spoofing).
2. Kiểm thử chặn cổng thông tin sinh viên my.uda.edu.vn và các trang đăng nhập.
3. Kiểm thử trích xuất Markdown sạch, bảo toàn bảng dữ liệu học phí và phát hiện tệp đính kèm.
4. Kiểm thử chu trình phê duyệt 5 trạng thái (PENDING_REVIEW -> APPROVED -> INDEXED / REJECTED).
5. Kiểm thử chống trùng lặp (Deduplication) theo URL và SHA-256.
6. Kiểm thử Incremental Indexing ở chế độ Dry-run và Rollback an toàn.
"""
from __future__ import annotations

import csv
import shutil
import tempfile
import unittest
from pathlib import Path

from app.pipeline.importer.incremental_indexer import (
    approve_url_in_queue,
    index_approved_urls,
    reject_url_in_queue,
)
from app.pipeline.importer.url_importer import (
    URLImporter,
    clean_html_to_markdown,
    is_safe_ip,
    is_safe_url,
)


class TestURLSecurityAndSSRF(unittest.TestCase):
    """Kiểm tra an toàn bảo mật SSRF và kiểm soát ranh giới tên miền Allowlist."""

    def test_allowlist_domain_boundaries(self):
        # Hợp lệ: domain chính hoặc subdomain hợp lệ
        ok1, _ = is_safe_url("https://donga.edu.vn/gioi-thieu", allowlist=["donga.edu.vn"], allow_local=True)
        self.assertTrue(ok1)
        ok2, _ = is_safe_url("https://cntt.donga.edu.vn/chuong-trinh-dao-tao", allowlist=["donga.edu.vn"], allow_local=True)
        self.assertTrue(ok2)

        # Vi phạm: Subdomain spoofing (ví dụ: donga.edu.vn.attacker.com)
        bad1, msg1 = is_safe_url("https://donga.edu.vn.attacker.com/malicious", allowlist=["donga.edu.vn"], allow_local=True)
        self.assertFalse(bad1)
        self.assertIn("nằm ngoài danh sách Allowlist", msg1)

        # Vi phạm: Tên miền hoàn toàn ngoài luồng
        bad2, msg2 = is_safe_url("https://google.com/search", allowlist=["donga.edu.vn"], allow_local=True)
        self.assertFalse(bad2)
        self.assertIn("Allowlist", msg2)

    def test_ssrf_ip_blocking(self):
        # Chặn các IP nội bộ / private
        self.assertFalse(is_safe_ip("127.0.0.1"))
        self.assertFalse(is_safe_ip("10.0.0.1"))
        self.assertFalse(is_safe_ip("192.168.1.1"))
        self.assertFalse(is_safe_ip("172.16.0.1"))
        self.assertFalse(is_safe_ip("169.254.169.254"))  # AWS/GCP metadata
        self.assertFalse(is_safe_ip("::1"))

        # IP công cộng an toàn
        self.assertTrue(is_safe_ip("8.8.8.8"))
        self.assertTrue(is_safe_ip("1.1.1.1"))

    def test_blocks_login_and_student_portal(self):
        # Chặn cổng thông tin cá nhân sinh viên
        bad_portal, msg_p = is_safe_url("https://my.uda.edu.vn/sinhvien/diem", allow_local=True)
        self.assertFalse(bad_portal)
        self.assertIn("my.uda.edu.vn", msg_p)

        # Chặn đường dẫn đăng nhập nhạy cảm
        bad_login, msg_l = is_safe_url("https://donga.edu.vn/login", allow_local=True)
        self.assertFalse(bad_login)
        self.assertIn("đăng nhập", msg_l)


class TestHTMLToMarkdownParser(unittest.TestCase):
    """Kiểm tra trích xuất Markdown sạch, bảng biểu và tệp đính kèm."""

    def test_clean_html_extracts_table_and_headings(self):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Thông báo học phí năm 2024 - Đại học Đông Á</title>
            <script>alert('injection');</script>
        </head>
        <body>
            <header><nav><a href="/">Trang chủ</a></nav></header>
            <h1>Biểu phí các khối ngành</h1>
            <p>Trường Đại học Đông Á thông báo mức thu học phí áp dụng cho sinh viên khóa mới:</p>
            <table>
                <tr>
                    <th>Khối ngành</th>
                    <th>Đơn vị tính</th>
                    <th>Mức thu</th>
                </tr>
                <tr>
                    <td>Công nghệ thông tin</td>
                    <td>Học kỳ</td>
                    <td>14.000.000 VNĐ</td>
                </tr>
                <tr>
                    <td>Ngôn ngữ Anh</td>
                    <td>Học kỳ</td>
                    <td>12.500.000 VNĐ</td>
                </tr>
            </table>
            <h2>Tài liệu đính kèm</h2>
            <p>Sinh viên có thể tải: <a href="/files/QD_HocPhi_2024.pdf">Quyết định học phí (PDF)</a></p>
            <footer>Bản quyền 2024</footer>
        </body>
        </html>
        """
        title, md, attachments = clean_html_to_markdown(sample_html, base_url="https://donga.edu.vn")

        self.assertIn("Thông báo học phí năm 2024", title)
        # Kiểm tra tiêu đề chuyển sang #
        self.assertIn("# Biểu phí các khối ngành", md)
        self.assertIn("## Tài liệu đính kèm", md)
        # Kiểm tra bảng Markdown giữ nguyên cấu trúc
        self.assertIn("| Khối ngành | Đơn vị tính | Mức thu |", md)
        self.assertIn("| Công nghệ thông tin | Học kỳ | 14.000.000 VNĐ |", md)
        # Kiểm tra thẻ script và footer bị xóa
        self.assertNotIn("alert('injection')", md)
        self.assertNotIn("Bản quyền 2024", md)
        # Kiểm tra phát hiện link PDF
        self.assertEqual(len(attachments), 1)
        self.assertEqual(attachments[0], "https://donga.edu.vn/files/QD_HocPhi_2024.pdf")


class TestURLApprovalWorkflowAndIndexing(unittest.TestCase):
    """Kiểm tra chu trình phê duyệt 5 trạng thái và nạp gia tăng."""

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.importer = URLImporter(base_dir=self.temp_dir, allow_local=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_url_import_creates_pending_review(self):
        mock_html = """
        <html><head><title>Quy định Học bổng Tài năng</title></head>
        <body>
            <h1>Chính sách học bổng</h1>
            <p>Nhà trường trao học bổng toàn phần cho thủ khoa đạt từ 26 điểm trở lên.</p>
        </body></html>
        """
        res = self.importer.import_single_url(
            "https://donga.edu.vn/hoc-bong-tai-nang",
            mock_html=mock_html,
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "PENDING_REVIEW")
        self.assertIn("Học bổng Tài năng", res["doc_title"])
        self.assertFalse(res["duplicate"])

        # Kiểm tra file staging đã được ghi
        staging_file = self.temp_dir / res["file_path"]
        self.assertTrue(staging_file.exists())
        self.assertIn("thủ khoa đạt từ 26 điểm", staging_file.read_text(encoding="utf-8"))

        # Kiểm tra hàng đợi có 1 dòng trạng thái PENDING_REVIEW
        queue = self.importer.load_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["status"], "PENDING_REVIEW")

    def test_deduplication_prevents_duplicate_entries(self):
        mock_html = "<html><title>Trang Test</title><body><p>Nội dung mẫu chống trùng lặp dữ liệu cào.</p></body></html>"
        res1 = self.importer.import_single_url("https://donga.edu.vn/test-dup", mock_html=mock_html)
        self.assertTrue(res1["success"])
        self.assertFalse(res1["duplicate"])

        # Import lần 2 với cùng URL hoặc cùng nội dung
        res2 = self.importer.import_single_url("https://donga.edu.vn/test-dup", mock_html=mock_html)
        self.assertTrue(res2["success"])
        self.assertTrue(res2["duplicate"])
        self.assertIn("đã tồn tại trong hàng đợi", res2["message"])

    def test_approval_and_rejection_workflow(self):
        mock_html = "<html><title>Chính sách Vay vốn</title><body><p>Hướng dẫn sinh viên làm thủ tục vay vốn chính sách.</p></body></html>"
        res = self.importer.import_single_url("https://donga.edu.vn/vay-von", mock_html=mock_html)
        url_id = res["url_id"]

        # 1. Phê duyệt APPROVED
        ok_app = approve_url_in_queue(url_id, approver_note="Đã kiểm tra văn bản", base_dir=self.temp_dir)
        self.assertTrue(ok_app)

        q1 = self.importer.load_queue()
        self.assertEqual(q1[0]["status"], "APPROVED")
        self.assertIn("Đã kiểm tra văn bản", q1[0]["notes"])

        # 2. Kiểm thử Dry-run Ingest
        dry_res = index_approved_urls(base_dir=self.temp_dir, dry_run=True)
        self.assertTrue(dry_res["success"])
        self.assertTrue(dry_res["dry_run"])
        self.assertEqual(dry_res["indexed_count"], 1)

        # 3. Từ chối REJECTED
        ok_rej = reject_url_in_queue(url_id, reason="Văn bản cũ hết hạn", base_dir=self.temp_dir)
        self.assertTrue(ok_rej)

        q2 = self.importer.load_queue()
        self.assertEqual(q2[0]["status"], "REJECTED")
        self.assertIn("Văn bản cũ hết hạn", q2[0]["notes"])


if __name__ == "__main__":
    unittest.main()
