from typing import Any, Dict

from pydantic import BaseModel, Field

from .common import VersionedPayload


class GlobalIssue(BaseModel):
    """Represents a single global-scope issue identified by static analysis.

    A Pydantic data model for issues that are not specific to a single line of
    code but instead relate to the overall structure, consistency, or
    configuration of the analyzed codebase. For example, a missing configuration
    file or an inconsistent naming convention across multiple modules.

    Attributes:
        severity (str): The severity level of the issue (e.g., 'ERROR', 'WARNING').
        type (str): A unique, machine-readable identifier for the issue category.
        sections (list[str]): A collection of identifiers, such as file paths or
            module names, where the issue is relevant.
        message (str): A human-readable description of the issue and its context.
        suggested_fix (str): An actionable, human-readable suggestion for resolving
            the issue.
    """

    severity: str
    type: str
    sections: list[str]
    message: str
    suggested_fix: str


class GlobalReviewDraft(BaseModel):
    """Represents a draft of a global review report for a specific artifact.

    This model aggregates findings from various automated and manual analyses,
    such as duplication checks, consistency validation, and style guide
    enforcement, into a single structured report.

    Attributes:
        artifact_type (str): The type of the artifact being reviewed (e.g.,
            'design_doc', 'api_spec').
        status (str): The current status of the review draft (e.g., 'in_progress',
            'completed').
        global_issues (list[GlobalIssue]): A list of high-level issues that apply
            to the entire artifact.
        duplication_findings (list[str]): A list of findings related to content
            duplication.
        consistency_findings (list[str]): A list of findings related to
            consistency across the artifact.
        style_findings (list[str]): A list of findings related to style guide
            violations.
        review_notes (list[str]): A list of general notes or comments from the
            reviewer.
    """

    artifact_type: str
    status: str
    global_issues: list[GlobalIssue]
    duplication_findings: list[str]
    consistency_findings: list[str]
    style_findings: list[str]
    review_notes: list[str]


class GlobalEdit(BaseModel):
    """{'docstring': 'Represent a single, atomic global configuration edit.'}."""

    path: str
    action: str
    value: Any
    reason: str


class GlobalRefinerDraft(BaseModel):
    """A data model for a proposed set of global content refinements.

    Encapsulates a collection of proposed global edits, the strategy guiding
    them, their current status, and any associated review notes.

    Attributes:
        status (str): The lifecycle status of the refinement draft (e.g., 'pending',
            'approved').
        editorial_strategy (str): A high-level description of the editorial
            approach guiding the edits.
        edits (list[GlobalEdit]): The sequence of specific `GlobalEdit` operations
            to be applied.
        review_notes (list[str]): A sequence of textual notes or comments from
            reviewers.
    """

    status: str
    editorial_strategy: str
    edits: list[GlobalEdit]
    review_notes: list[str]


class ExecutiveReportDraft(BaseModel):
    """A data model for the textual components of a draft executive report.

    This class defines the schema for a draft executive-level summary, serving
    as a data transfer object for its constituent sections.

    Attributes:
        executive_summary_text: The high-level summary of the report.
        burning_platform_text: The section describing the critical business problem
            or urgent need for action.
        tower_bottom_lines: A dictionary mapping a business unit or workstream
            identifier to its summary status.
        target_vision_text: The section describing the desired future state or
            strategic goal.
        roadmap_execution_text: The section outlining the implementation plan and
            timeline.
        executive_decisions_text: The section detailing key decisions required from
            the report's audience.
    """

    executive_summary_text: str
    burning_platform_text: str
    tower_bottom_lines: dict[str, str]
    target_vision_text: str
    roadmap_execution_text: str
    executive_decisions_text: str


class ExecutiveSummaryDraft(BaseModel):
    """Model a draft executive summary with a headline, narrative, and key business impacts."""

    headline: str
    narrative: str
    key_business_impacts: list[str]


class BurningPlatformItem(BaseModel):
    """Represents a single thematic issue in a 'burning platform' analysis."""

    theme: str
    business_risk: str
    root_causes: list[str]


class TowerBottomLineItem(BaseModel):
    """Represent a single data row for a tower's bottom-line summary."""

    id: str
    name: str
    score: str
    band: str
    status_color: str
    bottom_line: str


class EvolutionPrinciple(BaseModel):
    """Represents a single evolution principle, containing its title and description."""

    principle: str
    description: str


class StrategicPillar(BaseModel):
    """Represents a single strategic pillar for reporting.

    A data model encapsulating the name and a detailed description of a
    strategic pillar. Strategic pillars represent fundamental areas of focus
    within an organizational strategy.

    Attributes:
        pillar: The name or title of the strategic pillar.
        description: A detailed explanation of the pillar's scope and objectives.
    """

    pillar: str
    description: str


