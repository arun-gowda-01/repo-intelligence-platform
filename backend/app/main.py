"""
FastAPI entrypoint. Two endpoints for Stage 1:

  POST /ingest   { "repo_path": "/path/to/local/repo" }
  GET  /query?q=Where is authentication implemented?

Run with:  uvicorn app.main:app --reload   (from inside backend/)
"""
from fastapi import FastAPI
from pydantic import BaseModel

from app.ingestion.pipeline import ingest_repository
from app.rag.retriever import retrieve

app = FastAPI(title="Repo Intelligence Platform — Stage 1")


class IngestRequest(BaseModel):
    repo_path: str


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Parse, graph, chunk, and embed a local repository."""
    summary = ingest_repository(req.repo_path)
    return {"status": "ok", "summary": summary}


@app.get("/query")
def query(q: str, top_k: int = 5):
    """Semantic search over the most recently ingested repository."""
    results = retrieve(q, top_k=top_k)
    return {"question": q, "results": results}


@app.get("/health")
def health():
    return {"status": "ok"}
