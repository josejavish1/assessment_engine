"""Module: `run_executive_refiner.py` (TIER 1 EDITION 2026 - SELF HEALING).

Implements the Sovereign Style Manual application, featuring an automated retry mechanism to enforce tone and style compliance.
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
    """Load and parse a JSON file from a given path."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8-sig")))


async def refine_findings(client_name: str, findings: dict) -> dict:
    r"""{'docstring': "Refines a findings dictionary using an AI agent to meet content and structure protocols.\n\n    This asynchronous function orchestrates a multi-attempt process to rewrite a raw\n    findings dictionary into a standardized format. The function first infers the\n    report type ('global' or 'tower') based on the key structure of the input\n    `findings`. It then loads optional client-specific grounding data to provide\n    context to the AI agent. A retry mechanism with a maximum of three attempts\n    is implemented to handle recoverable errors, such as protocol violations\n    (`SecurityIntegrityViolation`) or malformed JSON responses from the agent.\n    On each subsequent attempt, the previous error is included in the prompt to\n    guide the agent toward a valid output.\n\n    Args:\n        client_name: The client's identifier, used to locate and load a\n            corresponding JSON file with contextual grounding data.\n        findings: The raw dictionary of findings. Its key structure is used to\n            determine the refinement strategy (e.g., 'global' if keys like\n            'executive_summary' are present).\n\n    Returns:\n        A dictionary containing the refined findings, parsed from the AI agent's\n        JSON output.\n\n    Raises:\n        RuntimeError: If the agent fails to produce a valid, protocol-compliant\n            dictionary within three attempts."}."""
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

    # Infer the report type to select the appropriate downstream processing strategy.
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
    """Orchestrates the end-to-end refinement and normalization of executive findings.

    This function serves as the main asynchronous entry point for the script, processing
    client findings through an LLM-based service and performing comprehensive
    post-processing to ensure data integrity and schema conformance. The process
    involves parsing command-line arguments, loading the source data, invoking the
    refinement service, and then applying a series of data preservation and
    normalization rules before overwriting the original file with the result.

    Post-processing is divided into two main stages:
    1.  **Sovereign Data Preservation**: Key data structures from the original
        input (e.g., `_generation_metadata`, `meta`, `heatmap`, `visuals`) are
        re-injected into the refined output. This mitigates the risk of data
        loss or hallucination-induced corruption for structured data not
        intended for modification by the refinement service.
    2.  **Schema Normalization**: The refined data structure is rigorously validated
        and conformed to a canonical schema. This includes adding default values,
        restructuring nested objects, renaming keys for consistency, and enforcing
        correct data types across sections like `burning_platform`,
        `execution_roadmap`, and `executive_decisions`.

    Args:
        The script is controlled via command-line arguments:
        --findings-path (str): The file path to the input JSON containing client
            findings. This file will be overwritten with the refined output.
        --client (str): The client identifier used to provide context to the
            refinement service.

    Raises:
        FileNotFoundError: If the file specified by `--findings-path` does not exist.
        json.JSONDecodeError: If the input findings file contains malformed JSON.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings-path", required=True)
    parser.add_argument("--client", required=True)
    args = parser.parse_args()

    findings_path = Path(args.findings_path)
    findings = load_json(findings_path)

    print(f"🚀 Iniciando Refinado Ejecutivo para {args.client}...")
    refined = await refine_findings(args.client, findings)

    # Sovereign Quality Assurance: Re-merge pristine, unmodified fields post-LLM processing to mitigate the risk of data loss or hallucination-induced corruption.
    # Re-inject structured data blocks that are not intended for LLM mutation, ensuring their integrity is preserved.
    for key in ["_generation_metadata", "meta", "intelligence_dossier", "heatmap", "visuals", "tower_bottom_lines"]:
        if key in findings and key not in refined:
            refined[key] = findings[key]

    # Preserve the integrity of the heatmap data structure, a critical input for the global radar chart visualization.
    if "heatmap" in findings and (not refined.get("heatmap") or len(refined.get("heatmap", [])) == 0):
        refined["heatmap"] = findings["heatmap"]

    # Section: Preventative Schema Normalization in the Refined Layer
    if "burning_platform" in refined and isinstance(refined["burning_platform"], list):
        for item in refined["burning_platform"]:
            if isinstance(item, dict) and "root_causes" in item and isinstance(item["root_causes"], str):
                item["root_causes"] = [item["root_causes"]]
                
    if "tower_bottom_lines" in refined and isinstance(refined["tower_bottom_lines"], list):
        for item in refined["tower_bottom_lines"]:
            if isinstance(item, dict):
                if "score" not in item: item["score"] = 4.0
                if "band" not in item: item["band"] = "Managed"
                if "status_color" not in item: item["status_color"] = "green"
                
    if "target_vision" in refined and isinstance(refined["target_vision"], dict):
        target_v = refined["target_vision"]
        if "evolution_principles" in target_v and isinstance(target_v["evolution_principles"], list):
            for item in target_v["evolution_principles"]:
                if isinstance(item, dict) and "title" in item and "principle" not in item:
                    item["principle"] = item["title"]
        if "strategic_pillars" in target_v and isinstance(target_v["strategic_pillars"], list):
            for item in target_v["strategic_pillars"]:
                if isinstance(item, dict) and "title" in item and "pillar" not in item:
                    item["pillar"] = item["title"]

    if "execution_roadmap" in refined and isinstance(refined["execution_roadmap"], dict):
        roadmap = refined["execution_roadmap"]
        
        # Normalize the `programs` data structure to conform to the canonical schema.
        if "programs" in roadmap and isinstance(roadmap["programs"], list):
            normalized_programs = []
            for p in roadmap["programs"]:
                if isinstance(p, dict):
                    p_copy = p.copy()
                    if "description" not in p_copy or not p_copy["description"]:
                        p_copy["description"] = p_copy.get("name") or p_copy.get("id") or "Programa de transformación tecnológica."
                    normalized_programs.append(p_copy)
                else:
                    normalized_programs.append(p)
            roadmap["programs"] = normalized_programs
            
        # Validate the existence of the `horizons` data structure, initializing if absent to prevent downstream null pointer exceptions.
        if "horizons" not in roadmap or not roadmap["horizons"]:
            roadmap["horizons"] = {
                "quick_wins_0_3_months": [],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": []
            }
            
        if "horizons" in roadmap and isinstance(roadmap["horizons"], dict):
            h_dict = roadmap["horizons"]
            if "quick_wins_0_6_months" in h_dict and "quick_wins_0_3_months" not in h_dict:
                h_dict["quick_wins_0_3_months"] = h_dict["quick_wins_0_6_months"]
                del h_dict["quick_wins_0_6_months"]
            if "year_1_6_12_months" in h_dict and "year_1_3_12_months" not in h_dict:
                h_dict["year_1_3_12_months"] = h_dict["year_1_6_12_months"]
                del h_dict["year_1_6_12_months"]
                
            for h_key in ["quick_wins_0_3_months", "year_1_3_12_months", "year_2_12_24_months", "year_3_24_36_months"]:
                if h_key not in h_dict or h_dict[h_key] is None:
                    h_dict[h_key] = []
                    
                if isinstance(h_dict[h_key], list):
                    normalized_list = []
                    for item in h_dict[h_key]:
                        if isinstance(item, str):
                            item = {"title": item}

                        if isinstance(item, dict):
                            item_copy = item.copy()
                            
                            # Stage 1: Consolidate program-related fields into a unified `program` object.
                            if "program" not in item_copy or not item_copy["program"]:
                                p_val = item_copy.get("program_id") or item_copy.get("program_name") or item_copy.get("program_title") or item_copy.get("program") or ""
                                item_copy["program"] = p_val
                            if "program_id" in item_copy:
                                del item_copy["program_id"]
                                
                            # Stage 2: Consolidate business case fields into a unified `business_case` object.
                            if "business_case" not in item_copy or not item_copy["business_case"]:
                                bc_val = item_copy.get("objective") or item_copy.get("description") or item_copy.get("business_impact") or item_copy.get("impact") or "Mitigación de deuda técnica."
                                item_copy["business_case"] = bc_val
                            if "objective" in item_copy:
                                del item_copy["objective"]
                                
                            # Stage 3: Normalize `start_month`, applying a default value if the field is null or zero to ensure valid temporal calculations.
                            if "start_month" not in item_copy or item_copy["start_month"] == 0:
                                if h_key == "quick_wins_0_3_months":
                                    item_copy["start_month"] = 1
                                elif h_key == "year_1_3_12_months":
                                    item_copy["start_month"] = 3
                                elif h_key == "year_2_12_24_months":
                                    item_copy["start_month"] = 12
                                elif h_key == "year_3_24_36_months":
                                    item_copy["start_month"] = 24
                                else:
                                    item_copy["start_month"] = 1
                                    
                            # Stage 4: Normalize `duration_months`, applying a default value if the field is null or zero to prevent invalid temporal calculations.
                            if "duration_months" not in item_copy or item_copy["duration_months"] == 0:
                                if h_key == "quick_wins_0_3_months":
                                    item_copy["duration_months"] = 3
                                elif h_key == "year_1_3_12_months":
                                    item_copy["duration_months"] = 9
                                elif h_key == "year_2_12_24_months":
                                    item_copy["duration_months"] = 12
                                elif h_key == "year_3_24_36_months":
                                    item_copy["duration_months"] = 12
                                else:
                                    item_copy["duration_months"] = 6
                                    
                            normalized_list.append(item_copy)
                        else:
                            normalized_list.append(item)
                    h_dict[h_key] = normalized_list

    if "executive_decisions" in refined and isinstance(refined["executive_decisions"], list):
        refined["executive_decisions"] = {"immediate_decisions": refined["executive_decisions"]}
    elif "executive_decisions" in refined and isinstance(refined["executive_decisions"], dict):
        if "immediate_decisions" not in refined["executive_decisions"]:
            refined["executive_decisions"]["immediate_decisions"] = []

    findings_path.write_text(
        json.dumps(refined, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Hallazgos refinados con éxito: {findings_path}")


if __name__ == "__main__":
    asyncio.run(main())