class TargetVisionDraft(BaseModel):
    r"""{'docstring': 'Represents a draft of a strategic target vision for a product or system.\n\nThis data model encapsulates the core components of a strategic vision,\nincluding its value proposition, the principles guiding its evolution, and the\nfoundational pillars that support the strategy.\n\nAttributes:\n    value_proposition: The central value statement defining the vision.\n    evolution_principles: A list of `EvolutionPrinciple` objects guiding\n        future development and adaptation.\n    strategic_pillars: A list of `StrategicPillar` objects that form the\n        foundational columns of the strategic vision.'}."""

    value_proposition: str
    evolution_principles: list[EvolutionPrinciple]
    strategic_pillars: list[StrategicPillar]


class ProgramDef(BaseModel):
    """A data model for a program's definition, including its name and description."""

    name: str
    description: str


class InitiativeDef(BaseModel):
    """Defines the static configuration for a single business initiative.

    This Pydantic model validates and structures the static definition of an
    initiative, typically sourced from a configuration file.

    Attributes:
        program: The parent program or portfolio to which the initiative belongs.
        title: The formal title of the initiative.
        business_case: A concise justification for the initiative's undertaking.
        start_month: The calendar month in which work is scheduled to begin,
            represented as an integer (1=January, 12=December).
        duration_months: The planned duration of the initiative, measured in whole
            months.
    """

    program: str
    title: str
    business_case: str
    start_month: int
    duration_months: int


class HorizonsDef(BaseModel):
    """Represents strategic initiatives categorized into distinct time horizons.

    This data model organizes initiatives into four sequential timeframes, ranging
    from immediate execution to long-term strategic projects spanning up to three
    years. Each horizon contains a list of corresponding initiatives.

    Attributes:
        quick_wins_0_3_months (list[InitiativeDef]): Initiatives scheduled for
            completion within the initial 0 to 3-month period.
        year_1_3_12_months (list[InitiativeDef]): Initiatives planned for the 3 to
            12-month timeframe.
        year_2_12_24_months (list[InitiativeDef]): Initiatives scheduled for the 12 to
            24-month timeframe.
        year_3_24_36_months (list[InitiativeDef]): Initiatives planned for the 24 to
            36-month timeframe.
    """

    quick_wins_0_3_months: list[InitiativeDef]
    year_1_3_12_months: list[InitiativeDef]
    year_2_12_24_months: list[InitiativeDef]
    year_3_24_36_months: list[InitiativeDef]


class ExecutionRoadmapDraft(BaseModel):
    """Represents a draft version of an execution roadmap.

    This model serves as a data container for the constituent parts of a roadmap
    draft, aggregating the planned programs and their corresponding time horizons.

    Attributes:
        programs: A list of `ProgramDef` objects included in the roadmap.
        horizons: A `HorizonsDef` object defining the temporal structure and
            intervals for the roadmap.
    """

    programs: list[ProgramDef]
    horizons: HorizonsDef


class ExecutiveDecisionItem(BaseModel):
    """Represent a single item requiring an executive decision."""

    decision_type: str
    action_required: str
    impact_if_delayed: str


class ExecutiveDecisionsDraft(BaseModel):
    """Model a draft of immediate executive decisions."""

    immediate_decisions: list[ExecutiveDecisionItem]


class GlobalReportDocumentMeta(BaseModel):
    """Represent the metadata structure for a global report document."""

    client: str
    date: str
    version: str


class GlobalReportPayload(VersionedPayload):
    """Represents the data payload for a comprehensive global report.

    Aggregates various components that constitute a global report into a single,
    structured container for data transfer and serialization. This class inherits
    versioning capabilities from `VersionedPayload`.

    Attributes:
        meta: Metadata associated with the global report document.
        executive_summary: The draft content for the executive summary section.
        burning_platform: A list of items outlining critical business challenges.
        intelligence_dossier: A dictionary containing intelligence data.
        heatmap: A list of raw heatmap data structured for direct client-side
            consumption, decoupling data generation from presentation logic.
        tower_bottom_lines: A list of bottom-line summaries from different
            business towers or departments.
        target_vision: The draft content for the target vision or future state section.
        execution_roadmap: The draft content for the strategic execution roadmap.
        executive_decisions: The draft content outlining executive decisions and
            action items.
        visuals: A dictionary mapping unique visual element identifiers to their
            data, such as a URL or a base64-encoded string.
    """

    meta: GlobalReportDocumentMeta
    executive_summary: ExecutiveSummaryDraft
    burning_platform: list[BurningPlatformItem]
    intelligence_dossier: dict = Field(default_factory=dict)
    heatmap: list[Any] = Field(
        default_factory=list
    )  # Raw heatmap data structured for direct consumption and client-side rendering, decoupling data generation from presentation logic.
    tower_bottom_lines: list[TowerBottomLineItem]
    target_vision: TargetVisionDraft
    execution_roadmap: ExecutionRoadmapDraft
    executive_decisions: ExecutiveDecisionsDraft
    visuals: Dict[str, str] = Field(default_factory=dict)
