from typing import List, Optional
from pydantic import BaseModel, Field
from .common import BaseDraftModel, VersionedPayload

class MaturityScoreProfile(BaseModel):
    profile_intro: str
    scoring_method_note: str
    radar_chart: str = ""
    pillars: List[dict] = Field(default_factory=list) # Pillars will be mapped from Blueprint

class ExecutiveSummaryAnnex(BaseModel):
    global_score: str
    global_band: str
    target_maturity: str
    headline: str
    summary_body: str
    message_strength: str = "Fortalezas clave identificadas en el entorno."
    message_gap: str = "Principales áreas de mejora y deuda técnica."
    message_bottleneck: str = "Cuellos de botella operativos que limitan el negocio."
    key_business_impacts: List[str]

class AsIsAnnex(BaseModel):
    narrative: str
    strengths: List[str]
    gaps: List[str]
    operational_impacts: List[str]

class ToBeAnnex(BaseModel):
    vision: str
    design_principles: List[str]

class RiskItemAnnex(BaseModel):
    risk: str
    impact: str
    probability: str
    mitigation_summary: str

class RisksAnnex(BaseModel):
    introduction: str
    risks: List[RiskItemAnnex]
    closing_summary: str = ""

class GapRowAnnex(BaseModel):
    pillar: str
    as_is_summary: str
    target_state: str
    key_gap: str

class GapAnnex(BaseModel):
    introduction: str
    target_capabilities: List[str]
    gap_rows: List[GapRowAnnex]
    closing_summary: str = ""

class InitiativeAnnex(BaseModel):
    sequence: int
    initiative: str
    objective: str
    priority: str
    expected_outcome: str
    dependencies_display: str

class TodoAnnex(BaseModel):
    introduction: str
    priority_initiatives: List[InitiativeAnnex]
    closing_summary: str = ""

class ConclusionAnnex(BaseModel):
    final_assessment: str
    executive_message: str
    priority_focus_areas: List[str]
    closing_statement: str

class AnnexSections(BaseModel):
    asis: AsIsAnnex
    tobe: ToBeAnnex
    gap: GapAnnex
    todo: TodoAnnex
    risks: RisksAnnex
    conclusion: ConclusionAnnex

class DomainIntroduction(BaseModel):
    introduction_paragraph: str
    technological_domain: str
    domain_objective: str
    evaluated_capabilities: List[str]
    included_components: List[str]

class AnnexPayload(VersionedPayload):
    document_meta: dict
    executive_summary: ExecutiveSummaryAnnex
    domain_introduction: DomainIntroduction
    pillar_score_profile: MaturityScoreProfile
    sections: AnnexSections
