#!/usr/bin/env python3
"""Autonomous Content Refiner for Molins T1 via gemini-4-argon (CFO-Grade)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List

from google.genai import types
from pydantic import BaseModel, Field

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from assessment_engine.infrastructure.genai_client import (
    ModelTier,
    create_genai_client,
    get_model,
)

class ExecSummaryRewrite(BaseModel):
    headline: str = Field(..., description="Un titular impactante de 1-2 líneas en español de España.")
    summary_body: str = Field(..., description="Tres párrafos densos, precisos y ejecutivos explicando el problema, los números y las consecuencias. Sin relleno.")
    key_business_impacts: List[str] = Field(..., description="Lista de 4 viñetas con los impactos de negocio directos. Lenguaje llano y contundente.")

class DomainIntroRewrite(BaseModel):
    domain_objective: str = Field(..., description="Objetivo claro y riguroso sin palabras vacías.")
    technological_domain: str = Field(..., description="La topología real y el perímetro físico exacto (fibra, SimpliVity, NetApp, básculas).")
    methodology: str = Field(..., description="Explicación sencilla de O-FAIR, CMMI y ASHRAE TC 9.9.")

class HealthCheckRewrite(BaseModel):
    capability: str = Field(..., description="Nombre de la capacidad técnica.")
    finding: str = Field(..., description="El diagnóstico del problema de forma llana, explicando por qué ocurre.")
    business_risk: str = Field(..., description="El riesgo de negocio estructurado como Fórmula de Defendibilidad: Frecuencia x Parada x Coste = ALE.")

class PillarRewrite(BaseModel):
    pilar_name: str
    health_check_asis: List[HealthCheckRewrite]

class BlueprintRewrite(BaseModel):
    pillars_analysis: List[PillarRewrite]

class CrossCapabilitiesRewrite(BaseModel):
    transformation_paradigm: str = Field(..., description="El paradigma a futuro (TO-BE). Visión estratégica clara.")
    next_steps_inaction: str = Field(..., description="El coste de no hacer nada frente a la modernización estructural (ROI).")

def main() -> None:
    client = create_genai_client()
    model_name = get_model(ModelTier.REASONING)
    
    blueprint_path = REPO_ROOT / "working/molins/T1/blueprint_t1_payload.json"
    annex_path = REPO_ROOT / "working/molins/T1/approved_annex_t1.template_payload.json"
    
    blueprint_data = json.loads(blueprint_path.read_text(encoding="utf-8-sig"))
    annex_data = json.loads(annex_path.read_text(encoding="utf-8-sig"))
    
    system_prompt = (
        "Actúa como un CTO Industrial y un CFO Hostil de una firma de consultoría Tier-1. "
        "Tu misión es reescribir el contenido técnico de este diagnóstico para que el CIO de Molins "
        "pueda defender un presupuesto multimillonario ante su Consejo de Administración.\n"
        "REGLAS INQUEBRANTABLES:\n"
        "1. Español de España (es-ES), con un lenguaje sencillo, directo y fluido. Cero jerga vacía.\n"
        "2. ZERO FLUFF: Cada frase debe aportar un dato técnico o financiero. Si no aporta valor, elimínala.\n"
        "3. Fórmula de Defendibilidad Financiera (O-FAIR): Cada euro de riesgo debe explicarse "
        "como: Frecuencia anual (TEF) x Horas de Parada x Coste/hora (lucro cesante) + Daños Secundarios = Exposición Anualizada (ALE).\n"
        "4. Cero Repetición: Ningún bloque de texto puede clonar información de otro bloque.\n"
        "5. Máximo Rigor: Usa la infraestructura real (Sant Vicenç dels Horts, HPE SimpliVity, NetApp, básculas de cemento, plantas de áridos, NIS2)."
    )

    print("--- ITERACIÓN 1: CAPÍTULO 1 (Resumen Ejecutivo) ---")
    prompt_exec = system_prompt + f"\n\nReescribe el resumen ejecutivo:\n{json.dumps(annex_data.get('executive_summary'), ensure_ascii=False)}"
    resp_exec = client.models.generate_content(
        model=model_name,
        contents=prompt_exec,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json", response_schema=ExecSummaryRewrite)
    )
    exec_rewritten = ExecSummaryRewrite.model_validate_json(resp_exec.text)
    if "executive_summary" not in annex_data:
        annex_data["executive_summary"] = {}
    annex_data["executive_summary"]["headline"] = exec_rewritten.headline
    annex_data["executive_summary"]["summary_body"] = exec_rewritten.summary_body
    annex_data["executive_summary"]["key_business_impacts"] = exec_rewritten.key_business_impacts

    print("--- ITERACIÓN 2: CAPÍTULO 2 (Topología y Metodología) ---")
    prompt_intro = system_prompt + f"\n\nReescribe la introducción del dominio:\n{json.dumps(annex_data.get('domain_introduction'), ensure_ascii=False)}"
    resp_intro = client.models.generate_content(
        model=model_name,
        contents=prompt_intro,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json", response_schema=DomainIntroRewrite)
    )
    intro_rewritten = DomainIntroRewrite.model_validate_json(resp_intro.text)
    annex_data["domain_introduction"] = intro_rewritten.model_dump()

    print("--- ITERACIÓN 3 & 4: CAPÍTULOS 3 & 4 (Pilares y Riesgos FAIR) ---")
    prompt_pillars = system_prompt + f"\n\nReescribe el diagnóstico de brechas y los riesgos de negocio (aplicando la Fórmula de Defendibilidad) para todos los pilares:\n{json.dumps(blueprint_data.get('pillars_analysis'), ensure_ascii=False)}"
    resp_pillars = client.models.generate_content(
        model=model_name,
        contents=prompt_pillars,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json", response_schema=BlueprintRewrite)
    )
    pillars_rewritten = BlueprintRewrite.model_validate_json(resp_pillars.text)
    
    # Merge rewritten findings/business risks back into the original structure to preserve scores
    for orig_pillar in blueprint_data["pillars_analysis"]:
        for rew_pillar in pillars_rewritten.pillars_analysis:
            if orig_pillar["pilar_name"] == rew_pillar.pilar_name or orig_pillar.get("pillar_name") == rew_pillar.pilar_name:
                for orig_hc in orig_pillar.get("health_check_asis", []):
                    for rew_hc in rew_pillar.health_check_asis:
                        if orig_hc.get("capability") == rew_hc.capability:
                            orig_hc["finding"] = rew_hc.finding
                            orig_hc["business_risk"] = rew_hc.business_risk

    print("--- ITERACIÓN 5: CAPÍTULO 5 (Conclusiones) ---")
    prompt_concl = system_prompt + f"\n\nReescribe las conclusiones transversales (paradigma y coste de inacción):\n{json.dumps(blueprint_data.get('cross_capabilities_analysis'), ensure_ascii=False)}"
    resp_concl = client.models.generate_content(
        model=model_name,
        contents=prompt_concl,
        config=types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json", response_schema=CrossCapabilitiesRewrite)
    )
    concl_rewritten = CrossCapabilitiesRewrite.model_validate_json(resp_concl.text)
    if "cross_capabilities_analysis" not in blueprint_data:
        blueprint_data["cross_capabilities_analysis"] = {}
    blueprint_data["cross_capabilities_analysis"]["transformation_paradigm"] = concl_rewritten.transformation_paradigm
    blueprint_data["cross_capabilities_analysis"]["next_steps_inaction"] = concl_rewritten.next_steps_inaction

    blueprint_path.write_text(json.dumps(blueprint_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    annex_path.write_text(json.dumps(annex_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Contenido refinado y sincronizado con éxito. Listo para compilación.")

if __name__ == "__main__":
    main()
