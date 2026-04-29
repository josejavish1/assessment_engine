from typing import List
from pydantic import BaseModel, Field, model_validator
from .common import BaseDraftModel

class TodoItem(BaseModel):
    initiative: str
    objective: str
    priority: str = Field(..., pattern="^(Alta|Media|Baja|High|Medium|Low)$")
    related_pillars: List[str]
    expected_outcome: str
    dependencies: List[str]

class TodoDraft(BaseDraftModel):
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
        if not self.todo_items:
            raise ValueError("La seccion TO-DO debe contener al menos un todo_item.")
        return self
