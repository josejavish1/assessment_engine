"""
Codebase AST Graph Primitive (Codebase Memory Engine).
Extracts symbol hierarchies, dependencies, routes, and call graphs
to prevent LLM context rot without re-reading entire file contents.
"""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger("assessment_engine.infrastructure.primitives.codebase_ast")


def extract_python_symbols(file_path: Path) -> dict[str, Any]:
    """Extracts classes, functions, async functions, and imports from a Python file."""
    symbols: dict[str, Any] = {
        "classes": [],
        "functions": [],
        "routes": [],
        "imports": []
    }
    try:
        content = file_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                symbols["classes"].append({
                    "name": node.name,
                    "methods": methods,
                    "line": node.lineno
                })
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decorators = []
                for dec in node.decorator_list:
                    dec_repr = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                    decorators.append(dec_repr)
                    if any(verb in dec_repr for verb in ["get(", "post(", "put(", "delete(", "patch("]):
                        symbols["routes"].append({
                            "endpoint": dec_repr,
                            "handler": node.name,
                            "line": node.lineno
                        })
                symbols["functions"].append({
                    "name": node.name,
                    "decorators": decorators,
                    "line": node.lineno
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    symbols["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                for alias in node.names:
                    symbols["imports"].append(f"{mod}.{alias.name}")

    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
        logger.debug(f"AST extract note on {file_path}: {ex}")

    return symbols


def extract_ts_js_symbols(file_path: Path) -> dict[str, Any]:
    """Extracts React components, exports, and imports from TS/TSX/JS files."""
    symbols: dict[str, Any] = {
        "components": [],
        "exports": [],
        "imports": []
    }
    try:
        content = file_path.read_text(encoding="utf-8")
        # Find imports
        for imp_match in re.finditer(r'import\s+(?:{[^}]+}|\w+|\*\s+as\s+\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', content):
            symbols["imports"].append(imp_match.group(1))

        # Find exported functions/components
        for fn_match in re.finditer(r'export\s+(?:default\s+)?(?:function|const)\s+([A-Za-z0-9_]+)', content):
            name = fn_match.group(1)
            if name[0].isupper():
                symbols["components"].append(name)
            symbols["exports"].append(name)

    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
        logger.debug(f"TS/JS extract note on {file_path}: {ex}")

    return symbols


def build_workspace_ast_graph(workspace_dir: Path) -> dict[str, Any]:
    """
    Constructs an in-memory structural graph of the entire workspace.
    Maps all symbols and dependencies across api/ and web/ or src/.
    """
    graph: dict[str, Any] = {
        "workspace": str(workspace_dir),
        "total_files": 0,
        "python_modules": {},
        "frontend_modules": {},
        "api_routes": []
    }

    if not workspace_dir.exists():
        return graph

    ignored_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}

    for path in workspace_dir.rglob("*"):
        if path.is_file() and not any(part in ignored_dirs for part in path.parts):
            rel_path = str(path.relative_to(workspace_dir))
            if path.suffix == ".py":
                graph["total_files"] += 1
                meta = extract_python_symbols(path)
                graph["python_modules"][rel_path] = meta
                for r in meta.get("routes", []):
                    graph["api_routes"].append({"file": rel_path, **r})
            elif path.suffix in (".ts", ".tsx", ".js", ".jsx"):
                graph["total_files"] += 1
                graph["frontend_modules"][rel_path] = extract_ts_js_symbols(path)

    return graph


def query_codebase_graph(workspace_dir: Path, query_symbol: str) -> dict[str, Any]:
    """
    Surgically queries the codebase AST graph for a symbol or dependency
    without needing to read and load full source files.
    """
    graph = build_workspace_ast_graph(workspace_dir)
    q = query_symbol.lower().strip()

    matches: dict[str, Any] = {
        "query": query_symbol,
        "matched_classes": [],
        "matched_functions": [],
        "matched_routes": [],
        "matched_components": [],
        "referencing_files": []
    }

    for fpath, data in graph["python_modules"].items():
        for cls_item in data["classes"]:
            if q in cls_item["name"].lower():
                matches["matched_classes"].append({"file": fpath, **cls_item})
        for fn_item in data["functions"]:
            if q in fn_item["name"].lower():
                matches["matched_functions"].append({"file": fpath, **fn_item})
        for imp in data["imports"]:
            if q in imp.lower():
                matches["referencing_files"].append({"file": fpath, "imports": imp})

    for r in graph["api_routes"]:
        if q in r["endpoint"].lower() or q in r["handler"].lower():
            matches["matched_routes"].append(r)

    for fpath, data in graph["frontend_modules"].items():
        for comp in data["components"]:
            if q in comp.lower():
                matches["matched_components"].append({"file": fpath, "component": comp})

    return matches
