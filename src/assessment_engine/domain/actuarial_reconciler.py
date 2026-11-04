"""Closed-form Actuarial and Financial Reconciliation Engine (RFC 065).

Provides deterministic mathematical reconciliation for enterprise risk portfolios,
guaranteeing zero split-brain between corporate ALE, domain allocations, and
scenario cards via the Hamilton Largest Remainder Method and exact quantization.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, localcontext
from typing import Any, Dict, List, Sequence, Tuple


class ActuarialReconciliationError(ValueError):
    """Raised when actuarial figures fail closed-form reconciliation."""


class ActuarialReconciler:
    """Deterministic closed-form financial and maturity reconciler."""

    @staticmethod
    def reconcile_domain_allocations(
        target_corporate_ale: int,
        domain_raw_exposures: Sequence[Tuple[str, Decimal]],
    ) -> Dict[str, int]:
        """Allocates corporate ALE across domains using the Hamilton Largest Remainder Method.

        Guarantees that sum(allocated.values()) == target_corporate_ale to the exact integer,
        eliminating 1-euro or 1-dollar rounding discrepancy anomalies across any currency.
        """
        if not domain_raw_exposures:
            raise ActuarialReconciliationError(
                "Domain raw exposures sequence cannot be empty."
            )

        if target_corporate_ale < 0:
            raise ActuarialReconciliationError("Target corporate ALE cannot be negative.")

        domain_ids = [d_id for d_id, _ in domain_raw_exposures]
        if len(domain_ids) != len(set(domain_ids)):
            raise ActuarialReconciliationError("Duplicate domain IDs are strictly prohibited.")

        if any(not raw.is_finite() or raw < Decimal("0") for _, raw in domain_raw_exposures):
            raise ActuarialReconciliationError(
                "Individual domain raw exposure must be a finite non-negative Decimal."
            )

        if target_corporate_ale == 0:
            return {domain_id: 0 for domain_id in domain_ids}

        total_raw = sum((raw for _, raw in domain_raw_exposures), Decimal("0"))
        if total_raw <= Decimal("0"):
            raise ActuarialReconciliationError(
                "Total raw domain exposure must be strictly positive for non-zero target."
            )

        with localcontext() as ctx:
            ctx.prec = 50
            target_dec = Decimal(str(target_corporate_ale))
            quotas: List[Tuple[str, int, Decimal]] = []
            for domain_id, raw_val in domain_raw_exposures:
                exact_quota = (target_dec * raw_val) / total_raw
                floor_val = int(exact_quota.to_integral_value(rounding=ROUND_FLOOR))
                remainder = exact_quota - Decimal(str(floor_val))
                quotas.append((domain_id, floor_val, remainder))

            current_sum = sum(item[1] for item in quotas)
            residual = target_corporate_ale - current_sum

            # Sort by descending remainder, then ascending domain_id for deterministic tie-breaking
            sorted_for_remainder = sorted(quotas, key=lambda x: (-x[2], x[0]))
            allocated: Dict[str, int] = {domain_id: floor_val for domain_id, floor_val, _ in quotas}

            for i in range(residual):
                win_domain_id = sorted_for_remainder[i][0]
                allocated[win_domain_id] += 1

            if sum(allocated.values()) != target_corporate_ale:
                raise ActuarialReconciliationError(
                    f"Largest remainder allocation invariant violated: {sum(allocated.values())} != {target_corporate_ale}"
                )

            return allocated

    @staticmethod
    def reconcile_scenario_card(sle: int, lef: Decimal) -> Dict[str, Any]:
        """Reconciles single loss expectancy and loss event frequency into integer ALE.

        Quantizes LEF to 2 decimal places and rounds ALE to the nearest integer:
        ALE = round_half_up(SLE * round(LEF, 2)).
        """
        if sle < 0:
            raise ActuarialReconciliationError("SLE cannot be negative.")
        if not lef.is_finite() or lef < Decimal("0"):
            raise ActuarialReconciliationError("LEF must be a finite non-negative Decimal.")

        quantized_lef = lef.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        reconciled_ale = int(
            (Decimal(str(sle)) * quantized_lef).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        )
        return {
            "sle": sle,
            "lef": quantized_lef,
            "ale_p50": reconciled_ale,
        }

    @staticmethod
    def reconcile_cmmi_scores(
        scores: Sequence[Decimal],
        weights: Sequence[Decimal] | None = None,
    ) -> Tuple[Decimal, Decimal]:
        """Calculates both simple arithmetic mean and weighted corporate mean.

        Returns: (simple_mean, weighted_mean) quantized to 2 decimal places.
        """
        if not scores:
            return Decimal("0.00"), Decimal("0.00")

        if any(not s.is_finite() or s < Decimal("0") or s > Decimal("5.00") for s in scores):
            raise ActuarialReconciliationError(
                "CMMI scores must be finite Decimals within range [0.00, 5.00]."
            )

        n_scores = Decimal(str(len(scores)))
        sum_scores = sum(scores, Decimal("0"))
        simple_mean = (sum_scores / n_scores).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if weights is not None:
            if len(weights) != len(scores):
                raise ActuarialReconciliationError(
                    f"Scores length ({len(scores)}) does not match weights length ({len(weights)})."
                )
            if any(not w.is_finite() or w < Decimal("0") for w in weights):
                raise ActuarialReconciliationError(
                    "Weights must be finite non-negative Decimals."
                )

            total_weight = sum(weights, Decimal("0"))
            if total_weight <= Decimal("0"):
                raise ActuarialReconciliationError("Total weight must be strictly positive.")

            weighted_sum = sum(s * w for s, w in zip(scores, weights))
            weighted_mean = (weighted_sum / total_weight).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            return simple_mean, weighted_mean

        return simple_mean, simple_mean
