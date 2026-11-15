"""Immutable Pydantic V2 Domain Schemas for Chapter 4 Executive Due Diligence.

Enforces the Monistic Actuarial Contract (Single Source of Truth):
Sections 4.1, 4.2, and 4.3 are strictly read-only projections of Chapter4SynthesisPayload.
All models are frozen, extra-forbidden, and validated with strict mathematical identities.
"""

from __future__ import annotations

from typing import Any, Self, Tuple
from pydantic import BaseModel, ConfigDict, Field, model_validator


class MonetaryInterval(BaseModel):
    """Calibrated economic interval [lower_bound, upper_bound].

    Represents conservative parametric boundaries without false precision.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    lower_bound: int = Field(..., ge=0, description="Lower conservative bound")
    upper_bound: int = Field(..., ge=0, description="Upper conservative bound")
    currency_iso: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    @property
    def midpoint(self) -> int:
        return (self.lower_bound + self.upper_bound) // 2

    def __add__(self, other: Any) -> MonetaryInterval:
        if not isinstance(other, MonetaryInterval):
            return NotImplemented
        if self.currency_iso != other.currency_iso:
            raise ValueError(
                f"Currency mismatch: {self.currency_iso} != {other.currency_iso}"
            )
        return MonetaryInterval(
            lower_bound=self.lower_bound + other.lower_bound,
            upper_bound=self.upper_bound + other.upper_bound,
            currency_iso=self.currency_iso,
        )

    @model_validator(mode="after")
    def validate_interval_order(self) -> Self:
        if self.lower_bound > self.upper_bound:
            raise ValueError(
                f"Invalid interval: lower_bound ({self.lower_bound:,}) "
                f"> upper_bound ({self.upper_bound:,})"
            )
        return self


class ThreeYearCompoundedTCO(BaseModel):
    """36-Month compounded Total Cost of Inaction (COI) projection."""

    model_config = ConfigDict(frozen=True, extra="forbid", populate_by_name=True)

    lower_bound: int = Field(..., ge=0, alias="lower_bound_eur")
    upper_bound: int = Field(..., ge=0, alias="upper_bound_eur")
    midpoint: int = Field(..., ge=0, alias="midpoint_eur")
    compounding_rate_annual: float = Field(default=0.0, ge=0.0, le=1.0)
    currency_iso: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    @property
    def lower_bound_eur(self) -> int:
        """Backward-compatible property alias."""
        return self.lower_bound

    @property
    def upper_bound_eur(self) -> int:
        """Backward-compatible property alias."""
        return self.upper_bound

    @property
    def midpoint_eur(self) -> int:
        """Backward-compatible property alias."""
        return self.midpoint

    @model_validator(mode="after")
    def validate_tco_bounds(self) -> Self:
        if self.lower_bound > self.upper_bound:
            raise ValueError(
                f"Invalid 3Y TCO bounds: lower_bound ({self.lower_bound:,}) "
                f"> upper_bound ({self.upper_bound:,})"
            )
        return self


class ChronicOperationalDragBreakdown(BaseModel):
    """Deterministic annual operational drag (COD) for Section 4.1.

    Combines engineering toil and contractual/licensing escalation.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    annual_engineering_toil_hours: int = Field(..., ge=0)
    engineering_toil_cost_interval: MonetaryInterval
    contractual_and_licensing_escalation_interval: MonetaryInterval
    total_chronic_drag_interval: MonetaryInterval

    @model_validator(mode="after")
    def verify_cod_reconciliation(self) -> Self:
        expected = (
            self.engineering_toil_cost_interval
            + self.contractual_and_licensing_escalation_interval
        )
        if (
            self.total_chronic_drag_interval.currency_iso != expected.currency_iso
            or self.total_chronic_drag_interval.lower_bound != expected.lower_bound
            or self.total_chronic_drag_interval.upper_bound != expected.upper_bound
        ):
            raise ValueError(
                f"COD Reconciliation Invariant Violated: total_chronic_drag_interval "
                f"([{self.total_chronic_drag_interval.lower_bound:,}, "
                f"{self.total_chronic_drag_interval.upper_bound:,}] {self.total_chronic_drag_interval.currency_iso}) "
                f"must equal exact sum of toil + escalation "
                f"([{expected.lower_bound:,}, {expected.upper_bound:,}] {expected.currency_iso})."
            )
        return self


