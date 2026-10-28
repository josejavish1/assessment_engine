"""
Synthesize and resolve implementation gaps for the Autonomous Product Director. Decoupled from autonomous_product_director.py to maintain modularity and prevent monolithic files.
"""
from __future__ import annotations

import difflib
import json
import logging
import re
from pathlib import Path
from typing import Any, Callable

from assessment_engine.infrastructure.evolution.orthogonal_gates import orthogonal_gates
from assessment_engine.infrastructure.evolution.reflexion_ledger import reflexion_ledger
from assessment_engine.infrastructure.evolution.sota_sourcer import CleanRoomPayload
from .director_models import ModulePlan, ProductGap

logger = logging.getLogger("assessment_engine.infrastructure.evolution.director_synthesizer")


def strip_markdown_fences(code: str) -> str:
    """Strip markdown code fences to produce pure compilable code."""
    lines = code.splitlines()
    while lines and lines[0].strip().startswith("```"):
        lines.pop(0)
    while lines and lines[-1].strip().startswith("```"):
        lines.pop()
    return "\n".join(lines).strip()


def _calculate_search_range(
    orig_len: int, search_len: int, norm_to_orig: list[int], start_line_hint: int | None
) -> range:
    """Calculate target sliding window search range using optional line hint."""
    max_start = orig_len - search_len + 1
    if start_line_hint is None or not norm_to_orig:
        return range(max(0, max_start))

    closest_norm_idx = min(
        range(len(norm_to_orig)),
        key=lambda idx: abs(norm_to_orig[idx] + 1 - start_line_hint),
        default=0,
    )
    window_start = max(0, closest_norm_idx - 30)
    window_end = min(max_start, closest_norm_idx + 30)
    return range(window_start, window_end)


def _fuzzy_locate_search_block(
    orig_lines: list[str],
    search_lines_norm: list[str],
    start_line_hint: int | None,
) -> tuple[int, int, float]:
    """Locate a fuzzy search block using a sliding window over normalized lines."""
    norm_to_orig = [idx for idx, line in enumerate(orig_lines) if line.strip()]
    orig_lines_norm = [line.strip() for line in orig_lines if line.strip()]

    search_len = len(search_lines_norm)
    best_match_idx = -1
    best_match_ratio = 0.0

    search_range = _calculate_search_range(len(orig_lines_norm), search_len, norm_to_orig, start_line_hint)
    norm_search_str = "\n".join(search_lines_norm)

    for i in search_range:
        window = orig_lines_norm[i : i + search_len]
        if window == search_lines_norm:
            best_match_idx = i
            best_match_ratio = 1.0
            break

        ratio = difflib.SequenceMatcher(None, norm_search_str, "\n".join(window)).ratio()
        if ratio > best_match_ratio:
            best_match_ratio = ratio
            best_match_idx = i

    if best_match_idx != -1 and (best_match_idx + search_len - 1) < len(norm_to_orig):
        return norm_to_orig[best_match_idx], norm_to_orig[best_match_idx + search_len - 1], best_match_ratio
    return -1, -1, best_match_ratio


def _apply_single_diff_block(
    current_code: str, start_line_str: str, search_text: str, replace_text: str
) -> str:
    """Apply a single diff block using exact, trimmed, or fuzzy matching."""
    if search_text in current_code:
        return current_code.replace(search_text, replace_text, 1)

    if search_text.strip() in current_code:
        return current_code.replace(search_text.strip(), replace_text.strip(), 1)

    search_lines_norm = [line.strip() for line in search_text.splitlines() if line.strip()]
    if not search_lines_norm:
        return current_code

    start_line_hint = int(start_line_str) if start_line_str and start_line_str.isdigit() else None
    orig_lines = current_code.splitlines(True)
    start_orig, end_orig, ratio = _fuzzy_locate_search_block(orig_lines, search_lines_norm, start_line_hint)
    threshold = 0.7 if start_line_hint is not None else 0.8

    if ratio >= threshold and start_orig != -1:
        candidate_text = "".join(orig_lines[start_orig : end_orig + 1])
        logger.info(f"[APD-Diff] Fuzzy Match exitoso (ratio: {ratio:.2f}) para bloque rebelde.")
        return current_code.replace(candidate_text, replace_text, 1)

    logger.warning(f"[APD-Diff] Fallo al localizar el bloque (fuzzy ratio muy bajo: {ratio:.2f}):\n{search_text[:100]}...")
    return current_code


