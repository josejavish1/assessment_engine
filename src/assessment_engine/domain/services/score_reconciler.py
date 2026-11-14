"""Quantitative State Reconciler Domain Service.

Enforces Single Source of Truth (SSOT) by projecting deterministic scores
from the scoring engine onto stochastic LLM-generated tower payloads,
safely overwriting hallucinated numbers while strictly preserving all qualitative narratives.
"""

from __future__ import annotations

import copy
import logging
import math
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Sequence, Set

logger = logging.getLogger(__name__)

_DECIMAL_SCORE_QUANTIZER = Decimal("0.01")

_ABSENCE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(?:lacks|absence|non-existent|embryonic|incipient|poc|to-be|unimplemented|ad-hoc)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bzero\b(?!\s*[-–]?\s*(?:trust|downtime|loss|rpo|rto|day|touch))",
        re.IGNORECASE,
    ),
)


class QuantitativeSplitBrainError(Exception):
    """Raised when structural topology between SSOT and Payload cannot be reconciled."""


def _normalize_id(identifier: Any) -> str:
    """Normalizes pillar or domain/tower identifiers for deterministic matching."""
    if identifier is None:
        return ""
    return str(identifier).strip().upper()


def _to_finite_decimal(value: Any, context_label: str) -> Decimal:
    """Safely converts a numeric value to a finite Decimal, rejecting NaN/Inf."""
    if value is None or isinstance(value, bool):
        raise QuantitativeSplitBrainError(f"Missing or boolean numeric value for {context_label}: {value!r}")
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise QuantitativeSplitBrainError(
            f"Invalid numeric representation for {context_label}: {value!r}"
        ) from exc

    if not dec.is_finite():
        raise QuantitativeSplitBrainError(
            f"Non-finite numeric value detected for {context_label}: {value!r}"
        )
    return dec


def _resolve_ssot_pillar_weights(
    ssot_pillars: List[Dict[str, Any]],
    domain_id: str,
) -> List[tuple[Decimal, Decimal]]:
    """Resolves normalized [0, 1] and percentage [0, 100] weights across the entire pillar vector."""
    raw_weights: List[Decimal] = []
    for idx, p in enumerate(ssot_pillars):
        p_label = f"Tower '{domain_id}' Pillar[{idx}]"
        raw_val = (
            p.get("weight_pct")
            if p.get("weight_pct") is not None
            else p.get("weight")
        )
        if raw_val is None:
            raise QuantitativeSplitBrainError(f"{p_label} is missing both 'weight_pct' and 'weight'.")
        dec_w = _to_finite_decimal(raw_val, f"{p_label}.weight")
        if dec_w < Decimal("0"):
            raise QuantitativeSplitBrainError(f"{p_label} has illegal negative weight: {dec_w}")
        raw_weights.append(dec_w)

    total_raw = sum(raw_weights, Decimal("0"))
    total_raw_f = float(total_raw)
    if not (math.isclose(total_raw_f, 1.0, abs_tol=0.001) or math.isclose(total_raw_f, 100.0, abs_tol=0.1)):
        raise QuantitativeSplitBrainError(
            f"Tower '{domain_id}' SSOT pillar weights do not sum to unity (1.0 or 100.0). "
            f"Actual sum: {total_raw_f:.6f}."
        )

    is_percentage_scale: bool = math.isclose(total_raw_f, 100.0, abs_tol=0.1)
    resolved: List[tuple[Decimal, Decimal]] = []
    hundred = Decimal("100")
    for dec_w in raw_weights:
        if is_percentage_scale:
            w_pct = dec_w.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            w_norm = (dec_w / hundred).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        else:
            w_norm = dec_w.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            w_pct = (dec_w * hundred).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        resolved.append((w_norm, w_pct))

    return resolved


