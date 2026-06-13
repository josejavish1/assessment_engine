"""
Módulo run_sota_researcher.py (SOTA EDITION 2026 - PARALLEL & DEEP).
Inyecta soluciones de vanguardia en los hallazgos técnicos usando búsqueda real en internet.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, cast

from google import genai
from google.genai import types

from domain.prompts.intelligence_prompts import get_sota_researcher_prompt
from infrastructure.runtime_paths import resolve_client_intelligence_path

def load_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))

async def research_pillar(client, p_name, gap_text, grounding_json):
    import asyncio
    print(f"        * Investigando vanguardia (CON INTERNET) para: {p_name}")
    prompt = get_sota_researcher_prompt(p_name, gap_text, grounding_json)
    
    config = types.GenerateContentConfig(
        tools=[{"google_search": {}}],
        system_instruction="Eres un Investigador Senior de Gartner. Tu misión es encontrar soluciones disruptivas 2026 usando búsqueda web."
    )
    
    response = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config
            )
            break
        except Exception as e:
            print(f"        ⚠️ [Reintento {attempt}/{max_attempts}] Fallo temporal en consulta SOTA para {p_name}: {e}")
            if attempt == max_attempts:
                print(f"        ❌ Fallo definitivo de API en SOTA para {p_name}. Aplicando fallback vacío.")
                return p_name, {}
            await asyncio.sleep(2)
    
    try:
        import re
        text = response.text or "{}"
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)
        sota_result = json.loads(text)
    except Exception as e:
        print(f"Error parsing JSON from search: {e}")
        sota_result = {}
        
    return p_name, sota_result

async def inject_sota(client_name: str, findings: dict) -> dict:
    print("    -> [Investigación SOTA] Lanzando investigación profunda 2026 con Internet...")

    intel_path = resolve_client_intelligence_path(client_name)
    grounding_data = {}
    if intel_path.exists():
        grounding_data = load_json(intel_path)
    grounding_json = json.dumps(grounding_data)

    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    results_map = {}
    for pillar in findings.get("pillar_findings", []):
        p_name = pillar.get("pillar_name")
        gap_text = pillar.get("gaps", [{}])[0].get("statement", "")
        _, res = await research_pillar(client, p_name, gap_text, grounding_json)
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

    print(f"🚀 Iniciando Investigación SOTA (Internet) para {args.client}...")
    enriched = await inject_sota(args.client, findings)

    findings_path.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Conocimiento SOTA inyectado con éxito: {findings_path}")

if __name__ == "__main__":
    asyncio.run(main())
