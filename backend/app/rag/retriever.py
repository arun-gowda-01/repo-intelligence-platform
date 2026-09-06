"""
Thin layer on top of the vector store: takes a natural-language
question, retrieves the top-k most relevant code chunks, and formats
them as citation-ready results (file path + line range + code).

This is deliberately kept separate from LLM answer synthesis
(answer_generator.py, added when you plug in an API key) — retrieval
quality can and should be evaluated on its own, independent of
whether the LLM writes a good sentence about it.
"""
from app.rag.vector_store import query as vector_query


def retrieve(question: str, top_k: int = 5) -> list[dict]:
    results = vector_query(question, top_k=top_k)

    formatted = []
    for r in results:
        meta = r["metadata"]
        formatted.append({
            "file_path": meta["file_path"],
            "unit_name": meta["unit_name"],
            "kind": meta["kind"],
            "lines": f"{meta['start_line']}-{meta['end_line']}",
            "code": r["text"],
            "similarity_distance": r["distance"],
        })
    return formatted
