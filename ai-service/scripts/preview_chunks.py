"""Tạo bản xem trước các đoạn đã cắt (chunk preview) cho các tài liệu đọc được trong data/raw_documents.

Chạy từ thư mục ai-service:
    python -m scripts.preview_chunks
"""
import csv
import json
import io
import sys
from pathlib import Path

from app.core.config import BASE_DIR
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.pdf_loader import load_text
from app.pipeline.preprocessor.structural_chunker import (
    chunk_document, extract_doc_title, check_article_order
)


def load_registry_titles(csv_path: Path) -> dict[str, str]:
    mapping = {}
    if csv_path.exists():
        try:
            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    fname = row.get("file", "").strip()
                    title = row.get("doc_title", "").strip()
                    if fname and title:
                        mapping[fname] = title
        except Exception:
            pass
    return mapping


def main() -> None:
    # Đảm bảo in UTF-8 không lỗi font trên console Windows
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    raw_dir = BASE_DIR / "data" / "raw_documents"
    preview_dir = BASE_DIR / "data" / "chunk_preview"
    preview_dir.mkdir(parents=True, exist_ok=True)

    if not raw_dir.exists():
        print(f"Thư mục không tồn tại: {raw_dir}")
        return

    # Tải danh sách tài liệu bị loại trừ
    excl_path = BASE_DIR / "data" / "excluded_documents.json"
    excluded_files = set()
    if excl_path.exists():
        try:
            excl_data = json.loads(excl_path.read_text(encoding="utf-8"))
            excluded_files = set(sum(excl_data.values(), []))
        except Exception:
            pass

    registry_titles = load_registry_titles(BASE_DIR / "data" / "docs_registry.csv")

    all_files = sorted(raw_dir.iterdir(), key=lambda p: p.name.lower())
    print(f"Tổng số file trong {raw_dir}: {len(all_files)}")
    print(f"Số file trong danh sách loại trừ: {len(excluded_files)}")
    print("=" * 80)

    processed_count = 0
    scanned_count = 0
    skipped_other = 0
    all_warnings: list[str] = []

    for file_path in all_files:
        if file_path.name == "quy_che_mau_demo.txt":
            continue

        if file_path.name in excluded_files:
            continue

        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            try:
                raw_text = load_text(file_path)
                cleaned = clean_text(raw_text)

                doc_title = registry_titles.get(file_path.name) or extract_doc_title(cleaned, fallback=file_path.stem)
                chunks = chunk_document(cleaned, doc_name=file_path.stem, status="ACTIVE", doc_title=doc_title)

                file_warnings = check_article_order(chunks, file_path.name)
                all_warnings.extend(file_warnings)

                out_file = preview_dir / f"{file_path.stem}_preview.txt"
                with out_file.open("w", encoding="utf-8") as f:
                    f.write(f"Tài liệu: {file_path.name}\n")
                    f.write(f"Tiêu đề trích xuất: {doc_title}\n")
                    f.write(f"Tổng số ký tự gốc: {len(raw_text)} | Sau làm sạch: {len(cleaned)}\n")
                    f.write(f"Tổng số đoạn cắt: {len(chunks)}\n")
                    f.write(f"Cảnh báo thứ tự Điều: {len(file_warnings)}\n")
                    f.write("=" * 80 + "\n\n")

                    for idx, c in enumerate(chunks, 1):
                        f.write(f"--- ĐOẠN {idx}/{len(chunks)} ---\n")
                        f.write(f"Mã đoạn: {c.chunk_id}\n")
                        f.write(f"Phần văn bản: {c.phan_van_ban or '(Không)'} | ")
                        f.write(f"Chương: {c.chuong or '(Không)'} | Điều: {c.dieu or '(Không)'}\n")
                        f.write(f"Tiêu đề điều: {c.dieu_title or '(Không)'}\n")
                        f.write(f"Trạng thái: {c.status} | Phần: {c.part}\n")
                        f.write(f"Số ký tự: {len(c.text)}\n")
                        f.write(f"200 ký tự đầu:\n{c.text[:200]}\n")
                        f.write("-" * 80 + "\n\n")

                print(f"[THÀNH CÔNG] {file_path.name}: {len(chunks)} đoạn ({len(file_warnings)} cảnh báo) -> data/chunk_preview/{out_file.name}")
                processed_count += 1

            except ValueError as ve:
                print(f"[BỎ QUA - SCAN/RỖNG] {file_path.name}: {ve}")
                scanned_count += 1
            except Exception as e:
                print(f"[BỎ QUA - LỖI ĐỌC] {file_path.name}: {e}")
                scanned_count += 1

        elif suffix in (".doc", ".docx"):
            print(f"[BỎ QUA - ĐỊNH DẠNG WORD] {file_path.name} (chưa hỗ trợ trích xuất tự động)")
            skipped_other += 1
        else:
            print(f"[BỎ QUA - ĐỊNH DẠNG KHÁC] {file_path.name}")
            skipped_other += 1

    # Ghi cảnh báo thứ tự Điều ra file canh_bao_dieu.txt
    warn_file = preview_dir / "canh_bao_dieu.txt"
    with warn_file.open("w", encoding="utf-8") as f:
        f.write("=== DANH SÁCH CẢNH BÁO THỨ TỰ ĐIỀU (GIAI ĐOẠN 2) ===\n")
        f.write(f"Tổng số cảnh báo phát hiện: {len(all_warnings)}\n\n")
        if all_warnings:
            for w in all_warnings:
                f.write(f"- {w}\n")
        else:
            f.write("[OK] Không phát hiện bất thường thứ tự Điều trên toàn bộ các file đã xử lý.\n")

    print("=" * 80)
    print(f"Tổng kết:")
    print(f"- Đã xử lý và tạo preview: {processed_count} tài liệu")
    print(f"- Bỏ qua do là PDF scan / rỗng: {scanned_count} tài liệu")
    print(f"- Bỏ qua do định dạng khác (.doc/.docx): {skipped_other} tài liệu")
    print(f"- Cảnh báo thứ tự Điều: {len(all_warnings)} cảnh báo -> {warn_file.name}")
    print(f"Toàn bộ file preview được lưu tại: {preview_dir}")


if __name__ == "__main__":
    main()
