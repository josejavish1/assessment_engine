from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _find_matching_finding(name: str, tech_obj: str, asis_findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    for finding in asis_findings:
        f_text = finding.get("finding", finding.get("risk_observed", "")).lower()
        words = [w for w in f_text.split() if len(w) > 5]
        if sum(1 for w in words if w in name or w in tech_obj) > 1:
            return finding
    return None


def _ground_single_project(
    proj: dict[str, Any],
    asis_findings: list[dict[str, Any]],
    doc_lang: str,
    reg_frameworks: str,
) -> None:
    bc = proj.get("business_case", "")
    if bc and "impacto estratégico basado en la validación" not in bc.lower():
        return

    name = proj.get("name", "").lower()
    tech_obj = proj.get("tech_objective", "").lower()
    matched = _find_matching_finding(name, tech_obj, asis_findings)

    from assessment_engine.infrastructure.localization import t

    if matched:
        impact = matched.get("impact", matched.get("business_risk", ""))
        proj["business_case"] = t(
            "business_case_direct_mitigation_template",
            locale=doc_lang,
            impact=impact,
        )
        proj["mitigates_risk_id"] = matched.get("node_id")
    else:
        proj["business_case"] = t(
            "business_case_strategic_enabler_template",
            locale=doc_lang,
            reg_frameworks=reg_frameworks,
        )


class BusinessCaseGroundingPolicy(BaseSovereignPolicy):
    """Grounds project business cases against AS-IS findings or generates a compliant fallback."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Populates missing project business cases by linking them to risk findings."""
        pillars = payload.get("pillars_analysis", [])
        doc_lang = payload.get("document_meta", {}).get("language", "es").lower()

        raw_frameworks = payload.get("document_meta", {}).get(
            "regulatory_frameworks", []
        )
        if isinstance(raw_frameworks, list) and raw_frameworks:
            reg_frameworks = ", ".join(raw_frameworks)
        else:
            reg_frameworks = "ISO 27001, NIS2"

        for p in pillars:
            asis_findings = p.get("health_check_asis", [])
            for proj in p.get("projects_todo", []):
                _ground_single_project(proj, asis_findings, doc_lang, reg_frameworks)

        return payload
