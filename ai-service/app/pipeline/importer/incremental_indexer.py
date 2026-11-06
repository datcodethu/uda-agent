"""Bộ nạp gia tăng (Incremental Indexer) cho các URL và tài liệu đã được phê duyệt.

Nguyên tắc:
1. Chỉ nạp các tài liệu có trạng thái APPROVED trong url_approval_queue.csv.
2. Trích xuất metadata: source_url, doc_title, crawled_at, sha256.
3. Chia đoạn có cấu trúc bằng structural_chunker (giữ bảng, tiêu đề, danh sách).
4. Đồng bộ ghi vào Qdrant và BM25 thông qua index_service.
5. Cập nhật trạng thái thành INDEXED trong hàng đợi.
6. Hỗ trợ Rollback an toàn nếu xảy ra lỗi trong quá trình nhúng vector.
"""
from __future__ import annotations

import csv
import datetime
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import BASE_DIR, settings
from app.pipeline import index_service
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.structural_chunker import chunk_document

logger = logging.getLogger("incremental_indexer")


def get_queue_path(base_dir: Optional[Path] = None) -> Path:
    b = base_dir or BASE_DIR
    return b / "data" / "url_approval_queue.csv"


def list_approved_items(base_dir: Optional[Path] = None) -> List[Dict[str, str]]:
    """Liệt kê tất cả các mục có trạng thái APPROVED đang chờ nạp."""
    q_path = get_queue_path(base_dir)
    if not q_path.exists():
        return []
    with open(q_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [r for r in reader if r.get("status") == "APPROVED"]


def approve_url_in_queue(url_id: str, approver_note: str = "", base_dir: Optional[Path] = None) -> bool:
    """Phê duyệt một URL trong hàng đợi (chuyển PENDING_REVIEW -> APPROVED)."""
    q_path = get_queue_path(base_dir)
    if not q_path.exists():
        return False

    with open(q_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    updated = False
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for r in rows:
        if r.get("url_id") == url_id:
            r["status"] = "APPROVED"
            r["approved_at"] = now_iso
            if approver_note:
                r["notes"] = f"{r.get('notes', '')} | Phê duyệt: {approver_note}".strip(" |")
            updated = True
            break

    if updated:
        fieldnames = list(rows[0].keys())
        with open(q_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
    return updated


def reject_url_in_queue(url_id: str, reason: str = "", base_dir: Optional[Path] = None) -> bool:
    """Từ chối một URL trong hàng đợi (chuyển PENDING_REVIEW -> REJECTED)."""
    q_path = get_queue_path(base_dir)
    if not q_path.exists():
        return False

    with open(q_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    updated = False
    for r in rows:
        if r.get("url_id") == url_id:
            r["status"] = "REJECTED"
            if reason:
                r["notes"] = f"{r.get('notes', '')} | Lý do từ chối: {reason}".strip(" |")
            updated = True
            break

    if updated:
        fieldnames = list(rows[0].keys())
        with open(q_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
    return updated


def index_approved_urls(
    base_dir: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Thực hiện Ingest các URL đã APPROVED:
    - Đọc file Markdown từ staging.
    - Cắt đoạn cấu trúc, gắn metadata source_url, doc_title.
    - Nạp vào Qdrant và dựng lại BM25 thông qua index_service.index_document.
    - Cập nhật trạng thái thành INDEXED trong url_approval_queue.csv.
    """
    b = base_dir or BASE_DIR
    q_path = get_queue_path(b)
    if not q_path.exists():
        return {"success": True, "indexed_count": 0, "items": []}

    with open(q_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    approved_rows = [r for r in rows if r.get("status") in ("APPROVED", "INDEX_ERROR")]
    if not approved_rows:
        return {"success": True, "indexed_count": 0, "message": "Không có URL nào đang ở trạng thái APPROVED để nạp"}

    indexed_items: List[Dict[str, Any]] = []

    if dry_run:
        # Chế độ kiểm tra dry-run không ghi Qdrant
        for r in approved_rows:
            url_id = r["url_id"]
            doc_title = r["doc_title"]
            sha256 = r["sha256"]
            file_rel = r.get("file_path", "")
            file_abs = b / file_rel if not Path(file_rel).is_absolute() else Path(file_rel)
            if not file_abs.exists():
                continue
            raw_text = file_abs.read_text(encoding="utf-8")
            clean_t = clean_text(raw_text)
            chunks = chunk_document(
                text=clean_t,
                doc_name=f"web_{sha256[:10]}",
                doc_title=doc_title,
            )
            indexed_items.append({
                "url_id": url_id,
                "source_url": r["source_url"],
                "doc_title": doc_title,
                "chunks_count": len(chunks),
            })
        return {
            "success": True,
            "dry_run": True,
            "indexed_count": len(indexed_items),
            "total_chunks": sum(it["chunks_count"] for it in indexed_items),
            "items": indexed_items,
        }

    # Thực hiện nạp thật từng tài liệu
    try:
        for r in approved_rows:
            url_id = r["url_id"]
            source_url = r["source_url"]
            doc_title = r["doc_title"]
            sha256 = r["sha256"]
            doc_name = f"web_{sha256[:10]}"
            file_rel = r.get("file_path", "")
            file_abs = b / file_rel if not Path(file_rel).is_absolute() else Path(file_rel)

            if not file_abs.exists():
                logger.error(f"Không tìm thấy file staging {file_abs} cho URL {url_id}")
                r["status"] = "ERROR"
                r["notes"] = f"{r.get('notes', '')} | Lỗi: Không tìm thấy file staging".strip(" |")
                continue

            raw_text = file_abs.read_text(encoding="utf-8")
            meta = {
                "doc_title": doc_title,
                "category": r.get("category", "tai_lieu_tong_hop"),
                "source_url": source_url,
                "crawled_at": r.get("discovered_at", ""),
                "content_type": "web_page",
            }

            # Nạp tài liệu qua index_service
            res_idx = index_service.index_document(
                doc_name=doc_name,
                text=raw_text,
                status="ACTIVE",
                meta=meta,
                doc_title=doc_title,
            )

            indexed_items.append({
                "url_id": url_id,
                "source_url": source_url,
                "doc_title": doc_title,
                "chunks_count": res_idx["chunks"],
            })
            r["status"] = "INDEXED"
            r["notes"] = f"{r.get('notes', '')} | Đã nạp {res_idx['chunks']} chunks vào Qdrant & BM25".strip(" |")

        # Lưu lại trạng thái INDEXED vào CSV
        fieldnames = list(rows[0].keys())
        with open(q_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

        return {
            "success": True,
            "dry_run": False,
            "indexed_count": len(indexed_items),
            "total_chunks": sum(it["chunks_count"] for it in indexed_items),
            "items": indexed_items,
        }
    except Exception as e:
        logger.error(f"Lỗi khi nạp chunks vào Qdrant: {e}", exc_info=True)
        # Rollback: Đánh dấu trạng thái lỗi
        for r in approved_rows:
            if r["status"] != "INDEXED":
                r["status"] = "INDEX_ERROR"
                r["notes"] = f"{r.get('notes', '')} | Lỗi Ingest: {e}".strip(" |")
        fieldnames = list(rows[0].keys())
        with open(q_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        return {
            "success": False,
            "error": f"INGEST_FAILED: {e}",
            "indexed_count": 0,
        }
