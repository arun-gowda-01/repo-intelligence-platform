"""
Builds a directed graph of file-level dependencies: an edge A -> B means
"file A imports something from module B". This is the structure Change
Impact Analysis (Stage 3) will traverse to find what else might break
when a file changes.
"""
import os
import networkx as nx

from app.ingestion.ast_parser import ParsedFile


def _module_name_from_path(file_path: str, repo_root: str) -> str:
    """Convert a file path like sample_repo/utils/db.py into a dotted
    module name like utils.db, so it can be matched against import statements."""
    rel_path = os.path.relpath(file_path, repo_root)
    rel_path = rel_path.replace(os.sep, ".")
    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]
    if rel_path.endswith(".__init__"):
        rel_path = rel_path[: -len(".__init__")]
    return rel_path


def build_dependency_graph(parsed_files: list[ParsedFile], repo_root: str) -> nx.DiGraph:
    """
    Returns a networkx DiGraph where:
      - nodes are module names (e.g. "auth.login", "utils.db")
      - edges represent "imports from" relationships
    Only edges to modules that actually exist in this repo are kept —
    external library imports (e.g. "hashlib") become isolated info we
    could track separately, but they're not part of the internal graph.
    """
    graph = nx.DiGraph()

    # First pass: register every file as a node
    module_names = {}
    for pf in parsed_files:
        mod_name = _module_name_from_path(pf.file_path, repo_root)
        module_names[pf.file_path] = mod_name
        graph.add_node(mod_name, file_path=pf.file_path)

    known_modules = set(module_names.values())

    # Second pass: add edges for imports that resolve to a module in this repo
    for pf in parsed_files:
        source_module = module_names[pf.file_path]
        for imported in pf.imports:
            # Match "utils.db" exactly, or the case where someone wrote
            # "from utils import db" (imported == "utils")
            matches = [m for m in known_modules if m == imported or m.startswith(imported + ".")]
            for match in matches:
                if match != source_module:
                    graph.add_edge(source_module, match)

    return graph


def get_impacted_modules(graph: nx.DiGraph, module_name: str) -> list[str]:
    """
    Given a module that changed, return every module that could be
    affected — i.e. every module that (directly or transitively)
    imports from it. Uses reverse graph traversal (ancestors).
    """
    if module_name not in graph:
        return []
    return list(nx.ancestors(graph, module_name))
