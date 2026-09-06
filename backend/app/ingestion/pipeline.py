"""
The full Stage 1 ingestion pipeline: point it at a local repo path and
it parses every file, builds the dependency graph, chunks the code,
and stores everything in the vector DB. This is the function the
/ingest API endpoint calls.
"""
import json
import networkx as nx

from app.ingestion.ast_parser import parse_repository
from app.ingestion.dependency_graph import build_dependency_graph
from app.ingestion.chunker import build_chunks
from app.rag.vector_store import add_chunks

_GRAPH_PATH = "./data/dependency_graph.json"


def ingest_repository(repo_path: str) -> dict:
    """Runs the full pipeline and returns a summary of what was ingested."""
    parsed_files = parse_repository(repo_path)

    graph = build_dependency_graph(parsed_files, repo_root=repo_path)
    # Persist the graph as plain JSON (node-link format) so other parts
    # of the app (or Stage 3's impact analysis) can load it without
    # re-parsing the whole repo.
    graph_data = nx.node_link_data(graph)
    with open(_GRAPH_PATH, "w") as f:
        json.dump(graph_data, f, indent=2)

    chunks = build_chunks(parsed_files)
    add_chunks(chunks)

    return {
        "files_parsed": len(parsed_files),
        "functions_and_classes_found": len(chunks),
        "dependency_edges": graph.number_of_edges(),
        "graph_saved_to": _GRAPH_PATH,
    }
