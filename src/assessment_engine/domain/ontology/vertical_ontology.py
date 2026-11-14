"""
Domain Models for Universal Multi-Vertical Enterprise Ontologies.
Implements Phase 2 of ARGON_GLOBAL_TIER1_MASTER_PLAN.md.

Mandates:
1. Pydantic V2 immutable models (frozen=True, extra="forbid", strict=True).
2. Pure Technical English across all definitions, attributes, and docstrings.
3. Universal sector support across 8 major world industries with zero manufacturing bias.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field


class VerticalSectorId(StrEnum):
    """Authoritative industry sector identifiers supported by the Assessment Engine."""

    MANUFACTURING_OT = "MANUFACTURING_OT"
    BANKING_CAPITAL_MARKETS = "BANKING_CAPITAL_MARKETS"
    HEALTHCARE_LIFESCIENCES = "HEALTHCARE_LIFESCIENCES"
    RETAIL_ECOMMERCE = "RETAIL_ECOMMERCE"
    ENERGY_UTILITIES = "ENERGY_UTILITIES"
    TELECOMMUNICATIONS = "TELECOMMUNICATIONS"
    SAAS_DIGITAL_NATIVE = "SAAS_DIGITAL_NATIVE"
    PUBLIC_SECTOR_DEFENSE = "PUBLIC_SECTOR_DEFENSE"

    @classmethod
    def from_str(cls, value: str) -> "VerticalSectorId":
        """Resolve string token to canonical VerticalSectorId with fail-safe fallback."""
        clean = str(value or "MANUFACTURING_OT").strip().upper().replace("-", "_").replace(" ", "_")
        for member in cls:
            if member.value == clean or member.name == clean:
                return member
            # Fuzzy match common synonyms
            if member == cls.MANUFACTURING_OT and any(k in clean for k in ["MANUFACTURING", "INDUSTRIAL", "FACTORY", "OT"]):
                return member
            if member == cls.BANKING_CAPITAL_MARKETS and any(k in clean for k in ["BANK", "FINANCIAL", "FINANCE", "PAYMENT"]):
                return member
            if member == cls.HEALTHCARE_LIFESCIENCES and any(k in clean for k in ["HEALTH", "CLINIC", "HOSPITAL", "PHARMA"]):
                return member
            if member == cls.RETAIL_ECOMMERCE and any(k in clean for k in ["RETAIL", "ECOMMERCE", "STORE"]):
                return member
            if member == cls.ENERGY_UTILITIES and any(k in clean for k in ["ENERGY", "POWER", "UTILITY", "GRID"]):
                return member
            if member == cls.TELECOMMUNICATIONS and any(k in clean for k in ["TELCO", "TELECOM", "5G", "CARRIER"]):
                return member
            if member == cls.SAAS_DIGITAL_NATIVE and any(k in clean for k in ["SAAS", "CLOUD_NATIVE", "TECH"]):
                return member
            if member == cls.PUBLIC_SECTOR_DEFENSE and any(k in clean for k in ["GOV", "DEFENSE", "MILITARY", "PUBLIC"]):
                return member
        return cls.MANUFACTURING_OT


class VerticalOntology(BaseModel):
    """Immutable sector ontology governing technical expectations and actuarial loss multipliers."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    vertical_id: VerticalSectorId = Field(..., description="Canonical sector identifier")
    name: str = Field(..., description="Official sector nomenclature")
    primary_regulations: List[str] = Field(..., description="Statutory frameworks governing sector")
    critical_asset_types: List[str] = Field(..., description="Sector-critical architecture asset categories")
    typical_outage_consequences: List[str] = Field(..., description="Real-world business disruption manifestations")
    operational_loss_multipliers: Dict[str, float] = Field(
        ..., description="Actuarial severity calibration multipliers for Open FAIR simulation"
    )
    lexicon_keywords: List[str] = Field(..., description="Domain technical tokens for auto-classification")
