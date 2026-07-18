import fitz  # PyMuPDF
import easyocr

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, PDF_SCANNED_DIR

logger = get_logger(__name__)

# Khởi tạo reader 1 lần duy nhất (nạp model), dùng lại cho toàn bộ file
READER = easyocr.Reader(["vi", "en"], gpu=False)

RENDER_DPI = 300


def pdf_to_images(pdf_path):
    """Render từng trang PDF thành ảnh (PNG bytes) bằng PyMuPDF."""
    doc = fitz.open(pdf_path)
    images = []
    zoom = RENDER_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        images.append(pix.tobytes("png"))

    doc.close()
    return images


def ocr_pdf(pdf_path) -> str:
    """OCR toàn bộ trang của 1 file PDF scanned, trả về text ghép lại."""
    images = pdf_to_images(pdf_path)
    pages_text = []

    for i, img_bytes in enumerate(images):
        result = READER.readtext(img_bytes, detail=0, paragraph=True)
        page_text = "\n".join(result)
        pages_text.append(page_text)
        logger.info(f"  Trang {i + 1}/{len(images)} xong ({len(page_text)} ký tự)")

    return "\n\n".join(pages_text)


def run_ocr() -> dict:
    """Quét toàn bộ PDF trong PDF_SCANNED_DIR, OCR, lưu ra DATA_INTERIM_DIR."""
    pdf_files = sorted(PDF_SCANNED_DIR.glob("*.pdf"))
    success, failed = 0, 0

    for pdf_path in pdf_files:
        logger.info(f"Đang OCR: {pdf_path.name}")
        try:
            text = ocr_pdf(pdf_path)
        except Exception as e:
            logger.warning(f"Lỗi OCR {pdf_path.name}: {e}")
            failed += 1
            continue

        if not text.strip():
            logger.warning(f"{pdf_path.name} OCR ra rỗng, bỏ qua")
            failed += 1
            continue

        output_path = DATA_INTERIM_DIR / f"{pdf_path.stem}.txt"
        output_path.write_text(text, encoding="utf-8")
        logger.info(f"Đã OCR: {pdf_path.name} -> {output_path.name}")
        success += 1

    logger.info(f"Hoàn tất OCR. Thành công: {success}/{len(pdf_files)}, Lỗi: {failed}")
    return {"success": success, "failed": failed, "total": len(pdf_files)}


if __name__ == "__main__":
    run_ocr()
