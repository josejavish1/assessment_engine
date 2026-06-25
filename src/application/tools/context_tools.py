from __future__ import annotations

#
import ast
import os
import time
from typing import Any

from infrastructure.runtime_paths import ROOT

TRACE_FILE = ROOT / "working" / "live_trace.txt"


def _log_trace(message: str) -> None:
    TRACE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')} - {message}\n")


def search_google_tier1(query: str, authority_domains: list[str] = None) -> str:
    """Executes a Google Custom Search API query and formats the results.

    Performs a search against the Google Custom Search API v1, retrieving up to 5
    results. This function requires the `GOOGLE_CSE_ID` and
    `GOOGLE_SEARCH_API_KEY` environment variables for configuration and
    authentication. If `authority_domains` are provided, the query is scoped to
    those specific sites using `site:` search operators.

    Args:
        query (str): The search phrase to submit to Google.
        authority_domains (list[str], optional): A list of domains to restrict
            the search to (e.g., 'example.com'). Defaults to None, indicating
            an unrestricted search.

    Returns:
        str: A formatted string of the top search results, each including a title,
            URL, and snippet. If no results are found, a specific notification
            string is returned. In case of configuration errors (e.g., missing
            environment variables) or API communication failures, a descriptive
            error message string is returned.
    """
    _log_trace(
        f"Ejecutando Búsqueda de Élite Google (Tier 1): {query} (Domains: {authority_domains})"
    )

    cse_id = os.environ.get("GOOGLE_CSE_ID")
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    if not cse_id:
        return "ERROR DE GOBERNANZA: GOOGLE_CSE_ID no configurado."

    try:
        import requests

        url = "https://www.googleapis.com/customsearch/v1"

        site_filter = ""
        if authority_domains:
            site_filter = (
                " (" + " OR ".join([f"site:{d}" for d in authority_domains]) + ")"
            )

        params = {"q": query + site_filter, "cx": cse_id, "num": 5}
        headers = {}

        if api_key:
            params["key"] = api_key
        else:
            return "ERROR: No hay API Key para Google Search."

        res = requests.get(url, params=params, headers=headers)
        res.raise_for_status()
        results = res.json().get("items", [])

        if not results:
            return f"No se encontraron resultados oficiales para: {query}."

        output = ["--- RESULTADOS OFICIALES GOOGLE SEARCH ---"]
        for idx, item in enumerate(results, 1):
            output.append(f"\n{idx}. {item.get('title')}")
            output.append(f"URL: {item.get('link')}")
            output.append(f"Snippet: {item.get('snippet')}")
        return "\n".join(output)
    except Exception as e:
        return (
            f"ERROR DEL SISTEMA OSINT: {e}. Basate exclusivamente en el Vault interno."
        )


def search_google_vertex_sovereign(
    query: str, authority_domains: list[str] = None
) -> str:
    r"""{'docstring': 'Executes a query against the Google Cloud Discovery Engine API.\n\n    This function constructs and sends a search request to a pre-configured\n    Discovery Engine data store. If `authority_domains` are specified, the\n    query is augmented with `site:` operators to constrain the search scope.\n\n    The function includes a fallback mechanism for resilience. If any exception\n    is encountered during the primary API call, it logs the error and delegates\n    the request to the `search_google_tier1` function, passing along the\n    original arguments.\n\n    Args:\n        query (str): The search term or question to execute.\n        authority_domains (list[str], optional): A list of domain names to which\n            the search should be restricted. Defaults to None.\n\n    Returns:\n        str: A formatted, newline-separated string containing up to five search\n            results, each with a title, URL, and snippet. If no results are\n            found, a corresponding message is returned. If the primary API call\n            fails, this will be the output of the fallback function.'}."""
    _log_trace(
        f"Ejecutando Búsqueda Soberana Vertex AI Search: {query} (Domains: {authority_domains})"
    )

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
    location = "global"
    # The unique identifier for the Vertex AI data store configured for public web search.
    # If a specialized search engine ID is not provided, fall back to the default general-purpose engine.
    search_engine_id = "default_search_engine"

    try:
        from google.cloud import discoveryengine_v1beta as discoveryengine

        client = discoveryengine.SearchServiceClient()

        serving_config = client.serving_config_path(
            project=project_id,
            location=location,
            data_store=search_engine_id,
            serving_config="default_config",
        )

        #
        full_query = query
        if authority_domains:
            full_query += (
                " (" + " OR ".join([f"site:{d}" for d in authority_domains]) + ")"
            )

        request = discoveryengine.SearchRequest(
            serving_config=serving_config,
            query=full_query,
            page_size=5,
        )

        response = client.search(request)

        output = ["--- RESULTADOS SOBERANOS VERTEX AI SEARCH ---"]
        count = 0
        for result in response.results:
            count += 1
            data = result.document.derived_struct_data
            title = data.get("title", "Sin título")
            link = data.get("link", "Sin URL")
            snippet = data.get("snippets", [{}])[0].get("snippet", "Sin resumen")
            output.append(f"\n{count}. {title}")
            output.append(f"URL: {link}")
            output.append(f"Resumen: {snippet}")

        if count == 0:
            return f"No se encontraron resultados soberanos para: {query}. Intenta una consulta más general."

        return "\n".join(output)
    except Exception as e:
        _log_trace(
            f"Fallo en Vertex AI Search: {e}. Intentando fallback a Google Search API estándar..."
        )
        # Fallback to the standard search API if the primary search mechanism fails, preserving the authentication context.
        return search_google_tier1(query, authority_domains)


def inspect_module(file_path: str) -> str:
    """Generates a structural summary of a Python module using Abstract Syntax Trees.

    Parses the Python source code at the given path to extract its high-level
    structure. The summary includes top-level functions, classes, and any methods
    defined directly within those classes. For each extracted element, the first
    line of its docstring is included to provide context.

    File system and parsing errors are handled internally, returning a descriptive
    error message instead of raising an exception.

    Args:
        file_path (str): The path to the target Python file, typically relative
            to a project root.

    Returns:
        str: A multi-line string representing the module's structure. If the
            file cannot be found, is not a Python file, or contains syntax
            errors, a string detailing the specific error is returned instead.
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
    r"""{'docstring': 'List all markdown files within the repository\'s `docs/` directory.\n\n    Recursively scans the project\'s `docs/` directory for all files with a\n    `.md` extension. The discovered file paths are formatted relative to the\n    project root. This utility is intended for discovery operations, such as\n    populating content for analysis or retrieval.\n\n    Returns:\n        A newline-separated string listing the relative paths of all located\n        markdown files, prefixed with a header. If the `docs/` directory does\n        not exist, returns the literal string "No docs folder found.".'}."""
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
    """Read the content of a file from a predefined root directory.

    Constructs an absolute path by joining a predefined root directory path
    with the provided relative `file_path`. This function encapsulates file
    I/O operations, specifically handling cases where the file does not exist
    or cannot be read. Instead of raising exceptions, it returns a formatted
    error string to the caller.

    Args:
        file_path (str): The path to the target file, relative to a
            pre-configured root directory.

    Returns:
        str: The UTF-8 decoded content of the file. A formatted error string
            is returned if the file is not found or if a read error occurs.
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
    """Return a list of available context tool functions."""
    return [
        inspect_module,
        list_architecture_docs,
        read_doc_file,
    ]
