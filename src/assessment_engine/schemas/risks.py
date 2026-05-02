from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class RiskItem(BaseModel):
    risk_name: str
    severity: str = Field(..., pattern="^(High|Medium|Low|Critical)$")
    business_impact: str
    technical_root_cause: str
    related_pillars: List[str]


class RisksDraft(BaseDraftModel):
    section_id: str = "risks"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "Risks"
    introduction: str
    risk_items: List[RiskItem]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        return ["oportunidades", "quick wins", "solucion"]
