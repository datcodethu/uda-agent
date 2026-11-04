"""
Thu thap du lieu web ngoai tuyen (Crawler) dung Crawl4AI cho de tai NCKH DH Dong A.
Tuan thu chat che:
1. Chi cao cac host/domain trong allowlist.txt (so khop domain/subdomain voi ranh gioi dau cham).
2. Chi chap nhan scheme http va https.
3. Kiem tra dia chi sau chuyen huong; neu roi allowlist thi loai bo.
4. Tuan thu robots.txt.
5. Mac dinh --dry-run (khong tai noi dung, khong ghi file, chi kiem tra va uoc tinh).
6. Tran cung an toan: toi da 100 trang, do sau toi da 2, nghi toi thieu 2.0s, timeout toi da 10 phut.
7. Dau ra: crawl_staging/pages/<hash>.txt (NFC), manifest.csv (BOM), links_dinh_kem.csv (BOM).
8. AN TOAN: Khong doc/in noi dung cao hay tieu de trang vao chat console.
"""

import argparse
import asyncio
import csv
import hashlib
import logging
import os
import re
import sys
import time
import unicodedata
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser
import urllib.request

# Cau hinh logging co ban
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("crawler")

# Cac tran cung khong the vuot qua bang tham so
HARD_MAX_PAGES = 100
HARD_MAX_DEPTH = 2
HARD_MIN_DELAY = 2.0
HARD_MAX_PAGE_TIMEOUT = 60.0
HARD_MAX_TOTAL_TIMEOUT = 600.0

# Duoi tep dinh kem can liet ke (chi liet ke URL, khong tai tep)
ATTACHMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx"}

DEFAULT_USER_AGENT = "DongA-RAG-Research-Bot/1.0 (+https://donga.edu.vn; Student Research Project)"


def load_lines(filepath: str) -> List[str]:
    """Doc file theo dong, bo qua dong trong va comment bat dau bang #. Ho tro loai bo markdown bullet (*, -, +)."""
    if not os.path.exists(filepath):
        return []
    items = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Loai bo cac ky tu danh sach markdown nhu *, -, +, 1. o dau dong
            line = re.sub(r"^[\*\-\+]\s+", "", line)
            line = re.sub(r"^\d+\.\s+", "", line)
            line = line.strip()
            if line and not line.startswith("#"):
                items.append(line)
    return items


def normalize_url(url: str) -> str:
    """Chuan hoa URL: loai bo fragment (#), viet thuong scheme va host."""
    clean_url, _ = urldefrag(url.strip())
    parsed = urlparse(clean_url)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    # Giu nguyen query neu co
    if parsed.query:
        return f"{scheme}://{netloc}{path}?{parsed.query}"
    return f"{scheme}://{netloc}{path}"


def is_valid_scheme(url: str) -> bool:
    """Chi chap nhan http va https, chan tat ca scheme khac nhu javascript:, file:, mailto:."""
    parsed = urlparse(url)
    return parsed.scheme.lower() in {"http", "https"}


def extract_hostname(url: str) -> str:
    """Trich xuat hostname bo qua port neu co."""
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if ":" in netloc:
        return netloc.split(":")[0]
    return netloc


def is_host_allowed(url: str, allowlist: List[str], allow_local: bool = False) -> bool:
    """
    Kiem tra hostname co nam trong allowlist khong.
    So khop dung ten may chu hoac ten mien con voi ranh gioi dau cham.
    Vi du:
      donga.edu.vn -> cho phep donga.edu.vn, daotao.donga.edu.vn
      chan ten mien gia mao nhu: donga.edu.vn.attacker.com, fakedonga.edu.vn
    """
    if not is_valid_scheme(url):
        return False

    host = extract_hostname(url)
    if not host:
        return False

    if allow_local and host in {"localhost", "127.0.0.1", "::1"}:
        return True

    for allowed in allowlist:
        allowed = allowed.strip().lower()
        if not allowed:
            continue
        # Chinh xac hostname
        if host == allowed:
            return True
        # La subdomain voi ranh gioi dau cham
        if host.endswith("." + allowed):
            return True

    return False


def is_attachment_link(url: str) -> Tuple[bool, str]:
    """Kiem tra xem URL co phai lien ket tep dinh kem (pdf, doc, docx, xls, xlsx) khong."""
    parsed = urlparse(url)
    path = parsed.path.lower()
    _, ext = os.path.splitext(path)
    if ext in ATTACHMENT_EXTENSIONS:
        return True, ext.lstrip(".")
    return False, ""


