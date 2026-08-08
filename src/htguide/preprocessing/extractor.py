import re

import fitz  # PyMuPDF

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, PDF_TEXT_DIR

logger = get_logger(__name__)

LEGACY_FONT_PATTERN = re.compile(r"(?i)\.vn|vni-|vni_")


def page_has_legacy_font(page) -> bool:
    fonts = page.get_fonts()
    return any(LEGACY_FONT_PATTERN.search(f[3]) for f in fonts)


def file_has_legacy_font(pdf_path) -> bool:
    doc = fitz.open(pdf_path)
    result = any(page_has_legacy_font(page) for page in doc)
    doc.close()
    return result


def extract_text_direct(pdf_path) -> str:
    """Trích text trực tiếp, không OCR — dùng cho file không có font lỗi."""
    doc = fitz.open(pdf_path)
    pages_text = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages_text)


def run_extractor() -> dict:
    """
    Chỉ xử lý file KHÔNG có font lỗi (trích trực tiếp, nhanh).
    File có font lỗi bị bỏ qua nếu đã có sẵn .txt (từ Colab); nếu chưa có, báo cần xử lý riêng.
    """
    pdf_files = sorted(PDF_TEXT_DIR.glob("*.pdf"))
    success, failed, skipped_existing, needs_ocr = 0, 0, 0, 0
    legacy_files_missing = []

    for pdf_path in pdf_files:
        output_path = DATA_INTERIM_DIR / f"{pdf_path.stem}.txt"

        try:
            has_legacy = file_has_legacy_font(pdf_path)
        except Exception as e:
            logger.warning(f"Không kiểm tra được font {pdf_path.name}: {e}")
            failed += 1
            continue

        if has_legacy:
            if output_path.exists():
                logger.info(f"[BỎ QUA - đã có sẵn .txt] {pdf_path.name}")
                skipped_existing += 1
            else:
                logger.warning(f"[CẦN OCR RIÊNG - chưa có .txt] {pdf_path.name}")
                legacy_files_missing.append(pdf_path.name)
                needs_ocr += 1
            continue

        try:
            text = extract_text_direct(pdf_path)
        except Exception as e:
            logger.warning(f"Lỗi trích {pdf_path.name}: {e}")
            failed += 1
            continue

        if not text.strip():
            logger.warning(f"{pdf_path.name} trích ra rỗng, bỏ qua")
            failed += 1
            continue

        output_path.write_text(text, encoding="utf-8")
        logger.info(f"Đã trích: {pdf_path.name}")
        success += 1

    logger.info(
        f"Hoàn tất. Thành công: {success}, Lỗi: {failed}, "
        f"Bỏ qua (đã có sẵn): {skipped_existing}, Cần OCR riêng: {needs_ocr}"
    )
    if legacy_files_missing:
        logger.warning("Các file sau CHƯA có .txt, cần OCR (Colab hoặc chạy OCR CPU riêng):")
        for f in legacy_files_missing:
            logger.warning(f"  - {f}")

    return {
        "success": success,
        "failed": failed,
        "skipped_existing": skipped_existing,
        "needs_ocr": needs_ocr,
    }


if __name__ == "__main__":
    run_extractor()
