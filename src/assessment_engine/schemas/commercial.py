from pydantic import BaseModel, Field

from .common import VersionedPayload


class DealFlash(BaseModel):
    purchase_driver: str
    ntt_win_theme: str


class CommercialSummaryDraft(BaseModel):
    deal_flash: DealFlash
    why_now_bullets: list[str]
    how_we_win_bullets: list[str]
    estimated_tam: str


class GtmStrategy(BaseModel):
    trojan_horse: str
    self_funded_transformation: str
    lock_in: str


class StakeholderMatrixItem(BaseModel):
    role: str
    focus: str
    message: str


class AccountDirectorOutput(BaseModel):
    commercial_summary: CommercialSummaryDraft
    gtm_strategy: GtmStrategy
    stakeholder_matrix: list[StakeholderMatrixItem]


class OpportunityPipelineItem(BaseModel):
    initiative: str
    tower_origin: str
    vendor_cosell: str
    revenue_type: str
    estimated_tcv: str
    cost_of_inaction: str
    client_objection: str
    objection_handling: str


class PresalesArchitectOutput(BaseModel):
    opportunities_pipeline: list[OpportunityPipelineItem]


class ContextAndWhy(BaseModel):
    origin: str
    cost_of_inaction: str


class SolutionAndWhat(BaseModel):
    target_state: str
    north_star_metric: str


class EngagementManagerOutput(BaseModel):
    context_and_why: ContextAndWhy
    solution_and_what: SolutionAndWhat


class ScopeAndHow(BaseModel):
    phases: list[str]
    deliverables: list[str]
    out_of_scope: list[str]


class DeliveryTeam(BaseModel):
    team_roles: list[str]


class LeadSolutionsArchitectOutput(BaseModel):
    scope_and_how: ScopeAndHow
    delivery_team: DeliveryTeam
    ai_transformation_strategy: str


class GovernanceAndAssumptions(BaseModel):
    governance_model: str
    assumptions: list[str]


class RiskManagementItem(BaseModel):
    risk: str
    mitigation: str


class DeliveryAndRiskDirectorOutput(BaseModel):
    governance_and_assumptions: GovernanceAndAssumptions
    risk_management: list[RiskManagementItem]
    activation_plan: list[str]


class WhyNttData(BaseModel):
    accelerators: list[str]
    partnerships: str


class InvestmentAndTimeline(BaseModel):
    estimated_duration: str
    tcv_range: str


class SalesPartnerOutput(BaseModel):
    why_ntt_data: WhyNttData
    investment_and_timeline: InvestmentAndTimeline
    executive_synthesis: str


class ProposalDraft(BaseModel):
    initiative_name: str
    context_and_why: ContextAndWhy
    solution_and_what: SolutionAndWhat
    scope_and_how: ScopeAndHow
    delivery_team: DeliveryTeam
    ai_transformation_strategy: str
    governance_and_assumptions: GovernanceAndAssumptions
    risk_management: list[RiskManagementItem]
    activation_plan: list[str]
    why_ntt_data: WhyNttData
    investment_and_timeline: InvestmentAndTimeline
    executive_synthesis: str


class CommercialDocumentMeta(BaseModel):
    client: str
    date: str
    version: str


class CommercialPayload(VersionedPayload):
    meta: CommercialDocumentMeta
    commercial_summary: CommercialSummaryDraft
    gtm_strategy: GtmStrategy
    stakeholder_matrix: list[StakeholderMatrixItem] = Field(default_factory=list)
    opportunities_pipeline: list[OpportunityPipelineItem]
    proactive_proposals: list[ProposalDraft]
    intelligence_dossier: dict = Field(default_factory=dict)
