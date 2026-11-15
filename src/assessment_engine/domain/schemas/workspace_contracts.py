"""
Canonical workspace contract schemas for multi-tenant assessment storage.
Strict Pydantic V2 models defining the physical workspace files:
- client_intelligence.json (ClientDossierV3)
- evidence_vault.json (EvidenceVaultContract)
- digital_twin_state.json (DigitalTwinStateContract)
- pipeline_status.json (PipelineStatusContract)
"""

from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class PerimeterScopeType(str, Enum):
    """Scope of the enterprise operational assessment."""
    GLOBAL_HOLDING = "GLOBAL_HOLDING"
    REGIONAL_DIVISION = "REGIONAL_DIVISION"
    SUBSIDIARY_ENTITY = "SUBSIDIARY_ENTITY"
    INDUSTRIAL_FACILITY = "INDUSTRIAL_FACILITY"


class RegulatoryFrameworkSpec(BaseModel):
    """Defines a binding regulatory or compliance framework."""
    model_config = ConfigDict(extra="forbid")

    framework_id: str = Field(..., description="Canonical framework code, e.g., NIS2, DORA, LGPD, IEC_62443, FCA_SYSC")
    jurisdiction_iso: str = Field(..., description="ISO 3166-1 alpha-2, e.g., ES, GB, BR, FR, US")
    enforcement_tier: str = Field(..., description="e.g., Essential Entity, Important Entity, Systemic Tier-1, General Compliance")
    applicability_rationale: str = Field(default="", description="Justification for mandatory applicability to this tenant")


class FinancialParameters(BaseModel):
    """Financial scale indicators used by the actuarial FAIR loss engine."""
    model_config = ConfigDict(extra="forbid")

    base_currency_iso: str = Field(..., pattern=r"^[A-Z]{3}$", description="ISO 4217 currency code, e.g., EUR, GBP, BRL, USD")
    annual_revenue_amount: float = Field(..., gt=0, description="Annual revenue in millions of base currency")
    ebitda_margin_pct: float = Field(default=15.0, ge=-100.0, le=100.0, description="Estimated EBITDA margin percentage")
    insurable_cyber_limit: float = Field(default=0.0, ge=0.0, description="Existing cyber insurance liability limit in millions")


class PerimeterDefinition(BaseModel):
    """Operational perimeter boundaries for the diagnostic."""
    model_config = ConfigDict(extra="forbid")

    scope_type: PerimeterScopeType = Field(default=PerimeterScopeType.GLOBAL_HOLDING)
    target_entity_name: str = Field(..., description="Name of the audited entity or division")
    parent_group_name: Optional[str] = Field(default=None, description="Consolidated holding group if scope is subsidiary")
    employee_headcount: int = Field(..., gt=0, description="Total headcount within evaluated perimeter")
    operating_countries_iso: List[str] = Field(default_factory=list, description="List of operating country ISO codes")
    critical_assets_summary: List[str] = Field(default_factory=list, description="Primary infrastructure asset categories")