def apply_search_replace_blocks(original_code: str, response_text: str) -> str:
    """Apply search-and-replace diff blocks to the original code using line-anchored fuzzy matching."""
    pattern = re.compile(r"(?:START_LINE:\s*(\d+)\s*\n)?<<<<\n?(.*?)\n?====\n?(.*?)\n?>>>>", re.DOTALL)
    blocks = pattern.findall(response_text)

    if not blocks:
        clean = strip_markdown_fences(response_text)
        if clean and len(clean.strip()) > 20 and "<<<<" not in clean:
            return clean
        return original_code

    new_code = original_code
    for start_line_str, search_text, replace_text in blocks:
        new_code = _apply_single_diff_block(new_code, start_line_str, search_text, replace_text)

    return new_code


def find_relevant_primitives_skeletons(task_description: str) -> str:
    """Find relevant classes and signatures in core/primitives/ to include as contracts in the prompt."""
    t_low = task_description.lower()
    skeletons: list[str] = []

    if any(k in t_low for k in ("pdf", "invoice", "doc", "print", "document")):
        skeletons.append(
            "// core/primitives/pdf_document_assembler.py\n"
            "class PdfDocumentAssembler:\n"
            "    def assemble_html_for_print(self, title: str, metadata: dict, sections: list) -> str: ...\n"
            "    def generate_pdf_bytes(self, html_content: str) -> bytes: ...\n"
        )
    if any(k in t_low for k in ("pricing", "charge", "tier", "quote", "discount", "tax", "vat")):
        skeletons.append(
            "// core/primitives/pricing_rules_engine.py\n"
            "class PricingRulesEngine:\n"
            "    def calculate_quote(self, base_cents: int, add_ons: list, coupon_code: str = None) -> QuoteResult: ...\n"
        )
    if any(k in t_low for k in ("map", "geo", "distance", "coord", "proximity")):
        skeletons.append(
            "// core/primitives/geo_engine.py\n"
            "class GeoEngine:\n"
            "    def haversine_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float: ...\n"
            "    def filter_within_radius(self, origin: tuple, items: list, radius_km: float) -> list: ...\n"
        )
    if any(k in t_low for k in ("sse", "stream", "realtime", "event", "feed")):
        skeletons.append(
            "// core/primitives/realtime_sse.py\n"
            "class SseStreamBroadcaster:\n"
            "    async def stream_generator(self, channel_id: str) -> AsyncGenerator[str, None]: ...\n"
            "    def publish_event(self, channel_id: str, event_data: dict) -> None: ...\n"
        )
    return "\n".join(skeletons)


