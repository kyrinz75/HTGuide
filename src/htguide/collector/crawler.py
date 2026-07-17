import os
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from htguide.utils.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

BASE_URL = os.getenv("BASE_URL")
USER_AGENT = os.getenv("USER_AGENT")
LIST_PAGES = [p.strip() for p in os.getenv("LIST_PAGES", "").split(",") if p.strip()]
MAX_DEPTH = int(os.getenv("MAX_DEPTH", 3))

HEADERS = {"User-Agent": USER_AGENT}
FILE_EXTENSIONS = (".pdf", ".docx", ".doc")
DOWNLOAD_PATTERN = re.compile(r"/download/[\w-]+/\d+")


def is_internal(url: str) -> bool:
    """Chỉ chấp nhận link cùng domain với BASE_URL, tránh crawl lan ra ngoài."""
    return urlparse(url).netloc == urlparse(BASE_URL).netloc


def is_in_scope(url: str) -> bool:
    """Chỉ crawl các URL nằm trong phạm vi BASE_URL, tránh lan sang mục khác của trường."""
    if "#" in url:
        return False
    return url.startswith(BASE_URL)


def is_file_link(url: str, text: str) -> bool:
    """Nhận diện file theo 2 cách: đuôi file rõ ràng, hoặc pattern URL /download/.../id"""
    url_lower = url.lower()
    text_lower = text.lower()

    has_extension = any(ext in url_lower for ext in FILE_EXTENSIONS) or any(
        ext in text_lower for ext in FILE_EXTENSIONS
    )
    is_download_pattern = bool(DOWNLOAD_PATTERN.search(url))

    return has_extension or is_download_pattern


def crawl(url: str, visited: set, found_files: list, depth: int = 0) -> None:
    if url in visited or depth > MAX_DEPTH:
        return
    visited.add(url)
    logger.info(f"[depth={depth}] Đang crawl: {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
    except requests.RequestException as e:
        logger.warning(f"Không truy cập được {url}: {e}")
        return

    if "text/html" not in res.headers.get("Content-Type", ""):
        return

    soup = BeautifulSoup(res.text, "lxml")
    links = soup.find_all("a", href=True)
    logger.info(f"[depth={depth}] Tìm thấy {len(links)} thẻ <a> trên {url}")

    for a in links:
        href = a["href"]
        full_url = urljoin(url, href)
        text = a.get_text(strip=True)

        if not is_internal(full_url):
            continue

        # Kiểm tra file TRƯỚC — vì link file nằm ở /download/..., ngoài phạm vi /daotao
        if is_file_link(full_url, text):
            found_files.append({"filename": text or full_url.split("/")[-1], "url": full_url})
            logger.info(f"Tìm thấy file (candidate): {text}")
            continue

        # Chỉ áp dụng is_in_scope cho các link KHÔNG phải file (để quyết định có crawl tiếp không)
        if not is_in_scope(full_url):
            continue

        if full_url not in visited:
            crawl(full_url, visited, found_files, depth=depth + 1)

def run_crawler() -> list[dict]:
    """Entry point: crawl toàn bộ LIST_PAGES, trả về danh sách file tìm được."""
    visited = set()
    found_files = []

    for page in LIST_PAGES:
        start_url = BASE_URL + page
        logger.info(f"Bắt đầu crawl: {start_url}")
        crawl(start_url, visited, found_files, depth=0)

    logger.info(f"Hoàn tất. Tổng số file tìm được: {len(found_files)}")
    return found_files


if __name__ == "__main__":
    results = run_crawler()
    for item in results:
        print(item)