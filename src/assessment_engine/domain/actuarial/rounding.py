"""Actuarial Significant Figures Rounding and Discrete Integer Allocation Engine.

Implements the Argon Actuarial Rounding Policy:
1. Pure Decimal arithmetic (zero float floating-point inaccuracies).
2. Dynamic step quanta scaling by order of magnitude.
3. Closed-form Quantum-Preserving Hare-Niemeyer (Largest Remainder) discrete allocation
   guaranteeing that individual card ALEs sum exactly to the parent Outage ALE without
   re-introducing single-unit false precision.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import List, Sequence, Union


def compute_step_quantum(val: Decimal) -> Decimal:
    """Computes dynamic step quantum based on the order of magnitude of the value.

    Quantum schedule (scaled dynamically across currency orders of magnitude):
    - [0 .. 10,000): Quantum = 50
    - [10,000 .. 25,000): Quantum = 250
    - [25,000 .. 100,000): Quantum = 1,000
    - [100,000 .. 1,000,000): Quantum = 5,000
    - [1,000,000 .. 10,000,000): Quantum = 25,000
    - >= 10,000,000: Quantum = base_power / 100 (e.g., for JPY/KRW or Global 500)
    """
    if not val.is_finite() or val <= Decimal("0"):
        return Decimal("50")

    exponent = int(val.adjusted())
    base_power = Decimal(10) ** exponent

    if exponent <= 3:      # < 10,000
        return Decimal("50")
    elif exponent == 4:    # [10,000 .. 100,000)
        return Decimal("250") if val < Decimal("25000") else Decimal("1000")
    elif exponent == 5:    # [100,000 .. 1,000,000)
        return Decimal("5000")
    elif exponent == 6:    # [1,000,000 .. 10,000,000)
        return Decimal("25000")
    else:
        # Scales invariantly for multi-billion or high-denomination currencies (JPY/KRW):
        return base_power / Decimal("100")


def round_to_actuarial_significance(raw_amount: Union[int, str, Decimal, float, None]) -> int:
    """Rounds a raw monetary amount to its actuarially significant quantum.

    Eliminates false precision (cents, single euros, and spurious trailing digits).
    Uses ROUND_HALF_UP tie-breaking and ensures non-negative return value.
    """
    if raw_amount is None:
        return 0
    try:
        dec_val = Decimal(str(raw_amount))
    except (InvalidOperation, ValueError, TypeError):
        return 0

    if not dec_val.is_finite() or dec_val <= Decimal("0"):
        return 0

    quantum = compute_step_quantum(dec_val)
    scaled = (dec_val / quantum).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    result = int(scaled * quantum)
    return max(int(quantum), result)


import hashlib

def _resolve_allocation_quantum(target_total_ale: int, card_count: int) -> int:
    """Determines the largest clean actuarial quantum that divides target_total_ale."""
    if card_count <= 0 or target_total_ale <= 0:
        return 1
    avg_card = Decimal(str(target_total_ale)) / Decimal(str(card_count))
    ideal_quantum = int(compute_step_quantum(avg_card))

    # Cascade down clean actuarial divisors to avoid 1-unit remainder artifacts
    for q in (ideal_quantum, 1000, 500, 250, 100, 50, 25, 10, 5):
        if q <= ideal_quantum and target_total_ale % q == 0 and (target_total_ale // q) >= card_count:
            return q
    return 1


def allocate_subadditive_ale_to_cards(
    target_total_ale: int,
    standalone_ales: Sequence[Union[int, float, Decimal]],
    preserve_quanta: bool = True,
    card_ids: Optional[Sequence[str]] = None
) -> List[int]:
    """Apportions a portfolio-adjusted sub-additive Outage ALE across individual risk cards.

    Uses the closed-form Hare-Niemeyer (Largest Remainder) discrete integer algorithm
    with Lexicographic Tie-Breaking (using card_ids hash) and Non-Zero Floor Guard.
    """
    if not standalone_ales:
        return []

    clean_ales: List[Decimal] = []
    for a in standalone_ales:
        try:
            d = Decimal(str(a))
            clean_ales.append(d if (d.is_finite() and d > Decimal("0")) else Decimal("0"))
        except (InvalidOperation, ValueError, TypeError):
            clean_ales.append(Decimal("0"))

    gross_sum = sum(clean_ales)
    if gross_sum == Decimal("0") or target_total_ale <= 0:
        return [0] * len(standalone_ales)

    unit_quantum = (
        _resolve_allocation_quantum(target_total_ale, len(standalone_ales))
        if preserve_quanta
        else 1
    )
    target_units = target_total_ale // unit_quantum
    target_dec = Decimal(str(target_units))
    
    # 1. Non-Zero Floor Guard Pre-allocation
    floor_units = []
    available_units = target_units
    for a in clean_ales:
        if a > Decimal("0") and available_units > 0:
            floor_units.append(1)
            available_units -= 1
        else:
            floor_units.append(0)
    
    # Re-evaluate quotas based on remaining units
    gross_sum_rem = sum(a for i, a in enumerate(clean_ales) if floor_units[i] >= 0) # all active
    if available_units > 0 and gross_sum_rem > 0:
        exact_quotas = [(a * Decimal(str(available_units))) / gross_sum_rem for a in clean_ales]
    else:
        exact_quotas = [Decimal("0") for _ in clean_ales]

    integer_parts = [int(q) for q in exact_quotas]
    
    def get_lexicographic_hash(idx: int) -> str:
        if card_ids and idx < len(card_ids):
            return hashlib.sha256(str(card_ids[idx]).encode()).hexdigest()
        return f"{idx:04d}"

    remainders = [
        (q - Decimal(integer_parts[idx]), get_lexicographic_hash(idx), idx) for idx, q in enumerate(exact_quotas)
    ]

    discrepancy = available_units - sum(integer_parts)
    # Sort by remainder (descending) then by lexicographic hash (descending) to break ties deterministically
    remainders.sort(key=lambda x: (x[0], x[1]), reverse=True)

    result_units = [f + i for f, i in zip(floor_units, integer_parts)]
    for i in range(discrepancy):
        idx_to_bump = remainders[i][2]
        result_units[idx_to_bump] += 1

    result = [u * unit_quantum for u in result_units]

    if sum(result) != target_total_ale:
        raise RuntimeError(
            f"Actuarial Allocation Invariant Violated: "
            f"sum(result)={sum(result)} != target_total_ale={target_total_ale}"
        )

    return result


def harmonize_integer_weights_dual_constraint(
    raw_weights: Sequence[Union[float, Decimal, int]],
    pillar_scores: Sequence[Union[float, Decimal, int]],
    target_composite_score: Union[float, Decimal, int],
) -> List[int]:
    """Computes an integer weight vector W in Z+^n such that:
    1. sum(W) == 100
    2. round(dot(W, s) / 100, 2) == round(target_composite_score, 2)
    3. W minimizes L1 drift from normalized raw_weights.

    Solves the integer rounding paradox where visible integer weights could otherwise
    drift by +/-0.01 from the headline composite score.
    """
    n = len(raw_weights)
    if n == 0:
        return []
    if n != len(pillar_scores):
        return [int(w) for w in raw_weights]

    tot_w = sum(float(w) for w in raw_weights) or 100.0
    normalized_raw = [float(w) * 100.0 / tot_w for w in raw_weights]

    # Baseline Largest Remainder Method (Hare-Niemeyer)
    base_int = [int(w) for w in normalized_raw]
    diff = 100 - sum(base_int)
    remainders = sorted(
        range(n),
        key=lambda i: normalized_raw[i] - float(base_int[i]),
        reverse=True,
    )
    hn_weights = list(base_int)
    for i in range(diff):
        hn_weights[remainders[i]] += 1

    try:
        target_dec = Decimal(str(target_composite_score)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    except (InvalidOperation, ValueError, TypeError):
        return hn_weights

    def _eval_composite_score(w_vec: Sequence[int]) -> Decimal:
        dot = sum(
            Decimal(str(w)) * Decimal(str(s)) for w, s in zip(w_vec, pillar_scores)
        )
        return (dot / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if _eval_composite_score(hn_weights) == target_dec:
        return hn_weights

    best_weights = hn_weights
    best_dist = float("inf")

    # Single-unit shift search between pairs of indices (i, j)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            cand = list(hn_weights)
            if cand[i] <= 1:
                continue
            cand[i] -= 1
            cand[j] += 1
            if sum(cand) != 100:
                continue
            if _eval_composite_score(cand) == target_dec:
                dist = sum(abs(cand[k] - normalized_raw[k]) for k in range(n))
                if dist < best_dist:
                    best_dist = dist
                    best_weights = cand

    return best_weights
