"""Kiểm tra khởi tạo volume bằng snapshot thật; không gọi API bên ngoài."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.docker_start import seed_storage


SEED = Path(__file__).resolve().parents[1] / "data" / "backup_pre_demo_20261104"


class TestDockerStorage(unittest.TestCase):
    def test_existing_unmarked_data_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            chunks = storage / "chunks.jsonl"
            chunks.write_text("existing data", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                seed_storage(SEED, storage)
            self.assertEqual(chunks.read_text(encoding="utf-8"), "existing data")

    def test_incomplete_initialized_volume_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            (storage / ".demo-initialized").touch()
            with self.assertRaises(RuntimeError):
                seed_storage(SEED, storage)

    @unittest.skipUnless((SEED / "qdrant_local" / "meta.json").exists(), "Snapshot được mount riêng, không có trong image")
    def test_real_snapshot_and_restart_preserve_dev_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            storage = Path(tmp)
            self.assertTrue(seed_storage(SEED, storage))
            chunks_path = storage / "chunks.jsonl"
            chunks = [json.loads(line) for line in chunks_path.read_text(encoding="utf-8").splitlines()]
            self.assertGreater(len(chunks), 0)
            # Dev có thể nạp/gỡ tài liệu; lần khởi động sau không được phục hồi đè lên.
            chunks_path.write_text("", encoding="utf-8")
            self.assertFalse(seed_storage(SEED, storage))
            self.assertEqual(chunks_path.read_text(encoding="utf-8"), "")


if __name__ == "__main__":
    unittest.main()
