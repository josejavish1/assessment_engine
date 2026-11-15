"""Domain actuarial package providing FAIR models, downtime calibration, and financial profiling."""

from __future__ import annotations

from assessment_engine.domain.actuarial.downtime_calibrator import (
    ActuarialDowntimeCalibrator,
)
from assessment_engine.domain.actuarial.financial_profile import (
    IndustryArchetype,
    TenantFinancialProfile,
)
from assessment_engine.domain.actuarial.rounding import (
    allocate_subadditive_ale_to_cards,
    compute_step_quantum,
    round_to_actuarial_significance,
)
from assessment_engine.domain.actuarial.schemas import (
    Chapter4SynthesisPayload,
    ChronicOperationalDragBreakdown,
    CostOfInactionTotal,
    HeatmapCoordinate,
    MonetaryInterval,
    ProbabilisticOutageALEBreakdown,
    TechnicalRiskScenario,
    ThreeYearCompoundedTCO,
)

__all__ = [
    "ActuarialDowntimeCalibrator",
    "Chapter4SynthesisPayload",
    "ChronicOperationalDragBreakdown",
    "CostOfInactionTotal",
    "HeatmapCoordinate",
    "IndustryArchetype",
    "MonetaryInterval",
    "ProbabilisticOutageALEBreakdown",
    "TechnicalRiskScenario",
    "TenantFinancialProfile",
    "ThreeYearCompoundedTCO",
    "allocate_subadditive_ale_to_cards",
    "compute_step_quantum",
    "round_to_actuarial_significance",
]
