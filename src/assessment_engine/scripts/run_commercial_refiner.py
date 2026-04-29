"""
Módulo run_commercial_refiner.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import sys
from pathlib import Path
from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.schemas.commercial import (
    AccountDirectorOutput,
    PresalesArchitectOutput,
    EngagementManagerOutput,
    LeadSolutionsArchitectOutput,
    DeliveryAndRiskDirectorOutput,
    SalesPartnerOutput,
)
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
from assessment_engine.prompts.commercial_prompts import (
    get_commercial_orchestrator_instruction,
    get_commercial_agent_prompt
)

ROOT = Path(__file__).resolve().parents[1]


async def call_commercial_agent(
    model_name, agent_role, instruction, payload_str, schema_cls, client_name="el cliente"
):
    from google.adk.agents import Agent
    from vertexai.agent_engines import AdkApp
    from assessment_engine.prompts.commercial_prompts import get_commercial_orchestrator_instruction

    agent = Agent(
        model=model_name,
        name=f"commercial_{agent_role.replace(' ', '')[-10:]}",
        instruction=get_commercial_orchestrator_instruction(),
        output_schema=schema_cls
    )
    app = AdkApp(agent=agent)

    prompt = get_commercial_agent_prompt(
        agent_role=agent_role, 
        instruction=instruction, 
        payload_str=payload_str
    )

    try:
        result = await run_agent(
            app,
            user_id=f"commercial-{agent_role.replace(' ', '')[-10:]}",
            message=prompt,
            schema=schema_cls
        )
        return result
    except Exception as e:
        print(f"Error parseando sección de {agent_role}: {e}")
        return {}


async def build_proactive_proposal(model_name, opp, payload_str, client_name):
    opp_name = opp.get("initiative", "Iniciativa Estratégica")
    print(
        f"    -> 🟢 Agente A1 (Engagement Manager): Contexto y Valor para '{opp_name}'..."
    )
    ag1 = await call_commercial_agent(
        model_name,
        "ENGAGEMENT MANAGER",
        f"Genera el contexto y visión para la oportunidad '{opp_name}'.",
        payload_str,
        EngagementManagerOutput,
        client_name,
    )

    print(
        f"    -> 🔵 Agente A2 (Lead Solutions Architect): Alcance Técnico para '{opp_name}'..."
    )
    ag2 = await call_commercial_agent(
        model_name,
        "LEAD SOLUTIONS ARCHITECT",
        f"Genera el alcance y equipo de delivery para la oportunidad '{opp_name}'.",
        payload_str,
        LeadSolutionsArchitectOutput,
        client_name,
    )

    print(
        f"    -> 🟠 Agente A3 (Delivery & Risk Director): Gobierno y Riesgos para '{opp_name}'..."
    )
    ag3 = await call_commercial_agent(
        model_name,
        "DELIVERY & RISK DIRECTOR",
        f"Genera el modelo de gobierno, asunciones y riesgos para la oportunidad '{opp_name}'.",
        payload_str,
        DeliveryAndRiskDirectorOutput,
        client_name,
    )

    print(f"    -> 🔴 Agente A4 (Sales Partner): Pitch Final para '{opp_name}'...")
    ag4 = await call_commercial_agent(
        model_name,
        "SALES PARTNER",
        f"Genera los diferenciadores de NTT Data y el timeline de inversión para la oportunidad '{opp_name}'.",
        payload_str,
        SalesPartnerOutput,
        client_name,
    )

    proposal = {
        "initiative_name": opp_name,
        "context_and_why": ag1.get("context_and_why", {}),
        "solution_and_what": ag1.get("solution_and_what", {}),
        "scope_and_how": ag2.get("scope_and_how", {}),
        "delivery_team": ag2.get("delivery_team", {}),
        "ai_transformation_strategy": ag2.get("ai_transformation_strategy", ""),
        "governance_and_assumptions": ag3.get("governance_and_assumptions", {}),
        "risk_management": ag3.get("risk_management", []),
        "activation_plan": ag3.get("activation_plan", []),
        "why_ntt_data": ag4.get("why_ntt_data", {}),
        "investment_and_timeline": ag4.get("investment_and_timeline", {}),
        "executive_synthesis": ag4.get("executive_synthesis", ""),
    }
    return proposal


def aggregate_blueprint_catalogs(blueprint_paths: list[Path]) -> dict:
    """Consolida el catálogo técnico de todos los blueprints encontrados."""
    catalog = {}
    for bp_path in blueprint_paths:
        try:
            with bp_path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)
            
            tower_id = data.get("document_meta", {}).get("tower_code", "UNKNOWN")
            tower_name = data.get("document_meta", {}).get("tower_name", "UNKNOWN")
            
            tower_entry = {
                "tower_name": tower_name,
                "executive_bottom_line": data.get("executive_snapshot", {}).get("bottom_line", ""),
                "technical_debt": data.get("cross_capabilities_analysis", {}).get("critical_technical_debt", ""),
                "initiatives": []
            }
            
            for pilar in data.get("pillars_analysis", []):
                for proj in pilar.get("projects_todo", []):
                    tower_entry["initiatives"].append({
                        "name": proj.get("initiative") or proj.get("name"),
                        "objective": proj.get("objective") or proj.get("tech_objective"),
                        "sizing": proj.get("sizing"),
                        "deliverables": proj.get("deliverables", [])
                    })
            
            catalog[tower_id] = tower_entry
        except Exception as e:
            print(f"⚠️ Error cargando blueprint {bp_path}: {e}")
            
    return catalog


async def refine_commercial_payload(payload, blueprints_catalog: dict = None):
    try:
        model_name = resolve_model_profile_for_role("global_refiner")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    # Construir contexto híbrido
    hybrid_context = {
        "strategic_global_context": payload,
        "tactical_tower_blueprints": blueprints_catalog or {}
    }
    payload_str = json.dumps(hybrid_context, ensure_ascii=False)
    client_name = payload.get("meta", {}).get("client", "el cliente")

    final_payload = {
        "_generation_metadata": {
            "artifact_type": "commercial_payload",
            "artifact_version": "1.0.0",
        },
        "meta": payload.get("meta", {}),
        "intelligence_dossier": {
            "source_blueprints": list((blueprints_catalog or {}).keys())
        }
    }

    print(
        "\nFase 1: Estrategia de Cuenta (Agente 1: Global Account Director) ----------"
    )
    strategy = await call_commercial_agent(
        model_name,
        "GLOBAL ACCOUNT DIRECTOR",
        "Diseña el Executive Summary Comercial, la Estrategia Go-to-Market y el Mapa de Stakeholders basándote en la visión estratégica global.",
        payload_str,
        AccountDirectorOutput,
        client_name,
    )
    final_payload.update(strategy)

    print(
        "\nFase 2: Calificación de Pipeline (Agente 2: Presales Architect) ----------"
    )
    pipeline = await call_commercial_agent(
        model_name,
        "ENTERPRISE PRESALES ARCHITECT",
        "Analiza el Roadmap Global y CRÚZALO con el catálogo 'tactical_tower_blueprints'. Genera un pipeline de oportunidades combinando las grandes iniciativas con los Quick Wins técnicos detectados en las torres (como Chaos Engineering, automatizaciones, BIA, etc.). Evalúa: vendor, revenue type, TCV y Manejo de Objeciones.",
        payload_str,
        PresalesArchitectOutput,
        client_name,
    )
    final_payload["opportunities_pipeline"] = pipeline.get(
        "opportunities_pipeline", []
    )

    print(
        "\nFase 3: Propuestas Proactivas (Orquestación Multi-Agente) ----------------"
    )
    opps = final_payload.get("opportunities_pipeline", [])
    top_opps = opps[:2]
    proposals = []

    for idx, opp in enumerate(top_opps, start=1):
        print(f"\n  [Orquestando Proposal {idx}/2]")
        proposal = await build_proactive_proposal(model_name, opp, payload_str, client_name)
        proposals.append(proposal)

    final_payload["proactive_proposals"] = proposals

    return final_payload


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python run_commercial_refiner.py <global_payload_json>")
        sys.exit(1)

    payload_path = Path((argv if argv is not None else sys.argv)[1]).resolve()
    client_dir = payload_path.parent
    
    with payload_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    # Buscar blueprints tácticos
    blueprint_paths = list(client_dir.glob("T*/blueprint_*_payload.json"))
    print(f"🔍 Encontrados {len(blueprint_paths)} blueprints técnicos para el contexto híbrido.")
    catalog = aggregate_blueprint_catalogs(blueprint_paths)

    final_payload = asyncio.run(refine_commercial_payload(payload, blueprints_catalog=catalog))

    output_path = payload_path.parent / "commercial_report_payload.json"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Payload comercial refinado guardado en: {output_path}")


if __name__ == "__main__":
    main()
