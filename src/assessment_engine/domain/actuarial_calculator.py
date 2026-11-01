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
    ) -> ComputedFairMetrics:
        """Evaluates FairActuarialInput parameters into verified, auditable financial metrics."""
        active_thresholds = thresholds or cls.DEFAULT_THRESHOLDS

        coupling_dec = Decimal(str(inputs.operational_coupling_factor))
        lef_dec = Decimal(str(inputs.loss_event_frequency_annual))

        effective_sle = (inputs.single_loss_magnitude_base * coupling_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        ale = (effective_sle * lef_dec).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # Safe return period calculation bounded against division by zero
        if lef_dec > Decimal("0.00001"):
            return_period = (Decimal("1.0") / lef_dec).quantize(
                Decimal("0.1"), rounding=ROUND_HALF_UP
            )
        else:
            return_period = Decimal("100.0")

        severity = cls._resolve_severity(ale, active_thresholds)

        return ComputedFairMetrics(
            effective_sle=effective_sle,
            annualized_loss_expectancy=ale,
            loss_event_frequency=inputs.loss_event_frequency_annual,
            return_period_years=return_period,
            severity_tier=severity,
            coupling_regime_label=inputs.coupling_regime.value,
        )

    @staticmethod
    def _resolve_severity(ale: Decimal, thresholds: Dict[str, Decimal]) -> str:
        """Determines the risk severity tier based on monetary ALE bounds."""
        if ale >= thresholds.get("CRITICAL", Decimal("25000.00")):
            return "CRITICAL"
        if ale >= thresholds.get("HIGH", Decimal("10000.00")):
            return "HIGH"
        if ale >= thresholds.get("ELEVATED", Decimal("3000.00")):
            return "ELEVATED"
        return "MODERATE"
