"""Provides functionality to augment technical findings with supplementary research.

This module executes parallelized web searches via a generative model to gather
additional information for technical analysis reports.
"""

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any, cast

from google import genai
from google.genai import types

from assessment_engine.domain.prompts.intelligence_prompts import (
    get_sota_researcher_prompt,
)
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_intelligence_path,
)


def load_json(path: Path) -> dict[str, Any]:
    """Load and parse a JSON file from a `pathlib.Path` object."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


async def research_pillar(client, p_name, gap_text, grounding_json):
    """Asynchronously researches a topic using a generative model with web search.

    Constructs a prompt from the topic (`p_name`), `gap_text`, and
    `grounding_json`. It then queries a generative AI model that is configured
    to use Google Search for information retrieval. The function includes a
    retry mechanism to handle transient API errors, attempting the call up to
    three times with a two-second delay between attempts.

    Upon receiving a response, it extracts the first JSON object from the raw
    text using a regular expression before parsing. If the API call fails after
    all retries or if the response cannot be parsed into a valid JSON object,
    it returns an empty dictionary for the results.

    Args:
        client: An asynchronous generative AI client object with an
            `aio.models.generate_content` method.
        p_name (str): The name of the research topic to investigate.
        gap_text (str): A textual description of a problem or information gap
            to contextualize the research prompt.
        grounding_json (str): A JSON-formatted string that provides additional
            grounding data for the prompt.

    Returns:
        tuple[str, dict]: A tuple containing the original `p_name` and a
            dictionary with the structured research results. An empty dictionary
            is returned in case of unrecoverable API or JSON parsing failures.
    """
    import asyncio

    print(f"        * Investigando vanguardia (CON INTERNET) para: {p_name}")
    prompt = get_sota_researcher_prompt(p_name, gap_text, grounding_json)

    config = types.GenerateContentConfig(
        tools=[{"google_search": {}}],
        system_instruction="Eres un Investigador Senior de Gartner. Tu misión es encontrar soluciones disruptivas 2026 usando búsqueda web.",
    )

    response = None
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash", contents=prompt, config=config
            )
            break
        except Exception as e:
            print(
                f"        ⚠️ [Reintento {attempt}/{max_attempts}] Fallo temporal en consulta de investigación para {p_name}: {e}"
            )
            if attempt == max_attempts:
                print(
                    f"        ❌ Fallo definitivo de API en consulta de investigación para {p_name}. Aplicando fallback vacío."
                )
                return p_name, {}
            await asyncio.sleep(2)

    try:
        import re

        text = response.text or "{}"
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
        sota_result = json.loads(text)
    except Exception as e:
        print(f"Error parsing JSON from search: {e}")
        sota_result = {}

    return p_name, sota_result


async def inject_sota(client_name: str, findings: dict) -> dict:
    r"""{'docstring': "Asynchronously enriches strategic findings with state-of-the-art research.\n\n    This function orchestrates an asynchronous research task for each strategic\n    pillar defined in the `findings` dictionary. For each pillar's specified\n    gap, it queries the Gemini API to identify relevant solutions,\n    architectural patterns, and strategic benefits. Optional, pre-existing\n    client data, loaded based on `client_name`, can provide grounding context\n    for the queries. The results are integrated back into the `findings`\n    dictionary by modifying the 'candidate_initiatives' in-place with new\n    titles and detailed, evidence-supported rationales.\n\n    Args:\n        client_name (str): The client identifier used to locate and load\n            supplementary grounding data for the research queries.\n        findings (dict): A dictionary containing the initial analysis, which is\n            modified in-place. It is expected to contain a 'pillar_findings'\n            key mapping to a list of pillar dictionaries. Each pillar\n            dictionary should contain keys such as 'pillar_name', 'gaps', and\n            'candidate_initiatives'.\n\n    Returns:\n        dict: The original `findings` dictionary object, now augmented with the\n        research results.\n\n    Raises:\n        IndexError: If 'gaps' or 'candidate_initiatives' lists within a pillar\n            are empty where at least one element is expected.\n        FileNotFoundError: Propagated if the client intelligence file specified\n            by `client_name` does not exist.\n        google.api_core.exceptions.GoogleAPICallError: Propagated from the\n            `genai` client upon API errors, such as authentication failure,\n            invalid requests, or network connectivity issues."}."""
    print(
        "    -> [Investigación Técnica] Lanzando investigación profunda 2026 con Internet..."
    )

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
        # Augment the initial analysis by incorporating publicly available information sourced from web research.
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
    """Orchestrates the technical research enrichment process from the command line.

    This asynchronous function serves as the main entry point for the script. It
    parses command-line arguments for an input findings JSON file and a client
    identifier. The function loads the specified JSON file, enriches its
    contents by calling the `inject_sota` coroutine, and then overwrites the
    original file with the enriched data.

    The script consumes the following command-line arguments:
      --findings-path: The local filesystem path to the input JSON file
        containing the findings to be enriched.
      --client: A string identifier for the client initiating the request.

    Raises:
        FileNotFoundError: If the file specified by `--findings-path` does not
            exist.
        json.JSONDecodeError: If the input findings file contains malformed JSON.
        IOError: If a file system error occurs during read or write
            operations.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings-path", required=True)
    parser.add_argument("--client", required=True)
    args = parser.parse_args()

    findings_path = Path(args.findings_path)
    findings = load_json(findings_path)

    print(f"[System] Initializing Technical Research (Internet Grounding) for {args.client}...")
    enriched = await inject_sota(args.client, findings)

    findings_path.write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"[System] Technical research context injected successfully: {findings_path}")


if __name__ == "__main__":
    asyncio.run(main())
