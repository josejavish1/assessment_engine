from typing import List, Optional

from pydantic import BaseModel, Field


class ThresholdMapping(BaseModel):
    """Maps a factual threshold condition to a specific maturity score."""

    condition: str = Field(
        description="Expression representing the condition, e.g., 'adoption >= 50'"
    )
    score: float = Field(
        description="The maturity score resulting if this condition is met."
    )


class RubricRule(BaseModel):
    """Represents an evaluation rule for a specific tower within a framework."""

    tower_id: str = Field(description="The tower code, e.g., 'T6'")
    query_template: str = Field(
        description="Template for the search query to gather facts."
    )
    evaluation_variable: str = Field(
        default="adoption",
        description="The variable to be extracted from evidence, e.g., 'adoption'",
    )
    thresholds: List[ThresholdMapping] = Field(
        description="List of mathematical threshold mappings for scoring."
    )
    default_score: float = Field(
        default=3.0, description="Fallback score if no threshold condition is met."
    )


class FrameworkRubric(BaseModel):
    """Declarative evaluation schema for a RAGE dynamic framework."""

    framework_id: str = Field(
        description="Unique framework identifier, e.g., 'ens_alta'"
    )
    framework_name: str = Field(
        description="Official name of the standard or regulation."
    )
    description: Optional[str] = None
    rules: List[RubricRule] = Field(
        description="Rules mapping towers to analytical criteria."
    )
