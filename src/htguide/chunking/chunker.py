import json
import re

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

# Nhận diện "Điều 1.", "Điều 12.", v.v. ở đầu dòng
ARTICLE_PATTERN = re.compile(r"(?m)^(Điều\s+\d+[.:])")

OVERLAP_CHARS = 200       # số ký tự lấy từ cuối chunk trước, gắn vào đầu chunk sau
MAX_CHUNK_CHARS = 3000    # nếu 1 Điều quá dài, chia nhỏ tiếp
FALLBACK_CHUNK_CHARS = 1500  # kích thước chunk khi không có cấu trúc Điều
FALLBACK_OVERLAP_CHARS = 200


def split_by_article(text: str) -> list[str]:
    """Chia văn bản theo 'Điều X.', trả về list các đoạn (mỗi đoạn bắt đầu bằng 'Điều X.')."""
    matches = list(ARTICLE_PATTERN.finditer(text))
    if not matches:
        return []

    chunks = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunks.append(text[start:end].strip())
    return chunks


def split_fixed_size(text: str, size: int, overlap: int) -> list[str]:
    """Fallback: chia theo ký tự cố định có overlap, dùng cho văn bản không có cấu trúc Điều."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


def split_long_chunk(chunk: str, size: int, overlap: int) -> list[str]:
    """Nếu 1 Điều quá dài, chia nhỏ tiếp bằng fixed-size + overlap (giữ nguyên nội dung Điều)."""
    if len(chunk) <= size:
        return [chunk]
    return split_fixed_size(chunk, size, overlap)


def add_overlap_between_chunks(chunks: list[str], overlap: int) -> list[str]:
    """Gắn N ký tự cuối của chunk trước vào đầu chunk sau, giữ ngữ cảnh nối tiếp giữa các Điều."""
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            result.append(chunk)
        else:
            prev_tail = chunks[i - 1][-overlap:]
            result.append(f"[...{prev_tail}]\n\n{chunk}")
    return result


def chunk_text(text: str, source_file: str) -> list[dict]:
    """Chia 1 văn bản thành các chunk, ưu tiên theo cấu trúc Điều, fallback fixed-size nếu không có."""
    article_chunks = split_by_article(text)

    if article_chunks:
        # Chia nhỏ tiếp các Điều quá dài
        expanded = []
        for c in article_chunks:
            expanded.extend(split_long_chunk(c, MAX_CHUNK_CHARS, OVERLAP_CHARS))
        final_chunks = add_overlap_between_chunks(expanded, OVERLAP_CHARS)
        method = "article"
    else:
        raw_chunks = split_fixed_size(text, FALLBACK_CHUNK_CHARS, FALLBACK_OVERLAP_CHARS)
        final_chunks = raw_chunks
        method = "fixed_size"

    return [
        {
            "chunk_id": f"{source_file}::{i}",
            "source_file": source_file,
            "method": method,
            "text": chunk,
        }
        for i, chunk in enumerate(final_chunks)
    ]


def run_chunker() -> dict:
    """Quét toàn bộ .txt trong DATA_INTERIM_DIR, chunk, lưu ra 1 file JSON tổng hợp."""
    txt_files = sorted(DATA_INTERIM_DIR.glob("*.txt"))
    all_chunks = []
    article_method_count, fixed_method_count = 0, 0

    for txt_path in txt_files:
        text = txt_path.read_text(encoding="utf-8")
        chunks = chunk_text(text, source_file=txt_path.stem)
        all_chunks.extend(chunks)

        if chunks and chunks[0]["method"] == "article":
            article_method_count += 1
        else:
            fixed_method_count += 1

        logger.info(f"{txt_path.name}: {len(chunks)} chunks ({chunks[0]['method'] if chunks else 'empty'})")

    output_path = DATA_PROCESSED_DIR / "chunks.json"
    output_path.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(
        f"Hoàn tất chunking. Tổng chunk: {len(all_chunks)} từ {len(txt_files)} file "
        f"(theo Điều: {article_method_count} file, fixed-size: {fixed_method_count} file)"
    )
    return {"total_chunks": len(all_chunks), "total_files": len(txt_files)}


if __name__ == "__main__":
    run_chunker()