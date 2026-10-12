"""Module đọc file .docx tuần tự (đoạn văn và bảng biểu Markdown) bằng python-docx."""
from __future__ import annotations
from pathlib import Path
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"


def iter_block_items(doc: Document):
    """Duyệt tuần tự paragraph và table theo đúng thứ tự xuất hiện trong XML."""
    if hasattr(doc, "element") and hasattr(doc.element, "body"):
        parent_elm = doc.element.body
    elif hasattr(doc, "_tc"):
        parent_elm = doc._tc
    else:
        raise ValueError("Đối tượng document không hợp lệ")

    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)


def format_table(table: Table) -> str:
    """Chuyển bảng Word thành bảng Markdown (nếu >= 2 hàng và >= 2 cột) hoặc văn bản thường (nếu bảng bố cục)."""
    rows = table.rows
    if not rows:
        return ""

    header_cells = rows[0].cells

    # Bảng chỉ dùng để bố cục (1 hàng hoặc 1 cột, như khối chữ ký, quốc hiệu):
    # Giữ dạng văn bản thường, không đổi thành bảng Markdown
    if len(rows) <= 1 or len(header_cells) <= 1:
        lines = []
        seen = set()
        for r in rows:
            for c in r.cells:
                if c._tc not in seen:
                    seen.add(c._tc)
                    t = c.text.strip()
                    if t:
                        lines.append(t)
        return "\n".join(lines)

    # Bảng dữ liệu thực sự (từ 2 hàng và 2 cột trở lên) -> chuyển thành bảng Markdown
    md_lines = []
    header_vals = []
    seen_header = set()
    for c in header_cells:
        if c._tc in seen_header:
            header_vals.append("")  # Ô gộp: tránh lặp chữ
        else:
            seen_header.add(c._tc)
            header_vals.append(c.text.strip().replace("\n", " "))

    if not any(header_vals):
        header_vals = [f"Cột {i}" for i in range(1, len(header_cells) + 1)]

    md_lines.append("| " + " | ".join(header_vals) + " |")
    md_lines.append("| " + " | ".join(["---"] * len(header_vals)) + " |")

    # Các hàng dữ liệu
    for r in rows[1:]:
        row_vals = []
        seen_row = set()
        for c in r.cells:
            if c._tc in seen_row:
                row_vals.append("")
            else:
                seen_row.add(c._tc)
                row_vals.append(c.text.strip().replace("\n", " "))
        md_lines.append("| " + " | ".join(row_vals) + " |")

    return "\n".join(md_lines)


def load_docx(path: str | Path) -> str:
    """Đọc toàn văn .docx theo đúng thứ tự đoạn văn và bảng biểu."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {p}")

    doc = Document(str(p))
    body_items = []

    for item in iter_block_items(doc):
        if isinstance(item, Paragraph):
            t = item.text.strip()
            # Trích xuất thêm text trong hộp văn bản (txbxContent) nếu có lồng trong đoạn
            tb_nodes = item._p.findall(f".//{{{W_NS}}}txbxContent")
            tb_texts = []
            for tb in tb_nodes:
                txt = "".join(n.text for n in tb.iter(f"{{{W_NS}}}t") if n.text).strip()
                if txt and txt not in t:
                    tb_texts.append(txt)
            if tb_texts:
                combined_tb = "\n".join(tb_texts)
                t = f"{t}\n{combined_tb}".strip() if t else combined_tb

            if t:
                body_items.append(t)
        elif isinstance(item, Table):
            formatted_tbl = format_table(item)
            if formatted_tbl:
                body_items.append(formatted_tbl)

    return "\n\n".join(body_items).strip()

