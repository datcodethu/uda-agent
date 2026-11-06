"""Pipeline tái tạo Kho tri thức v2 (donga_kb_v2):
1. Kiểm toán và xác minh 21 URL seeds.
2. Thu thập nội dung, bóc tách Markdown sạch, bảo toàn bảng biểu/tiêu đề/số liệu.
3. Tạo source_manifest.csv, crawl_results.csv, crawl_attachment_links.csv.
"""
from __future__ import annotations
import csv
import hashlib
import json
import logging
import os
import re
import socket
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rebuild_v2")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.pipeline.importer.url_importer import (
    clean_html_to_markdown,
    is_safe_ip,
    is_safe_url,
    DEFAULT_USER_AGENT,
)

ALLOWLIST_V2 = ["donga.edu.vn", "uda.edu.vn", "baodanang.vn"]
SEEDS_FILE = BASE_DIR / "crawler" / "seeds.txt"
STAGING_V2_DIR = BASE_DIR / "data" / "staging_v2"
EVAL_DIR = BASE_DIR.parent / "evaluation" / "kb_rebuild_v2"


def load_seeds() -> list[str]:
    """Đọc và chuẩn hóa danh sách URLs từ seeds.txt."""
    if not SEEDS_FILE.exists():
        raise FileNotFoundError(f"Không tìm thấy tệp seeds: {SEEDS_FILE}")
    with SEEDS_FILE.open("r", encoding="utf-8") as f:
        content = f.read()
    # seeds.txt có thể phân tách bằng khoảng trắng hoặc xuống dòng
    raw_urls = [u.strip() for u in content.split() if u.strip()]
    # Khử trùng lặp giữ nguyên thứ tự
    seen = set()
    urls = []
    for u in raw_urls:
        if u not in seen:
            seen.add(u)
            urls.append(u)
    return urls


def determine_content_type(url: str, html_content: str = "") -> str:
    """Xác định loại nội dung của trang."""
    u = url.lower()
    if "thuvien" in u:
        return "huong_dan_thu_vien"
    if "do-gui-xe" in u or "the-xe" in u:
        return "quy_dinh_gui_xe"
    if "chuan-dau-ra" in u or "ngoai-ngu" in u:
        return "chuan_dau_ra_ngoai_ngu"
    if "canvas" in u:
        return "huong_dan_hoc_online"
    if "dang-ky-hoc-lai" in u:
        return "huong_dan_dang_ky_hoc_phan"
    if "noi-quy-hoc-duong" in u or "quy-dinh-van-hoa" in u:
        return "noi_quy_van_hoa"
    if "quy-che-dao-tao" in u:
        return "quy_che_dao_tao"
    if "hoc-ky-he" in u or "nghi-he" in u:
        return "ke_hoach_hoc_tap"
    if "thong-tin-hoc-vu" in u or "lien-he" in u or "tai-lieu" in u:
        return "thong_tin_hoc_vu_lien_he"
    if "nghien-cuu-khoa-hoc" in u:
        return "hoat_dong_nckh"
    return "trang_tin_tong_hop"


