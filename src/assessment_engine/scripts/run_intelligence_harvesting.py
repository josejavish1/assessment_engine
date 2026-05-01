"""
Módulo run_intelligence_harvesting.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import sys
from datetime import datetime, timezone
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
    ClientDossierV3,
    RegulatoryHarvest,
    TechHarvest,
)
from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.scripts.lib.client_intelligence import (
    build_confidence_block,
    estimate_confidence_score,
    infer_related_towers,
)
from assessment_engine.scripts.lib.runtime_paths import resolve_client_intelligence_path


async def run_market_intelligence(client_name: str, output_path: Path):
    print(f"\n🔍 Iniciando Inteligencia de Mercado para: {client_name}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

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
    now_iso = datetime.now(timezone.utc).isoformat()
    reg_source = reg_data.get("source_evidence", "")
    biz_source = biz_data.get("source_evidence", "")
    tech_source = tech_data.get("source_evidence", "")
    priority_markets = biz_data.get("priority_markets", [])
    business_lines = biz_data.get("business_lines", [])
    active_transformations = biz_data.get("active_transformations", [])
    business_constraints = biz_data.get("business_constraints", [])
    regulatory_pressures = reg_data.get("regulatory_pressures", [])
    vendor_dependencies = tech_data.get("vendor_dependencies", [])
    operating_constraints = tech_data.get("operating_constraints", [])
    recent_incident_signals = tech_data.get("recent_incident_signals", [])

    claims: list[dict] = []
    for index, framework in enumerate(reg_data.get("frameworks", []), start=1):
        score = estimate_confidence_score(source_count=1, specificity_signals=2)
        claims.append(
            {
                "claim_id": f"regulatory_{index}",
                "claim": f"El cliente está expuesto a {framework}.",
                "claim_type": "fact",
                "confidence": build_confidence_block(score),
                "sources": [{"source": reg_source}],
                "source_reliability_score": 70,
                "valid_for_domains": ["tower", "global", "commercial"],
                "related_towers": infer_related_towers(framework, " ".join(regulatory_pressures)),
            }
        )
    for index, driver in enumerate(biz_data.get("business_drivers", []), start=1):
        score = estimate_confidence_score(
            source_count=1,
            specificity_signals=1 + len(priority_markets) + len(business_lines),
        )
        claims.append(
            {
                "claim_id": f"business_driver_{index}",
                "claim": driver,
                "claim_type": "inference",
                "confidence": build_confidence_block(score),
                "sources": [{"source": biz_source}],
                "source_reliability_score": 65,
                "valid_for_domains": ["global", "commercial"],
                "related_towers": infer_related_towers(driver),
            }
        )
    for index, transformation in enumerate(active_transformations, start=1):
        score = estimate_confidence_score(
            source_count=1,
            specificity_signals=1 + len(priority_markets) + len(business_constraints),
        )
        claims.append(
            {
                "claim_id": f"transformation_{index}",
                "claim": transformation,
                "claim_type": "inference",
                "confidence": build_confidence_block(score),
                "sources": [{"source": biz_source}],
                "source_reliability_score": 65,
                "valid_for_domains": ["tower", "global", "commercial"],
                "related_towers": infer_related_towers(transformation, " ".join(business_constraints)),
            }
        )
    for index, trend in enumerate(tech_data.get("tech_trends", []), start=1):
        score = estimate_confidence_score(
            source_count=1,
            specificity_signals=1 + len(vendor_dependencies) + len(recent_incident_signals),
        )
        claims.append(
            {
                "claim_id": f"tech_trend_{index}",
                "claim": trend,
                "claim_type": "inference",
                "confidence": build_confidence_block(score),
                "sources": [{"source": tech_source}],
                "source_reliability_score": 65,
                "valid_for_domains": ["tower", "global", "commercial"],
                "related_towers": infer_related_towers(trend, tech_data.get("tech_footprint", "")),
            }
        )
    for index, vendor in enumerate(vendor_dependencies, start=1):
        score = estimate_confidence_score(
            source_count=1,
            specificity_signals=1 + len(operating_constraints),
        )
        claims.append(
            {
                "claim_id": f"vendor_dependency_{index}",
                "claim": f"Existe dependencia relevante de {vendor}.",
                "claim_type": "fact",
                "confidence": build_confidence_block(score),
                "sources": [{"source": tech_source}],
                "source_reliability_score": 65,
                "valid_for_domains": ["tower", "global", "commercial"],
                "related_towers": infer_related_towers(vendor, " ".join(operating_constraints)),
            }
        )
    for index, incident in enumerate(recent_incident_signals, start=1):
        score = estimate_confidence_score(source_count=1, specificity_signals=2, uncertainty_penalty=5)
        claims.append(
            {
                "claim_id": f"incident_signal_{index}",
                "claim": incident,
                "claim_type": "scenario",
                "confidence": build_confidence_block(score),
                "sources": [{"source": tech_source}],
                "source_reliability_score": 60,
                "valid_for_domains": ["tower", "global", "commercial"],
                "related_towers": infer_related_towers(incident, "resilience operations network"),
            }
        )

    raw_dossier = {
        "version": "3.0",
        "client_name": client_name,
        "metadata": {
            "dossier_id": f"{client_name}-draft",
            "schema_version": "3.0",
            "created_at": now_iso,
            "modified_at": now_iso,
            "last_verified_at": None,
            "lang": "es",
            "generated_by": "assessment_engine",
            "prompt_version": "intelligence_prompts_v3",
            "timeliness": {
                "created_at": now_iso,
                "modified_at": now_iso,
                "last_verified_at": None,
                "valid_until": None,
                "stale_after_days": 30,
            },
        },
        "profile": {
            "industry": reg_data.get("sector"),
            "financial_tier": biz_data.get("financial_tier"),
            "operating_model": None,
            "regions": [],
            "priority_markets": priority_markets,
            "business_lines": business_lines,
        },
        "regulatory_context": [
            {
                "name": framework,
                "applicability": "high",
                "confidence": build_confidence_block(
                    estimate_confidence_score(source_count=1, specificity_signals=2)
                ),
                "sources": [{"source": reg_source}],
                "impacted_domains": infer_related_towers(framework, " ".join(regulatory_pressures)),
            }
            for framework in reg_data.get("frameworks", [])
        ],
        "business_context": {
            "ceo_agenda": {
                "summary": biz_data.get("ceo_agenda"),
                "confidence": build_confidence_block(
                    estimate_confidence_score(
                        source_count=1,
                        specificity_signals=1 + len(priority_markets) + len(business_lines),
                    )
                ),
                "sources": [{"source": biz_source}],
                "evidence_strength": "medium",
            },
            "strategic_priorities": [
                {
                    "name": driver,
                    "confidence": build_confidence_block(
                        estimate_confidence_score(
                            source_count=1,
                            specificity_signals=1 + len(priority_markets),
                        )
                    ),
                    "sources": [{"source": biz_source}],
                    "rationale": None,
                }
                for driver in biz_data.get("business_drivers", [])
            ],
            "business_model_signals": business_lines,
            "active_transformations": active_transformations,
            "transformation_horizon": {
                "stage": "H1",
                "label": "Pending auditor validation",
                "rationale": "Pendiente de evaluación del Auditor.",
                "confidence": build_confidence_block(50),
                "sources": [],
            },
            "constraints": business_constraints,
        },
        "technology_context": {
            "footprint_summary": {
                "summary": tech_data.get("tech_footprint"),
                "confidence": build_confidence_block(
                    estimate_confidence_score(
                        source_count=1,
                        specificity_signals=1 + len(vendor_dependencies) + len(operating_constraints),
                    )
                ),
                "sources": [{"source": tech_source}],
                "evidence_strength": "medium",
            },
            "technology_drivers": [
                {
                    "name": trend,
                    "confidence": build_confidence_block(
                        estimate_confidence_score(
                            source_count=1,
                            specificity_signals=1 + len(vendor_dependencies),
                        )
                    ),
                    "sources": [{"source": tech_source}],
                    "rationale": None,
                }
                for trend in tech_data.get("tech_trends", [])
            ],
            "vendor_dependencies": vendor_dependencies,
            "operating_constraints": operating_constraints,
            "recent_incident_signals": recent_incident_signals,
        },
        "tower_overrides": {},
        "claims": claims,
        "review": {
            "human_review_status": "pending",
            "approved_by": None,
            "approved_at": None,
            "review_notes": [],
        },
        "extensions": {
            "regulatory_pressures": regulatory_pressures,
        },
    }

    # --- ETAPA 3: LA AUDITORÍA (Red Team) ---
    print("  -> Verificación de Coherencia y Madurez (Auditor)...")
    final_dossier = await run_agent(
        app, 
        user_id="auditor_agent", 
        message=get_auditor_harvester_prompt(json.dumps(raw_dossier)),
        raw_output_file=raw_audit_file,
        schema=ClientDossierV3
    )

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
