from __future__ import annotations

import uuid
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _is_finding_addressed_by_projects(
    finding: dict[str, Any], projects: list[dict[str, Any]]
) -> bool:
    node_id = finding.get("node_id")
    finding_cap = str(finding.get("capability", "")).lower()

    for proj in projects:
        # 1. Direct explicit link via node_id
        if node_id and (
            proj.get("mitigates_risk_id") == node_id
            or node_id in proj.get("mitigated_risk_ids", [])
        ):
            return True
        # 2. Capability architectural match
        proj_cap = str(proj.get("capability", "")).lower()
        if finding_cap and proj_cap and finding_cap == proj_cap:
            return True

    # 3. Semantic overlap: requires substantive domain term overlap, not generic words
    f_text = finding.get("finding", finding.get("risk_observed", ""))
    stopwords = {
        "sistema",
        "sistemas",
        "servicio",
        "servicios",
        "proceso",
        "procesos",
        "entorno",
        "entornos",
        "gestión",
        "control",
        "controles",
    }
    words = [
        w.lower()
        for w in f_text.split()
        if len(w) > 5 and w.lower() not in stopwords
    ]
    if not words:
        return True

    all_proj_text = " ".join(
        f"{proj.get('name', '')} {proj.get('tech_objective', '')}"
        for proj in projects
    ).lower()
    matched_count = sum(1 for w in words if w in all_proj_text)
    return (matched_count >= 2) or (len(words) == 1 and matched_count == 1)


def _build_remediation_project(
    finding: dict[str, Any], f_text: str, doc_lang: str = "es"
) -> dict[str, Any]:
    default_cap = "Infraestructura" if doc_lang == "es" else "Infrastructure"
    default_impact = (
        "Riesgo Operativo" if doc_lang == "es" else "Operational Risk"
    )
    cap = finding.get("capability", finding.get("target_state", default_cap))
    impact = finding.get(
        "impact", finding.get("business_risk", default_impact)
    )

    if doc_lang == "en":
        return {
            "node_id": str(uuid.uuid4()),
            "name": f"Tactical Remediation Program: {cap}",
            "transformation_typology": "Core Modernization & Risk Mitigation",
            "business_case": f"Direct Risk Mitigation: {impact}",
            "tech_objective": f"Remediate technical gap identified in AS-IS: {f_text}",
            "deliverables": [
                "Remediation Plan",
                "Patch & Configuration Deployment",
                "Gap Closure Verification Report",
            ],
            "sizing": "S",
            "duration": "H1 (Months 1-3)",
            "program_id": None,
            "mitigates_risk_id": finding.get("node_id"),
        }

    return {
        "node_id": str(uuid.uuid4()),
        "name": f"Programa de Remediación Táctica: {cap}",
        "transformation_typology": "Core Modernization & Risk Mitigation",
        "business_case": f"Mitigación Directa de Riesgo: {impact}",
        "tech_objective": f"Resolver la brecha detectada en el AS-IS: {f_text}",
        "deliverables": [
            "Plan de Remediación",
            "Ejecución de Parches/Configuraciones",
            "Informe de Cierre de Brecha",
        ],
        "sizing": "S",
        "duration": "H1 (Mes 1-3)",
        "program_id": None,
        "mitigates_risk_id": finding.get("node_id"),
    }


class ReverseTraceabilityPolicy(BaseSovereignPolicy):
    """Enforces reverse traceability by synthesizing remediation initiatives for orphan AS-IS gaps."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Injects remediation projects into a payload for unaddressed findings."""
        pillars = payload.get("pillars_analysis", [])
        doc_lang = str(
            payload.get("document_meta", {}).get("language", "es")
        ).lower()

        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            projects = p.get("projects_todo", [])

            for finding in asis_findings:
                if not _is_finding_addressed_by_projects(finding, projects):
                    f_text = finding.get(
                        "finding", finding.get("risk_observed", "")
                    )
                    fallback_proj = _build_remediation_project(
                        finding, f_text, doc_lang=doc_lang
                    )
                    projects.append(fallback_proj)

        return payload
