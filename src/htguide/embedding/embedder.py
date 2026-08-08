import json

import chromadb
import ollama

from htguide.utils.logger import get_logger
from htguide.utils.paths import CHROMA_DIR, DATA_PROCESSED_DIR

logger = get_logger(__name__)

EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "htech_regulations"
BATCH_LOG_EVERY = 20


def load_chunks() -> list[dict]:
    chunks_path = DATA_PROCESSED_DIR / "chunks.json"
    return json.loads(chunks_path.read_text(encoding="utf-8"))


def embed_text(text: str) -> list[float]:
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


def run_embedder() -> dict:
    chunks = load_chunks()

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    existing_ids = set(collection.get()["ids"]) if collection.count() > 0 else set()

    success, skipped, failed = 0, 0, 0

    for i, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]

        if chunk_id in existing_ids:
            skipped += 1
            continue

        try:
            embedding = embed_text(chunk["text"])
        except Exception as e:
            logger.warning(f"Lỗi embedding {chunk_id}: {e}")
            failed += 1
            continue

        collection.add(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[chunk["text"]],
            metadatas=[{"source_file": chunk["source_file"], "method": chunk["method"]}],
        )
        success += 1

        if (i + 1) % BATCH_LOG_EVERY == 0:
            logger.info(f"Đã xử lý {i + 1}/{len(chunks)} chunks...")

    logger.info(
        f"Hoàn tất embedding. Thành công: {success}, Bỏ qua (đã có): {skipped}, "
        f"Lỗi: {failed}. Tổng trong collection: {collection.count()}"
    )
    return {"success": success, "skipped": skipped, "failed": failed}


if __name__ == "__main__":
    run_embedder()
