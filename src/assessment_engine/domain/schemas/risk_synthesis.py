"""Domain schemas for reverse FAIR risk synthesis contracts."""

from __future__ import annotations

import hashlib
from typing import Protocol
from pydantic import BaseModel, Field


class RiskSynthesisContext(BaseModel):
    """Immutable context vector defining inputs for risk synthesis."""

    client_name: str
    industry: str = "Enterprise"
    sub_industry: str = "Corporate"
    maturity_tier: str = "Level 3 - Defined"
    doc_lang: str = "en"
    currency_symbol: str = "GBP"
    hourly_rate: float
    verified_tech_stack: list[str] = Field(default_factory=list)
    tower_code: str
    tower_name: str
    pillar_id: str
    pillar_name: str
    kpi_id: str
    assessed_score: float
    calibrated_ale: float
    downtime_minutes: int
    stoppage_loss: float
    recovery_burn: float
    penalty_loss: float
    total_sle: float

    def compute_context_hash(self, prompt_version: str = "v1") -> str:
        """Compute SHA-256 fingerprint for cryptographic cache validation."""
        payload_str = (
            f"{self.client_name}|{self.sub_industry}|{self.maturity_tier}|{self.doc_lang}|"
            f"{self.currency_symbol}|{self.hourly_rate:.2f}|{sorted(self.verified_tech_stack)}|"
            f"{self.tower_code}|{self.pillar_id}|{self.kpi_id}|{self.assessed_score:.2f}|"
            f"{self.calibrated_ale:.2f}|{self.total_sle:.2f}|{prompt_version}"
        )
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


class SynthesizedRiskItem(BaseModel):
    """Strictly typed domain output representing an enriched, stack-aware risk scenario."""

    risk_id: str
    causal_risk_title: str
    technical_failure_mechanism: str
    actuarial_justification: str
    remediation_architecture: str
    context_hash: str


class IRiskSynthesizer(Protocol):
    """Interface defining the contract for risk synthesis providers."""

    def synthesize_risk(self, ctx: RiskSynthesisContext) -> SynthesizedRiskItem:
        """Synthesize a stack-grounded, actuarially reconciled risk item."""
        ...
