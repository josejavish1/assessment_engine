"""Domain schema definitions for the enriched tower annex payload.

Enforces structural parity across all assessment towers (T1..T10) prior to
document rendering, preventing split-brain schema degradation.
"""

from __future__ import annotations

from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class DocumentMetadata(BaseModel):
    """Tenant and localization metadata extracted from runtime configuration."""

    model_config = ConfigDict(extra="allow")

    client_name: str = Field(..., min_length=1)
    tower_id: str = Field(..., pattern=r"^T([1-9]|10)$")
    language: str = Field(..., pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    doc_lang: str = Field(..., pattern=r"^[a-z]{2}(-[A-Z]{2})?$")
    currency_code: str = Field(..., pattern=r"^[A-Z]{3}$")
    vertical_industry: str = Field(default="enterprise_general")


class EnrichedPillarProfile(BaseModel):
    """Enriched structural representation of a single capability pillar."""

    model_config = ConfigDict(extra="allow")

    pillar_id: str
    pillar_label: str
    raw_score: float = Field(..., ge=0.0, le=5.0)
    formatted_score: str
    maturity_tier_label: str
    executive_reading: str
    deficient_kpi_labels: list[str] = Field(default_factory=list)
    forensic_evidence_refs: list[str] = Field(default_factory=list)


class FinancialTelemetryBlock(BaseModel):
    """Actuarial and financial exposure metrics bound from the CFO Gate."""

    model_config = ConfigDict(extra="allow")

    currency_code: str
    authoritative_hourly_downtime_cost: float = Field(default=0.0, ge=0.0)
    total_annualized_risk_exposure: float
    formatted_risk_exposure: str
    remediation_capex_estimate: float
    formatted_capex_estimate: str
    remediation_opex_estimate: float
    formatted_opex_estimate: str
    actuarial_confidence_band: str


class EnrichedTowerPayload(BaseModel):
    """Master contract enforcing the 21 mandatory structural keys across all towers."""

    model_config = ConfigDict(extra="allow")

    # Core 11 Base Keys (Normalized)
    document_meta: DocumentMetadata
    executive_summary: dict[str, Any]
    tower_score_summary: dict[str, Any]
    pillar_score_profile: dict[str, list[EnrichedPillarProfile] | Any]
    kpi_assessment_matrix: list[dict[str, Any]]
    findings_register: list[dict[str, Any]]
    risk_heatmap_data: dict[str, Any]
    remediation_roadmap: dict[str, Any]
    architecture_topology: dict[str, Any]
    compliance_mapping: dict[str, Any]
    appendix_glossary: dict[str, Any]

    # Advanced 10 Enriched Keys (Previously exclusive to T1 manual scripts)
    financial_telemetry: FinancialTelemetryBlock
    forensic_evidence_ledger: list[dict[str, Any]]
    localized_taxonomy_map: dict[str, str]
    pillar_executive_narratives: dict[str, str]
    benchmark_peer_comparison: dict[str, Any]
    operational_blast_radius: dict[str, Any]
    target_operating_model_gaps: list[dict[str, Any]]
    technical_debt_quantification: dict[str, Any]
    governance_control_deficiencies: list[dict[str, Any]]
    enrichment_audit_trail: dict[str, str]
