"""Cổng nạp kho quy chế theo bảng đăng ký (docs_registry.csv).

Chỉ chọn nạp các file thỏa mãn đồng thời:
1. da_duyet = true (không phân biệt hoa thường)
2. loai = quy_che_truong (chỉ xét cột loai làm cổng chặn)
3. status = ACTIVE (không phân biệt hoa thường)
4. public_or_internal = public (hoặc internal nếu có cờ --allow-internal)
5. file có thật trong raw_documents (tên file hợp lệ, không chứa /, \\, .., không trùng dòng, so sánh Unicode NFC)

Chế độ mặc định: --dry-run (không gọi embedding, không ghi Qdrant, không ghi chunks.jsonl).
Chỉ nạp thật khi có cờ --apply.
"""
from __future__ import annotations
import argparse
import collections
import csv
import io
import sys
import unicodedata
from pathlib import Path

from app.core.config import BASE_DIR
from app.pipeline import index_service
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.pdf_loader import load_text
from app.pipeline.preprocessor.structural_chunker import (
    chunk_document, extract_doc_title
)

# Các cột bắt buộc trong bảng đăng ký CSV
REQUIRED_COLUMNS = ["file", "da_duyet", "loai", "status", "public_or_internal"]

# Danh sách khóa metadata được phép ghi vào chunk
ALLOWED_METADATA_KEYS = (
    "doc_id", "doc_title", "doc_number", "effective_date", "category", "applies_to"
)

# Ngưỡng phát hiện bất thường cắt sai (Phiên 4C)
ANOMALY_MIN_CHUNKS = 10
ANOMALY_RATIO_THRESHOLD = 0.50


def check_chunking_anomaly(
    chunks: list[object],
    min_chunks: int = ANOMALY_MIN_CHUNKS,
    ratio_threshold: float = ANOMALY_RATIO_THRESHOLD,
) -> tuple[bool, str, dict | None]:
    """Kiểm tra bất thường cấu trúc cắt đoạn (Phiên 4C).

    Nếu văn bản có từ min_chunks đoạn trở lên mà một cặp nhãn (phan_van_ban, dieu)
    chiếm > ratio_threshold số đoạn thì đánh dấu NGHI NGỜ CẮT SAI.
    """
    total = len(chunks)
    if total < min_chunks:
        return False, "", None

    counter: collections.Counter[tuple[str, str]] = collections.Counter()
    for c in chunks:
        pvb = getattr(c, "phan_van_ban", None) if hasattr(c, "phan_van_ban") else (c.get("phan_van_ban", "") if isinstance(c, dict) else "")
        dieu = getattr(c, "dieu", None) if hasattr(c, "dieu") else (c.get("dieu", "") if isinstance(c, dict) else "")
        counter[(pvb or "", dieu or "")] += 1

    if not counter:
        return False, "", None

    (top_pvb, top_dieu), count = counter.most_common(1)[0]
    ratio = count / total
    if ratio > ratio_threshold:
        pvb_display = top_pvb or "(chính)"
        dieu_display = top_dieu or "(không có Điều)"
        msg = (
            f"NGHI NGỜ CẮT SAI: nhóm ('{pvb_display}', '{dieu_display}') "
            f"chiếm {ratio:.1%} ({count}/{total} đoạn > {ratio_threshold:.0%})"
        )
        detail = {
            "phan_van_ban": top_pvb,
            "dieu": top_dieu,
            "count": count,
            "total": total,
            "ratio": ratio,
        }
        return True, msg, detail

    return False, "", None


def check_duplicate_chunk_ids(chunks: list[dict]) -> tuple[int, dict[str, int]]:
    """Kiểm tra các chunk_id bị trùng lặp trên toàn bộ danh sách chunks."""
    id_counts = collections.Counter(c.get("chunk_id", "") for c in chunks if c.get("chunk_id"))
    duplicates = {cid: cnt for cid, cnt in id_counts.items() if cnt > 1}
    return len(duplicates), duplicates


