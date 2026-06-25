from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class AsIsPillar(BaseModel):
    """Defines the schema for the as-is assessment results of a single pillar.

    This data model captures the current state of an assessed pillar, including
    its score, maturity level, a summary of findings, and its operational impact.

    Attributes:
        pillar: The name of the assessment pillar (e.g., 'Security', 'Reliability').
        score: The calculated numerical score for the pillar on a predefined scale.
        maturity_level: The assessed maturity level for the pillar (e.g.,
            'Level 1 - Initial', 'Level 4 - Optimized').
        findings_summary: A list of strings, each summarizing a key observation
            or finding for the pillar.
        operational_impact: A textual description of how the pillar's current
            state affects business or technical operations.
    """
    pillar: str = Field(..., description="The name of the assessment pillar.")
    score: float = Field(..., description="The calculated score for the pillar.")
    maturity_level: str = Field(
        ..., description="Maturity level of the pillar (e.g., Level 2 - Basic)."
    )
    findings_summary: List[str] = Field(..., description="A summary of the findings for this pillar.")
    operational_impact: str = Field(..., description="Operational impact assessment.")


class AsIsDraft(BaseDraftModel):
    r"""{'AsIsDraft': "Represents the 'AS-IS' draft section of a technology tower assessment.\n\nThis data model captures the complete current-state analysis for a specific\ntechnology or business vertical (tower), including its core pillars, overarching\nthemes, and a high-level executive summary.\n\nAttributes:\n    section_id: The unique identifier for this section type, fixed to 'asis'.\n    status: The current status of the document, fixed to 'draft'.\n    tower_id: The unique identifier for the tower being assessed.\n    tower_name: The human-readable name of the tower.\n    section_title: The display title for this section, fixed to 'AS-IS'.\n    executive_narrative: A high-level summary of the current state findings.\n    pillars: A list of `AsIsPillar` objects, each detailing a specific\n        capability area within the tower's current state.\n    cross_cutting_themes: A list of themes or observations that apply across\n        multiple pillars.\n    notes_for_reviewer: An optional list of internal notes for reviewers.", 'AsIsDraft.get_forbidden_phrases': 'Return a list of phrases forbidden in AS-IS documents.'}."""
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
        """Return a list of phrases forbidden in AS-IS documents."""
        return [
            "TO-BE",
            "estado objetivo",
            "capacidades objetivo",
            "roadmap",
            "recomendamos",
            "plan de accion",
        ]
