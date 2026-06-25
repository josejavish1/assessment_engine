from typing import List

from pydantic import BaseModel, Field, model_validator

from .common import BaseDraftModel


class TodoItem(BaseModel):
    """A Pydantic model representing a single, structured to-do item.

    This model leverages Pydantic for data validation, ensuring that all fields are
    correctly typed and that the 'priority' field conforms to a predefined set of
    allowed string values.

    Attributes:
        initiative (str): The high-level initiative or project name associated with
            the item.
        objective (str): The specific, measurable goal of this to-do item.
        priority (str): The priority level of the task. Must conform to the regex
            '^(Alta|Media|Baja|High|Medium|Low)$'.
        related_pillars (List[str]): A list of strategic pillars or organizational
            areas this item supports.
        expected_outcome (str): A description of the desired result or state after
            the item's completion.
        dependencies (List[str]): A list of identifiers for other tasks or items
            that must be completed before this one can be started.
    """

    initiative: str
    objective: str
    priority: str = Field(..., pattern="^(Alta|Media|Baja|High|Medium|Low)$")
    related_pillars: List[str]
    expected_outcome: str
    dependencies: List[str]


class TodoDraft(BaseDraftModel):
    r"""{'TodoDraft': 'Represents a data model for a "TO-DO" section draft.\n\nAttributes:\n    section_id: The unique identifier for the section. Defaults to "todo".\n    status: The current status of the draft. Defaults to "draft".\n    tower_id: The identifier for the associated tower.\n    tower_name: The name of the associated tower.\n    section_title: The title of the section. Defaults to "TO-DO".\n    introduction: Introductory text for the TO-DO list.\n    todo_items: A list of individual `TodoItem` objects.\n    closing_summary: A concluding summary for the TO-DO section.\n    notes_for_reviewer: Optional notes intended for a reviewer.', 'TodoDraft.get_forbidden_phrases': 'Return a static list of forbidden phrases for the TO-DO section.', 'TodoDraft.validate_todo_items': 'Validate that the `todo_items` list is not empty.\n\nThis is a Pydantic model validator that runs after model initialization to\nenforce the presence of at least one to-do item.\n\nReturns:\n    The validated instance of the class.\n\nRaises:\n    ValueError: If the `todo_items` list is empty.'}."""

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
        """{'docstring': 'Return a static list of forbidden phrases.'}."""
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
        """Validate that the `todo_items` list is not empty.

        This Pydantic `model_validator` runs after initial field validation to
        ensure that the `todo_items` attribute contains at least one element.

        Returns:
            The validated model instance (`self`).

        Raises:
            ValueError: If the `todo_items` list is empty.
        """
        if not self.todo_items:
            raise ValueError("La seccion TO-DO debe contener al menos un todo_item.")
        return self
