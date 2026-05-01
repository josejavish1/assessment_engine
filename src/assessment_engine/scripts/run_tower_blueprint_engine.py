"""
Módulo run_tower_blueprint_engine.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import sys
from assessment_engine.schemas.blueprint import (
    PillarBlueprintDraft, 
    OrchestratorBlueprintDraft, 
    BlueprintPayload,
    ExecutiveSnapshot,
    CrossCapabilitiesAnalysis
)
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.prompts.blueprint_prompts import (
    get_blueprint_architect_instruction,
    get_pilar_architect_prompt,
    get_critic_prompt,
    get_closing_orchestrator_prompt
)
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_blueprint_payload_path,
    resolve_case_input_path,
    resolve_client_intelligence_path,
    resolve_client_dir,
    resolve_tower_definition_file,
)
from assessment_engine.scripts.lib.client_intelligence import (
    build_client_context_packet,
    build_client_context_text,
    client_intelligence_to_legacy,
    get_target_maturity,
    load_client_intelligence,
)

def get_default_blueprint_payload(client_name, tower_name, tower_id, intel_data) -> dict:
    """Provee una estructura base completa que cumple con el contrato de BlueprintPayload."""
    return {
        "document_meta": {
            "client_name": client_name,
            "tower_name": tower_name,
            "tower_code": tower_id,
            "financial_tier": intel_data.get("financial_tier", "Tier 2"),
            "transformation_horizon": intel_data.get("transformation_horizon", "General"),
        },
        "executive_snapshot": {
            "bottom_line": "Análisis estratégico pendiente de consolidación por el orquestador.",
            "decisions": [],
            "cost_of_inaction": "El retraso en la transformación mantiene los riesgos operativos actuales.",
            "structural_risks": [],
            "business_impact": "Pendiente de determinar impacto detallado.",
            "operational_benefits": [],
            "transformation_complexity": "Media (estimación base)"
        },
        "cross_capabilities_analysis": {
            "common_deficiency_patterns": [],
            "transformation_paradigm": "Evolución por dominios técnicos.",
            "critical_technical_debt": "Deuda técnica identificada en los pilares individuales."
        },
        "roadmap": [],
        "external_dependencies": [],
        "pillars_analysis": [],
    }

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
    client_dir = resolve_client_dir(client_name)
    tower_dir = client_dir / tower_id
    case_input_path = resolve_case_input_path(client_name, tower_id)
    intel_path = resolve_client_intelligence_path(client_name)

    if not case_input_path.exists():
        print(f"Error: No se encuentra input para {tower_id}")
        return

    case_data = json.loads(case_input_path.read_text(encoding="utf-8"))
    raw_intel_data = {}
    intel_data = {}
    intel_packet = {}
    if intel_path.exists():
        raw_intel_data = load_client_intelligence(intel_path)
        intel_data = client_intelligence_to_legacy(raw_intel_data)
        intel_packet = build_client_context_packet(raw_intel_data, tower_id=tower_id)

    tower_name = case_data.get("tower_name")

    # Preparar contexto masivo
    intel_str = (
        build_client_context_text(raw_intel_data, tower_id=tower_id)
        if intel_packet
        else json.dumps(intel_data, indent=2, ensure_ascii=False)
    )
    context_str = case_data.get("context_summary", "")
    if case_data.get("client_context") and not intel_packet:
        intel_str = json.dumps(case_data.get("client_context", {}), indent=2, ensure_ascii=False)

    try:
        from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
        model_name = resolve_model_profile_for_role("section_writer")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    # Agrupar respuestas por pilar
    pillars_map = {}
    tower_def_path = resolve_tower_definition_file(tower_id)
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

    # Inicialización Normalizada (Contrato Estricto)
    blueprint_payload = get_default_blueprint_payload(client_name, tower_name, tower_id, intel_data)
    if intel_packet:
        blueprint_payload["client_context"] = intel_packet
    failed_pillars = []

    # PROCESAR PILARES EN SERIE PARA MÁXIMA CALIDAD
    for p_id in sorted(pillars_map.keys()):
        p_result = await process_pilar_blueprint(
            model_name, client_name, tower_name, pillars_map[p_id], context_str, intel_str
        )
        if p_result:
            p_result["score"] = pillars_map[p_id]["score"]
            p_result["target_score"] = get_target_maturity(intel_data, tower_id, 4.0)
            blueprint_analysis = p_result.get("pillar_analysis", p_result)
            blueprint_payload["pillars_analysis"].append(blueprint_analysis)
        else:
            failed_pillars.append(pillars_map[p_id]["label"])

    if failed_pillars:
        print(
            "⚠️ Pilares sin respuesta válida: "
            + ", ".join(failed_pillars)
        )

    if not blueprint_payload["pillars_analysis"]:
        raise RuntimeError(
            "No se pudo generar ningún análisis de pilar para el blueprint."
        )

    # AGENTE DE CIERRE: SNAPSHOT Y ROADMAP
    print("    -> Generando Snapshot Ejecutivo y Roadmap Estratégico...")
    closing_prompt = get_closing_orchestrator_prompt(
        tower_name=tower_name,
        pillars_analysis_json=json.dumps(blueprint_payload["pillars_analysis"]),
        intel_str=intel_str
    )
    try:
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
            # Actualizamos solo si recibimos datos válidos del agente
            blueprint_payload.update(closing_data)
    except Exception as e:
        raise RuntimeError(f"Error en agente de cierre blueprint: {e}") from e

    # Validación Final del Contrato con Pydantic
    try:
        blueprint_payload["_generation_metadata"] = {
            "artifact_type": "blueprint_payload",
            "artifact_version": "1.0.0",
        }
        # Forzamos validación para asegurar que el JSON resultante sea íntegro
        validated_model = BlueprintPayload.model_validate(blueprint_payload)
        final_payload_dict = validated_model.model_dump(by_alias=True)
    except Exception as val_err:
        raise RuntimeError(
            f"Error de validación en payload final del blueprint: {val_err}"
        ) from val_err

    # GUARDAR PAYLOAD
    output_path = resolve_blueprint_payload_path(client_name, tower_id)
    output_path.write_text(
        json.dumps(final_payload_dict, indent=2, ensure_ascii=False),
        encoding="utf-8-sig",
    )
    print(f"✅ Payload del Blueprint generado y validado: {output_path}")



def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 3:
        print("Uso: python -m assessment_engine.scripts.run_tower_blueprint_engine <client> <tower_id>")
        sys.exit(1)
    asyncio.run(run_tower_blueprint((argv if argv is not None else sys.argv)[1], (argv if argv is not None else sys.argv)[2]))

if __name__ == "__main__":
    main()
