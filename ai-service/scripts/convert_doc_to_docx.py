"""Chuyển đổi an toàn .doc sang .docx bằng Microsoft Word COM (DispatchEx).

Chạy từ thư mục ai-service:
    Thử nghiệm 1-2 file:  python -m scripts.convert_doc_to_docx --sample
    Chạy toàn bộ 19 file: python -m scripts.convert_doc_to_docx
"""
import sys
import io
import csv
import argparse
from pathlib import Path

# Đảm bảo in UTF-8 không lỗi font trên console Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from docx import Document
from app.core.config import BASE_DIR
from app.pipeline.preprocessor.docx_loader import load_docx

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"
WD_FORMAT_XML_DOCUMENT = 16  # Định dạng .docx trong Word COM


def check_environment() -> bool:
    """Kiểm tra môi trường hệ thống trước khi chạy COM."""
    if sys.platform != "win32":
        print("=" * 80)
        print("[THÔNG BÁO NỀN TẢNG]")
        print("Script convert_doc_to_docx.py chỉ chạy trên hệ điều hành Windows vì cần Microsoft Word COM.")
        print("Hệ thống chính (Loader, Chunker, Retriever, API) trên Linux/Docker hoàn toàn KHÔNG cần")
        print("chạy script này, vì đã đọc trực tiếp các tệp .docx trong thư mục 'data/doc_da_chuyen/'.")
        print("=" * 80)
        return False
    return True


def inspect_docx_metrics(docx_path: Path) -> tuple[int, int, int]:
    """Đếm số bảng, số hộp văn bản (txbxContent), và số ảnh/drawing trong file .docx."""
    try:
        doc = Document(str(docx_path))
        table_count = len(doc.tables)
        txbx_count = len(doc.element.findall(f".//{{{W_NS}}}txbxContent"))
        drawing_count = (
            len(doc.element.findall(f".//{{{W_NS}}}drawing"))
            + len(doc.element.findall(f".//{{{W_NS}}}pict"))
            + len(doc.element.findall(f".//{{{V_NS}}}shape"))
        )
        return table_count, txbx_count, drawing_count
    except Exception as e:
        print(f"Lỗi khi đọc số liệu {docx_path.name}: {e}")
        return 0, 0, 0


def classify_document(text: str) -> str:
    """Gợi ý phân loại sơ bộ tài liệu dựa trên từ khóa trong nội dung."""
    t = text.lower()
    if any(k in t for k in ["luật số", "nghị định", "thông tư", "quốc hội", "công báo"]):
        return "nghi_ngo_phap_luat"
    if any(k in t for k in [
        "đơn xin", "đơn đề nghị", "giấy xác nhận", "biên bản", "bảng tổng hợp",
        "hướng dẫn quy trình", "kính gửi:", "kính gửi :", "đề nghị cấp"
    ]):
        return "mau_don"
    if any(k in t for k in ["quy chế", "quy định", "quyết định", "điều 1", "điều 2", "chương i"]):
        return "quy_che"
    return "khac"


