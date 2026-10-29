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

from assessment_engine.domain.prompts.intelligence_prompts import (
    get_global_refiner_prompt,
    get_tower_refiner_prompt,
)
from assessment_engine.infrastructure.ai_client import run_agent
from assessment_engine.infrastructure.governance import (
    SecurityIntegrityViolation,
)
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_intelligence_path,
)


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

    from assessment_engine.infrastructure.config_loader import (
        resolve_model_for_role,
    )

    model_name = resolve_model_for_role("global_refiner_strict")
    agent = Agent(
        name="executive_refiner",
        model=model_name,
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


def _preserve_sovereign_blocks(
    refined: dict[str, Any], raw_findings: dict[str, Any]
) -> None:
    """Re-merge pristine, unmodified fields post-LLM processing to mitigate corruption."""
    for key in [
        "_generation_metadata",
        "meta",
        "intelligence_dossier",
        "heatmap",
        "visuals",
        "tower_bottom_lines",
    ]:
        if key in raw_findings and key not in refined:
            refined[key] = raw_findings[key]

    if "heatmap" in raw_findings and (
        not refined.get("heatmap") or len(refined.get("heatmap", [])) == 0
    ):
        refined["heatmap"] = raw_findings["heatmap"]


def _normalize_burning_platform(refined: dict[str, Any]) -> None:
    """Normalize burning platform root causes into list format."""
    if "burning_platform" in refined and isinstance(refined["burning_platform"], list):
        for item in refined["burning_platform"]:
            if (
                isinstance(item, dict)
                and "root_causes" in item
                and isinstance(item["root_causes"], str)
            ):
                item["root_causes"] = [item["root_causes"]]


def _normalize_tower_bottom_lines(
    refined: dict[str, Any], raw_findings: dict[str, Any]
) -> None:
    """Ensure all tower bottom lines have id, name, score (as string), band, and status colors."""
    original_tbl = {
        (orig.get("id") or orig.get("tower_id") or orig.get("name") or orig.get("tower_name")): orig
        for orig in raw_findings.get("tower_bottom_lines", [])
        if isinstance(orig, dict)
    }

    if "tower_bottom_lines" in refined and isinstance(
        refined["tower_bottom_lines"], list
    ):
        for item in refined["tower_bottom_lines"]:
            if isinstance(item, dict):
                key = item.get("id") or item.get("tower_id") or item.get("name") or item.get("tower_name")
                orig_match = original_tbl.get(key, {})
                if "id" not in item:
                    item["id"] = item.get("tower_id") or orig_match.get("id") or "T1"
                if "name" not in item:
                    item["name"] = item.get("tower_name") or orig_match.get("name") or "Infraestructura General"
                if "score" not in item or item["score"] is None:
                    item["score"] = orig_match.get("score", 0.0)
                if "band" not in item or item["band"] is None:
                    item["band"] = orig_match.get("band", "Unassessed")
                if "status_color" not in item or item["status_color"] is None:
                    try:
                        score_val = float(item["score"])
                    except ValueError:
                        score_val = 0.0
                    item["status_color"] = orig_match.get(
                        "status_color",
                        "amber" if score_val < 3.0 else "green",
                    )


def _normalize_target_vision(refined: dict[str, Any]) -> None:
    """Normalize keys in target vision evolution principles and strategic pillars."""
    if "target_vision" in refined and isinstance(refined["target_vision"], dict):
        target_v = refined["target_vision"]
        if "evolution_principles" in target_v and isinstance(
            target_v["evolution_principles"], list
        ):
            for item in target_v["evolution_principles"]:
                if (
                    isinstance(item, dict)
                    and "title" in item
                    and "principle" not in item
                ):
                    item["principle"] = item["title"]
        if "strategic_pillars" in target_v and isinstance(
            target_v["strategic_pillars"], list
        ):
            for item in target_v["strategic_pillars"]:
                if isinstance(item, dict) and "title" in item and "pillar" not in item:
                    item["pillar"] = item["title"]


def _normalize_roadmap_horizon_item(item: Any, h_key: str) -> Any:
    """Normalize fields, timing and duration for a single roadmap horizon initiative."""
    if isinstance(item, str):
        item = {"title": item}
    if not isinstance(item, dict):
        return item

    item_copy = item.copy()

    # Stage 1: Consolidate program field
    if "program" not in item_copy or not item_copy["program"]:
        item_copy["program"] = (
            item_copy.get("program_id")
            or item_copy.get("program_name")
            or item_copy.get("program_title")
            or item_copy.get("program")
            or ""
        )
    item_copy.pop("program_id", None)

    # Stage 2: Consolidate business case
    if "business_case" not in item_copy or not item_copy["business_case"]:
        item_copy["business_case"] = (
            item_copy.get("objective")
            or item_copy.get("description")
            or item_copy.get("business_impact")
            or item_copy.get("impact")
            or "Mitigación de deuda técnica."
        )
    item_copy.pop("objective", None)

    # Stage 3: Normalize start_month
    start_defaults = {
        "quick_wins_0_3_months": 1,
        "year_1_3_12_months": 3,
        "year_2_12_24_months": 12,
        "year_3_24_36_months": 24,
    }
    if "start_month" not in item_copy or item_copy["start_month"] == 0:
        item_copy["start_month"] = start_defaults.get(h_key, 1)

    # Stage 4: Normalize duration_months
    duration_defaults = {
        "quick_wins_0_3_months": 3,
        "year_1_3_12_months": 9,
        "year_2_12_24_months": 12,
        "year_3_24_36_months": 12,
    }
    if "duration_months" not in item_copy or item_copy["duration_months"] == 0:
        item_copy["duration_months"] = duration_defaults.get(h_key, 6)

    return item_copy


def _normalize_programs_list(roadmap: dict[str, Any]) -> None:
    """Normalize program names and descriptions within execution roadmap."""
    if "programs" not in roadmap or not isinstance(roadmap["programs"], list):
        return
    normalized_programs = []
    for p in roadmap["programs"]:
        if isinstance(p, dict):
            p_copy = p.copy()
            if not p_copy.get("description"):
                p_copy["description"] = (
                    p_copy.get("name")
                    or p_copy.get("id")
                    or "Programa de transformación tecnológica."
                )
            normalized_programs.append(p_copy)
        else:
            normalized_programs.append(p)
    roadmap["programs"] = normalized_programs


def _normalize_horizons_dict(roadmap: dict[str, Any]) -> None:
    """Normalize standard temporal horizons and ensure lists are populated."""
    if "horizons" not in roadmap or not roadmap["horizons"]:
        roadmap["horizons"] = {
            "quick_wins_0_3_months": [],
            "year_1_3_12_months": [],
            "year_2_12_24_months": [],
            "year_3_24_36_months": [],
        }

    if not isinstance(roadmap.get("horizons"), dict):
        return
    h_dict = roadmap["horizons"]
    if "quick_wins_0_6_months" in h_dict and "quick_wins_0_3_months" not in h_dict:
        h_dict["quick_wins_0_3_months"] = h_dict.pop("quick_wins_0_6_months")
    if "year_1_6_12_months" in h_dict and "year_1_3_12_months" not in h_dict:
        h_dict["year_1_3_12_months"] = h_dict.pop("year_1_6_12_months")

    for h_key in [
        "quick_wins_0_3_months",
        "year_1_3_12_months",
        "year_2_12_24_months",
        "year_3_24_36_months",
    ]:
        if h_key not in h_dict or h_dict[h_key] is None:
            h_dict[h_key] = []
        if isinstance(h_dict[h_key], list):
            h_dict[h_key] = [
                _normalize_roadmap_horizon_item(item, h_key) for item in h_dict[h_key]
            ]


def _normalize_execution_roadmap(refined: dict[str, Any]) -> None:
    """Normalize program metadata and horizon timing across execution roadmap."""
    if not (
        "execution_roadmap" in refined
        and isinstance(refined["execution_roadmap"], dict)
    ):
        return
    roadmap = refined["execution_roadmap"]
    _normalize_programs_list(roadmap)
    _normalize_horizons_dict(roadmap)


def _normalize_executive_decisions(refined: dict[str, Any]) -> None:
    """Normalize executive decisions into standard dict with immediate_decisions list."""
    if "executive_decisions" in refined and isinstance(
        refined["executive_decisions"], list
    ):
        refined["executive_decisions"] = {
            "immediate_decisions": refined["executive_decisions"]
        }
    elif "executive_decisions" in refined and isinstance(
        refined["executive_decisions"], dict
    ):
        if "immediate_decisions" not in refined["executive_decisions"]:
            refined["executive_decisions"]["immediate_decisions"] = []


def postprocess_refined_findings(
    refined: dict[str, Any], raw_findings: dict[str, Any]
) -> dict[str, Any]:
    """Execute complete post-processing pipeline: preserve sovereign blocks and normalize schema conformance."""
    _preserve_sovereign_blocks(refined, raw_findings)
    _normalize_burning_platform(refined)
    _normalize_tower_bottom_lines(refined, raw_findings)
    _normalize_target_vision(refined)
    _normalize_execution_roadmap(refined)
    _normalize_executive_decisions(refined)
    return refined


async def main(argv: list[str] | None = None) -> None:
    """Orchestrates the end-to-end refinement and normalization of executive findings."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings-path", required=True)
    parser.add_argument("--client", required=True)
    args = parser.parse_args(argv)

    findings_path = Path(args.findings_path)
    findings = load_json(findings_path)

    print(f"🚀 Iniciando Refinado Ejecutivo para {args.client}...")
    refined = await refine_findings(args.client, findings)
    final_refined = postprocess_refined_findings(refined, findings)

    findings_path.write_text(
        json.dumps(final_refined, indent=2, ensure_ascii=False), encoding="utf-8-sig"
    )
    print(f"✅ Hallazgos refinados con éxito: {findings_path}")


if __name__ == "__main__":
    asyncio.run(main())
