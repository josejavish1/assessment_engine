"""Causal Regulatory Gating and Statutory Liability Engine (SR 11-7)."""

from __future__ import annotations

from typing import Optional
from assessment_engine.domain.schemas.actuarial_contracts import (
    CausalNature,
    DataClassification,
)


class RegulatoryGatingEngine:
    """Enforces causal indicator gating on statutory data protection penalties (GDPR, NIS2, DORA).

    Prevents spurious regulatory fines on purely physical, telecommunications, or resource-exhaustion events.
    """

    @staticmethod
    def is_privacy_breach_eligible(
        causal_nature: CausalNature,
        data_classification: DataClassification,
    ) -> bool:
        """Determines whether a threat scenario can legally incur data protection regulatory fines.

        Indicator function:
        I_breach = 1 if causal_nature == MALICIOUS_EXFILTRATION and data_classification == REGULATED_PII_FINANCIAL
        I_breach = 0 otherwise
        """
        if causal_nature != CausalNature.MALICIOUS_EXFILTRATION:
            return False
        return data_classification == DataClassification.REGULATED_PII_FINANCIAL

    @staticmethod
    def calculate_statutory_privacy_exposure(
        causal_nature: CausalNature,
        data_classification: DataClassification,
        baseline_statutory_fine: float,
    ) -> float:
        """Returns statutory data privacy exposure, strictly gated to 0.0 EUR on non-breach physical events."""
        if not RegulatoryGatingEngine.is_privacy_breach_eligible(
            causal_nature, data_classification
        ):
            return 0.0
        return float(max(0.0, baseline_statutory_fine))
