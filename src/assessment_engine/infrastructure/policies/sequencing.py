from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

def _sequence_single_project(proj: dict[str, Any], doc_lang: str = "en") -> None:
    """Enforces horizon sequencing for a single project based on name and scope."""
    name_low = proj.get("name", "").lower()
    typology = proj.get("typology", "").lower()
    sizing = proj.get("sizing", "M").upper()

    import unicodedata
    name_low_ascii = unicodedata.normalize("NFKD", name_low).encode("ASCII", "ignore").decode("utf-8")
    is_foundation_plan = (
        "platform adoption" in name_low_ascii
        or "adoption strategy" in name_low_ascii
        or "container adoption" in name_low_ascii
        or "adopcion" in name_low_ascii
        or "adoption" in name_low_ascii
    )
    is_platform_pilot = (
        "internal developer platform" in name_low
        or "pilot" in name_low
        or "piloto" in name_low
        or "kubernetes" in name_low
        or "eks" in name_low
    )

    from assessment_engine.infrastructure.localization import t

    if is_foundation_plan:
        proj["duration"] = t("horizon_1_kickoff", locale=doc_lang)
        proj["tech_objective"] = t("seq_tech_objective_container_guidelines", locale=doc_lang)
    elif is_platform_pilot:
        proj["duration"] = t("horizon_2_pilot", locale=doc_lang)
    elif sizing == "S" or "tactical" in typology or "quick" in typology:
        proj["duration"] = t("duration_h1_month_1_3", locale=doc_lang)
    elif sizing in ["L", "XL"] or "strategic" in typology:
        proj["duration"] = t("duration_h3_month_12_24", locale=doc_lang)
    else:
        proj["duration"] = t("duration_h2_month_3_12", locale=doc_lang)


class SequencingPolicy(BaseSovereignPolicy):
    """Enforces logical project time horizons based on initiative dependencies."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Patches project timelines and objectives in a payload based on business rules."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        import os
        doc_lang = (
            payload.get("document_meta", {}).get("language")
            or os.environ.get("ASSESSMENT_DOC_LANG")
            or "en"
        ).lower()

        for p in pillars:
            for proj in p.get("projects_todo", []):
                _sequence_single_project(proj, doc_lang=doc_lang)

        return payload
