from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class AsIsPillar(BaseModel):
    """Data model for the 'as-is' assessment of a single organizational pillar.

    Encapsulates the current state analysis for a specific assessment area,
    including its score, maturity level, key findings, and operational impact.

    Attributes:
        pillar: The name of the pillar being assessed (e.g., 'Security').
        score: The calculated numerical score for the pillar.
        maturity_level: The descriptive maturity level designation corresponding
            to the pillar's score (e.g., 'Level 2 - Basic').
        findings_summary: A list of strings summarizing key findings.
        operational_impact: A description of the operational consequences
            associated with the findings.
    """

    pillar: str = Field(..., description="Pillar name")
    score: float = Field(..., description="Pillar score")
    maturity_level: str = Field(
        ..., description="Maturity level designation, e.g., 'Level 2 - Basic'."
    )
    findings_summary: List[str] = Field(..., description="Summary of findings")
    operational_impact: str = Field(..., description="Operational impact")


class AsIsDraft(BaseDraftModel):
    """Defines the data model for a draft 'AS-IS' analysis section.

    This model captures the current state analysis for a specific technology or
    business tower. It includes a high-level narrative, detailed analysis
    pillars, cross-cutting themes, and other metadata required for document
    generation and review.

    Attributes:
        section_id: The unique identifier for the section, defaulted to "asis".
        status: The current status of the section, defaulted to "draft".
        tower_id: The unique identifier for the associated technology or
            business tower.
        tower_name: The human-readable name of the associated tower.
        section_title: The title of the section, defaulted to "AS-IS".
        executive_narrative: A high-level summary of the current state.
        pillars: A list of detailed analysis pillars for the current state.
        cross_cutting_themes: A list of themes that span multiple pillars.
        notes_for_reviewer: Optional notes intended for document reviewers.
    """

    section_id: str = "asis"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "AS-IS"
    executive_narrative: str
    pillars: List[AsIsPillar]
    cross_cutting_themes: List[str]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return a list of phrases forbidden in an 'as-is' analysis context."""
        return [
            "TO-BE",
            "estado objetivo",
            "capacidades objetivo",
            "roadmap",
            "recomendamos",
            "plan de accion",
        ]
