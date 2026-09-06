"""
Wraps a sentence-transformers model to turn text (code or a natural
language query) into a vector. Using the SAME model for both code
chunks and user queries is what makes semantic search work — they
need to land in the same vector space to be comparable.

Model choice: 'all-MiniLM-L6-v2' is small, fast on CPU, and good enough
to validate the pipeline end-to-end. In Stage 2, when we train the bug
classifier, we'll evaluate whether a code-specific model (e.g.
'flax-sentence-embeddings/st-codesearch-distilroberta-base' or
CodeBERT-based embeddings) improves retrieval accuracy@k over this
baseline — that comparison itself is a good thing to report.
"""
from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns a list of vectors (as plain lists)."""
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return embeddings.tolist()


def embed_query(query: str) -> list[float]:
    """Embed a single query string (e.g. a user's question)."""
    return embed_texts([query])[0]