def _extract_pillar_text(payload_pillar: Dict[str, Any]) -> str:
    """Extracts aggregated textual evidence from health checks and architectural descriptions."""
    findings_part = " ".join(
        str(hc.get("finding", "")) + " " + str(hc.get("business_risk", ""))
        for hc in payload_pillar.get("health_check_asis", [])
        if isinstance(hc, dict)
    )
    desc_part = str(payload_pillar.get("asis_architecture_description", ""))
    thought_part = str(payload_pillar.get("thought_process", ""))
    return f"{findings_part} {desc_part} {thought_part}".lower()


def _has_empirical_absence_evidence(
    pillar_text: str,
    extra_tokens: Sequence[str] = (),
) -> bool:
    """Evaluates whether empirical pillar text indicates absence or embryonic state."""
    if any(p.search(pillar_text) for p in _ABSENCE_PATTERNS):
        return True
    for token in extra_tokens:
        escaped = re.escape(token.strip())
        if escaped and re.search(rf"\b{escaped}\b", pillar_text, re.IGNORECASE):
            return True
    return False


def _extract_optional_float(mapping: Dict[str, Any], *keys: str) -> Optional[float]:
    """Safely extracts the first non-None float from candidate keys without falsy-zero bugs."""
    for k in keys:
        val = mapping.get(k)
        if val is not None and not isinstance(val, bool):
            try:
                flt = float(val)
                if math.isfinite(flt):
                    return max(1.0, min(5.0, flt))
            except (ValueError, TypeError):
                continue
    return None


def _arbitrate_pillar_score(
    payload_pillar: Dict[str, Any],
    exact_p_score: float,
    old_score_flt: Optional[float],
    effective_tower_id: str,
    pillar_label: Any,
    extra_absence_tokens: Sequence[str] = (),
) -> tuple[float, bool]:
    """Arbitrates survey vs empirical evidence under the Empirical Supremacy Invariant.

    Enforces that free-text regex patterns never automatically penalize or downgrade
    canonical survey scores. Overrides only occur when backed by structured, verified
    empirical audit findings within the same domain.
    """
    epistemic_state = str(payload_pillar.get("epistemic_state", "")).strip().upper()

    verified_score_flt = _extract_optional_float(
        payload_pillar, "verified_empirical_score", "empirical_score", "calibrated_score"
    )

    # Formal audit override (RFC-083, RFC-085 & Universal Epistemic Plan):
    # Only trigger survey inflation arbitration if:
    # 1. An explicit structured verified empirical score is provided and diverges >= 0.25, OR
    # 2. An explicit foundational discovery finding (<= 1.59, Level 1 Initial) proves capability absence with delta > 1.0.
    # Textual keyword matching in LLM prose is strictly prohibited from altering scores.
    is_survey_inflation = (
        (verified_score_flt is not None and abs(exact_p_score - verified_score_flt) >= 0.25)
        or (
            old_score_flt is not None
            and (exact_p_score - old_score_flt) > 1.0
            and (
                old_score_flt <= 1.59
                or epistemic_state in {"UNOBSERVED_BLINDSPOT", "EMBRYONIC", "ABSENT"}
            )
        )
    )

    if not is_survey_inflation:
        old_score = payload_pillar.get("score")
        if old_score != exact_p_score:
            logger.info(
                "[SSOT Reconciler] Tower %s | Pillar %s: Overwriting hallucinated score (%s) -> SSOT (%s).",
                effective_tower_id,
                pillar_label,
                old_score,
                exact_p_score,
            )
        return exact_p_score, False

    if verified_score_flt is not None:
        empirical_candidate = verified_score_flt
    else:
        empirical_candidate = old_score_flt if old_score_flt is not None else 1.25

    reconciled_score = round(max(1.0, min(5.0, empirical_candidate)), 2)
    perception_delta = round(exact_p_score - reconciled_score, 2)
    logger.warning(
        "[SSOT Reconciler] Rejecting survey inflation on Tower %s | Pillar %s: "
        "Survey declared (%s) vs Empirical evidence (%s) | Delta=+%s. Enforcing Empirical Supremacy.",
        effective_tower_id,
        pillar_label,
        exact_p_score,
        reconciled_score,
        perception_delta,
    )
    payload_pillar["declared_score"] = exact_p_score
    payload_pillar["survey_declared_score"] = exact_p_score
    payload_pillar["calibrated_score"] = reconciled_score
    payload_pillar["perception_gap_delta"] = -perception_delta
    payload_pillar["perception_gap_warning"] = True
    return reconciled_score, True


