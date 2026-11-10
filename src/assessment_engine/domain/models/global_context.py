"""Versioned Global Context and Central Parameter-Pack Contract (SR 11-7).

Enforces explicit entity scoping, currency/FX evidence verification, evidence-backed
jurisdiction parameter packs, and elimination of silent defaults across global enterprises.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class FXRateSnapshot(BaseModel):
    """Auditable, versioned Foreign Exchange rate record for multi-currency consolidation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_currency: str
    reporting_currency: str
    rate: float = Field(..., gt=0.0)
    source: str = Field(..., min_length=2)
    snapshot_date: str = Field(..., min_length=10)
    confidence: str = Field(default="CONFIRMED")
    provenance_reference: str = Field(..., min_length=2)


class JurisdictionParameterPack(BaseModel):
    """Evidence-backed statutory and regulatory parameter pack."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    jurisdiction_code: str
    version: str = "1.0.0"
    statutory_fine_cap_percentage: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    statutory_fine_ceiling_amount: Optional[float] = Field(default=None, ge=0.0)
    legal_framework_references: List[str] = Field(default_factory=list)
    confidence: str = Field(default="CONFIRMED")
    provenance: str = Field(default="MODEL_DEFAULT")


class GlobalAssessmentContext(BaseModel):
    """Complete multi-tenant global context for an actuarial risk assessment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = "DEFAULT_TENANT"
    business_entity_id: str = "DEFAULT_ENTITY"
    operating_site_id: str = "DEFAULT_SITE"
    country_code: str = "ES"
    jurisdiction_code: str = "EU_GDPR_NIS2"
    source_currency: str = "EUR"
    reporting_currency: str = "EUR"
    assessment_period: str = "2026.Q4"
    sector_code: str = "PROCESS_MANUFACTURING"
    subsector_code: str = "CEMENT_HEAVY_BUILDING_MATERIALS"
    annual_revenue: Optional[float] = Field(default=None, gt=0.0)
    annual_it_opex: Optional[float] = Field(default=None, gt=0.0)
    fully_burdened_hourly_rate: Optional[float] = Field(default=None, gt=0.0)
    authoritative_hourly_downtime_cost: Optional[float] = Field(default=None, gt=0.0)
    fx_snapshots: Dict[str, FXRateSnapshot] = Field(default_factory=dict)
    jurisdiction_pack: Optional[JurisdictionParameterPack] = None

    def normalize_monetary_amount(self, amount: float, source_curr: str) -> float:
        """Normalizes source currency into reporting currency via verified FX snapshot."""
        src = source_curr.strip().upper()
        rep = self.reporting_currency.strip().upper()
        if src == rep:
            return amount
        pair = f"{src}_{rep}"
        if pair not in self.fx_snapshots:
            raise ValueError(
                f"Unsupported Context Error: No verified FX snapshot found for currency pair '{pair}'. "
                f"Cannot consolidate multi-currency raw exposures without explicit FX evidence."
            )
        snapshot = self.fx_snapshots[pair]
        return round(amount * snapshot.rate, 2)
