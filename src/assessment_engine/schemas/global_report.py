from typing import Any, Dict

from pydantic import BaseModel, Field

from .common import VersionedPayload


class GlobalIssue(BaseModel):
    """Represents a single global issue identified during a code analysis.

    This class serves as a data container for an issue that pertains to the
    entire codebase or project, rather than a specific file or line number.

    Attributes:
        severity: The severity level of the issue, typically an enumerated
            string such as 'ERROR' or 'WARNING'.
        type: A machine-readable identifier categorizing the issue (e.g.,
            'UNUSED_DEPENDENCY').
        sections: A list of strings identifying the report sections or analysis
            phases where this issue is relevant.
        message: A human-readable description of the identified issue.
        suggested_fix: A human-readable, actionable recommendation for
            resolving the issue.
    """
    severity: str
    type: str
    sections: list[str]
    message: str
    suggested_fix: str


class GlobalReviewDraft(BaseModel):
    """Represents a draft of a global review for a software artifact.

    This data model aggregates all findings, issues, and metadata generated
    during a comprehensive, cross-cutting review process. It serves as the
    primary data structure for storing and communicating review outcomes before
    they are finalized.

    Attributes:
        artifact_type (str): The type of the artifact under review (e.g.,
            'design_doc', 'api_spec').
        status (str): The current status of the review draft (e.g., 'in_progress',
            'completed').
        global_issues (list[GlobalIssue]): High-level issues identified across the
            entire artifact.
        duplication_findings (list[str]): Specific findings related to content
            duplication.
        consistency_findings (list[str]): Findings related to inconsistencies
            in terminology, formatting, or logic.
        style_findings (list[str]): Findings related to violations of established
            style guides.
        review_notes (list[str]): General notes or comments from reviewers.
    """
    artifact_type: str
    status: str
    global_issues: list[GlobalIssue]
    duplication_findings: list[str]
    consistency_findings: list[str]
    style_findings: list[str]
    review_notes: list[str]


class GlobalEdit(BaseModel):
    """A data model representing a single, atomic global edit operation.

    This class defines the structure for a modification intended for widespread
    application, such as across multiple configuration files or data structures. It
    encapsulates the target location, the modification type, the new data, and
    the rationale for the change.

    Attributes:
        path (str): The locator for the item to be modified. This can be a file
            system path or a key path within a structured format (e.g.,
            'a.b.c' for nested objects).
        action (str): The type of operation to execute. Common values include
            'add', 'remove', or 'replace'.
        value (Any): The data associated with the action. For 'add' and
            'replace' operations, this is the new content. For a 'remove'
            operation, this field is typically ignored.
        reason (str): A human-readable justification for the edit, intended for
            logging, auditing, or review purposes.
    """
    path: str
    action: str
    value: Any
    reason: str


class GlobalRefinerDraft(BaseModel):
    """{'docstring': 'Represents a draft of global edits and the overarching strategy.'}."""
    status: str
    editorial_strategy: str
    edits: list[GlobalEdit]
    review_notes: list[str]


class ExecutiveReportDraft(BaseModel):
    """A data model for the textual components of a draft executive report.

    This Pydantic model defines the schema for the distinct sections that constitute
    a complete executive summary document.

    Attributes:
        executive_summary_text: The high-level summary of the report's content.
        burning_platform_text: A description of the critical business problem or
            "burning platform" being addressed.
        tower_bottom_lines: A mapping from organizational tower or team names to
            their respective summary statements.
        target_vision_text: The narrative describing the desired future state or
            strategic vision.
        roadmap_execution_text: The detailed plan for execution, including the
            project roadmap.
        executive_decisions_text: A summary of key decisions required from
            executive leadership.
    """
    executive_summary_text: str
    burning_platform_text: str
    tower_bottom_lines: dict[str, str]
    target_vision_text: str
    roadmap_execution_text: str
    executive_decisions_text: str


class ExecutiveSummaryDraft(BaseModel):
    """{'docstring': 'Model the data structure for a draft executive summary.'}."""
    headline: str
    narrative: str
    key_business_impacts: list[str]


class BurningPlatformItem(BaseModel):
    """Model a single 'burning platform' item, detailing its theme, business risk, and root causes."""
    theme: str
    business_risk: str
    root_causes: list[str]


class TowerBottomLineItem(BaseModel):
    """Represent a single entry in a tower's bottom line report."""
    id: str
    name: str
    score: str
    band: str
    status_color: str
    bottom_line: str


