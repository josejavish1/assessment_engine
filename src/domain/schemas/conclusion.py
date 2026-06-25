from typing import List

from pydantic import model_validator

from .common import BaseDraftModel


class ConclusionDraft(BaseDraftModel):
    r"""{'ConclusionDraft': 'Represents the data model for the "Conclusion" section of a document.\n\nThis Pydantic model defines the structure for the conclusion section,\nincluding final assessments, executive messages, and key focus areas.\nIt inherits from BaseDraftModel and includes post-initialization validation\nfor critical fields.\n\nAttributes:\n    section_id (str): The unique identifier for the section, fixed to "conclusion".\n    status (str): The current status of the draft, defaults to "draft".\n    tower_id (str): The identifier of the associated tower.\n    tower_name (str): The name of the associated tower.\n    section_title (str): The title of the section, defaults to "Conclusion".\n    final_assessment (str): A comprehensive final assessment of the subject matter.\n    executive_message (str): A high-level message tailored for an executive audience.\n    priority_focus_areas (List[str]): A list of key areas identified for future focus.\n    closing_statement (str): The final closing remarks for the document.\n    notes_for_reviewer (List[str]): An optional list of notes for the reviewer.', 'ConclusionDraft.get_forbidden_phrases': 'Return a static list of forbidden phrases for the conclusion section.', 'ConclusionDraft.validate_conclusion_fields': 'Validate that essential conclusion fields are not empty after initialization.\n\nThis Pydantic validator ensures that `final_assessment` and\n`executive_message` are non-empty strings.\n\nReturns:\n    The validated instance of the class.\n\nRaises:\n    ValueError: If `final_assessment` or `executive_message` is an empty string.'}."""
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
        """Return the static list of forbidden phrases."""
        return [
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "roadmap detallado",
            "quick wins",
        ]

    @model_validator(mode="after")
    def validate_conclusion_fields(self) -> "ConclusionDraft":
        """Ensure `final_assessment` and `executive_message` fields are present.

        A Pydantic model validator that executes after model initialization.
        It confirms that the `final_assessment` and `executive_message` attributes
        have been assigned non-falsy values.

        Returns:
            ConclusionDraft: The validated instance of the model.

        Raises:
            ValueError: If `final_assessment` or `executive_message` is `None` or
                an empty string.
        """
        if not self.final_assessment:
            raise ValueError("La seccion Conclusion debe contener 'final_assessment'.")
        if not self.executive_message:
            raise ValueError("La seccion Conclusion debe contener 'executive_message'.")
        return self
