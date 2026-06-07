"""
Módulo run_sota_researcher.py (SOTA EDITION 2026 - PARALLEL & DEEP).
Inyecta soluciones de vanguardia en los hallazgos técnicos.
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, cast

from google.adk.agents import Agent
from google.adk.tools import google_search
from vertexai.agent_engines import AdkApp

from domain.prompts.intelligence_prompts import get_sota_researcher_prompt
from infrastructure.ai_client import run_agent
from infrastructure.runtime_paths import resolve_client_intelligence_path


def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


async def research_pillar(app, p_name, gap_text, grounding_json):
    print(f"        * Investigando vanguardia para: {p_name}")
    sota_result = await run_agent(
        app,
        user_id="sota_res",
        message=get_sota_researcher_prompt(p_name, gap_text, grounding_json),
    )
    return p_name, sota_result


async def inject_sota(client_name: str, findings: dict) -> dict:
    print("    -> [Investigación SOTA] Lanzando investigación profunda 2026...")

    intel_path = resolve_client_intelligence_path(client_name)
    grounding_data = {}
    if intel_path.exists():
        grounding_data = load_json(intel_path)
    grounding_json = json.dumps(grounding_data)

    agent = Agent(
        name="sota_researcher",
        model="gemini-2.5-pro",
        tools=[google_search],
        instruction="Eres un Investigador Senior de Gartner. Tu misión es encontrar soluciones disruptivas 2026 usando búsqueda web.",
    )
    app = AdkApp(agent=agent)

    results_map = {}
    for pillar in findings.get("pillar_findings", []):
        p_name = pillar.get("pillar_name")
        gap_text = pillar.get("gaps", [{}])[0].get("statement", "")
        _, res = await research_pillar(app, p_name, gap_text, grounding_json)
        results_map[p_name] = res

    for pillar in findings.get("pillar_findings", []):
        p_name = pillar.get("pillar_name")
        sota_result = results_map.get(p_name, {})

        init = pillar.get("candidate_initiatives", [{}])[0]
        # Inyectar el SOTA
        if sota_result.get("sota_solution_name"):
            init["title"] = f"Implantación de {sota_result['sota_solution_name']}"
            base_rationale = (
                f"{sota_result.get('strategic_benefit', '')} "
                f"La arquitectura seguirá el patrón de {sota_result.get('architectural_pattern', 'vanguardia')}."
            )
            source_ref_raw = sota_result.get("source_reference", "")
            if isinstance(source_ref_raw, dict):
                source_ref = json.dumps(source_ref_raw)
            else:
                source_ref = str(source_ref_raw).strip()

            if source_ref and source_ref.lower() not in [
                "none",
                "null",
                "n/a",
                "",
                "gartner 2026",
                "{}",
            ]:
                base_rationale += f" [Referencia de Mercado: {source_ref}]"
            init["rationale"] = base_rationale

    return findings


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings-path", required=True)
    parser.add_argument("--client", required=True)
    args = parser.parse_args()

    findings_path = Path(args.findings_path)
    findings = load_json(findings_path)

    print(f"🚀 Iniciando Investigación SOTA para {args.client}...")
    enriched = await inject_sota(args.client, findings)

    findings_path.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Conocimiento SOTA inyectado con éxito: {findings_path}")


if __name__ == "__main__":
    asyncio.run(main())
