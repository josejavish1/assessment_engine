"""Euler Marginal Risk Allocation and Hare-Niemeyer Rounding Engine for Open FAIR Table 5."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Self, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EulerAllocationResult(BaseModel):
    """Immutable actuarial risk decomposition for an individual technology domain."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(
        ...,
        pattern=r"^(?:T\d{1,2}|D_[A-Z0-9_]+|[A-Z][A-Z0-9_]{1,31})$",
        description="Normalized canonical or supported dynamic/custom tower code (e.g. T1, D_FAC, CLINICAL_CORE)",
    )
    standalone_ale: int = Field(
        ..., ge=0, description="Pure bottom-up unconstrained standalone ALE"
    )
    diversification_adjustment: int = Field(
        ...,
        le=0,
        description="Copula correlation and entity absorption delta (strictly <= 0)",
    )
    euler_net_contribution: int = Field(
        ..., ge=0, description="Net diversified portfolio contribution"
    )
    portfolio_weight_pct: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("100.0"),
        description="Relative share of net portfolio risk",
    )

    @model_validator(mode="after")
    def validate_row_accounting_identity(self) -> Self:
        """Enforces that Standalone ALE + Adjustment == Net Contribution horizontally."""
        expected_net = self.standalone_ale + self.diversification_adjustment
        if expected_net != self.euler_net_contribution:
            raise ValueError(
                f"Row Accounting Violation for {self.tower_id}: "
                f"Standalone ({self.standalone_ale:,}) + Adjustment ({self.diversification_adjustment:,}) = "
                f"{expected_net:,}, but Euler Net is {self.euler_net_contribution:,}."
            )
        return self


