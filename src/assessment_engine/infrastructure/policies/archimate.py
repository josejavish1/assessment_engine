from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.localization import (
    get_archimate_catalog,
    get_archimate_fallback_deliverables,
)
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _resolve_project_deliverables(
    name: str, tech_obj: str, doc_lang: str = "es"
) -> list[str]:
    combined_text = f"{name.lower()} {tech_obj.lower()}"
    matched = set()
    catalog = get_archimate_catalog(doc_lang)

    for kw, deliverables in catalog.items():
        if kw in combined_text:
            matched.update(deliverables)

    if not matched:
        # Cross-match with alternate fallback catalog if primary returned nothing
        alt_catalog = get_archimate_catalog("es" if doc_lang == "en" else "en")
        for kw, deliverables in alt_catalog.items():
            if kw in combined_text:
                matched.update(deliverables)

    if matched:
        return list(matched)

    return get_archimate_fallback_deliverables(doc_lang)


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """Populates or replaces generic deliverables with concrete ArchiMate technical deliverables."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replaces generic or missing project deliverables with catalog-based items."""
        pillars = payload.get("pillars_analysis", [])
        doc_lang = str(
            payload.get("document_meta", {}).get("language", "es")
        ).lower()

        for p in pillars:
            for proj in p.get("projects_todo", []):
                curr = proj.get("deliverables", [])
                is_generic = (
                    not curr
                    or any("diseño de arquitectura" in d.lower() for d in curr)
                    or any("architecture design" in d.lower() for d in curr)
                    or any("documento de diseño técnico" in d.lower() for d in curr)
                    or any("technical architecture design" in d.lower() for d in curr)
                    or any(d.strip() == "Plan de Pruebas y Validación" for d in curr)
                )
                if is_generic:
                    proj["deliverables"] = _resolve_project_deliverables(
                        proj.get("name", ""),
                        proj.get("tech_objective", ""),
                        doc_lang=doc_lang,
                    )
        return payload
