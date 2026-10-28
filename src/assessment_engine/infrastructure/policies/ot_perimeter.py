from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

from assessment_engine.infrastructure.epistemic_graph import EpistemicGraph
from assessment_engine.infrastructure.policies.base import BaseSovereignPolicy

logger = logging.getLogger(__name__)


def _resolve_industry(payload: dict[str, Any]) -> str:
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    intel_path = Path(f"working/{client_id}/client_intelligence.json")
    if not intel_path.exists():
        client_base = client_id.split("_")[0]
        intel_path = Path(f"working/{client_id}/{client_base}/client_intelligence.json")

    if intel_path.exists():
        try:
            with open(intel_path, "r", encoding="utf-8-sig") as inf:
                intel = json.load(inf)
                return intel.get("profile", {}).get("industry", "Standard")
        except (OSError, json.JSONDecodeError) as ex:
            logger.debug(f"[PolicyEngine] Error leyendo perfil de inteligencia: {ex}")

    env_ind = os.environ.get("ASSESSMENT_INDUSTRY", "").lower()
    if env_ind == "energy" or "critical infrastructure" in env_ind:
        return "Critical Infrastructure"

    try:
        from assessment_engine.infrastructure.config_loader import load_brand_profile
        brand_profile = load_brand_profile()
        if brand_profile.get("styling", {}).get("is_critical", False):
            return "Critical Infrastructure"
    except (ImportError, KeyError, ValueError) as ex:
        logger.debug(f"[PolicyEngine] Fallback de perfil de marca omitido: {ex}")

    return "Standard"


def _patch_data_diode_deliverable(proj: dict[str, Any], deliverable_text: str, objective_suffix: str) -> None:
    if "deliverables" not in proj:
        proj["deliverables"] = []
    if not any("diodo de datos" in d.lower() for d in proj["deliverables"]):
        proj["deliverables"].append(deliverable_text)
        proj["tech_objective"] = (proj.get("tech_objective", "") + objective_suffix).strip()


class OTPerimeterPolicy(BaseSovereignPolicy):
    """Enforces mandatory data diode hardware controls for Critical Infrastructure/Energy clients."""

    def evaluate_and_patch(
        self, graph: EpistemicGraph, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conditionally injects data diode security controls into a project portfolio."""
        pillars = payload.get("pillars_analysis", [])
        if not pillars:
            return payload

        has_scada = False
        has_aiops = False

        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                if "scada" in name or "legada" in name or "infraestructura legacy" in name:
                    has_scada = True
                if "aiops" in name or "observabilidad predictiva" in name or "observabilidad" in name:
                    has_aiops = True

        if not (has_scada and has_aiops):
            return payload

        for p in pillars:
            for proj in p.get("projects_todo", []):
                name = proj.get("name", "").lower()
                if "scada" in name or "legada" in name or "infraestructura legacy" in name:
                    _patch_data_diode_deliverable(
                        proj,
                        "Implementación de un Diodo de Datos Unidireccional por Hardware para extracción segura de telemetría sin canal de retorno.",
                        " El aislamiento físico del entorno SCADA se mantendrá de forma inquebrantable mediante el uso de un diodo de datos unidireccional.",
                    )
                if "aiops" in name or "observabilidad predictiva" in name or "observabilidad" in name:
                    _patch_data_diode_deliverable(
                        proj,
                        "Despliegue del gateway receptor del Diodo de Datos de OT para ingesta pasiva de telemetría en AWS IoT Core.",
                        " Toda la ingesta de telemetría en tiempo real de subestaciones y OT se canalizará de forma 100% pasiva y segura mediante diodos de datos unidireccionales.",
                    )

        return payload
