"""Nạp tất cả .pdf/.txt trong data/raw_documents.
Chạy từ thư mục ai-service:   python -m scripts.ingest_folder
LƯU Ý: nếu dùng Qdrant local thì phải TẮT server uvicorn trước khi chạy script này."""
import sys
from pathlib import Path

from app.core.config import BASE_DIR
from app.pipeline import index_service
from app.pipeline.preprocessor.pdf_loader import load_text


def main(folder: str | None = None) -> None:
    folder_path = Path(folder) if folder else BASE_DIR / "data" / "raw_documents"
    files = sorted(p for p in folder_path.iterdir() if p.suffix.lower() in (".pdf", ".txt"))
    if not files:
        print(f"Không có file .pdf/.txt trong {folder_path}")
        return
    for f in files:
        try:
            info = index_service.index_document(f.stem, load_text(f))
            print(f"OK   {f.name}: {info['chunks']} chunk")
        except Exception as e:
            print(f"LỖI  {f.name}: {e}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
