"""
Módulo run_evidence_analyst.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import json
from pathlib import Path

from assessment_engine.scripts.lib.runtime_paths import ROOT


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_statement(value: str) -> str:
    return " ".join(str(value).split()).strip()


def first_evidence_refs(
    evidences: list[dict], pillar_id: str, limit: int = 3
) -> list[str]:
    refs = []
    for evidence in evidences:
        if pillar_id in evidence.get("pillar_ids", []):
            refs.append(evidence["evidence_id"])
        if len(refs) >= limit:
            break
    return refs


def first_kpi_evidence_refs(
    evidences: list[dict], kpi_id: str, limit: int = 2
) -> list[str]:
    refs = []
    for evidence in evidences:
        if kpi_id in evidence.get("kpi_ids", []):
            refs.append(evidence["evidence_id"])
        if len(refs) >= limit:
            break
    return refs


def band_for_score(score: float, tower_definition: dict) -> str:
    for band in tower_definition.get("score_bands", []):
        if band["min"] <= score <= band["max"]:
            return band["label"]
    return tower_definition["score_bands"][-1]["label"]


def capability_phrase(kpi_name: str) -> str:
    name = kpi_name.lower()
    if "rto/rpo" in name:
        return "RTO/RPO medidos y revisados periódicamente."
    if "dependencias" in name or "alcance" in name:
        return "Dependencias integradas en gobierno de cambios."
    if "roles" in name or "gobierno" in name:
        return "Gobierno formal con seguimiento de acciones correctivas."
    if "pruebas" in name and "ransomware" in name:
        return "Pruebas regulares con tiempos medidos y acciones cerradas."
    if "restore" in name:
        return "Restauraciones periódicas con métricas de tiempo y éxito."
    if "backup" in name:
        return "Cobertura gobernada y auditada periódicamente."
    if "runbooks" in name or "orquestación" in name:
        return "Runbooks gobernados y recuperación orquestada de forma repetible."
    if "drift" in name or "entorno dr" in name or "preparación" in name:
        return "Entornos de recuperación validados con control de drift."
    if "inmutables" in name:
        return "Inmutabilidad gobernada y auditada."
    if "air-gap" in name or "segregación" in name:
        return "Air-gap operativo con controles de acceso reforzados."
    if "integridad" in name:
        return "Validación periódica de integridad con evidencia de clean restore."
    if "spof" in name:
        return "Eliminación sistemática de puntos únicos de fallo."
    if "failover" in name:
        return "Failover probado regularmente con métricas de conmutación."
    if "mttr" in name or "automatización" in name:
        return "Automatización extendida con MTTR medido."
    return f"{kpi_name} operando a nivel gobernado y medido."


def strength_statement(kpi_name: str) -> str:
    return normalize_statement(
        f"{kpi_name} presenta una base funcional ya implantada, con evidencia suficiente para sostener un nivel operativo aprovechable."
    )


def gap_statement(kpi_name: str) -> str:
    return normalize_statement(
        f"{kpi_name} no está todavía industrializado ni validado con la consistencia necesaria, lo que limita la resiliencia demostrable del pilar."
    )


def risk_title(pillar_name: str) -> str:
    return normalize_statement(f"Brecha operativa en {pillar_name}")


def initiative_title(pillar_name: str) -> str:
    return normalize_statement(f"Programa de mejora para {pillar_name}")


def build_findings(
    case_input: dict,
    evidence_ledger: dict,
    scoring_output: dict,
    tower_definition: dict,
) -> dict:
    evidences = evidence_ledger.get("evidences", [])
    answers_by_kpi = {
        answer["kpi_id"]: answer for answer in case_input.get("answers", [])
    }
    pillar_score_map = {
        item["pillar_id"]: item for item in scoring_output.get("pillar_scores", [])
    }

    pillar_findings = []
    for pillar in tower_definition.get("pillars", []):
        pillar_score = pillar_score_map[pillar["pillar_id"]]
        strengths = []
        gaps = []
        target_capabilities = []
        candidate_initiatives = []
        claims = []

        for kpi in pillar.get("kpis", []):
            answer = answers_by_kpi.get(kpi["kpi_id"])
            if not answer:
                continue
            score = float(answer["value"])
            refs = first_kpi_evidence_refs(evidences, kpi["kpi_id"])

            if score >= 3:
                strengths.append(
                    {
                        "statement": strength_statement(kpi["kpi_name"]),
                        "kpi_refs": [kpi["kpi_id"]],
                        "evidence_refs": refs,
                    }
                )
            else:
                gaps.append(
                    {
                        "statement": gap_statement(kpi["kpi_name"]),
                        "kpi_refs": [kpi["kpi_id"]],
                        "evidence_refs": refs,
                    }
                )

            target_capabilities.append(
                {
                    "kpi_id": kpi["kpi_id"],
                    "target_level": 4,
                    "target_capability": capability_phrase(kpi["kpi_name"]),
                }
            )

        if not strengths:
            strengths.append(
                {
                    "statement": normalize_statement(
                        f"{pillar['pillar_name']} dispone de capacidades iniciales sobre las que se puede construir una mejora estructurada."
                    ),
                    "kpi_refs": [],
                    "evidence_refs": first_evidence_refs(
                        evidences, pillar["pillar_id"]
                    ),
                }
            )
        if not gaps:
            gaps.append(
                {
                    "statement": normalize_statement(
                        f"{pillar['pillar_name']} mantiene margen de mejora para alcanzar un nivel plenamente optimizado y medible."
                    ),
                    "kpi_refs": [],
                    "evidence_refs": first_evidence_refs(
                        evidences, pillar["pillar_id"]
                    ),
                }
            )

        if pillar_score["score_exact"] < 4:
            candidate_initiatives.append(
                {
                    "initiative_id": f"{pillar['pillar_id'].replace('.', '-')}-01",
                    "title": initiative_title(pillar["pillar_name"]),
                    "priority": "Alta" if pillar_score["score_exact"] < 3 else "Media",
                    "horizon": "Sin calendario detallado",
                    "success_metric": (
                        f"{pillar['pillar_name']} operando con pruebas, métricas y evidencias suficientes para sostener Nivel 4."
                    ),
                    "depends_on": [],
                    "rationale": normalize_statement(
                        "Permite cerrar la brecha actual del pilar y sostener resiliencia demostrable de forma repetible."
                    ),
                    "kpi_refs": [kpi["kpi_id"] for kpi in pillar.get("kpis", [])],
                    "evidence_refs": first_evidence_refs(
                        evidences, pillar["pillar_id"]
                    ),
                }
            )

        claims.append(
            normalize_statement(
                f"{pillar['pillar_name']} se sitúa actualmente en {band_for_score(pillar_score['score_exact'], tower_definition)} con score {pillar_score['score_exact']:.2f}."
            )
        )
        claims.append(
            normalize_statement(
                f"La principal brecha de {pillar['pillar_name']} está vinculada a validación operativa, repetibilidad y trazabilidad de la evidencia."
            )
        )

        pillar_findings.append(
            {
                "pillar_id": pillar["pillar_id"],
                "pillar_name": pillar["pillar_name"],
                "score_exact": pillar_score["score_exact"],
                "score_display_1d": pillar_score["score_display_1d"],
                "current_maturity_band": band_for_score(
                    pillar_score["score_exact"], tower_definition
                ),
                "target_maturity_default": scoring_output["target_maturity_default"],
                "strengths": strengths,
                "gaps": gaps,
                "risks": [
                    {
                        "risk_id": f"{pillar['pillar_id'].replace('.', '-')}-R1",
                        "title": risk_title(pillar["pillar_name"]),
                        "cause": normalize_statement(
                            "El pilar no alcanza todavía un nivel optimizado y mantiene dependencias de procesos parciales o evidencia insuficiente."
                        ),
                        "impact": "Muy Alto"
                        if pillar_score["score_exact"] < 2.6
                        else "Alto",
                        "probability": "Media-Alta"
                        if pillar_score["score_exact"] < 3
                        else "Media",
                        "kpi_refs": [kpi["kpi_id"] for kpi in pillar.get("kpis", [])],
                        "evidence_refs": first_evidence_refs(
                            evidences, pillar["pillar_id"]
                        ),
                    }
                ],
                "target_capabilities": target_capabilities,
                "candidate_initiatives": candidate_initiatives,
                "approved_claims_for_writer": claims,
            }
        )

    strongest = max(
        scoring_output["pillar_scores"], key=lambda item: item["score_exact"]
    )
    weakest = min(scoring_output["pillar_scores"], key=lambda item: item["score_exact"])

    return {
        "schema_name": "findings",
        "schema_version": "1.0",
        "reusable": False,
        "case_id": case_input["case_id"],
        "tower_id": case_input["tower_id"],
        "tower_name": case_input["tower_name"],
        "input_refs": {
            "tower_definition": f"tower_definition_{case_input['tower_id']}.json",
            "case_input": "case_input.json",
            "scoring_output": "scoring_output.json",
            "evidence_ledger": "evidence_ledger.json",
        },
        "assessment_summary": {
            "tower_score_exact": scoring_output["tower_score_exact"],
            "tower_score_display_1d": scoring_output["tower_score_display_1d"],
            "maturity_band_from_exact": scoring_output["maturity_band_from_exact"][
                "label"
            ],
            "validation_state": case_input.get("validation_state", "Exploratoria"),
            "target_maturity_default": scoring_output["target_maturity_default"],
            "gap_to_target_exact": scoring_output["gap_to_target_exact"],
            "key_messages": [
                {
                    "message": normalize_statement(
                        f"La torre {case_input['tower_id']} muestra su mejor base operativa en {strongest['pillar_name']}, que actúa como pilar de estabilidad actual."
                    ),
                    "evidence_refs": first_evidence_refs(
                        evidences, strongest["pillar_id"]
                    ),
                    "derived_from": [strongest["pillar_id"]],
                },
                {
                    "message": normalize_statement(
                        f"La mayor brecha se concentra en {weakest['pillar_name']}, donde la resiliencia todavía no está suficientemente demostrada ni medida."
                    ),
                    "evidence_refs": first_evidence_refs(
                        evidences, weakest["pillar_id"]
                    ),
                    "derived_from": [weakest["pillar_id"]],
                },
                {
                    "message": normalize_statement(
                        "La evolución objetivo exige pasar de capacidades parciales o declarativas a una recuperación gobernada, repetible y apoyada en evidencia operativa."
                    ),
                    "evidence_refs": [evidences[0]["evidence_id"]] if evidences else [],
                    "derived_from": [
                        item["pillar_id"] for item in scoring_output["pillar_scores"]
                    ],
                },
            ],
        },
        "pillar_findings": pillar_findings,
        "_build_metadata": {
            "case_input": "case_input.json",
            "evidence_ledger": "evidence_ledger.json",
            "scoring_output": "scoring_output.json",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    parser.add_argument("--evidence-ledger", required=True)
    parser.add_argument("--scoring-output", required=True)
    args = parser.parse_args()

    case_input_path = Path(args.case_input).resolve()
    evidence_ledger_path = Path(args.evidence_ledger).resolve()
    scoring_output_path = Path(args.scoring_output).resolve()

    case_input = load_json(case_input_path)
    evidence_ledger = load_json(evidence_ledger_path)
    scoring_output = load_json(scoring_output_path)
    tower_definition = load_json(
        ROOT
        / "engine_config"
        / "towers"
        / case_input["tower_id"]
        / f"tower_definition_{case_input['tower_id']}.json"
    )

    findings = build_findings(
        case_input, evidence_ledger, scoring_output, tower_definition
    )
    output_path = case_input_path.with_name("findings.json")
    output_path.write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"findings generado en: {output_path}")
    print(f"pillar_findings: {len(findings['pillar_findings'])}")


if __name__ == "__main__":
    main()
