"""Script thống kê phân loại ý định trên file CSV câu hỏi.

Chỉ in các chỉ số tổng hợp và số thứ tự dòng bị chặn bởi đường tắt.
Tuyệt đối KHÔNG in nội dung câu hỏi ra màn hình.

Chạy:
    python -m scripts.do_phan_loai --csv <duong_dan_csv> --cot <ten_cot_cau_hoi>
"""
from __future__ import annotations
import argparse
import csv
import io
import sys
from pathlib import Path

from app.pipeline.query_transformation.intent_classifier import Intent, classify


def analyze_classification(csv_path: Path, col_name: str) -> dict:
    """Đọc file CSV và phân loại từng câu hỏi, chỉ trả về thống kê số liệu."""
    resolved_path = csv_path.resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {resolved_path}")

    total_valid = 0
    skipped_empty = 0
    counts = {
        Intent.ACADEMIC: 0,
        Intent.PERSONAL: 0,
        Intent.OUT_OF_SCOPE: 0,
    }
    blocked_csv_lines: list[int] = []

    # Mở file với utf-8-sig để xử lý BOM nếu có
    with csv_path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [k.strip() for k in (reader.fieldnames or []) if k]
        if col_name not in fieldnames:
            # Thử tìm không phân biệt hoa thường
            matched_col = None
            for fn in fieldnames:
                if fn.lower() == col_name.lower():
                    matched_col = fn
                    break
            if not matched_col:
                raise ValueError(
                    f"Cột '{col_name}' không tồn tại trong file {csv_path.name}. "
                    f"Các cột hiện có: {', '.join(fieldnames)}"
                )
            col_name = matched_col

        # Dòng 1 trong file là header, dòng dữ liệu bắt đầu từ dòng 2
        for line_num, row in enumerate(reader, start=2):
            q_text = (row.get(col_name) or "").strip()
            if not q_text:
                skipped_empty += 1
                continue

            total_valid += 1
            res_intent = classify(q_text)
            counts[res_intent] = counts.get(res_intent, 0) + 1

            if res_intent in (Intent.PERSONAL, Intent.OUT_OF_SCOPE):
                blocked_csv_lines.append(line_num)

    return {
        "csv_path": str(resolved_path),
        "csv_name": csv_path.name,
        "col_name": col_name,
        "total_valid": total_valid,
        "skipped_empty": skipped_empty,
        "academic": counts[Intent.ACADEMIC],
        "personal": counts[Intent.PERSONAL],
        "out_of_scope": counts[Intent.OUT_OF_SCOPE],
        "total_blocked": len(blocked_csv_lines),
        "blocked_csv_lines": blocked_csv_lines,
    }


def print_report(stats: dict) -> None:
    """In báo cáo số liệu phân loại ra terminal mà không in nội dung câu hỏi."""
    total = stats["total_valid"]

    def pct(val: int) -> str:
        return f"{val / total:.1%}" if total > 0 else "0.0%"

    print("\n" + "=" * 60)
    print(" BÁO CÁO THỐNG KÊ PHÂN LOẠI Ý ĐỊNH")
    print(f" File: {stats['csv_name']} | Cột: '{stats['col_name']}'")
    print("=" * 60)
    print(f" Tổng số câu hỏi hợp lệ       : {total}")
    if stats["skipped_empty"] > 0:
        print(f" Số dòng rỗng bỏ qua          : {stats['skipped_empty']}")
    print("-" * 60)
    print(f" 1. Học vụ (ACADEMIC - đi tiếp)   : {stats['academic']:<5} ({pct(stats['academic'])})")
    print(f" 2. Cá nhân (PERSONAL - chặn)     : {stats['personal']:<5} ({pct(stats['personal'])})")
    print(f" 3. Ngoài lề (OUT_OF_SCOPE - chặn): {stats['out_of_scope']:<5} ({pct(stats['out_of_scope'])})")
    print("-" * 60)
    print(f" Tổng số câu bị đường tắt chặn  : {stats['total_blocked']:<5} ({pct(stats['total_blocked'])})")
    if stats["blocked_csv_lines"]:
        lines_str = ", ".join(f"dòng {ln}" for ln in stats["blocked_csv_lines"])
        print(f" Danh sách dòng CSV bị chặn     : [{lines_str}]")
    else:
        print(" Danh sách dòng CSV bị chặn     : [Không có câu nào bị chặn]")
    print("=" * 60 + "\n")


def main(argv: list[str] | None = None) -> None:
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except (AttributeError, io.UnsupportedOperation):
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
            except Exception:
                pass

    parser = argparse.ArgumentParser(description="Đo số lượng phân loại ý định trên file CSV.")
    parser.add_argument("--csv", type=Path, required=True, help="Đường dẫn đến file CSV cần đo")
    parser.add_argument("--cot", default="cau_hoi", help="Tên cột chứa câu hỏi (mặc định: cau_hoi)")

    args = parser.parse_args(argv)
    stats = analyze_classification(args.csv, args.cot)
    print_report(stats)


if __name__ == "__main__":
    main()
