"""
Given a bug report written in plain English, retrieve candidate code
chunks (same vector search as RAG) and ask Gemini to reason about which
ones are most likely related to the root cause. This is a second,
separately-evaluated use case for the same retrieval infrastructure.
"""
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY
from app.rag.retriever import retrieve

_client = None
_MODEL_NAME = "gemini-3.6-flash"

_SYSTEM_PROMPT = """You are a debugging assistant. You will be given:
1. A bug report or issue description written by a user
2. A set of code snippets retrieved as potentially relevant, each with file path and line range

Task:
- Identify which snippet(s), if any, most likely relate to the root cause of the described bug.
- Explain your reasoning in plain terms: what in the code could produce the described symptom.
- Rank the candidates from most to least likely, with a one-line justification each.
- If none of the snippets seem relevant, say so explicitly rather than forcing a match."""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY not set. Copy .env.example to .env and add your key "
                "(get one free at https://aistudio.google.com)."
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def _format_candidates(results: list[dict]) -> str:
    blocks = []
    for r in results:
        blocks.append(
            f"File: {r['file_path']}\n"
            f"Function/Class: {r['unit_name']} (lines {r['lines']})\n"
            f"```\n{r['code']}\n```"
        )
    return "\n\n".join(blocks)


def localize_issue(issue_text: str, top_k: int = 5) -> dict:
    """
    Retrieve candidate code for a bug report and get the LLM's reasoning
    about which candidates are most likely the root cause.
    Returns both the raw candidates (for your own evaluation) and the
    LLM's explanation (for the user-facing answer).
    """
    candidates = retrieve(issue_text, top_k=top_k)

    if not candidates:
        return {
            "issue": issue_text,
            "candidates": [],
            "analysis": "No code was found — has a repository been ingested yet?",
        }

    client = _get_client()
    candidates_text = _format_candidates(candidates)

    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=f"Issue description: {issue_text}\n\nCandidate snippets:\n{candidates_text}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            max_output_tokens=1200,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )

    return {
        "issue": issue_text,
        "candidates": candidates,
        "analysis": response.text,
    }
