# Stage 1: Ingestion + Dependency Graph + Repository RAG

## What this does
Point it at a local folder of Python code, and it will:
1. Parse every `.py` file (functions, classes, imports)
2. Build a dependency graph (what imports what)
3. Chunk each function/class and embed it
4. Let you ask natural-language questions and get back the most relevant code

A `sample_repo/` folder is included so you can test it immediately without
needing a real GitHub repo yet.

## Setup (run these once)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The first time you run it, `sentence-transformers` will download a small
model (~90MB) — this needs an internet connection once, then it's cached
locally.

## Run the server

```bash
# from inside backend/, with the venv activated
uvicorn app.main:app --reload
```

You should see it start on `http://127.0.0.1:8000`.

## Try it out

**1. Ingest the sample repo:**
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_path": "../sample_repo"}'
```
You should get back a summary: files parsed, functions found, dependency edges.

**2. Ask a question:**
```bash
curl "http://127.0.0.1:8000/query?q=Where is authentication implemented?"
```
You should get back the `authenticate_user` and `hash_password` functions
from `auth/login.py`, ranked by relevance.

**3. Try other questions:**
```bash
curl "http://127.0.0.1:8000/query?q=How are users looked up in the database?"
curl "http://127.0.0.1:8000/query?q=How do I compute an average?"
```

**4. Point it at a real repo:** clone any small Python project locally, then
`POST /ingest` with its path instead of `../sample_repo`.

## What's NOT done yet (next stages)
- No LLM synthesis yet — `/query` returns raw retrieved code, not a written
  answer. That's the next thing to add (`answer_generator.py`), once you
  have an Anthropic/OpenAI API key.
- No evaluation numbers yet — next step is hand-labeling 20-30
  (question, correct file) pairs against a real repo and measuring
  Recall@5 / MRR, per the PRD.
- Dependency graph is saved to `data/dependency_graph.json` but not used
  anywhere yet — that's for Stage 3 (Impact Analysis).
- JavaScript/TypeScript support isn't in yet — Python only for now.

## File-by-file: what each piece does (quick reference)

| File | Job |
|---|---|
| `app/ingestion/ast_parser.py` | Reads Python files, extracts every function/class + its exact source, plus import statements |
| `app/ingestion/dependency_graph.py` | Turns imports into a graph; answers "what depends on X?" |
| `app/ingestion/chunker.py` | Turns each function/class into one embeddable chunk with metadata |
| `app/ingestion/pipeline.py` | Runs the above three in order, saves the graph, stores chunks |
| `app/rag/embedder.py` | Turns text into vectors using a pretrained sentence-transformers model |
| `app/rag/vector_store.py` | Stores/searches those vectors using Chroma (local, file-based) |
| `app/rag/retriever.py` | Takes a question, returns the top-k most relevant code chunks |
| `app/main.py` | FastAPI app exposing `/ingest` and `/query` over HTTP |
