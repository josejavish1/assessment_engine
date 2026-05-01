from pydantic import BaseModel, Field
from typing import Dict, Any
from .common import VersionedPayload

class GlobalIssue(BaseModel):
    severity: str
    type: str
    sections: list[str]
    message: str
    suggested_fix: str

class GlobalReviewDraft(BaseModel):
    artifact_type: str
    status: str
    global_issues: list[GlobalIssue]
    duplication_findings: list[str]
    consistency_findings: list[str]
    style_findings: list[str]
    review_notes: list[str]

class GlobalEdit(BaseModel):
    path: str
    action: str
    value: Any
    reason: str

class GlobalRefinerDraft(BaseModel):
    status: str
    editorial_strategy: str
    edits: list[GlobalEdit]
    review_notes: list[str]

class ExecutiveReportDraft(BaseModel):
    executive_summary_text: str
    burning_platform_text: str
    tower_bottom_lines: dict[str, str]
    target_vision_text: str
    roadmap_execution_text: str
    executive_decisions_text: str

class ExecutiveSummaryDraft(BaseModel):
    headline: str
    narrative: str
    key_business_impacts: list[str]

class BurningPlatformItem(BaseModel):
    theme: str
    business_risk: str
    root_causes: list[str]

class TowerBottomLineItem(BaseModel):
    id: str
    name: str
    score: str
    band: str
    status_color: str
    bottom_line: str

class EvolutionPrinciple(BaseModel):
    principle: str
    description: str

class StrategicPillar(BaseModel):
    pillar: str
    description: str

class TargetVisionDraft(BaseModel):
    value_proposition: str
    evolution_principles: list[EvolutionPrinciple]
    strategic_pillars: list[StrategicPillar]

class ProgramDef(BaseModel):
    name: str
    description: str

class InitiativeDef(BaseModel):
    program: str
    title: str
    business_case: str
    start_month: int
    duration_months: int

class HorizonsDef(BaseModel):
    quick_wins_0_3_months: list[InitiativeDef]
    year_1_3_12_months: list[InitiativeDef]
    year_2_12_24_months: list[InitiativeDef]
    year_3_24_36_months: list[InitiativeDef]

class ExecutionRoadmapDraft(BaseModel):
    programs: list[ProgramDef]
    horizons: HorizonsDef

class ExecutiveDecisionItem(BaseModel):
    decision_type: str
    action_required: str
    impact_if_delayed: str

class ExecutiveDecisionsDraft(BaseModel):
    immediate_decisions: list[ExecutiveDecisionItem]

class GlobalReportDocumentMeta(BaseModel):
    client: str
    date: str
    version: str

class GlobalReportPayload(VersionedPayload):
    meta: GlobalReportDocumentMeta
    executive_summary: ExecutiveSummaryDraft
    burning_platform: list[BurningPlatformItem]
    intelligence_dossier: dict = Field(default_factory=dict)
    heatmap: list[Any] = Field(default_factory=list) # Raw heatmap data passthrough
    tower_bottom_lines: list[TowerBottomLineItem]
    target_vision: TargetVisionDraft
    execution_roadmap: ExecutionRoadmapDraft
    executive_decisions: ExecutiveDecisionsDraft
    visuals: Dict[str, str] = Field(default_factory=dict)
