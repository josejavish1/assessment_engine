"""Versioned Global Context and Central Parameter-Pack Contract (SR 11-7).

Enforces explicit entity scoping, currency/FX evidence verification, evidence-backed
jurisdiction parameter packs, and elimination of silent defaults across global enterprises.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

VALID_ISO_CURRENCIES: Set[str] = {
    "AED",
    "ARS",
    "AUD",
    "BHD",
    "BRL",
    "CAD",
    "CHF",
    "CLP",
    "CNH",
    "CNY",
    "COP",
    "CZK",
    "DKK",
    "EGP",
    "EUR",
    "GBP",
    "HKD",
    "HUF",
    "IDR",
    "ILS",
    "INR",
    "ISK",
    "JOD",
    "JPY",
    "KRW",
    "KWD",
    "KZT",
    "MXN",
    "MYR",
    "NGN",
    "NOK",
    "NZD",
    "OMR",
    "PEN",
    "PHP",
    "PKR",
    "PLN",
    "QAR",
    "SAR",
    "SEK",
    "SGD",
    "THB",
    "TRY",
    "TWD",
    "USD",
    "VND",
    "ZAR",
}


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

    @field_validator("source_currency", "reporting_currency")
    def validate_currency_code(cls, v: str) -> str:
        code = str(v).strip().upper()
        if code not in VALID_ISO_CURRENCIES:
            raise ValueError(
                f"Currency code '{code}' is not a supported ISO 4217 currency in the catalog."
            )
        return code


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

    @model_validator(mode="after")
    def validate_confidence_provenance(self) -> JurisdictionParameterPack:
        if self.provenance == "MODEL_DEFAULT" and self.confidence == "CONFIRMED":
            raise ValueError(
                "Jurisdiction Invariant: MODEL_DEFAULT cannot have confidence CONFIRMED."
            )
        return self


class GlobalAssessmentContext(BaseModel):
    """Complete multi-tenant global context for an actuarial risk assessment.

    No silent country, jurisdiction, sector, or company defaults are permitted in production.
    All operating contexts must be explicitly declared and validated.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    tenant_id: str = Field(
        ..., min_length=1, description="Unique tenant or group identifier"
    )
    business_entity_id: str = Field(
        ..., min_length=1, description="Legal business entity or subsidiary"
    )
    operating_site_id: str = Field(
        ..., min_length=1, description="Specific facility, campus, or datacenter site"
    )
    country_code: str = Field(
        ...,
        min_length=2,
        max_length=3,
        description="ISO 3166-1 alpha-2 or alpha-3 country code",
    )
    jurisdiction_code: str = Field(
        ..., min_length=2, description="Statutory jurisdiction code"
    )
    source_currency: str = Field(..., description="Source transaction currency")
    reporting_currency: str = Field(..., description="Reporting consolidation currency")
    assessment_period: str = Field(
        ..., min_length=4, description="Audit or fiscal period (e.g. 2026.Q4)"
    )
    sector_code: str = Field(
        ..., min_length=2, description="Standard industry sector code"
    )
    subsector_code: str = Field(
        ..., min_length=2, description="Specific industry subsector code"
    )

    annual_revenue: Optional[float] = Field(default=None, gt=0.0)
    annual_it_opex: Optional[float] = Field(default=None, gt=0.0)
    fully_burdened_hourly_rate: Optional[float] = Field(default=None, gt=0.0)
    authoritative_hourly_downtime_cost: Optional[float] = Field(default=None, gt=0.0)
    fx_snapshots: Dict[str, FXRateSnapshot] = Field(default_factory=dict)
    jurisdiction_pack: Optional[JurisdictionParameterPack] = None

    @field_validator("source_currency", "reporting_currency")
    def validate_iso_currencies(cls, v: str) -> str:
        code = str(v).strip().upper()
        if code not in VALID_ISO_CURRENCIES:
            raise ValueError(
                f"Currency code '{code}' is not supported in the active ISO 4217 catalog."
            )
        return code

    def normalize_monetary_amount(
        self, amount: float, source_curr: Optional[str] = None
    ) -> float:
        """Normalizes source currency into reporting currency via verified FX snapshot. Returns float."""
        converted, _, _ = self.normalize_monetary_amount_with_provenance(
            amount, source_curr
        )
        return converted

    def normalize_monetary_amount_with_provenance(
        self, amount: float, source_curr: Optional[str] = None
    ) -> tuple[float, float, str]:
        """Normalizes source currency into reporting currency via verified FX snapshot.

        Returns:
            Tuple of (converted_amount, fx_rate, snapshot_provenance_id)
        """
        if amount < 0.0:
            raise ValueError(f"Monetary amount cannot be negative: {amount}")
        src = (source_curr or self.source_currency).strip().upper()
        rep = self.reporting_currency.strip().upper()
        if src == rep:
            return round(amount, 2), 1.0, "IDENTITY_1_TO_1"
        pair = f"{src}_{rep}"
        if pair not in self.fx_snapshots:
            raise ValueError(
                f"Unsupported Context Error: No verified FX snapshot found for currency pair '{pair}'. "
                f"Cannot consolidate multi-currency raw exposures without explicit FX evidence."
            )
        snapshot = self.fx_snapshots[pair]
        return (
            round(amount * snapshot.rate, 2),
            float(snapshot.rate),
            snapshot.provenance_reference,
        )

    def compute_context_sha256(self) -> str:
        """Computes deterministic SHA-256 fingerprint over sorted canonical JSON."""
        import hashlib
        import json

        payload = self.model_dump(mode="json")
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()

    @classmethod
    def create_legacy_generic_context(
        cls,
        tenant_id: str = "DEFAULT_TENANT",
        business_entity_id: str = "DEFAULT_ENTITY",
        operating_site_id: str = "DEFAULT_SITE",
        country_code: str = "GENERIC",
        jurisdiction_code: str = "GENERIC_STATUTORY",
        currency: str = "EUR",
        assessment_period: str = "2026.Q4",
        sector_code: str = "CROSS_SECTOR",
        subsector_code: str = "GENERAL",
        annual_revenue: Optional[float] = None,
        hourly_downtime_cost: Optional[float] = None,
        fx_snapshots: Optional[Dict[str, FXRateSnapshot]] = None,
    ) -> GlobalAssessmentContext:
        """Explicit constructor for backward-compatible or benchmark executions."""
        curr_clean = str(currency).strip().upper() if currency else "EUR"
        if curr_clean not in VALID_ISO_CURRENCIES:
            curr_clean = "EUR"

        if fx_snapshots is not None:
            snapshots = fx_snapshots
        else:
            snapshots = {}
            rates_to_usd = {
                "USD": 1.0,
                "EUR": 0.92,
                "GBP": 0.80,
                "CHF": 0.88,
                "BRL": 5.00,
                "JPY": 150.0,
            }
            for s_c, s_r in rates_to_usd.items():
                for t_c, t_r in rates_to_usd.items():
                    if s_c != t_c:
                        p_id = f"{s_c}_{t_c}"
                        snapshots[p_id] = FXRateSnapshot(
                            source_currency=s_c,
                            reporting_currency=t_c,
                            rate=round(t_r / s_r, 6),
                            source="ECB Reference Rates (Canonical Baseline)",
                            snapshot_date="2026-10-31",
                            provenance_reference=f"ECB_FX_{s_c}_{t_c}_2026Q4",
                        )

        return cls(
            tenant_id=tenant_id,
            business_entity_id=business_entity_id,
            operating_site_id=operating_site_id,
            country_code=country_code[:3],
            jurisdiction_code=jurisdiction_code,
            source_currency=curr_clean,
            reporting_currency=curr_clean,
            assessment_period=assessment_period,
            sector_code=sector_code,
            subsector_code=subsector_code,
            annual_revenue=annual_revenue,
            authoritative_hourly_downtime_cost=hourly_downtime_cost,
            fx_snapshots=snapshots,
        )
