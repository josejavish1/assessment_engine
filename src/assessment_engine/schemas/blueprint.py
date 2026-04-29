from pydantic import BaseModel, Field, ConfigDict
from .common import VersionedPayload

class HealthCheckAsIs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    target_state: str = Field(..., alias="capability")
    risk_observed: str = Field(..., alias="finding")
    impact: str = Field(..., alias="business_risk")

class TargetArchitectureToBe(BaseModel):
    vision: str
    design_principles: list[str]

class ProjectToDo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    initiative: str = Field(..., alias="name")
    expected_outcome: str = Field(..., alias="business_case")
    objective: str = Field(..., alias="tech_objective")
    deliverables: list[str]
    sizing: str
    duration: str

class PillarBlueprintDraft(BaseModel):
    pilar_id: str
    pilar_name: str
    score: float = 0.0
    target_score: float = 4.0
    health_check_asis: list[HealthCheckAsIs]
    target_architecture_tobe: TargetArchitectureToBe
    projects_todo: list[ProjectToDo]

class ExecutiveSnapshot(BaseModel):
    bottom_line: str
    decisions: list[str]
    cost_of_inaction: str
    structural_risks: list[str]
    business_impact: str
    operational_benefits: list[str]
    transformation_complexity: str

class CrossCapabilitiesAnalysis(BaseModel):
    common_deficiency_patterns: list[str]
    transformation_paradigm: str
    critical_technical_debt: str

class RoadmapWave(BaseModel):
    wave: str
    projects: list[str]

class ExternalDependency(BaseModel):
    project: str
    depends_on: str
    reason: str

class OrchestratorBlueprintDraft(VersionedPayload):
    executive_snapshot: ExecutiveSnapshot
    cross_capabilities_analysis: CrossCapabilitiesAnalysis
    roadmap: list[RoadmapWave]
    external_dependencies: list[ExternalDependency]

class BlueprintDocumentMeta(BaseModel):
    client_name: str
    tower_name: str
    tower_code: str
    financial_tier: str
    transformation_horizon: str

class BlueprintPayload(OrchestratorBlueprintDraft):
    document_meta: BlueprintDocumentMeta
    pillars_analysis: list[PillarBlueprintDraft]
