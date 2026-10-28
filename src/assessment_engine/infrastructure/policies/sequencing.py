from __future__ import annotations

from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _sequence_single_project(proj: dict[str, Any]) -> None:
    name_low = proj.get("name", "").lower()
    if (
        "adopción de plataforma de contenedores" in name_low
        or "estrategia de adopción" in name_low
    ):
        proj["duration"] = "Horizonte 1 - Fase de Arranque (Mes 1-2)"
        proj["tech_objective"] = (
            "Establecer las directrices operativas, de gobernanza, de costes y de seguridad para cargas de contenedores antes de iniciar desarrollos técnicos de IDP."
        )
    elif (
        "plataforma interna de desarrollo" in name_low
        or "piloto" in name_low
        or "kubernetes" in name_low
        or "eks" in name_low
    ):
        proj["duration"] = "Horizonte 2 (Mes 3-12)"


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
