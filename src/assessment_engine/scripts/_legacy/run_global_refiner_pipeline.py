"""
Módulo run_global_refiner_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import vertexai
from google.adk.agents import Agent
from assessment_engine.scripts.lib.ai_client import run_agent
from vertexai.agent_engines import AdkApp

from assessment_engine.schemas.global_report import GlobalRefinerDraft
from assessment_engine.scripts.lib.config_loader import resolve_model_profile_for_role
from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults
from assessment_engine.prompts.global_prompts import (
    get_global_refiner_instruction,
    get_global_refiner_prompt
)

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def apply_edits_to_annex(annex: dict, edits: list[dict]) -> tuple[dict, int]:
    applied_count = 0
    # Lógica simplificada de parches, iterando los edits del agente
    for edit in edits:
        path_str = edit.get("path", "")
        action = edit.get("action", "")
        value = edit.get("value")
        
        if not path_str or not action:
            continue
            
        parts = path_str.strip("/").split("/")
        current = annex
        try:
            for i, part in enumerate(parts[:-1]):
                if isinstance(current, dict):
                    current = current[part]
                elif isinstance(current, list):
                    current = current[int(part)]
            
            last_part = parts[-1]
            if action == "replace":
                if isinstance(current, dict):
                    current[last_part] = value
                    applied_count += 1
                elif isinstance(current, list):
                    current[int(last_part)] = value
                    applied_count += 1
            elif action == "delete":
                if isinstance(current, dict):
                    del current[last_part]
                    applied_count += 1
                elif isinstance(current, list):
                    del current[int(last_part)]
                    applied_count += 1
        except Exception as e:
            print(f"Warning: Fallo al aplicar edit {edit}: {e}")
            
    return annex, applied_count


async def run_global_refiner(
    tower_dir: str,
    tower_id: str,
    tower_name: str,
):
    ensure_google_cloud_env_defaults()
    project = os.environ["GOOGLE_CLOUD_PROJECT"]
    location = os.environ["GOOGLE_CLOUD_LOCATION"]

    vertexai.Client(project=project, location=location)

    refiner_model_profile = resolve_model_profile_for_role("global_refiner")

    case_dir = Path(tower_dir)
    approved_annex_file = case_dir / "approved_annex_t5.generated.json"
    review_report_file = case_dir / "global_review_report.json"

    annex = load_json(approved_annex_file)
    review_report = load_json(review_report_file)

    if review_report.get("status") == "approve":
        print("El documento ya está aprobado globalmente. No se requiere refinado.")
        output_file = case_dir / "approved_annex_refined.json"
        save_json(output_file, annex)
        return

    refiner_agent = Agent(
        model=refiner_model_profile["model"],
        name="t5_global_refiner_agent",
        instruction=get_global_refiner_instruction()
    )
    refiner_app = AdkApp(agent=refiner_agent)

    print(f"\n=== Iniciando Global Refiner para {tower_id} ===")

    prompt = get_global_refiner_prompt(
        tower_id=tower_id,
        tower_name=tower_name,
        annex_json=json.dumps(annex, ensure_ascii=False, indent=2),
        review_report_json=json.dumps(review_report, ensure_ascii=False, indent=2)
    )

    refiner_data = await run_agent(
        refiner_app,
        user_id="global_refiner_local_dev",
        message=prompt,
        schema=GlobalRefinerDraft
    )

    if not refiner_data:
        raise RuntimeError("No se pudo obtener el plan de refinado.")

    edits = refiner_data.get("edits", [])
    if edits:
        refined_annex, count = apply_edits_to_annex(annex, edits)
        print(f"✅ Refinado aplicado: {count} parches ejecutados.")
    else:
        refined_annex = annex
        print("✅ No se requirieron parches estructurales.")

    output_file = case_dir / "approved_annex_refined.json"
    save_json(output_file, refined_annex)
    
    plan_file = case_dir / "global_refiner_plan.json"
    save_json(plan_file, refiner_data)


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) != 4:
        print(
            "Uso: python -m assessment_engine.scripts.run_global_refiner_pipeline <tower_dir> <tower_id> <tower_name>"
        )
        sys.exit(1)

    tower_dir = (argv if argv is not None else sys.argv)[1]
    tower_id = (argv if argv is not None else sys.argv)[2]
    tower_name = (argv if argv is not None else sys.argv)[3]

    asyncio.run(run_global_refiner(tower_dir, tower_id, tower_name))


if __name__ == "__main__":
    main()
