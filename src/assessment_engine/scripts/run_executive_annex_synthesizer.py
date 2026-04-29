"""
Módulo run_executive_annex_synthesizer.py.
Implementa el flujo Top-Down: Toma el Blueprint y genera el resumen para el Anexo del CTO.
"""
import asyncio
import json
import sys
import yaml
from pathlib import Path
from typing import Optional

from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.schemas.blueprint import BlueprintPayload
from assessment_engine.schemas.annex_synthesis import AnnexPayload
from vertexai.agent_engines import AdkApp
from google.adk.agents import Agent

ROOT = Path(__file__).resolve().parents[3]


def derive_maturity_band(score: float) -> str:
    if score >= 4.5:
        return "Optimizado"
    if score >= 3.5:
        return "Gestionado"
    if score >= 2.5:
        return "Definido"
    if score >= 1.5:
        return "Repetible"
    return "Inicial"


def infer_priority_from_size(sizing: str) -> str:
    text = str(sizing or "").strip().lower()
    if text in {"xs", "s"}:
        return "Alta"
    if text in {"m", "media", "medium"}:
        return "Media"
    if text in {"l", "xl", "large"}:
        return "Baja"
    return "Media"


def truncate_list(items, limit):
    return items[:limit] if isinstance(items, list) else items

def load_yaml_config(filename: str) -> dict:
    filepath = Path(__file__).resolve().parent.parent / "prompts" / "registry" / filename
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

from assessment_engine.scripts.lib.contract_utils import robust_load_payload