class EvolutionPrinciple(BaseModel):
    """Model an evolutionary principle with its name and description."""
    principle: str
    description: str


class StrategicPillar(BaseModel):
    """Model a strategic pillar with a name and a description."""
    pillar: str
    description: str


class TargetVisionDraft(BaseModel):
    """Defines the data model for a strategic target vision document.

    This Pydantic model provides a structured representation for the key components
    of a system's or product's long-term vision, including its core value,
    guiding principles, and foundational focus areas.

    Attributes:
        value_proposition (str): The central value statement articulating the primary
            benefit and purpose of the target vision.
        evolution_principles (list[EvolutionPrinciple]): A collection of tenets
            that guide and constrain development towards the target state.
        strategic_pillars (list[StrategicPillar]): The fundamental, high-level
            areas of focus or themes that constitute the core of the vision.
    """
    value_proposition: str
    evolution_principles: list[EvolutionPrinciple]
    strategic_pillars: list[StrategicPillar]


class ProgramDef(BaseModel):
    """Represent a program's definition."""
    name: str
    description: str


class InitiativeDef(BaseModel):
    """Model the definition of a single strategic initiative."""
    program: str
    title: str
    business_case: str
    start_month: int
    duration_months: int


class HorizonsDef(BaseModel):
    """Model strategic initiatives categorized into four distinct time horizons."""
    quick_wins_0_3_months: list[InitiativeDef]
    year_1_3_12_months: list[InitiativeDef]
    year_2_12_24_months: list[InitiativeDef]
    year_3_24_36_months: list[InitiativeDef]


class ExecutionRoadmapDraft(BaseModel):
    """Defines the data model for a draft execution roadmap.

    This class encapsulates the program definitions and time horizons that
    constitute a new roadmap.

    Attributes:
        programs: A list of `ProgramDef` objects defining the roadmap's scope.
        horizons: A `HorizonsDef` object defining the roadmap's timeframes.
    """
    programs: list[ProgramDef]
    horizons: HorizonsDef


class ExecutiveDecisionItem(BaseModel):
    """Represent a single decision item for an executive report."""
    decision_type: str
    action_required: str
    impact_if_delayed: str


class ExecutiveDecisionsDraft(BaseModel):
    """Represent a draft of executive-level decisions."""
    immediate_decisions: list[ExecutiveDecisionItem]


class GlobalReportDocumentMeta(BaseModel):
    """Represent the metadata for a global report document."""
    client: str
    date: str
    version: str


class GlobalReportPayload(VersionedPayload):
    """Represents the data contract for a global report payload.

    This class aggregates all data components that constitute a global report. It
    serves as the primary data transfer object (DTO) for services that produce
    or consume global report information.

    Attributes:
        meta (GlobalReportDocumentMeta): Metadata associated with the report document.
        executive_summary (ExecutiveSummaryDraft): Draft content for the executive
            summary section.
        burning_platform (list[BurningPlatformItem]): A list of items outlining
            critical business challenges or the 'burning platform'.
        intelligence_dossier (dict): A dictionary containing intelligence data, such
            as competitor analysis or market trends. Defaults to an empty dict.
        heatmap (list[Any]): Raw data payload intended for direct passthrough to a
            downstream heatmap rendering system. Defaults to an empty list.
        tower_bottom_lines (list[TowerBottomLineItem]): A list of summary statements
            or key takeaways from different business verticals ('towers').
        target_vision (TargetVisionDraft): Draft content describing the future state
            or target vision.
        execution_roadmap (ExecutionRoadmapDraft): Draft content for the strategic
            execution roadmap.
        executive_decisions (ExecutiveDecisionsDraft): Draft content outlining key
            executive decisions.
        visuals (Dict[str, str]): A mapping of visual asset identifiers to their
            string representations (e.g., URLs, base64 encoded data). Defaults to
            an empty dict.
    """
    meta: GlobalReportDocumentMeta
    executive_summary: ExecutiveSummaryDraft
    burning_platform: list[BurningPlatformItem]
    intelligence_dossier: dict = Field(default_factory=dict)
    heatmap: list[Any] = Field(default_factory=list)  # Raw heatmap data payload intended for direct passthrough. This allows downstream systems to apply their own specific aggregation and rendering logic.
    tower_bottom_lines: list[TowerBottomLineItem]
    target_vision: TargetVisionDraft
    execution_roadmap: ExecutionRoadmapDraft
    executive_decisions: ExecutiveDecisionsDraft
    visuals: Dict[str, str] = Field(default_factory=dict)
