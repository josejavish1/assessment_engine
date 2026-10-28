"""
Compare modules differentially for the Autonomous Product Director. Decoupled from autonomous_product_director.py to maintain modularity and avoid monolithic files.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Callable

from assessment_engine.infrastructure.evolution.epistemic_distiller import ProductStrategyDossier
from assessment_engine.infrastructure.evolution.orthogonal_gates import orthogonal_gates
from assessment_engine.infrastructure.evolution.reflexion_ledger import reflexion_ledger
from assessment_engine.infrastructure.evolution.sota_sourcer import SotaIntelligenceReport
from .director_models import ModulePlan, ProductGap

logger = logging.getLogger("assessment_engine.infrastructure.evolution.director_comparator")


def evaluate_orthogonal_gaps(
    implemented_code_map: dict[str, str],
    modules: list[ModulePlan],
    baseline_code_map: dict[str, str],
    repo_root: Path,
) -> list[ProductGap]:
    """Evaluate the four orthogonal deterministic gates on each synthesized file."""
    orthogonal_gaps: list[ProductGap] = []
    for target_file, code in implemented_code_map.items():
        mod = next((m for m in modules if m.target_file == target_file), None)
        base_code = baseline_code_map.get(target_file)
        test_rel = mod.test_file if mod else None

        gate_report = orthogonal_gates.evaluate_all(
            target_file_rel=target_file,
            candidate_code=code,
            baseline_code=base_code,
            test_file_rel=test_rel,
            workspace_dir=repo_root,
            batch_files=implemented_code_map,
        )

        if not gate_report.passed and gate_report.failed_gate:
            failed = gate_report.failed_gate
            logger.warning(f"[APD-Paso4] 🛑 Compuerta {failed.gate_name} bloqueó la entrega: {failed.failure_signature}")
            reflexion_ledger.record_failure(
                category=failed.gate_name,
                error_signature=failed.failure_signature or "GATE_FAILURE",
                target_file=target_file,
                corrective_axiom=failed.prescriptive_action or "Subsanar fallo en compuerta ortogonal.",
            )
            orthogonal_gaps.append(ProductGap(
                id=f"{failed.gate_name}_{failed.failure_signature}",
                description=failed.prescriptive_action or "Fallo en compuerta ortogonal determinista.",
                target_module=target_file,
                is_yagni_approved=True,
            ))
    return orthogonal_gaps


def _find_module_by_ext(modules: list[ModulePlan], is_frontend: bool) -> str:
    """Find first module plan matching requested architectural layer (Frontend vs Backend)."""
    for m in modules:
        is_ui = m.target_file.endswith((".tsx", ".jsx", ".vue", ".svelte", ".html"))
        if is_ui == is_frontend:
            return m.target_file
    return modules[0].target_file if modules else "core_mod"


def _resolve_target_module_for_gap(text: str, modules: list[ModulePlan]) -> str:
    """Map feature gap to appropriate target module based on keywords."""
    is_ui_token = bool(re.search(r"\b(css|svg|dom|html|ui|button|modal|view|card|grid|responsive|aria|dialog|canvas)\b", text.lower()))
    return _find_module_by_ext(modules, is_frontend=is_ui_token)


def _parse_red_team_gaps(gaps_data: Any, modules: list[ModulePlan]) -> list[ProductGap] | None:
    """Parse list of gaps emitted by the Red Team LLM."""
    if not isinstance(gaps_data, list):
        return None
    gaps: list[ProductGap] = []
    for g_item in gaps_data:
        target_file = g_item.get("target_file") or _resolve_target_module_for_gap(g_item.get("description", ""), modules)
        gaps.append(ProductGap(
            id=g_item.get("id", f"GAP_INV_{len(gaps)+1:02d}"),
            description=g_item.get("description", "Invariante no satisfecho según Red Team"),
            target_module=target_file,
            is_yagni_approved=True,
        ))
    return gaps


def run_cognitive_red_team_audit(
    all_code: str,
    actual_dossier: ProductStrategyDossier,
    modules: list[ModulePlan],
    generate_content_fn: Callable[[str], Any],
    strip_markdown_fn: Callable[[str], str],
) -> list[ProductGap] | None:
    """Execute an LLM-based red team audit."""
    if not actual_dossier.must_have_invariants or len(all_code.strip()) <= 50:
        return None

    try:
        inv_list = "\n".join(f"- [INV_{i:02d}] {inv}" for i, inv in enumerate(actual_dossier.must_have_invariants, 1))
        leaders_str = ", ".join(actual_dossier.leaders) if actual_dossier.leaders else "Stripe, Vercel, Linear"
        prompt = (
            f"Eres el Principal Engineer y Revisor Hostil de Arquitectura de los líderes de la industria ({leaders_str}).\n"
            "Realiza un Code Review implacable del código implementado frente a los estándares de producción Tier-1 de tu empresa.\n\n"
            f"INVARIANTES REQUERIDOS MINADOS:\n{inv_list}\n\n"
            "RÚBRICA DE CODE REVIEW NO NEGOCIABLE:\n"
            "1. SEGURIDAD Y CONFIANZA EN CLIENTE (Zero-Client Trust):\n"
            "   - ¿Se delega al navegador alguna validación de negocio crítica?\n"
            "   - Si existe, veta la entrega y exige mover la validación a un endpoint de servidor.\n\n"
            "2. CONCURRENCIA Y RESILIENCIA (Idempotency & Race Conditions):\n"
            "   - En acciones mutantes o financieras, ¿existe protección contra doble click e Idempotency-Key?\n"
            "   - Si falta, exige la cabecera o estado de deshabilitación.\n\n"
            "3. ESTÁNDARES Y ROBUSTEZ TÉCNICA (RFC / ISO Compliance):\n"
            "   - ¿Hay asunciones locales o formatos hardcodeados en lugar de estándares universales?\n\n"
            "REGLA ANTI-SOBREINGENIERÍA (YAGNI ESTRICTO):\n"
            "- NO sugieras refactorizaciones cosméticas ni añadir dependencias externas al package.json.\n"
            "- Emite brechas ÚNICAMENTE sobre código defectuoso, vulnerable o que viole la rúbrica anterior.\n\n"
            f"CÓDIGO IMPLEMENTADO:\n```\n{all_code[:50000]}\n```\n\n"
            "Si encuentras violaciones a la rúbrica o invariantes no cubiertos, emite una lista JSON estricta:\n"
            '[{"id": "GAP_STAFF_01", "description": "Descripción precisa del fallo", "target_file": "ruta/al/archivo_responsable"}]\n'
            "Indica en 'target_file' la ruta exacta del archivo responsable que debe corregirse.\n"
            "Si todos los invariantes y la rúbrica están rigurosamente cubiertos con lógica de negocio real, responde: []\n"
            "Devuelve exclusivamente el JSON."
        )
        resp = generate_content_fn(prompt)
        if resp and resp.text:
            clean_json = strip_markdown_fn(resp.text)
            return _parse_red_team_gaps(json.loads(clean_json), modules)
    except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
        logger.debug(f"[APD-Paso4] Fallo en Red Team cognitivo: {ex}. Aplicando auditoría heurística estricta.")
    return None


def run_heuristic_invariants_fallback(
    all_code: str,
    actual_dossier: ProductStrategyDossier,
    modules: list[ModulePlan],
    anti_features_lower: list[str],
) -> list[ProductGap]:
    """Perform a deterministic invariant audit based on lexical-semantic substrate analysis."""
    gaps: list[ProductGap] = []
    for idx, inv in enumerate(actual_dossier.must_have_invariants, 1):
        clean_inv = inv.replace("•", "").strip()
        STOPWORDS = {"funcional", "estable", "sistema", "modulo", "implementar", "óptimo", "adecuado", "relevante"}
        key_terms = [w.lower() for w in clean_inv.split() if len(w) > 4 and w.lower() not in STOPWORDS]
        matched_terms = [t for t in key_terms if t in all_code]

        has_substance = len(all_code.strip()) > 30
        is_satisfied = has_substance and (
            len(matched_terms) >= max(1, min(2, len(key_terms)))
            if key_terms else True
        )

        if not is_satisfied:
            gap_id = f"GAP_INV_{idx:02d}"
            is_yagni = not any(af in inv.lower() for af in anti_features_lower)
            target_file = _resolve_target_module_for_gap(clean_inv, modules)

            gaps.append(ProductGap(
                id=gap_id,
                description=f"Invariante no satisfecho (Red Team): {inv}",
                target_module=target_file,
                is_yagni_approved=is_yagni,
            ))
    return gaps
