"""
Módulo build_global_report_payload.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json
import sys
from pathlib import Path


def load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def _compute_input_mode(blueprint_towers: list[str], legacy_towers: list[str]) -> str:
    if blueprint_towers and legacy_towers:
        return "mixed-blueprint-legacy"
    if blueprint_towers:
        return "blueprint-only"
    if legacy_towers:
        return "legacy-only"
    return "empty"


def _build_source_version(blueprint_towers: list[str], legacy_towers: list[str]) -> str:
    mode = _compute_input_mode(blueprint_towers, legacy_towers)
    blueprint_part = ",".join(blueprint_towers) or "none"
    legacy_part = ",".join(legacy_towers) or "none"
    return f"{mode};blueprints={blueprint_part};legacy={legacy_part}"


def _build_version_label(mode: str) -> str:
    if mode == "mixed-blueprint-legacy":
        return "v2.2 - Blueprint-first Engine (legacy fallback)"
    if mode == "legacy-only":
        return "v2.2 - Legacy fallback mode"
    return "v2.2 - Blueprint-first Engine"


def build_global_payload(client_dir, client_name, *, allow_legacy_fallback=True):
    # Intentamos cargar los nuevos Blueprints primero
    blueprint_files = list(client_dir.glob("T*/blueprint_*_payload.json"))
    refined_files = list(client_dir.glob("T*/approved_annex_*.refined.json"))

    if not blueprint_files and (not refined_files or not allow_legacy_fallback):
        print(f"No se encontraron archivos de torre en {client_dir}")
        return None

    towers_data = []
    strategic_risks = []
    all_initiatives = []
    all_principles = []
    all_implications = []
    blueprint_towers = []
    legacy_towers = []

    tower_names_map = {
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

    processed_towers = set()

    # 1. Prioridad: Procesar Blueprints
    for bp in sorted(
        blueprint_files,
        key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
    ):
        data = load_json(bp)
        if not data:
            continue

        tid = data.get("document_meta", {}).get("tower_code", bp.parent.name).upper()
        processed_towers.add(tid)
        blueprint_towers.append(tid)
        tname = tower_names_map.get(
            tid, data.get("document_meta", {}).get("tower_name", tid)
        )

        # Extraer datos del Blueprint
        avg_score = 0.0
        target_score = 4.0
        if data.get("pillars_analysis"):
            avg_score = sum(p.get("score", 0) for p in data["pillars_analysis"]) / len(
                data["pillars_analysis"]
            )
            target_score = data["pillars_analysis"][0].get("target_score", 4.0)

        towers_data.append(
            {
                "id": tid,
                "name": tname,
                "score": f"{avg_score:.1f}",
                "band": "Optimizada" if avg_score >= 3.5 else "Básica",
                "status_color": "E06666"
                if avg_score < 2.6
                else ("FFD966" if avg_score < 3.4 else "93C47D"),
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

    # 2. Fallback: Procesar archivos antiguos solo para torres no procesadas
    if allow_legacy_fallback:
        for rf in sorted(
            refined_files,
            key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
        ):
            tid = rf.parent.name.upper()
            if tid in processed_towers:
                continue

            data = load_json(rf)
            if not data:
                continue

            legacy_towers.append(tid)
            sections = data.get("sections", {})
            conclusion = sections.get("conclusion", {})
            asis = sections.get("asis", {})
            risks_sec = sections.get("risks", {})
            todo = sections.get("todo", {})
            tobe = sections.get("tobe", {})

            tname = tower_names_map.get(tid, data.get("tower_name"))

            score_val = 0.0
            try:
                score_str = (
                    asis.get("maturity_summary", {}).get("score_display", "0").split()[0]
                )
                score_val = float(score_str)
            except Exception:
                pass

            tower_summary = conclusion.get("executive_message") or asis.get(
                "executive_narrative", "Sin resumen disponible."
            )
            band_text = (
                asis.get("maturity_summary", {})
                .get("maturity_band", "N/A")
                .replace("Basico", "Básico")
            )

            towers_data.append(
                {
                    "id": tid,
                    "name": tname,
                    "score": f"{score_val:.1f}",
                    "band": band_text,
                    "status_color": "E06666"
                    if score_val < 2.6
                    else ("FFD966" if score_val < 3.4 else "93C47D"),
                    "executive_message": tower_summary,
                    "target_maturity": tobe.get("target_maturity", {}).get(
                        "recommended_level", "N/A"
                    ),
                }
            )

            for r in risks_sec.get("risks", []):
                if str(r.get("impact")).lower() in ["muy alto", "critico", "alto"]:
                    strategic_risks.append(
                        {
                            "id": f"R-{tid}",
                            "title": r.get("risk"),
                            "tower": tname,
                            "impact_level": r.get("impact"),
                            "description": r.get("cause"),
                            "business_impact": r.get("mitigation_summary"),
                        }
                    )

            for item in todo.get("todo_items", []):
                all_initiatives.append(
                    {
                        "tower": tname,
                        "title": item.get("initiative"),
                        "objective": item.get("objective"),
                        "priority": item.get("priority"),
                        "expected_outcome": item.get("expected_outcome"),
                    }
                )

            # Consolidar To-Be de archivos antiguos
            if tobe:
                all_principles.extend(tobe.get("architecture_principles", []))
                all_implications.extend(tobe.get("operating_model_implications", []))

    if not towers_data:
        return None

    blueprint_towers = sorted(dict.fromkeys(blueprint_towers))
    legacy_towers = sorted(dict.fromkeys(legacy_towers))
    input_mode = _compute_input_mode(blueprint_towers, legacy_towers)
    if legacy_towers:
        print(
            "⚠️ Global payload usando fallback legacy para torres sin blueprint: "
            + ", ".join(legacy_towers)
        )

    avg_score = round(sum(float(t["score"]) for t in towers_data) / len(towers_data), 1)

    # Eliminar duplicados y limitar
    unique_principles = list(dict.fromkeys(all_principles))[:10]
    unique_implications = list(dict.fromkeys(all_implications))[:10]

    return {
        "_generation_metadata": {
            "artifact_type": "global_report_payload",
            "artifact_version": "1.0.0",
            "source_version": _build_source_version(blueprint_towers, legacy_towers),
        },
        "meta": {
            "client": client_name,
            "date": "14 de Abril de 2026",
            "version": _build_version_label(input_mode),
        },
        "executive_summary": {
            "score": str(avg_score),
            "headline": f"Índice de Madurez Tecnológica Global: {avg_score}/5.0",
            "narrative": "PENDIENTE DE REFINADO ESTRATÉGICO",
            "top_insights": [],
        },
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
    allow_legacy_fallback = "--blueprint-only" not in raw_args[4:]
    client_dir = Path(raw_args[1])
    client_name = raw_args[2]
    payload = build_global_payload(
        client_dir,
        client_name,
        allow_legacy_fallback=allow_legacy_fallback,
    )
    if payload:
        Path(raw_args[3]).write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print("Payload dinámico generado con éxito.")

if __name__ == "__main__":
    main()
