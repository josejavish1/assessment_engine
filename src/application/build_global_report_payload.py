"""Constructs the global report payload, encapsulating the primary business logic for the Assessment Engine's reporting pipeline."""

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
    """Safely loads and parses a JSON file from a specified path.

    This function is designed to be resilient to I/O or parsing errors. It returns
    `None` if the file does not exist, cannot be read, or contains malformed JSON,
    silencing all exceptions during the process. The file is read using the
    'utf-8-sig' encoding to correctly handle an optional leading byte order mark (BOM).

    Args:
        path: The `pathlib.Path` object pointing to the target JSON file.

    Returns:
        The deserialized JSON data as a `dict[str, Any]`, or `None` if an
        error occurs during file access or parsing.
    """
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
    r"""{'docstring': "Aggregates client data into a consolidated global report payload.\n\n    This function orchestrates the construction of a comprehensive dictionary by\n    collating data from multiple sources within a client's directory. It parses\n    and merges tower-specific blueprint files (`T*/blueprint_*_payload.json`),\n    prioritizing data from higher-numbered towers. The aggregated data is then\n    enriched with contextual information from `client_intelligence.json` and a\n    dynamically generated strategic roadmap from an orchestration process.\n\n    The process involves calculating maturity scores, extracting strategic risks,\n    compiling initiatives, and resolving identifiers against an epistemic graph\n    to produce human-readable labels. The final output is a structured payload\n    intended for generating a global client report, with provisions for executive\n    summary content to be overridden by the client intelligence file.\n\n    Args:\n        client_dir: The filesystem path to the root directory for a specific\n            client. This directory is expected to contain tower-specific\n            subdirectories (e.g., 'T1', 'T2') which hold blueprint JSON files.\n        client_name: The canonical name of the client. This identifier is used\n            for lookups within the epistemic graph and is embedded in the final\n            payload metadata.\n\n    Returns:\n        A dictionary representing the complete global report payload if successful.\n        Returns None if no blueprint files are found in the specified `client_dir`\n        or if the discovered files yield no processable data.\n\n    Raises:\n        FileNotFoundError: If the `client_dir` path does not exist.\n        json.JSONDecodeError: If a blueprint or client intelligence file contains\n            malformed JSON.\n        KeyError: If a required key is missing from the input JSON data\n            structures, particularly in sections not accessed with a `.get()`\n            fallback.\n        TypeError: If data in an input file has an unexpected type, causing a\n            failure in downstream operations such as numerical conversions."}."""
    # The loading process prioritizes new Blueprints to ensure that the most recent configurations are applied, establishing a clear override precedence for legacy versions.
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

    # Initializes the payload construction process by loading and parsing all relevant Blueprint configurations.
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

        # Extracts foundational data from the active Blueprint configuration, which serves as the primary input for the report generation logic.
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

        # Extracts associated principles and implications from the Blueprint configuration if they are defined.
        if data.get("architecture_principles"):
            all_principles.extend(data.get("architecture_principles", []))
        if data.get("operating_model_implications"):
            all_implications.extend(data.get("operating_model_implications", []))

    if not towers_data:
        return None

    blueprint_towers = sorted(dict.fromkeys(blueprint_towers))

    # Executes the graph-based resolution algorithm to determine strategic alignments and dependencies, a core component of Phase 2 Tier 1 logic.
    from application.run_strategic_orchestrator import run_strategic_orchestration

    strategic_result = run_strategic_orchestration(client_name)
    strategic_roadmap = strategic_result.get("roadmap", [])

    # Resolves UUIDs against the graph's data dictionary to substitute them with human-readable labels, ensuring the final report is intelligible to end-users.
    graph = EpistemicGraph(client_id=slugify(client_name))
    truth = graph.resolve_truth()

    def get_label(node_id: str) -> str:
        """Resolve a node ID to its canonical display label.

        Searches the global `truth` data structure for a label associated with the
        provided `node_id`. The resolution logic attempts to find a label value from
        predicates in a specific order of precedence:
        1. 'PROPOSES_INITIATIVE'
        2. 'IDENTIFIED_AS_GAP'

        If no label is found under these predicates, the function returns the
        original `node_id` as a fallback identifier.

        Args:
            node_id: The unique identifier for the node to be resolved.

        Returns:
            The corresponding display label as a string, or the original `node_id`
            if a label cannot be resolved.
        """
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

            # Executes a case-insensitive deduplication process to maintain data integrity by canonicalizing entries that differ only in character casing.
            norm_label = human_name.strip().upper()
            if norm_label in seen_labels:
                continue
            seen_labels.add(norm_label)

            # Truncates description fields that are repurposed as titles to a maximum length, preventing text overflow and maintaining visual layout consistency in the generated report.
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

    # Aggregates a distinct set of all programs to ensure data integrity and prevent redundant entries in subsequent processing stages.
    unique_waves = list(set(w["wave"] for w in strategic_roadmap))
    for uw in unique_waves:
        final_roadmap_programs.append(
            {"name": uw, "description": f"Fase de {uw} de la estrategia."}
        )

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Performs deduplication on the aggregated list and truncates it to a predefined maximum length, ensuring the final result set is both unique and concise.
    unique_principles = list(dict.fromkeys(all_principles))
    unique_implications = list(dict.fromkeys(all_implications))

    # Serializes the resolved data into the final `GlobalReportPayload` Pydantic schema for validation and downstream consumption.
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
            "programs": [],  #
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

    # Populates the Programs-by-Tower data structure, a prerequisite for enabling the 'To-Do' deep dive analysis feature in the final report.
    for t in towers_data:
        payload["execution_roadmap"]["programs"].append(
            {
                "id": t["id"],
                "name": f"Programa: Modernización de {t['name']}",
                "description": t["executive_message"],
                "projects": [i for i in all_initiatives if i["tower"] == t["name"]],
            }
        )

    # Applies an executive-level refinement layer, allowing for the direct override of certain report elements as specified by Tier 1 configurations.
    # Dynamically extracts the headline and C-level narrative from client-specific configuration extensions, if such extensions are provided.
    intel_headline = None
    intel_narrative = None
    
    if intelligence_path.exists():
        try:
            raw_intel = load_client_intelligence(intelligence_path)
            extensions = raw_intel.get("extensions", {}) if isinstance(raw_intel, dict) else {}
            exec_sum = extensions.get("executive_summary", {}) if isinstance(extensions, dict) else {}
            if isinstance(exec_sum, dict):
                intel_headline = exec_sum.get("headline")
                intel_narrative = exec_sum.get("narrative")
        except Exception:
            pass

    if intel_headline:
        payload["executive_summary"]["headline"] = intel_headline
    else:
        payload["executive_summary"]["headline"] = f"{client_name}: Estrategia de Modernización de Infraestructura"

    if intel_narrative:
        payload["executive_summary"]["narrative"] = intel_narrative

    return payload


def main(argv: list[str] | None = None) -> None:
    """Parses command-line arguments to build and save a global report payload.

    This function serves as the main entry point for the script. It orchestrates
    the process by parsing command-line arguments for a client directory, client
    name, and an output file path. It then invokes `build_global_payload` to
    construct the report data and serializes the resulting payload to a
    JSON file at the specified output path.

    Args:
        argv: An optional list of string arguments, defaulting to `sys.argv`.
            The list is expected to contain the script name followed by the
            client directory path, client name, and the output file path.

    Raises:
        SystemExit: If fewer than four command-line arguments are provided.
        IOError: If an error occurs while writing the payload to the output file
            (e.g., permission denied, non-existent parent directory).
        TypeError: If the payload returned by `build_global_payload` contains
            objects that cannot be serialized to JSON.
    """
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
