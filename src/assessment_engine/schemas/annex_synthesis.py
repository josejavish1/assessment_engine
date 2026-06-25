from typing import List

from pydantic import BaseModel, Field

from .common import VersionedPayload


class MaturityScoreProfile(BaseModel):
    """Represents a system's comprehensive maturity score profile.

    This data model encapsulates all components of a maturity score assessment,
    including introductory text, scoring methodology, a visual chart, and the
    detailed scores for each defined pillar. The pillars are typically derived
    programmatically from a central system 'Blueprint' configuration.

    Attributes:
        profile_intro (str): An introductory text or summary for the maturity
            profile.
        scoring_method_note (str): A note detailing the methodology used for
            scoring.
        radar_chart (str): A string representation of a radar chart, such as a
            base64-encoded image or SVG data URI.
        pillars (List[dict]): A list of dictionaries, where each dictionary
            represents a pillar of the maturity model and its associated scores.
    """

    profile_intro: str
    scoring_method_note: str
    radar_chart: str = ""
    pillars: List[dict] = Field(
        default_factory=list
    )  # Pillars are programmatically derived from the system's 'Blueprint' configuration.


class ExecutiveSummaryAnnex(BaseModel):
    """A data model for the synthesized content of an executive summary annex.

    This model encapsulates all information required to generate the executive summary
    section of an assessment report, including overall scores, maturity levels,
    narrative components, and key findings.

    Attributes:
        global_score (str): The string representation of the overall assessment score.
        global_band (str): The maturity band corresponding to the global score (e.g.,
            'Foundational', 'Optimizing').
        target_maturity (str): The desired or target maturity level for the entity
            under assessment.
        headline (str): A concise, high-level headline for the executive summary.
        summary_body (str): The main narrative body of the executive summary.
        message_strength (str): The introductory message for the key strengths
            section. Defaults to a standard phrase.
        message_gap (str): The introductory message for the improvement areas and
            technical debt section. Defaults to a standard phrase.
        message_bottleneck (str): The introductory message for the operational
            bottlenecks section. Defaults to a standard phrase.
        key_business_impacts (List[str]): A list of strings, each describing a key
            business impact identified during the assessment.
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
    """Model an As-Is Annex detailing a current state analysis."""

    narrative: str
    strengths: List[str]
    gaps: List[str]
    operational_impacts: List[str]


class ToBeAnnex(BaseModel):
    """Encapsulate the high-level vision and guiding design principles for a system."""

    vision: str
    design_principles: List[str]


class RiskItemAnnex(BaseModel):
    """Represent a single risk item with its description, impact, probability, and mitigation summary."""

    risk: str
    impact: str
    probability: str
    mitigation_summary: str


class RisksAnnex(BaseModel):
    """Represent the risks annex section of a document."""

    introduction: str
    risks: List[RiskItemAnnex]
    closing_summary: str = ""


class GapRowAnnex(BaseModel):
    """Represents a single row in a gap analysis annex.

    This data model defines the schema for an entry in a gap analysis table,
    used to articulate the delta between a current and a desired future state
    for a specific strategic domain.

    Attributes:
        pillar: The strategic pillar or high-level category for this analysis.
        as_is_summary: A description of the current operational state ('As-Is').
        target_state: A description of the desired future state ('To-Be').
        key_gap: The identified delta between the current and target states.
    """

    pillar: str
    as_is_summary: str
    target_state: str
    key_gap: str


class GapAnnex(BaseModel):
    r"""{'docstring': 'Defines the data structure for a gap analysis annex.\n\nThis Pydantic model specifies the schema for an appendix that outlines the\nfindings of a capability gap analysis. It includes an introduction, the\nscope of assessed capabilities, detailed gap descriptions, and an optional\nsummary.\n\nAttributes:\n    introduction: A string containing the introductory text for the gap\n        analysis section.\n    target_capabilities: A list of strings, where each string represents a\n        capability that was evaluated during the analysis.\n    gap_rows: A list of `GapRowAnnex` objects, with each object detailing\n        a specific identified capability gap.\n    closing_summary: An optional string containing the concluding summary of\n        the analysis. Defaults to an empty string.'}."""

    introduction: str
    target_capabilities: List[str]
    gap_rows: List[GapRowAnnex]
    closing_summary: str = ""


class InitiativeAnnex(BaseModel):
    """Define the data model for a single strategic initiative within an annex document."""

    sequence: int
    initiative: str
    objective: str
    priority: str
    expected_outcome: str
    dependencies_display: str


class TodoAnnex(BaseModel):
    """A data model for a structured 'TODO' annex.

    This class defines the data schema for a section that outlines key priority
    initiatives, typically for use in planning or status reporting documents.

    Attributes:
        introduction (str): The introductory text for the annex.
        priority_initiatives (List[InitiativeAnnex]): A list of objects,
            each representing a detailed initiative.
        closing_summary (str): An optional concluding summary for the section.
    """

    introduction: str
    priority_initiatives: List[InitiativeAnnex]
    closing_summary: str = ""


class ConclusionAnnex(BaseModel):
    """Represents the concluding section of a synthesized report."""

    final_assessment: str
    executive_message: str
    priority_focus_areas: List[str]
    closing_statement: str


class AnnexSections(BaseModel):
    """A data model that aggregates all constituent sections of a technical annex.

    Attributes:
        asis (AsIsAnnex): The section detailing the current state analysis ('As-Is').
        tobe (ToBeAnnex): The section detailing the desired future state ('To-Be').
        gap (GapAnnex): The section analyzing the gap between the current and future states.
        todo (TodoAnnex): The section outlining actionable items and tasks ('To-Do').
        risks (RisksAnnex): The section identifying potential risks and mitigation plans.
        conclusion (ConclusionAnnex): The concluding section summarizing the annex findings.
    """

    asis: AsIsAnnex
    tobe: ToBeAnnex
    gap: GapAnnex
    todo: TodoAnnex
    risks: RisksAnnex
    conclusion: ConclusionAnnex


class DomainIntroduction(BaseModel):
    """Represents the introductory narrative for a specific technological domain.

    This model encapsulates the primary textual and categorical elements that
    constitute a formal introduction to a technology area, including its purpose,
    scope, and core components.

    Attributes:
        introduction_paragraph: A narrative paragraph that provides a high-level
            overview of the technological domain.
        technological_domain: The formal name of the technological domain (e.g.,
            'Large Language Models').
        domain_objective: A concise statement defining the primary objective or
            fundamental purpose of the technology within this domain.
        evaluated_capabilities: A list of specific capabilities or functionalities
            that are typically assessed or are characteristic of this domain.
        included_components: A list of core technologies, architectural
            components, or sub-systems that constitute the domain.
    """

    introduction_paragraph: str
    technological_domain: str
    domain_objective: str
    evaluated_capabilities: List[str]
    included_components: List[str]


class AnnexPayload(VersionedPayload):
    """A data container for the complete payload required to synthesize an annex document.

    This class aggregates all components, from high-level metadata to detailed content
    sections, necessary for the generation of a complete annex. It inherits from
    `VersionedPayload` to incorporate versioning information.

    Attributes:
        document_meta: A dictionary containing metadata for the annex document, such as
            title, author, and creation date.
        executive_summary: An `ExecutiveSummaryAnnex` instance containing the content for
            the executive summary section.
        domain_introduction: A `DomainIntroduction` instance providing the introductory
            content for the specific domain covered by the annex.
        pillar_score_profile: A `MaturityScoreProfile` instance representing the
            scoring profile across different assessment pillars or categories.
        sections: An `AnnexSections` instance that holds the main, detailed content
            sections of the document.
    """

    document_meta: dict
    executive_summary: ExecutiveSummaryAnnex
    domain_introduction: DomainIntroduction
    pillar_score_profile: MaturityScoreProfile
    sections: AnnexSections
