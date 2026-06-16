"""
Módulo build_global_report_payload.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

from assessment_engine.scripts.lib.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from assessment_engine.scripts.lib.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    status_color_for_score,
)

logger = logging.getLogger(__name__)

TOWER_NAMES_MAP = {
    "T1": "Infraestructura Física y CPD",
    "T2": "Cómputo Híbrido y Plataformas",
    "T3": "Redes y Conectividad",
    "T4": "Servicios de Datos y Almacenamiento",
    "T5": "Resiliencia y Continuidad (DR)",
    "T6": "Seguridad de Infraestructura",
    "T7": "Operaciones Digitales (ITSM)",
    "T8": "Estrategia, Gobierno y FinOps",
    "T9": "Puesto de Trabajo Digital (DEX)",
    "T10": "Sistemas Legacy y Mainframe",
}


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _build_source_version(blueprint_towers: list[str]) -> str:
    blueprint_part = ",".join(blueprint_towers) or "none"
    return f"blueprint-only;blueprints={blueprint_part}"


def build_global_payload(client_dir: Path, client_name: str) -> dict[str, Any] | None:
    # Intentamos cargar los nuevos Blueprints primero
    blueprint_files = list(client_dir.glob("T*/blueprint_*_payload.json"))

    if not blueprint_files:
        logger.warning(f"No se encontraron archivos de torre en {client_dir}")
        return None

    towers_data = []
    strategic_risks = []
    all_initiatives = []
    all_principles = []
    all_implications = []
    blueprint_towers = []
    intelligence_dossier = {}

    intelligence_path = Path(client_dir) / "client_intelligence.json"
    if intelligence_path.exists():
        try:
            intelligence_dossier = build_client_context_packet(
                load_client_intelligence(intelligence_path)
            )
        except Exception:
            intelligence_dossier = {}

    # 1. Prioridad: Procesar Blueprints
    for bp in sorted(
        blueprint_files,
        key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
    ):
        data = load_json(bp)
        if not data:
            continue

        tid = data.get("document_meta", {}).get("tower_code", bp.parent.name).upper()
        blueprint_towers.append(tid)
        tname = TOWER_NAMES_MAP.get(
            tid, data.get("document_meta", {}).get("tower_name", tid)
        )

        # Extraer datos del Blueprint
        pillars_analysis = data.get("pillars_analysis", [])
        avg_score = average_pillar_score(pillars_analysis, default=0.0)
        target_score = average_pillar_target(pillars_analysis, default=4.0)

        towers_data.append(
            {
                "id": tid,
                "name": tname,
                "score": f"{avg_score:.1f}",
                "band": band_for_score(avg_score),
                "status_color": status_color_for_score(avg_score),
                "executive_message": data.get("executive_snapshot", {}).get(
                    "bottom_line", ""
                ),
                "target_maturity": f"{target_score:.1f}",
            }
        )

        for pilar in data.get("pillars_analysis", []):
            for hc in pilar.get("health_check_asis", []):
                strategic_risks.append(
                    {
                        "id": f"R-{tid}",
                        "title": hc.get("capability"),
                        "tower": tname,
                        "impact_level": "Alto",
                        "description": hc.get("finding"),
                        "business_impact": hc.get("business_risk"),
                    }
                )
            for proj in pilar.get("projects_todo", []):
                all_initiatives.append(
                    {
                        "tower": tname,
                        "title": proj.get("name"),
                        "objective": proj.get("tech_objective"),
                        "priority": "Alta",
                        "expected_outcome": proj.get("business_case"),
                    }
                )

        # Recolectar principios e implicaciones del Blueprint si existen
        if data.get("architecture_principles"):
            all_principles.extend(data.get("architecture_principles", []))
        if data.get("operating_model_implications"):
            all_implications.extend(data.get("operating_model_implications", []))

    if not towers_data:
        return None

    blueprint_towers = sorted(dict.fromkeys(blueprint_towers))

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Eliminar duplicados y limitar
    unique_principles = list(dict.fromkeys(all_principles))[:10]
    unique_implications = list(dict.fromkeys(all_implications))[:10]

    return {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
            "source_version": _build_source_version(blueprint_towers),
        },
        "meta": {
            "client": client_name,
            "date": "14 de Abril de 2026",
            "version": "v2.3 - Blueprint-first Engine",
        },
        "executive_summary": {
            "score": str(avg_score),
            "headline": f"Índice de Madurez Tecnológica Global: {avg_score}/5.0",
            "narrative": "PENDIENTE DE REFINADO ESTRATÉGICO",
            "top_insights": [],
        },
        "intelligence_dossier": intelligence_dossier,
        "heatmap": sorted(
            towers_data, key=lambda x: int(x["id"][1:]) if x["id"][1:].isdigit() else 99
        ),
        "tower_summaries": sorted(
            towers_data, key=lambda x: int(x["id"][1:]) if x["id"][1:].isdigit() else 99
        ),
        "strategic_risks": sorted(
            strategic_risks, key=lambda x: x["impact_level"], reverse=True
        )[:10],
        "architecture_principles": unique_principles,
        "operating_model_implications": unique_implications,
        "key_initiatives": sorted(
            all_initiatives, key=lambda x: x["priority"] == "Alta", reverse=True
        )[:15],
        "visuals": {
            "radar_chart": "global_radar_chart.png",
            "roadmap_timeline": "global_roadmap_timeline.png",
        },
    }


def main(argv: list[str] | None = None) -> None:
    raw_args = list(argv if argv is not None else sys.argv)
    if len(raw_args) < 4:
        sys.exit(1)
    client_dir = Path(raw_args[1])
    client_name = raw_args[2]
    payload = build_global_payload(client_dir, client_name)
    if payload:
        Path(raw_args[3]).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        logger.info("Payload dinámico generado con éxito.")


if __name__ == "__main__":
    main()