def _resolve_matched_ssot_index(
    payload_pillar: Dict[str, Any],
    idx: int,
    ssot_pillars: List[Dict[str, Any]],
    ssot_index_by_id: Dict[str, int],
    consumed_indices: Set[int],
    effective_tower_id: str,
) -> int:
    """Deterministically identifies the corresponding SSOT pillar index."""
    raw_id = payload_pillar.get("pillar_id") if payload_pillar.get("pillar_id") is not None else payload_pillar.get("id")
    p_id = _normalize_id(raw_id)
    short_id = p_id.split(".")[-1] if "." in p_id else p_id

    matched_idx = ssot_index_by_id.get(p_id)
    if matched_idx is None:
        matched_idx = ssot_index_by_id.get(short_id)

    if matched_idx is None or matched_idx in consumed_indices:
        if idx not in consumed_indices:
            fallback_idx = idx
        else:
            remaining = [i for i in range(len(ssot_pillars)) if i not in consumed_indices]
            fallback_idx = remaining[0]
        logger.warning(
            "Tower '%s': Pillar ID '%s' not uniquely matched in SSOT. Falling back to SSOT index [%d].",
            effective_tower_id,
            raw_id,
            fallback_idx,
        )
        matched_idx = fallback_idx

    consumed_indices.add(matched_idx)
    return matched_idx


def _validate_reconciliation_inputs(
    tower_payload: Dict[str, Any],
    scoring_ssot: Dict[str, Any],
    precision: str,
) -> tuple[Dict[str, Any], str, Decimal]:
    """Validates root inputs, creates defensive deepcopy, and resolves effective domain ID."""
    if not isinstance(tower_payload, dict):
        raise QuantitativeSplitBrainError("tower_payload must be a dictionary.")
    if not isinstance(scoring_ssot, dict):
        raise QuantitativeSplitBrainError("scoring_ssot must be a dictionary.")

    result_payload = copy.deepcopy(tower_payload)
    doc_meta = result_payload.get("document_meta")
    meta_tower_code = doc_meta.get("tower_code") if isinstance(doc_meta, dict) else None

    tower_id = _normalize_id(
        result_payload.get("tower_id")
        or meta_tower_code
        or result_payload.get("tower_code")
        or result_payload.get("domain_id")
    )
    ssot_tower_id = _normalize_id(
        scoring_ssot.get("tower_id")
        or scoring_ssot.get("domain_id")
        or scoring_ssot.get("tower_code")
    )

    if tower_id and ssot_tower_id and tower_id != ssot_tower_id:
        raise QuantitativeSplitBrainError(
            f"Topology mismatch: Payload Tower ID ('{tower_id}') != SSOT Tower ID ('{ssot_tower_id}')."
        )

    effective_tower_id = tower_id or ssot_tower_id or "UNKNOWN_DOMAIN"
    quantizer = Decimal(precision)
    return result_payload, effective_tower_id, quantizer


