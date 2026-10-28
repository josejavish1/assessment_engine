"""
Cross-Lingual Knowledge Projector (RFC-018 SOTA 2026).
Decouples ontological domain knowledge from surface natural language.
Reuses 100% of the Socratic calibration cases, invariants, and trade-offs
for any language worldwide (including Hindi, Indic scripts, Japanese, etc.)
via prompt-conditioned zero-shot projection.

Gobernanza: Radon V(G) <= 8, Zero-Print, Fail-Closed Security.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from assessment_engine.infrastructure.evolution.socratic_calibrator import (
    SocraticCalibrationResult,
    SocraticOption,
    SocraticQuestion,
)
from assessment_engine.infrastructure.genai_client import ModelTier, create_genai_client, get_model

logger = logging.getLogger("assessment_engine.infrastructure.evolution.cross_lingual_projector")


def is_spanish_prompt(prompt: str) -> bool:
    """Check whether user prompt is in Spanish for zero-cost immediate bypass."""
    clean = prompt.lower().strip()
    if not clean:
        return True
    words = set(clean.split())
    if words & {"pour", "avec", "une", "dans", "sur", "est", "sont", "des", "the", "and", "for", "with", "from", "und", "für", "mit"}:
        return False
    if any(c in clean for c in "ñ¿¡"):
        return True
    return bool(re.search(r"\b(el|la|los|las|un|una|unos|unas|para|con|de|del|quiero|crear|plataforma|sistema|cita|citas)\b", clean))


INDIC_AND_ASIAN_SCRIPTS = (
    (r"[\u3040-\u309f\u30a0-\u30ff]", "ja"),  # Japanese (Hiragana/Katakana)
    (r"[\u0900-\u097f]", "hi"),               # Devanagari (Hindi, Marathi, Sanskrit)
    (r"[\u0b80-\u0bff]", "ta"),               # Tamil
    (r"[\u0980-\u09ff]", "bn"),               # Bengali
    (r"[\u0c00-\u0c7f]", "te"),               # Telugu
    (r"[\u0a80-\u0aff]", "gu"),               # Gujarati
    (r"[\u0d00-\u0d7f]", "ml"),               # Malayalam
    (r"[\u4e00-\u9fff]", "zh"),               # Chinese (Hanzi)
    (r"[\uac00-\ud7af]", "ko"),               # Korean (Hangul)
    (r"[\u0600-\u06ff]", "ar"),               # Arabic
    (r"[\u0400-\u04ff]", "ru"),               # Cyrillic
)


def detect_prompt_locale(prompt: str) -> str:
    """Detect approximate locale code based on Unicode scripts and stopwords."""
    clean = prompt.lower().strip()
    if not clean or is_spanish_prompt(prompt):
        return "es"
    for pattern, loc in INDIC_AND_ASIAN_SCRIPTS:
        if re.search(pattern, clean):
            return loc
    words = set(clean.split())
    if words & {"pour", "avec", "une", "dans", "sur", "est", "sont", "des"}:
        return "fr"
    if words & {"der", "die", "das", "und", "für", "mit", "von"}:
        return "de"
    return "en"


def _extract_projection_payload(result: SocraticCalibrationResult) -> dict[str, Any]:
    """Extract human-facing text strings for surface projection."""
    return {
        "domain_detected": result.domain_detected,
        "welcome_insight": result.welcome_insight,
        "questions": [
            {
                "text": q.text,
                "options": [{"label": opt.label, "description": opt.description} for opt in q.options],
            }
            for q in result.questions
        ],
    }


def _reconstruct_projected_result(
    original: SocraticCalibrationResult, projected_data: dict[str, Any]
) -> SocraticCalibrationResult:
    """Reconstruct Socratic result injecting projected text into original objects."""
    proj_domain = projected_data.get("domain_detected", original.domain_detected)
    proj_insight = projected_data.get("welcome_insight", original.welcome_insight)
    proj_questions_data = projected_data.get("questions", [])

    new_questions: list[SocraticQuestion] = []
    new_fast_track: dict[str, str] = {}

    for q_idx, orig_q in enumerate(original.questions):
        p_q = proj_questions_data[q_idx] if q_idx < len(proj_questions_data) else {}
        new_text = p_q.get("text", orig_q.text)
        p_opts = p_q.get("options", [])

        new_opts: list[SocraticOption] = []
        for o_idx, orig_o in enumerate(orig_q.options):
            p_o = p_opts[o_idx] if o_idx < len(p_opts) else {}
            new_label = p_o.get("label", orig_o.label)
            new_desc = p_o.get("description", orig_o.description)

            new_opt = SocraticOption(
                id=orig_o.id,
                label=new_label,
                description=new_desc,
                is_recommended=orig_o.is_recommended,
                activates_primitives=orig_o.activates_primitives,
            )
            new_opts.append(new_opt)
            if new_opt.is_recommended and orig_q.id not in new_fast_track:
                new_fast_track[orig_q.id] = new_opt.label

        new_questions.append(
            SocraticQuestion(
                id=orig_q.id,
                text=new_text,
                options=new_opts,
                architectural_intent=orig_q.architectural_intent,
                has_custom_option=orig_q.has_custom_option,
            )
        )

    return SocraticCalibrationResult(
        domain_detected=proj_domain,
        welcome_insight=proj_insight,
        requires_calibration=original.requires_calibration,
        questions=new_questions,
        recommended_fast_track=new_fast_track,
        is_blocked=original.is_blocked,
    )


async def project_socratic_result_to_locale(
    result: SocraticCalibrationResult, user_prompt_or_locale: str, client: Any = None
) -> SocraticCalibrationResult:
    """Project human-facing surface of Socratic result into the user prompt's locale."""
    if is_spanish_prompt(user_prompt_or_locale) or not result.questions:
        return result

    client = client or create_genai_client()
    model_name = get_model(ModelTier.FAST)
    payload = _extract_projection_payload(result)

    sys_instruction = (
        "You are the Worldwide Universal Localization Engine of Soverik Platform.\n"
        "Translate all human-facing labels, descriptions, and insights in the JSON "
        "into the EXACT SAME natural language, dialect, and script used in the USER PROMPT REFERENCE.\n"
        "RULES:\n"
        "1. If the user prompt is in Hindi, output natural professional Hindi (Devanagari).\n"
        "2. If the user prompt is in Japanese, output natural professional Japanese.\n"
        "3. If the user prompt is in Tamil, output natural Tamil.\n"
        "4. If the user prompt is in English, output English.\n"
        "5. Maintain the exact JSON keys, structure, and array lengths.\n"
        "6. Do not translate code identifiers or brand names (Stripe, Twilio, Cal.com).\n"
        "7. Output strictly valid JSON without markdown fences.\n\n"
        f"USER PROMPT REFERENCE:\n{user_prompt_or_locale}"
    )

    try:
        resp = await client.aio.models.generate_content(
            model=model_name,
            contents=[json.dumps(payload, ensure_ascii=False)],
            config={
                "system_instruction": sys_instruction,
                "response_mime_type": "application/json",
                "thinking_config": {"thinking_budget": 0},
                "temperature": 0.0,
                "max_output_tokens": 1500,
            },
        )
        if resp and resp.text:
            clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", resp.text.strip(), flags=re.MULTILINE)
            projected_data = json.loads(clean)
            return _reconstruct_projected_result(result, projected_data)
    except Exception as ex:
        logger.debug(f"[CrossLingualProjector] Fallo en proyección universal: {ex}. Sirviendo fallback seguro.")

    return result
