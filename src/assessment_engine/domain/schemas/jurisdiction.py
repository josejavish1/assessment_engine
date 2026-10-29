"""Domain schemas for Jurisdictional Architectural Sovereignty."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class JurisdictionSovereigntyProfile(BaseModel):
    """Encapsulates territorial architectural invariants and sovereign cloud requirements for a jurisdiction."""

    name: str = Field(description="Full jurisdiction designation, e.g. Germany / DACH & Central Europe.")
    region_code: str = Field(description="ISO 3166-1 alpha-2 country code or region tag, e.g. DE, ES, US.")
    sovereign_cloud_providers: List[str] = Field(
        default_factory=list,
        description="Qualified sovereign cloud and datacenter providers with regional enclaves.",
    )
    architectural_invariants: List[str] = Field(
        default_factory=list,
        description="Mandatory technical and operational architecture invariants required in this jurisdiction.",
    )
    connectivity_standards: List[str] = Field(
        default_factory=list,
        description="Direct peering, interconnection and physical encryption network standards.",
    )
    primary_hsm_standard: str = Field(
        default="FIPS 140-2 Level 3",
        description="Jurisdiction-mandated hardware security module (HSM) qualification standard.",
    )
    data_residency_rules: List[str] = Field(
        default_factory=list,
        description="Legal and technical data boundary, custody, and residency requirements.",
    )


class JurisdictionalRegistry(BaseModel):
    """Top-level registry mapping region codes to their corresponding sovereign profiles."""

    version: str = "1.0.0"
    jurisdictions: Dict[str, JurisdictionSovereigntyProfile] = Field(default_factory=dict)
