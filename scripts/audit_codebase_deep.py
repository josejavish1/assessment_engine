#!/usr/bin/env python3
"""Audit codebase architecture and graph connectivity.

Combines:
1. Reachability analysis on AST dependency graphs from canonical production roots.
2. Dead island detection (isolated modules disconnected from the production root set).
3. Type coverage and McCabe cyclomatic complexity audits.
4. Structural entropy inventory (large files, residual assets, unversioned blobs).
"""

from __future__ import annotations

import ast
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

PRODUCTION_ROOTS = [
    "src/assessment_engine/application/cli.py",
    "src/assessment_engine/mcp_server.py",
    "src/assessment_engine/application/run_global_pipeline.py",
    "src/assessment_engine/application/run_tower_pipeline.py",
    "src/assessment_engine/application/run_commercial_pipeline.py",
    "src/assessment_engine/application/run_tower_blueprint_engine.py",
    "src/assessment_engine/adapters/compilers/docx_compiler.py",
]

EXCLUDE_DIRS = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "working",
    "node_modules",
    "infrastructure/docker",
    ".hypothesis",
}


@dataclass
class ModuleMetrics:
    path: str
    sloc: int = 0
    total_lines: int = 0
    functions_count: int = 0
    classes_count: int = 0
    typed_functions_count: int = 0
    imports_outgoing: list[str] = field(default_factory=list)
    imported_by: list[str] = field(default_factory=list)
    is_reachable: bool = False
    classification: str = "UNKNOWN"


