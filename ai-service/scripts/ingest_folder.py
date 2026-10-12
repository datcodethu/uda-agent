"""Script cũ nạp cả thư mục (ĐÃ NGỪNG SỬ DỤNG).
Đã được thay thế bằng scripts/ingest_approved.py để kiểm soát nạp theo bảng đăng ký."""
import sys


def main(folder: str | None = None) -> None:
    print(
        "CẢNH BÁO: scripts/ingest_folder.py đã ngừng sử dụng và được thay thế bằng scripts/ingest_approved.py.\n"
        "Vui lòng sử dụng cú pháp mới để kiểm soát nạp theo bảng đăng ký:\n"
        "    python -m scripts.ingest_approved          (mặc định --dry-run để xem trước)\n"
        "    python -m scripts.ingest_approved --apply  (nạp thật vào kho)"
    )
    return


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