def _extract_and_validate_pillars(
    result_payload: Dict[str, Any],
    scoring_ssot: Dict[str, Any],
    effective_tower_id: str,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[tuple[Decimal, Decimal]], Dict[str, int]]:
    """Extracts and validates pillar topology and cardinality across SSOT and payload."""
    raw_ssot_pillars = (
        scoring_ssot.get("pillar_scores")
        if scoring_ssot.get("pillar_scores") is not None
        else scoring_ssot.get("pillars")
    )
    if not isinstance(raw_ssot_pillars, list) or len(raw_ssot_pillars) == 0:
        raise QuantitativeSplitBrainError(
            f"SSOT for Tower '{effective_tower_id}' contains zero pillars."
        )

    ssot_pillars: List[Dict[str, Any]] = [p for p in raw_ssot_pillars if isinstance(p, dict)]
    resolved_weights = _resolve_ssot_pillar_weights(ssot_pillars, effective_tower_id)

    ssot_index_by_id: Dict[str, int] = {}
    for idx, p in enumerate(ssot_pillars):
        p_id = _normalize_id(p.get("pillar_id") if p.get("pillar_id") is not None else p.get("id"))
        if p_id:
            ssot_index_by_id[p_id] = idx
            if "." in p_id:
                ssot_index_by_id.setdefault(p_id.split(".")[-1], idx)

    payload_pillars = result_payload.get("pillars_analysis")
    if not isinstance(payload_pillars, list):
        raise QuantitativeSplitBrainError(
            f"Payload for Tower '{effective_tower_id}' has missing or invalid 'pillars_analysis' list."
        )

    if len(payload_pillars) != len(ssot_pillars):
        raise QuantitativeSplitBrainError(
            f"Cardinality violation in Tower '{effective_tower_id}': Payload has "
            f"{len(payload_pillars)} pillars, but topology SSOT specifies {len(ssot_pillars)}."
        )

    return payload_pillars, ssot_pillars, resolved_weights, ssot_index_by_id


def _apply_pillar_reconciliation(
    payload_pillars: List[Dict[str, Any]],
    ssot_pillars: List[Dict[str, Any]],
    ssot_index_by_id: Dict[str, int],
    resolved_weights: List[tuple[Decimal, Decimal]],
    effective_tower_id: str,
    quantizer: Decimal,
    extra_absence_tokens: Sequence[str],
    calibration_overrides: Sequence[Dict[str, Any]] = (),
) -> bool:
    """Iterates through all pillars, arbitrating scores and setting deterministic weights."""
    consumed_ssot_indices: Set[int] = set()
    any_arbitrated = False

    for idx, payload_pillar in enumerate(payload_pillars):
        if not isinstance(payload_pillar, dict):
            raise QuantitativeSplitBrainError(
                f"Payload for Tower '{effective_tower_id}' contains non-object pillar at index {idx}."
            )

        matched_idx = _resolve_matched_ssot_index(
            payload_pillar, idx, ssot_pillars, ssot_index_by_id, consumed_ssot_indices, effective_tower_id
        )
        matched_ssot = ssot_pillars[matched_idx]
        if matched_ssot.get("pillar_id"):
            payload_pillar["pillar_id"] = matched_ssot["pillar_id"]

        raw_p_score = (
            matched_ssot.get("score_exact")
            if matched_ssot.get("score_exact") is not None
            else matched_ssot.get("score")
        )
        p_score_dec = _to_finite_decimal(
            raw_p_score,
            f"Tower '{effective_tower_id}' Pillar '{matched_ssot.get('pillar_id', matched_idx)}' score",
        )
        exact_p_score = float(p_score_dec.quantize(quantizer, rounding=ROUND_HALF_UP))
        w_norm_dec, w_pct_dec = resolved_weights[matched_idx]

        # Bind explicit RFC-083 calibration override if present
        p_id = str(payload_pillar.get("pillar_id") or "").strip()
        matched_p_id = str(matched_ssot.get("pillar_id") or "").strip()
        for ov in calibration_overrides:
            target_pid = str(ov.get("pillar_id") or "").strip()
            if target_pid and (target_pid == p_id or target_pid == matched_p_id):
                cal_s = float(ov["calibrated_score"])
                payload_pillar["verified_empirical_score"] = cal_s
                payload_pillar["calibrated_score"] = cal_s
                payload_pillar["declared_score"] = float(ov.get("declared_score", exact_p_score))
                if ov.get("calibration_rationale"):
                    payload_pillar["calibration_rationale"] = ov.get("calibration_rationale")

        old_score_flt = _extract_optional_float(payload_pillar, "score")

        reconciled_score, was_arbitrated = _arbitrate_pillar_score(
            payload_pillar=payload_pillar,
            exact_p_score=exact_p_score,
            old_score_flt=old_score_flt,
            effective_tower_id=effective_tower_id,
            pillar_label=payload_pillar.get("pillar_id", idx),
            extra_absence_tokens=extra_absence_tokens,
        )
        if was_arbitrated:
            any_arbitrated = True

        payload_pillar["score"] = reconciled_score
        payload_pillar["exact_score"] = reconciled_score
        payload_pillar["weight"] = float(w_norm_dec)
        payload_pillar["weight_pct"] = float(
            w_pct_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        )

        canonical_name = matched_ssot.get("pillar_name") if matched_ssot.get("pillar_name") is not None else matched_ssot.get("name")
        if canonical_name and "pillar_name" in payload_pillar:
            payload_pillar["pillar_name"] = str(canonical_name).strip()

    return any_arbitrated


