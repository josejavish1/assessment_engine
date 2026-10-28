from __future__ import annotations

import uuid
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _is_orphan_finding(f_text: str, all_proj_text: str) -> bool:
    words = [w.lower() for w in f_text.split() if len(w) > 5]
    if not words:
        return False
    return sum(1 for w in words if w in all_proj_text) == 0


def _build_remediation_project(finding: dict[str, Any], f_text: str) -> dict[str, Any]:
    cap = finding.get("capability", finding.get("target_state", "Infraestructura"))
    impact = finding.get("impact", finding.get("business_risk", "Riesgo Operativo"))
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
        "duration": "Horizonte 1 (Mes 1-3)",
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
        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            projects = p.get("projects_todo", [])

            all_proj_text = " ".join(
                f"{proj.get('name', '')} {proj.get('tech_objective', '')}"
                for proj in projects
            ).lower()

            for finding in asis_findings:
                f_text = finding.get("finding", finding.get("risk_observed", ""))
                if _is_orphan_finding(f_text, all_proj_text):
                    fallback_proj = _build_remediation_project(finding, f_text)
                    p["projects_todo"].append(fallback_proj)
                    all_proj_text += f" {fallback_proj['name'].lower()} {fallback_proj['tech_objective'].lower()}"

        return payload
