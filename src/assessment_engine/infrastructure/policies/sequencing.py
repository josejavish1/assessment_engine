from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _sequence_single_project(proj: dict[str, Any]) -> None:
    name_low = proj.get("name", "").lower()
    typology = str(proj.get("transformation_typology", "")).lower()
    sizing = str(proj.get("sizing", "")).upper()

    is_foundation_plan = (
        "adopción de plataforma" in name_low
        or "estrategia de adopción" in name_low
        or "container adoption" in name_low
        or "adoption strategy" in name_low
    )
    is_platform_pilot = (
        "plataforma interna de desarrollo" in name_low
        or "piloto" in name_low
        or "pilot" in name_low
        or "kubernetes" in name_low
        or "eks" in name_low
    )

    if is_foundation_plan:
        proj["duration"] = "Horizonte 1 - Fase de Arranque (Mes 1-2)"
        proj["tech_objective"] = (
            "Establecer las directrices operativas, de gobernanza, de costes y de seguridad para cargas de contenedores antes de iniciar desarrollos técnicos de IDP."
        )
    elif is_platform_pilot:
        proj["duration"] = "Horizonte 2 (Mes 3-12)"
    elif sizing == "S" or "tactical" in typology or "quick" in typology:
        proj["duration"] = "H1 (Mes 1-3)"
    elif sizing in ["L", "XL"] or "strategic" in typology:
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
