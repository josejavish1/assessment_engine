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
    from assessment_engine.infrastructure.localization import (
        get_localized_string,
        load_locales_catalog,
        resolve_base_locale,
    )

    base_loc = resolve_base_locale(doc_lang)
    catalog = load_locales_catalog()
    loc_entry = catalog.get(base_loc, catalog.get("en", catalog.get("es", {})))

    default_cap = (
        "Infraestructura" if base_loc == "es" else "Infrastructure"
    )
    default_impact = (
        "Riesgo Operativo" if base_loc == "es" else "Operational Risk"
    )
    cap = finding.get("capability", finding.get("target_state", default_cap))
    impact = finding.get(
        "impact", finding.get("business_risk", default_impact)
    )

    name = get_localized_string(
        "remediation_project_name_template",
        locale=base_loc,
        capability=cap,
        default=(
            f"Programa de Remediación Táctica: {cap}"
            if base_loc == "es"
            else f"Tactical Remediation Program: {cap}"
        ),
    )
    b_case = get_localized_string(
        "remediation_business_case_template",
        locale=base_loc,
        impact=impact,
        default=(
            f"Mitigación Directa de Riesgo: {impact}"
            if base_loc == "es"
            else f"Direct Risk Mitigation: {impact}"
        ),
    )
    tech_obj = get_localized_string(
        "remediation_tech_objective_template",
        locale=base_loc,
        finding_text=f_text,
        default=(
            f"Resolver la brecha detectada en el AS-IS: {f_text}"
            if base_loc == "es"
            else f"Remediate technical gap identified in AS-IS: {f_text}"
        ),
    )
    duration = loc_entry.get(
        "remediation_duration",
        "H1 (Mes 1-3)" if base_loc == "es" else "H1 (Months 1-3)",
    )
    deliverables = loc_entry.get(
        "remediation_deliverables",
        (
            [
                "Plan de Remediación",
                "Ejecución de Parches/Configuraciones",
                "Informe de Cierre de Brecha",
            ]
            if base_loc == "es"
            else [
                "Remediation Plan",
                "Patch & Configuration Deployment",
                "Gap Closure Verification Report",
            ]
        ),
    )

    return {
        "node_id": str(uuid.uuid4()),
        "name": name,
        "transformation_typology": "Core Modernization & Risk Mitigation",
        "business_case": b_case,
        "tech_objective": tech_obj,
        "deliverables": list(deliverables),
        "sizing": "S",
        "duration": duration,
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
