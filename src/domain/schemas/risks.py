from typing import List

from pydantic import BaseModel, Field

from .common import BaseDraftModel


class RiskItem(BaseModel):
    """Represents a single, structured risk item.

    This class defines the data schema for a risk, utilizing Pydantic for
    data validation and serialization. Instantiation will raise a
    `pydantic.ValidationError` if the input data fails to conform to the
    defined types and constraints.

    Attributes:
        risk_name: A human-readable, unique identifier for the risk.
        severity: The severity level, constrained to 'High', 'Medium', 'Low', or
            'Critical'.
        business_impact: A textual description of the potential business
            consequences should the risk be realized.
        technical_root_cause: A textual description of the fundamental technical
            vulnerability, misconfiguration, or condition giving rise to the risk.
        related_pillars: A list of associated domains or categories, such as
            'Security' or 'Reliability', that this risk pertains to.
    """

    risk_name: str
    severity: str = Field(..., pattern="^(High|Medium|Low|Critical)$")
    business_impact: str
    technical_root_cause: str
    related_pillars: List[str]


class RisksDraft(BaseDraftModel):
    r"""{'RisksDraft': 'A data model representing a draft of the "Risks" section.\n\nAttributes:\n    section_id: The unique identifier for this section type.\n    status: The current drafting status.\n    tower_id: The identifier of the associated tower.\n    tower_name: The name of the associated tower.\n    section_title: The display title for this section.\n    introduction: The introductory text for the risks section.\n    risk_items: A list of individual risk items.\n    notes_for_reviewer: A list of notes intended for the reviewer.', 'RisksDraft.get_forbidden_phrases': 'Return the list of forbidden phrases.'}."""

    section_id: str = "risks"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "Risks"
    introduction: str
    risk_items: List[RiskItem]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return the static list of forbidden phrases."""
        return ["oportunidades", "quick wins", "solucion"]