def print_store_status() -> dict:
    """In tình trạng kho tài liệu hiện tại:
    - Mỗi tài liệu 1 dòng: doc_name, số đoạn, status, effective_date.
    - Kiểm tra trùng lặp chunk_id (kỳ vọng 0).
    - Tổng số tài liệu và tổng số đoạn.
    Chỉ in số liệu, không in nội dung quy chế.
    """
    from app.pipeline.retrieval import chunk_store

    all_chunks = chunk_store.load_all()

    docs_summary: dict[str, dict] = {}
    for c in all_chunks:
        dn = c.get("doc_name", "")
        if not dn:
            continue
        if dn not in docs_summary:
            docs_summary[dn] = {
                "doc_name": dn,
                "chunks": 0,
                "status": c.get("status", "ACTIVE"),
                "effective_date": c.get("effective_date", "") or "(trống)",
            }
        docs_summary[dn]["chunks"] += 1
        if docs_summary[dn]["effective_date"] == "(trống)" and c.get("effective_date"):
            docs_summary[dn]["effective_date"] = c.get("effective_date")

    num_dups, dup_dict = check_duplicate_chunk_ids(all_chunks)

    print("\n" + "=" * 80)
    print(" TÌNH TRẠNG KHO VĂN BẢN QUY CHẾ (CHUNKS.JSONL / QDRANT)")
    print("=" * 80)
    print(f"Tổng số tài liệu: {len(docs_summary)} | Tổng số đoạn: {len(all_chunks)}")
    print(f"Kiểm tra trùng chunk_id: {num_dups} mã trùng (kỳ vọng: 0)")
    if num_dups > 0:
        for cid, cnt in list(dup_dict.items())[:5]:
            print(f"  - CẢNH BÁO: mã '{cid}' xuất hiện {cnt} lần!")
    print("-" * 80)
    print(f"{'Tên tài liệu (doc_name)':<35} | {'Số đoạn':<8} | {'Trạng thái':<10} | {'Ngày hiệu lực'}")
    print("-" * 80)
    if not docs_summary:
        print("  (Kho hiện đang trống)")
    else:
        for dn, info in sorted(docs_summary.items(), key=lambda x: x[0]):
            print(f"{info['doc_name']:<35} | {info['chunks']:<8} | {info['status']:<10} | {info['effective_date']}")
    print("=" * 80 + "\n")

    return {
        "total_documents": len(docs_summary),
        "total_chunks": len(all_chunks),
        "duplicate_chunks": num_dups,
        "documents": list(docs_summary.values()),
    }


def prune_unapproved_documents(
    approved_doc_names: set[str],
    registry_rows: list[dict],
    blocked_list: list[dict],
    apply: bool = False,
) -> list[dict]:
    """So khớp các tài liệu đang có trong kho với danh sách được duyệt và gỡ bỏ.

    Mặc định: dry-run (chỉ liệt kê tài liệu, số đoạn, lý do).
    Khi apply=True: gọi index_service.remove_document để gỡ và tự động dựng lại BM25.
    """
    from app.pipeline.retrieval import chunk_store

    current_docs = chunk_store.list_documents()
    to_prune: list[dict] = []

    # Lập bản đồ lý do chặn từ blocked_list
    blocked_reasons: dict[str, str] = {}
    for b in blocked_list:
        b_file = b.get("file", "")
        b_stem = Path(b_file).stem
        blocked_reasons[b_stem] = b.get("reason", "")
        blocked_reasons[b_file] = b.get("reason", "")

    # Lập bản đồ dòng từ registry_rows
    reg_map: dict[str, dict] = {}
    for r in registry_rows:
        rf = r.get("file", "").strip()
        if rf:
            reg_map[rf] = r
            reg_map[Path(rf).stem] = r

    for doc in current_docs:
        dn = doc["doc_name"]
        if dn not in approved_doc_names:
            # Xác định lý do cụ thể
            reason = ""
            if dn in blocked_reasons:
                reason = blocked_reasons[dn]
            elif dn in reg_map:
                r = reg_map[dn]
                r_reasons = []
                if r.get("da_duyet", "").lower() != "true":
                    r_reasons.append(f"da_duyet='{r.get('da_duyet')}'")
                if r.get("loai", "").lower() != "quy_che_truong":
                    r_reasons.append(f"loai='{r.get('loai')}' (chỉ chấp nhận loai='quy_che_truong')")
                if r.get("status", "").upper() != "ACTIVE":
                    r_reasons.append(f"status='{r.get('status')}'")
                reason = "; ".join(r_reasons) if r_reasons else "không đủ điều kiện phê duyệt"
            else:
                reason = "không còn trong bảng đăng ký docs_registry.csv"

            to_prune.append({
                "doc_name": dn,
                "chunks": doc.get("chunks", 0),
                "status": doc.get("status", "ACTIVE"),
                "reason": reason,
            })

    print("\n" + "=" * 80)
    mode_title = "GỠ TÀI LIỆU KHÔNG CÒN DUYỆT (--apply --prune)" if apply else "DANH SÁCH TÀI LIỆU SẼ BỊ GỠ (DRY-RUN --prune)"
    print(f" {mode_title} ({len(to_prune)} tài liệu)")
    print("=" * 80)
    if not to_prune:
        print("  (Không có tài liệu nào cần gỡ, kho tài liệu hoàn toàn khớp với danh sách phê duyệt)")
    else:
        for idx, item in enumerate(to_prune, 1):
            action_tag = "[ĐÃ GỠ]" if apply else "[SẼ GỠ]"
            print(f"  {idx}. {action_tag} {item['doc_name']}: {item['chunks']} đoạn | Lý do: {item['reason']}")
            if apply:
                res = index_service.remove_document(item["doc_name"])
                print(f"     -> Đã xóa {res.get('deleted_chunks', 0)} đoạn khỏi kho và tự động dựng lại BM25.")

        if not apply:
            print("\n  * Ghi chú: Đây là chế độ Dry-Run an toàn. Dữ liệu kho chưa bị thay đổi.")
            print("    Chạy với cả 2 cờ '--apply --prune' để tiến hành gỡ thật khỏi Qdrant và JSONL.")
    print("-" * 80 + "\n")
    return to_prune


