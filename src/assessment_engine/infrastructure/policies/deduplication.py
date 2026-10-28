from __future__ import annotations

import uuid
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy


def _is_platform_eng_project(name: str) -> bool:
    low = name.lower()
    return "platform engineering" in low or "ingeniería de plataforma" in low


def _build_unified_platform_project(
    doc_lang: str, cloud_provider: str
) -> dict[str, Any]:
    cloud_label = (
        cloud_provider
        if cloud_provider
        else (
            "la nube corporativa"
            if doc_lang == "es"
            else "the corporate cloud"
        )
    )
    if doc_lang == "es":
        return {
            "node_id": str(uuid.uuid4()),
            "name": "Programa Estratégico de Platform Engineering y Autoservicio Híbrido",
            "transformation_typology": "Automation & Platform Engineering",
            "business_case": f"Reducción de la carga cognitiva de los equipos de desarrollo y operaciones mediante la unificación de portales y catálogos sobre {cloud_label}.",
            "tech_objective": "Consolidar las iniciativas de cómputo híbrido, landing zones y provisión automática bajo una única Plataforma Interna de Desarrollo (IDP) unificada y autoservicio.",
            "deliverables": [
                "Definición del catálogo de servicios unificado.",
                f"Integración de las APIs de provisión de {cloud_label} Landing Zones.",
                "Despliegue del portal central de Autoservicio para el desarrollador.",
            ],
            "sizing": "XL",
            "duration": "H1 (Mes 1-6)",
            "program_id": None,
        }
    return {
        "node_id": str(uuid.uuid4()),
        "name": "Platform Engineering and Hybrid Self-Service Strategic Program",
        "transformation_typology": "Automation & Platform Engineering",
        "business_case": f"Reduction of developer cognitive load through unified catalogs and self-service portals over {cloud_label}.",
        "tech_objective": "Consolidate compute, landing zone, and automated provisioning capabilities under a single Internal Developer Platform (IDP).",
        "deliverables": [
            "Unified service catalog definition.",
            f"API integration for {cloud_label} Landing Zone provisioning.",
            "Developer Self-Service portal deployment.",
        ],
        "sizing": "XL",
        "duration": "H1 (Mes 1-6)",
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
            payload.get("document_meta", {}).get("language", "es").lower()
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
                if _is_platform_eng_project(proj.get("name", "")):
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
