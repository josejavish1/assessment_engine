"""Actuarial Significant Figures Rounding and Discrete Integer Allocation Engine.

Implements the Argon Actuarial Rounding Policy:
1. Pure Decimal arithmetic (zero float floating-point inaccuracies).
2. Dynamic step quanta scaling by order of magnitude.
3. Closed-form Hare-Niemeyer (Largest Remainder) discrete integer allocation
   guaranteeing that individual card ALEs sum exactly to the parent Outage ALE.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
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
    if val <= Decimal("0"):
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


def round_to_actuarial_significance(raw_amount: Union[int, str, Decimal, float]) -> int:
    """Rounds a raw monetary amount to its actuarially significant quantum.

    Eliminates false precision (cents, single euros, and spurious trailing digits).
    Uses ROUND_HALF_UP ties breaking and ensures non-negative return value.
    """
    if raw_amount is None:
        return 0
    val = max(Decimal("0"), Decimal(str(raw_amount)))
    if val == Decimal("0"):
        return 0

    quantum = compute_step_quantum(val)
    scaled = (val / quantum).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    result = int(scaled * quantum)
    return max(int(quantum), result)


def allocate_subadditive_ale_to_cards(
    target_total_ale: int,
    standalone_ales: Sequence[Union[int, float, Decimal]],
) -> List[int]:
    """Apportions a portfolio-adjusted sub-additive Outage ALE across individual risk cards.

    Uses the closed-form Hare-Niemeyer (Largest Remainder) discrete integer algorithm.
    Guarantees:
    1. sum(allocated_ales) == target_total_ale EXACTLY (to the single integer).
    2. Proportional preservation of each card's relative actuarial weight.
    3. Monotonic non-negative integer results.
    """
    if not standalone_ales:
        return []

    clean_ales = [max(Decimal("0"), Decimal(str(a))) for a in standalone_ales]
    gross_sum = sum(clean_ales)

    if gross_sum == Decimal("0") or target_total_ale <= 0:
        return [0] * len(standalone_ales)

    target_dec = Decimal(str(target_total_ale))

    # Exact quota calculation
    exact_quotas = [(a * target_dec) / gross_sum for a in clean_ales]
    integer_parts = [int(q) for q in exact_quotas]
    remainders = [(q - Decimal(integer_parts[idx]), idx) for idx, q in enumerate(exact_quotas)]

    # Discrepancy to distribute
    discrepancy = target_total_ale - sum(integer_parts)

    # Sort descending by remainder, breaking ties by index
    remainders.sort(key=lambda x: (x[0], -x[1]), reverse=True)

    result = list(integer_parts)
    for i in range(discrepancy):
        idx_to_bump = remainders[i][1]
        result[idx_to_bump] += 1

    # Invariant assertion: exact sum
    if sum(result) != target_total_ale:
        raise RuntimeError(
            f"Actuarial Allocation Invariant Violated: "
            f"sum(result)={sum(result)} != target_total_ale={target_total_ale}"
        )

    return result
