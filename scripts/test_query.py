import sys

import chromadb
import ollama

from htguide.utils.paths import CHROMA_DIR

EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "htech_regulations"


def query_collection(query: str, n_results: int = 3):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = client.get_collection(COLLECTION_NAME)

    query_embedding = ollama.embeddings(model=EMBED_MODEL, prompt=query)["embedding"]
    results = collection.query(query_embeddings=[query_embedding], n_results=n_results)

    print(f"\nCâu hỏi: {query}\n{'=' * 60}")
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i]["source_file"]
        distance = results["distances"][0][i]
        print(f"\n--- Kết quả {i + 1} (nguồn: {source}, khoảng cách: {distance:.4f}) ---")
        print(doc[:400])
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_collection(" ".join(sys.argv[1:]))
    else:
        sample_queries = [
            "Điều kiện xét tốt nghiệp là gì?",
            "Quy định về đăng ký học phần",
            "Lịch thi học kỳ",
        ]
        for q in sample_queries:
            query_collection(q)