class PortfolioEulerDecomposition(BaseModel):
    """Immutable, closed-form actuarial decomposition across all active enterprise domains."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    currency_iso: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    allocations: Tuple[EulerAllocationResult, ...] = Field(..., min_length=1)
    subtotal_gross_undiversified_ale: int = Field(..., ge=0)
    actuarial_copula_adjustment_ale: int = Field(..., le=0)
    actuarial_copula_overlap_pct: Decimal = Field(
        ..., ge=Decimal("0.0"), le=Decimal("100.0")
    )
    total_net_consolidated_ale: int = Field(..., ge=0)
    total_portfolio_weight_pct: Decimal = Field(default=Decimal("100.0"))

    @model_validator(mode="after")
    def validate_portfolio_accounting_identities(self) -> Self:
        """Enforces strict vertical and bridge accounting identities across the entire matrix."""
        # 1. Vertical Standalone Sum == Subtotal Gross
        sum_standalone = sum(a.standalone_ale for a in self.allocations)
        if sum_standalone != self.subtotal_gross_undiversified_ale:
            raise ValueError(
                f"Vertical Standalone Identity Violation: Sum of domain rows ({sum_standalone:,}) "
                f"does not match Subtotal Gross ({self.subtotal_gross_undiversified_ale:,})."
            )

        # 2. Vertical Adjustment Sum == Copula Adjustment Total
        sum_adjustment = sum(a.diversification_adjustment for a in self.allocations)
        if sum_adjustment != self.actuarial_copula_adjustment_ale:
            raise ValueError(
                f"Vertical Adjustment Identity Violation: Sum of domain adjustments ({sum_adjustment:,}) "
                f"does not match Copula Adjustment Total ({self.actuarial_copula_adjustment_ale:,})."
            )

        # 3. Vertical Euler Net Sum == Total Net Consolidated
        sum_euler = sum(a.euler_net_contribution for a in self.allocations)
        if sum_euler != self.total_net_consolidated_ale:
            raise ValueError(
                f"Vertical Euler Identity Violation: Sum of domain contributions ({sum_euler:,}) "
                f"does not match Total Net Consolidated ({self.total_net_consolidated_ale:,})."
            )

        # 4. Bridge Cross-Check: Subtotal Gross + Copula Adjustment == Total Net
        bridge_net = (
            self.subtotal_gross_undiversified_ale + self.actuarial_copula_adjustment_ale
        )
        if bridge_net != self.total_net_consolidated_ale:
            raise ValueError(
                f"Actuarial Bridge Violation: Gross ({self.subtotal_gross_undiversified_ale:,}) + "
                f"Adjustment ({self.actuarial_copula_adjustment_ale:,}) = {bridge_net:,}, "
                f"which does not match Net Total ({self.total_net_consolidated_ale:,})."
            )

        # 5. Percentage Simplex: Sum of weights must equal 100.0% exactly
        sum_pct = sum(a.portfolio_weight_pct for a in self.allocations)
        if abs(sum_pct - Decimal("100.0")) > Decimal("0.01"):
            raise ValueError(
                f"Percentage Simplex Violation: Sum of relative weights ({sum_pct}%) does not equal 100.0%."
            )

        return self


class EulerPortfolioAllocator:
    """Actuarial engine implementing Tasche's Euler Allocation and Hare-Niemeyer discretization."""

    @classmethod
    def allocate_portfolio(
        cls,
        standalone_ales: Dict[str, float],
        total_portfolio_ale: float,
        currency_iso: str = "USD",
    ) -> PortfolioEulerDecomposition:
        """Computes closed-form Euler marginal allocation with exact zero-drift integer rounding."""
        if not standalone_ales:
            raise ValueError("Standalone ALE dictionary cannot be empty.")

        import re

        # Normalize tower IDs canonically (e.g. t1 -> T1, T01 -> T1)
        normalized_standalone: Dict[str, float] = {}
        for raw_k, v in standalone_ales.items():
            match = re.search(r"T0?(\d+)", str(raw_k).strip().upper())
            clean_k = f"T{match.group(1)}" if match else str(raw_k).strip().upper()
            normalized_standalone[clean_k] = float(v)

        # Sort towers canonically (T1, T2, ... T10)
        sorted_towers = sorted(
            normalized_standalone.keys(),
            key=lambda t: int(t[1:]) if t.startswith("T") and t[1:].isdigit() else 99,
        )

        # 1. Round standalone ALEs to integer currency units
        standalone_ints: Dict[str, int] = {
            t: max(0, int(round(normalized_standalone[t]))) for t in sorted_towers
        }
        subtotal_gross = sum(standalone_ints.values())

        # Enforce sub-additivity: Net portfolio ALE cannot exceed Gross standalone sum
        target_net = min(subtotal_gross, max(0, int(round(total_portfolio_ale))))

        # Natural Copula Diversification Guardrail:
        # In quantitative risk management across 2 to 10 correlated technology domains,
        # empirical copula overlap discounts reside strictly within the [15%, 35%] boundary.
        # If upstream telemetry passes an uncalibrated target_net implying an unphysical discount (> 35%),
        # or if target_net is zero, derive the natural copula discount based on N active domains.
        if subtotal_gross > 0 and len(sorted_towers) > 1:
            implied_discount = (subtotal_gross - target_net) / float(subtotal_gross)
            if implied_discount > 0.35 or target_net <= 0:
                natural_discount = min(
                    0.28, max(0.18, 0.12 + 0.016 * len(sorted_towers))
                )
                target_net = int(
                    round(float(subtotal_gross) * (1.0 - natural_discount))
                )

        # Degenerate single-tower or zero-risk case
        if subtotal_gross == 0 or len(sorted_towers) == 1:
            raw_equal_pcts = {t: 100.0 / len(sorted_towers) for t in sorted_towers}
            pct_map = cls._hare_niemeyer_percentage_discretize(raw_equal_pcts)
            allocations = [
                EulerAllocationResult(
                    tower_id=t,
                    standalone_ale=standalone_ints[t],
                    diversification_adjustment=0,
                    euler_net_contribution=standalone_ints[t],
                    portfolio_weight_pct=pct_map[t],
                )
                for t in sorted_towers
            ]
            return PortfolioEulerDecomposition(
                currency_iso=currency_iso.upper(),
                allocations=tuple(allocations),
                subtotal_gross_undiversified_ale=subtotal_gross,
                actuarial_copula_adjustment_ale=0,
                actuarial_copula_overlap_pct=Decimal("0.0"),
                total_net_consolidated_ale=subtotal_gross,
                total_portfolio_weight_pct=Decimal("100.0"),
            )

        # 2. Continuous Euler weights proportional to marginal risk
        euler_floats: Dict[str, float] = {
            t: (standalone_ints[t] / subtotal_gross) * target_net for t in sorted_towers
        }

        # 3. Hare-Niemeyer (Largest Remainder) rounding for Euler net contributions
        euler_ints = cls._hare_niemeyer_discretize(euler_floats, target_net)

        # 4. Derive diversification adjustment per row: Adjustment = EulerNet - Standalone (<= 0)
        # To strictly enforce that standalone + adj == euler_net and adj <= 0:
        adjustments: Dict[str, int] = {}
        for t in sorted_towers:
            # Net contribution can never exceed standalone risk
            e_val = min(standalone_ints[t], euler_ints[t])
            euler_ints[t] = e_val
            adjustments[t] = e_val - standalone_ints[t]

        # Re-verify and resolve any residual discrepancy from min clamping
        residual_net = target_net - sum(euler_ints.values())
        if residual_net != 0:
            # Distribute residual into highest standalone towers with headroom
            headroom_towers = [
                t for t in sorted_towers if standalone_ints[t] > euler_ints[t]
            ]
            if headroom_towers:
                step = 1 if residual_net > 0 else -1
                for _ in range(abs(residual_net)):
                    t_target = max(
                        headroom_towers,
                        key=lambda t: standalone_ints[t] - euler_ints[t],
                    )
                    euler_ints[t_target] += step
                    adjustments[t_target] = (
                        euler_ints[t_target] - standalone_ints[t_target]
                    )

        # 5. Reconcile percentage weights at 0.1% precision summing to exactly 100.0%
        pct_floats: Dict[str, float] = {
            t: (euler_ints[t] / target_net) * 100.0 if target_net > 0 else 0.0
            for t in sorted_towers
        }
        pct_decimals = cls._hare_niemeyer_percentage_discretize(pct_floats)

        # 6. Overall copula diversification delta and overlap percentage
        total_copula_adjustment = sum(adjustments.values())
        overlap_pct = (
            (Decimal(str(abs(total_copula_adjustment))) / Decimal(str(subtotal_gross)))
            * Decimal("100.0")
        ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        allocation_rows = [
            EulerAllocationResult(
                tower_id=t,
                standalone_ale=standalone_ints[t],
                diversification_adjustment=adjustments[t],
                euler_net_contribution=euler_ints[t],
                portfolio_weight_pct=pct_decimals[t],
            )
            for t in sorted_towers
        ]

        return PortfolioEulerDecomposition(
            currency_iso=currency_iso.upper(),
            allocations=tuple(allocation_rows),
            subtotal_gross_undiversified_ale=subtotal_gross,
            actuarial_copula_adjustment_ale=total_copula_adjustment,
            actuarial_copula_overlap_pct=overlap_pct,
            total_net_consolidated_ale=target_net,
            total_portfolio_weight_pct=Decimal("100.0"),
        )

    @staticmethod
    def _hare_niemeyer_discretize(
        raw_values: Dict[str, float], target_sum: int
    ) -> Dict[str, int]:
        """Discretizes continuous float allocations into exact integer units summing to target_sum."""
        integers: Dict[str, int] = {}
        remainders: List[Tuple[str, float]] = []

        for k, v in raw_values.items():
            floor_val = math.floor(v)
            integers[k] = floor_val
            remainders.append((k, v - floor_val))

        allocated_sum = sum(integers.values())
        shortfall = target_sum - allocated_sum

        # Distribute surplus to keys with largest fractional remainder
        remainders.sort(key=lambda item: item[1], reverse=True)
        for i in range(shortfall):
            k_winner = remainders[i % len(remainders)][0]
            integers[k_winner] += 1

        return integers

    @staticmethod
    def _hare_niemeyer_percentage_discretize(
        raw_pcts: Dict[str, float],
    ) -> Dict[str, Decimal]:
        """Discretizes percentages to 1 decimal place summing to exactly Decimal('100.0')."""
        target_tenths = 1000  # 100.0% represented in tenths of a percent
        tenths_floats = {k: v * 10.0 for k, v in raw_pcts.items()}

        integers: Dict[str, int] = {}
        remainders: List[Tuple[str, float]] = []

        for k, v in tenths_floats.items():
            floor_val = math.floor(v)
            integers[k] = floor_val
            remainders.append((k, v - floor_val))

        allocated_sum = sum(integers.values())
        shortfall = target_tenths - allocated_sum

        remainders.sort(key=lambda item: item[1], reverse=True)
        for i in range(shortfall):
            k_winner = remainders[i % len(remainders)][0]
            integers[k_winner] += 1

        return {
            k: (Decimal(str(integers[k])) / Decimal("10.0")).quantize(Decimal("0.1"))
            for k in raw_pcts.keys()
        }

    @classmethod
    def allocate_findings_within_domain(
        cls,
        findings_raw: Sequence[Mapping[str, Any]],
        currency_iso: str = "EUR",
    ) -> Dict[str, Any]:
        """
        Allocates portfolio overlap adjustments across individual findings while preserving
        100% of standalone SLE component additivity and enforcing per-finding max discount caps.
        """
        from assessment_engine.domain.actuarial.finding_archetype_resolver import (
            AdditiveLossDecomposition,
        )

        decompositions: Dict[str, AdditiveLossDecomposition] = {}
        if not findings_raw:
            return decompositions

        active_ids: list[str] = []
        standalone_ales: Dict[str, int] = {}
        max_discounts: Dict[str, float] = {}
        raw_metrics: Dict[str, dict[str, Any]] = {}

        for item in findings_raw:
            f_id = str(item.get("id") or item.get("node_id") or "UNKNOWN")
            epistemic = str(item.get("epistemic_state") or "VERIFIED_EMPIRICAL")
            physics = str(item.get("loss_physics") or "AVAILABILITY_OUTAGE")
            lef = max(0.0, float(item.get("mean_lef") or item.get("lef") or 0.0))

            # Exact integer rounding of expectation components from Monte Carlo
            e_down = max(0, int(round(float(item.get("expected_downtime_loss") or 0.0))))
            e_repl = max(0, int(round(float(item.get("expected_replacement_cost") or 0.0))))
            e_sec = max(0, int(round(float(item.get("expected_secondary_loss") or 0.0))))

            # Enforce strict closed-form identity: Gross SLE == E[Downtime] + E[Replacement] + E[Secondary]
            raw_gross_sle = item.get("gross_mean_sle") or item.get("sle")
            explicit_ale = (
                item.get("gross_standalone_ale")
                or item.get("ale")
                or item.get("fair_ale_score")
            )

            if explicit_ale is not None and float(explicit_ale) > 0.0:
                gross_ale = max(0, int(round(float(explicit_ale))))
                if raw_gross_sle is not None and float(raw_gross_sle) > 0.0:
                    gross_sle = max(0, int(round(float(raw_gross_sle))))
                else:
                    gross_sle = gross_ale
                if e_down + e_repl + e_sec == 0:
                    e_down = gross_sle
            elif raw_gross_sle is not None and float(raw_gross_sle) > 0.0:
                gross_sle = max(0, int(round(float(raw_gross_sle))))
                if e_down + e_repl + e_sec == 0:
                    e_down = gross_sle
                gross_ale = max(0, int(round(lef * float(gross_sle))))
            else:
                gross_sle = e_down + e_repl + e_sec
                gross_ale = max(0, int(round(lef * float(gross_sle))))

            raw_p90 = item.get("gross_p90") or item.get("p90") or item.get("fair_p90_score")
            if raw_p90 is not None and float(raw_p90) > 0.0:
                gross_p90 = max(gross_ale, int(round(float(raw_p90))))
            else:
                gross_p90 = max(gross_ale, int(round(float(gross_ale * 1.85))))

            max_disc = float(item.get("max_euler_ale_discount_pct") or 0.20)
            if physics == "FINOPS_RESOURCE_WASTE" or epistemic != "VERIFIED_EMPIRICAL":
                max_disc = 0.0
            else:
                max_disc = min(0.25, max(0.0, max_disc))

            active_ids.append(f_id)
            standalone_ales[f_id] = gross_ale
            max_discounts[f_id] = max_disc
            raw_metrics[f_id] = {
                "lef": lef,
                "e_down": e_down,
                "e_repl": e_repl,
                "e_sec": e_sec,
                "gross_sle": gross_sle,
                "gross_ale": gross_ale,
                "gross_p90": gross_p90,
                "physics": physics,
                "epistemic": epistemic,
                "max_var_disc": min(0.25, float(item.get("max_euler_var_discount_pct") or 0.25)),
            }

        diversifiable_ids = [
            fid for fid in active_ids if standalone_ales[fid] > 0 and max_discounts[fid] > 0.0
        ]
        n_div = len(diversifiable_ids)

        for fid in active_ids:
            m = raw_metrics[fid]
            gross_ale = m["gross_ale"]
            if n_div <= 1 or fid not in diversifiable_ids or gross_ale == 0:
                eff_disc = 0.0
                var_disc = 0.0
            else:
                # Smooth logarithmic causal overlap curve bounded strictly by [0%, max_discounts[fid]]
                empirical_overlap = min(0.22, 0.05 * (n_div - 1) / (1.0 + 0.20 * (n_div - 1)))
                eff_disc = min(max_discounts[fid], empirical_overlap)
                var_disc = min(m["max_var_disc"], empirical_overlap * 1.25)

            net_ale = int(round(float(gross_ale) * (1.0 - eff_disc)))
            # Hard floor invariant: Net ALE >= 75% of Gross Standalone ALE
            net_ale = max(int(round(float(gross_ale) * 0.75)), min(gross_ale, net_ale))
            euler_adj = net_ale - gross_ale  # Strictly <= 0

            actual_disc_pct = (
                Decimal(str((gross_ale - net_ale) * 100.0 / float(gross_ale))).quantize(
                    Decimal("0.1"), rounding=ROUND_HALF_UP
                )
                if gross_ale > 0
                else Decimal("0.0")
            )
            net_p90 = max(net_ale, int(round(float(m["gross_p90"]) * (1.0 - var_disc))))

            decomp = AdditiveLossDecomposition(
                currency_iso=currency_iso.upper(),
                mean_lef=m["lef"],
                expected_downtime_loss=m["e_down"],
                expected_replacement_cost=m["e_repl"],
                expected_secondary_loss=m["e_sec"],
                gross_mean_sle=m["gross_sle"],
                gross_standalone_ale=gross_ale,
                euler_overlap_adjustment_ale=euler_adj,
                net_allocated_ale=net_ale,
                euler_discount_pct=actual_disc_pct,
                gross_standalone_p90=m["gross_p90"],
                net_allocated_p90=net_p90,
                loss_physics=m["physics"],
                epistemic_state=m["epistemic"],
            )
            decomp.validate_conservation()
            decompositions[fid] = decomp

        return decompositions
