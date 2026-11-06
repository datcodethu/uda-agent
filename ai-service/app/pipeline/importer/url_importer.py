"""Module thu thập, kiểm tra an toàn và trích xuất nguồn tri thức từ URL (NotebookLM-like).

Cung cấp:
1. is_safe_url: Phòng chống tấn công SSRF, chặn IP nội bộ, loopback, cloud metadata và kiểm tra domain allowlist.
2. clean_html_to_markdown: Trích xuất nội dung văn bản thuần, tiêu đề, bảng biểu Markdown và danh sách.
3. import_single_url: Thu thập 1 URL, làm sạch, tính hash, chống trùng lặp và đưa vào hàng đợi phê duyệt.
4. discover_website: Khám phá các trang con trong phạm vi allowlist có kiểm soát trần cứng.
"""
from __future__ import annotations

import csv
import datetime
import hashlib
import ipaddress
import logging
import os
import re
import socket
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("url_importer")

# Danh sách tên miền được phép thu thập mặc định
DEFAULT_ALLOWLIST = ["donga.edu.vn", "uda.edu.vn"]

# Danh sách từ khóa đường dẫn nhạy cảm cần loại trừ (đăng nhập, dữ liệu sinh viên cá nhân)
SENSITIVE_PATH_PATTERNS = [
    r"/login\b",
    r"/dang-nhap\b",
    r"/admin\b",
    r"/wp-admin\b",
    r"/cpanel\b",
    r"/user\b",
    r"/api/auth\b",
]
_SENSITIVE_PATH_RE = re.compile("|".join(SENSITIVE_PATH_PATTERNS), re.IGNORECASE)

DEFAULT_USER_AGENT = "DongA-RAG-Research-Bot/1.0 (+https://donga.edu.vn; Student Research Project)"

# Các định dạng tệp đính kèm cần phát hiện
ATTACHMENT_EXTS = {".pdf", ".docx", ".doc", ".xlsx", ".xls"}


