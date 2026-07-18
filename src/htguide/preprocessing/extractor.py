import fitz  # PyMuPDF

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, PDF_TEXT_DIR

logger = get_logger(__name__)


def extract_text_from_pdf(pdf_path) -> str:
    """Trích toàn bộ text từ 1 file PDF text-based."""
    doc = fitz.open(pdf_path)
    pages_text = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages_text)


def run_extractor() -> dict:
    """Quét toàn bộ PDF trong PDF_TEXT_DIR, trích text, lưu ra DATA_INTERIM_DIR dưới dạng .txt."""
    pdf_files = sorted(PDF_TEXT_DIR.glob("*.pdf"))
    success, failed = 0, 0

    for pdf_path in pdf_files:
        try:
            text = extract_text_from_pdf(pdf_path)
        except Exception as e:
            logger.warning(f"Không trích được text từ {pdf_path.name}: {e}")
            failed += 1
            continue

        if not text.strip():
            logger.warning(f"{pdf_path.name} trích ra rỗng, bỏ qua")
            failed += 1
            continue

        output_path = DATA_INTERIM_DIR / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")
        logger.info(f"Đã trích: {pdf_path.name} -> {output_path.name}")
        success += 1

    logger.info(f"Hoàn tất trích text. Thành công: {success}/{len(pdf_files)}, Lỗi: {failed}")
    return {"success": success, "failed": failed, "total": len(pdf_files)}


if __name__ == "__main__":
    run_extractor()