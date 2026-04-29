"""
Módulo run_tower_blueprint_engine.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import sys
from pathlib import Path
from assessment_engine.schemas.blueprint import PillarBlueprintDraft, OrchestratorBlueprintDraft
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_pilar_architect_prompt,
    get_critic_prompt,
    get_closing_orchestrator_prompt
)

ROOT = Path(__file__).resolve().parents[3]


async def process_pilar_blueprint(
    model_name, client_name, tower_name, pilar_data, context_str, intel_str
):
    """Procesa un pilar individual con el Squad de Arquitecto + Crítico."""
    print(f"    -> Analizando Pilar: {pilar_data['label']}...")

    pilar_id = pilar_data["id"]
    pilar_label = pilar_data["label"]
    pilar_score = pilar_data["score"]

    answers_json = json.dumps(pilar_data["answers"], indent=2, ensure_ascii=False)
    prompt = get_pilar_architect_prompt(
        tower_name=tower_name,
        pilar_label=pilar_label,
        pilar_score=pilar_score,
        context_str=context_str,
        intel_str=intel_str,
        answers_json=answers_json,
        pilar_id=pilar_id
    )

    # 1. Agente Escritor
    try:
        from google.adk.agents import Agent
        from vertexai.agent_engines import AdkApp

        agent_architect = Agent(
            name="blueprint_architect",
            model=model_name,
            instruction=get_blueprint_architect_instruction(),
            output_schema=PillarBlueprintDraft
        )
        app_architect = AdkApp(agent=agent_architect)

        raw_output = await run_agent(
            app_architect, 
            user_id=f"architect_{pilar_id}", 
            message=prompt, 
            schema=PillarBlueprintDraft
        )

        # 2. Agente Crítico (Refinado)
        if raw_output:
            agent_critic = Agent(
                name="blueprint_critic",
                model=model_name,
                instruction=get_blueprint_architect_instruction(),
                output_schema=PillarBlueprintDraft
            )
            app_critic = AdkApp(agent=agent_critic)

            raw_output_json = json.dumps(raw_output)
            critic_prompt = get_critic_prompt(
                pilar_label=pilar_label,
                client_name=client_name,
                raw_output_json=raw_output_json
            )
            final_output = await run_agent(
                app_critic, 
                user_id=f"critic_{pilar_id}", 
                message=critic_prompt, 
                schema=PillarBlueprintDraft
            )
            return final_output or raw_output
    except Exception as e:
        print(f"Error procesando pilar {pilar_label}: {e}")
    return None


async def run_tower_blueprint(client_name, tower_id):
    client_dir = ROOT / "working" / client_name
    tower_dir = client_dir / tower_id
    case_input_path = tower_dir / "case_input.json"
    intel_path = client_dir / "client_intelligence.json"

    if not case_input_path.exists():
        print(f"Error: No se encuentra input para {tower_id}")
        return

    case_data = json.loads(case_input_path.read_text(encoding="utf-8"))
    intel_data = {}
    if intel_path.exists():
        intel_data = json.loads(intel_path.read_text(encoding="utf-8-sig"))

    tower_name = case_data.get("tower_name")

    # Preparar contexto masivo
    intel_str = json.dumps(intel_data, indent=2, ensure_ascii=False)
    context_str = case_data.get("context_summary", "")

    try:
        from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
        model_name = resolve_model_profile_for_role("writer_fast")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    # Agrupar respuestas por pilar
    pillars_map = {}
    tower_def_path = (
        ROOT
        / "engine_config"
        / "towers"
        / tower_id
        / f"tower_definition_{tower_id}.json"
    )
    tower_def = json.loads(tower_def_path.read_text(encoding="utf-8"))

    for p in tower_def.get("pillars", []):
        pillars_map[p["pillar_id"]] = {
            "id": p["pillar_id"],
            "label": p["pillar_name"],
            "score": 0,
            "answers": [],
        }

    for ans in case_data.get("answers", []):
        p_id = ".".join(ans["kpi_id"].split(".")[:2])
        if p_id in pillars_map:
            pillars_map[p_id]["answers"].append(ans)

    for p_id, p_data in pillars_map.items():
        if p_data["answers"]:
            p_data["score"] = round(
                sum(float(a["value"]) for a in p_data["answers"])
                / len(p_data["answers"]),
                1,
            )

    print(f"🏗️ Generando Blueprint de Transformación para {tower_name}...")

    blueprint_payload = {
        "document_meta": {
            "client_name": client_name,
            "tower_name": tower_name,
            "tower_code": tower_id,
            "financial_tier": intel_data.get("financial_tier", "Tier 2"),
            "transformation_horizon": intel_data.get(
                "transformation_horizon", "General"
            ),
        },
        "executive_snapshot": {},
        "pillars_analysis": [],
    }

    # PROCESAR PILARES EN SERIE PARA MÁXIMA CALIDAD
    for p_id in sorted(pillars_map.keys()):
        p_result = await process_pilar_blueprint(
            model_name, client_name, tower_name, pillars_map[p_id], context_str, intel_str
        )
        if p_result:
            p_result["score"] = pillars_map[p_id]["score"]
            p_result["target_score"] = intel_data.get("target_maturity_matrix", {}).get(
                tower_id, 4.0
            )
            blueprint_analysis = p_result.get("pillar_analysis", p_result)
            blueprint_payload["pillars_analysis"].append(blueprint_analysis)

    # AGENTE DE CIERRE: SNAPSHOT Y ROADMAP
    print("    -> Generando Snapshot Ejecutivo y Roadmap Estratégico...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str
    )
    try:
        from google.adk.agents import Agent
        from vertexai.agent_engines import AdkApp

        orchestrator_agent = Agent(
            name="blueprint_orchestrator",
            model=model_name,
            instruction=get_blueprint_architect_instruction(),
            output_schema=OrchestratorBlueprintDraft
        )
        app_orchestrator = AdkApp(agent=orchestrator_agent)

        closing_data = await run_agent(
            app_orchestrator, 
            user_id="master_orchestrator", 
            message=closing_prompt, 
            schema=OrchestratorBlueprintDraft
        )
        if closing_data:
            blueprint_payload.update(closing_data)
    except Exception as e:
        print(f"Error en agente de cierre blueprint: {e}")

    # Inyectar metadatos de versión (aseguramos que estén tras el update de closing_data)
    blueprint_payload["_generation_metadata"] = {
        "artifact_type": "blueprint_payload",
        "artifact_version": "1.0.0",
    }

    # GUARDAR PAYLOAD
    output_path = tower_dir / f"blueprint_{tower_id.lower()}_payload.json"
    output_path.write_text(
        json.dumps(blueprint_payload, indent=2, ensure_ascii=False),
        encoding="utf-8-sig",
    )
    print(f"✅ Payload del Blueprint generado: {output_path}")


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 3:
        print("Uso: python -m assessment_engine.scripts.run_tower_blueprint_engine <client> <tower_id>")
        sys.exit(1)
    asyncio.run(run_tower_blueprint((argv if argv is not None else sys.argv)[1], (argv if argv is not None else sys.argv)[2]))

if __name__ == "__main__":
    main()