def classify_suspicious_type(text: str) -> str:
    """
    Dem so dong bat dau bang Chuong hoac Dieu de phan loai so bo.
    Tu 3 dong bat dau bang Dieu tro len: co_cau_truc_dieu; nguoc lai: khac.
    Ho tro ca dinh dang markdown nhu **Dieu 1** hoac - Dieu 1.
    """
    lines = text.splitlines()
    dieu_count = 0
    for line in lines:
        cleaned = line.strip()
        # So khop bat dau bang Dieu hoac kem ky tu markdown (*, -, #, >)
        if re.match(r"^[\*\-\#\>\s]*(điều|dieu)\b", cleaned, re.IGNORECASE):
            dieu_count += 1

    if dieu_count >= 3:
        return "co_cau_truc_dieu"
    return "khac"


def sanitize_nfc(text: str) -> str:
    """Chuan hoa chuoi Unicode sang dang NFC."""
    return unicodedata.normalize("NFC", text)


class RobotsChecker:
    """Kiem tra robots.txt voi co che cache theo host de khong goi lap lai."""

    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.user_agent = user_agent
        self._parsers: Dict[str, Optional[RobotFileParser]] = {}

    def is_allowed(self, url: str, timeout: float = 10.0) -> Tuple[bool, str]:
        """
        Kiem tra URL co duoc robots.txt cho phep khong.
        Tra ve (is_allowed, reason).
        """
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        if base not in self._parsers:
            rp = RobotFileParser()
            robots_url = f"{base}/robots.txt"
            try:
                req = urllib.request.Request(
                    robots_url,
                    headers={"User-Agent": self.user_agent}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8", errors="replace")
                        rp.parse(content.splitlines())
                        self._parsers[base] = rp
                    else:
                        # Status khac 200 (vi du 404): mac dinh cho phep
                        self._parsers[base] = None
            except Exception as e:
                # Loi mang hoac khong co robots.txt -> mac dinh cho phep
                self._parsers[base] = None

        rp = self._parsers.get(base)
        if rp is None:
            return True, "robots_txt_not_found_or_allowed"

        allowed = rp.can_fetch(self.user_agent, url)
        if allowed:
            return True, "robots_txt_allowed"
        return False, "robots_txt_disallowed"


def run_dry_run(
    seeds: List[str],
    allowlist: List[str],
    allow_local: bool = False,
    user_agent: str = DEFAULT_USER_AGENT,
    max_pages: int = 20,
    delay: float = 2.0,
) -> Dict[str, any]:
    """
    Che do Dry-Run:
    - Kiem tra danh sach seed URLs.
    - Kiem tra tinh hop le cua scheme, allowlist, robots.txt.
    - KHONG tai noi dung trang.
    - KHONG ghi bat ky tep nao vao disk.
    - In tong ket: so URL hop le, so bi chan theo tung ly do, thoi gian uoc tinh.
    """
    robots_checker = RobotsChecker(user_agent=user_agent)
    projected_urls = []
    blocked_reasons: Dict[str, int] = {
        "invalid_scheme": 0,
        "outside_allowlist": 0,
        "robots_disallowed": 0,
    }

    print("\n" + "=" * 60)
    print("CHẾ ĐỘ DRY-RUN (KIỂM TRA DỰ KIẾN, KHÔNG TẢI TRANG, KHÔNG GHI FILE)")
    print("=" * 60)
    print(f"User-Agent   : {user_agent}")
    print(f"Allowlist    : {', '.join(allowlist) if allowlist else '(Rỗng)'}")
    print(f"Allow Local  : {allow_local}")
    print(f"Max Pages    : {max_pages}")
    print(f"Min Delay    : {delay:.1f}s")
    print("-" * 60)

    for raw_url in seeds:
        url = normalize_url(raw_url)
        parsed = urlparse(url)

        # 1. Kiem tra Scheme
        if not is_valid_scheme(url):
            blocked_reasons["invalid_scheme"] += 1
            print(f"[CHẶN - LƯỢC ĐỒ KHÔNG HỢP LỆ]: {parsed.scheme}://... (chỉ nhận http/https)")
            continue

        # 2. Kiem tra Allowlist
        if not is_host_allowed(url, allowlist, allow_local=allow_local):
            blocked_reasons["outside_allowlist"] += 1
            print(f"[CHẶN - NGOÀI ALLOWLIST]: {extract_hostname(url)} (đường dẫn: {parsed.path})")
            continue

        # 3. Kiem tra Robots.txt
        robots_ok, reason = robots_checker.is_allowed(url)
        if not robots_ok:
            blocked_reasons["robots_disallowed"] += 1
            print(f"[CHẶN - ROBOTS.TXT CẤM]: host={parsed.netloc}, path={parsed.path}")
            continue

        # URL hop le
        projected_urls.append({
            "url": url,
            "host": parsed.netloc,
            "path": parsed.path or "/",
        })
        if len(projected_urls) >= max_pages:
            break

    print("-" * 60)
    print("DANH SÁCH URL DỰ KIẾN THU THẬP:")
    for idx, item in enumerate(projected_urls, 1):
        print(f"  {idx}. [Host: {item['host']}] [Path: {item['path']}]")

    est_duration = len(projected_urls) * delay
    print("-" * 60)
    print(f"Tổng số URL dự kiến cào   : {len(projected_urls)}")
    print(f"Số URL bị chặn theo lý do:")
    print(f"  - Lược đồ không hợp lệ : {blocked_reasons['invalid_scheme']}")
    print(f"  - Nằm ngoài Allowlist  : {blocked_reasons['outside_allowlist']}")
    print(f"  - Robots.txt cấm       : {blocked_reasons['robots_disallowed']}")
    print(f"Thời gian chạy ước tính   : ~{est_duration:.1f} giây (~{est_duration/60:.2f} phút)")
    print("=" * 60 + "\n")

    return {
        "projected_count": len(projected_urls),
        "blocked_reasons": blocked_reasons,
        "est_duration": est_duration,
        "projected_urls": projected_urls,
    }


async def run_apply(
    seeds: List[str],
    allowlist: List[str],
    output_dir: str,
    allow_local: bool = False,
    user_agent: str = DEFAULT_USER_AGENT,
    max_pages: int = 20,
    max_depth: int = 1,
    delay: float = 2.0,
    page_timeout: float = 30.0,
    total_timeout: float = 600.0,
) -> Dict[str, any]:
    """
    Che do Apply (Cao that):
    - Khoi tao crawl4ai AsyncWebCrawler.
    - Duyet BFS theo hang doi (url, depth).
    - Tuan thu allowlist truoc va sau khi chuyen huong.
    - Trich xuat lien ket dinh kem (chi ghi link, khong tai tep).
    - Trich xuat markdown, chuan hoa NFC, bo trung theo sha256.
    - Luu pages/<sha256[:16]>.txt, manifest.csv (BOM), links_dinh_kem.csv (BOM).
    """
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    except ImportError as e:
        logger.error("Chua cai dat crawl4ai. Hay chay 'pip install -r requirements-crawler.txt' trong venv cua crawler.")
        raise RuntimeError("Chua cai dat crawl4ai. Vui long su dung ai-service\\crawler\\venv.") from e

    pages_dir = os.path.join(output_dir, "pages")
    os.makedirs(pages_dir, exist_ok=True)
    manifest_path = os.path.join(output_dir, "manifest.csv")
    attachments_path = os.path.join(output_dir, "links_dinh_kem.csv")

    robots_checker = RobotsChecker(user_agent=user_agent)
    start_time = time.time()

    # Khoi tao manifest va links_dinh_kem neu chua co
    if not os.path.exists(manifest_path):
        with open(manifest_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "url", "url_cuoi", "ma_http", "loai_noi_dung", "so_ky_tu",
                "sha256", "thoi_gian_cao", "robots_ok", "loai_nghi_ngo", "so_link_dinh_kem"
            ])

    if not os.path.exists(attachments_path):
        with open(attachments_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["url_trang_nguon", "url_tep_dinh_kem", "loai_tep"])

    # Tap cac sha256 da luu de loai trung lap
    seen_hashes: Set[str] = set()
    visited_urls: Set[str] = set()

    # Doc hash cu neu co
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                h = row.get("sha256")
                if h:
                    seen_hashes.add(h)
                u = row.get("url")
                if u:
                    visited_urls.add(u)

    queue: List[Tuple[str, int]] = []
    for s in seeds:
        u = normalize_url(s)
        if u not in visited_urls:
            queue.append((u, 0))

    saved_count = 0
    duplicate_count = 0
    blocked_count = 0

    browser_config = BrowserConfig(
        headless=True,
        user_agent=user_agent,
        verbose=False,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=int(page_timeout * 1000), # crawl4ai ms
    )

    print(f"\n[BẮT ĐẦU CÀO THẬT]: Tối đa {max_pages} trang, độ sâu {max_depth}, nghỉ {delay:.1f}s.")
    print(f"Thư mục lưu trữ: {output_dir}")

    async with AsyncWebCrawler(config=browser_config) as crawler:
        while queue and saved_count < max_pages:
            # Kiem tra tong thoi gian
            if time.time() - start_time > total_timeout:
                logger.warning(f"Vuot qua tong thoi gian cho phep ({total_timeout}s). Dung thu thap.")
                break

            current_url, depth = queue.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            # Kiem tra Scheme
            if not is_valid_scheme(current_url):
                blocked_count += 1
                continue

            # Kiem tra Allowlist
            if not is_host_allowed(current_url, allowlist, allow_local=allow_local):
                blocked_count += 1
                continue

            # Kiem tra Robots
            robots_ok, _ = robots_checker.is_allowed(current_url)
            if not robots_ok:
                blocked_count += 1
                continue

            # Nghi toi thieu giua cac yeu cau
            await asyncio.sleep(delay)

            crawl_time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                result = await crawler.arun(url=current_url, config=run_config)
            except Exception as e:
                logger.error(f"Loi khi cao {current_url}: {type(e).__name__}")
                continue

            # Lay URL cuoi sau chuyen huong
            final_url = normalize_url(getattr(result, "final_url", None) or getattr(result, "url", current_url))

            # Kiem tra xem sau chuyen huong co con trong allowlist khong
            if not is_host_allowed(final_url, allowlist, allow_local=allow_local):
                logger.warning(f"URL sau chuyen huong roi khoi allowlist: {final_url}. Bo qua.")
                blocked_count += 1
                continue

            status_code = getattr(result, "status_code", 200) or 200
            if status_code >= 400:
                logger.warning(f"Ma HTTP loi {status_code} tai {current_url}. Bo qua.")
                continue

            # Lay noi dung markdown
            raw_md = ""
            if hasattr(result, "markdown"):
                if hasattr(result.markdown, "raw_markdown"):
                    raw_md = result.markdown.raw_markdown
                elif isinstance(result.markdown, str):
                    raw_md = result.markdown
            if not raw_md and hasattr(result, "cleaned_html"):
                raw_md = result.cleaned_html or ""

            # Chuan hoa Unicode NFC
            clean_text = sanitize_nfc(raw_md.strip())
            char_count = len(clean_text)

            # Tinh SHA-256
            sha256_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

            # Trich xuat cac lien ket trong trang de phan loai: tep dinh kem vs BFS
            links = []
            if hasattr(result, "links"):
                if isinstance(result.links, dict):
                    # crawl4ai 0.4+: dict chua 'internal' va 'external'
                    for category in ("internal", "external"):
                        cat_links = result.links.get(category, [])
                        for item in cat_links:
                            href = item.get("href") if isinstance(item, dict) else str(item)
                            if href:
                                links.append(href)
                elif isinstance(result.links, list):
                    for item in result.links:
                        href = item.get("href") if isinstance(item, dict) else str(item)
                        if href:
                            links.append(href)

            # Xu ly link dinh kem va link duyet tiep
            found_attachments = []
            next_links = []
            for lk in links:
                abs_lk = normalize_url(urljoin(final_url, lk))
                is_att, ext = is_attachment_link(abs_lk)
                if is_att:
                    found_attachments.append((abs_lk, ext))
                else:
                    if is_valid_scheme(abs_lk) and is_host_allowed(abs_lk, allowlist, allow_local=allow_local):
                        next_links.append(abs_lk)

            # Ghi cac lien ket dinh kem tim thay vao links_dinh_kem.csv
            if found_attachments:
                with open(attachments_path, "a", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    for att_url, att_type in found_attachments:
                        writer.writerow([current_url, att_url, att_type])

            # Bo trung theo sha256
            if sha256_hash in seen_hashes:
                duplicate_count += 1
                logger.info(f"[TRÙNG HASH] Trang {current_url} co sha256 da ton tai. Bo qua ghi tep.")
                continue

            seen_hashes.add(sha256_hash)

            # Xac dinh loai nghi ngo
            suspicious_type = classify_suspicious_type(clean_text)

            # Luu file markdown sach
            short_hash = sha256_hash[:16]
            file_name = f"{short_hash}.txt"
            page_file_path = os.path.join(pages_dir, file_name)
            with open(page_file_path, "w", encoding="utf-8") as pf:
                pf.write(clean_text)

            saved_count += 1

            # Ghi vao manifest.csv
            with open(manifest_path, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_url,
                    final_url,
                    status_code,
                    "text/markdown",
                    char_count,
                    sha256_hash,
                    crawl_time_str,
                    "dung",
                    suspicious_type,
                    len(found_attachments)
                ])

            print(f"  [ĐÃ LƯU] #{saved_count}: {file_name} ({char_count} ký tự, {len(found_attachments)} link đính kèm, nghi_ngờ: {suspicious_type})")

            # Day cac link con vao hang doi neu do sau hop le
            if depth < max_depth:
                for nl in next_links:
                    if nl not in visited_urls and nl not in [q[0] for q in queue]:
                        queue.append((nl, depth + 1))

    total_spent = time.time() - start_time
    print("-" * 60)
    print(f"HOÀN TẤT THU THẬP:")
    print(f"  - Số trang đã lưu mới : {saved_count}")
    print(f"  - Số trang bị trùng   : {duplicate_count}")
    print(f"  - Tổng thời gian chạy : {total_spent:.1f}s")
    print(f"  - Manifest cập nhật   : {manifest_path}")
    print(f"  - Links đính kèm      : {attachments_path}")
    print("=" * 60 + "\n")

    return {
        "saved_count": saved_count,
        "duplicate_count": duplicate_count,
        "total_spent": total_spent,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Cong cu thu thap du lieu web ngoai tuyen (Crawler)")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--dry-run", action="store_true", default=True, help="Chi kiem tra va uoc tinh, khong tai trang (Mac dinh)")
    mode_group.add_argument("--apply", action="store_true", help="Chay cao that va luu staging")

    parser.add_argument("--test-local", action="store_true", help="Cho phep netloc la localhost/127.0.0.1 phuc vu kiem thu noi bo")
    parser.add_argument("--max-pages", type=int, default=20, help="So trang toi da (mac dinh 20, tran cung 100)")
    parser.add_argument("--max-depth", type=int, default=1, help="Do sau duyet link toi da (mac dinh 1, tran cung 2)")
    parser.add_argument("--delay", type=float, default=2.0, help="Thoi gian nghi giua cac yeu cau (mac dinh 2.0s, toi thieu 2.0s)")
    parser.add_argument("--page-timeout", type=float, default=30.0, help="Thoi gian cho moi trang (mac dinh 30s, toi da 60s)")
    parser.add_argument("--total-timeout", type=float, default=600.0, help="Tong thoi gian chay toi da (mac dinh 600s, tran cung 600s)")
    parser.add_argument("--allowlist-file", type=str, default=None, help="Duong dan tep allowlist.txt")
    parser.add_argument("--seeds-file", type=str, default=None, help="Duong dan tep seeds.txt")
    parser.add_argument("--output-dir", type=str, default=None, help="Thu muc staging dau ra")
    parser.add_argument("--user-agent", type=str, default=DEFAULT_USER_AGENT, help="User agent danh cho bot nghien cuu")

    return parser.parse_args()