def is_safe_ip(ip_str: str) -> bool:
    """Kiểm tra địa chỉ IP có phải là IP công cộng an toàn không.
    Ngăn chặn SSRF tới mạng nội bộ, loopback, link-local (169.254) và cloud metadata.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or str(ip) in ("0.0.0.0", "::")
        ):
            return False
        return True
    except ValueError:
        return False


def is_host_allowed(host: str, allowlist: list[str]) -> bool:
    """Kiểm tra host có thuộc allowlist theo ranh giới tên miền chuẩn (chống subdomain spoofing)."""
    h = host.lower().strip()
    if ":" in h:
        h = h.split(":")[0]
    for domain in allowlist:
        d = domain.lower().strip()
        if h == d or h.endswith("." + d):
            return True
    return False


def is_safe_url(
    url: str,
    allowlist: Optional[list[str]] = None,
    allow_local: bool = False,
) -> Tuple[bool, str]:
    """Kiểm tra toàn diện tính an toàn của URL trước khi gửi yêu cầu HTTP:
    1. Kiểm tra Scheme (chỉ nhận http, https).
    2. Chặn các trang cổng thông tin cá nhân hoặc yêu cầu đăng nhập.
    3. Kiểm tra ranh giới domain Allowlist.
    4. Phân giải DNS và chặn IP private/loopback/cloud metadata (chống SSRF).
    """
    if not url or not isinstance(url, str):
        return False, "URL rỗng hoặc không đúng định dạng chuỗi"

    url_clean = url.strip()
    try:
        parsed = urllib.parse.urlparse(url_clean)
    except Exception as e:
        return False, f"Lỗi cú pháp URL: {e}"

    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False, f"Lược đồ '{scheme}' không được chấp nhận (chỉ nhận http/https)"

    hostname = parsed.hostname
    if not hostname:
        return False, "Không tìm thấy tên miền (hostname) trong URL"

    hostname_clean = hostname.lower()

    # Kiểm tra cổng nếu có (chỉ cho phép 80, 443 hoặc port nội bộ khi allow_local=True)
    port = parsed.port
    if port and port not in (80, 443) and not allow_local:
        return False, f"Cổng mạng '{port}' không nằm trong cổng web chuẩn (80, 443)"

    # Kiểm tra chặn trang đăng nhập / dữ liệu sinh viên cá nhân (như my.uda.edu.vn)
    if "my.uda.edu.vn" in hostname_clean:
        return False, "Cổng thông tin sinh viên my.uda.edu.vn chứa dữ liệu cá nhân yêu cầu xác thực, không cào tự động"

    if _SENSITIVE_PATH_RE.search(parsed.path or ""):
        return False, "Đường dẫn chứa từ khóa đăng nhập hoặc trang quản trị nhạy cảm"

    # Kiểm tra Allowlist
    domains = allowlist if allowlist is not None else DEFAULT_ALLOWLIST
    if allow_local and hostname_clean in ("localhost", "127.0.0.1", "testserver"):
        pass  # Cho phép trong môi trường test
    elif not is_host_allowed(hostname_clean, domains):
        return False, f"Tên miền '{hostname_clean}' nằm ngoài danh sách Allowlist ({', '.join(domains)})"

    # Phân giải DNS và kiểm tra SSRF nếu không bật cờ allow_local
    if not allow_local:
        try:
            addr_info = socket.getaddrinfo(hostname_clean, port or (443 if scheme == "https" else 80))
            for res in addr_info:
                sockaddr = res[4]
                ip_cand = sockaddr[0]
                if not is_safe_ip(ip_cand):
                    return False, f"Địa chỉ IP phân giải '{ip_cand}' thuộc dải mạng nội bộ hoặc không an toàn (SSRF Block)"
        except socket.gaierror:
            return False, f"Không thể phân giải tên miền '{hostname_clean}' qua DNS"
        except Exception as e:
            return False, f"Lỗi thẩm tra địa chỉ IP: {e}"

    return True, "URL an toàn và hợp lệ"


def clean_html_to_markdown(html_content: str, base_url: str = "") -> Tuple[str, str, List[str]]:
    """Trích xuất Markdown sạch từ HTML:
    - Trích xuất tiêu đề văn bản (title hoặc h1).
    - Giữ các cấp tiêu đề (#, ##, ###).
    - Giữ cấu trúc bảng dữ liệu (Table -> Markdown Table).
    - Giữ danh sách (li -> - ).
    - Phát hiện các liên kết tệp đính kèm (.pdf, .docx).
    - Khử trùng thẻ script, style, nav, footer, iframe.
    """
    if not html_content:
        return "", "", []

    text = html_content
    # Loại bỏ script, style, nav, footer, noscript, svg, iframe (không xóa form vì trang ASP.NET bao bọc toàn bộ body bằng form)
    for tag in ["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "iframe"]:
        text = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Loại bỏ các nút bấm và ô nhập liệu form
    text = re.sub(r"<(?:input|button|select|option)[^>]*>.*?</(?:button|select)>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<(?:input|button)[^>]*>", " ", text, flags=re.IGNORECASE)

    # Trích xuất tiêu đề trang
    doc_title = "Tài liệu Web Đại học Đông Á"
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    if title_match:
        cand_title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
        # Loại bỏ đuôi thương hiệu lặp lại
        cand_title = re.sub(r"\s*[-|]\s*(?:Trường\s+)?Đại\s+học\s+Đông\s+Á.*$", "", cand_title, flags=re.IGNORECASE).strip()
        if cand_title:
            doc_title = cand_title
    else:
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.IGNORECASE | re.DOTALL)
        if h1_match:
            cand_title = re.sub(r"<[^>]+>", "", h1_match.group(1)).strip()
            if cand_title:
                doc_title = cand_title

    # Thu thập các link tệp đính kèm
    detected_attachments: List[str] = []
    for m in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', text, re.IGNORECASE):
        href = m.group(1).strip()
        full_href = urllib.parse.urljoin(base_url, href) if base_url else href
        parsed_href = urllib.parse.urlparse(full_href)
        ext = os.path.splitext(parsed_href.path.lower())[1]
        if ext in ATTACHMENT_EXTS:
            if full_href not in detected_attachments:
                detected_attachments.append(full_href)

    # Chuyển đổi bảng <table> thành Markdown Table
    def _convert_table(match):
        table_html = match.group(0)
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, flags=re.DOTALL | re.IGNORECASE)
        if not rows:
            return ""

        md_rows = []
        is_first = True
        col_count = 0

        for r in rows:
            cells = re.findall(r"<(?:th|td)[^>]*>(.*?)</(?:th|td)>", r, flags=re.DOTALL | re.IGNORECASE)
            clean_cells = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c)).strip() for c in cells]
            if not any(clean_cells):
                continue
            if is_first:
                col_count = len(clean_cells)
                md_rows.append("| " + " | ".join(clean_cells) + " |")
                md_rows.append("| " + " | ".join(["---"] * col_count) + " |")
                is_first = False
            else:
                # Cân bằng số cột
                if len(clean_cells) < col_count:
                    clean_cells.extend([""] * (col_count - len(clean_cells)))
                md_rows.append("| " + " | ".join(clean_cells[:col_count]) + " |")

        return "\n\n" + "\n".join(md_rows) + "\n\n"

    text = re.sub(r"<table[^>]*>.*?</table>", _convert_table, text, flags=re.DOTALL | re.IGNORECASE)

    # Chuyển đổi các thẻ heading
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"\n\n# \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"\n\n## \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"\n\n### \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h[4-6][^>]*>(.*?)</h[4-6]>", r"\n\n#### \1\n\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Chuyển đổi danh sách <li>
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", text, flags=re.DOTALL | re.IGNORECASE)

    # Chuyển đổi đoạn văn <p> và ngắt dòng <br>
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\n\1\n\n", text, flags=re.DOTALL | re.IGNORECASE)

    # Xóa toàn bộ các thẻ HTML còn lại
    text = re.sub(r"<[^>]+>", " ", text)

    # Giải mã thực thể HTML cơ bản
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')

    # Chuẩn hóa khoảng trắng và dòng trống
    lines = [unicodedata.normalize("NFC", l.strip()) for l in text.splitlines()]
    clean_lines = []
    last_empty = False
    for l in lines:
        if not l:
            if not last_empty:
                clean_lines.append("")
                last_empty = True
        else:
            clean_lines.append(l)
            last_empty = False

    cleaned_markdown = "\n".join(clean_lines).strip()
    return doc_title, cleaned_markdown, detected_attachments


class URLImporter:
    """Bộ nạp và kiểm duyệt nguồn kiến thức từ URL (NotebookLM-like)."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        allowlist: Optional[list[str]] = None,
        allow_local: bool = False,
    ):
        self.base_dir = base_dir or Path(r"E:\workspace\donga-rag-system\ai-service").resolve()
        self.allowlist = allowlist or DEFAULT_ALLOWLIST
        self.allow_local = allow_local

        self.staging_dir = self.base_dir / "data" / "staging_url_imports"
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        self.queue_path = self.base_dir / "data" / "url_approval_queue.csv"
        self._ensure_queue_file()

    def _ensure_queue_file(self) -> None:
        """Đảm bảo file url_approval_queue.csv tồn tại với đúng tiêu đề."""
        if not self.queue_path.exists():
            fieldnames = [
                "url_id", "source_url", "doc_title", "sha256", "status",
                "category", "discovered_at", "approved_at", "notes", "file_path", "attachment_links"
            ]
            with open(self.queue_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

    def load_queue(self) -> List[Dict[str, str]]:
        """Đọc toàn bộ danh sách hàng đợi phê duyệt URL."""
        if not self.queue_path.exists():
            return []
        with open(self.queue_path, "r", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def save_queue(self, rows: List[Dict[str, str]]) -> None:
        """Ghi lại toàn bộ danh sách hàng đợi phê duyệt URL."""
        fieldnames = [
            "url_id", "source_url", "doc_title", "sha256", "status",
            "category", "discovered_at", "approved_at", "notes", "file_path", "attachment_links"
        ]
        with open(self.queue_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    def import_single_url(
        self,
        url: str,
        category: str = "tai_lieu_tong_hop",
        mock_html: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Thu thập 1 URL đơn lẻ (Single URL Import):
        - Kiểm tra tính an toàn SSRF & Allowlist.
        - Tải nội dung web (hoặc nhận mock_html phục vụ kiểm thử).
        - Trích xuất Markdown sạch, tiêu đề và tệp đính kèm.
        - Tính hash SHA-256 chống trùng lặp.
        - Lưu vào staging và đưa vào url_approval_queue.csv ở trạng thái PENDING_REVIEW.
        """
        # 1. Thẩm tra an toàn URL
        is_safe, msg = is_safe_url(url, allowlist=self.allowlist, allow_local=self.allow_local)
        if not is_safe:
            return {
                "success": False,
                "error": f"URL_SECURITY_BLOCKED: {msg}",
                "status": "REJECTED",
                "source_url": url,
            }

        # 2. Thu thập nội dung
        if mock_html is not None:
            html_text = mock_html
            final_url = url
        else:
            try:
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": DEFAULT_USER_AGENT}
                )
                with urllib.request.urlopen(req, timeout=15.0) as resp:
                    final_url = resp.geturl()
                    # Kiểm tra an toàn URL sau chuyển hướng
                    is_safe_redirect, redirect_msg = is_safe_url(
                        final_url, allowlist=self.allowlist, allow_local=self.allow_local
                    )
                    if not is_safe_redirect:
                        return {
                            "success": False,
                            "error": f"REDIRECT_BLOCKED: Sau chuyển hướng URL không an toàn ({redirect_msg})",
                            "status": "REJECTED",
                            "source_url": url,
                        }

                    content_bytes = resp.read(5 * 1024 * 1024) # Giới hạn tối đa 5MB
                    encoding = resp.headers.get_content_charset() or "utf-8"
                    html_text = content_bytes.decode(encoding, errors="replace")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"FETCH_FAILED: {type(e).__name__} - {e}",
                    "status": "ERROR",
                    "source_url": url,
                }

        # 3. Làm sạch và trích xuất Markdown
        doc_title, md_content, attachments = clean_html_to_markdown(html_text, base_url=final_url)
        if len(md_content.strip()) < 50:
            return {
                "success": False,
                "error": "CONTENT_EMPTY: Nội dung trang quá ít chữ hoặc không trích xuất được văn bản",
                "status": "REJECTED",
                "source_url": url,
            }

        # 4. Tính toán SHA-256
        sha256 = hashlib.sha256(md_content.encode("utf-8")).hexdigest()

        # 5. Kiểm tra trùng lặp
        queue_rows = self.load_queue()
        for q in queue_rows:
            if q["sha256"] == sha256 or q["source_url"] == final_url:
                return {
                    "success": True,
                    "duplicate": True,
                    "url_id": q["url_id"],
                    "status": q["status"],
                    "doc_title": q["doc_title"],
                    "source_url": final_url,
                    "message": f"Nội dung URL đã tồn tại trong hàng đợi với mã {q['url_id']} (Trạng thái: {q['status']})",
                }

        # 6. Lưu file vào staging
        filename = f"{sha256[:16]}.md"
        out_path = self.staging_dir / filename
        
        # Thêm header metadata an toàn
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        full_content = (
            f"# {doc_title}\n\n"
            f"> Nguồn tham chiếu: [{final_url}]({final_url})\n"
            f"> Thời gian thu thập: {now_iso}\n\n"
            f"{md_content}\n"
        )
        out_path.write_text(full_content, encoding="utf-8")

        # 7. Ghi vào hàng đợi phê duyệt
        url_id = f"URL-{datetime.datetime.now().strftime('%Y%m%d')}-{sha256[:6].upper()}"
        new_row = {
            "url_id": url_id,
            "source_url": final_url,
            "doc_title": doc_title,
            "sha256": sha256,
            "status": "PENDING_REVIEW",
            "category": category,
            "discovered_at": now_iso,
            "approved_at": "",
            "notes": f"Trích xuất thành công {len(md_content)} ký tự. Phát hiện {len(attachments)} liên kết đính kèm.",
            "file_path": str(out_path.relative_to(self.base_dir)).replace("\\", "/"),
            "attachment_links": "; ".join(attachments[:5]),
        }
        queue_rows.append(new_row)
        self.save_queue(queue_rows)

        return {
            "success": True,
            "duplicate": False,
            "url_id": url_id,
            "status": "PENDING_REVIEW",
            "doc_title": doc_title,
            "sha256": sha256,
            "source_url": final_url,
            "file_path": new_row["file_path"],
            "attachments_count": len(attachments),
            "content_length": len(md_content),
        }

    def discover_website(
        self,
        seed_url: str,
        max_depth: int = 1,
        max_pages: int = 5,
        min_delay: float = 2.0,
        mock_pages: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Khám phá các trang con từ URL hạt giống (Website Discovery):
        - Giới hạn độ sâu (max_depth) và số trang (max_pages).
        - Chỉ duyệt trong phạm vi allowlist.
        - Phát hiện liên kết và đính kèm.
        - Mọi trang đều đưa vào staging ở trạng thái PENDING_REVIEW, KHÔNG auto-ingest.
        """
        is_safe, msg = is_safe_url(seed_url, allowlist=self.allowlist, allow_local=self.allow_local)
        if not is_safe:
            return {"success": False, "error": f"SEED_URL_BLOCKED: {msg}", "discovered": []}

        discovered: List[Dict[str, Any]] = []
        visited_urls: Set[str] = set()
        queue: List[Tuple[str, int]] = [(seed_url, 0)]

        while queue and len(discovered) < max_pages:
            curr_url, depth = queue.pop(0)
            if curr_url in visited_urls:
                continue
            visited_urls.add(curr_url)

            # Cào trang hiện tại
            html_to_use = mock_pages.get(curr_url) if mock_pages else None
            res = self.import_single_url(curr_url, mock_html=html_to_use)
            if res.get("success"):
                discovered.append(res)

            if depth < max_depth and (mock_pages is not None or not self.allow_local):
                # Trích xuất các liên kết con từ html
                html_src = html_to_use or ""
                for m in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>', html_src, re.IGNORECASE):
                    link = urllib.parse.urljoin(curr_url, m.group(1).strip())
                    clean_link, _ = urllib.parse.urldefrag(link)
                    if clean_link not in visited_urls and is_safe_url(clean_link, allowlist=self.allowlist, allow_local=self.allow_local)[0]:
                        queue.append((clean_link, depth + 1))

            if not mock_pages:
                time.sleep(min_delay)

        return {
            "success": True,
            "seed_url": seed_url,
            "discovered_count": len(discovered),
            "discovered": discovered,
        }


# Hàm tiện ích module-level
def import_single_url(url: str, **kwargs) -> Dict[str, Any]:
    importer = URLImporter()
    return importer.import_single_url(url, **kwargs)


def discover_website(seed_url: str, **kwargs) -> Dict[str, Any]:
    importer = URLImporter()
    return importer.discover_website(seed_url, **kwargs)
