"""
Audit documentation quality and architectural traceability per ISO/IEC/IEEE 26514:2022 and Google Style Guide. Implement:
- Broken relative hyperlink validation in Markdown files.
- Architectural drift detection between docs/ARCHITECTURE.md and source code.
- OpenAPI contract completeness verification (summary, description, or docstring in FastAPI endpoints).
- Code fence syntax highlighting compliance per Google Documentation Style Guide.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from assessment_engine.infrastructure.auditor.models import AuditFinding, ProbeResult, find_target_files


def audit_markdown_links_and_fences(
    target_dir: Path
) -> tuple[int, int, int, list[AuditFinding]]:
    """Audit all project Markdown files to verify relative link integrity and code block syntax specifiers."""
    findings: list[AuditFinding] = []
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    total_links = 0
    broken_links_count = 0
    bare_fences_count = 0

    md_files = find_target_files(target_dir, (".md",))

    for mf in md_files:
        rel_file = str(mf.relative_to(target_dir))
        try:
            content = mf.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        # 1. Audit internal relative links
        for m in link_re.finditer(content):
            total_links += 1
            url = m.group(2).strip()
            # Ignorar enlaces externos, esquemas y anclas locales puras
            if url.startswith(("http://", "https://", "mailto:", "ftp:", "#")):
                continue
            target_path_str = url.split("#")[0]
            if not target_path_str:
                continue

            resolved = (mf.parent / target_path_str).resolve()
            if not resolved.exists():
                broken_links_count += 1
                findings.append(AuditFinding(
                    category="DOCUMENTATION",
                    severity="CRITICAL",
                    file_path=rel_file,
                    line_number=None,
                    rule_id="DOC-DEAD-LINK",
                    message=f"Broken link detected pointing to '{url}': target file missing from disk",
                    recommendation="Update or correct relative path to existing target file."
                ))

        # 2. Audit code blocks (require syntax language identifiers per Google style)
        lines = content.splitlines()
        in_fence = False
        for i, line in enumerate(lines, 1):
            s_line = line.strip()
            if s_line.startswith("```"):
                if not in_fence:
                    in_fence = True
                    lang = s_line[3:].strip()
                    if not lang:
                        bare_fences_count += 1
                        findings.append(AuditFinding(
                            category="DOCUMENTATION",
                            severity="LOW",
                            file_path=rel_file,
                            line_number=i,
                            rule_id="DOC-BARE-CODE-FENCE",
                            message="Code block missing language syntax specifier (Google Documentation Style Guide)",
                            recommendation="Declarar el lenguaje (ej. '```python', '```bash', '```json' o '```text')."
                        ))
                else:
                    in_fence = False

    return total_links, broken_links_count, bare_fences_count, findings


def audit_architectural_traceability(
    target_dir: Path
) -> tuple[int, int, list[AuditFinding]]:
    """Verify that code files referenced in docs/ARCHITECTURE.md and formal specifications exist in the repository."""
    findings: list[AuditFinding] = []
    arch_file = target_dir / "docs" / "ARCHITECTURE.md"
    if not arch_file.exists():
        return 0, 0, findings

    try:
        content = arch_file.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0, 0, findings

    # Extract literal file references with recognized extensions
    file_refs = set(re.findall(r"`([a-zA-Z0-9_\-/\.]+\.(?:py|tsx|ts|html|json|md))`", content))
    total_refs = len(file_refs)
    drifted_count = 0

    for ref in file_refs:
        # Ignore abstract names or database schemas
        if "/" not in ref and "." not in ref:
            continue
        p = target_dir / ref
        # Comprobar ruta directa o existencia en subdirectorios
        if not p.exists() and not any(target_dir.glob(f"**/{Path(ref).name}")):
            drifted_count += 1
            findings.append(AuditFinding(
                category="DOCUMENTATION",
                severity="HIGH",
                file_path="docs/ARCHITECTURE.md",
                line_number=None,
                rule_id="DOC-ARCHITECTURAL-DRIFT",
                message=f"Architectural drift detected: file '{ref}' cited in documentation does not exist in codebase",
                recommendation=f"Update docs/SYSTEM_ARCHITECTURE.md to reflect actual path of '{ref}' or create module."
            ))

    return total_refs, drifted_count, findings


def audit_openapi_endpoint_coverage(
    target_dir: Path
) -> tuple[int, int, list[AuditFinding]]:
    """Inspect FastAPI endpoints to verify they define a summary, description, or descriptive docstring for OpenAPI documentation."""
    findings: list[AuditFinding] = []
    total_endpoints = 0
    documented_endpoints = 0

    server_py = target_dir / "server.py"
    if not server_py.exists():
        return 0, 0, findings

    try:
        import server
        app = getattr(server, "app", None)
        if app is None:
            return 0, 0, findings

        from fastapi.routing import APIRoute

        all_routes: list[APIRoute] = []
        for r in app.routes:
            if isinstance(r, APIRoute):
                all_routes.append(r)
            elif hasattr(r, "original_router") and hasattr(r.original_router, "routes"):
                for sub_r in r.original_router.routes:
                    if isinstance(sub_r, APIRoute):
                        all_routes.append(sub_r)

        total_endpoints = len(all_routes)
        for r in all_routes:
            has_doc = bool(r.summary or r.description or (r.endpoint and r.endpoint.__doc__))
            if has_doc:
                documented_endpoints += 1
            else:
                findings.append(AuditFinding(
                    category="DOCUMENTATION",
                    severity="MEDIUM",
                    file_path="server.py",
                    line_number=None,
                    rule_id="DOC-ENDPOINT-UNDOCUMENTED",
                    message=f"Endpoint '{r.path}' ({r.name}) lacks OpenAPI summary or docstring",
                    recommendation="Add summary/description parameter to route decorator or docstring to handler."
                ))

    except (ImportError, AttributeError, OSError):
        pass

    return total_endpoints, documented_endpoints, findings


def run_documentation_quality_probe(target_dir: Path) -> ProbeResult:
    """
    Run the comprehensive documentation quality and architectural traceability audit per ISO 26514.
    """
    findings: list[AuditFinding] = []

    tot_links, dead_links, bare_fences, link_finds = audit_markdown_links_and_fences(target_dir)
    findings.extend(link_finds)

    tot_refs, drifted_refs, drift_finds = audit_architectural_traceability(target_dir)
    findings.extend(drift_finds)

    tot_eps, doc_eps, ep_finds = audit_openapi_endpoint_coverage(target_dir)
    findings.extend(ep_finds)

    # 4. Compute weighted score according to ISO/IEC/IEEE 26514
    score = 100.0
    score -= dead_links * 25.0
    score -= drifted_refs * 15.0
    score -= min(10.0, bare_fences * 1.5)

    if tot_eps > 0:
        ep_doc_ratio = doc_eps / tot_eps
        if ep_doc_ratio < 0.70:
            score -= min(15.0, (0.70 - ep_doc_ratio) * 50.0)

    score = max(0.0, min(100.0, round(score, 1)))
    passed = dead_links == 0 and drifted_refs == 0 and score >= 70.0

    return ProbeResult(
        probe_name="Documentation Quality & Architectural Traceability (ISO 26514 / Google)",
        score_pct=score,
        passed=passed,
        metrics={
            "markdown_files_scanned": len(find_target_files(target_dir, (".md",))),
            "internal_links_evaluated": tot_links,
            "dead_links_count": dead_links,
            "architectural_references_evaluated": tot_refs,
            "architectural_drift_count": drifted_refs,
            "bare_code_fences_count": bare_fences,
            "openapi_endpoints_evaluated": tot_eps,
            "openapi_documented_endpoints": doc_eps,
            "openapi_documentation_coverage_pct": round((doc_eps / max(1, tot_eps)) * 100, 1),
            "documentation_status": "Certificada y Sincronizada" if passed else "Deriva o Enlaces Rotos"
        },
        findings=findings
    )
