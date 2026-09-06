"""
FastAPI entrypoint. Endpoints:

  POST /ingest          { "repo_path": "/path/to/local/repo" }
  GET  /query?q=...      raw retrieval only (no LLM) — useful for eval
  POST /ask              { "question": "..." } -> LLM-synthesized cited answer
  POST /localize-issue    { "issue_text": "..." } -> likely relevant code + reasoning
  GET  /health

Run with:  uvicorn app.main:app --reload   (from inside backend/)
"""
from fastapi import FastAPI
from pydantic import BaseModel

from app.ingestion.pipeline import ingest_repository
from app.rag.retriever import retrieve
from app.rag.answer_generator import generate_answer
from app.rag.issue_localizer import localize_issue

app = FastAPI(title="Repo Intelligence Platform — Stage 1")


class IngestRequest(BaseModel):
    repo_path: str


class AskRequest(BaseModel):
    question: str
    top_k: int = 5


class LocalizeRequest(BaseModel):
    issue_text: str
    top_k: int = 5


@app.post("/ingest")
def ingest(req: IngestRequest):
    """Parse, graph, chunk, and embed a local repository."""
    summary = ingest_repository(req.repo_path)
    return {"status": "ok", "summary": summary}


@app.get("/query")
def query(q: str, top_k: int = 5):
    """Raw semantic search only — no LLM call. Used by the eval script
    to measure retrieval quality independent of answer generation."""
    results = retrieve(q, top_k=top_k)
    return {"question": q, "results": results}


@app.post("/ask")
def ask(req: AskRequest):
    """Full RAG: retrieve relevant code, then have Claude write a cited answer."""
    results = retrieve(req.question, top_k=req.top_k)
    answer = generate_answer(req.question, results)
    return {"question": req.question, "answer": answer, "sources": results}


@app.post("/localize-issue")
def localize(req: LocalizeRequest):
    """Given a bug report, find likely relevant code and explain why."""
    return localize_issue(req.issue_text, top_k=req.top_k)


@app.get("/health")
def health():
    return {"status": "ok"}
