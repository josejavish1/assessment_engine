from __future__ import annotations

import ast
import time
from typing import Any

from duckduckgo_search import DDGS

from assessment_engine.scripts.lib.runtime_paths import ROOT

TRACE_FILE = ROOT / "working" / "live_trace.txt"


def _log_trace(message: str) -> None:
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")


def search_internet_best_practices(query: str) -> str:
    """
    Searches the internet for state-of-the-art (SOTA) best practices, current tools, and industry standards
    related to the query. Use this to ensure your proposed plans align with world-class engineering patterns.

    Args:
        query: The search query, e.g., 'GitHub Actions PR reconciliation best practices security 2026'.
    """
    _log_trace(f"Investigando SOTA en Internet: {query}")
    try:
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No se encontraron resultados en internet."

        output = ["--- RESULTADOS DE BÚSQUEDA WEB ---"]
        for idx, res in enumerate(results, 1):
            output.append(f"\n{idx}. {res.get('title', '')}")
            output.append(f"Resumen: {res.get('body', '')}")
        return "\n".join(output)
    except Exception as e:
        return f"Error al buscar en internet: {e}"


def inspect_module(file_path: str) -> str:
    """
    Parses a Python file using the abstract syntax tree (AST) and returns a structural skeleton
    containing all classes, methods, functions, and their docstrings.
    Use this to understand what a file does without reading its entire source code.

    Args:
        file_path: The relative path to the python file from the repository root.
    """
    _log_trace(f"Inspeccionando AST del módulo: {file_path}")
    path = ROOT / file_path
    if not path.exists():
        return f"Error: File '{file_path}' not found."
    if not path.suffix == ".py":
        return f"Error: '{file_path}' is not a python file."

    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception as e:
        return f"Error parsing '{file_path}': {e}"

    lines = [f"--- SKELETON OF {file_path} ---"]
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            lines.append(f"def {node.name}(...):")
            doc = ast.get_docstring(node)
            if doc:
                lines.append(f'    """{doc.splitlines()[0]}..."""')
        elif isinstance(node, ast.ClassDef):
            lines.append(f"class {node.name}:")
            doc = ast.get_docstring(node)
            if doc:
                lines.append(f'    """{doc.splitlines()[0]}..."""')
            for sub_node in node.body:
                if isinstance(sub_node, ast.FunctionDef) or isinstance(
                    sub_node, ast.AsyncFunctionDef
                ):
                    lines.append(f"    def {sub_node.name}(...):")

    return "\n".join(lines)


def list_architecture_docs() -> str:
    """
    Lists all available markdown documentation files in the repository.
    Use this to find relevant documentation to read.
    """
    _log_trace("Explorando el índice de documentación del repositorio...")
    docs_dir = ROOT / "docs"
    if not docs_dir.exists():
        return "No docs folder found."

    files = list(docs_dir.rglob("*.md"))
    lines = ["Available documentation files:"]
    for f in files:
        lines.append(f"- {f.relative_to(ROOT)}")
    return "\n".join(lines)


def read_doc_file(file_path: str) -> str:
    """
    Reads the full content of a documentation markdown file.

    Args:
        file_path: The relative path to the markdown file from the repository root.
    """
    _log_trace(f"Leyendo documento de arquitectura: {file_path}")
    path = ROOT / file_path
    if not path.exists():
        return f"Error: File '{file_path}' not found."

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"


def get_context_tools() -> list[Any]:
    return [
        inspect_module,
        list_architecture_docs,
        read_doc_file,
        search_internet_best_practices,
    ]