def _finalize_root_score(
    result_payload: Dict[str, Any],
    payload_pillars: List[Dict[str, Any]],
    quantizer: Decimal,
    effective_tower_id: str,
    any_arbitrated: bool,
) -> None:
    """Computes exact dot-product root score and syncs both executive summary and snapshot."""
    recalculated_root = sum(
        Decimal(str(p["score"])) * Decimal(str(p["weight"]))
        for p in payload_pillars
    )
    recalculated_root_flt = float(recalculated_root.quantize(quantizer, rounding=ROUND_HALF_UP))

    if any_arbitrated:
        logger.warning(
            "[SSOT Reconciler] Recomputing Tower %s root score due to Empirical Supremacy: -> %s",
            effective_tower_id,
            recalculated_root_flt,
        )

    result_payload["score"] = recalculated_root_flt
    result_payload["exact_score"] = float(recalculated_root)
    result_payload["overall_score"] = recalculated_root_flt
    result_payload["maturity_score"] = recalculated_root_flt

    formatted_score = f"{recalculated_root_flt:.2f}"
    numeric_score = float(recalculated_root)

    for exec_key in ("executive_summary", "executive_snapshot"):
        if isinstance(result_payload.get(exec_key), dict):
            result_payload[exec_key]["global_score"] = formatted_score
            result_payload[exec_key]["global_score_numeric"] = numeric_score


def reconcile_tower_scores(
    tower_payload: Dict[str, Any],
    scoring_ssot: Dict[str, Any],
    precision: str = "0.01",
    extra_absence_tokens: Sequence[str] = (),
) -> Dict[str, Any]:
    """Overwrites hallucinated scores and weights in the tower payload with

    the deterministic outputs from run_scoring.py::build_scoring().
    Preserves all qualitative narratives, evidence links, and health checks.
    """
    result_payload, effective_tower_id, quantizer = _validate_reconciliation_inputs(
        tower_payload, scoring_ssot, precision
    )

    (
        payload_pillars,
        ssot_pillars,
        resolved_weights,
        ssot_index_by_id,
    ) = _extract_and_validate_pillars(result_payload, scoring_ssot, effective_tower_id)

    overrides_list = result_payload.get("calibration_overrides") or []
    if not overrides_list:
        intel_d = result_payload.get("client_intelligence") or {}
        overrides_list = intel_d.get("calibration_overrides", [])

    any_arbitrated = _apply_pillar_reconciliation(
        payload_pillars,
        ssot_pillars,
        ssot_index_by_id,
        resolved_weights,
        effective_tower_id,
        quantizer,
        extra_absence_tokens,
        overrides_list,
    )

    _finalize_root_score(result_payload, payload_pillars, quantizer, effective_tower_id, any_arbitrated)

    return result_payload
