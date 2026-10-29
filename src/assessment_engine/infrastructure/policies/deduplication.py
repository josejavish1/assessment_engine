from __future__ import annotations

import uuid
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _is_platform_eng_project(proj_or_name: Any) -> bool:
    if isinstance(proj_or_name, dict):
        if proj_or_name.get("transformation_typology") in [
            "Automation & Platform Engineering",
            "Platform Engineering",
        ]:
            return True
        name = str(proj_or_name.get("name", ""))
    else:
        name = str(proj_or_name or "")

    low = name.lower()
    return (
        "platform engineering" in low
        or "plattform engineering" in low
        or "ingenier" in low and "plataform" in low
        or "engenharia" in low and "plataforma" in low
        or "idp" in low
        or "developer platform" in low
    )


def _build_unified_platform_project(
    doc_lang: str, cloud_provider: str
) -> dict[str, Any]:
    from assessment_engine.infrastructure.localization import (
        get_localized_list,
        t,
    )

    cloud_label = cloud_provider or t(
        "default_corporate_cloud_label", locale=doc_lang
    )
    raw_delivs = get_localized_list(
        "unified_platform_program_deliverables", locale=doc_lang
    )
    deliverables = [d.format(cloud_label=cloud_label) for d in raw_delivs]

    return {
        "node_id": str(uuid.uuid4()),
        "name": t("unified_platform_program_name", locale=doc_lang),
        "transformation_typology": "Automation & Platform Engineering",
        "business_case": t(
            "unified_platform_program_business_case",
            locale=doc_lang,
            cloud_label=cloud_label,
        ),
        "tech_objective": t(
            "unified_platform_program_tech_objective",
            locale=doc_lang,
            cloud_label=cloud_label,
        ),
        "deliverables": deliverables,
        "sizing": "XL",
        "duration": t("duration_h1_month_1_6", locale=doc_lang),
        "program_id": None,
    }


class DeduplicationPolicy(BaseSovereignPolicy):
    """Consolidates disparate platform engineering projects into a single strategic program for Tower 2."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolidates platform engineering initiatives into T2.P4."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        tower_code = payload.get("document_meta", {}).get("tower_code", "")
        if tower_code != "T2":
            return payload

        doc_lang = (
            payload.get("document_meta", {}).get("language", "en").lower()
        )
        cloud_provider = payload.get("document_meta", {}).get(
            "cloud_provider", ""
        )
        target_pilar_id = "T2.P4"
        found_platform_projects: list[dict[str, Any]] = []

        for p in pillars:
            p_id = p.get("pilar_id")
            if p_id == target_pilar_id:
                continue
            for proj in list(p.get("projects_todo", [])):
                if _is_platform_eng_project(proj):
                    found_platform_projects.append(proj)
                    p["projects_todo"].remove(proj)

        if not found_platform_projects:
            return payload

        unified_proj = _build_unified_platform_project(doc_lang, cloud_provider)
        for p in pillars:
            if p.get("pilar_id") == target_pilar_id:
                p["projects_todo"] = [unified_proj]
                break

        return payload