class ProbabilisticOutageALEBreakdown(BaseModel):
    """Stochastic Availability & Disruption Loss Exposure (Open FAIR ALE) for Section 4.1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gross_standalone_ale_sum: int = Field(..., ge=0)
    portfolio_subadditivity_factor: float = Field(..., ge=0.50, le=1.0)
    annual_outage_ale_interval: MonetaryInterval
    worst_case_single_outage_event: MonetaryInterval

    @model_validator(mode="after")
    def verify_outage_currency_consistency(self) -> Self:
        if (
            self.annual_outage_ale_interval.currency_iso
            != self.worst_case_single_outage_event.currency_iso
        ):
            raise ValueError(
                f"Outage currency mismatch: {self.annual_outage_ale_interval.currency_iso} "
                f"!= {self.worst_case_single_outage_event.currency_iso}"
            )
        return self


class CostOfInactionTotal(BaseModel):
    """Consolidated annual Cost of Inaction (COI = COD + Outage ALE)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lever_1_toil_share_pct: float = Field(..., ge=0.0, le=100.0)
    lever_2_outage_ale_share_pct: float = Field(..., ge=0.0, le=100.0)
    lever_3_contractual_share_pct: float = Field(..., ge=0.0, le=100.0)
    annual_total_coi_interval: MonetaryInterval

    @model_validator(mode="after")
    def verify_share_percentages_sum_to_100(self) -> Self:
        total_pct = (
            self.lever_1_toil_share_pct
            + self.lever_2_outage_ale_share_pct
            + self.lever_3_contractual_share_pct
        )
        if abs(total_pct - 100.0) > 0.60:
            raise ValueError(
                f"Lever share percentages must sum to 100%, got {total_pct:.2f}%."
            )
        return self


class HeatmapCoordinate(BaseModel):
    """Cell mapping on the 5x5 Actuarial Risk Matrix."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    likelihood_index: int = Field(..., ge=1, le=5)
    impact_index: int = Field(..., ge=1, le=5)
    truncated_title: str = Field(..., min_length=3, max_length=42)


class TechnicalRiskScenario(BaseModel):
    """Quantified risk scenario card for Section 4.2 and Section 4.3."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    risk_id: str = Field(..., pattern=r"^[A-Z0-9_\-\.]+$")
    title: str = Field(..., min_length=5, max_length=120)
    custody_role: str = Field(
        default="PRIMARY_CUSTODIAN",
        pattern=r"^(PRIMARY_CUSTODIAN|TANGENTIAL_CONTRIBUTOR)$",
        description="'PRIMARY_CUSTODIAN' or 'TANGENTIAL_CONTRIBUTOR'",
    )
    threat_event_frequency_annual: float = Field(..., ge=0.01, le=100.0)
    vulnerability_ratio: float = Field(..., ge=0.0, le=1.0)
    mttr_recovery_hours: float = Field(..., ge=0.1, le=720.0)
    calibrated_annual_ale: MonetaryInterval
    heatmap_coordinate: HeatmapCoordinate
    physical_evidence: str = Field(..., min_length=20)
    root_cause_mechanism: str = Field(..., min_length=20)
    business_impact_narrative: str = Field(..., min_length=20)
    required_mitigation: str = Field(..., min_length=20)
    is_full_card_rendered: bool = Field(
        default=True,
        description="True for Tier 1 and Tier 2 strategic risks; False for residual table rows.",
    )