def parse_registry(csv_path: Path) -> list[dict]:
    """Đọc bảng đăng ký tài liệu CSV (hỗ trợ UTF-8 có BOM hoặc không BOM).

    Dừng và báo lỗi rõ nếu thiếu một trong 5 cột bắt buộc:
    file, da_duyet, loai, status, public_or_internal.
    """
    if not csv_path.exists():
        return []
    rows: list[dict] = []
    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [k.strip() for k in (reader.fieldnames or []) if k]
        missing = [col for col in REQUIRED_COLUMNS if col not in fieldnames]
        if missing:
            raise ValueError(
                f"Bảng đăng ký thiếu cột bắt buộc: {', '.join(missing)}. "
                f"Yêu cầu đủ 5 cột: {', '.join(REQUIRED_COLUMNS)}."
            )
        for r in reader:
            cleaned_row = {
                (k.strip() if k else ""): (v.strip() if isinstance(v, str) else v)
                for k, v in r.items()
                if k is not None
            }
            if any(cleaned_row.values()):
                rows.append(cleaned_row)
    return rows


def filter_approved_files(
    registry_rows: list[dict],
    raw_dir: Path,
    allow_internal: bool = False
) -> tuple[list[dict], list[dict]]:
    """Lọc các tài liệu theo quy tắc phê duyệt nghiêm ngặt (default-deny).

    Trả về: (approved_list, blocked_list)
    """
    approved: list[dict] = []
    blocked: list[dict] = []

    # Đếm số lần xuất hiện của tên file (chuẩn hóa Unicode NFC) để phát hiện dòng trùng
    file_counts: collections.Counter[str] = collections.Counter()
    for r in registry_rows:
        fn = r.get("file", "").strip()
        if fn:
            fn_nfc = unicodedata.normalize("NFC", fn)
            file_counts[fn_nfc] += 1

    # Lập danh mục file thực tế trên đĩa (chuẩn hóa Unicode NFC)
    disk_files_by_nfc: dict[str, Path] = {}
    if raw_dir.exists():
        for disk_file in raw_dir.iterdir():
            if disk_file.is_file():
                disk_files_by_nfc[unicodedata.normalize("NFC", disk_file.name)] = disk_file

    registered_nfc_files: set[str] = set()

    for row in registry_rows:
        file_name = row.get("file", "").strip()
        doc_id = row.get("doc_id", "").strip()
        da_duyet = row.get("da_duyet", "").strip()
        loai = row.get("loai", "").strip()
        status = row.get("status", "").strip()
        poi = row.get("public_or_internal", "").strip()

        reasons = []

        if not file_name:
            reasons.append("thiếu tên file trong bảng đăng ký")
            target_path = None
        else:
            file_name_nfc = unicodedata.normalize("NFC", file_name)
            registered_nfc_files.add(file_name_nfc)

            # (4) Cột file chỉ là tên file: chặn nếu chứa /, \ hoặc ..
            if "/" in file_name or "\\" in file_name or ".." in file_name:
                reasons.append("tên file chứa ký tự không hợp lệ (/, \\, hoặc ..)")

            # (4) File xuất hiện ở hai dòng thì chặn cả hai dòng
            if file_counts[file_name_nfc] > 1:
                reasons.append(f"file xuất hiện {file_counts[file_name_nfc]} lần trong bảng đăng ký (dòng trùng lặp)")

            # (4) Đường dẫn chuẩn hóa phải nằm trong raw_documents
            try:
                target_path = (raw_dir / file_name).resolve()
                raw_dir_resolved = raw_dir.resolve()
                if raw_dir_resolved not in target_path.parents and target_path.parent != raw_dir_resolved:
                    reasons.append("đường dẫn file nằm ngoài thư mục raw_documents")
            except Exception:
                reasons.append("đường dẫn file không hợp lệ")
                target_path = None

        # (2) & (3) Các điều kiện cổng chặn
        if da_duyet.lower() != "true":
            reasons.append(f"da_duyet != true (giá trị: '{da_duyet}')")
        if loai.lower() != "quy_che_truong":
            reasons.append(f"loai != quy_che_truong (giá trị: '{loai}', chỉ chấp nhận loai='quy_che_truong')")
        if status.upper() != "ACTIVE":
            reasons.append(f"status != ACTIVE (giá trị: '{status}')")

        # Điều kiện thứ tư: public_or_internal = public; dòng internal bị chặn trừ khi có cờ --allow-internal
        poi_lower = poi.lower()
        if poi_lower == "internal":
            if not allow_internal:
                reasons.append("public_or_internal == internal (cần cờ --allow-internal)")
        elif poi_lower != "public":
            reasons.append(f"public_or_internal != public (giá trị: '{poi}')")

        # Đối chiếu tồn tại file trên đĩa qua NFC
        if file_name and target_path:
            file_name_nfc = unicodedata.normalize("NFC", file_name)
            if file_name_nfc in disk_files_by_nfc:
                actual_file_path = disk_files_by_nfc[file_name_nfc]
            else:
                actual_file_path = raw_dir / file_name
                if not actual_file_path.is_file():
                    reasons.append(f"file không tồn tại trong {raw_dir.name}")
        else:
            actual_file_path = None

        if not reasons and actual_file_path and actual_file_path.is_file():
            category_val = row.get("category", "").strip() or loai
            applies_to_val = row.get("applies_to", "").strip() or "ALL"
            approved.append({
                "file": file_name,
                "file_path": actual_file_path,
                "doc_id": doc_id,
                "doc_title": row.get("doc_title", "").strip(),
                "doc_number": row.get("doc_number", "").strip(),
                "effective_date": row.get("effective_date", "").strip(),
                "category": category_val,
                "applies_to": applies_to_val,
                "public_or_internal": poi,
                "row": row,
            })
        else:
            display_name = file_name or f"(bản ghi doc_id={doc_id or 'trống'})"
            blocked.append({
                "file": display_name,
                "reason": "; ".join(reasons),
                "row": row,
            })

    # Kiểm tra các file trên đĩa nhưng không có dòng trong bảng đăng ký
    if raw_dir.exists():
        for disk_nfc, disk_path in sorted(disk_files_by_nfc.items(), key=lambda p: p[0].lower()):
            if disk_path.name == "quy_che_mau_demo.txt":
                continue  # Bỏ qua file demo test
            if disk_nfc not in registered_nfc_files:
                blocked.append({
                    "file": disk_path.name,
                    "reason": "không có trong bảng đăng ký docs_registry.csv",
                    "row": None,
                })

    return approved, blocked


