"""Actuarial calculation engine for Open FAIR quantitative loss modeling."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict

from assessment_engine.domain.schemas.risk_ontology import FairActuarialInput


@dataclass(frozen=True)
class ComputedFairMetrics:
    """Immutable actuarial metrics derived from Open FAIR input distributions."""

    effective_sle: Decimal
    annualized_loss_expectancy: Decimal
    loss_event_frequency: float
    return_period_years: Decimal
    severity_tier: str  # "CRITICAL", "HIGH", "ELEVATED", "MODERATE"
    coupling_regime_label: str
    ownership_type: str = "PRIMARY_CUSTODIAN"
    primary_risk_ref: Optional[str] = None
    contributing_towers: Optional[list[str]] = None
    is_deduplicated: bool = False


class ActuarialEngine:
    """Stateless mathematical calculator executing Open FAIR exposure modeling."""

    DEFAULT_THRESHOLDS: Dict[str, Decimal] = {
        "CRITICAL": Decimal("25000.00"),
        "HIGH": Decimal("10000.00"),
        "ELEVATED": Decimal("3000.00"),
    }

    @classmethod
    def evaluate(
        cls,
        inputs: FairActuarialInput,
        thresholds: Optional[Dict[str, Decimal]] = None,
        portfolio_total_ale: Optional[Decimal] = None,
        ownership_type: str = "PRIMARY_CUSTODIAN",
        primary_risk_ref: Optional[str] = None,
        contributing_towers: Optional[list[str]] = None,
    ) -> ComputedFairMetrics:
        """Evaluates FairActuarialInput parameters into verified, auditable financial metrics."""
        if thresholds is not None:
            active_thresholds = thresholds
        elif portfolio_total_ale is not None and portfolio_total_ale > Decimal("0.00"):
            active_thresholds = {
                "CRITICAL": (portfolio_total_ale * Decimal("0.15")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "HIGH": (portfolio_total_ale * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "ELEVATED": (portfolio_total_ale * Decimal("0.015")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            }
        else:
            base_magnitude = inputs.single_loss_magnitude_base * Decimal(str(inputs.operational_coupling_factor))
            if base_magnitude > Decimal("0.00"):
                active_thresholds = {
                    "CRITICAL": (base_magnitude * Decimal("0.50")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    "HIGH": (base_magnitude * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                    "ELEVATED": (base_magnitude * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                }
            else:
                active_thresholds = cls.DEFAULT_THRESHOLDS

        coupling_dec = Decimal(str(inputs.operational_coupling_factor))
        lef_dec = Decimal(str(inputs.loss_event_frequency_annual))

        is_tangential = (ownership_type == "TANGENTIAL_CONTRIBUTOR")
        if is_tangential:
            effective_sle = Decimal("0.00")
            ale = Decimal("0.00")
            is_deduplicated = True
        else:
            effective_sle = (inputs.single_loss_magnitude_base * coupling_dec).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            ale = (effective_sle * lef_dec).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            is_deduplicated = False

        # Safe return period calculation bounded against division by zero
        if lef_dec > Decimal("0.00001"):
            return_period = (Decimal("1.0") / lef_dec).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
        else:
            return_period = Decimal("100.0")

        intrinsic_ale = (inputs.single_loss_magnitude_base * coupling_dec * lef_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        severity = cls._resolve_severity(ale if not is_tangential else intrinsic_ale, active_thresholds)

        return ComputedFairMetrics(
            effective_sle=effective_sle,
            annualized_loss_expectancy=ale,
            loss_event_frequency=inputs.loss_event_frequency_annual,
            return_period_years=return_period,
            severity_tier=severity,
            coupling_regime_label=inputs.coupling_regime.value,
            ownership_type=ownership_type,
            primary_risk_ref=primary_risk_ref,
            contributing_towers=contributing_towers,
            is_deduplicated=is_deduplicated,
        )

    @staticmethod
    def _resolve_severity(ale: Decimal, thresholds: Dict[str, Decimal]) -> str:
        """Determines the risk severity tier based on monetary ALE bounds."""
        if ale <= Decimal("0.00"):
            return "MODERATE"
        if ale >= thresholds.get("CRITICAL", Decimal("25000.00")):
            return "CRITICAL"
        if ale >= thresholds.get("HIGH", Decimal("10000.00")):
            return "HIGH"
        if ale >= thresholds.get("ELEVATED", Decimal("3000.00")):
            return "ELEVATED"
        return "MODERATE"


def calculate_severity_weighted_sle(
    rto_hours: float,
    effective_rate: float,
    severity: str,
    is_spof: bool = False,
) -> tuple[float, float, float, float]:
    """Calculates Single Loss Expectancy (SLE) decomposed into operational, replacement, and secondary components.

    Scale-invariant, pure function mapping recovery time and hourly downtime burn into:
    (sle_total, alpha_blast_radius, replacement_cost, secondary_cost).
    """
    is_crit = is_spof or severity == "CRITICAL"
    if is_crit:
        alpha = 0.85
        repl = effective_rate * 2.0
        sec = effective_rate * 3.5
    elif severity == "HIGH":
        alpha = 0.55
        repl = effective_rate * 0.75
        sec = effective_rate * 1.5
    else:
        alpha = 0.25
        repl = 0.0
        sec = effective_rate * 0.5

    sle = (rto_hours * alpha * effective_rate) + repl + sec
    return sle, alpha, repl, sec