def convert_docs(sample_mode: bool = False) -> list[dict]:
    if not check_environment():
        return []

    try:
        import win32com.client
    except ImportError:
        print("LỖI: Chưa cài đặt thư viện 'pywin32'. Hãy chạy: pip install pywin32")
        return []

    raw_dir = (BASE_DIR / "data" / "raw_documents").resolve()
    out_dir = (BASE_DIR / "data" / "doc_da_chuyen").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_file = BASE_DIR / "data" / "ket_qua_chuyen_doi.csv"

    doc_files = sorted(raw_dir.glob("*.doc"))
    if not doc_files:
        print(f"Không tìm thấy file .doc nào trong {raw_dir}")
        return []

    print(f"Tổng số file .doc tìm thấy: {len(doc_files)}")
    print(f"Thư mục lưu .docx đã chuyển: {out_dir}")

    # Chế độ --sample: chọn 1 file có bảng và 1 file không có bảng
    selected_files = []
    if sample_mode:
        sample_with_table = None
        sample_no_table = None
        for f in doc_files:
            if f.name == "2021_11_11_9_15_271.doc":
                sample_with_table = f
            elif f.name == "2021_11_6_16_22_31g.doc":
                sample_no_table = f
        
        if sample_with_table:
            selected_files.append(sample_with_table)
        if sample_no_table:
            selected_files.append(sample_no_table)
        if not selected_files:
            selected_files = doc_files[:2]
        print(f"\n[CHẾ ĐỘ CHẠY THỬ --sample] Sẽ thử nghiệm {len(selected_files)} file:")
        for sf in selected_files:
            print(f" - {sf.name}")
    else:
        selected_files = doc_files

    results = []

    # Khởi tạo Word COM độc lập qua DispatchEx (không đụng chạm tài liệu đang mở của người dùng)
    print("\nKhởi động Microsoft Word qua COM (DispatchEx - phiên riêng biệt)...")
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False
    except Exception as e:
        print("=" * 80)
        print("[LỖI KHỞI TẠO WORD COM]")
        print(f"Không thể khởi động Microsoft Word: {e}")
        print("Vui lòng đảm bảo máy tính đã cài đặt ứng dụng Microsoft Word (bản 2016 trở lên).")
        print("=" * 80)
        return []

    try:
        for idx, src_path in enumerate(selected_files, 1):
            dest_name = f"{src_path.stem}.docx"
            dest_path = out_dir / dest_name
            record = {
                "file_goc": src_path.name,
                "file_dich": dest_name,
                "trang_thai": "loi_doc_file",
                "so_ky_tu": 0,
                "so_bang_goc": 0,
                "so_bang_docx": 0,
                "so_hop_van_ban": 0,
                "so_anh_drawing": 0,
                "goi_y_loai": "khac",
                "dong_dau": "",
                "ghi_chu": "",
            }

            print(f"\n[{idx}/{len(selected_files)}] Đang xử lý: {src_path.name}...")
            try:
                # 1) Mở file .doc ở chế độ chỉ đọc, không sửa hay xóa file gốc
                doc_com = word.Documents.Open(
                    str(src_path),
                    ReadOnly=True,
                    ConfirmConversions=False,
                    AddToRecentFiles=False,
                )
                orig_tables = int(doc_com.Tables.Count)
                record["so_bang_goc"] = orig_tables

                # 2) Lưu sang định dạng .docx (wdFormatXMLDocument = 16)
                doc_com.SaveAs2(str(dest_path), FileFormat=WD_FORMAT_XML_DOCUMENT)
                doc_com.Close(False)

                # 3) Đọc và đo số liệu từ file .docx vừa sinh ra bằng python-docx
                docx_tables, txbx_cnt, draw_cnt = inspect_docx_metrics(dest_path)
                record["so_bang_docx"] = docx_tables
                record["so_hop_van_ban"] = txbx_cnt
                record["so_anh_drawing"] = draw_cnt

                # 4) Trích xuất text tuần tự bằng docx_loader
                text = load_docx(dest_path)
                so_ky_tu = len(text)
                record["so_ky_tu"] = so_ky_tu

                # 2-3 dòng đầu để hỗ trợ phân loại
                lines_preview = [ln.strip() for ln in text.split("\n") if ln.strip()][:3]
                record["dong_dau"] = " // ".join(lines_preview)
                record["goi_y_loai"] = classify_document(text)

                # 5) Phân loại trạng thái nghiêm ngặt theo yêu cầu
                if so_ky_tu < 100:
                    record["trang_thai"] = "docx_it_chu"
                    record["ghi_chu"] = f"File có quá ít chữ ({so_ky_tu} ký tự). Có thể là ảnh dán hoặc scan."
                    print(f"  -> CẢNH BÁO: {record['trang_thai']} ({so_ky_tu} ký tự)")
                elif orig_tables != docx_tables:
                    record["trang_thai"] = "can_duyet"
                    record["ghi_chu"] = f"LỆCH SỐ BẢNG: gốc {orig_tables} bảng, docx đọc ra {docx_tables} bảng"
                    print(f"  -> CẢNH BÁO: {record['ghi_chu']}")
                elif txbx_cnt > 0 or draw_cnt > 0:
                    record["trang_thai"] = "can_duyet"
                    record["ghi_chu"] = f"CẦN DUYỆT: có {txbx_cnt} hộp văn bản, {draw_cnt} ảnh/drawing (nguy cơ sót chữ ngoài luồng chính)"
                    print(f"  -> CẦN DUYỆT: {record['ghi_chu']}")
                else:
                    record["trang_thai"] = "ok"
                    record["ghi_chu"] = "Khớp số bảng, không có textbox/ảnh nổi"
                    print(f"  -> THÀNH CÔNG (ok): {orig_tables} bảng khớp, {so_ky_tu} ký tự")

            except Exception as e:
                record["trang_thai"] = "loi_doc_file"
                record["ghi_chu"] = str(e)
                print(f"  -> LỖI: {e}")

            results.append(record)

    finally:
        print("\nĐang đóng Word COM (word.Quit())...")
        word.Quit()
        del word

    # Ghi kết quả vào CSV chuẩn utf-8-sig
    fieldnames = [
        "file_goc",
        "file_dich",
        "trang_thai",
        "so_ky_tu",
        "so_bang_goc",
        "so_bang_docx",
        "so_hop_van_ban",
        "so_anh_drawing",
        "goi_y_loai",
        "dong_dau",
        "ghi_chu",
    ]
    with csv_file.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nĐã ghi nhật ký đối chiếu vào: {csv_file}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Chuyển đổi .doc sang .docx an toàn bằng Word COM.")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Chạy thử nghiệm 1-2 file đại diện trước khi chạy toàn bộ 19 file.",
    )
    args = parser.parse_args()
    convert_docs(sample_mode=args.sample)


if __name__ == "__main__":
    main()