def run_ingest(
    registry_path: Path,
    raw_dir: Path,
    apply: bool = False,
    allow_internal: bool = False,
    prune: bool = False,
    status: bool = False,
    allow_anomaly: bool = False,
) -> dict:
    """Thực thi kiểm duyệt hoặc nạp tài liệu. Mặc định là dry-run (apply=False)."""
    if not registry_path.exists():
        print(f"CẢNH BÁO: Bảng đăng ký không tồn tại: {registry_path}")
        return {"approved": 0, "blocked": 0, "status": "missing_registry"}

    try:
        rows = parse_registry(registry_path)
    except ValueError as e:
        print(f"LỖI: {e}")
        return {"approved": 0, "blocked": 0, "status": "invalid_registry", "error": str(e)}

    approved_candidates, blocked = filter_approved_files(rows, raw_dir, allow_internal=allow_internal)

    mode_name = "NẠP THẬT (--apply)" if apply else "KIỂM DUYỆT (DRY-RUN - MẶC ĐỊNH)"
    print("=" * 80)
    print(f" CỔNG NẠP KHO QUY CHẾ ĐẠI HỌC ĐÔNG Á: {mode_name}")
    print(f" Bảng đăng ký: {registry_path}")
    print(f" Thư mục file gốc: {raw_dir}")
    if allow_internal:
        print(" Chế độ: --allow-internal (cho phép tài liệu nội bộ)")
    if allow_anomaly:
        print(" Chế độ: --allow-anomaly (cho phép nạp tài liệu bị nghi ngờ cắt sai)")
    if prune:
        print(" Tùy chọn: --prune (kiểm tra và gỡ tài liệu không còn được phê duyệt)")
    if status:
        print(" Tùy chọn: --status (in bảng tổng hợp tình trạng kho)")
    print("=" * 80)

    # 1. Xử lý các file được duyệt
    successfully_approved: list[dict] = []
    total_chunks = 0
    total_chars = 0

    print(f"\n[DANH SÁCH FILE ĐƯỢC PHÊ DUYỆT ({len(approved_candidates)} file)]:")
    for idx, item in enumerate(approved_candidates, 1):
        fpath = item["file_path"]
        # (5) Lỗi đọc một file không làm dừng cả lượt, ghi vào danh sách bị chặn kèm lý do
        try:
            raw_text = load_text(fpath)
            cleaned = clean_text(raw_text)
            doc_title = item["doc_title"] or extract_doc_title(cleaned, fallback=fpath.stem)
            chunks = chunk_document(
                cleaned,
                doc_name=fpath.stem,
                status="ACTIVE",
                doc_title=doc_title
            )
            char_count = sum(len(c.text if hasattr(c, "text") else c.get("text", "")) for c in chunks)

            # (Phiên 4C) Kiểm tra bất thường cấu trúc cắt đoạn (>50% một nhãn trên văn bản >= 10 đoạn)
            is_anomaly, anomaly_msg, anomaly_detail = check_chunking_anomaly(chunks)
            if is_anomaly:
                if not allow_anomaly:
                    print(f"  {idx}. [CHẶN - NGHI NGỜ CẮT SAI] {item['file']}:\n     - {anomaly_msg}")
                    blocked.append({
                        "file": item["file"],
                        "reason": anomaly_msg,
                        "row": item.get("row"),
                        "anomaly_detail": anomaly_detail,
                    })
                    continue
                else:
                    print(f"  {idx}. [CẢNH BÁO BẤT THƯỜNG (--allow-anomaly)] {item['file']}:\n     - {anomaly_msg}")

            total_chunks += len(chunks)
            total_chars += char_count

            if apply:
                meta = {
                    "doc_id": item["doc_id"],
                    "doc_title": doc_title,
                    "doc_number": item["doc_number"],
                    "effective_date": item["effective_date"],
                    "category": item["category"],
                    "applies_to": item["applies_to"],
                }
                res = index_service.index_document(
                    doc_name=fpath.stem,
                    text=raw_text,
                    status="ACTIVE",
                    meta=meta,
                    doc_title=doc_title
                )
                print(f"  {idx}. [ĐÃ NẠP] {item['file']}: doc_title='{doc_title}', {res['chunks']} đoạn")
            else:
                # (6) Dry-run chỉ in tên file và số liệu, không in nội dung quy chế
                print(
                    f"  {idx}. [SẼ NẠP] {item['file']}:\n"
                    f"     - Tiêu đề: {doc_title}\n"
                    f"     - Số đoạn cắt: {len(chunks)} đoạn | Tổng ký tự: {char_count:,} ký tự\n"
                    f"     - Metadata: doc_id={item['doc_id']}, số hiệu={item['doc_number'] or '(trống)'}, "
                    f"ngày hiệu lực={item['effective_date'] or '(trống)'}, đối tượng={item['applies_to']}"
                )
            successfully_approved.append(item)
        except Exception as e:
            print(f"  {idx}. [LỖI ĐỌC] {item['file']}: {e}")
            blocked.append({
                "file": item["file"],
                "reason": f"lỗi đọc/xử lý file: {e}",
                "row": item.get("row")
            })

    # 2. Danh sách file bị chặn
    print(f"\n[DANH SÁCH FILE BỊ CHẶN ({len(blocked)} file)]:")
    if not blocked:
        print("  (Không có file nào bị chặn)")
    else:
        for idx, item in enumerate(blocked, 1):
            print(f"  {idx}. [CHẶN] {item['file']}: {item['reason']}")

    # 3. Gỡ tài liệu không còn được duyệt (nếu có cờ --prune)
    pruned_docs: list[dict] = []
    if prune:
        approved_doc_names = {Path(it["file"]).stem for it in successfully_approved}
        pruned_docs = prune_unapproved_documents(
            approved_doc_names=approved_doc_names,
            registry_rows=rows,
            blocked_list=blocked,
            apply=apply,
        )

    # 4. Tình trạng kho (nếu có cờ --status)
    store_status = None
    if status:
        store_status = print_store_status()

    # 5. Tổng kết
    print("\n" + "-" * 80)
    if apply:
        prune_msg = f", đã gỡ {len(pruned_docs)} file" if prune else ""
        print(f"KẾT QUẢ: Đã nạp thành công {len(successfully_approved)} file ({total_chunks} đoạn){prune_msg}. Bị chặn: {len(blocked)} file.")
    else:
        prune_msg = f", dự kiến gỡ {len(pruned_docs)} file" if prune else ""
        print(
            f"KẾT QUẢ DRY-RUN: Dự kiến nạp {len(successfully_approved)} file ({total_chunks} đoạn, {total_chars:,} ký tự){prune_msg}. "
            f"Bị chặn: {len(blocked)} file.\n"
            f"(Chế độ Dry-Run an toàn: Chưa gọi API embedding, chưa ghi Qdrant, chưa ghi chunks.jsonl.\n"
            f" Thêm cờ --apply để tiến hành nạp/gỡ thật vào kho)."
        )
    print("=" * 80 + "\n")

    return {
        "approved": len(successfully_approved),
        "blocked": len(blocked),
        "total_chunks": total_chunks,
        "total_chars": total_chars,
        "pruned": len(pruned_docs),
        "pruned_docs": pruned_docs,
        "store_status": store_status,
        "mode": "apply" if apply else "dry-run",
    }


