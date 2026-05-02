from typing import List

from pydantic import model_validator

from .common import BaseDraftModel


class ConclusionDraft(BaseDraftModel):
    section_id: str = "conclusion"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "Conclusion"
    final_assessment: str
    executive_message: str
    priority_focus_areas: List[str]
    closing_statement: str
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        return [
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "roadmap detallado",
            "quick wins",
        ]

    @model_validator(mode="after")
    def validate_conclusion_fields(self) -> "ConclusionDraft":
        if not self.final_assessment:
            raise ValueError("La seccion Conclusion debe contener 'final_assessment'.")
        if not self.executive_message:
            raise ValueError("La seccion Conclusion debe contener 'executive_message'.")
        return self
