"""
Plan modules and apply YAGNI filtering for the Autonomous Product Director.
Decoupled from autonomous_product_director.py to maintain modularity and prevent monolithic files.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

from assessment_engine.infrastructure.evolution.epistemic_distiller import ProductStrategyDossier
from assessment_engine.infrastructure.evolution.sota_sourcer import SotaIntelligenceReport
from .director_models import LOCAL_CAPABILITIES, LocalBoundaryScope, ModulePlan

logger = logging.getLogger("assessment_engine.infrastructure.evolution.director_planner")


def _check_hard_legal_invariants(text: str) -> str | None:
    """Check deterministic hard legal invariants (PCI-DSS, RGPD, Sync Blocking)."""
    if "almacenar pan" in text or "tarjeta en texto plano" in text:
        return "Vetado por Invariante Legal: Prohibido almacenar PAN/tarjeta en cliente (PCI-DSS SAQ A)."
    if "opt-out" in text and "consentimiento" in text:
        return "Vetado por Invariante Legal: El consentimiento debe ser opt-in explícito previo (RGPD Art. 7)."
    if "bloqueante síncrono" in text or "sin timeout" in text:
        return "Vetado por Invariante de Rendimiento: Prohibidas llamadas síncronas sin timeout en hilo principal."
    return None


def _evaluate_anti_feature_llm(
    m_name: str,
    purpose: str,
    anti_features: tuple[str, ...],
    generate_content_fn: Callable[[str], Any],
) -> str | None:
    """Evaluate semantic anti-pattern violation using cognitive model."""
    try:
        af_list = "\n".join(f"- {af}" for af in anti_features)
        prompt = (
            "Eres un Evaluador Arquitectónico YAGNI.\n"
            f"Evalúa si el módulo propuesto viola ALGUN de los siguientes anti-patrones prohibidos:\n\n"
            f"ANTI-PATRONES PROHIBIDOS (Cubo 3):\n{af_list}\n\n"
            f"MÓDULO A EVALUAR:\nNombre: {m_name}\nPropósito: {purpose}\n\n"
            "Responde EXCLUSIVAMENTE 'SI' si viola claramente la intención de un anti-patrón (es sobreingeniería o una mala práctica descrita).\n"
            "Responde EXCLUSIVAMENTE 'NO' si es una funcionalidad legítima o si las palabras clave se usan en un buen contexto.\n"
        )
        resp = generate_content_fn(prompt)
        if resp and resp.text and "SI" in resp.text.strip().upper():
            return "Vetado semánticamente por Cubo 3 (Anti-Feature detectada por LLM)"
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[APD-Paso2] Fallo en evaluación semántica de YAGNI: {ex}")
    return None


def _evaluate_anti_feature_heuristic(text: str, anti_features: tuple[str, ...]) -> str | None:
    """Evaluate anti-feature violations heuristically matching significant tokens."""
    for af in anti_features:
        af_low = af.lower()
        clean_af = af_low.replace("descarte:", "").replace("veto:", "").replace("prohibido:", "").strip()
        af_words = [w for w in clean_af.split() if len(w) > 4]
        matched_words = [w for w in af_words if w in text]
        if len(matched_words) >= 2 or (len(af_words) == 1 and len(matched_words) == 1):
            return f"Vetado por Cubo 3 (Heurística Fallback): {af}"
    return None


def evaluate_anti_feature_veto(
    m_name: str,
    purpose: str,
    actual_dossier: ProductStrategyDossier,
    client: Any,
    generate_content_fn: Callable[[str], Any],
) -> str | None:
    """Evaluate whether a proposed module violates legal invariants or Cube 3 anti-features."""
    text_to_check = f"{m_name} {purpose}".lower()

    legal_veto = _check_hard_legal_invariants(text_to_check)
    if legal_veto:
        return legal_veto

    if client:
        return _evaluate_anti_feature_llm(m_name, purpose, actual_dossier.deliberate_anti_features, generate_content_fn)

    return _evaluate_anti_feature_heuristic(text_to_check, actual_dossier.deliberate_anti_features)


def resolve_local_transcription(
    text_to_check: str,
    m_name: str,
    purpose: str,
) -> tuple[str, str, bool]:
    """Translate complex architectural intent into local capabilities at zero cost."""
    for cap_key, capability in LOCAL_CAPABILITIES.items():
        matched = next((k for k in capability.keywords if k in text_to_check), None)
        if matched:
            return (
                f"{capability.substitute_name} [de {matched}]",
                capability.substitute_purpose,
                True,
            )
    return m_name, purpose, False


def plan_and_apply_yagni(
    task: str,
    scope: LocalBoundaryScope,
    dossier: ProductStrategyDossier | SotaIntelligenceReport,
    raw_modules: list[dict[str, Any]],
    client: Any,
    generate_content_fn: Callable[[str], Any],
) -> list[ModulePlan]:
    """Apply the YAGNI rubric and build the approved module plan."""
    actual_dossier = dossier.dossier if isinstance(dossier, SotaIntelligenceReport) else dossier
    approved_plans: list[ModulePlan] = []

    for m in raw_modules:
        m_id = m.get("id", "mod_01")
        m_name = m.get("name", "Core Module")
        t_file = m.get("target_file", "core/primitives/feature.py")
        test_file = m.get("test_file", f"tests/test_{Path(t_file).stem}.py")
        purpose = m.get("purpose", task)
        invs = m.get("invariants", list(actual_dossier.must_have_invariants[:3]))

        text_to_check = f"{m_name} {purpose}".lower()
        veto_reason = evaluate_anti_feature_veto(m_name, purpose, actual_dossier, client, generate_content_fn)

        effective_name = m_name
        effective_purpose = purpose
        is_transcribed = False

        if not veto_reason:
            effective_name, effective_purpose, is_transcribed = resolve_local_transcription(
                text_to_check, m_name, purpose
            )

        is_approved = is_transcribed or (veto_reason is None)

        approved_plans.append(ModulePlan(
            id=m_id,
            name=effective_name,
            target_file=t_file,
            test_file=test_file,
            purpose=effective_purpose,
            invariants=invs,
            is_yagni_approved=is_approved,
            veto_reason=veto_reason if not is_transcribed else None,
        ))

    return approved_plans
