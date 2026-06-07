"""
Módulo run_executive_refiner.py (TIER 1 EDITION 2026 - SELF HEALING).
Aplica el Manual de Estilo Soberano con reintentos automáticos ante violaciones de tono.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, cast

from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from domain.prompts.intelligence_prompts import (
    get_global_refiner_prompt,
    get_tower_refiner_prompt,
)
from infrastructure.ai_client import run_agent
from infrastructure.governance import (
    SecurityIntegrityViolation,
)
from infrastructure.runtime_paths import resolve_client_intelligence_path


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


async def refine_findings(client_name: str, findings: dict) -> dict:
    print("    -> [Refinado Ejecutivo] Aplicando Estándares Tier 1...")

    intel_path = resolve_client_intelligence_path(client_name)
    grounding_data = {}
    if intel_path.exists():
        grounding_data = load_json(intel_path)

    agent = Agent(
        name="executive_refiner",
        model="gemini-2.5-pro",
        instruction="Eres un Partner de una firma de consultoría estratégica. Tu tono es frío, profesional e impecable. Devuelve ÚNICAMENTE JSON.",
    )
    app = AdkApp(agent=agent)

    # Detectar tipo de informe
    is_global = (
        "executive_summary" in findings
        and "burning_platform" in findings
        and "tower_bottom_lines" in findings
    )
    prompt_func = get_global_refiner_prompt if is_global else get_tower_refiner_prompt

    last_error = ""
    for attempt in range(3):
        try:
            message = prompt_func(json.dumps(findings), json.dumps(grounding_data))
            if last_error:
                message += f"\n\n🚨 VIOLACIÓN DE PROTOCOLO DETECTADA:\n{last_error}\nPor favor, corrige el texto para que sea 100% neutral y profesional."

            refined_findings = await run_agent(
                app, user_id="exec_refiner", message=message
            )
            return refined_findings

        except (SecurityIntegrityViolation, json.JSONDecodeError) as e:
            last_error = str(e)
            print(
                f"    ⚠️ Fallo de protocolo diplomático (Intento {attempt + 1}). Re-refinando..."
            )

    raise RuntimeError(
        f"Fallo crítico: El Refinador no ha logrado cumplir el protocolo Tier 1 tras 3 intentos. Error: {last_error}"
    )


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings-path", required=True)
    parser.add_argument("--client", required=True)
    args = parser.parse_args()

    findings_path = Path(args.findings_path)
    findings = load_json(findings_path)

    print(f"🚀 Iniciando Refinado Ejecutivo para {args.client}...")
    refined = await refine_findings(args.client, findings)

    findings_path.write_text(
        json.dumps(refined, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Hallazgos refinados con éxito: {findings_path}")


if __name__ == "__main__":
    asyncio.run(main())
