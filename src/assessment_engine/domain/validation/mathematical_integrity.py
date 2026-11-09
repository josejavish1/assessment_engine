"""Mathematical Integrity Gatekeeper Domain Service.

Guarantees that sum_product(pillars.score, pillars.weight) == tower.score
within strict floating-point quantization tolerances across any N-pillar topology.
"""

from __future__ import annotations

import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List


class MathematicalIntegrityViolation(AssertionError):
    """Raised when a tower payload violates quantitative conservation laws."""


def _parse_finite_decimal(value: Any, label: str) -> Decimal:
    """Validates and converts a numeric field to a finite Decimal."""
    if value is None or isinstance(value, bool):
        raise MathematicalIntegrityViolation(f"{label} is null or boolean ({value!r}).")
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise MathematicalIntegrityViolation(
            f"{label} has invalid numeric representation ({value!r})."
        ) from exc

    if not dec.is_finite():
        raise MathematicalIntegrityViolation(
            f"{label} is non-finite ({value!r})."
        )
    return dec


def assert_tower_mathematical_integrity(
    tower_payload: Dict[str, Any],
    score_tolerance: float = 0.015,
    weight_tolerance: float = 0.001,
) -> None:
    """Validates fundamental invariants across any N-pillar topology:

    1. Non-Negativity & Finiteness: Every pillar weight >= 0 and finite; scores are finite.
    2. Conservation of Probability/Weight: Sum(pillar.weight) == 1.0 (or 100.0 if percentage-based).
    3. Dot-Product Identity: Sum(pillar.score * normalized_weight) == tower.score.

    :raises MathematicalIntegrityViolation: if any invariant is breached.
    """
    if not isinstance(tower_payload, dict):
        raise MathematicalIntegrityViolation("Tower payload must be a JSON object / dict.")

    doc_meta = tower_payload.get("document_meta")
    meta_code = doc_meta.get("tower_code") if isinstance(doc_meta, dict) else None

    tower_id = str(
        tower_payload.get("tower_id")
        or meta_code
        or tower_payload.get("tower_code")
        or tower_payload.get("domain_id")
        or "UNKNOWN_TOWER"
    ).strip()

    tower_score_raw = tower_payload.get("score")
    if tower_score_raw is None:
        raise MathematicalIntegrityViolation(f"[{tower_id}] Missing root 'score' attribute.")

    tower_score_dec = _parse_finite_decimal(tower_score_raw, f"[{tower_id}] root 'score'")

    pillars: List[Dict[str, Any]] = tower_payload.get("pillars_analysis", [])
    if not isinstance(pillars, list) or not pillars:
        raise MathematicalIntegrityViolation(
            f"[{tower_id}] 'pillars_analysis' array is empty or missing."
        )

    # Determine whether to evaluate uniform 'weight' or uniform 'weight_pct' across the vector
    use_normalized_key = all(
        isinstance(p, dict) and p.get("weight") is not None for p in pillars
    )

    total_raw_weight = Decimal("0")
    weighted_score_sum = Decimal("0")

    for idx, p in enumerate(pillars):
        if not isinstance(p, dict):
            raise MathematicalIntegrityViolation(
                f"[{tower_id} -> INDEX_{idx}] Pillar entry is not a dictionary."
            )
        p_id = p.get("pillar_id", f"INDEX_{idx}")
        p_score_raw = p.get("score")
        p_weight_raw = (
            p.get("weight")
            if use_normalized_key
            else (p.get("weight") if p.get("weight") is not None else p.get("weight_pct"))
        )

        if p_score_raw is None or p_weight_raw is None:
            raise MathematicalIntegrityViolation(
                f"[{tower_id} -> {p_id}] Null quantitative metric detected "
                f"(score={p_score_raw}, weight={p_weight_raw})."
            )

        p_score_dec = _parse_finite_decimal(p_score_raw, f"[{tower_id} -> {p_id}] score")
        p_weight_dec = _parse_finite_decimal(p_weight_raw, f"[{tower_id} -> {p_id}] weight")

        if p_weight_dec < Decimal("0"):
            raise MathematicalIntegrityViolation(
                f"[{tower_id} -> {p_id}] Negative pillar weight detected ({p_weight_dec})."
            )

        total_raw_weight += p_weight_dec
        weighted_score_sum += p_score_dec * p_weight_dec

    total_raw_weight_float = float(total_raw_weight)

    # Handle percentage weights (sum == 100.0) vs normalized weights (sum == 1.0)
    if math.isclose(total_raw_weight_float, 1.0, abs_tol=weight_tolerance):
        normalized_weighted_sum = weighted_score_sum
    elif math.isclose(total_raw_weight_float, 100.0, abs_tol=weight_tolerance * 100.0):
        normalized_weighted_sum = weighted_score_sum / Decimal("100")
    else:
        raise MathematicalIntegrityViolation(
            f"[{tower_id}] Pillar weights do not sum to unity (1.0 or 100.0). "
            f"Actual sum: {total_raw_weight_float:.6f}"
        )

    quantized_calculated_score = float(
        normalized_weighted_sum.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    reported_tower_score = float(
        tower_score_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )

    delta = abs(quantized_calculated_score - reported_tower_score)
    if delta > score_tolerance:
        pillar_debug = ", ".join(
            [
                f"{p.get('pillar_id', f'P{i}')}:"
                f"(S={p.get('score')}, W={p.get('weight') if p.get('weight') is not None else p.get('weight_pct')})"
                for i, p in enumerate(pillars)
            ]
        )
        raise MathematicalIntegrityViolation(
            f"SPLIT-BRAIN DETECTED in [{tower_id}]!\n"
            f"  Reported Tower Score : {reported_tower_score:.2f}\n"
            f"  Calculated DotProduct: {quantized_calculated_score:.2f} (Raw: {float(normalized_weighted_sum):.4f})\n"
            f"  Variance Delta       : {delta:.4f} (Max Allowed Tolerance: {score_tolerance})\n"
            f"  Pillar Breakdown     : [{pillar_debug}]"
        )
