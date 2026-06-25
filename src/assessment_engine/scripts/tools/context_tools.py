from __future__ import annotations

#
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
    """Executes a web search for a given query and formats the top results.

    This function utilizes the `duckduckgo-search` library to perform a
    text-based search. It retrieves a maximum of five results, extracting the
    title and body snippet for each, and compiles them into a single formatted
    string.

    Args:
        query (str): The search term or phrase to be queried.

    Returns:
        str: A string containing the formatted search results, a no-results
            message, or an error message. Specifically, it returns one of the
            following:
            - A multi-line string with the top search results.
            - The literal string "No se encontraron resultados en internet." if
              the search yields no results.
            - A string detailing the error (e.g., "Error al buscar en internet:
              <exception_details>") if the search operation fails.
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
    """Generate a structural outline of a Python module from its source code.

    Parses a Python source file into an Abstract Syntax Tree (AST) to extract
    a high-level structural outline. The outline includes all top-level classes,
    functions, and asynchronous functions. For each class, its methods are also
    listed. The first line of the docstring is included for top-level
    definitions (classes and functions), but not for methods within classes.
    All function and method signatures are simplified to `(...)` to focus on
    the structure.

    Args:
        file_path: The path to the Python source file. The path is resolved
            relative to a predefined root directory.

    Returns:
        A string containing the structural skeleton of the module. If the file
        is not found, is not a valid Python file, or contains syntax errors
        that prevent parsing, a string containing an error message is returned.
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
    """List all markdown architecture documentation files in the repository.

    Recursively scans the 'docs' subdirectory within the project root for all
    files with a '.md' extension. The paths of the discovered files, relative
    to the project root, are compiled into a single, formatted string.

    Returns:
        A multi-line string listing the discovered markdown files, each
        prefixed with '- '. The list is preceded by a header. If the 'docs'
        directory is not found, the literal string "No docs folder found."
        is returned.
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
    r"""{'docstring': "Reads the content of a file relative to a predefined application root.\n\n    This function constructs an absolute path by joining a predefined root path\n    with the provided relative `file_path`. Instead of raising exceptions for\n    common I/O issues, it returns a descriptive error message as a string, making\n    it suitable for contexts where fault tolerance is preferred over program\n    termination.\n\n    Args:\n        file_path: The path to the target file, specified relative to the\n            application's root directory.\n\n    Returns:\n        The UTF-8 decoded content of the file as a string. If the file does not\n        exist or a read error occurs, a formatted string detailing the error\n        is returned."}."""
    _log_trace(f"Leyendo documento de arquitectura: {file_path}")
    path = ROOT / file_path
    if not path.exists():
        return f"Error: File '{file_path}' not found."

    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file '{file_path}': {e}"


def get_context_tools() -> list[Any]:
    """Return a list of available context-gathering tool functions."""
    return [
        inspect_module,
        list_architecture_docs,
        read_doc_file,
        search_internet_best_practices,
    ]
