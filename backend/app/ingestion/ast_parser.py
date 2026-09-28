"""
Parses Python source files using the built-in `ast` module and extracts
a structured representation: every function/class, its source code,
docstring, line range, and the module's imports.

We use Python's built-in `ast` (not tree-sitter) for Stage 1 to keep setup
simple — no extra grammar installs. tree-sitter gets added when we support
JavaScript/TypeScript in a later stage.
"""
import ast
import os
from dataclasses import dataclass, field


@dataclass
class CodeUnit:
    """One function or class extracted from a file."""
    name: str
    kind: str          # "function" or "class"
    file_path: str
    start_line: int
    end_line: int
    source: str
    docstring: str | None = None


@dataclass
class ParsedFile:
    file_path: str
    imports: list[str] = field(default_factory=list)
    units: list[CodeUnit] = field(default_factory=list)


def _get_source_segment(source_lines: list[str], node: ast.AST) -> str:
    """Extract the exact source text for a given AST node using its line numbers."""
    start = node.lineno - 1
    end = node.end_lineno  # end_lineno is inclusive, and slicing is exclusive-at-end
    return "\n".join(source_lines[start:end])


def parse_file(file_path: str) -> ParsedFile:
    """
    Parse a single .py file into a ParsedFile containing its imports
    and every top-level (and nested) function/class definition.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    source_lines = source.splitlines()

    tree = ast.parse(source, filename=file_path)
    parsed = ParsedFile(file_path=file_path)

    for node in ast.walk(tree):
        # Track imports so we can build the dependency graph later
        if isinstance(node, ast.Import):
            for alias in node.names:
                parsed.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            parsed.imports.append(node.module)

        # Extract functions and classes as CodeUnits
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parsed.units.append(CodeUnit(
                name=node.name,
                kind="function",
                file_path=file_path,
                start_line=node.lineno,
                end_line=node.end_lineno,
                source=_get_source_segment(source_lines, node),
                docstring=ast.get_docstring(node),
            ))
        elif isinstance(node, ast.ClassDef):
            parsed.units.append(CodeUnit(
                name=node.name,
                kind="class",
                file_path=file_path,
                start_line=node.lineno,
                end_line=node.end_lineno,
                source=_get_source_segment(source_lines, node),
                docstring=ast.get_docstring(node),
            ))

    return parsed


def parse_repository(repo_path: str, exclude_tests: bool = True) -> list[ParsedFile]:
    """
    Walk a directory tree and parse every .py file found.
    Skips common noise directories (venv, node_modules, .git, etc).

    exclude_tests: when True (the default), also skips test files and
    test directories. This matters for RAG retrieval quality — test
    function names (e.g. test_set_basicauth) tend to contain the same
    keywords a user's question would use, so they out-rank the actual
    implementation in semantic search unless filtered out. Set to False
    if you specifically want tests included (e.g. a future "find
    existing tests for this function" feature).
    """
    SKIP_DIRS = {".git", "venv", ".venv", "node_modules", "__pycache__", "dist", "build"}
    TEST_DIRS = {"tests", "test"}
    parsed_files = []

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if exclude_tests:
            dirs[:] = [d for d in dirs if d not in TEST_DIRS]
        for filename in files:
            if not filename.endswith(".py"):
                continue
            if exclude_tests and (filename.startswith("test_") or filename.endswith("_test.py")):
                continue
            full_path = os.path.join(root, filename)
            try:
                parsed_files.append(parse_file(full_path))
            except SyntaxError:
                # Skip files that don't parse (e.g. Python 2 code, corrupted files)
                continue

    return parsed_files
