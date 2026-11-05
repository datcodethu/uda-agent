"""Khởi tạo kho demo trên volume riêng rồi chạy một tiến trình Uvicorn."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid


def seed_storage(seed_dir: Path, storage_dir: Path) -> bool:
    """Chỉ khởi tạo volume trống; không ghi đè dữ liệu đã được dev thay đổi."""
    storage_dir.mkdir(parents=True, exist_ok=True)
    marker = storage_dir / ".demo-initialized"
    chunks_path = storage_dir / "chunks.jsonl"
    qdrant_path = storage_dir / "qdrant_local"
    if marker.exists():
        if not chunks_path.is_file() or not (qdrant_path / "meta.json").is_file():
            raise RuntimeError("Volume demo đã khởi tạo nhưng thiếu dữ liệu. Hãy kiểm tra/khôi phục volume.")
        return False
    if chunks_path.exists() or qdrant_path.exists():
        raise RuntimeError("Volume có dữ liệu nhưng chưa có dấu khởi tạo; không tự ghi đè. Hãy kiểm tra volume.")

    # Kiểm tra cả JSONL và vector trước khi đưa cặp dữ liệu vào sử dụng.
    chunks = [json.loads(line) for line in (seed_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [c["chunk_id"] for c in chunks]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("Snapshot demo rỗng hoặc trùng chunk_id.")
    with tempfile.TemporaryDirectory(prefix=".seed-", dir=storage_dir) as staging:
        stage = Path(staging)
        shutil.copyfile(seed_dir / "chunks.jsonl", stage / "chunks.jsonl")
        shutil.copytree(seed_dir / "qdrant_local", stage / "qdrant_local", ignore=shutil.ignore_patterns(".lock"))
        from qdrant_client import QdrantClient

        client = QdrantClient(path=str(stage / "qdrant_local"))
        try:
            points, _ = client.scroll("donga_regulations", limit=len(chunks) + 1, with_payload=True, with_vectors=False)
            expected = {str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])): c for c in chunks}
            if len(points) != len(chunks) or any(
                str(p.id) not in expected or p.payload != expected[str(p.id)] for p in points
            ):
                raise ValueError("Snapshot JSONL và Qdrant không đồng bộ.")
        finally:
            client.close()
        (stage / "chunks.jsonl").replace(chunks_path)
        (stage / "qdrant_local").replace(qdrant_path)
        marker.write_text("backup_pre_demo_20261104\n", encoding="utf-8")
    print(f"Demo storage initialized: {len(chunks)} chunks; no embedding API calls.", flush=True)
    return True


def main() -> None:
    seed = os.environ.get("DEMO_SEED_DIR")
    if seed:
        seed_storage(Path(seed), Path(os.environ.get("CHUNKS_FILE", "/srv/storage/chunks.jsonl")).parent)
    # Qdrant local chỉ cho một tiến trình truy cập kho: không dùng --workers/--reload.
    os.execv(sys.executable, [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