async def synthesize_annex(client_name: str, tower_id: str):
    print(f"🧠 [Top-Down] Sintetizando Anexo Ejecutivo para {tower_id}...")
    
    client_dir = ROOT / "working" / client_name
    tower_dir = client_dir / tower_id
    blueprint_path = tower_dir / f"blueprint_{tower_id.lower()}_payload.json"
    output_path = tower_dir / f"approved_annex_{tower_id.lower()}.template_payload.json"
    client_intelligence_path = client_dir / "client_intelligence.json"
    radar_chart_path = tower_dir / "pillar_radar_chart.generated.png"
    
    if not blueprint_path.exists():
        print(f"❌ Error: No se encontró el Blueprint en {blueprint_path}")
        return

    # 1. Cargar la Verdad Técnica (Blueprint) de forma robusta
    blueprint = robust_load_payload(blueprint_path, BlueprintPayload, "Blueprint")
    blueprint_data = blueprint.model_dump(by_alias=True)
    client_intelligence = {}
    if client_intelligence_path.exists():
        client_intelligence = json.loads(
            client_intelligence_path.read_text(encoding="utf-8-sig")
        )
    
    # 2. Cargar Instrucciones YAML
    config = load_yaml_config("annex_executive_synthesizer.yaml")
    
    prompt = f"Eres un {config['role']} con expertise en {config['expertise']}.\n"
    prompt += config['context_description'].format(tower_name=blueprint.document_meta.tower_name) + "\n\n"
    prompt += f"BLUEPRINT TÉCNICO DE REFERENCIA (Única fuente de verdad):\n{blueprint.model_dump_json(indent=2)}\n\n"
    if client_intelligence:
        prompt += "CONTEXTO ESTRATÉGICO DEL CLIENTE (prioridad editorial, no fuente alternativa de hechos):\n"
        prompt += json.dumps(
            {
                "ceo_agenda": client_intelligence.get("ceo_agenda", ""),
                "technological_drivers": client_intelligence.get("technological_drivers", []),
                "transformation_horizon": client_intelligence.get("transformation_horizon", ""),
                "regulatory_frameworks": client_intelligence.get("regulatory_frameworks", []),
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n\n"
    snapshot = blueprint_data.get("executive_snapshot", {})
    if snapshot:
        prompt += "PALANCAS EJECUTIVAS QUE DEBEN GUIAR EL TONO DEL ANEXO:\n"
        prompt += json.dumps(
            {
                "bottom_line": snapshot.get("bottom_line", ""),
                "cost_of_inaction": snapshot.get("cost_of_inaction", ""),
                "business_impact": snapshot.get("business_impact", ""),
                "key_decisions": snapshot.get("decisions", []),
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n\n"
    prompt += "TAREA:\n" + config['task'] + "\n\n"
    prompt += "INSTRUCCIONES ESPECÍFICAS:\n"
    for ins in config['instructions']:
        prompt += f"- {ins}\n"
    
    prompt += "\nREGLAS DE TONO:\n"
    for rule in config['tone_rules']:
        prompt += f"- {rule}\n"

    prompt += "\nRESTRICCIONES EDITORIALES ADICIONALES:\n"
    prompt += "- El anexo debe sonar a documento para comité de dirección, no a documento de arquitectura.\n"
    prompt += "- Prioriza continuidad de operación, crecimiento, M&A, regulación, plataforma de datos e IA sobre detalle técnico.\n"
    prompt += "- Si un término técnico no cambia una decisión ejecutiva, omítelo.\n"
    prompt += "- El valor del TO-BE debe expresarse como capacidad de negocio, no como diseño de plataforma.\n"

    prompt += f"\n{config['handover']}\n"

    # 3. Llamar a la IA
    try:
        from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
        model_name = resolve_model_profile_for_role("writer_fast")["model"]
    except Exception:
        model_name = "gemini-2.5-pro"

    agent = Agent(
        name="executive_synthesizer",
        model=model_name,
        instruction=f"Eres un {config['role']}. Tu misión es: {config['mission']}",
        output_schema=AnnexPayload
    )
    app = AdkApp(agent=agent)
    
    result = await run_agent(
        app,
        user_id=f"synthesizer_{tower_id}",
        message=prompt,
        schema=AnnexPayload
    )
    
    if result:
        # Inyectar metadatos de versión
        result['_generation_metadata'] = {
            "artifact_type": "annex_payload",
            "artifact_version": "1.0.0",
            "source_version": blueprint.generation_metadata.artifact_version if blueprint.generation_metadata else "unknown"
        }
        # Enriquecer con metadatos y datos del blueprint que no necesitan IA
        meta_dict = blueprint.document_meta.model_dump()
        meta_dict["report_variant"] = "short" # Forzar variante corta por defecto para el Anexo Ejecutivo
        result['document_meta'] = meta_dict
        
        # Mapear scores y pilares directamente desde el Blueprint
        total_score = 0
        pillars_list = []
        for p in blueprint.pillars_analysis:
            total_score += p.score
            band = derive_maturity_band(p.score)
            pillars_list.append({
                "pillar_label": p.pilar_name,
                "score_display": str(p.score),
                "maturity_band": band,
                "executive_reading": p.health_check_asis[0].risk_observed if p.health_check_asis else "N/A"
            })
            
        avg_score = round(total_score / len(blueprint.pillars_analysis), 1) if blueprint.pillars_analysis else 0
        global_band = derive_maturity_band(avg_score)
        
        result['pillar_score_profile']['pillars'] = pillars_list
        if radar_chart_path.exists():
            result['pillar_score_profile']['radar_chart'] = str(radar_chart_path)
        result['executive_summary']['global_score'] = f"{avg_score} / 5.0"
        result['executive_summary']['global_band'] = global_band
        result['executive_summary']['target_maturity'] = str(blueprint.pillars_analysis[0].target_score) if blueprint.pillars_analysis else "4.0"
        
        # Mapear los riesgos, gaps e iniciativas directamente desde el Blueprint (Single Source of Truth)
        risks_mapped = []
        gaps_mapped = []
        initiatives_mapped = []
        target_capabilities_mapped = []
        
        for p in blueprint.pillars_analysis:
            target_capabilities_mapped.append(f"{p.pilar_name}: {p.target_architecture_tobe.vision}")
            
            for asis in p.health_check_asis:
                risks_mapped.append({
                    "risk": f"{p.pilar_name}: {asis.risk_observed}",
                    "impact": asis.impact,
                    "probability": "Alta",
                    "mitigation_summary": asis.target_state,
                })
                gaps_mapped.append({
                    "pillar": p.pilar_name,
                    "as_is_summary": asis.risk_observed,
                    "target_state": asis.target_state,
                    "key_gap": asis.impact,
                })
                
            for proj in p.projects_todo:
                initiatives_mapped.append({
                    "initiative": proj.initiative,
                    "objective": proj.objective,
                    "priority": infer_priority_from_size(proj.sizing),
                    "expected_outcome": proj.expected_outcome,
                    "dependencies_display": ", ".join(proj.deliverables) if proj.deliverables else "Sin dependencias explícitas",
                })

        initiatives_mapped = [
            {"sequence": idx, **item}
            for idx, item in enumerate(truncate_list(initiatives_mapped, 6), start=1)
        ]
        risks_mapped = truncate_list(risks_mapped, 6)
        gaps_mapped = truncate_list(gaps_mapped, 6)
        target_capabilities_mapped = truncate_list(target_capabilities_mapped, 5)

        result['sections']['risks'] = {
            "introduction": "Los riesgos más materiales de esta torre se concentran en continuidad operativa, exposición regulatoria y capacidad real para sostener crecimiento y transformación.",
            "risks": risks_mapped, 
            "closing_summary": "La inacción amplifica el riesgo operativo y reduce la capacidad de ejecución de la agenda estratégica."
        }
        
        result['sections']['todo'] = {
            "introduction": "Las iniciativas se han priorizado por su capacidad de reducir riesgo material y habilitar continuidad, escalabilidad y ejecución estratégica.", 
            "priority_initiatives": initiatives_mapped, 
            "closing_summary": "El blueprint contiene el detalle técnico y de implantación de cada iniciativa."
        }
        
        result['sections']['gap'] = {
            "introduction": "Las brechas seleccionadas son las que hoy tienen mayor impacto sobre la resiliencia del negocio y la viabilidad del crecimiento.", 
            "target_capabilities": target_capabilities_mapped, 
            "gap_rows": gaps_mapped, 
            "closing_summary": "Cerrar estas brechas es condición necesaria para pasar de una resiliencia reactiva a una capacidad operativa verificable."
        }

        # Validar el payload final con el esquema Pydantic para asegurar consistencia total
        validated_payload = AnnexPayload.model_validate(result)
        final_json = validated_payload.model_dump(by_alias=True)

        # Guardar resultado
        output_path.write_text(json.dumps(final_json, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Anexo Ejecutivo sintetizado con éxito: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m assessment_engine.scripts.run_executive_annex_synthesizer <client> <tower>")
        sys.exit(1)
    asyncio.run(synthesize_annex(sys.argv[1], sys.argv[2]))
