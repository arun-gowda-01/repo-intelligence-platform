"""
Turns each CodeUnit (function/class) into a "chunk": a piece of text
to embed, plus metadata to show the user where it came from.

Why chunk per-function instead of fixed-size line chunks (e.g. every 50
lines)? Fixed-size chunking cuts functions in half at arbitrary points,
which destroys the semantic meaning of the code. Chunking per-function
keeps each chunk a complete, coherent unit — this is the single biggest
lever for good retrieval quality in code RAG.
"""
from dataclasses import dataclass

from app.ingestion.ast_parser import ParsedFile


@dataclass
class Chunk:
    id: str                # unique id, e.g. "auth/login.py::authenticate_user"
    text: str               # what gets embedded (docstring + source)
    file_path: str
    unit_name: str
    kind: str
    start_line: int
    end_line: int


def build_chunks(parsed_files: list[ParsedFile]) -> list[Chunk]:
    chunks = []
    for pf in parsed_files:
        for unit in pf.units:
            # unit.source already includes the docstring (it's extracted
            # from the exact source range of the function/class), so we
            # embed it as-is — no need to prepend the docstring separately.
            embed_text = unit.source

            chunks.append(Chunk(
                id=f"{unit.file_path}::{unit.name}",
                text=embed_text,
                file_path=unit.file_path,
                unit_name=unit.name,
                kind=unit.kind,
                start_line=unit.start_line,
                end_line=unit.end_line,
            ))
    return chunks
