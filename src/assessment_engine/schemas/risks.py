from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class RiskItem(BaseModel):
    """A data model representing a single, structured risk item.

    This Pydantic model provides data validation to ensure that risk information
    conforms to a predefined schema, including constraints on specific fields.

    Attributes:
        risk_name (str): The unique name or title of the risk.
        severity (str): The severity level of the risk. Must be one of 'Critical',
            'High', 'Medium', or 'Low'.
        business_impact (str): A description of the potential business impact should
            the risk materialize.
        technical_root_cause (str): An explanation of the underlying technical
            reason for the risk.
        related_pillars (List[str]): A list of business or technical pillars
            associated with the risk (e.g., 'Security', 'Reliability').
    """
    risk_name: str
    severity: str = Field(..., pattern="^(High|Medium|Low|Critical)$")
    business_impact: str
    technical_root_cause: str
    related_pillars: List[str]


class RisksDraft(BaseDraftModel):
    """Return a static list of forbidden phrases for the risks section."""
    section_id: str = "risks"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "Risks"
    introduction: str
    risk_items: List[RiskItem]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return a static list of forbidden phrases."""
        return ["oportunidades", "quick wins", "solucion"]
