from typing import List

from pydantic import BaseModel, Field, model_validator

from .common import BaseDraftModel


class TodoItem(BaseModel):
    r"""{'docstring': "Represents a validated to-do item or task.\n\nA Pydantic data model that defines the structure and constraints for a single\nto-do item. The model ensures type safety and value validation upon\ninstantiation.\n\nAttributes:\n    initiative (str): The primary title or name of the to-do item.\n    objective (str): A detailed description of the task's purpose.\n    priority (str): The assigned priority level. Must conform to the pattern\n        '^(Alta|Media|Baja|High|Medium|Low)$'.\n    related_pillars (List[str]): A list of strategic pillars associated with\n        the item.\n    expected_outcome (str): A description of the measurable result upon\n        completion.\n    dependencies (List[str]): A list of identifiers for prerequisite tasks.\n\nRaises:\n    pydantic.ValidationError: If any of the provided field values do not\n        conform to their specified types or constraints."}."""

    initiative: str
    objective: str
    priority: str = Field(..., pattern="^(Alta|Media|Baja|High|Medium|Low)$")
    related_pillars: List[str]
    expected_outcome: str
    dependencies: List[str]


class TodoDraft(BaseDraftModel):
    r"""{'TodoDraft': 'Represents the data schema for a draft of a \'TO-DO\' section.\n\nThis Pydantic model defines the structure, content, and metadata for a\nTO-DO section, ensuring data validation upon instantiation.\n\nAttributes:\n    section_id: The unique identifier for this section type.\n    status: The current status of the draft, e.g., "draft".\n    tower_id: The unique identifier for the associated tower.\n    tower_name: The display name of the associated tower.\n    section_title: The display title for the TO-DO section.\n    introduction: An introductory paragraph for the section.\n    todo_items: A list of `TodoItem` objects representing individual tasks.\n    closing_summary: A concluding summary for the section.\n    notes_for_reviewer: An optional list of notes for the reviewer.', 'TodoDraft.get_forbidden_phrases': 'Return a static list of forbidden phrases for content validation.', 'TodoDraft.validate_todo_items': 'Ensure the `todo_items` list is not empty.\n\nThis Pydantic model validator runs after model initialization to confirm that\nthe TO-DO section contains at least one `TodoItem`.\n\nReturns:\n    The validated instance of the model.\n\nRaises:\n    ValueError: If `todo_items` is an empty list.'}."""

    section_id: str = "todo"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "TO-DO"
    introduction: str
    todo_items: List[TodoItem]
    closing_summary: str
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return a static list of forbidden phrases."""
        return [
            "2027",
            "2028",
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "roadmap detallado",
        ]

    @model_validator(mode="after")
    def validate_todo_items(self) -> "TodoDraft":
        """Validate that the `todo_items` list is not empty."""
        if not self.todo_items:
            raise ValueError("La seccion TO-DO debe contener al menos un todo_item.")
        return self
