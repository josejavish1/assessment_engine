# core/chassis/introspection.py

import os
import ast
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

try:
    from assessment_engine.infrastructure.domain_compiler_matrix import CAPABILITY_TAXONOMY_MATRIX
except ImportError:
    CAPABILITY_TAXONOMY_MATRIX: Dict[str, List[str]] = {}


class SoverikIntrospectionEngine:
    """Live catalog introspection and semantic capability search engine."""

    def __init__(self, base_path: str = "core") -> None:
        self.base_path = base_path
        self.catalog: Dict[str, List[Dict[str, Any]]] = {
            "primitives": [],
            "components": [],
            "routers": []
        }

    def build_catalog(self) -> Dict[str, List[Dict[str, Any]]]:
        """Build live catalog by scanning system paths."""
        self.catalog["primitives"] = self._index_primitives(os.path.join(self.base_path, "primitives"))
        self.catalog["components"] = self._index_components(os.path.join(self.base_path, "components"))
        self.catalog["routers"] = self._index_routers(os.path.join(self.base_path, "routers"))
        return self.catalog

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search capabilities semantically in catalog."""
        results: List[Dict[str, Any]] = []
        for category, items in self.catalog.items():
            self._search_in_category(category, items, query, results)
        return sorted(results, key=lambda x: float(x["score"]), reverse=True)

    def _search_in_category(self, category: str, items: List[Dict[str, Any]], query: str, results: List[Dict[str, Any]]) -> None:
        """Search within a specific catalog category."""
        for item in items:
            score = self._match_capability(item["name"], item["meta"], query)
            if score > 0:
                results.append({"category": category, "item": item, "score": score})

    def _index_primitives(self, path: str) -> List[Dict[str, Any]]:
        """Index genome primitives."""
        return self._scan_and_extract(path, "primitive")

    def _index_components(self, path: str) -> List[Dict[str, Any]]:
        """Index UI and logical visual components."""
        return self._scan_and_extract(path, "component")

    def _index_routers(self, path: str) -> List[Dict[str, Any]]:
        """Index routers and API endpoints."""
        return self._scan_and_extract(path, "router")

    def _scan_and_extract(self, path: str, kind: str) -> List[Dict[str, Any]]:
        """Scan directory and extract AST declarations."""
        results: List[Dict[str, Any]] = []
        try:
            for root, _, files in os.walk(path):
                results.extend(self._process_directory_files(root, files, kind))
        except Exception as e:
            logger.debug(f"Error scanning directory {path}: {e}")
        return results

    def _process_directory_files(self, root: str, files: List[str], kind: str) -> List[Dict[str, Any]]:
        """Process files within target directory."""
        results: List[Dict[str, Any]] = []
        for file in files:
            fpath = os.path.join(root, file)
            if file.endswith(".py"):
                results.extend(self._extract_ast_nodes(fpath, kind))
            elif file.endswith((".tsx", ".ts")) and not file.endswith(".d.ts"):
                name = file.replace(".tsx", "").replace(".ts", "")
                results.append({"name": name, "meta": {"doc": f"Visual Component: {name}", "kind": kind, "file": fpath}})
        return results

    def _extract_ast_nodes(self, filepath: str, kind: str) -> List[Dict[str, Any]]:
        """Parse Python source file and extract AST nodes."""
        items: List[Dict[str, Any]] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for node in tree.body:
                self._process_ast_node(node, filepath, kind, items)
        except Exception as e:
            logger.debug(f"AST parse error in {filepath}: {e}")
        return items

    def _process_ast_node(self, node: ast.stmt, filepath: str, kind: str, items: List[Dict[str, Any]]) -> None:
        """Process an individual AST statement node."""
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            doc = ast.get_docstring(node) or ""
            items.append({
                "name": node.name,
                "meta": {"doc": doc, "kind": kind, "file": filepath}
            })

    def _match_capability(self, name: str, meta: Dict[str, Any], query: str) -> float:
        """Evaluate relevance of a capability against query."""
        score = 0.0
        try:
            q_lower = query.lower()
            if q_lower in name.lower():
                score += 0.5
            if q_lower in str(meta.get("doc", "")).lower():
                score += 0.3
            
            score += self._match_taxonomy(name, q_lower)
        except Exception as e:
            logger.debug(f"Match error for {name}: {e}")
        return score

    def _match_taxonomy(self, name: str, q_lower: str) -> float:
        """Evaluate taxonomy relevance using capability matrix."""
        score = 0.0
        for intent, mapped_items in CAPABILITY_TAXONOMY_MATRIX.items():
            if q_lower in str(intent).lower() and name in mapped_items:
                score += 1.0
                break
        return score
