from htguide.collector.crawler import run_crawler
from htguide.collector.downloader import run_downloader
from htguide.collector.classifier import run_classifier
from htguide.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("=== Bước 1: Crawl tìm link tài liệu ===")
    found_files = run_crawler()

    logger.info("=== Bước 2: Tải file về ===")
    downloaded = run_downloader(found_files)

    logger.info("=== Bước 3: Phân loại PDF text-based vs scanned ===")
    counts = run_classifier()

    logger.info(
        f"=== HOÀN TẤT === Tìm: {len(found_files)}, "
        f"Tải: {len(downloaded)}, "
        f"Text: {counts['text']}, Scanned: {counts['scanned']}"
    )


if __name__ == "__main__":
    main()