def main(argv: list[str] | None = None) -> None:
    # (6) Đặt sys.stdout.reconfigure chỉ trong main()
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, io.UnsupportedOperation):
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(
        description="Cổng nạp kho quy chế Đại học Đông Á theo bảng đăng ký docs_registry.csv."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Chế độ kiểm duyệt xem trước (mặc định), không ghi dữ liệu, không gọi API."
    )
    group.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Chế độ nạp thật vào kho vector và BM25."
    )
    parser.add_argument(
        "--allow-internal",
        action="store_true",
        default=False,
        help="Cho phép nạp tài liệu nội bộ (public_or_internal = internal)."
    )
    parser.add_argument(
        "--prune",
        action="store_true",
        default=False,
        help="So sánh với kho và gỡ các tài liệu không còn được phê duyệt (mặc định dry-run; chỉ gỡ thật khi có cả --apply)."
    )
    parser.add_argument(
        "--status",
        action="store_true",
        default=False,
        help="In bảng tình trạng kho tài liệu hiện tại (doc_name, số đoạn, status, ngày hiệu lực, trùng lặp chunk_id)."
    )
    parser.add_argument(
        "--allow-anomaly",
        action="store_true",
        default=False,
        help="Cho phép nạp tài liệu bị nghi ngờ cắt sai (>50% số đoạn thuộc một cặp nhãn Điều)."
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=BASE_DIR / "data" / "docs_registry.csv",
        help="Đường dẫn file docs_registry.csv (mặc định: data/docs_registry.csv)"
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=BASE_DIR / "data" / "raw_documents",
        help="Đường dẫn thư mục raw_documents (mặc định: data/raw_documents)"
    )

    args = parser.parse_args(argv)
    apply_mode = bool(args.apply)
    run_ingest(
        args.registry,
        args.raw_dir,
        apply=apply_mode,
        allow_internal=bool(args.allow_internal),
        prune=bool(args.prune),
        status=bool(args.status),
        allow_anomaly=bool(args.allow_anomaly),
    )


if __name__ == "__main__":
    main()
