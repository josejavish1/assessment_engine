from typing import List

from pydantic import model_validator

from .common import BaseDraftModel


class ConclusionDraft(BaseDraftModel):
    r"""{'ConclusionDraft': 'Defines the data model for the conclusion section of a document draft.\n\nThis Pydantic model specifies the schema for a conclusion, including fields\nfor final assessments, executive summaries, and focus areas. It inherits\nfrom `BaseDraftModel` and incorporates a validator to enforce the presence\nof critical content.\n\nAttributes:\n    section_id: A fixed identifier for the section, defaults to "conclusion".\n    status: The workflow status of the draft, defaults to "draft".\n    tower_id: The unique identifier for the associated technology tower.\n    tower_name: The human-readable name of the associated technology tower.\n    section_title: The display title for the section, defaults to "Conclusion".\n    final_assessment: A comprehensive summary of findings and the final\n        assessment.\n    executive_message: A concise, high-level message intended for executive\n        stakeholders.\n    priority_focus_areas: A list of key areas identified for immediate\n        attention.\n    closing_statement: Final concluding remarks for the document.\n    notes_for_reviewer: A list of optional notes for the reviewer.', 'get_forbidden_phrases': 'Return a list of hardcoded phrases forbidden in the conclusion.', 'validate_conclusion_fields': 'Ensure `final_assessment` and `executive_message` fields are non-empty.\n\nThis Pydantic `model_validator` executes after model initialization to\nconfirm that mandatory conclusion fields contain content.\n\nReturns:\n    The validated `ConclusionDraft` instance.\n\nRaises:\n    ValueError: If `final_assessment` or `executive_message` is an empty\n        string.'}."""

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
        """Return a static list of forbidden phrases."""
        return [
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "roadmap detallado",
            "quick wins",
        ]

    @model_validator(mode="after")
    def validate_conclusion_fields(self) -> "ConclusionDraft":
        r"""{'docstring': 'Validates that essential conclusion fields are non-empty.\n\nThis Pydantic `model_validator` runs after initial field validation to\nensure that both `final_assessment` and `executive_message` contain\nnon-falsy values.\n\nReturns:\n    The validated `ConclusionDraft` instance.\n\nRaises:\n    ValueError: If `final_assessment` or `executive_message` is missing\n        or empty.'}."""
        if not self.final_assessment:
            raise ValueError("La seccion Conclusion debe contener 'final_assessment'.")
        if not self.executive_message:
            raise ValueError("La seccion Conclusion debe contener 'executive_message'.")
        return self
