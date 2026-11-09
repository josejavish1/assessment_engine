"""Neurosymbolic AST Topology & Transitive Closure Reachability Probe.

Evaluates the architectural integrity of the codebase:
- Constructs a directed module dependency graph (DiGraph) via AST import analysis.
- Resolves package boundary re-exports (__init__.py) for idiomatic modular architecture.
- Computes transitive closure reachability via BFS from canonical production roots.
- Identifies unreachable dead islands and isolated modules with zero production impact.
"""

from __future__ import annotations

import ast
from collections import deque
import logging
from pathlib import Path
from typing import Any

import networkx as nx

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult

logger = logging.getLogger(__name__)

PRODUCTION_ROOTS: set[str] = {
    "application/cli.py",
    "mcp_server.py",
    "application/run_global_pipeline.py",
    "application/run_tower_pipeline.py",
    "application/run_commercial_pipeline.py",
    "application/run_commercial_refiner.py",
    "application/run_global_synthesizer_tobe.py",
    "application/run_intelligence_harvesting.py",
    "application/run_tower_blueprint_engine.py",
    "application/build_evidence_ledger.py",
    "application/build_global_report_payload.py",
    "application/export_graph_state.py",
    "application/pipelines/raw_evidence_ingestion_pipeline.py",
    "application/sync_payload_scores.py",
    "application/validate_tower_definition.py",
    "application/generate_executive_roadmap_image.py",
    "application/generate_mermaid_gantt.py",
    "application/generate_global_radar_chart.py",
    "application/generate_tower_radar_chart.py",
    "adapters/compilers/docx_compiler.py",
    "adapters/compilers/tomo_asis_ast_compiler.py",
    "adapters/compilers/payload_to_ast.py",
    "adapters/render_commercial_report.py",
    "adapters/render_tower_annex_from_template.py",
    "adapters/render_web_presentation.py",
    "adapters/render_lineage_portal.py",
    "application/tools/apex_dispatcher.py",
    "application/tools/run_product_owner_orchestrator.py",
    "cli/enrich_tower_payload_cli.py",
}


def _index_package_reexports(src_dir: Path) -> dict[str, set[str]]:
    """Index package __init__.py files and map each package to its re-exported submodules."""
    package_submodules: dict[str, set[str]] = {}
    for init_f in src_dir.rglob("__init__.py"):
        rel_parent = str(init_f.parent.relative_to(src_dir))
        pkg_alias = "assessment_engine." + rel_parent.replace("/", ".")
        if rel_parent == ".":
            pkg_alias = "assessment_engine"
        submods = set()
        try:
            tree = ast.parse(init_f.read_text(encoding="utf-8", errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    submods.add(node.module.split(".")[-1])
        except (SyntaxError, OSError) as err:
            logger.debug("AST parsing error on %s: %s", init_f, err)
        package_submodules[pkg_alias] = submods
    return package_submodules


def _extract_imports(file_path: Path, package_submodules: dict[str, set[str]]) -> set[str]:
    """Parse AST to extract imported module names, resolving package re-exports."""
    imported_modules: set[str] = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8", errors="ignore"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
                if node.module in package_submodules:
                    for sm in package_submodules[node.module]:
                        imported_modules.add(f"{node.module}.{sm}")
            elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name)):
                func_name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
                if func_name == "import_module" and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    imported_modules.add(node.args[0].value)
    except (SyntaxError, OSError) as err:
        logger.debug("AST parsing error on %s: %s", file_path, err)
    return imported_modules


def run_neurosymbolic_topology_probe(target_dir: Path) -> ProbeResult:
    """Execute transitive closure reachability and AST topology audit."""
    src_dir = target_dir / "src" / "assessment_engine"
    if not src_dir.is_dir():
        src_dir = target_dir / "src"
    if not src_dir.is_dir():
        return ProbeResult(
            probe_name="Neurosymbolic AST Topology & Dead Code (Zero-Entropy)",
            score_pct=100.0,
            passed=True,
            metrics={"total_modules": 0, "dead_islands_count": 0},
        )

    all_py = sorted(
        [
            p
            for p in src_dir.rglob("*.py")
            if not p.name.startswith("__")
            and "_legacy" not in p.parts
            and ".venv" not in p.parts
        ]
    )

    package_submodules = _index_package_reexports(src_dir)

    G = nx.DiGraph()
    for f in all_py:
        rel = str(f.relative_to(src_dir))
        G.add_node(rel)

    for f in all_py:
        source_rel = str(f.relative_to(src_dir))
        imports = _extract_imports(f, package_submodules)
        for target_f in all_py:
            target_rel = str(target_f.relative_to(src_dir))
            if source_rel == target_rel:
                continue

            target_mod = target_f.stem
            if any(target_mod in imp for imp in imports):
                G.add_edge(source_rel, target_rel)

    # Compute Transitive Closure via BFS from Canonical Production Roots
    active_roots = [r for r in PRODUCTION_ROOTS if G.has_node(r)]
    if not active_roots:
        active_roots = [
            n
            for n in G.nodes()
            if any(
                e in n.lower()
                for e in ("main.py", "app.py", "cli.py", "service.py", "api.py", "index.py")
            )
        ] or [n for n in G.nodes() if G.in_degree(n) == 0]
    reachable: set[str] = set()
    queue = deque(active_roots)
    visited = set(active_roots)

    while queue:
        curr = queue.popleft()
        reachable.add(curr)
        for successor in G.successors(curr):
            if successor not in visited:
                visited.add(successor)
                queue.append(successor)

    total_modules = len(all_py)
    dead_islands: list[str] = []
    findings: list[AuditFinding] = []

    for node in G.nodes():
        if node not in reachable:
            if any(part in node for part in ("tools/", "bootstrap/", "evolution/")):
                continue
            dead_islands.append(node)
            findings.append(
                AuditFinding(
                    category="TOPOLOGY",
                    severity="HIGH",
                    file_path=str(src_dir / node),
                    line_number=None,
                    rule_id="TOPOLOGY-DEAD-ISLAND",
                    message=f"Dead island module detected: '{node}' is unreachable from production roots.",
                    recommendation="Wire module into production pipeline DAG or delete to preserve zero-entropy.",
                )
            )

    reachable_count = total_modules - len(dead_islands)
    reachability_ratio = round((reachable_count / max(1, total_modules)) * 100.0, 1)

    passed = len(dead_islands) == 0
    score = reachability_ratio if passed else min(reachability_ratio, 75.0)

    return ProbeResult(
        probe_name="Neurosymbolic AST Topology & Dead Code (Zero-Entropy)",
        score_pct=score,
        passed=passed,
        metrics={
            "total_modules": total_modules,
            "production_roots_count": len(active_roots),
            "reachable_modules_count": reachable_count,
            "dead_islands_count": len(dead_islands),
            "reachability_pct": reachability_ratio,
        },
        findings=findings,
    )
