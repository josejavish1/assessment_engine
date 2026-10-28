"""
Polyglot RepoMap Primitive — GEMA 01 (DeepMind / Anthropic SOTA 2026).
Extracts definitions (def) and references (ref) from Python, TypeScript, and JavaScript.
Constructs a directed dependency graph and calculates Personalized PageRank to rank most relevant code symbols.
Packs compact repository topology within a strict token budget (default 1024 tokens).
"""

from __future__ import annotations

import ast
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

logger = logging.getLogger("assessment_engine.infrastructure.primitives.repomap")

TagType = Literal["def", "ref"]


@dataclass(frozen=True)
class CodeTag:
    rel_path: str
    name: str
    kind: TagType  # "def" (class, function) or "ref" (call, import)
    line: int


@dataclass
class RepoMapConfig:
    max_map_tokens: int = 1024
    damping_factor: float = 0.85
    supported_extensions: tuple[str, ...] = (".py", ".ts", ".js", ".tsx", ".jsx", ".html")
    excluded_dirs: tuple[str, ...] = (
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "node_modules",
        "dist",
        ".mypy_cache",
        ".pytest_cache",
        "research",
    )


class RepoMapPrimitive:
    """Provide a topological repository map for LLM semantic navigation. Use tag extraction and Personalized PageRank to rank files and symbols."""

    def __init__(self, config: Optional[RepoMapConfig] = None) -> None:
        self.config = config or RepoMapConfig()

    def extract_python_tags(self, root_dir: Path, py_file: Path) -> list[CodeTag]:
        """Extrae funciones, clases y llamadas mediante Python AST."""
        tags: list[CodeTag] = []
        try:
            rel_path = str(py_file.relative_to(root_dir))
            tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    tags.append(CodeTag(rel_path, node.name, "def", node.lineno))
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    tags.append(CodeTag(rel_path, node.id, "ref", node.lineno))
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"[RepoMap] Error parseando {py_file.name}: {ex}")
        return tags

    def extract_js_ts_tags(self, root_dir: Path, js_file: Path) -> list[CodeTag]:
        """Extract functions, classes, and exports in JS/TS using structured lexical analysis."""
        tags: list[CodeTag] = []
        try:
            rel_path = str(js_file.relative_to(root_dir))
            content = js_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()

            # Regex para definiciones: function foo, class Bar, const foo = () =>
            def_patterns = [
                re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_$]+)"),
                re.compile(r"^\s*(?:export\s+)?class\s+([a-zA-Z0-9_$]+)"),
                re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\("),
            ]
            import_pattern = re.compile(r"import\s+(?:{[^}]+}|\*\s+as\s+[a-zA-Z0-9_$]+|[a-zA-Z0-9_$]+)\s+from")

            for idx, line in enumerate(lines, 1):
                for pat in def_patterns:
                    m = pat.search(line)
                    if m:
                        tags.append(CodeTag(rel_path, m.group(1), "def", idx))
                        break
                if import_pattern.search(line):
                    # Extraer identificadores importados
                    words = re.findall(r"\b[a-zA-Z0-9_$]{3,}\b", line)
                    for w in words:
                        if w not in ("import", "from", "default", "type", "as"):
                            tags.append(CodeTag(rel_path, w, "ref", idx))
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:# noqa: BLE001
            logger.debug(f"[RepoMap] Error parseando JS/TS {js_file.name}: {ex}")
        return tags

    def calculate_pagerank(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, int]],
        active_files: Optional[list[str]] = None,
    ) -> dict[str, float]:
        """Compute Personalized PageRank. Use NetworkX if available; otherwise, run the power iteration algorithm with a damping factor of 0.85."""
        if not nodes:
            return {}
        if len(nodes) == 1:
            return {nodes[0]: 1.0}

        try:
            import networkx as nx

            g = nx.DiGraph()
            for n in nodes:
                g.add_node(n)
            for src, dst, w in edges:
                g.add_edge(src, dst, weight=w)

            personalization = None
            if active_files:
                valid_active = [f for f in active_files if f in nodes]
                if valid_active:
                    personalization = {n: (1.0 / len(valid_active) if n in valid_active else 0.0) for n in nodes}

            return nx.pagerank(
                g,
                alpha=self.config.damping_factor,
                personalization=personalization,
                weight="weight",
                max_iter=100,
            )
        except (RuntimeError, ValueError, KeyError, OSError, TypeError, ImportError):
            return self._power_iteration_pagerank(nodes, edges, active_files)

    def _power_iteration_pagerank(
        self,
        nodes: list[str],
        edges: list[tuple[str, str, int]],
        active_files: Optional[list[str]] = None,
    ) -> dict[str, float]:
        """Fall back to pure linear algebra power iteration."""
        n_count = len(nodes)
        node_idx = {n: i for i, n in enumerate(nodes)}
        p = [1.0 / n_count] * n_count

        teleport = [1.0 / n_count] * n_count
        if active_files:
            valid_active = [f for f in active_files if f in nodes]
            if valid_active:
                teleport = [(1.0 / len(valid_active) if n in valid_active else 0.0) for n in nodes]

        adj: dict[int, list[tuple[int, int]]] = {i: [] for i in range(n_count)}
        for src, dst, w in edges:
            if src in node_idx and dst in node_idx:
                adj[node_idx[src]].append((node_idx[dst], w))

        for _ in range(20):
            new_p = [0.0] * n_count
            for i in range(n_count):
                out_edges = adj[i]
                if not out_edges:
                    for j in range(n_count):
                        new_p[j] += p[i] / n_count
                else:
                    total_w = sum(w for _, w in out_edges)
                    for dst_idx, w in out_edges:
                        new_p[dst_idx] += p[i] * (w / total_w)
            p = [self.config.damping_factor * new_p[k] + (1.0 - self.config.damping_factor) * teleport[k] for k in range(n_count)]

        return {nodes[i]: p[i] for i in range(n_count)}

    def _scan_repo_files_and_tags(
        self, root: Path
    ) -> tuple[list[str], dict[str, list[CodeTag]]]:
        """Recursively collect supported files and extract their code tags."""
        nodes: list[str] = []
        file_tags: dict[str, list[CodeTag]] = {}
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix not in self.config.supported_extensions:
                continue
            if any(ex in p.parts for ex in self.config.excluded_dirs):
                continue
            rel_path = str(p.relative_to(root))
            nodes.append(rel_path)
            if p.suffix == ".py":
                file_tags[rel_path] = self.extract_python_tags(root, p)
            elif p.suffix in (".ts", ".js", ".tsx", ".jsx"):
                file_tags[rel_path] = self.extract_js_ts_tags(root, p)
        return nodes, file_tags

    def _build_reference_edges(
        self, file_tags: dict[str, list[CodeTag]]
    ) -> list[tuple[str, str, int]]:
        """Build directed edges between files based on definitions and references."""
        defs_map = {t.name: rel for rel, tags in file_tags.items() for t in tags if t.kind == "def"}
        edge_weights: dict[tuple[str, str], int] = {}
        for rel_path, tags in file_tags.items():
            for t in tags:
                if t.kind == "ref" and t.name in defs_map:
                    target_file = defs_map[t.name]
                    if rel_path != target_file:
                        pair = (rel_path, target_file)
                        edge_weights[pair] = edge_weights.get(pair, 0) + 1
        return [(src, dst, w) for (src, dst), w in edge_weights.items()]

    def _render_ranked_topology(
        self,
        sorted_files: list[str],
        file_tags: dict[str, list[CodeTag]],
        ranks: dict[str, float],
        budget: int
    ) -> str:
        """Format textual output within a strict token budget."""
        output_lines = [
            "# REPOSITORY TOPOLOGY (Personalized PageRank Centrality)",
            f"# Ranked {len(sorted_files)} modules, budget ~{budget} tokens",
            "",
        ]
        char_budget = budget * 4
        current_chars = 0

        for f in sorted_files:
            tags = file_tags.get(f, [])
            defs = [t.name for t in tags if t.kind == "def"]
            score = ranks.get(f, 0.0)
            file_header = f"{f} [score: {score:.4f}]:"
            block_lines = [file_header]
            for d in defs[:8]:
                block_lines.append(f"  - {d}")
            if not defs:
                block_lines.append("  (definitions internal/unexported)")
            block_lines.append("")

            block_text = "\n".join(block_lines)
            if current_chars + len(block_text) > char_budget and current_chars > 0:
                output_lines.append("... [remaining modules truncated to preserve token budget]")
                break

            output_lines.extend(block_lines)
            current_chars += len(block_text)

        return "\n".join(output_lines)

    def build_symbol_map(
        self,
        root_dir: Path,
        active_files: Optional[list[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Build the topological repository map ranked by Personalized PageRank. Modularized using the Strangler Fig pattern (McCabe V(G) <= 5)."""
        budget = max_tokens or self.config.max_map_tokens
        root = root_dir.resolve()
        nodes, file_tags = self._scan_repo_files_and_tags(root)

        if not nodes:
            return "# REPOSITORY TOPOLOGY: Empty workspace"

        edges = self._build_reference_edges(file_tags)
        ranks = self.calculate_pagerank(nodes, edges, active_files=active_files)
        sorted_files = sorted(nodes, key=lambda f: ranks.get(f, 0.0), reverse=True)

        return self._render_ranked_topology(sorted_files, file_tags, ranks, budget)

    def generate_map(
        self,
        workspace_dir: Path,
        active_files: Optional[list[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Public API alias conforming to the primitives contract."""
        return self.build_symbol_map(workspace_dir, active_files=active_files, max_tokens=max_tokens)


repomap = RepoMapPrimitive()