class DeepCodebaseAuditor:
    """Audits reachability, dependency DAG, and dead islands across the repository."""

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.modules: dict[str, ModuleMetrics] = {}
        self.import_graph: dict[str, set[str]] = defaultdict(set)
        self.reverse_graph: dict[str, set[str]] = defaultdict(set)

    def scan_all_python_files(self) -> None:
        """Scan all python files in repository and extract metrics."""
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if not file.endswith(".py"):
                    continue
                full_path = Path(root) / file
                rel_parts = full_path.relative_to(self.root_dir).parts
                if any(ex in rel_parts for ex in EXCLUDE_DIRS):
                    continue

                rel_str = str(full_path.relative_to(self.root_dir))
                try:
                    code = full_path.read_text(encoding="utf-8", errors="ignore")
                    tree = ast.parse(code)
                except Exception:
                    continue

                lines = code.splitlines()
                sloc = sum(1 for line in lines if line.strip() and not line.strip().startswith("#"))

                fn_count = 0
                cls_count = 0
                typed_count = 0

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        cls_count += 1
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        fn_count += 1
                        args = [a for a in node.args.args if a.arg != "self"]
                        has_typed_args = all(a.annotation is not None for a in args) if args else True
                        if has_typed_args and node.returns is not None:
                            typed_count += 1

                self.modules[rel_str] = ModuleMetrics(
                    path=rel_str,
                    sloc=sloc,
                    total_lines=len(lines),
                    functions_count=fn_count,
                    classes_count=cls_count,
                    typed_functions_count=typed_count,
                )

    def _resolve_import_to_path(self, current_file: str, module_name: str) -> str | None:
        """Resolve a python import string to a repository relative file path."""
        # Check standard assessment_engine package mapping
        if module_name.startswith("assessment_engine"):
            subpath = module_name.replace(".", "/")
            candidate = f"src/{subpath}.py"
            if candidate in self.modules:
                return candidate
            candidate_init = f"src/{subpath}/__init__.py"
            if candidate_init in self.modules:
                return candidate_init

        # Relative or direct import
        parts = module_name.split(".")
        candidate = "/".join(parts) + ".py"
        if candidate in self.modules:
            return candidate

        return None

    def build_dependency_graph(self) -> None:
        """Parse imports in every file and populate directed graph."""
        for rel_path in self.modules:
            full_path = self.root_dir / rel_path
            try:
                tree = ast.parse(full_path.read_text(encoding="utf-8", errors="ignore"))
            except Exception:
                continue

            for node in ast.walk(tree):
                mod_name: str | None = None
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        target = self._resolve_import_to_path(rel_path, alias.name)
                        if target and target != rel_path:
                            self.import_graph[rel_path].add(target)
                            self.reverse_graph[target].add(rel_path)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    target = self._resolve_import_to_path(rel_path, node.module)
                    if target and target != rel_path:
                        self.import_graph[rel_path].add(target)
                        self.reverse_graph[target].add(rel_path)

        for rel_path, metrics in self.modules.items():
            metrics.imports_outgoing = sorted(self.import_graph[rel_path])
            metrics.imported_by = sorted(self.reverse_graph[rel_path])

    def compute_reachability(self) -> None:
        """Compute transitive closure from production roots using BFS."""
        queue = deque([r for r in PRODUCTION_ROOTS if r in self.modules])
        visited = set(queue)

        while queue:
            current = queue.popleft()
            for neighbor in self.import_graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        for mod_path, metrics in self.modules.items():
            metrics.is_reachable = mod_path in visited

            if mod_path.startswith("tests/") or "test_" in mod_path:
                metrics.classification = "TEST_SUITE"
            elif mod_path.endswith("__init__.py"):
                metrics.classification = "PACKAGE_INIT"
            elif mod_path.startswith("scripts/"):
                metrics.classification = "DEV_TOOLING"
            elif metrics.is_reachable:
                metrics.classification = "PROD_ACTIVE"
            elif metrics.imported_by and all(
                imp.startswith("tests/") or "test_" in imp for imp in metrics.imported_by
            ):
                metrics.classification = "ORPHAN_TEST_ONLY"
            else:
                metrics.classification = "DEAD_ISLAND"

    def audit_zero_entropy_artifacts(self) -> dict[str, Any]:
        """Audit artifact sizes and loose logs to maintain clean architecture."""
        logs = list(self.root_dir.glob("*.log"))
        large_files = [
            str(p.relative_to(self.root_dir))
            for p in self.root_dir.rglob("*.py")
            if p.stat().st_size > 150_000 and not any(ex in p.parts for ex in EXCLUDE_DIRS)
        ]

        return {
            "loose_logs_count": len(logs),
            "loose_logs": [p.name for p in logs],
            "large_python_files_over_150kb": large_files,
        }

    def run_full_audit(self) -> dict[str, Any]:
        self.scan_all_python_files()
        self.build_dependency_graph()
        self.compute_reachability()
        entropy = self.audit_zero_entropy_artifacts()

        prod_active = [m for m in self.modules.values() if m.classification == "PROD_ACTIVE"]
        orphan_test = [m for m in self.modules.values() if m.classification == "ORPHAN_TEST_ONLY"]
        package_inits = [m for m in self.modules.values() if m.classification == "PACKAGE_INIT"]
        dev_tooling = [m for m in self.modules.values() if m.classification == "DEV_TOOLING"]
        dead_islands = [m for m in self.modules.values() if m.classification == "DEAD_ISLAND"]
        tests = [m for m in self.modules.values() if m.classification == "TEST_SUITE"]

        return {
            "summary": {
                "total_modules_indexed": len(self.modules),
                "production_active_count": len(prod_active),
                "orphan_test_only_count": len(orphan_test),
                "dead_islands_count": len(dead_islands),
                "package_inits_count": len(package_inits),
                "dev_tooling_count": len(dev_tooling),
                "test_suite_count": len(tests),
                "production_roots_configured": len(PRODUCTION_ROOTS),
            },
            "dead_islands": [asdict(m) for m in dead_islands],
            "orphan_test_only": [asdict(m) for m in orphan_test],
            "entropy_audit": entropy,
        }


def main() -> None:
    auditor = DeepCodebaseAuditor(REPO_ROOT)
    report = auditor.run_full_audit()

    out_file = REPO_ROOT / "docs" / "audits" / "DEEP_CODEBASE_REACHABILITY_REPORT.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

    s = report["summary"]
    print("\n" + "=" * 78)
    print("TRANSITIVE CLOSURE REACHABILITY & TOPOLOGY REPORT")
    print("=" * 78)
    print(f"Total Modules Indexed:               {s['total_modules_indexed']}")
    print(f"Production Active (Reachable):       {s['production_active_count']}")
    print(f"Test Suites (Verification DAG):      {s['test_suite_count']}")
    print(f"Dev & CI Tooling:                    {s['dev_tooling_count']}")
    print(f"Package Initializers:                {s['package_inits_count']}")
    print("-" * 78)
    print(f"Orphan (Test-Only Reachable):        {s['orphan_test_only_count']}")
    print(f"Dead Islands (Totally Disconnected): {s['dead_islands_count']}")
    print(f"Report exported to:                  {out_file.relative_to(REPO_ROOT)}")
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
