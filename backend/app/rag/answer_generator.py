"""
Takes the raw retrieved chunks from retriever.py and turns them into a
readable answer with citations, using Gemini. This is deliberately a
thin, separate layer on top of retrieval — retrieval quality (which
chunks came back) and generation quality (how well the LLM writes about
them) are two different things to evaluate independently.
"""
from google import genai
from google.genai import types

from app.config import GEMINI_API_KEY

_client = None

# Free-tier-eligible model as of writing. If Google renames/deprecates
# this, check https://ai.google.dev/gemini-api/docs/models for the
# current free Flash-tier model name and swap it in below.
_MODEL_NAME = "gemini-3.6-flash"

_SYSTEM_PROMPT = """You are a code assistant answering questions about a specific codebase.
You will be given:
1. A user question about the codebase
2. A set of retrieved code snippets, each labeled with its file path and line range

Rules:
- Answer ONLY using the provided snippets. If the answer isn't in them, say so clearly.
- Always cite the specific file path and function/line range for every claim you make.
- Be concise: 2-5 sentences plus code references, not a full essay.
- If multiple snippets are relevant, synthesize them into one coherent answer rather than listing them separately.
- Never invent file paths, function names, or line numbers that weren't in the provided snippets."""


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


def _format_snippets(results: list[dict]) -> str:
    """Turn retriever.py's output into the text block the prompt expects."""
    blocks = []
    for r in results:
        blocks.append(
            f"File: {r['file_path']}\n"
            f"Function/Class: {r['unit_name']} (lines {r['lines']})\n"
            f"```\n{r['code']}\n```"
        )
    return "\n\n".join(blocks)


def generate_answer(question: str, retrieved_results: list[dict]) -> str:
    """Synthesize a cited answer from retrieved code chunks."""
    if not retrieved_results:
        return "I couldn't find any relevant code for this question in the ingested repository."

    client = _get_client()
    snippets_text = _format_snippets(retrieved_results)

    response = client.models.generate_content(
        model=_MODEL_NAME,
        contents=f"Retrieved snippets:\n{snippets_text}\n\nUser question: {question}",
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            max_output_tokens=1024,
            thinking_config=types.ThinkingConfig(thinking_level="low"),
        ),
    )
    return response.text
