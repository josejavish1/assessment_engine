"""
Módulo run_intelligence_harvesting.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import sys
from pathlib import Path

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from assessment_engine.prompts.intelligence_prompts import (
    get_auditor_harvester_prompt,
    get_business_harvester_prompt,
    get_regulatory_harvester_prompt,
    get_tech_harvester_prompt,
)
from assessment_engine.schemas.intelligence import (
    BusinessHarvest,
    ClientDossier,
    RegulatoryHarvest,
    TechHarvest,
)
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.runtime_paths import resolve_client_intelligence_path


async def run_market_intelligence(client_name: str, output_path: Path):
    print(f"\n🔍 Iniciando Inteligencia de Mercado para: {client_name}")

    agent = Agent(
        name="osint_agent",
        model="gemini-2.5-pro",
        instruction="Eres un analista de inteligencia de mercado B2B de NTT DATA. Tu objetivo es buscar en la web y proporcionar datos basados en evidencias reales.",
    )
    app = AdkApp(agent=agent)
    
    # Archivos para logs raw
    raw_reg_file = output_path.parent / "raw_harvester_reg.txt"
    raw_biz_file = output_path.parent / "raw_harvester_biz.txt"
    raw_tech_file = output_path.parent / "raw_harvester_tech.txt"
    raw_audit_file = output_path.parent / "raw_auditor_agent.txt"

    # --- ETAPA 1: LOS HARVESTERS ---

    print("  -> Ejecutando Harvester Regulatorio...")
    reg_data = await run_agent(
        app, 
        user_id="harvester_reg", 
        message=get_regulatory_harvester_prompt(client_name),
        raw_output_file=raw_reg_file,
        schema=RegulatoryHarvest
    )

    print("  -> Ejecutando Harvester de Negocio (Agenda del CEO y Finanzas)...")
    biz_data = await run_agent(
        app, 
        user_id="harvester_biz", 
        message=get_business_harvester_prompt(client_name),
        raw_output_file=raw_biz_file,
        schema=BusinessHarvest
    )

    print("  -> Ejecutando Harvester Tecnológico (OSINT)...")
    tech_data = await run_agent(
        app, 
        user_id="harvester_tech", 
        message=get_tech_harvester_prompt(client_name),
        raw_output_file=raw_tech_file,
        schema=TechHarvest
    )

    # --- ETAPA 2: LA SÍNTESIS ---
    print("  -> Preparando borrador (Analista)...")
    raw_dossier = {
        "client_name": client_name,
        "industry": reg_data.get("sector"),
        "financial_tier": biz_data.get("financial_tier"),
        "regulatory_frameworks": reg_data.get("frameworks", []),
        "ceo_agenda": biz_data.get("ceo_agenda"),
        "technological_drivers": biz_data.get("business_drivers", []) + tech_data.get("tech_trends", []),
        "osint_footprint": tech_data.get("tech_footprint"),
        "transformation_horizon": "Pendiente de evaluación del Auditor.",
        "target_maturity_matrix": {},
        "evidences": [
            reg_data.get("source_evidence", ""),
            biz_data.get("source_evidence", ""),
            tech_data.get("source_evidence", ""),
        ],
    }

    # --- ETAPA 3: LA AUDITORÍA (Red Team) ---
    print("  -> Verificación de Coherencia y Madurez (Auditor)...")
    final_dossier = await run_agent(
        app, 
        user_id="auditor_agent", 
        message=get_auditor_harvester_prompt(json.dumps(raw_dossier)),
        raw_output_file=raw_audit_file,
        schema=ClientDossier
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(final_dossier, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"\n✅ Dossier de Inteligencia Estratégica completado: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python run_intelligence_harvesting.py <client_name>")
        sys.exit(1)

    client_name = sys.argv[1]
    output_path = resolve_client_intelligence_path(client_name)

    asyncio.run(run_market_intelligence(client_name, output_path))


if __name__ == "__main__":
    main()
