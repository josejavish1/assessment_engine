from pydantic import BaseModel, Field

from .common import VersionedPayload


class DealFlash(BaseModel):
    """Model a deal flash summary with the customer's purchase driver and the deal's win theme."""
    purchase_driver: str
    ntt_win_theme: str


class CommercialSummaryDraft(BaseModel):
    """Defines the data schema for a commercial summary draft."""
    deal_flash: DealFlash
    why_now_bullets: list[str]
    how_we_win_bullets: list[str]
    estimated_tam: str


class GtmStrategy(BaseModel):
    """Represents a data model for Go-to-Market (GTM) strategies.

    This model encapsulates distinct strategic approaches for product introduction and
    market scaling. Each attribute holds a textual description of a specific,
    well-defined GTM tactic.

    Attributes:
        trojan_horse (str): Describes a strategy where a free or low-cost product
            is offered to establish a market presence, with the intent of
            upselling or cross-selling premium features or related products.
        self_funded_transformation (str): Describes a strategy where initial
            revenue from a core product is used to finance the development and
            market introduction of new, more transformative products.
        lock_in (str): Describes a strategy focused on generating high switching
            costs for customers, making it difficult or expensive for them to
            migrate to a competitor's offerings.
    """
    trojan_horse: str
    self_funded_transformation: str
    lock_in: str


class StakeholderMatrixItem(BaseModel):
    """Represent a single entry in a stakeholder communication matrix."""
    role: str
    focus: str
    message: str


class AccountDirectorOutput(BaseModel):
    r"""{'docstring': "Data model for the consolidated output of an Account Director's analysis.\n\n    Attributes:\n        commercial_summary: A structured representation of the commercial summary draft.\n        gtm_strategy: The proposed Go-To-Market (GTM) strategy.\n        stakeholder_matrix: A list that maps key stakeholders to their designated\n            project roles."}."""
    commercial_summary: CommercialSummaryDraft
    gtm_strategy: GtmStrategy
    stakeholder_matrix: list[StakeholderMatrixItem]


class OpportunityPipelineItem(BaseModel):
    """{'docstring': 'Model a single entry in a commercial opportunity pipeline.'}."""
    initiative: str
    tower_origin: str
    vendor_cosell: str
    revenue_type: str
    estimated_tcv: str
    cost_of_inaction: str
    client_objection: str
    objection_handling: str


class PresalesArchitectOutput(BaseModel):
    """Represents the structured output of a presales architect's analysis.

    This data model encapsulates a pipeline of sales opportunities, typically
    derived from the analysis of unstructured data such as customer communications.

    Attributes:
        opportunities_pipeline: A list of `OpportunityPipelineItem` objects, each
            detailing a single identified sales opportunity.
    """
    opportunities_pipeline: list[OpportunityPipelineItem]


class ContextAndWhy(BaseModel):
    """Represent the context and justification for a decision or action."""
    origin: str
    cost_of_inaction: str


class SolutionAndWhat(BaseModel):
    """Models the desired outcome and key success metric for a solution."""
    target_state: str
    north_star_metric: str


class EngagementManagerOutput(BaseModel):
    """Encapsulates the context ('why') and solution ('what') of a strategic proposal."""
    context_and_why: ContextAndWhy
    solution_and_what: SolutionAndWhat


class ScopeAndHow(BaseModel):
    """Defines the scope, deliverables, and exclusions for a project."""
    phases: list[str]
    deliverables: list[str]
    out_of_scope: list[str]


class DeliveryTeam(BaseModel):
    """Model a delivery team with its associated member roles."""
    team_roles: list[str]


class LeadSolutionsArchitectOutput(BaseModel):
    """Represents the structured output from a Lead Solutions Architect.

    Encapsulates the key deliverables resulting from an architect's analysis
    of a customer's technical and business requirements. This model serves as a
    formal specification for the proposed solution.

    Attributes:
        scope_and_how (ScopeAndHow): The detailed technical scope and
            implementation plan.
        delivery_team (DeliveryTeam): The proposed structure and composition of the
            delivery team.
        ai_transformation_strategy (str): A high-level summary of the AI
            transformation strategy.
    """
    scope_and_how: ScopeAndHow
    delivery_team: DeliveryTeam
    ai_transformation_strategy: str


class GovernanceAndAssumptions(BaseModel):
    """Represents the governance model and key assumptions for a system or project.

    Attributes:
        governance_model: The identifier or description of the governance model.
        assumptions: A list of strings, each articulating a key assumption.
    """
    governance_model: str
    assumptions: list[str]


