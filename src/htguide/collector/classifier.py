import shutil

import fitz  # PyMuPDF

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_RAW_DIR, PDF_SCANNED_DIR, PDF_TEXT_DIR

logger = get_logger(__name__)

MIN_TEXT_LENGTH = 20  # ngưỡng ký tự tối thiểu để coi là "có text"
SAMPLE_PAGES = 3       # chỉ kiểm tra vài trang đầu, đủ để kết luận, không cần đọc hết file


def is_scanned_pdf(path) -> bool:
    """Trả về True nếu PDF gần như không có text trích xuất được (khả năng cao là scan/ảnh)."""
    try:
        doc = fitz.open(path)
    except Exception as e:
        logger.warning(f"Không mở được {path.name}: {e}")
        return False  # không chắc chắn -> để nguyên, không phân loại nhầm

    text_len = 0
    for page in doc[:SAMPLE_PAGES]:
        text_len += len(page.get_text().strip())
    doc.close()

    return text_len < MIN_TEXT_LENGTH


def classify_pdf(path) -> str:
    """Phân loại 1 file PDF, move vào đúng thư mục, trả về loại đã phân ('text' | 'scanned' | 'error')."""
    if is_scanned_pdf(path):
        target_dir = PDF_SCANNED_DIR
        label = "scanned"
    else:
        target_dir = PDF_TEXT_DIR
        label = "text"

    target_path = target_dir / path.name

    counter = 1
    while target_path.exists():
        target_path = target_dir / f"{path.stem}_{counter}{path.suffix}"
        counter += 1

    shutil.move(str(path), str(target_path))
    logger.info(f"[{label}] {path.name} -> {target_dir.name}/")
    return label


def run_classifier() -> dict:
    """Quét toàn bộ PDF trong DATA_RAW_DIR (không đệ quy vào thư mục con), phân loại từng file."""
    pdf_files = [f for f in DATA_RAW_DIR.glob("*.pdf") if f.is_file()]

    counts = {"text": 0, "scanned": 0, "error": 0}

    for pdf_path in pdf_files:
        label = classify_pdf(pdf_path)
        counts[label] = counts.get(label, 0) + 1

    logger.info(
        f"Hoàn tất phân loại. Text-based: {counts['text']}, "
        f"Scanned: {counts['scanned']}, Lỗi: {counts.get('error', 0)}"
    )
    return counts


if __name__ == "__main__":
    run_classifier()