def build_synthesis_prompt(
    target_file: str,
    current_code: str,
    file_mods: list[ModulePlan],
    clean_room_payloads: list[CleanRoomPayload] | None,
    repo_root: Path,
) -> str:
    """Construct the formal engineering prompt for Gemini with immutable system constraints."""
    ref_snippets = []
    if clean_room_payloads:
        for payload in clean_room_payloads:
            for cf in payload.files[:2]:
                ref_snippets.append(
                    f"// --- REFERENCIA GITHUB [{payload.repo_name} / {cf.rel_path}] ---\n"
                    f"{cf.code[:1500]}\n"
                )
    ref_text = "\n".join(ref_snippets) if ref_snippets else "// Sin repositorio externo de referencia."
    cap_list = "\n".join(f"- [{m.id}] {m.name}: {m.purpose}" for m in file_mods)

    ui_anchor = ""
    if target_file.endswith((".tsx", ".jsx")):
        ui_anchor = (
            "5. ANCLAJE DE UX/UI: Este archivo es un componente de Interfaz de Usuario (React).\n"
            "   Es OBLIGATORIO utilizar componentes de Tailwind CSS y Lucide Icons.\n"
        )

    preflight_block = reflexion_ledger.format_preflight_prompt_block(target_file)
    if preflight_block:
        preflight_block = f"\n{preflight_block}\n"

    prompt = (
        f"Eres el Ingeniero Principal de Autonomuos (SOTA 2026).\n"
        f"Tu misión es implementar las siguientes capacidades en '{target_file}':\n\n"
        f"CAPACIDADES A IMPLEMENTAR:\n{cap_list}\n\n"
        f"CÓDIGO BASE PREEXISTENTE:\n```\n{current_code[:40000]}\n```\n\n"
        f"REFERENCIA CLEAN-ROOM DE GITHUB:\n```\n{ref_text}\n```\n\n"
        f"{preflight_block}"
        "REGLAS INMUTABLES DE INGENIERÍA:\n"
        "1. Preserva el 100% de la funcionalidad preexistente. Construye de forma aditiva.\n"
        "2. Cero librerías externas no instaladas. Usa primitivas locales a coste $0.00.\n"
        "3. Tipado estricto sin casts 'any'.\n"
        "4. SOBERANÍA: Usa Web APIs nativas W3C ('crypto.subtle', 'Intl', 'ResizeObserver').\n"
        "5. SUSTRATO FUNCIONAL: PROHIBIDO usar iconos estáticos como sustitutos de funcionalidad.\n"
        "6. SIMETRÍA: Endpoints StreamingResponse/FileResponse para recursos exportables.\n"
        "7. CABLEADO LOCAL: Conecta el frontend con la API local ('/api/...') vía fetch().\n"
        "8. PREFIJOS LIMPIOS: Define prefijos relativos en routers (ej. prefix='' o prefix='/maps').\n"
    )

    task_desc = " ".join(f"{m.name} {m.purpose}" for m in file_mods) + f" {target_file}"
    skeletons = find_relevant_primitives_skeletons(task_desc)
    if skeletons:
        prompt += f"\n### CONTRATO DE REUTILIZACIÓN DE PRIMITIVAS:\n{skeletons}\n\n"

    target_path_obj = repo_root / target_file
    is_new = not target_path_obj.exists() or current_code.strip().startswith(("// Autonomuos Module:", "# Autonomuos Module:"))

    if target_file.endswith(".json") or is_new:
        prompt += "4. Devuelve el archivo COMPLETO dentro de un bloque markdown ```<lang> ... ```.\n"
    else:
        prompt += (
            "4. Devuelve EXCLUSIVAMENTE bloques de búsqueda y reemplazo (SEARCH/REPLACE):\n"
            "START_LINE: <línea_inicio>\n<<<<\ncódigo original\n====\nnuevo código\n>>>>\n"
        )
    prompt += ui_anchor
    return prompt


def generate_and_parse_candidate(
    prompt: str,
    target_file: str,
    current_code: str,
    is_new_file: bool,
    generate_content_fn: Callable[..., Any],
    apply_search_replace_fn: Callable[[str, str], str],
    cache_name: Any | None = None,
) -> tuple[str, str]:
    """Stream code generation via Gemini and reconcile replacement blocks or markdown formatting."""
    resp_stream = generate_content_fn(prompt, stream=True, cache_name=cache_name)
    full_text = ""
    if resp_stream:
        try:
            for chunk in resp_stream:
                if chunk.text:
                    full_text += chunk.text
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex_stream:
            logger.warning(f"[APD-Stream] Stream interrumpido ({ex_stream}). Fallback directo...")
            resp_direct = generate_content_fn(prompt, stream=False, cache_name=None)
            full_text = resp_direct.text if (resp_direct and resp_direct.text) else ""

        if is_new_file or target_file.endswith(".json"):
            match = re.search(r"```[a-zA-Z0-9_-]*\n(.*?)\n```", full_text, flags=re.DOTALL)
            cand_code = match.group(1).strip() if match else full_text.strip()
        else:
            cand_code = apply_search_replace_fn(current_code, full_text)
            if cand_code == current_code:
                match = re.search(r"```[a-zA-Z0-9_-]*\n(.*?)\n```", full_text, flags=re.DOTALL)
                if match and len(match.group(1).strip()) > 50:
                    cand_code = match.group(1).strip()

        return cand_code, full_text

    return current_code, ""


