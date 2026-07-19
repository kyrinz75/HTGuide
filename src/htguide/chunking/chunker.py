import json
import re

from htguide.utils.logger import get_logger
from htguide.utils.paths import DATA_INTERIM_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

ARTICLE_PATTERN = re.compile(r"(?m)^(Điều\s+\d+[.:])")

OVERLAP_CHARS = 200
MAX_CHUNK_CHARS = 3000
FALLBACK_CHUNK_CHARS = 1500
FALLBACK_OVERLAP_CHARS = 200
MIN_CHUNK_CHARS = 150  # dưới ngưỡng này, gộp vào chunk liền kề


def split_by_article(text: str) -> list[str]:
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
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if c]


def split_long_chunk(chunk: str, size: int, overlap: int) -> list[str]:
    if len(chunk) <= size:
        return [chunk]
    return split_fixed_size(chunk, size, overlap)


def add_overlap_between_chunks(chunks: list[str], overlap: int) -> list[str]:
    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            result.append(chunk)
        else:
            prev_tail = chunks[i - 1][-overlap:]
            result.append(f"[...{prev_tail}]\n\n{chunk}")
    return result


def merge_short_chunks(chunks: list[str], min_chars: int) -> list[str]:
    """Gộp các chunk quá ngắn (vd: chỉ có chữ ký, tiêu đề rời) vào chunk liền kề."""
    if not chunks:
        return chunks

    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if len(chunk) < min_chars:
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)

    if len(merged) > 1 and len(merged[0]) < min_chars:
        merged[1] = merged[0] + "\n\n" + merged[1]
        merged.pop(0)

    return merged


def chunk_text(text: str, source_file: str) -> list[dict]:
    article_chunks = split_by_article(text)

    if article_chunks:
        expanded = []
        for c in article_chunks:
            expanded.extend(split_long_chunk(c, MAX_CHUNK_CHARS, OVERLAP_CHARS))
        expanded = merge_short_chunks(expanded, MIN_CHUNK_CHARS)
        final_chunks = add_overlap_between_chunks(expanded, OVERLAP_CHARS)
        method = "article"
    else:
        raw_chunks = split_fixed_size(text, FALLBACK_CHUNK_CHARS, FALLBACK_OVERLAP_CHARS)
        final_chunks = merge_short_chunks(raw_chunks, MIN_CHUNK_CHARS)
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
    txt_files = sorted(DATA_INTERIM_DIR.glob("*.txt"))
    all_chunks = []
    article_method_count, fixed_method_count = 0, 0
    dropped_count = 0

    for txt_path in txt_files:
        text = txt_path.read_text(encoding="utf-8")
        chunks = chunk_text(text, source_file=txt_path.stem)

        # Loại chunk quá ngắn không gộp được (thường là file gần như rỗng nội dung)
        kept_chunks = [c for c in chunks if len(c["text"]) >= MIN_CHUNK_CHARS]
        dropped_count += len(chunks) - len(kept_chunks)

        all_chunks.extend(kept_chunks)

        if kept_chunks and kept_chunks[0]["method"] == "article":
            article_method_count += 1
        elif kept_chunks:
            fixed_method_count += 1
        else:
            logger.warning(f"{txt_path.name}: toàn bộ chunk bị loại do quá ngắn")

        logger.info(f"{txt_path.name}: {len(kept_chunks)} chunks giữ lại")

    output_path = DATA_PROCESSED_DIR / "chunks.json"
    output_path.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(
        f"Hoàn tất chunking. Tổng chunk: {len(all_chunks)} từ {len(txt_files)} file "
        f"(theo Điều: {article_method_count} file, fixed-size: {fixed_method_count} file, "
        f"đã loại: {dropped_count} chunk quá ngắn)"
    )
    return {"total_chunks": len(all_chunks), "total_files": len(txt_files), "dropped": dropped_count}
if __name__ == "__main__":
    run_chunker()
