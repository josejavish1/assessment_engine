from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _sequence_single_project(proj: dict[str, Any]) -> None:
    name_low = proj.get("name", "").lower()
    typology = str(proj.get("transformation_typology", "")).lower()
    sizing = str(proj.get("sizing", "")).upper()

    is_foundation = (
        "estrategia" in name_low
        or "strategy" in name_low
        or "adopción" in name_low
        or "adoption" in name_low
        or "governance" in typology
        or "tactical" in typology
        or sizing == "S"
    )
    is_platform_or_core = (
        "platform" in name_low
        or "idp" in name_low
        or "kubernetes" in name_low
        or "core" in typology
        or "platform engineering" in typology
        or sizing in ["M", "L", "XL"]
    )

    if is_foundation and sizing in ["S", "M"]:
        proj["duration"] = "H1 (Mes 1-3)"
    elif is_platform_or_core:
        if sizing in ["L", "XL"]:
            proj["duration"] = "H3 (Mes 12-24)"
        else:
            proj["duration"] = "H2 (Mes 3-12)"


class SequencingPolicy(BaseSovereignPolicy):
    """Enforces logical project time horizons based on initiative dependencies."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Patches project timelines and objectives in a payload based on business rules."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        for p in pillars:
            for proj in p.get("projects_todo", []):
                _sequence_single_project(proj)

        return payload
