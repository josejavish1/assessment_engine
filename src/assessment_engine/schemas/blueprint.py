from pydantic import BaseModel, ConfigDict, Field

from .common import VersionedPayload


class HealthCheckAsIs(BaseModel):
    """Represents the observed state of a system component from a health check.

    This model defines the data structure for the "as-is" condition identified
    during a system health assessment. It encapsulates the capability under review,
    the specific risk or finding that was observed, and the corresponding business
    impact. The model supports instantiation via field names or their designated
    aliases.

    Attributes:
        target_state: The target capability or desired state being assessed.
            Populated by the alias 'capability'.
        risk_observed: The specific finding or risk identified during the health
            check. Populated by the alias 'finding'.
        impact: The potential business impact associated with the observed risk.
            Populated by the alias 'business_risk'.
    """
    model_config = ConfigDict(populate_by_name=True)

    target_state: str = Field(..., alias="capability")
    risk_observed: str = Field(..., alias="finding")
    impact: str = Field(..., alias="business_risk")


class TargetArchitectureToBe(BaseModel):
    r"""{'docstring': "Represents the target 'to-be' state of a system architecture.\n\nThis data model encapsulates the strategic vision and foundational design\nprinciples that guide the evolution of a system towards its desired future state.\n\nAttributes:\n    vision: A string articulating the strategic goals and desired future state\n        of the system.\n    design_principles: A list of strings, where each string is a fundamental\n        tenet or constraint that governs design and implementation decisions."}."""
    vision: str
    design_principles: list[str]


class ProjectToDo(BaseModel):
    """Represents a structured plan for a project or initiative.

    A Pydantic model that defines the schema for a project task. The model is
    configured to allow instantiation using either field names or their specified
    aliases, facilitating deserialization from data sources that use alternative
    naming conventions.

    Attributes:
        initiative (str): The name or title of the project. Aliased as 'name'.
        expected_outcome (str): A description of the anticipated business value or
            result. Aliased as 'business_case'.
        objective (str): The specific technical goal to be achieved. Aliased as
            'tech_objective'.
        deliverables (list[str]): A list of concrete outputs or results required for
            project completion.
        sizing (str): An estimation of the project's effort, typically expressed
            as a T-shirt size (e.g., 'S', 'M', 'L').
        duration (str): The estimated time required for completion (e.g.,
            '2 weeks').
    """
    model_config = ConfigDict(populate_by_name=True)

    initiative: str = Field(..., alias="name")
    expected_outcome: str = Field(..., alias="business_case")
    objective: str = Field(..., alias="tech_objective")
    deliverables: list[str]
    sizing: str
    duration: str


class PillarBlueprintDraft(BaseModel):
    """Represents a draft of a strategic blueprint for a single pillar.

    This Pydantic model captures the complete state of a pillar's assessment,
    including its current health, target architecture, and the projects
    required to transition to the target state.

    Attributes:
        pilar_id: A unique string identifier for the pillar.
        pilar_name: The human-readable name of the pillar.
        score: The calculated health score for the pillar's current state.
            Defaults to 0.0.
        target_score: The desired target health score for the pillar.
            Defaults to 4.0.
        health_check_asis: A list of `HealthCheckAsIs` models detailing the
            current state ("As-Is") assessments.
        target_architecture_tobe: A `TargetArchitectureToBe` model defining the
            desired future state ("To-Be") architecture.
        projects_todo: A list of `ProjectToDo` models outlining the work
            required to transition from the current state to the target
            architecture.
    """
    pilar_id: str
    pilar_name: str
    score: float = 0.0
    target_score: float = 4.0
    health_check_asis: list[HealthCheckAsIs]
    target_architecture_tobe: TargetArchitectureToBe
    projects_todo: list[ProjectToDo]


class ExecutiveSnapshot(BaseModel):
    r"""{'docstring': "A data model representing a high-level summary for executive review.\n\n    This model structures the key information points required for an executive to\n    make a strategic decision regarding a proposal or project.\n\n    Attributes:\n        bottom_line (str): The primary conclusion or key takeaway of the proposal.\n        decisions (list[str]): A collection of key decisions that require\n            executive action or approval.\n        cost_of_inaction (str): A description of the negative consequences or\n            missed opportunities if the proposed action is not taken.\n        structural_risks (list[str]): A list of potential risks related to the\n            project's foundational assumptions, dependencies, or architecture.\n        business_impact (str): A summary of the anticipated positive effects on the\n            business if the proposal is implemented.\n        operational_benefits (list[str]): A list of specific, tangible\n            improvements to business operations.\n        transformation_complexity (str): An assessment of the difficulty and scope\n            of the proposed change (e.g., 'Low', 'Medium', 'High')."}."""
    bottom_line: str
    decisions: list[str]
    cost_of_inaction: str
    structural_risks: list[str]
    business_impact: str
    operational_benefits: list[str]
    transformation_complexity: str


class CrossCapabilitiesAnalysis(BaseModel):
    """Represent the consolidated findings from a cross-capability system analysis."""
    common_deficiency_patterns: list[str]
    transformation_paradigm: str
    critical_technical_debt: str


class RoadmapWave(BaseModel):
    """Represent a single wave or time period within a product roadmap."""
    wave: str
    projects: list[str]


class ExternalDependency(BaseModel):
    """Represent an external dependency between two projects."""
    project: str
    depends_on: str
    reason: str


class OrchestratorBlueprintDraft(VersionedPayload):
    r"""{'docstring': 'Represents a draft version of a strategic orchestration blueprint.\n\n    A data container that aggregates the core components of a strategic plan\n    proposal prior to its finalization. This class inherits from `VersionedPayload`\n    to enable version tracking of the draft.\n\n    Attributes:\n        executive_snapshot: An `ExecutiveSnapshot` providing a high-level summary\n            for leadership review.\n        cross_capabilities_analysis: A `CrossCapabilitiesAnalysis` detailing the\n            interactions and synergies among different functional capabilities.\n        roadmap: A sequence of `RoadmapWave` objects that define the phased\n            implementation plan.\n        external_dependencies: A sequence of `ExternalDependency` objects\n            enumerating requirements from or commitments to external teams or\n            systems.'}."""
    executive_snapshot: ExecutiveSnapshot
    cross_capabilities_analysis: CrossCapabilitiesAnalysis
    roadmap: list[RoadmapWave]
    external_dependencies: list[ExternalDependency]


class BlueprintDocumentMeta(BaseModel):
    """Defines the data model for the metadata of a blueprint document."""
    client_name: str
    tower_name: str
    tower_code: str
    financial_tier: str
    transformation_horizon: str


class BlueprintPayload(OrchestratorBlueprintDraft):
    """Bundle an orchestrator blueprint draft with its document metadata and pillar analysis."""
    document_meta: BlueprintDocumentMeta
    pillars_analysis: list[PillarBlueprintDraft]
