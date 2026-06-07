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

from infrastructure.client_intelligence import (
    build_client_context_packet,
    load_client_intelligence,
)
from infrastructure.epistemic_graph import EpistemicGraph
from infrastructure.global_maturity_policy import (
    average_pillar_score,
    average_pillar_target,
    band_for_score,
    status_color_for_score,
)
from infrastructure.text_utils import slugify

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

    # 2. RESOLUCIÓN ESTRATÉGICA BASADA EN GRAFOS (PHASE 2 TIER 1)
    from application.run_strategic_orchestrator import run_strategic_orchestration

    strategic_result = run_strategic_orchestration(client_name)
    strategic_roadmap = strategic_result.get("roadmap", [])

    # Resolver etiquetas reales desde el grafo para evitar UUIDs en el reporte
    graph = EpistemicGraph(client_id=slugify(client_name))
    truth = graph.resolve_truth()

    def get_label(node_id: str) -> str:
        predicates = truth.get(node_id, {})
        return (
            predicates.get("PROPOSES_INITIATIVE", {}).get("value")
            or predicates.get("IDENTIFIED_AS_GAP", {}).get("value")
            or node_id
        )

    final_roadmap_programs = []
    final_horizons = {
        "quick_wins_0_3_months": [],
        "year_1_3_12_months": [],
        "year_2_12_24_months": [],
        "year_3_24_36_months": [],
    }

    seen_labels = set()
    for wave in strategic_roadmap:
        wave_label = wave["wave"]
        for node_id in wave["projects"]:
            human_name = get_label(node_id)

            # Case-insensitive deduplication for the report
            norm_label = human_name.strip().upper()
            if norm_label in seen_labels:
                continue
            seen_labels.add(norm_label)

            # Evitar descripciones demasiado largas como títulos
            if len(human_name) > 120:
                human_name = human_name[:117] + "..."

            init_def = {
                "program": wave_label,
                "title": human_name,
                "business_case": "Mitigación de deuda técnica identificada en el grafo.",
                "start_month": 0
                if "0" in wave_label
                else 6
                if "1" in wave_label
                else 12,
                "duration_months": 6,
            }
            if "0" in wave_label:
                final_horizons["quick_wins_0_3_months"].append(init_def)
            elif "1" in wave_label:
                final_horizons["year_1_3_12_months"].append(init_def)
            else:
                final_horizons["year_2_12_24_months"].append(init_def)

    # Programas únicos
    unique_waves = list(set(w["wave"] for w in strategic_roadmap))
    for uw in unique_waves:
        final_roadmap_programs.append(
            {"name": uw, "description": f"Fase de {uw} de la estrategia."}
        )

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Eliminar duplicados y limitar
    unique_principles = list(dict.fromkeys(all_principles))
    unique_implications = list(dict.fromkeys(all_implications))

    # 3. CONVERTIR A SCHEMA GLOBALREPORTPAYLOAD (TIER 1)
    payload = {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
            "source_version": _build_source_version(blueprint_towers),
        },
        "meta": {
            "client": client_name,
            "date": "14 de Junio de 2026",
            "version": "v6.0 - Sovereign DTO",
        },
        "executive_summary": {
            "headline": f"Índice de Madurez Tecnológica Global: {avg_score}/5.0",
            "narrative": "PENDIENTE DE REFINADO ESTRATÉGICO",
            "key_business_impacts": [
                "Aceleración del time-to-market",
                "Reducción de riesgo operacional",
                "Optimización de costes cloud",
            ],
            "top_strategic_risks": strategic_risks[:5],
            "maturity_pulse": {
                "score": avg_score,
                "band": band_for_score(avg_score),
                "trend": "Stable",
            },
        },
        "strategic_overview": {
            "asis_summary": "El ecosistema tecnológico actual muestra una fragmentación estructural entre silos operativos y una dependencia de procesos manuales que limita la escalabilidad.",
            "tobe_vision": "Evolución hacia un modelo de plataforma automatizada y soberana (Sovereign DTO) que habilite la resiliencia operativa y la eficiencia económica.",
            "value_targets": unique_implications[:5],
        },
        "burning_platform": [
            {
                "theme": risk.get("title", "Riesgo Técnico"),
                "business_risk": risk.get("business_impact", "Impacto no cuantificado"),
                "root_causes": [
                    risk.get("description", "Causa raíz bajo investigación")
                ],
            }
            for risk in strategic_risks[:5]
        ],
        "intelligence_dossier": intelligence_dossier,
        "heatmap": towers_data,
        "tower_bottom_lines": [
            {
                "id": t["id"],
                "name": t["name"],
                "score": t["score"],
                "band": t["band"],
                "status_color": t["status_color"],
                "bottom_line": t["executive_message"],
            }
            for t in towers_data
        ],
        "target_vision": {
            "value_proposition": "Transformación hacia un modelo de plataforma soberana y automatizada.",
            "evolution_principles": [
                {"principle": p, "description": "Principio de diseño estratégico."}
                for p in unique_principles[:5]
            ],
            "strategic_pillars": [
                {"pillar": p, "description": "Pilar de transformación."}
                for p in unique_implications[:5]
            ],
        },
        "execution_roadmap": {
            "programs": [],  # Will be populated below
            "horizons": final_horizons,
        },
        "executive_decisions": {
            "immediate_decisions": [
                {
                    "decision_type": "Inversión",
                    "action_required": "Aprobar presupuesto para Wave 0",
                    "impact_if_delayed": "Retraso crítico en el plan de transformación",
                }
            ]
        },
        "visuals": {
            "radar_chart": "global_radar_chart.png",
            "roadmap_timeline": "global_roadmap_timeline.png",
        },
    }

    # Populate Programs by Tower for To-Do deep dive
    for t in towers_data:
        payload["execution_roadmap"]["programs"].append(
            {
                "id": t["id"],
                "name": f"Programa: Modernización de {t['name']}",
                "description": t["executive_message"],
                "projects": [i for i in all_initiatives if i["tower"] == t["name"]],
            }
        )

    # EXECUTIVE REFINEMENT (TIER 1 OVERRIDE)
    if client_name.lower() == "redeia":
        payload["executive_summary"]["headline"] = (
            "Redeia: Catalizador de la Doble Transición - Estrategia de Modernización 2026"
        )
        payload["executive_summary"]["narrative"] = (
            "Redeia se encuentra en una coyuntura estratégica crítica, actuando como el catalizador de la transición ecológica y digital en España. El presente assessment revela un Índice de Madurez Tecnológica Global de 3.0/5.0, caracterizado por un núcleo operacional robusto pero condicionado por silos tecnológicos y una deuda técnica acumulada en procesos manuales. La transición hacia el modelo H2 (Hyperautomation) es el imperativo para habilitar el Plan Estratégico 2025-2030. La arquitectura Sovereign DTO propuesta orquesta una transformación en tres Waves, priorizando la resiliencia cibernética (NIS2) y la industrialización de la plataforma Azure (Círculo de Datos) como cimientos ineludibles para la escalabilidad del negocio y la excelencia operativa exigida a un operador de infraestructuras críticas nacionales."
        )

    return payload


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
