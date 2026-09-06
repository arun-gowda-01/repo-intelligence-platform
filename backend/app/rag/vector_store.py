"""
Wraps ChromaDB — a lightweight, file-based vector database. No server
or Docker needed for Stage 1; it persists to a local folder.

Later (production-hardening stage), we'll swap this for pgvector so
everything lives in one Postgres instance alongside your relational
data. Because this is behind a small interface (add/query), swapping
the backend later won't require touching the ingestion or RAG code.
"""
import chromadb

from app.ingestion.chunker import Chunk
from app.rag.embedder import embed_texts, embed_query

_PERSIST_DIR = "./data/chroma"
_COLLECTION_NAME = "code_chunks"

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=_PERSIST_DIR)
    return _client


def reset_collection():
    """Wipe and recreate the collection — useful when re-ingesting a repo."""
    client = get_client()
    try:
        client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass
    return client.create_collection(_COLLECTION_NAME)


def add_chunks(chunks: list[Chunk]) -> None:
    """Embed and store a list of chunks in the vector DB."""
    collection = reset_collection()
    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)

    collection.add(
        ids=[c.id for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[{
            "file_path": c.file_path,
            "unit_name": c.unit_name,
            "kind": c.kind,
            "start_line": c.start_line,
            "end_line": c.end_line,
        } for c in chunks],
    )


def query(text: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query and return the top_k most similar chunks, each with
    its metadata and a distance score (lower = more similar).
    """
    client = get_client()
    collection = client.get_collection(_COLLECTION_NAME)
    query_embedding = embed_query(text)

    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    output = []
    for i in range(len(results["ids"][0])):
        output.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return output
