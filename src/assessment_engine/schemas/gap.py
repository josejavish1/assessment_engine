from typing import List
from pydantic import BaseModel, Field
from .common import BaseDraftModel

class GapItem(BaseModel):
    pillar: str
    as_is_summary: str
    target_state: str
    key_gap: str
    operational_implication: str

class GapDraft(BaseDraftModel):
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
        return [
            "quick wins",
            "roadmap",
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "plan de evolucion",
            "plan de evolución",
        ]
