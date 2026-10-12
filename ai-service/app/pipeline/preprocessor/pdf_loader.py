from pathlib import Path
import re
from app.pipeline.preprocessor.docx_loader import load_docx

_VN_ACCENT_RE = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.IGNORECASE)
_LETTER_RE = re.compile(r"[a-zA-ZàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]")
_MIXED_DIGIT_RE = re.compile(r"\b[a-zA-ZÀ-ỸđĐ]+\d+[a-zA-ZÀ-ỸđĐ]+\b")
_WEIRD_PUNCT_WORD_RE = re.compile(r"\b[a-zA-ZÀ-ỸđĐ]+[*&'\"`][a-zA-ZÀ-ỸđĐ]+\b")


def check_pdf_health(text: str, num_pages: int) -> tuple[str, str]:
    """Kiểm tra tình trạng văn bản PDF: 'ok', 'can_ocr', hoặc 'loi_font'."""
    clean_t = text.strip()
    if len(clean_t) < 50 * max(1, num_pages):
        return "can_ocr", "PDF scan hoặc rỗng chữ, không thể trích xuất text trực tiếp"

    letters = _LETTER_RE.findall(clean_t)
    if len(letters) >= 500:
        accents = _VN_ACCENT_RE.findall(clean_t)
        accent_ratio = len(accents) / len(letters)
        corrupted_tokens = len(_MIXED_DIGIT_RE.findall(clean_t)) + len(_WEIRD_PUNCT_WORD_RE.findall(clean_t))

        # Tiếng Việt chuẩn luôn có tỷ lệ nguyên âm có dấu từ 20% - 35%
        # Nếu tỷ lệ dấu < 5% hoặc có trên 10 từ lỗi chèn số/ký tự dị dạng -> lỗi font
        if accent_ratio < 0.05 or corrupted_tokens > 10:
            return "loi_font", f"Nghi lỗi font/bảng mã (tỷ lệ dấu: {accent_ratio*100:.2f}%, từ lỗi: {corrupted_tokens})"

    return "ok", "Đọc tốt"


def load_text(path: str | Path) -> str:
    """Đọc .pdf, .docx hoặc .txt. Trả về text sạch hoặc báo lỗi kèm mã trạng thái rõ ràng."""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".txt":
        return p.read_text(encoding="utf-8")

    if suffix == ".docx":
        text = load_docx(p)
        if len(text.strip()) < 100:
            raise ValueError(f"'{p.name}' [docx_it_chu]: File Word có quá ít chữ (< 100 ký tự). Có thể là ảnh dán.")
        return text

    if suffix == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(str(p))
        pages = [(pg.extract_text() or "") for pg in reader.pages]
        text = "\n".join(pages)

        status, reason = check_pdf_health(text, len(reader.pages))
        if status == "can_ocr":
            raise ValueError(f"'{p.name}' [can_ocr]: {reason}. Cần xin bản gốc từ Phòng Đào tạo.")
        if status == "loi_font":
            raise ValueError(f"'{p.name}' [loi_font]: {reason}. Dừng nạp.")

        return text

    raise ValueError(f"'{p.name}' [loi_doc_file]: Chưa hỗ trợ định dạng {suffix}. Dùng .pdf, .docx hoặc .txt")

