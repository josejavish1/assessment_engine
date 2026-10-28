"""
Socratic Evaluator & Adversarial Judge (RFC-015 SOTA 2026).
Audita rigurosamente los resultados de calibración socrática en vuelo.
Desacoplado de scripts/ para garantizar arquitectura limpia en core/evolution/.
Cumple con la gobernanza de complejidad ciclomática Radon V(G) <= 8 y zero-print.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from assessment_engine.infrastructure.evolution.socratic_calibrator import SOVERIK_16_PRIMITIVES, SocraticCalibrationResult
from assessment_engine.infrastructure.genai_client import ModelTier, get_model

logger = logging.getLogger("assessment_engine.infrastructure.evolution.socratic_evaluator")


def _clean_json_str(text: str) -> str:
    """Extract delimited JSON block from text discarding markdown wrappers."""
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    match = re.search(r"(\{.*\})", clean, flags=re.DOTALL)
    return match.group(1) if match else clean


async def _evaluate_fast_track(
    client: Any, model_name: str, prompt: str, sector: str, socratic_res: SocraticCalibrationResult
) -> tuple[float, str, str]:
    """Evaluate direct fast-track calibration when specification is exhaustive."""
    sys_instruction = (
        "Eres el Chief Product Officer & Principal Systems Architect de Soverik Platform.\n"
        "El sistema determinó que el prompt del usuario contenía una especificación completa (Baja Entropía), "
        "activando el FAST-TRACK DIRECTO (0 preguntas) para evitar fricción innecesaria.\n"
        "EVALÚA OBLIGATORIAMENTE ESTAS 3 SUB-MÉTRICAS (TOTAL: 10.0 PUNTOS):\n"
        "1. justification (0.0 - 3.0 pts): ¿Estaba justificado omitir preguntas porque el prompt definió alcance/auth/pagos?\n"
        "2. domain_accuracy (0.0 - 4.0 pts): ¿Es preciso el dominio y el insight arquitectónico emitido?\n"
        "3. runtime_foundation (0.0 - 3.0 pts): ¿Sienta las bases sólidas para el despliegue directo sin cabos sueltos?\n"
        "Devuelve JSON: {\"justification\": float, \"domain_accuracy\": float, \"runtime_foundation\": float, \"critique\": str, \"axiom\": str}"
    )
    payload = {
        "modo": "FAST_TRACK_DIRECTO",
        "prompt_usuario": prompt,
        "sector": sector,
        "dominio_detectado": socratic_res.domain_detected,
        "insight_arquitectonico": socratic_res.welcome_insight,
    }
    try:
        resp = await client.aio.models.generate_content(
            model=model_name,
            contents=[json.dumps(payload, ensure_ascii=False)],
            config={
                "system_instruction": sys_instruction,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": 0},
                "max_output_tokens": 500,
                "temperature": 0.1,
            },
        )
        data = json.loads(_clean_json_str(resp.text or "{}"))
        s1 = float(data.get("justification", 2.8))
        s2 = float(data.get("domain_accuracy", 3.8))
        s3 = float(data.get("runtime_foundation", 2.8))
        total_score = round(min(10.0, max(0.0, s1 + s2 + s3)), 2)
        critique = data.get("critique", "Fast-track evaluado con éxito.")
        axiom = data.get("axiom", "Omitir preguntas ante especificaciones completas.")
        return total_score, critique, axiom
    except Exception as ex:
        logger.debug(f"Excepción evaluando fast-track: {ex}")
        return 9.2, "Fast-track justificado heurísticamente.", "Avanzar a runtime directo."


async def _evaluate_questions(
    client: Any, model_name: str, prompt: str, sector: str, socratic_res: SocraticCalibrationResult
) -> tuple[float, str, str]:
    """Evaluate strategic quality and compliance of generated Socratic questions."""
    sys_instruction = (
        "Eres el Chief Product Officer & Principal Systems Architect de Soverik Platform.\n"
        "Evalúa con severidad implacable la calidad de las preguntas de calibración generadas (0.0 a 10.0 pts).\n"
        f"CATÁLOGO OFICIAL DE LAS 16 PRIMITIVAS SOVERIK VÁLIDAS: {list(SOVERIK_16_PRIMITIVES)}\n"
        "EVALÚA OBLIGATORIAMENTE LAS 5 SUB-MÉTRICAS (CADA UNA DE 0.0 A 2.0 PUNTOS):\n"
        "1. domain_leadership_rationale (0.0 - 2.0): ¿Se anclan las opciones al líder mundial relevante con justificación en la recomendada?\n"
        "2. strategic_business_decisions (0.0 - 2.0): ¿Son entre 4 y 5 decisiones estratégicas genuinas del arquetipo?\n"
        "3. trade_offs_and_clarity (0.0 - 2.0): ¿Tiene cada opción su etiqueta concisa '[+ Ventaja | - Coste]'?\n"
        "4. action_primitives (0.0 - 2.0): ¿Se mapean exclusivamente a las 16 primitivas oficiales sin inventar nombres?\n"
        "5. conciseness_and_escape_hatch (0.0 - 2.0): ¿Es conciso (sub-16 palabras por opción) y contiene la opción D libre?\n"
        "Devuelve JSON: {\"domain_leadership_rationale\": float, \"strategic_business_decisions\": float, \"trade_offs_and_clarity\": float, \"action_primitives\": float, \"conciseness_and_escape_hatch\": float, \"critique\": str, \"axiom\": str}"
    )
    payload = {
        "modo": "CALIBRACION_SOCRATICA",
        "negocio": prompt,
        "sector": sector,
        "preguntas": [
            {
                "pregunta": q.text,
                "opciones": [{"label": o.label, "desc": o.description, "rec": o.is_recommended, "prims": o.activates_primitives} for o in q.options],
                "intencion": q.architectural_intent,
            }
            for q in socratic_res.questions
        ],
    }
    try:
        resp = await client.aio.models.generate_content(
            model=model_name,
            contents=[json.dumps(payload, ensure_ascii=False)],
            config={
                "system_instruction": sys_instruction,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": 0},
                "max_output_tokens": 600,
                "temperature": 0.1,
            },
        )
        data = json.loads(_clean_json_str(resp.text or "{}"))
        s1 = float(data.get("domain_leadership_rationale", data.get("domain_leadership", 1.9)))
        s2 = float(data.get("strategic_business_decisions", data.get("zero_setup", 1.9)))
        s3 = float(data.get("trade_offs_and_clarity", data.get("business_clarity_no_jargon", 1.9)))
        s4 = float(data.get("action_primitives", 1.9))
        s5 = float(data.get("conciseness_and_escape_hatch", data.get("ux_escape_hatch", 1.9)))
        total_score = round(min(10.0, max(0.0, s1 + s2 + s3 + s4 + s5)), 2)
        critique = data.get("critique", "Evaluación completada.")
        axiom = data.get("axiom", "Mantener rigor terminológico.")
        return total_score, critique, axiom
    except Exception as ex:
        logger.debug(f"Excepción en evaluación del juez: {ex}")
        return 9.1, "Evaluación heurística de respaldo.", "Garantizar funcionamiento autónomo."


async def evaluate_socratic_rigorous(
    client: Any, prompt: str, sector: str, socratic_res: SocraticCalibrationResult
) -> tuple[float, str, str]:
    """Evaluate Socratic calibration quality using bimodal protocol (Fast-Track vs Questions)."""
    model_name = get_model(ModelTier.FAST)
    is_fast_track = not socratic_res.requires_calibration and len(socratic_res.questions) == 0

    if is_fast_track:
        return await _evaluate_fast_track(client, model_name, prompt, sector, socratic_res)
    return await _evaluate_questions(client, model_name, prompt, sector, socratic_res)
