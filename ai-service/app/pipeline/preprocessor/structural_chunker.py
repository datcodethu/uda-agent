"""Cắt văn bản quy chế theo cấu trúc Chương / Điều (không cắt mù theo số ký tự).

Mỗi chunk bắt đầu bằng dòng tiêu đề ngữ cảnh, ví dụ:
    [Quy chế đào tạo 2025 | Chương II: ... | Điều 15. Chuẩn đầu ra ngoại ngữ]
để embedding và BM25 đều "thấy" được vị trí của đoạn trong văn bản.
"""
from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass, asdict

from app.core.textutils import slugify

CHUONG_RE = re.compile(r"^\s*chương\s+([ivxlcdm]+|\d+)\b\s*[.:\-–]?\s*(.*)$", re.IGNORECASE)
DIEU_RE = re.compile(
    r"^\s*(?i:điều)\s+(\d+[a-z]?)(?:\s*[.:\-–—]\s*(.*)|\s+([A-ZÀ-ỸĐ][^\n]*)|[.:\-–—]?\s*)$"
)
TRANS_RE = re.compile(
    r"^\s*(QUY\s+(?:ĐỊNH|CHẾ)\s+(?:BAN\s+HÀNH\s+)?KÈM\s+THEO|QUY\s+(?:ĐỊNH|CHẾ)\s+VỀ)\b",
    re.IGNORECASE,
)
PL_RE = re.compile(r"^\s*PHỤ\s+LỤC\b", re.IGNORECASE)


@dataclass
class Chunk:
    chunk_id: str
    doc_name: str
    chuong: str
    dieu: str          # "Điều 15" hoặc "" nếu là phần mở đầu
    dieu_title: str
    text: str
    status: str = "ACTIVE"
    part: int = 1
    phan_van_ban: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _is_table_line(ln: str) -> bool:
    return "|" in ln


def _clean_overlap(text: str, overlap_max: int = 150) -> str:
    """Lấy đoạn gối đầu 100-150 ký tự theo ranh giới câu từ cuối đoạn trước. Không cắt giữa bảng."""
    if not text or overlap_max <= 0:
        return ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines or _is_table_line(lines[-1]):
        return ""
    tail = text[-min(len(text), overlap_max * 2):]
    matches = list(re.finditer(r"(?<=[.!?])\s+", tail))
    if matches:
        last_start = matches[-1].end()
        candidate = tail[last_start:].strip()
        if 40 <= len(candidate) <= overlap_max + 50:
            return candidate
    return ""


def _split_body(body: str, max_body: int, overlap: int) -> list[str]:
    """Cắt thân bài của Điều ưu tiên theo bảng và ranh giới câu/Khoản, gối đầu sạch và lặp lại header bảng."""
    raw_lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not raw_lines:
        return [""]

    blocks: list[tuple[bool, list[str]]] = []
    cur_lines: list[str] = []
    cur_is_table = False

    for ln in raw_lines:
        is_tbl = _is_table_line(ln)
        if cur_lines and is_tbl != cur_is_table:
            blocks.append((cur_is_table, cur_lines))
            cur_lines = [ln]
            cur_is_table = is_tbl
        else:
            cur_lines.append(ln)
            cur_is_table = is_tbl

    if cur_lines:
        blocks.append((cur_is_table, cur_lines))

    parts: list[str] = []
    cur_chunk = ""

    for is_tbl, lines in blocks:
        if is_tbl:
            tbl_text = "\n".join(lines)
            if cur_chunk and len(cur_chunk) + 1 + len(tbl_text) > max_body:
                parts.append(cur_chunk.strip())
                cur_chunk = ""

            if len(tbl_text) <= max_body:
                cur_chunk = (cur_chunk + "\n" + tbl_text).strip() if cur_chunk else tbl_text
            else:
                hdr = lines[0]
                if len(lines) > 1 and re.match(r"^\|?[-:\s|]+\|?$", lines[1]):
                    hdr = lines[0] + "\n" + lines[1]
                    rows = lines[2:]
                else:
                    rows = lines[1:]

                tbl_cur = hdr
                for r in rows:
                    if len(tbl_cur) + 1 + len(r) > max_body:
                        parts.append(tbl_cur.strip())
                        tbl_cur = hdr + "\n" + r
                    else:
                        tbl_cur += "\n" + r
                if tbl_cur.strip():
                    cur_chunk = tbl_cur.strip()
        else:
            for ln in lines:
                sub_lines = []
                while len(ln) > max_body:
                    cut = ln.rfind(". ", 0, max_body)
                    if cut > 0:
                        sub_lines.append(ln[:cut + 1])
                        ln = ln[cut + 2:].lstrip()
                    else:
                        cut = ln.rfind(" ", 0, max_body)
                        cut = cut if cut > 0 else max_body
                        sub_lines.append(ln[:cut])
                        ln = ln[cut:].lstrip()
                sub_lines.append(ln)

                for sub in sub_lines:
                    if cur_chunk and len(cur_chunk) + 1 + len(sub) > max_body:
                        prev = cur_chunk.strip()
                        parts.append(prev)
                        ov = _clean_overlap(prev, overlap)
                        cur_chunk = (ov + "\n" + sub).strip() if ov else sub
                    else:
                        cur_chunk = (cur_chunk + "\n" + sub).strip() if cur_chunk else sub

    if cur_chunk.strip():
        parts.append(cur_chunk.strip())

    return parts or [""]


