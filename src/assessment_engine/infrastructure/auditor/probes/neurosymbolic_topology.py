"""
Audit probe for codebase topological architecture and dead code / orphan detection.
Constructs NetworkX AST dependency graphs to certify zero structural rot.
"""
from __future__ import annotations

import ast
from pathlib import Path

import networkx as nx

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult


def _extract_imports(file_path: Path) -> set[str]:
    """Parse AST to extract imported module names."""
    imported_modules: set[str] = set()
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return imported_modules

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    return imported_modules


def run_neurosymbolic_topology_probe(target_dir: Path) -> ProbeResult:
    """Analyze AST module dependencies to detect dead code orphans and structural debt."""
    src_dir = target_dir / "src" / "assessment_engine"
    if not src_dir.is_dir():
        src_dir = target_dir / "src"
    if not src_dir.is_dir():
        return ProbeResult(
            probe_name="neurosymbolic_topology",
            score_pct=100.0,
            passed=True,
            metrics={"total_modules": 0, "orphans_count": 0},
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

    G = nx.DiGraph()
    for f in all_py:
        rel = str(f.relative_to(src_dir))
        G.add_node(rel)

    for f in all_py:
        source_rel = str(f.relative_to(src_dir))
        imports = _extract_imports(f)
        for target_f in all_py:
            target_rel = str(target_f.relative_to(src_dir))
            if source_rel == target_rel:
                continue

            # Check if imported target is referenced
            target_mod = target_f.stem
            if any(target_mod in imp for imp in imports):
                G.add_edge(source_rel, target_rel)

    canonical_core = 0
    active_leaves = 0
    orphans: list[str] = []

    # Known CLI / Entry points that legitimately have in_degree == 0
    entry_point_names = {
        "cli.py",
        "mcp_server.py",
        "run_tower_pipeline.py",
        "run_global_pipeline.py",
        "run_commercial_pipeline.py",
        "run_tower_blueprint_engine.py",
        "build_case_input.py",
        "build_evidence_ledger.py",
        "run_evidence_analyst.py",
        "run_scoring.py",
        "run_sota_researcher.py",
        "run_executive_annex_synthesizer.py",
        "run_executive_refiner.py",
        "run_commercial_refiner.py",
        "build_global_report_payload.py",
        "render_lineage_portal.py",
        "render_commercial_report.py",
        "render_tower_annex_from_template.py",
        "render_tower_blueprint.py",
        "render_global_report_from_template.py",
        "generate_mermaid_gantt.py",
        "generate_executive_roadmap_image.py",
        "generate_global_radar_chart.py",
        "generate_tower_radar_chart.py",
        "generate_asis_markdown_modules.py",
        "compile_asis_docx_from_modules.py",
        "validate_section_output.py",
        "validate_tower_definition.py",
    }

    findings: list[AuditFinding] = []

    for node in G.nodes():
        in_deg = G.in_degree(node)
        out_deg = G.out_degree(node)
        fname = Path(node).name
        is_tool_or_bootstrap = any(part in node for part in ("tools/", "bootstrap/", "evolution/"))

        if in_deg >= 2:
            canonical_core += 1
        elif in_deg >= 1 or fname in entry_point_names or is_tool_or_bootstrap:
            active_leaves += 1
        elif in_deg == 0 and out_deg == 0:
            orphans.append(node)
            findings.append(
                AuditFinding(
                    category="TOPOLOGY",
                    severity="HIGH",
                    file_path=str(src_dir / node),
                    line_number=None,
                    rule_id="TOPOLOGY-DEAD-CODE-ORPHAN",
                    message=f"Módulo huérfano confirmado '{node}': 0 referencias entrantes y 0 salientes (código muerto).",
                    recommendation="Eliminar el módulo para mantener la arquitectura de entropía cero.",
                )
            )
        else:
            active_leaves += 1

    passed = len(orphans) == 0
    score = 100.0 if passed else max(0.0, 100.0 - (len(orphans) * 20.0))

    return ProbeResult(
        probe_name="neurosymbolic_topology",
        score_pct=score,
        passed=passed,
        metrics={
            "total_modules": len(all_py),
            "canonical_core_count": canonical_core,
            "active_leaves_count": active_leaves,
            "orphans_count": len(orphans),
        },
        findings=findings,
    )
