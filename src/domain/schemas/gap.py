from typing import List

from pydantic import BaseModel

from .common import BaseDraftModel


class GapItem(BaseModel):
    """Represent a single item in a gap analysis report."""
    pillar: str
    as_is_summary: str
    target_state: str
    key_gap: str
    operational_implication: str


class GapDraft(BaseDraftModel):
    """A Pydantic model that defines the schema for a GAP analysis draft.

    This model encapsulates all the necessary components for a preliminary GAP
    assessment, including the associated tower, introduction, a list of
    identified gaps, and summaries.

    Attributes:
        section_id: A static identifier for this section type, fixed to "gap".
        status: The current status of the draft, fixed to "draft".
        tower_id: The unique identifier for the associated technology tower.
        tower_name: The human-readable name of the associated technology tower.
        section_title: The title of the section, fixed to "GAP Analysis".
        introduction: A textual introduction to the GAP analysis.
        gap_items: A list of structured objects, each detailing an identified gap.
        cross_cutting_gap_summary: A list of strings summarizing gaps that affect
            multiple areas.
        notes_for_reviewer: An optional list of notes for the document reviewer.
    """
    section_id: str = "gap"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "GAP Analysis"
    introduction: str
    gap_items: List[GapItem]
    cross_cutting_gap_summary: List[str]
    notes_for_reviewer: List[str] = []

    @classmethod
    def get_forbidden_phrases(cls) -> List[str]:
        """Return the static list of forbidden phrases."""
        return [
            "quick wins",
            "roadmap",
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "plan de evolucion",
            "plan de evolución",
        ]
