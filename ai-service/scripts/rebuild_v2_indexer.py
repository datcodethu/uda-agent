"""Rebuild Knowledge Base v2 (donga_kb_v2):
- Đọc các tệp Markdown tại data/staging_v2/
- Phân đoạn cấu trúc học vụ (Academic Structural Chunker)
- Lưu chunks vào data/chunks_v2.jsonl
- Nhúng vector bằng Gemini Embedding API (768 chiều)
- Upsert vào collection donga_kb_v2 tại data/qdrant_local_v2/
- Xây dựng chỉ mục BM25 v2 độc lập tại data/bm25_index_v2.pkl
- Xuất evaluation/kb_rebuild_v2/ingest_results.csv
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import logging
import os
import pickle
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rebuild_indexer_v2")

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.core.config import settings
from app.core.textutils import slugify
from app.pipeline.preprocessor.structural_chunker import (
    DIEU_RE,
    CHUONG_RE,
    TRANS_RE,
    PL_RE,
    _clean_overlap,
    _is_table_line,
    _split_body,
)

STAGING_V2_DIR = BASE_DIR / "data" / "staging_v2"
QDRANT_V2_PATH = BASE_DIR / "data" / "qdrant_local_v2"
CHUNKS_V2_FILE = BASE_DIR / "data" / "chunks_v2.jsonl"
BM25_V2_FILE = BASE_DIR / "data" / "bm25_index_v2.pkl"
EVAL_DIR = BASE_DIR.parent / "evaluation" / "kb_rebuild_v2"
COLLECTION_V2_NAME = "donga_kb_v2"


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    """Tách phần YAML header và thân bài Markdown."""
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
            body = parts[2].strip()
    return meta, body


def chunk_academic_markdown(
    meta: Dict[str, str],
    body: str,
    max_chars: int = 1200,
    overlap_chars: int = 150,
) -> List[Dict[str, Any]]:
    """Phân đoạn tài liệu Markdown học vụ bảo toàn cấu trúc Điều/Khoản, Bảng, và Tiêu đề."""
    source_id = meta.get("source_id", "SRC-UNKNOWN")
    doc_title = meta.get("title", "")
    source_url = meta.get("url", "")
    crawled_at = meta.get("crawled_at", "")
    content_type = meta.get("content_type", "tai_lieu_tong_hop")
    slug = slugify(source_id)

    lines = body.splitlines()

    # Kiểm tra xem văn bản có cấu trúc "Điều" hay không (như Quy chế đào tạo SRC-V2-009)
    has_dieu = sum(1 for ln in lines if DIEU_RE.match(ln)) >= 3

    sections: List[Tuple[str, str, str, str, str]] = []  # (phan, chuong, dieu, title, content)
    buf: List[str] = []
    cur_phan = ""
    cur_chuong = ""
    cur_dieu = ""
    cur_title = ""

    def flush_section():
        nonlocal buf
        txt = "\n".join(buf).strip()
        if txt:
            sections.append((cur_phan, cur_chuong, cur_dieu, cur_title, txt))
        buf = []

    if has_dieu:
        # Sử dụng logic bóc tách Điều/Chương chuẩn của Trường
        last_dieu_num = 0
        i = 0
        while i < len(lines):
            line = lines[i]
            strip_ln = line.strip()

            if not strip_ln:
                buf.append(line)
                i += 1
                continue

            if TRANS_RE.match(strip_ln):
                flush_section()
                cur_phan = "quy_dinh_kem_theo"
                cur_chuong = cur_dieu = cur_title = ""
                buf.append(line)
                i += 1
                continue

            if PL_RE.match(strip_ln):
                flush_section()
                cur_phan = "phu_luc"
                cur_chuong = cur_dieu = cur_title = ""
                buf.append(line)
                i += 1
                continue

            m_ch = CHUONG_RE.match(strip_ln)
            if m_ch:
                flush_section()
                title_ch = m_ch.group(2).strip()
                cur_chuong = f"Chương {m_ch.group(1).upper()}" + (f": {title_ch}" if title_ch else "")
                cur_dieu = cur_title = ""
                i += 1
                continue

            m_dieu = DIEU_RE.match(strip_ln)
            if m_dieu:
                flush_section()
                num_m = re.match(r"\d+", m_dieu.group(1))
                num = int(num_m.group()) if num_m else 0
                if cur_phan == "quyet_dinh" and num == 1 and last_dieu_num > 1:
                    cur_phan = "quy_dinh_kem_theo"
                last_dieu_num = num

                cur_dieu = f"Điều {m_dieu.group(1)}"
                cand_t = (m_dieu.group(2) or m_dieu.group(3) or "").strip().rstrip(".")
                cur_title = cand_t
                i += 1
                continue

            buf.append(line)
            i += 1
        flush_section()

    else:
        # Bóc tách theo Tiêu đề Markdown (# , ## , ### )
        i = 0
        while i < len(lines):
            line = lines[i]
            strip_ln = line.strip()

            m_h = re.match(r"^(#{1,4})\s+(.+)$", strip_ln)
            if m_h:
                flush_section()
                heading_level = len(m_h.group(1))
                heading_text = m_h.group(2).strip().rstrip(".")
                if heading_level == 1:
                    cur_chuong = heading_text
                    cur_dieu = ""
                    cur_title = ""
                elif heading_level in (2, 3):
                    cur_dieu = heading_text
                    cur_title = ""
                i += 1
                continue

            buf.append(line)
            i += 1
        flush_section()

    # Tạo chunks từ các sections
    chunks: List[Dict[str, Any]] = []
    seen_ids: Dict[str, int] = {}

    for pvb, chuong_, dieu_, title_, content in sections:
        # Xây dựng breadcrumb header
        head = [doc_title or source_id]
        if chuong_:
            head.append(chuong_)
        if dieu_:
            head.append(f"{dieu_}. {title_}" if title_ else dieu_)
        header = "[" + " | ".join(head) + "]"

        max_body = max(200, max_chars - len(header) - 2)
        parts = _split_body(content, max_body, overlap_chars) if content else [""]

        for k, part in enumerate(parts, 1):
            did = dieu_.replace("Điều ", "d").replace(" ", "_").lower() if dieu_ else "d0"
            did = re.sub(r"[^\w\-]", "", did)[:30]
            cid = f"{slug}-{did}-{k}"
            if cid in seen_ids:
                seen_ids[cid] += 1
                cid = f"{cid}-x{seen_ids[cid]}"
            else:
                seen_ids[cid] = 0

            full_chunk_text = (header + "\n" + part).strip()

            chunks.append({
                "chunk_id": cid,
                "doc_name": source_id,
                "doc_title": doc_title,
                "source_id": source_id,
                "source_url": source_url,
                "crawled_at": crawled_at,
                "content_type": content_type,
                "version": "v2",
                "chuong": chuong_,
                "dieu": dieu_,
                "dieu_title": title_,
                "section_heading": header,
                "part": k,
                "status": "ACTIVE",
                "text": full_chunk_text,
                "chars_length": len(full_chunk_text),
            })

    return chunks


def build_bm25_v2(chunks: List[Dict[str, Any]]) -> Any:
    """Xây dựng chỉ mục BM25 cho tập chunks v2."""
    from rank_bm25 import BM25Okapi
    token_re = re.compile(r"\w+", re.UNICODE)

    def tokenize(text: str) -> list[str]:
        return token_re.findall(text.lower())

    corpus = [tokenize(c["text"]) for c in chunks]
    index = BM25Okapi(corpus) if corpus else None
    return index


def run_rebuild_indexer(dry_run: bool = False):
    """Quy trình tổng thể nạp kho tri thức v2."""
    staging_files = sorted(STAGING_V2_DIR.glob("*.md"))
    if not staging_files:
        logger.error(f"Không tìm thấy tệp nào trong {STAGING_V2_DIR}")
        return

    logger.info(f"Bắt đầu phân đoạn {len(staging_files)} tài liệu Staging v2...")

    all_chunks: List[Dict[str, Any]] = []
    ingest_report_rows: List[Dict[str, Any]] = []

    for fpath in staging_files:
        raw_text = fpath.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw_text)
        src_id = meta.get("source_id", fpath.stem)
        title = meta.get("title", "")
        url = meta.get("url", "")

        chunks = chunk_academic_markdown(meta, body, max_chars=1200, overlap_chars=150)
        all_chunks.extend(chunks)

        logger.info(f"[{src_id}] {title[:40]}... -> {len(chunks)} chunks")

        ingest_report_rows.append({
            "source_id": src_id,
            "doc_title": title,
            "source_url": url,
            "chunks_count": len(chunks),
            "chars_count": len(body),
            "status": "CHUNKED" if dry_run else "INDEXED",
        })

    logger.info(f"Tổng số chunks tạo ra: {len(all_chunks)} chunks.")

    if dry_run:
        logger.info("Chế độ DRY-RUN: Không gọi API Embedding và không ghi Qdrant.")
        return all_chunks

    # 1. Lưu chunks_v2.jsonl
    CHUNKS_V2_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CHUNKS_V2_FILE.open("w", encoding="utf-8") as f:
        for c in all_chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    logger.info(f"Đã lưu toàn bộ chunks v2 vào {CHUNKS_V2_FILE}")

    # 2. Xây dựng và lưu chỉ mục BM25 v2
    bm25 = build_bm25_v2(all_chunks)
    with BM25_V2_FILE.open("wb") as f:
        pickle.dump({"chunks": all_chunks, "bm25": bm25}, f)
    logger.info(f"Đã lưu chỉ mục BM25 v2 vào {BM25_V2_FILE}")

# 3. Nhúng vector và Upsert vào Qdrant Local v2
    from qdrant_client import QdrantClient, models
    from app.pipeline.retrieval.dense_search import get_embedder, embed_query

    EMBED_CACHE_FILE = BASE_DIR / "data" / "embeddings_cache_v2.pkl"
    cache: Dict[str, List[float]] = {}
    if EMBED_CACHE_FILE.exists():
        try:
            with open(EMBED_CACHE_FILE, "rb") as f:
                cache = pickle.load(f)
            logger.info(f"Đã tải {len(cache)} vectors từ bộ nhớ đệm {EMBED_CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Không thể đọc cache: {e}")

    logger.info(f"Khởi tạo Qdrant Local v2 tại: {QDRANT_V2_PATH}")
    QDRANT_V2_PATH.mkdir(parents=True, exist_ok=True)
    client = QdrantClient(path=str(QDRANT_V2_PATH))

    # Kiểm tra chiều vector
    dim = len(embed_query("kiểm tra số chiều vector"))
    logger.info(f"Số chiều vector embedding: {dim}")

    if client.collection_exists(COLLECTION_V2_NAME):
        logger.info(f"Collection {COLLECTION_V2_NAME} đã tồn tại. Đang xóa để làm mới từ đầu...")
        client.delete_collection(COLLECTION_V2_NAME)

    client.create_collection(
        collection_name=COLLECTION_V2_NAME,
        vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
    )
    logger.info(f"Đã tạo collection mới: {COLLECTION_V2_NAME}")

    # Nhúng vector có bộ nhớ đệm và cơ chế tự động thử lại khi gặp 429
    texts = [c["text"] for c in all_chunks]
    logger.info(f"Bắt đầu nhúng vector cho {len(texts)} chunks (batch size 20, chống lỗi 429)...")

    embedder = get_embedder()
    vectors: List[List[float]] = []
    batch_size = 20

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_hashes = [hashlib.sha256(t.encode("utf-8")).hexdigest() for t in batch]

        # Kiểm tra xem batch này đã có trong cache chưa
        cached_batch = [cache.get(h) for h in batch_hashes]
        if all(v is not None for v in cached_batch):
            vectors.extend(cached_batch)
            continue

        # Cần gọi API cho các text chưa có trong cache
        for attempt in range(5):
            try:
                sub_vecs = embedder.embed_documents(batch, task_type="RETRIEVAL_DOCUMENT")
                for h, v in zip(batch_hashes, sub_vecs):
                    cache[h] = v
                vectors.extend(sub_vecs)

                # Lưu cache ngay sau mỗi batch thành công
                try:
                    with open(EMBED_CACHE_FILE, "wb") as f:
                        pickle.dump(cache, f)
                except Exception:
                    pass

                logger.info(f"Đã nhúng {len(vectors)}/{len(texts)} chunks (Batch {i // batch_size + 1})...")
                time.sleep(2.0)  # Nghỉ 2s giữa các batch
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    sleep_time = 35.0
                    m_retry = re.search(r"retry in (\d+(\.\d+)?)s", err_str)
                    if m_retry:
                        sleep_time = float(m_retry.group(1)) + 2.0
                    logger.warning(f"Gặp lỗi hạn ngạch 429 (lần thử {attempt + 1}/5). Nghỉ {sleep_time:.1f}s trước khi thử lại...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"Lỗi khi embed batch {i}: {e}")
                    raise e

    logger.info(f"Đã nhúng thành công toàn bộ {len(vectors)} vectors.")

    points = [
        models.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, c["chunk_id"])),
            vector=v,
            payload=c,
        )
        for c, v in zip(all_chunks, vectors)
    ]

    # Upsert vào Qdrant
    client.upsert(collection_name=COLLECTION_V2_NAME, points=points)
    col_info = client.get_collection(COLLECTION_V2_NAME)
    logger.info(f"Upsert hoàn tất! Tổng số points trong {COLLECTION_V2_NAME}: {col_info.points_count}")

    # 4. Xuất ingest_results.csv
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    ingest_csv = EVAL_DIR / "ingest_results.csv"
    with ingest_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source_id", "doc_title", "source_url", "chunks_count", "chars_count", "status"],
        )
        writer.writeheader()
        writer.writerows(ingest_report_rows)

    logger.info(f"Đã xuất báo cáo: {ingest_csv}")
    return all_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rebuild Knowledge Base v2")
    parser.add_argument("--dry-run", action="store_true", help="Chạy thử nghiệm không gọi embedding API")
    args = parser.parse_args()
    run_rebuild_indexer(dry_run=args.dry_run)
