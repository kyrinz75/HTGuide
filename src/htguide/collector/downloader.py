import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_RAW_DIR, DOCX_DIR

load_dotenv()
logger = get_logger(__name__)

USER_AGENT = os.getenv("USER_AGENT")
BASE_URL = os.getenv("BASE_URL")
HEADERS = {
    "User-Agent": USER_AGENT,
    "Referer": BASE_URL,
}

CONTENT_TYPE_MAP = {
    "application/pdf": (".pdf", DATA_RAW_DIR),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": (".docx", DOCX_DIR),
    "application/msword": (".doc", DOCX_DIR),
}

AMBIGUOUS_TYPES = {"application/force-download", "application/octet-stream"}


def guess_extension_from_disposition(res: requests.Response) -> str | None:
    """Khi Content-Type không rõ ràng, thử đoán đuôi file từ Content-Disposition header."""
    disposition = res.headers.get("Content-Disposition", "")
    match = re.search(r'filename="?([^";]+)"?', disposition)
    if match:
        filename = match.group(1)
        for ext in (".pdf", ".docx", ".doc"):
            if filename.lower().endswith(ext):
                return ext
    return None

def safe_filename(name: str, fallback: str) -> str:
    """Loại bỏ ký tự không hợp lệ cho tên file, dùng fallback nếu tên rỗng."""
    name = name.strip() or fallback
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name[:200]
def download_file(item: dict) -> dict | None:
    url = item["url"]
    filename_hint = item["filename"]

    try:
        res = requests.get(url, headers=HEADERS, stream=True, timeout=20)
        res.raise_for_status()
    except requests.RequestException as e:
        logger.warning(f"Không tải được {url}: {e}")
        return None

    content_type = res.headers.get("Content-Type", "").split(";")[0].strip()

    if content_type in CONTENT_TYPE_MAP:
        ext, target_dir = CONTENT_TYPE_MAP[content_type]
    elif content_type in AMBIGUOUS_TYPES:
        # Content-Type không rõ ràng -> thử đoán qua Content-Disposition hoặc mặc định coi là PDF
        guessed_ext = guess_extension_from_disposition(res)
        if guessed_ext in (".docx", ".doc"):
            ext, target_dir = guessed_ext, DOCX_DIR
        else:
            ext, target_dir = ".pdf", DATA_RAW_DIR  # mặc định coi là PDF vì đa số văn bản trường là PDF
        logger.info(f"Content-Type mơ hồ ({content_type}) cho {url}, đoán là {ext}")
    else:
        logger.warning(f"Bỏ qua {url} — Content-Type không hợp lệ: {content_type}")
        return None

    base_name = safe_filename(filename_hint, fallback=url.split("/")[-1])
    if not base_name.lower().endswith(ext):
        base_name += ext

    target_path = target_dir / base_name

    counter = 1
    while target_path.exists():
        stem = Path(base_name).stem
        target_path = target_dir / f"{stem}_{counter}{ext}"
        counter += 1

    with open(target_path, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.info(f"Đã tải: {target_path.name}")
    return {"filename": target_path.name, "url": url, "path": str(target_path)}

def run_downloader(found_files: list[dict]) -> list[dict]:
    downloaded = []
    for item in tqdm(found_files, desc="Đang tải file"):
        result = download_file(item)
        if result:
            downloaded.append(result)

    logger.info(f"Hoàn tất tải. Thành công: {len(downloaded)}/{len(found_files)}")
    return downloaded


if __name__ == "__main__":
    from htguide.collector.crawler import run_crawler

    files = run_crawler()
    run_downloader(files)