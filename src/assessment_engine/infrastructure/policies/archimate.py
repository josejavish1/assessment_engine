from __future__ import annotations
import logging
logger = logging.getLogger(__name__)

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.localization import (
    get_archimate_catalog,
    get_archimate_fallback_deliverables,
)
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _resolve_project_deliverables(
    name: str, tech_obj: str, doc_lang: str
) -> list[str]:
    combined_text = f"{name.lower()} {tech_obj.lower()}"
    matched = set()
    catalog = get_archimate_catalog(doc_lang)

    for kw, deliverables in catalog.items():
        if kw in combined_text:
            matched.update(deliverables)

    if not matched:
        # Cross-match with alternate fallback catalog if primary returned nothing
        for fallback_lang in ["en", "es"]:
            if fallback_lang == doc_lang:
                continue
            alt_catalog = get_archimate_catalog(fallback_lang)
            for kw, deliverables in alt_catalog.items():
                if kw in combined_text:
                    matched.update(deliverables)
            if matched:
                break

    if matched:
        return list(matched)

    return get_archimate_fallback_deliverables(doc_lang)


def _load_generic_deliverable_triggers() -> list[str]:
    from assessment_engine.infrastructure.runtime_paths import ROOT
    import json
    p = ROOT / "engine_config/locales_asis_annex.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get(
                "generic_deliverable_triggers", []
            )
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug("[Fallback] Handled exception: %s", ex)
    return ["design", "test plan"]


class ArchiMateDeliverablesPolicy(BaseSovereignPolicy):
    """Aligns target state project deliverables with ArchiMate 3.1 artifacts and standard Work Breakdown Structures."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replaces generic or missing project deliverables with catalog-based items."""
        pillars = payload.get("pillars_analysis", [])
        doc_lang = str(
            payload.get("document_meta", {}).get("language", "en")
        ).lower()

        triggers = _load_generic_deliverable_triggers()
        for p in pillars:
            for proj in p.get("projects_todo", []):
                curr = proj.get("deliverables", [])
                is_generic = not curr or any(
                    any(tr in d.lower() for tr in triggers) for d in curr
                )
                if is_generic:
                    proj["deliverables"] = _resolve_project_deliverables(
                        proj.get("name", ""),
                        proj.get("tech_objective", ""),
                        doc_lang=doc_lang,
                    )
        return payload