class ClientDossierV3(BaseModel):
    """Master enterprise intelligence dossier stored in client_intelligence.json."""
    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(default="3.0.0", description="Strict semantic contract version")
    client_slug: str = Field(..., pattern=r"^[a-z0-9\-_]+$", description="URL-safe sanitized client slug")
    legal_entity_name: str = Field(..., description="Registered corporate legal entity name")
    industry_vertical_code: str = Field(..., description="Standardized industry vertical ID")
    primary_hq_country_iso: str = Field(..., pattern=r"^[A-Z]{2}$", description="Headquarters country ISO code")
    output_locale: str = Field(default="en", description="Target deliverable language code, e.g., en, es, pt")
    last_updated_utc: str = Field(..., description="ISO 8601 UTC timestamp of last modification")
    perimeter: PerimeterDefinition
    financials: FinancialParameters
    regulatory_landscape: List[RegulatoryFrameworkSpec] = Field(default_factory=list)
    executive_context_synthesis: str = Field(default="", description="Consolidated strategic synthesis from context discovery")
    strategic_pain_points: List[str] = Field(default_factory=list, description="List of primary operational pain points")

    @property
    def profile(self) -> Any:
        """Backwards-compatible profile accessor returning profile dictionary."""
        class ProfileShim:
            def __init__(self, parent: ClientDossierV3):
                self.parent = parent
                self.regulatory_frameworks = [
                    (r.framework_code if hasattr(r, "framework_code") else str(r))
                    for r in parent.regulatory_landscape
                ]
                self.industry = parent.industry_vertical_code
                self.primary_hq_country_iso = parent.primary_hq_country_iso
                self.language = parent.output_locale
                self.annual_revenue = parent.financials.annual_revenue_amount

            def get(self, key: str, default: Any = None) -> Any:
                return getattr(self, key, default)

        return ProfileShim(self)

    @model_validator(mode="before")
    @classmethod
    def adapt_legacy_or_canonical_format(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if "legal_entity_name" in data and "financials" in data and "perimeter" in data:
            return data

        raw_slug = data.get("client_slug") or data.get("client_name") or "enterprise-client"
        sanitized_slug = re.sub(r"[^a-z0-9\-_]", "-", str(raw_slug).lower()).strip("-")
        legal_name = str(data.get("legal_entity_name") or data.get("client_name") or "Enterprise Client")
        profile = data.get("profile") if isinstance(data.get("profile"), dict) else {}
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        tech = data.get("technology_context") if isinstance(data.get("technology_context"), dict) else {}
        biz = data.get("business_context") if isinstance(data.get("business_context"), dict) else {}

        stack = tech.get("group_level_stack")
        if isinstance(stack, list):
            crit_assets = [str(x) for x in stack]
        elif isinstance(stack, dict):
            crit_assets = [str(k) for k in stack.keys()]
        else:
            crit_assets = ["Corporate Core Platforms"]

        ceo_agenda = biz.get("ceo_agenda") if isinstance(biz.get("ceo_agenda"), dict) else {}

        return {
            "schema_version": str(data.get("schema_version") or "3.0.0"),
            "client_slug": sanitized_slug,
            "legal_entity_name": legal_name,
            "industry_vertical_code": str(data.get("industry_vertical_code") or profile.get("industry") or "HEAVY_MANUFACTURING"),
            "primary_hq_country_iso": str(data.get("primary_hq_country_iso") or profile.get("primary_hq_country_iso") or "ES").upper()[:2],
            "output_locale": str(data.get("output_locale") or profile.get("language") or "es"),
            "last_updated_utc": str(data.get("last_updated_utc") or metadata.get("created_at") or "2026-11-15T00:00:00Z"),
            "perimeter": data.get("perimeter") or {
                "scope_type": "GLOBAL_HOLDING",
                "target_entity_name": legal_name,
                "employee_headcount": int(profile.get("employee_headcount") or 5000),
                "operating_countries_iso": profile.get("operating_countries_iso") or ["ES"],
                "critical_assets_summary": crit_assets or ["Core Infrastructure"],
            },
            "financials": data.get("financials") or {
                "base_currency_iso": str(metadata.get("currency_code") or "EUR").upper()[:3],
                "annual_revenue_amount": float(profile.get("annual_revenue") or 1250000000.0),
                "ebitda_margin_pct": float(profile.get("ebitda_margin_pct") or 15.0),
                "insurable_cyber_limit": 0.0,
            },
            "regulatory_landscape": data.get("regulatory_landscape") or [],
            "executive_context_synthesis": str(data.get("executive_context_synthesis") or ceo_agenda.get("summary") or ""),
            "strategic_pain_points": data.get("strategic_pain_points") or [],
        }


class EvidenceSourceType(str, Enum):
    """Origin of a forensic evidence statement or fragment."""
    INTERVIEW_TRANSCRIPT = "INTERVIEW_TRANSCRIPT"
    EXECUTIVE_NOTES = "EXECUTIVE_NOTES"
    QUESTIONNAIRE_MATRIX = "QUESTIONNAIRE_MATRIX"
    OSINT_HARVESTER = "OSINT_HARVESTER"


class EvidenceFragment(BaseModel):
    """Atomic evidence record extracted from context sessions or matrix inputs."""
    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(..., description="Deterministic SHA-256 prefixed identifier, e.g., EV-8F9A2B")
    source_type: EvidenceSourceType
    source_filename: str = Field(default="", description="Original file or session name")
    ingestion_timestamp_utc: str = Field(..., description="ISO 8601 UTC timestamp")
    raw_verbatim_text: str = Field(..., description="Verbatim text extracted from conversation or notes")
    normalized_claim: str = Field(default="", description="Synthesized technical claim")
    mapped_domain_ids: List[str] = Field(default_factory=list, description="Associated technology tower IDs, e.g., T1, T2")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Epistemic confidence rating")
    speaker_role: Optional[str] = Field(default=None, description="e.g., CTO, CISO, Head of Infrastructure")


class EvidenceVaultContract(BaseModel):
    """Forensic evidence ledger persisted in evidence_vault.json."""
    model_config = ConfigDict(extra="forbid")

    client_slug: str
    total_fragments: int
    integrity_hash: str = Field(default="", description="SHA-256 integrity seal over all fragments")
    fragments: List[EvidenceFragment] = Field(default_factory=list)


class QuestionResponseItem(BaseModel):
    """Individual question response and maturity indicator."""
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(..., description="e.g., T1.P1.K1.PR1")
    prompt_key: str = Field(default="", description="i18n lookup key in engine_config/locales_ui.json")
    response_text: str = Field(default="", description="Forensic notes or observations for this question")
    maturity_indicator: float = Field(default=3.0, ge=1.0, le=5.0, description="Maturity rating on 1.0 - 5.0 scale")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Linked EvidenceFragment IDs")


class SecurityTowerState(BaseModel):
    """Maturity and evidence state for a single infrastructure tower."""
    model_config = ConfigDict(extra="forbid")

    tower_id: str = Field(..., description="e.g., T1, T2, T3 ... T10")
    calibrated_maturity_score: float = Field(default=3.0, ge=1.0, le=5.0)
    target_to_be_score: float = Field(default=4.0, ge=1.0, le=5.0)
    assessor_forensic_notes: str = Field(default="", description="Tower-level synthesis notes")
    is_applicable: bool = Field(default=True, description="Whether this discipline is in scope")
    completed: bool = Field(default=False, description="Whether this tower assessment has been marked finished")
    question_responses: List[QuestionResponseItem] = Field(default_factory=list)


class DigitalTwinStateContract(BaseModel):
    """Real-time technical state vector persisted in digital_twin_state.json."""
    model_config = ConfigDict(extra="forbid")

    client_slug: str
    last_synchronized_utc: str
    overall_maturity_index: float = Field(default=3.0, ge=1.0, le=5.0)
    completion_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    towers: Dict[str, SecurityTowerState] = Field(default_factory=dict)


class PipelineStageStatus(str, Enum):
    """Compilation stage states."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineStatusContract(BaseModel):
    """Real-time compilation telemetry stored in pipeline_status.json."""
    model_config = ConfigDict(extra="forbid")

    job_id: str
    client_slug: str
    status: PipelineStageStatus = Field(default=PipelineStageStatus.QUEUED)
    current_stage: str = Field(default="IDLE")
    progress_pct: float = Field(default=0.0, ge=0.0, le=100.0)
    message_key: str = Field(default="")
    completed_files: List[str] = Field(default_factory=list)
    error_detail: Optional[str] = None
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
