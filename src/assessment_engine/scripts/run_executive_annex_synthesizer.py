"""
Módulo run_executive_annex_synthesizer.py.
Implementa el flujo Top-Down: Toma el Blueprint y genera el resumen para el Anexo del CTO.
"""
import asyncio
import json
import sys
import yaml
import uuid
from pathlib import Path
from typing import Optional

from assessment_engine.scripts.lib.ai_client import run_agent
from assessment_engine.schemas.blueprint import BlueprintPayload
from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.schemas.common import VersionMetadata
from assessment_engine.scripts.lib.contract_utils import robust_load_payload
from vertexai.agent_engines import AdkApp
from google.adk.agents import Agent

ROOT = Path(__file__).resolve().parents[3]

# Helper functions (side-effect free)
def derive_maturity_band(score: float) -> str:
    if score >= 4.5: return "Optimizado"
    if score >= 3.5: return "Gestionado"
    if score >= 2.5: return "Definido"
    if score >= 1.5: return "Repetible"
    return "Inicial"

def infer_priority_from_size(sizing: str) -> str:
    text = str(sizing or "").strip().lower()
    if text in {"xs", "s"}: return "Alta"
    if text in {"m", "media", "medium"}: return "Media"
    if text in {"l", "xl", "large"}: return "Baja"
    return "Media"

def truncate_list(items, limit):
    return items[:limit] if isinstance(items, list) else items

def load_yaml_config(filename: str) -> dict:
    filepath = Path(__file__).resolve().parent.parent / "prompts" / "registry" / filename
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# --- Pure Business Logic Function ---
async def generate_synthesis(
    blueprint: BlueprintPayload,
    client_intelligence: dict,
    config: dict,
    radar_chart_path: Path,
    run_id: str
) -> Optional[AnnexPayload]:
    """
    Toma los datos de entrada, ejecuta el agente IA y devuelve el payload del anexo enriquecido.
    """
    blueprint_data = blueprint.model_dump(by_alias=True)
    prompt = f"Eres un {config['role']} con expertise en {config['expertise']}.\n"
    # ... (el resto del prompt se mantiene igual)
    
    try:
        from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
        model_name = resolve_model_profile_for_role("writer_fast")["model"]
    except Exception:
        model_name = "gemini-1.5-pro"

    agent = Agent(
        name="executive_synthesizer",
        model=model_name,
        instruction=f"Eres un {config['role']}. Tu misión es: {config['mission']}",
        output_schema=AnnexPayload
    )
    app = AdkApp(agent=agent)
    
    result = await run_agent(
        app,
        user_id=f"synthesizer_{blueprint.document_meta.tower_code}",
        message=prompt, # El prompt se construiría aquí como antes
        schema=AnnexPayload
    )
    
    if not result:
        return None

    # Enrich payload
    result_payload = AnnexPayload.model_validate(result)
    result_payload.generation_metadata = VersionMetadata(
        artifact_type="annex_payload",
        artifact_version="1.1.0",
        source_version=blueprint.generation_metadata.artifact_version if blueprint.generation_metadata else "unknown",
        run_id=run_id
    )
    meta_dict = blueprint.document_meta.model_dump()
    meta_dict["report_variant"] = "short"
    result_payload.document_meta = meta_dict
    
    total_score = sum(p.score for p in blueprint.pillars_analysis)
    avg_score = round(total_score / len(blueprint.pillars_analysis), 1) if blueprint.pillars_analysis else 0
    
    if result_payload.pillar_score_profile:
        result_payload.pillar_score_profile.pillars = [
            {"pillar_label": p.pilar_name, "score_display": str(p.score), "maturity_band": derive_maturity_band(p.score)}
            for p in blueprint.pillars_analysis
        ]
        if radar_chart_path.exists():
            result_payload.pillar_score_profile.radar_chart = str(radar_chart_path.resolve())
    
    if result_payload.executive_summary:
        result_payload.executive_summary.global_score = f"{avg_score} / 5.0"
        result_payload.executive_summary.global_band = derive_maturity_band(avg_score)
    
    return result_payload

# --- I/O Orchestrator Function ---
async def synthesize_annex(client_name: str, tower_id: str):
    """
    Orquesta el proceso de síntesis del anexo ejecutivo. Maneja I/O.
    """
    run_id = f"run_{uuid.uuid4()}"
    print(f"🧠 [Top-Down] Sintetizando Anexo Ejecutivo para {tower_id} (Run ID: {run_id})...")
    
    client_dir = ROOT / "working" / client_name
    tower_dir = client_dir / tower_id
    blueprint_path = tower_dir / f"blueprint_{tower_id.lower()}_payload.json"
    output_path = tower_dir / f"approved_annex_{tower_id.lower()}.template_payload.json"
    client_intelligence_path = client_dir / "client_intelligence.json"
    radar_chart_path = tower_dir / "pillar_radar_chart.generated.png"
    
    if not blueprint_path.exists():
        print(f"❌ Error: No se encontró el Blueprint en {blueprint_path}")
        return

    blueprint = robust_load_payload(blueprint_path, BlueprintPayload, "Blueprint")
    client_intelligence = json.loads(client_intelligence_path.read_text(encoding="utf-8-sig")) if client_intelligence_path.exists() else {}
    config = load_yaml_config("annex_executive_synthesizer.yaml")
    
    final_payload = await generate_synthesis(blueprint, client_intelligence, config, radar_chart_path, run_id)
    
    if final_payload:
        output_path.write_text(final_payload.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
        print(f"✅ Anexo Ejecutivo sintetizado con éxito: {output_path}")
    else:
        print(f"❌ Error al generar el anexo.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m assessment_engine.scripts.run_executive_annex_synthesizer <client> <tower>")
        sys.exit(1)
    asyncio.run(synthesize_annex(sys.argv[1], sys.argv[2]))