def inspect_and_crawl_seeds() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Thu thập, làm sạch và ghi nhận metadata cho toàn bộ 21 URLs."""
    urls = load_seeds()
    STAGING_V2_DIR.mkdir(parents=True, exist_ok=True)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    crawl_results = []
    attachment_links = []

    logger.info(f"Bắt đầu xử lý {len(urls)} URLs từ {SEEDS_FILE}...")

    for idx, url in enumerate(urls, 1):
        source_id = f"SRC-V2-{idx:03d}"
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc

        logger.info(f"[{idx}/{len(urls)}] Đang kiểm tra URL: {url}")

        # 1. Kiểm tra an toàn bảo mật
        safe, reason = is_safe_url(url, allowlist=ALLOWLIST_V2)
        if not safe:
            logger.warning(f"URL không an toàn hoặc vi phạm allowlist: {url} (Lý do: {reason})")
            manifest_rows.append({
                "source_id": source_id,
                "original_url": url,
                "domain": domain,
                "content_type": "UNKNOWN",
                "title": "BỊ TỪ CHỐI",
                "crawled_at": datetime.now(timezone.utc).isoformat(),
                "issued_date": "",
                "effective_date": "",
                "content_hash": "",
                "status": "BLOCKED_SECURITY",
                "access_rights": "DENIED",
                "notes": f"Lỗi an toàn: {reason}",
            })
            crawl_results.append({
                "source_id": source_id,
                "url": url,
                "status": "BLOCKED",
                "chars_length": 0,
                "file_path": "",
                "error": reason,
            })
            continue

        # 2. Tải trang web an toàn
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": DEFAULT_USER_AGENT},
            )
            # Giới hạn timeout 15 giây
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                final_url = resp.geturl()
                # Kiểm tra an toàn sau chuyển hướng (redirect)
                final_safe, final_reason = is_safe_url(final_url, allowlist=ALLOWLIST_V2)
                if not final_safe:
                    raise ValueError(f"Chuyển hướng đến URL không an toàn: {final_url} ({final_reason})")

                raw_bytes = resp.read()
                # Thử giải mã utf-8
                try:
                    html_text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    html_text = raw_bytes.decode("latin-1", errors="ignore")

        except Exception as e:
            logger.error(f"Lỗi khi tải URL {url}: {e}")
            manifest_rows.append({
                "source_id": source_id,
                "original_url": url,
                "domain": domain,
                "content_type": determine_content_type(url),
                "title": "LỖI TẢI TRANG",
                "crawled_at": datetime.now(timezone.utc).isoformat(),
                "issued_date": "",
                "effective_date": "",
                "content_hash": "",
                "status": "FETCH_FAILED",
                "access_rights": "PUBLIC",
                "notes": f"Lỗi mạng: {str(e)[:100]}",
            })
            crawl_results.append({
                "source_id": source_id,
                "url": url,
                "status": "FAILED",
                "chars_length": 0,
                "file_path": "",
                "error": str(e),
            })
            continue

        # 3. Bóc tách Markdown sạch và liên kết đính kèm
        title, md_content, raw_attachments = clean_html_to_markdown(html_text, base_url=url)
        content_hash = hashlib.sha256(md_content.encode("utf-8")).hexdigest()
        c_type = determine_content_type(url, html_text)

        # Lưu liên kết tệp đính kèm
        for att_url in raw_attachments:
            ext = os.path.splitext(urllib.parse.urlparse(att_url).path.lower())[1]
            attachment_links.append({
                "source_id": source_id,
                "page_url": url,
                "attachment_url": att_url,
                "extension": ext,
            })

        # 4. Lưu tệp Staging Markdown
        staging_filename = f"{source_id}_{content_hash[:12]}.md"
        staging_path = STAGING_V2_DIR / staging_filename

        # Header YAML / Metadata đầu tệp
        file_content = (
            f"---\n"
            f"source_id: {source_id}\n"
            f"url: {url}\n"
            f"title: {title}\n"
            f"domain: {domain}\n"
            f"content_type: {c_type}\n"
            f"crawled_at: {datetime.now(timezone.utc).isoformat()}\n"
            f"sha256: {content_hash}\n"
            f"---\n\n"
            f"# {title}\n\n"
            f"{md_content}\n"
        )
        with staging_path.open("w", encoding="utf-8") as f:
            f.write(file_content)

        logger.info(f"Đã lưu staging: {staging_filename} ({len(md_content)} ký tự, {len(raw_attachments)} tệp đính kèm)")

        manifest_rows.append({
            "source_id": source_id,
            "original_url": url,
            "domain": domain,
            "content_type": c_type,
            "title": title,
            "crawled_at": datetime.now(timezone.utc).isoformat(),
            "issued_date": "",
            "effective_date": "",
            "content_hash": content_hash,
            "status": "EXTRACTED_STAGING",
            "access_rights": "PUBLIC",
            "notes": f"Trích xuất thành công {len(md_content)} ký tự, {len(raw_attachments)} tệp đính kèm.",
        })

        crawl_results.append({
            "source_id": source_id,
            "url": url,
            "status": "SUCCESS",
            "chars_length": len(md_content),
            "file_path": str(staging_path.relative_to(BASE_DIR)),
            "error": "",
        })

        # Nghỉ nhẹ giữa các request để không làm nghẽn server trường
        time.sleep(0.5)

    # 5. Xuất source_manifest.csv
    manifest_csv = EVAL_DIR / "source_manifest.csv"
    manifest_fields = [
        "source_id", "original_url", "domain", "content_type", "title",
        "crawled_at", "issued_date", "effective_date", "content_hash",
        "status", "access_rights", "notes"
    ]
    with manifest_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        writer.writerows(manifest_rows)

    # 6. Xuất crawl_results.csv
    crawl_csv = EVAL_DIR / "crawl_results.csv"
    with crawl_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "url", "status", "chars_length", "file_path", "error"])
        writer.writeheader()
        writer.writerows(crawl_results)

    # 7. Xuất crawl_attachment_links.csv
    att_csv = EVAL_DIR / "crawl_attachment_links.csv"
    with att_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["source_id", "page_url", "attachment_url", "extension"])
        writer.writeheader()
        writer.writerows(attachment_links)

    logger.info(f"Hoàn tất thu thập: {len(manifest_rows)} URLs đã xử lý.")
    logger.info(f"Đã xuất: {manifest_csv}")
    logger.info(f"Đã xuất: {crawl_csv}")
    logger.info(f"Đã xuất: {att_csv}")

    return manifest_rows, crawl_results, attachment_links


if __name__ == "__main__":
    inspect_and_crawl_seeds()
