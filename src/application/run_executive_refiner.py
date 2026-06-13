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

    # RE-MERGE DE CAMPOS PUROS PARA PREVENIR LA PÉRDIDA DE DATOS DEL LLM (Sovereign Quality Assurance)
    # Re-inyectamos los bloques estructurados que el LLM no tiene por qué mutar o recrear
    for key in ["_generation_metadata", "meta", "intelligence_dossier", "heatmap", "visuals", "tower_bottom_lines"]:
        if key in findings and key not in refined:
            refined[key] = findings[key]

    # Salvaguarda de heatmap para el gráfico de radar global
    if "heatmap" in findings and (not refined.get("heatmap") or len(refined.get("heatmap", [])) == 0):
        refined["heatmap"] = findings["heatmap"]

    # NORMALIZACIÓN PREVENTIVA DE ESQUEMAS EN REFINED
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
        
        # Normalize programs
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
            
        # Ensure horizons exists
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
                            
                            # 1. Map program_id / program_name / etc. to program
                            if "program" not in item_copy or not item_copy["program"]:
                                p_val = item_copy.get("program_id") or item_copy.get("program_name") or item_copy.get("program_title") or item_copy.get("program") or ""
                                item_copy["program"] = p_val
                            if "program_id" in item_copy:
                                del item_copy["program_id"]
                                
                            # 2. Map objective / description / business_impact / etc. to business_case
                            if "business_case" not in item_copy or not item_copy["business_case"]:
                                bc_val = item_copy.get("objective") or item_copy.get("description") or item_copy.get("business_impact") or item_copy.get("impact") or "Mitigación de deuda técnica."
                                item_copy["business_case"] = bc_val
                            if "objective" in item_copy:
                                del item_copy["objective"]
                                
                            # 3. Handle start_month if missing or 0
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
                                    
                            # 4. Handle duration_months if missing or 0
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