class RiskManagementItem(BaseModel):
    r"""{'docstring': 'Represent a single risk and its corresponding mitigation.\n\nAttributes:\n    risk: A description of the identified risk.\n    mitigation: The plan or action to mitigate the identified risk.'}."""
    risk: str
    mitigation: str


class DeliveryAndRiskDirectorOutput(BaseModel):
    """Encapsulates the consolidated output for project delivery and risk assessment.

    This data model serves as a structured container for the outcomes of governance,
    risk management, and activation planning processes.

    Attributes:
        governance_and_assumptions: The project governance framework and its
            underlying assumptions.
        risk_management: A list of identified risks, each with its corresponding
            management strategy.
        activation_plan: An ordered list of strings describing the sequential steps for
            project activation or deployment.
    """
    governance_and_assumptions: GovernanceAndAssumptions
    risk_management: list[RiskManagementItem]
    activation_plan: list[str]


class WhyNttData(BaseModel):
    """Represent the 'Why NTT DATA' section of a commercial document."""
    accelerators: list[str]
    partnerships: str


class InvestmentAndTimeline(BaseModel):
    """Model the estimated duration and Total Contract Value (TCV) range for a project."""
    estimated_duration: str
    tcv_range: str


class SalesPartnerOutput(BaseModel):
    """Encapsulates the structured commercial output of a sales partner analysis.

    This data model aggregates the primary components of a commercial proposal,
    including the value proposition, financial investment, and an executive
    summary.

    Attributes:
        why_ntt_data: A structured representation of the value proposition and
            rationale for selecting the partner.
        investment_and_timeline: A detailed breakdown of the project's financial
            investment and projected timeline.
        executive_synthesis: A concise summary of the proposal, intended for
            executive review.
    """
    why_ntt_data: WhyNttData
    investment_and_timeline: InvestmentAndTimeline
    executive_synthesis: str


class ProposalDraft(BaseModel):
    """Represents the structured data model for a commercial proposal draft.

    This Pydantic model defines all the required sections and their corresponding
    data structures to ensure a complete and valid proposal document is generated.

    Attributes:
        initiative_name (str): The official name of the proposed initiative.
        context_and_why (ContextAndWhy): Section detailing the background, problem,
            and rationale.
        solution_and_what (SolutionAndWhat): Section describing the proposed
            solution's components.
        scope_and_how (ScopeAndHow): Section defining the project's boundaries and
            methodology.
        delivery_team (DeliveryTeam): Details of the team proposed to execute the
            project.
        ai_transformation_strategy (str): The strategy for leveraging AI within the
            initiative.
        governance_and_assumptions (GovernanceAndAssumptions): The governance
            framework and key assumptions.
        risk_management (list[RiskManagementItem]): A list of identified risks and
            their mitigation plans.
        activation_plan (list[str]): A high-level plan or list of steps for project
            activation.
        why_ntt_data (WhyNttData): The value proposition for choosing NTT DATA as
            the partner.
        investment_and_timeline (InvestmentAndTimeline): The required financial
            investment and project timeline.
        executive_synthesis (str): A concise summary of the proposal for
            executives.
    """
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
    """Models the metadata for a commercial document.

    Attributes:
        client: The name or identifier of the associated client.
        date: The publication date of the document in ISO 8601 format (YYYY-MM-DD).
        version: The document version string, preferably following semantic
            versioning (e.g., "1.0.0").
    """
    client: str
    date: str
    version: str


class CommercialPayload(VersionedPayload):
    """Models the comprehensive commercial data payload for a document.

    This class aggregates various components of a commercial strategy, including
    summaries, go-to-market plans, stakeholder analyses, and sales pipelines.
    It inherits versioning capabilities from its parent class.

    Attributes:
        meta (CommercialDocumentMeta): Metadata associated with the commercial
            document.
        commercial_summary (CommercialSummaryDraft): The draft summary of the
            commercial aspects.
        gtm_strategy (GtmStrategy): The go-to-market strategy details.
        stakeholder_matrix (list[StakeholderMatrixItem]): A list of key
            stakeholders and their roles.
        opportunities_pipeline (list[OpportunityPipelineItem]): The pipeline of
            business opportunities.
        proactive_proposals (list[ProposalDraft]): A collection of drafted
            proposals.
        intelligence_dossier (dict): A flexible container for competitive and
            market intelligence.
    """
    meta: CommercialDocumentMeta
    commercial_summary: CommercialSummaryDraft
    gtm_strategy: GtmStrategy
    stakeholder_matrix: list[StakeholderMatrixItem] = Field(default_factory=list)
    opportunities_pipeline: list[OpportunityPipelineItem]
    proactive_proposals: list[ProposalDraft]
    intelligence_dossier: dict = Field(default_factory=dict)