class Chapter4SynthesisPayload(BaseModel):
    """THE MONISTIC ACTUARIAL CONTRACT.

    Sections 4.1, 4.2, and 4.3 are strictly projections of this single immutable object.
    Zero calculation drift and zero presentation math mutation permitted.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str = Field(..., min_length=2, max_length=16)
    tower_name: str = Field(..., min_length=3)
    enterprise_id: str = Field(..., min_length=2)
    evaluated_cmmi_maturity: float = Field(..., ge=1.0, le=5.0)
    currency_iso: str = Field(default="EUR", pattern=r"^[A-Z]{3}$")

    # Section 4.1: Cost of Inaction
    chronic_operational_drag: ChronicOperationalDragBreakdown
    probabilistic_outage_ale: ProbabilisticOutageALEBreakdown
    total_annual_coi: CostOfInactionTotal
    three_year_compounded_tco: ThreeYearCompoundedTCO

    # Section 4.2 & Section 4.3: Strategic Risk Scenarios
    technical_risk_cards: Tuple[TechnicalRiskScenario, ...] = Field(..., min_length=1)

    @model_validator(mode="after")
    def verify_chapter_actuarial_monism(self) -> Self:
        """Enforces ironclad horizontal, vertical, and currency accounting identities across Chapter 4."""
        # Invariant 0: Global Currency Monism
        intervals_to_check = [
            self.chronic_operational_drag.total_chronic_drag_interval.currency_iso,
            self.probabilistic_outage_ale.annual_outage_ale_interval.currency_iso,
            self.total_annual_coi.annual_total_coi_interval.currency_iso,
            self.three_year_compounded_tco.currency_iso,
            *(c.calibrated_annual_ale.currency_iso for c in self.technical_risk_cards),
        ]
        for curr in intervals_to_check:
            if curr != self.currency_iso:
                raise ValueError(
                    f"Currency Monism Violated: root currency is {self.currency_iso}, "
                    f"but nested component uses {curr}."
                )

        # Invariant 1: Total Annual COI == COD + Outage ALE
        expected_coi = (
            self.chronic_operational_drag.total_chronic_drag_interval
            + self.probabilistic_outage_ale.annual_outage_ale_interval
        )
        actual_coi = self.total_annual_coi.annual_total_coi_interval

        if (
            actual_coi.lower_bound != expected_coi.lower_bound
            or actual_coi.upper_bound != expected_coi.upper_bound
        ):
            raise ValueError(
                f"Split-Brain Invariant 1 Violated: Total Annual COI "
                f"([{actual_coi.lower_bound:,}, {actual_coi.upper_bound:,}]) "
                f"!= COD + Outage ALE ([{expected_coi.lower_bound:,}, {expected_coi.upper_bound:,}])."
            )

        # Invariant 2: Sum of primary card ALEs must reconcile with Lever 2 (Outage ALE)
        primary_cards = [
            c for c in self.technical_risk_cards if c.custody_role == "PRIMARY_CUSTODIAN"
        ]
        outage_ale = self.probabilistic_outage_ale.annual_outage_ale_interval

        if not primary_cards and outage_ale.upper_bound > 0:
            raise ValueError(
                "Split-Brain Invariant 2 Violated: Outage ALE > 0 but zero PRIMARY_CUSTODIAN risk cards present."
            )

        if primary_cards:
            cards_low_sum = sum(c.calibrated_annual_ale.lower_bound for c in primary_cards)
            cards_high_sum = sum(c.calibrated_annual_ale.upper_bound for c in primary_cards)

            if (
                cards_low_sum != outage_ale.lower_bound
                or cards_high_sum != outage_ale.upper_bound
            ):
                raise ValueError(
                    f"Split-Brain Invariant 2 Violated: Primary Risk Cards ALE sum "
                    f"([{cards_low_sum:,}, {cards_high_sum:,}]) != Lever 2 Outage ALE "
                    f"([{outage_ale.lower_bound:,}, {outage_ale.upper_bound:,}])."
                )

        return self