def synthesize_file_best_of_n(
    prompt: str,
    target_file: str,
    current_code: str,
    is_new_file: bool,
    repo_root: Path,
    batch_files: dict[str, str] | None,
    generate_content_fn: Callable[..., Any],
    apply_search_replace_fn: Callable[[str, str], str],
    cache_name: Any | None = None,
) -> str:
    """Execute the test-time compute protocol (Best-of-N, N=2) guided by orthogonal gating."""
    cand_1_code, full_text_1 = generate_and_parse_candidate(
        prompt, target_file, current_code, is_new_file,
        generate_content_fn, apply_search_replace_fn, cache_name,
    )

    if len(cand_1_code.strip()) <= 50:
        return cand_1_code

    gate_rep_1 = orthogonal_gates.evaluate_all(
        target_file_rel=target_file,
        candidate_code=cand_1_code,
        baseline_code=current_code,
        workspace_dir=repo_root,
        batch_files=batch_files,
    )

    if gate_rep_1.passed:
        logger.info("[APD-TestTimeCompute] Candidato 1 superó las 4 compuertas ortogonales al primer intento (Pass@1).")
        return cand_1_code

    failed = gate_rep_1.failed_gate
    logger.warning(
        f"[APD-TestTimeCompute] Candidato 1 vetado por {failed.gate_name} ({failed.failure_signature}). "
        f"Generando Candidato 2 guiado por la compuerta..."
    )
    reflexion_ledger.record_failure(
        category=failed.gate_name,
        error_signature=failed.failure_signature or "GATE_FAILURE",
        target_file=target_file,
        corrective_axiom=failed.prescriptive_action or "Subsanar fallo de compuerta.",
    )

    prompt_2 = (
        f"{prompt}\n\n"
        f"ALERTA CRÍTICA: El intento previo falló la compuerta [{failed.gate_name}] ({failed.failure_signature}):\n"
        f"{failed.prescriptive_action}\n"
    )
    if is_new_file:
        prompt_2 += "Corrige esta deficiencia y vuelve a generar el archivo completo en un bloque markdown.\n"
    else:
        prompt_2 += "Corrige esta deficiencia estrictamente en los bloques de reemplazo (search/replace).\n"

    cand_2_code, full_text_2 = generate_and_parse_candidate(
        prompt_2, target_file, current_code, is_new_file,
        generate_content_fn, apply_search_replace_fn, cache_name,
    )

    gate_rep_2 = orthogonal_gates.evaluate_all(
        target_file_rel=target_file,
        candidate_code=cand_2_code,
        baseline_code=current_code,
        workspace_dir=repo_root,
        batch_files=batch_files,
    )

    if gate_rep_2.passed:
        logger.info("[APD-TestTimeCompute] Candidato 2 aprobado con éxito tras feedback de compuerta.")
        reflexion_ledger.record_contrastive_exemplar(
            category=failed.gate_name,
            task_hint=target_file,
            failed_snippet=full_text_1[:1200],
            verified_diff=full_text_2[:1500],
        )
        return cand_2_code

    logger.warning("[APD-TestTimeCompute] Ambos candidatos tienen observaciones. Aplicando Ockham Reranker...")
    return cand_2_code if len(cand_2_code) <= len(cand_1_code) else cand_1_code
