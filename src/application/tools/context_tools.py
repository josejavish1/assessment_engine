from __future__ import annotations

# --- START OF BUSINESS LOGIC ---
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
    """
    Realiza una búsqueda de élite en Google Search para obtener información estratégica.
    Autenticación dual: Intenta usar Cuenta de Servicio (OAuth2) o API Key.
    """
    _log_trace(
        f"Ejecutando Búsqueda de Élite Google (Tier 1): {query} (Domains: {authority_domains})"
    )

    cse_id = os.environ.get("GOOGLE_CSE_ID")
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    sa_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

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
        # ÉLITE: Intentar obtener token de la Cuenta de Servicio para bypass de políticas
        if sa_path and os.path.exists(sa_path):
            try:
                from google.auth.transport.requests import Request
                from google.oauth2 import service_account

                scopes = ["https://www.googleapis.com/auth/cloud-platform"]
                creds = service_account.Credentials.from_service_account_file(
                    sa_path, scopes=scopes
                )
                creds.refresh(Request())
                headers["Authorization"] = f"Bearer {creds.token}"
                _log_trace("Uso de Token OAuth2 de Cuenta de Servicio detectado.")
            except Exception as e_auth:
                _log_trace(
                    f"No se pudo obtener token OAuth2: {e_auth}. Usando API Key como fallback."
                )
                if api_key:
                    params["key"] = api_key
        elif api_key:
            params["key"] = api_key
        else:
            return "ERROR: No hay credenciales (SA o API Key) para Google Search."

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
    """
    Realiza una búsqueda de élite soberana usando el motor de Vertex AI Search de Google Cloud.
    Ideal para obtener información estratégica y noticias corporativas verificadas.
    """
    _log_trace(
        f"Ejecutando Búsqueda Soberana Vertex AI Search: {query} (Domains: {authority_domains})"
    )

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "sub403o4u0q5")
    location = "global"
    # El Data Store ID para búsqueda en internet pública en Vertex AI
    # Por defecto, usamos el motor de búsqueda general
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

        # Construir query con filtrado
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
        # Fallback a la API de búsqueda estándar pero bien autenticada
        return search_google_tier1(query, authority_domains)


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
    ]
