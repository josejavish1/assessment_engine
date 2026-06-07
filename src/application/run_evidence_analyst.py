"""
Módulo run_evidence_analyst.py (AI ENHANCED EDITION 2026 - FULL CONTEXT).
Refactorizado para que la IA vea no solo el score, sino la RESPUESTA REAL del cliente.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, cast

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from domain.maturity_band import resolve_maturity_band
from domain.prompts.intelligence_prompts import get_technical_analyst_prompt
from infrastructure.ai_client import run_agent
from infrastructure.runtime_paths import ROOT


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


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


def band_for_score(score: float, tower_definition: dict) -> str:
    return resolve_maturity_band(score, tower_definition.get("score_bands", []))[
        "label"
    ]


async def build_findings(
    case_input: dict,
    evidence_ledger: dict,
    scoring_output: dict,
    tower_definition: dict,
) -> dict:
    evidences = evidence_ledger.get("evidences", [])
    tower_id = scoring_output.get("tower_id", "Unknown")
    context_summary = case_input.get("context_summary", "")

    # Extraer las respuestas del test para dar profundidad a la IA
    # 'case_input' contiene la lista de 'answers' que tienen [kpi_id, score, context]
    answers_text = ""
    for ans in case_input.get("answers", []):
        answers_text += f"- KPI {ans.get('kpi_id')}: Score {ans.get('score')} | Info: {ans.get('context', 'Sin comentarios')}\n"

    # Setup AI Agent
    agent = Agent(
        name="technical_analyst",
        model="gemini-2.5-pro",
        instruction="Eres un Arquitecto Senior de NTT DATA especializado en infraestructuras críticas.",
    )
    app = AdkApp(agent=agent)

    pillar_findings = []

    for pillar in scoring_output.get("pillar_scores", []):
        p_id = pillar["pillar_id"]
        p_name = pillar["pillar_name"]
        p_score = pillar["score_exact"]

        print(
            f"    -> Analizando pilar {p_id} con IA (Contexto Jerárquico + Respuestas Test)..."
        )

        # 1. Separar Evidencias: Estratégicas vs Granulares
        p_strat_context = [
            e.get("excerpt", "")
            for e in evidences
            if p_id in e.get("pillar_ids", [])
            and e.get("source_type") == "strategic_summary"
        ]
        p_granular_evidence = [
            f"[{e.get('fragment_id')}] {e.get('excerpt')}"
            for e in evidences
            if p_id in e.get("pillar_ids", [])
            and e.get("source_type") == "atomic_fragment"
        ]

        strat_str = "\n".join(p_strat_context)
        granular_str = "\n".join(p_granular_evidence)[:3000]

        # 2. Filtrar respuestas del test de este pilar
        p_answers = "\n".join(
            [a for a in answers_text.split("\n") if f"KPI {p_id}." in a]
        )

        full_analysis_context = f"""
        RESUMEN ESTRATÉGICO DE CONTEXTO:
        {strat_str}

        ANÁLISIS DE RESPUESTAS DEL TEST:
        {p_answers}
        """

        # 3. Llamada al agente con evidencia granulada
        analysis = await run_agent(
            app,
            user_id="tech_analyst",
            message=get_technical_analyst_prompt(
                tower_id, p_name, p_score, full_analysis_context, granular_str
            ),
        )

        strength_text = analysis.get("strength", "Capacidad operativa validada.")
        strength_frag = analysis.get("strength_fragment_id")

        gap_text = analysis.get("gap", "Brecha de madurez identificada.")
        gap_frag = analysis.get("gap_fragment_id")

        r_title = analysis.get("risk_title", f"Riesgo en {p_name}")

        inits_data = analysis.get("initiatives", [])
        candidate_initiatives = []
        for idx, init_data in enumerate(inits_data):
            candidate_initiatives.append(
                {
                    "initiative_id": f"{p_id}-INIT-0{idx + 1}",
                    "title": init_data.get(
                        "title", f"Plan de mejora {p_name} {idx + 1}"
                    ),
                    "priority": "Alta" if p_score < 2.5 else "Media",
                    "horizon": init_data.get("horizon", "Mid-term"),
                    "rationale": init_data.get(
                        "rationale", "Mejora de la resiliencia operativa."
                    ),
                }
            )

        pillar_findings.append(
            {
                "pillar_id": p_id,
                "pillar_name": p_name,
                "score_exact": p_score,
                "score_display_1d": round(p_score, 1),
                "current_maturity_band": band_for_score(p_score, tower_definition),
                "strengths": [
                    {"statement": strength_text, "fragment_id": strength_frag}
                ],
                "gaps": [{"statement": gap_text, "fragment_id": gap_frag}],
                "risks": [
                    {"title": r_title, "severity": "High" if p_score < 3 else "Medium"}
                ],
                "candidate_initiatives": candidate_initiatives,
            }
        )

    return {
        "schema_name": "findings",
        "case_id": scoring_output.get("case_id"),
        "tower_id": tower_id,
        "assessment_summary": {
            "key_messages": [
                {
                    "message": f"La torre {tower_id} presenta un estado de madurez de {scoring_output['tower_score_display_1d']}.",
                    "derived_from": [p["pillar_id"] for p in pillar_findings],
                }
            ]
        },
        "pillar_findings": pillar_findings,
    }


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-input", required=True)
    parser.add_argument("--evidence-ledger", required=True)
    parser.add_argument("--scoring-output", required=True)
    args = parser.parse_args()

    case_input = load_json(Path(args.case_input))
    evidence_ledger = load_json(Path(args.evidence_ledger))
    scoring_output = load_json(Path(args.scoring_output))

    tower_id = scoring_output["tower_id"]
    tower_def_path = (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )
    tower_definition = load_json(tower_def_path)

    print(f"🚀 Iniciando Análisis de Evidencias IA Senior para {tower_id}...")
    findings = await build_findings(
        case_input, evidence_ledger, scoring_output, tower_definition
    )

    output_path = Path(args.scoring_output).parent / "findings.json"
    output_path.write_text(
        json.dumps(findings, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Hallazgos generados con IA Senior: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
