"""Công cụ dòng lệnh quản lý hàng đợi phê duyệt URL (NotebookLM-like).

Cú pháp:
  python -m scripts.manage_url_queue list
  python -m scripts.manage_url_queue import <url> [--category <cat>]
  python -m scripts.manage_url_queue approve <url_id> [--note <ghi_chu>]
  python -m scripts.manage_url_queue reject <url_id> [--reason <ly_do>]
  python -m scripts.manage_url_queue ingest [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Đảm bảo stdout UTF-8 trên Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.pipeline.importer.incremental_indexer import (
    approve_url_in_queue,
    index_approved_urls,
    list_approved_items,
    reject_url_in_queue,
)
from app.pipeline.importer.url_importer import URLImporter


def cmd_list(args):
    importer = URLImporter()
    rows = importer.load_queue()
    if not rows:
        print("Hàng đợi URL hiện đang trống.")
        return

    print("=" * 80)
    print(f"{'MÃ URL':<16} | {'TRẠNG THÁI':<15} | {'TIÊU ĐỀ':<35} | NGUỒN")
    print("=" * 80)
    for r in rows:
        title = (r['doc_title'][:32] + "...") if len(r['doc_title']) > 35 else r['doc_title']
        print(f"{r['url_id']:<16} | {r['status']:<15} | {title:<35} | {r['source_url']}")
    print("=" * 80)
    print(f"Tổng số mục: {len(rows)}")


def cmd_import(args):
    importer = URLImporter()
    print(f"Bắt đầu nhập URL: {args.url}")
    res = importer.import_single_url(args.url, category=args.category)
    if res.get("success"):
        if res.get("duplicate"):
            print(f"[TRÙNG LẶP]: {res.get('message')}")
        else:
            print(f"[THÀNH CÔNG]: Đã trích xuất và đưa vào hàng đợi với mã: {res['url_id']}")
            print(f"  Tiêu đề: {res['doc_title']}")
            print(f"  Trạng thái: {res['status']} (Đang chờ duyệt)")
            print(f"  File staging: {res['file_path']}")
            print(f"  Độ dài văn bản: {res['content_length']} ký tự")
    else:
        print(f"[THẤT BẠI]: {res.get('error')}")


def cmd_approve(args):
    ok = approve_url_in_queue(args.url_id, approver_note=args.note or "Phê duyệt bởi Admin")
    if ok:
        print(f"[ĐÃ DUYỆT]: Mục {args.url_id} đã chuyển sang trạng thái APPROVED. Sẵn sàng nạp (ingest).")
    else:
        print(f"[LỖI]: Không tìm thấy mã URL {args.url_id} trong hàng đợi.")


def cmd_reject(args):
    ok = reject_url_in_queue(args.url_id, reason=args.reason or "Từ chối bởi Admin")
    if ok:
        print(f"[ĐÃ TỪ CHỐI]: Mục {args.url_id} đã chuyển sang trạng thái REJECTED.")
    else:
        print(f"[LỖI]: Không tìm thấy mã URL {args.url_id} trong hàng đợi.")


def cmd_ingest(args):
    print(f"Bắt đầu nạp các URL có trạng thái APPROVED (chế độ dry-run={args.dry_run})...")
    res = index_approved_urls(dry_run=args.dry_run)
    if res.get("success"):
        print(f"[HOÀN TẤT]: Đã xử lý {res.get('indexed_count')} URL, tổng cộng {res.get('total_chunks', 0)} chunks.")
        for item in res.get("items", []):
            print(f"  - [{item['url_id']}] {item['doc_title']}: {item['chunks_count']} chunks")
    else:
        print(f"[LỖI INGEST]: {res.get('error')}")


def main():
    parser = argparse.ArgumentParser(description="Quản lý hàng đợi phê duyệt URL kiến thức RAG")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list
    subparsers.add_parser("list", help="Liệt kê toàn bộ URL trong hàng đợi")

    # import
    p_import = subparsers.add_parser("import", help="Thu thập 1 URL đưa vào hàng đợi")
    p_import.add_argument("url", help="Địa chỉ URL cần thu thập")
    p_import.add_argument("--category", default="tai_lieu_tong_hop", help="Phân loại tài liệu")

    # approve
    p_approve = subparsers.add_parser("approve", help="Phê duyệt một URL")
    p_approve.add_argument("url_id", help="Mã định danh URL (ví dụ: URL-20261105-ABCD12)")
    p_approve.add_argument("--note", default="", help="Ghi chú phê duyệt")

    # reject
    p_reject = subparsers.add_parser("reject", help="Từ chối một URL")
    p_reject.add_argument("url_id", help="Mã định danh URL")
    p_reject.add_argument("--reason", default="", help="Lý do từ chối")

    # ingest
    p_ingest = subparsers.add_parser("ingest", help="Nạp các URL đã APPROVED vào Qdrant và BM25")
    p_ingest.add_argument("--dry-run", action="store_true", help="Chỉ kiểm tra, không ghi DB")

    args = parser.parse_args()
    if args.command == "list":
        cmd_list(args)
    elif args.command == "import":
        cmd_import(args)
    elif args.command == "approve":
        cmd_approve(args)
    elif args.command == "reject":
        cmd_reject(args)
    elif args.command == "ingest":
        cmd_ingest(args)


if __name__ == "__main__":
    main()