def _is_article_title(candidate: str, next_line: str) -> bool:
    c = candidate.strip()
    if not c or len(c) > 120:
        return False
    c_lower = c.lower()
    if (c_lower.startswith("ban hành") or
            c_lower.startswith("quyết định có hiệu lực") or
            c_lower.startswith("quyết định này có hiệu lực") or
            c_lower.startswith("trưởng phòng") or
            c_lower.startswith("chánh văn phòng") or
            c_lower.startswith("các ông (bà)") or
            c_lower.startswith("các ông/bà")):
        return False
    nxt = next_line.strip() if next_line else ""
    if c.endswith("."):
        if nxt and re.match(r"^(\d+\.|-|\+)", nxt):
            return True
        return False
    return True


def extract_doc_title(text: str, fallback: str = "") -> str:
    """Trích xuất tiêu đề văn bản từ phần đầu văn bản (trang 1)."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines[:35]):
        if re.match(r"^\s*QUYẾT\s+ĐỊNH\s*$", ln, re.IGNORECASE):
            j = i + 1
            title_lines = []
            while j < len(lines) and j < i + 5:
                nxt = lines[j]
                if any(k in nxt.upper() for k in ["HIỆU TRƯỞNG", "CĂN CỨ", "XÉT ĐỀ NGHỊ", "QUYẾT ĐỊNH:"]):
                    break
                title_lines.append(nxt)
                if nxt.endswith("."):
                    break
                j += 1
            if title_lines:
                cand = " ".join(title_lines).strip().rstrip(".")
                cand = re.sub(r"^(?:về\s+việc\s+|về\s+)?(?:ban\s+hành\s+)?", "", cand, flags=re.IGNORECASE).strip()
                if cand:
                    return cand

        m_ve = re.match(r"^\s*(?:về\s+việc\s+|về\s+)(?:ban\s+hành\s+)?(.*)$", ln, re.IGNORECASE)
        if m_ve and m_ve.group(1).strip():
            cand = m_ve.group(1).strip().rstrip(".")
            if len(cand) > 10:
                return cand

        m_qc = re.match(r"^\s*(QUY\s+CHẾ|QUY\s+ĐỊNH)\s+(.*)$", ln, re.IGNORECASE)
        if m_qc and m_qc.group(2).strip():
            return f"{m_qc.group(1)} {m_qc.group(2)}".strip().rstrip(".")

    return fallback


def parse_dieu_number(dieu_str: str) -> tuple[int, str]:
    """Tách số Điều thành (số nguyên, hậu tố chữ). Ví dụ: 'Điều 5a' -> (5, 'a')"""
    m = re.search(r"(\d+)\s*([a-z]?)", dieu_str, re.IGNORECASE)
    if not m:
        return (0, "")
    return (int(m.group(1)), m.group(2).lower())


def check_article_order(chunks: list[Chunk], doc_name: str) -> list[str]:
    """Kiểm tra thứ tự Điều (CẢNH BÁO: phát hiện nhảy số, trùng số, giảm số; hỗ trợ 5a)."""
    warnings = []
    sections: dict[str, list[tuple[str, str, str]]] = {}

    for c in chunks:
        if not c.dieu or c.part != 1:
            continue
        sections.setdefault(c.phan_van_ban, []).append((c.dieu, c.dieu_title, c.chunk_id))

    for pvb, articles in sections.items():
        prev_num = 0
        prev_suffix = ""
        prev_dieu = ""
        seen_nums: set[tuple[int, str]] = set()

        for dieu, title, cid in articles:
            num, suffix = parse_dieu_number(dieu)
            if num == 0:
                continue

            cur_tuple = (num, suffix)
            if cur_tuple in seen_nums:
                warnings.append(f"[{doc_name}] [TRÙNG SỐ] {dieu} xuất hiện lặp lại tại đoạn {cid} (phần: {pvb or 'chính'})")
            elif prev_num > 0:
                if num < prev_num:
                    warnings.append(f"[{doc_name}] [GIẢM SỐ] {dieu} giảm từ {prev_dieu} tại đoạn {cid} (phần: {pvb or 'chính'})")
                elif num == prev_num and suffix < prev_suffix:
                    warnings.append(f"[{doc_name}] [GIẢM SỐ] {dieu} nhỏ hơn {prev_dieu} tại đoạn {cid} (phần: {pvb or 'chính'})")
                elif num > prev_num + 1:
                    skipped = [f"Điều {i}" for i in range(prev_num + 1, num)]
                    warnings.append(f"[{doc_name}] [NHẢY SỐ] Từ {prev_dieu} nhảy sang {dieu} (thiếu {', '.join(skipped)}) tại đoạn {cid} (phần: {pvb or 'chính'})")

            seen_nums.add(cur_tuple)
            prev_num = num
            prev_suffix = suffix
            prev_dieu = dieu

    return warnings


def chunk_document(text: str, doc_name: str, status: str = "ACTIVE",
                   max_chars: int = 1200, overlap: int = 150,
                   doc_title: str | None = None) -> list[Chunk]:
    text = unicodedata.normalize("NFC", text)
    lines = text.split("\n")

    articles: list[tuple[str, str, str, str, str]] = []  # (phan_van_ban, chuong, dieu, title, body)
    cur_phan = "quyet_dinh" if re.search(r"^\s*QUYẾT\s+ĐỊNH\b", text[:2000], re.MULTILINE | re.IGNORECASE) else ""
    chuong = dieu = dieu_title = ""
    last_dieu_num = 0
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body or dieu:
            articles.append((cur_phan, chuong, dieu, dieu_title, body))
        buf.clear()

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue

        if TRANS_RE.match(line):
            flush()
            cur_phan = "quy_dinh_kem_theo"
            chuong = dieu = dieu_title = ""
            last_dieu_num = 0
            buf.append(line)
            continue

        if PL_RE.match(line):
            flush()
            cur_phan = "phu_luc"
            chuong = dieu = dieu_title = ""
            last_dieu_num = 0
            buf.append(line)
            continue

        m = CHUONG_RE.match(line)
        if m:
            flush()
            title = m.group(2).strip()
            if not title:  # tiêu đề chương thường nằm ở dòng kế tiếp, viết HOA
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    nxt = lines[j].strip()
                    if nxt.isupper() and not DIEU_RE.match(nxt) and not CHUONG_RE.match(nxt):
                        title, i = nxt, j + 1
            chuong = f"Chương {m.group(1).upper()}" + (f": {title}" if title else "")
            dieu = dieu_title = ""
            continue

        m = DIEU_RE.match(line)
        if m:
            flush()
            num_match = re.match(r"\d+", m.group(1))
            num = int(num_match.group()) if num_match else 0
            if cur_phan == "quyet_dinh" and num == 1 and last_dieu_num > 1:
                cur_phan = "quy_dinh_kem_theo"
                chuong = ""
            last_dieu_num = num

            dieu = f"Điều {m.group(1)}"
            cand = (m.group(2) or m.group(3) or "").strip()
            nxt_line = ""
            j = i
            while j < len(lines):
                if lines[j].strip():
                    nxt_line = lines[j].strip()
                    break
                j += 1
            if _is_article_title(cand, nxt_line):
                dieu_title = cand.rstrip(".")
            else:
                dieu_title = ""
                if cand:
                    buf.append(cand)
            continue

        buf.append(line)
    flush()

    chunks: list[Chunk] = []
    seen: dict[str, int] = {}
    slug = slugify(doc_name)
    has_distinct_sections = any(a[0] in ("quyet_dinh", "quy_dinh_kem_theo", "phu_luc") for a in articles)

    for pvb, chuong_, dieu_, title_, body in articles:
        head = [doc_title or doc_name]
        if chuong_:
            head.append(chuong_)
        if dieu_:
            head.append(f"{dieu_}. {title_}" if title_ else dieu_)
        header = "[" + " | ".join(head) + "]"
        max_body = max(200, max_chars - len(header) - 1)
        parts = _split_body(body, max_body, overlap) if body else [""]

        pvb_tag = ""
        if has_distinct_sections:
            if pvb == "quyet_dinh":
                pvb_tag = "qd"
            elif pvb == "quy_dinh_kem_theo":
                pvb_tag = "qdkt"
            elif pvb == "phu_luc":
                pvb_tag = "pl"

        for k, part in enumerate(parts, 1):
            did = dieu_.replace("Điều ", "d").lower() if dieu_ else "d0"
            cid = f"{slug}-{pvb_tag}-{did}-{k}" if pvb_tag else f"{slug}-{did}-{k}"
            if cid in seen:
                seen[cid] += 1
                cid = f"{cid}-x{seen[cid]}"
            else:
                seen[cid] = 0
            chunks.append(Chunk(
                chunk_id=cid, doc_name=doc_name, chuong=chuong_, dieu=dieu_,
                dieu_title=title_, text=(header + "\n" + part).strip(),
                status=status, part=k, phan_van_ban=pvb,
            ))
    return chunks