def main():
    args = parse_args()

    # Xac dinh thu muc goc crawler
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

    allowlist_path = args.allowlist_file or os.path.join(current_dir, "allowlist.txt")
    seeds_path = args.seeds_file or os.path.join(current_dir, "seeds.txt")
    output_dir = args.output_dir or os.path.join(project_root, "ai-service", "data", "crawl_staging")

    # Ap dung cac tran cung an toan
    max_pages = min(max(1, args.max_pages), HARD_MAX_PAGES)
    max_depth = min(max(0, args.max_depth), HARD_MAX_DEPTH)
    delay = max(args.delay, HARD_MIN_DELAY)
    page_timeout = min(max(5.0, args.page_timeout), HARD_MAX_PAGE_TIMEOUT)
    total_timeout = min(max(30.0, args.total_timeout), HARD_MAX_TOTAL_TIMEOUT)

    allowlist = load_lines(allowlist_path)
    seeds = load_lines(seeds_path)

    if not seeds:
        print(f"[CẢNH BÁO] Không tìm thấy URL seed nào trong {seeds_path}.")
        return

    # Uu tien che do: neu nguoi dung truyen ro --apply thi chay apply; mac dinh la dry-run
    is_apply = args.apply

    if not is_apply:
        run_dry_run(
            seeds=seeds,
            allowlist=allowlist,
            allow_local=args.test_local,
            user_agent=args.user_agent,
            max_pages=max_pages,
            delay=delay,
        )
    else:
        asyncio.run(
            run_apply(
                seeds=seeds,
                allowlist=allowlist,
                output_dir=output_dir,
                allow_local=args.test_local,
                user_agent=args.user_agent,
                max_pages=max_pages,
                max_depth=max_depth,
                delay=delay,
                page_timeout=page_timeout,
                total_timeout=total_timeout,
            )
        )


if __name__ == "__main__":
    main()
