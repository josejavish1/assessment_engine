"""Pre-flight Actuarial CFO Audit Gate enforcing mathematical and physical invariants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Sequence


class ActuarialAuditGateViolationError(ValueError):
    """Raised when risk telemetry or payload violates CFO credibility boundaries."""


@dataclass(frozen=True)
class ActuarialAuditPolicy:
    """Configurable boundaries and thresholds for the CFO Audit Gate."""

    min_hot_swap_mttr_hours: Decimal = Decimal("1.5")
    min_cold_rebuild_mttr_hours: Decimal = Decimal("4.0")
    max_ale_to_revenue_ratio: Decimal = Decimal("0.15")
    tolerance: Decimal = Decimal("5.00")
    forbidden_certainty_tokens: tuple[str, ...] = (
        "garantiza",
        "guarantees",
        "100% seguro",
        "100% certain",
        "inevitablemente causará",
        "inevitably causes",
        "revienta los compresores",
        "destruye",
    )


class CfoActuarialGate:
    """Constitutional gatekeeper verifying realism, floors, and independence of risk scenarios."""

    def __init__(self, policy: ActuarialAuditPolicy = ActuarialAuditPolicy()) -> None:
        self._policy = policy

    def verify_scenario_realism(
        self,
        mttr_hours: float | Decimal,
        hourly_rate: float | Decimal,
        parts_cost: float | Decimal,
        sle: float | Decimal,
        lef: float | Decimal,
        ale: float | Decimal,
        is_cold_rebuild: bool = False,
    ) -> None:
        """Verifies MTTR physical floor and mathematical parametric equality."""
        mttr_dec = Decimal(str(round(float(mttr_hours), 2)))
        hr_dec = Decimal(str(round(float(hourly_rate), 2)))
        parts_dec = Decimal(str(round(float(parts_cost), 2)))
        sle_dec = Decimal(str(round(float(sle), 2)))
        lef_dec = Decimal(str(round(float(lef), 4)))
        ale_dec = Decimal(str(round(float(ale), 2)))

        floor = (
            self._policy.min_cold_rebuild_mttr_hours
            if is_cold_rebuild
            else self._policy.min_hot_swap_mttr_hours
        )
        if mttr_dec < floor:
            raise ActuarialAuditGateViolationError(
                f"MTTR {mttr_dec}h is below physical industrial plant recovery floor ({floor}h)."
            )

        expected_sle = (mttr_dec * hr_dec) + parts_dec
        if abs(expected_sle - sle_dec) > self._policy.tolerance:
            raise ActuarialAuditGateViolationError(
                f"Parametric SLE mismatch: expected {expected_sle}, got {sle_dec} (diff: {abs(expected_sle - sle_dec)})."
            )

        expected_ale = sle_dec * lef_dec
        if abs(expected_ale - ale_dec) > self._policy.tolerance:
            raise ActuarialAuditGateViolationError(
                f"Parametric ALE mismatch: expected {expected_ale}, got {ale_dec} (diff: {abs(expected_ale - ale_dec)})."
            )

    def verify_probabilistic_tone(self, narrative_text: str) -> None:
        """Ensures risk descriptions adhere to probabilistic hypotheses rather than catastrophic determinism."""
        text_lower = narrative_text.lower()
        for token in self._policy.forbidden_certainty_tokens:
            if token in text_lower:
                raise ActuarialAuditGateViolationError(
                    f"Narrative contains forbidden deterministic certainty token: '{token}'."
                )

    def verify_portfolio(
        self,
        scenarios: Sequence[Mapping[str, Any]],
        annual_enterprise_revenue: Decimal | float,
    ) -> None:
        """Audits an entire risk scenario portfolio against CFO credibility boundaries."""
        revenue_dec = Decimal(str(annual_enterprise_revenue))
        if revenue_dec <= Decimal("0"):
            raise ActuarialAuditGateViolationError(
                "Annual enterprise revenue must be strictly positive."
            )

        seen_cascade_domains: set[str] = set()
        total_portfolio_ale = Decimal("0.00")

        for scenario in scenarios:
            mttr = scenario.get("mttr_hours", 2.0)
            hourly_cost = scenario.get("hourly_downtime_cost", 10000.0)
            parts = scenario.get("direct_replacement_cost", scenario.get("parts_cost", 0.0))
            sle = scenario.get("sle_amount", scenario.get("sle", 0.0))
            lef = scenario.get("aro_frequency", scenario.get("lef", scenario.get("tef", 1.0)))
            ale = scenario.get("ale_amount", scenario.get("ale", 0.0))
            is_cold = scenario.get("is_cold_rebuild", False)

            self.verify_scenario_realism(
                mttr_hours=mttr,
                hourly_rate=hourly_cost,
                parts_cost=parts,
                sle=sle,
                lef=lef,
                ale=ale,
                is_cold_rebuild=is_cold,
            )

            narrative = str(
                scenario.get("narrative_hypothesis")
                or scenario.get("finding")
                or scenario.get("business_risk")
                or ""
            )
            if narrative:
                self.verify_probabilistic_tone(narrative)

            domain_id = str(scenario.get("primary_cascade_domain_id") or scenario.get("domain_id") or "")
            if domain_id:
                if domain_id in seen_cascade_domains and not scenario.get("is_deduplicated", False):
                    raise ActuarialAuditGateViolationError(
                        f"Double-counted cascade domain '{domain_id}' detected without deduplication flag."
                    )
                seen_cascade_domains.add(domain_id)

            if not scenario.get("is_deduplicated", False):
                total_portfolio_ale += Decimal(str(round(float(ale), 2)))

        max_allowed_ale = revenue_dec * self._policy.max_ale_to_revenue_ratio
        if total_portfolio_ale > max_allowed_ale:
            raise ActuarialAuditGateViolationError(
                f"Portfolio ALE ({total_portfolio_ale}) exceeds CFO credibility ceiling "
                f"({max_allowed_ale}) for annual revenue {revenue_dec}."
            )
