import re

import fitz  # PyMuPDF

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, PDF_TEXT_DIR

logger = get_logger(__name__)

RENDER_DPI = 300

LEGACY_FONT_PATTERN = re.compile(r"(?i)\.vn|vni-|vni_")

_reader = None


def get_ocr_reader():
    global _reader
    if _reader is None:
        import easyocr
        logger.info("Khởi tạo EasyOCR reader (lần đầu, có thể mất chút thời gian)...")
        _reader = easyocr.Reader(["vi", "en"], gpu=False)
    return _reader


def page_has_legacy_font(page) -> bool:
    fonts = page.get_fonts()
    return any(LEGACY_FONT_PATTERN.search(f[3]) for f in fonts)


def ocr_page(page) -> str:
    zoom = RENDER_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix)
    img_bytes = pix.tobytes("png")

    reader = get_ocr_reader()
    result = reader.readtext(img_bytes, detail=0, paragraph=True)
    return "\n".join(result)


def extract_text_from_pdf(pdf_path) -> tuple[str, int]:
    doc = fitz.open(pdf_path)
    pages_text = []
    ocr_page_count = 0

    for i, page in enumerate(doc):
        if page_has_legacy_font(page):
            logger.info(f"  Trang {i + 1}: font legacy phát hiện -> OCR")
            text = ocr_page(page)
            ocr_page_count += 1
        else:
            text = page.get_text()
        pages_text.append(text)

    doc.close()
    return "\n\n".join(pages_text), ocr_page_count


def run_extractor() -> dict:
    pdf_files = sorted(PDF_TEXT_DIR.glob("*.pdf"))
    success, failed, files_with_ocr = 0, 0, 0

    for pdf_path in pdf_files:
        try:
            text, ocr_count = extract_text_from_pdf(pdf_path)
        except Exception as e:
            logger.warning(f"Không trích được text từ {pdf_path.name}: {e}")
            failed += 1
            continue

        if not text.strip():
            logger.warning(f"{pdf_path.name} trích ra rỗng, bỏ qua")
            failed += 1
            continue

        if ocr_count > 0:
            files_with_ocr += 1
            logger.info(f"{pdf_path.name}: {ocr_count} trang được OCR do font legacy")

        output_path = DATA_INTERIM_DIR / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")
        logger.info(f"Đã trích: {pdf_path.name} -> {output_path.name}")
        success += 1

    logger.info(
        f"Hoàn tất trích text. Thành công: {success}/{len(pdf_files)}, Lỗi: {failed}, "
        f"File có trang cần OCR: {files_with_ocr}"
    )
    return {"success": success, "failed": failed, "total": len(pdf_files), "files_with_ocr": files_with_ocr}


if __name__ == "__main__":
    run_extractor()
