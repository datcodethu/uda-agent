"""Công cụ chẩn đoán cấu trúc phân đoạn và các mẫu đề mục của tài liệu quy chế.
Phiên 4B: Chỉ phân tích và đề xuất phương án, không thay đổi logic nạp hay dữ liệu kho.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

from app.core.config import settings
from app.pipeline.preprocessor.cleaner import clean_text
from app.pipeline.preprocessor.pdf_loader import load_text


# --- Các biểu thức chính quy nhận diện đề mục ---
RE_CHUONG_DIEU_MUC_PHAN = re.compile(
    r"^\s*(?:chương|điều|mục|phần)\b",
    re.IGNORECASE,
)
RE_SO_LA_MA = re.compile(
    r"^\s*(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI|XVII|XVIII|XIX|XX)[\.\:\-\s]",
)
RE_SO_THAP_PHAN = re.compile(
    r"^\s*\d+(?:\.\d+)*[\.\:\-\s]",
)
RE_CHU_CAI = re.compile(
    r"^\s*(?:[A-Z]\.|\b[a-z]\)|\b[A-Z]\))[\s]",
)


def normalize_nfc(text: str) -> str:
    """Chuẩn hóa chuỗi ký tự theo chuẩn Unicode NFC."""
    return unicodedata.normalize("NFC", text).strip()


def analyze_chunks_distribution(chunks: list[dict], target_doc: str | None = None) -> dict:
    """Thống kê phân bổ đoạn cắt theo từng cặp (phan_van_ban, dieu) từ danh sách chunk.
    Gắn cờ cảnh báo bất thường nếu có nhóm chiếm trên 50% tổng số đoạn của văn bản.
    """
    if target_doc:
        norm_target = normalize_nfc(target_doc).lower()
        target_stem = Path(norm_target).stem
        filtered = []
        for c in chunks:
            c_doc = normalize_nfc(str(c.get("doc_name", ""))).lower()
            c_doc_stem = Path(c_doc).stem
            if norm_target in (c_doc, c_doc_stem) or target_stem in (c_doc, c_doc_stem):
                filtered.append(c)
    else:
        filtered = chunks

    total_chunks = len(filtered)
    total_chars = sum(len(c.get("text", "")) for c in filtered)

    # Thống kê theo cặp (phan_van_ban, dieu)
    groups: dict[tuple[str, str], dict] = {}
    for c in filtered:
        phan = c.get("phan_van_ban", "(không)")
        dieu = c.get("dieu", "(không)")
        key = (phan, dieu)
        if key not in groups:
            groups[key] = {
                "phan_van_ban": phan,
                "dieu": dieu,
                "count": 0,
                "chars": 0,
                "chunk_ids": [],
            }
        groups[key]["count"] += 1
        groups[key]["chars"] += len(c.get("text", ""))
        groups[key]["chunk_ids"].append(c.get("chunk_id", ""))

    anomalies = []
    group_list = []
    for (phan, dieu), g in groups.items():
        pct = (g["count"] / total_chunks * 100) if total_chunks > 0 else 0.0
        g["pct_chunks"] = pct
        g["is_anomaly"] = pct > 50.0
        if g["is_anomaly"]:
            anomalies.append(g)
        group_list.append(g)

    # Sắp xếp nhóm theo số đoạn giảm dần
    group_list.sort(key=lambda x: x["count"], reverse=True)

    # Kiểm tra xem có trường page trong metadata không
    has_page_info = any(bool(c.get("page")) for c in filtered) if filtered else False

    return {
        "target_doc": target_doc,
        "total_chunks": total_chunks,
        "total_chars": total_chars,
        "groups": group_list,
        "anomalies": anomalies,
        "has_page_info": has_page_info,
        "chunks": filtered,
    }


def classify_heading_lines(text: str) -> dict[str, list[dict]]:
    """Quét văn bản gốc theo từng dòng và phân loại các dòng có dạng đề mục thành 5 nhóm:
    1. CHƯƠNG_ĐIỀU_MỤC_PHẦN
    2. SỐ_LA_MÃ
    3. SỐ_THẬP_PHÂN
    4. CHỮ_CÁI
    5. CHỮ_HOA_TOÀN_BỘ (< 100 ký tự)
    """
    categories: dict[str, list[dict]] = {
        "CHUONG_DIEU_MUC_PHAN": [],
        "SO_LA_MA": [],
        "SO_THAP_PHAN": [],
        "CHU_CAI": [],
        "CHU_HOA_TOAN_BO": [],
    }

    lines = text.splitlines()
    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line:
            continue

        matched_cat = None
        if RE_CHUONG_DIEU_MUC_PHAN.search(line):
            matched_cat = "CHUONG_DIEU_MUC_PHAN"
        elif RE_SO_LA_MA.search(line):
            matched_cat = "SO_LA_MA"
        elif RE_SO_THAP_PHAN.search(line):
            matched_cat = "SO_THAP_PHAN"
        elif RE_CHU_CAI.search(line):
            matched_cat = "CHU_CAI"
        else:
            # Kiểm tra dòng viết hoa toàn bộ và ngắn hơn 100 ký tự
            if len(line) < 100 and line.isupper():
                matched_cat = "CHU_HOA_TOAN_BO"

        if matched_cat:
            categories[matched_cat].append({
                "line_no": line_no,
                "prefix_80": line[:80],
            })

    return categories


def inspect_decision_boundary(cleaned_text: str) -> dict:
    """Xác định ranh giới giữa phần Quyết định ban hành (Điều 1, 2, 3) và phần hướng dẫn đính kèm."""
    lines = cleaned_text.splitlines()

    dieu_lines: list[tuple[int, str]] = []
    quyet_dinh_end_line = -1

    # Tìm vị trí các Điều và tìm điểm kết thúc Quyết định ban hành
    for idx, line in enumerate(lines, start=1):
        s = line.strip()
        if re.match(r"^Điều\s+\d+", s, re.IGNORECASE):
            dieu_lines.append((idx, s[:80]))

        # Dấu hiệu kết thúc Quyết định ban hành: nơi nhận / hiệu lực thi hành / người ký
        if re.search(r"^\s*Nơi nhận\s*:", s, re.IGNORECASE) or re.search(r"^\s*KT\.\s*HIỆU TRƯỞNG", s, re.IGNORECASE):
            quyet_dinh_end_line = idx

    # Tính độ dài phần Quyết định ban hành
    if quyet_dinh_end_line > 0:
        qd_chars = sum(len(lines[i]) + 1 for i in range(quyet_dinh_end_line))
        total_chars = len(cleaned_text)
        rem_chars = total_chars - qd_chars
    else:
        qd_chars = 0
        rem_chars = len(cleaned_text)

    return {
        "dieu_lines": dieu_lines,
        "quyet_dinh_end_line": quyet_dinh_end_line,
        "qd_chars": qd_chars,
        "rem_chars": rem_chars,
        "total_lines": len(lines),
    }


def diagnose_document(
    doc_file_name: str,
    chunks_path: Path,
    raw_dir: Path,
    output_preview_dir: Path,
) -> dict:
    """Thực hiện đầy đủ quy trình chẩn đoán cho 1 văn bản:
    1. Đọc chunks.jsonl và phân tích phân bổ.
    2. Đọc file raw_documents và nhận diện các mẫu đề mục.
    3. Ghi file preview chi tiết ra đĩa.
    4. Trả về kết quả tổng hợp (không in nội dung quy chế ra console).
    """
    target_path = raw_dir / doc_file_name
    if not target_path.exists():
        # Thử tìm file với các đuôi phổ biến
        matches = list(raw_dir.glob(f"{Path(doc_file_name).stem}.*"))
        if matches:
            target_path = matches[0]
        else:
            raise FileNotFoundError(f"Không tìm thấy file {doc_file_name} trong {raw_dir}")

    # Đọc văn bản gốc qua loader và cleaner
    raw_text = load_text(target_path)
    cleaned = clean_text(raw_text)

    # Đọc chunks.jsonl
    all_chunks = []
    if chunks_path.exists():
        with chunks_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    all_chunks.append(json.loads(line))

    # 1. Thống kê chunks
    dist = analyze_chunks_distribution(all_chunks, target_path.name)

    # 2. Phân loại đề mục
    headings = classify_heading_lines(cleaned)

    # 3. Phân tích ranh giới Quyết định
    boundary = inspect_decision_boundary(cleaned)

    # 4. Ghi file preview ra đĩa
    output_preview_dir.mkdir(parents=True, exist_ok=True)
    preview_file = output_preview_dir / f"chan_doan_{target_path.name}.txt"

    with preview_file.open("w", encoding="utf-8") as out:
        out.write(f"BÁO CÁO CHẨN ĐOÁN CẤU TRÚC VĂN BẢN: {target_path.name}\n")
        out.write("=" * 80 + "\n\n")

        out.write("I. THỐNG KÊ PHÂN ĐOẠN HIỆN TẠI (TỪ CHUNKS.JSONL)\n")
        out.write(f"- Tổng số đoạn: {dist['total_chunks']}\n")
        out.write(f"- Tổng số ký tự: {dist['total_chars']:,}\n")
        out.write(f"- Thông tin số trang (page): {'CÓ' if dist['has_page_info'] else 'KHÔNG (THIẾU)'}\n")
        out.write("\nPhân bổ theo cặp (phần văn bản, điều):\n")
        for g in dist["groups"]:
            mark = " [BẤT THƯỜNG > 50%]" if g["is_anomaly"] else ""
            out.write(
                f"  + Phần: {g['phan_van_ban']:<18} | {g['dieu']:<10} | {g['count']:>2} đoạn ({g['pct_chunks']:>5.1f}%) "
                f"| {g['chars']:>6,} ký tự{mark}\n"
            )

        out.write("\n" + "=" * 80 + "\n")
        out.write("II. DANH SÁCH DÒNG CÓ DẤU HIỆU TIÊU ĐỀ/ĐỀ MỤC TRONG VĂN BẢN GỐC\n\n")

        for cat_name, items in headings.items():
            out.write(f"--- KIỂU: {cat_name} (Tổng: {len(items)} dòng) ---\n")
            for item in items:
                out.write(f"[Dòng {item['line_no']:>4d}] {item['prefix_80']}\n")
            out.write("\n")

        out.write("=" * 80 + "\n")
        out.write("III. RANH GIỚI QUYẾT ĐỊNH BAN HÀNH\n")
        out.write(f"- Dòng kết thúc phần Quyết định ban hành: {boundary['quyet_dinh_end_line']}\n")
        out.write(f"- Dung lượng phần Quyết định: {boundary['qd_chars']:,} ký tự\n")
        out.write(f"- Dung lượng phần tài liệu đính kèm: {boundary['rem_chars']:,} ký tự\n")

    return {
        "file_name": target_path.name,
        "preview_file": preview_file,
        "dist": dist,
        "headings_count": {cat: len(items) for cat, items in headings.items()},
        "boundary": boundary,
    }


def main() -> None:
    # Cấu hình UTF-8 cho stdout trong terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Chẩn đoán cấu trúc phân đoạn và đề mục của văn bản quy chế.")
    parser.add_argument("file_name", nargs="?", default="2024_11_14_14_26_46A.pdf", help="Tên file PDF cần chẩn đoán")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    chunks_file = Path(settings.chunks_file)
    raw_dir = base_dir / "data" / "raw_documents"
    preview_dir = base_dir / "data" / "chunk_preview"

    print("=" * 80)
    print(f"BẮT ĐẦU CHẨN ĐOÁN CẤU TRÚC VĂN BẢN: {args.file_name}")
    print("=" * 80)

    res = diagnose_document(args.file_name, chunks_file, raw_dir, preview_dir)

    dist = res["dist"]
    h_counts = res["headings_count"]
    bound = res["boundary"]

    print("\n1. THỐNG KÊ PHÂN ĐOẠN HIỆN TẠI (TỪ data/chunks.jsonl):")
    print(f"   - Tổng số đoạn: {dist['total_chunks']}")
    print(f"   - Tổng số ký tự: {dist['total_chars']:,}")
    print(f"   - Thông tin số trang (page): {'CÓ' if dist['has_page_info'] else 'KHÔNG (THIẾU)'}")
    print("\n   Phân bổ nhóm (phan_van_ban, dieu):")
    for g in dist["groups"]:
        alert = " -> [CẢNH BÁO BẤT THƯỜNG > 50%]" if g["is_anomaly"] else ""
        print(f"     * ({g['phan_van_ban']}, {g['dieu']}): {g['count']} đoạn ({g['pct_chunks']:.1f}%), {g['chars']:,} ký tự{alert}")

    print("\n2. SỐ LƯỢNG DÒNG THEO TỪNG KIỂU ĐỀ MỤC TRONG VĂN BẢN GỐC:")
    for cat, count in h_counts.items():
        print(f"   - Kiểu {cat:<22}: {count:>3} dòng")

    print("\n3. RANH GIỚI QUYẾT ĐỊNH BAN HÀNH:")
    print(f"   - Dòng kết thúc phần Quyết định: dòng {bound['quyet_dinh_end_line']} (trên tổng {bound['total_lines']} dòng)")
    print(f"   - Phần Quyết định ban hành chiếm  : {bound['qd_chars']:,} ký tự")
    print(f"   - Phần tài liệu hướng dẫn còn lại: {bound['rem_chars']:,} ký tự")

    print(f"\n[XUẤT KẾT QUẢ CHI TIẾT]: Đã lưu danh sách dòng đề mục vào:")
    print(f" -> {res['preview_file']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
