from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field, field_validator

class RegulatoryHarvest(BaseModel):
    sector: str
    frameworks: List[str]
    regulatory_pressures: List[str] = Field(default_factory=list)
    source_evidence: str

class BusinessHarvest(BaseModel):
    ceo_agenda: str
    business_drivers: List[str]
    financial_tier: str = Field(..., pattern="^(Tier 1|Tier 2|Tier 3)$")
    priority_markets: List[str] = Field(default_factory=list)
    business_lines: List[str] = Field(default_factory=list)
    active_transformations: List[str] = Field(default_factory=list)
    business_constraints: List[str] = Field(default_factory=list)
    source_evidence: str

class TechHarvest(BaseModel):
    tech_footprint: str
    tech_trends: List[str]
    vendor_dependencies: List[str] = Field(default_factory=list)
    operating_constraints: List[str] = Field(default_factory=list)
    recent_incident_signals: List[str] = Field(default_factory=list)
    source_evidence: str

class ClientDossier(BaseModel):
    client_name: str
    industry: str
    financial_tier: str
    regulatory_frameworks: List[str]
    ceo_agenda: str
    technological_drivers: List[str]
    osint_footprint: str
    transformation_horizon: str
    target_maturity_matrix: Dict[str, float]
    evidences: List[str]


Confidence = Literal["low", "medium", "high"]
Applicability = Literal["low", "medium", "high"]
HorizonStage = Literal["H1", "H2", "H3"]
ClaimType = Literal["fact", "inference", "assumption"]


class EvidenceRef(BaseModel):
    source: str
    note: str | None = None


class SourcedText(BaseModel):
    summary: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class SourcedItem(BaseModel):
    name: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class RegulatoryFramework(BaseModel):
    name: str
    applicability: Applicability = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class TransformationHorizon(BaseModel):
    stage: HorizonStage
    label: str
    rationale: str
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class TowerContext(BaseModel):
    target_maturity: float = Field(ge=1.0, le=5.0)
    business_criticality: Confidence = "medium"
    regulatory_pressure: Confidence = "medium"
    change_urgency: Confidence = "medium"
    constraints: List[str] = Field(default_factory=list)


class ClientProfile(BaseModel):
    industry: str
    financial_tier: str
    operating_model: str | None = None
    regions: List[str] = Field(default_factory=list)


class BusinessContext(BaseModel):
    ceo_agenda: SourcedText
    technological_drivers: List[SourcedItem] = Field(default_factory=list)
    osint_footprint: SourcedText
    transformation_horizon: TransformationHorizon
    constraints: List[str] = Field(default_factory=list)


class EvidenceClaim(BaseModel):
    claim_id: str
    claim: str
    claim_type: ClaimType
    confidence: Confidence = "medium"
    sources: List[EvidenceRef] = Field(default_factory=list)


class ClientDossierV2(BaseModel):
    version: Literal["2.0"] = "2.0"
    client_name: str
    profile: ClientProfile
    regulatory_frameworks: List[RegulatoryFramework] = Field(default_factory=list)
    business_context: BusinessContext
    tower_overrides: Dict[str, TowerContext] = Field(default_factory=dict)
    evidence_register: List[EvidenceClaim] = Field(default_factory=list)


class ConfidenceAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    label: Confidence
    method: str = "custom"

    @field_validator("label", mode="before")
    @classmethod
    def normalize_label(cls, value: str) -> str:
        normalized = str(value).strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"critical", "very_high"}:
            return "high"
        if normalized in {"moderate", "mid"}:
            return "medium"
        if normalized in {"very_low"}:
            return "low"
        return normalized


class TimelinessWindow(BaseModel):
    created_at: str | None = None
    modified_at: str | None = None
    last_verified_at: str | None = None
    valid_until: str | None = None
    stale_after_days: int | None = Field(default=None, ge=1)


class ClaimSource(BaseModel):
    source: str
    note: str | None = None
    source_type: str = "public"
    source_reliability_score: int | None = Field(default=None, ge=0, le=100)


class SourcedTextV3(BaseModel):
    summary: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    evidence_strength: str | None = None


class SourcedItemV3(BaseModel):
    name: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    rationale: str | None = None


class RegulatoryFrameworkV3(BaseModel):
    name: str
    applicability: Applicability = "medium"
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    impacted_domains: List[str] = Field(default_factory=list)


class TransformationHorizonV3(BaseModel):
    stage: HorizonStage
    label: str
    rationale: str
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)


class TowerContextV3(BaseModel):
    target_maturity: float = Field(ge=1.0, le=5.0)
    business_criticality: ConfidenceAssessment
    regulatory_pressure: ConfidenceAssessment
    change_urgency: ConfidenceAssessment
    rationale: str | None = None
    constraints: List[str] = Field(default_factory=list)
    related_claim_ids: List[str] = Field(default_factory=list)


class ClientProfileV3(BaseModel):
    industry: str
    financial_tier: str
    operating_model: str | None = None
    regions: List[str] = Field(default_factory=list)
    priority_markets: List[str] = Field(default_factory=list)
    business_lines: List[str] = Field(default_factory=list)


class BusinessContextV3(BaseModel):
    ceo_agenda: SourcedTextV3
    strategic_priorities: List[SourcedItemV3] = Field(default_factory=list)
    business_model_signals: List[str] = Field(default_factory=list)
    active_transformations: List[str] = Field(default_factory=list)
    transformation_horizon: TransformationHorizonV3
    constraints: List[str] = Field(default_factory=list)


class TechnologyContextV3(BaseModel):
    footprint_summary: SourcedTextV3
    technology_drivers: List[SourcedItemV3] = Field(default_factory=list)
    vendor_dependencies: List[str] = Field(default_factory=list)
    operating_constraints: List[str] = Field(default_factory=list)
    recent_incident_signals: List[str] = Field(default_factory=list)


class IntelligenceClaimV3(BaseModel):
    claim_id: str
    claim: str
    claim_type: Literal["fact", "inference", "assumption", "scenario", "alternative_hypothesis"]
    confidence: ConfidenceAssessment
    sources: List[ClaimSource] = Field(default_factory=list)
    source_reliability_score: int | None = Field(default=None, ge=0, le=100)
    valid_for_domains: List[str] = Field(default_factory=list)
    related_towers: List[str] = Field(default_factory=list)


class IntelligenceReviewV3(BaseModel):
    human_review_status: Literal["pending", "reviewed", "approved", "rejected"] = "pending"
    approved_by: str | None = None
    approved_at: str | None = None
    review_notes: List[str] = Field(default_factory=list)


class IntelligenceMetadataV3(BaseModel):
    dossier_id: str
    schema_version: Literal["3.0"] = "3.0"
    created_at: str
    modified_at: str
    last_verified_at: str | None = None
    lang: str = "es"
    generated_by: str = "assessment_engine"
    prompt_version: str | None = None
    timeliness: TimelinessWindow | None = None


class ClientDossierV3(BaseModel):
    version: Literal["3.0"] = "3.0"
    client_name: str
    metadata: IntelligenceMetadataV3
    profile: ClientProfileV3
    regulatory_context: List[RegulatoryFrameworkV3] = Field(default_factory=list)
    business_context: BusinessContextV3
    technology_context: TechnologyContextV3
    tower_overrides: Dict[str, TowerContextV3] = Field(default_factory=dict)
    claims: List[IntelligenceClaimV3] = Field(default_factory=list)
    review: IntelligenceReviewV3 = Field(default_factory=IntelligenceReviewV3)
    extensions: Dict[str, Any] = Field(default_factory=dict)
