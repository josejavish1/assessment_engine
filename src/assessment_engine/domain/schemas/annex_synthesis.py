from typing import List

from pydantic import BaseModel, Field

from .common import VersionedPayload


class MaturityScoreProfile(BaseModel):
    r"""{'docstring': 'Represents a maturity score profile for a given assessment.\n\n    This data model encapsulates introductory text, scoring methodology notes,\na radar chart visualization, and a detailed breakdown of scoring pillars\nderived from a blueprint definition.\n\n    Attributes:\n        profile_intro: Introductory text for the maturity score profile.\n        scoring_method_note: An explanatory note on the scoring methodology used.\n        radar_chart: Data for a radar chart visualization, typically a\n            base64-encoded image or a data URI. Defaults to an empty string.\n        pillars: A list of dictionaries, where each dictionary represents a\n            scoring pillar. The attributes for each pillar are programmatically\n            mapped from a corresponding blueprint definition.'}."""

    profile_intro: str
    scoring_method_note: str
    radar_chart: str = ""
    pillars: List[dict] = Field(
        default_factory=list
    )  # Pillar attributes are programmatically mapped from the corresponding Blueprint definition.


class ExecutiveSummaryAnnex(BaseModel):
    """A data model for an executive summary annex.

    This model encapsulates the structured data required to generate an executive
    summary section of a report, including scores, maturity targets, narrative
    elements, and key business impacts.

    Attributes:
        global_score (str): The overall calculated score for the assessment.
        global_band (str): The performance band corresponding to the global score.
        target_maturity (str): The desired or target maturity level.
        headline (str): The main headline for the executive summary.
        summary_body (str): The main narrative content of the summary.
        message_strength (str): The introductory message for the strengths section.
        message_gap (str): The introductory message for the improvement areas section.
        message_bottleneck (str): The introductory message for the bottlenecks section.
        key_business_impacts (List[str]): A list of key identified business impacts.
    """

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
    """Model an As-Is analysis annex, capturing narrative, strengths, gaps, and operational impacts."""

    narrative: str
    strengths: List[str]
    gaps: List[str]
    operational_impacts: List[str]


class ToBeAnnex(BaseModel):
    """Model the vision and design principles for a target system."""

    vision: str
    design_principles: List[str]


class RiskItemAnnex(BaseModel):
    """Model a single, structured risk item for document annexes."""

    risk: str
    impact: str
    probability: str
    mitigation_summary: str


class RisksAnnex(BaseModel):
    """A data model representing the risks annex of a document.

    Attributes:
        introduction: The introductory text for the risks annex.
        risks: A list of `RiskItemAnnex` objects, where each object details a
            specific risk.
        closing_summary: An optional concluding summary for the risks annex.
            Defaults to an empty string if not provided.
    """

    introduction: str
    risks: List[RiskItemAnnex]
    closing_summary: str = ""


class GapRowAnnex(BaseModel):
    """Model a single gap analysis entry, including the pillar, current state, target state, and the identified gap."""

    pillar: str
    as_is_summary: str
    target_state: str
    key_gap: str


class GapAnnex(BaseModel):
    """A data model for a structured gap analysis annex.

    This model serves as a data contract for the output of a capability gap
    analysis. It encapsulates the introductory context, the scope of capabilities
    under review, a detailed breakdown of identified gaps, and a final summary.

    Attributes:
        introduction: The introductory text providing context for the analysis.
        target_capabilities: A list of strings identifying the capabilities
            being assessed.
        gap_rows: A list of `GapRowAnnex` objects, each detailing a specific
            identified gap.
        closing_summary: A concluding summary of the analysis findings; defaults
            to an empty string.
    """

    introduction: str
    target_capabilities: List[str]
    gap_rows: List[GapRowAnnex]
    closing_summary: str = ""


class InitiativeAnnex(BaseModel):
    """Model a single strategic initiative within a document annex."""

    sequence: int
    initiative: str
    objective: str
    priority: str
    expected_outcome: str
    dependencies_display: str


class TodoAnnex(BaseModel):
    r"""{'docstring': 'Represents a structured TODO annex containing key initiatives.\n\n    This model organizes a collection of priority initiatives within a larger\n    document structure, framed by an introduction and an optional closing summary.\n\n    Attributes:\n        introduction (str): The introductory text or overview for the annex.\n        priority_initiatives (List[InitiativeAnnex]): A sequence of detailed\n            priority initiatives.\n        closing_summary (str): An optional concluding summary. Defaults to an\n            empty string.'}."""

    introduction: str
    priority_initiatives: List[InitiativeAnnex]
    closing_summary: str = ""


class ConclusionAnnex(BaseModel):
    """Represents the concluding annex of a synthesized report.

    This data model encapsulates the final assessment, executive summary, key focus
    areas, and a closing statement for a comprehensive report.

    Attributes:
        final_assessment: A conclusive, high-level judgment based on the report's
            findings.
        executive_message: A condensed summary of the report's most critical
            information tailored for an executive audience.
        priority_focus_areas: A list of key areas identified as requiring
            immediate attention or action.
        closing_statement: A formal, concluding remark to end the report.
    """

    final_assessment: str
    executive_message: str
    priority_focus_areas: List[str]
    closing_statement: str


class AnnexSections(BaseModel):
    """Model a complete collection of structured annex sections."""

    asis: AsIsAnnex
    tobe: ToBeAnnex
    gap: GapAnnex
    todo: TodoAnnex
    risks: RisksAnnex
    conclusion: ConclusionAnnex


class DomainIntroduction(BaseModel):
    """A data model for the introductory section of a technological domain evaluation.

    This model encapsulates the descriptive metadata for a technology domain, defining
    its purpose, scope, and the specific capabilities and components under evaluation.

    Attributes:
        introduction_paragraph: A free-text narrative introducing the technological
            domain.
        technological_domain: The formal name of the technological area being
            evaluated.
        domain_objective: A concise statement of the primary goal for evaluating
            this domain.
        evaluated_capabilities: A sequence of specific capabilities or features
            assessed within the domain.
        included_components: A sequence of components, systems, or tools included
            in the evaluation.
    """

    introduction_paragraph: str
    technological_domain: str
    domain_objective: str
    evaluated_capabilities: List[str]
    included_components: List[str]


class AnnexPayload(VersionedPayload):
    """Represents the data payload required for annex document synthesis.

    This class aggregates all components necessary for the construction of an
    annex document, including metadata, summary text, domain-specific
    introductions, maturity scores, and the main content sections. It inherits
    from `VersionedPayload` to support version management of the payload
    structure.

    Attributes:
        document_meta (dict): A dictionary containing metadata associated with
            the document, such as its title and version.
        executive_summary (ExecutiveSummaryAnnex): An object representing the
            executive summary section of the annex.
        domain_introduction (DomainIntroduction): An object representing the
            introduction for the specific domain.
        pillar_score_profile (MaturityScoreProfile): An object representing the
            profile of maturity scores across different pillars.
        sections (AnnexSections): An object that aggregates the main content
            sections of the annex document.
    """

    document_meta: dict
    executive_summary: ExecutiveSummaryAnnex
    domain_introduction: DomainIntroduction
    pillar_score_profile: MaturityScoreProfile
    sections: AnnexSections
