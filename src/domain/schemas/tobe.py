from typing import Any, List

from pydantic import BaseModel, Field, field_validator

from .common import BaseDraftModel


class TargetMaturity(BaseModel):
    """Encapsulates the recommended target maturity state for a capability.

    This data model defines the desired future state by specifying a maturity
    level, its corresponding numerical score, and the justification for the
    recommendation.

    Attributes:
        recommended_level: The descriptive name of the target maturity level (e.g.,
            'Level 4 - Optimized').
        recommended_score_reference: The numerical score corresponding to the
            recommended level, formatted as a string (e.g., '4.0').
        justification: A textual explanation detailing the rationale behind the
            recommended target maturity.
    """
    recommended_level: str = Field(
        ..., description="Target maturity level (e.g., 'Level 4 - Optimized')."
    )
    recommended_score_reference: str = Field(
        ..., description="The numerical score corresponding to the target maturity level (e.g., 4.0)."
    )
    justification: str = Field(
        ..., description="A detailed rationale for the target maturity level."
    )


class PillarCapability(BaseModel):
    """Represents the target capabilities associated with a specific pillar.

    Attributes:
        pillar: The name of the pillar.
        target_capabilities: A list of capability identifiers to be attained for the
            pillar.
    """
    pillar: str = Field(..., description="The name of the pillar.")
    target_capabilities: List[str] = Field(
        ..., description="A list of capabilities to be attained."
    )


class ToBeDraft(BaseDraftModel):
    r"""[{'name': 'ToBeDraft', 'path': 'tobe.py', 'type': 'class', 'docstring': 'Represents the data model for the \'To-Be\' section of a draft document.\n\nThis class defines the Pydantic model for the target state description,\nincluding strategic goals, capabilities, architecture, and operational changes.\nIt enforces data integrity through built-in validation rules.\n\nAttributes:\n    section_id: The unique identifier for this section, fixed to "tobe".\n    status: The current status of the draft section, defaulting to "draft".\n    tower_id: The unique identifier of the associated technology tower.\n    tower_name: The name of the associated technology tower.\n    section_title: The title of the section, fixed to "TO-BE".\n    introduction: An introductory text describing the target state.\n    target_maturity: A `TargetMaturity` object detailing the desired\n        maturity level and its justification.\n    target_capabilities_by_pillar: A list of `PillarCapability` objects,\n        each outlining target capabilities for a specific pillar.\n    architecture_principles: A list of key architecture principles that will\n        govern the target state.\n    operating_model_implications: A list of anticipated implications for the\n        organization\'s operating model.\n    notes_for_reviewer: An optional list of notes intended for the document\n        reviewer.'}, {'name': 'get_forbidden_phrases', 'path': 'tobe.py', 'type': 'function', 'docstring': 'Return a static list of forbidden phrases for content validation.'}, {'name': 'validate_pillars_not_empty', 'path': 'tobe.py', 'type': 'function', 'docstring': 'Validate that `target_capabilities_by_pillar` is not empty.\n\nThis Pydantic class method validator ensures that the list of target\ncapability pillars contains at least one entry.\n\nArgs:\n    cls: The class being validated.\n    v: The input value for the `target_capabilities_by_pillar` field.\n\nReturns:\n    The input value `v` if it is not an empty list.\n\nRaises:\n    ValueError: If the input list `v` is empty.'}]."""
    section_id: str = "tobe"
    status: str = "draft"
    tower_id: str
    tower_name: str
    section_title: str = "TO-BE"
    introduction: str
    target_maturity: TargetMaturity
    target_capabilities_by_pillar: List[PillarCapability]
    architecture_principles: List[str]
    operating_model_implications: List[str]
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return a list of forbidden phrases."""
        return [
            "quick wins",
            "roadmap",
            "0-3 meses",
            "3-6 meses",
            "6-12 meses",
            "plan de evolucion",
            "plan de evolución",
        ]

    @field_validator("target_capabilities_by_pillar")
    @classmethod
    def validate_pillars_not_empty(cls, v: Any) -> Any:
        """Ensures the `target_capabilities_by_pillar` field is not empty.

        This class method is a Pydantic validator that checks if the input value
        for the `target_capabilities_by_pillar` field is a non-empty collection.

        Args:
            cls: The Pydantic model class on which the validator is called.
            v: The input value for the field being validated.

        Returns:
            The original input value `v` if it is not empty.

        Raises:
            ValueError: If the input value `v` is empty or otherwise evaluates to
                False in a boolean context.
        """
        if not v:
            raise ValueError("Debe haber al menos un pilar con capacidades objetivo")
        return v


class Defect(BaseModel):
    """Represents a single detected defect or issue.

    This data model encapsulates information about a specific problem identified
    during an analysis, including its severity, category, a descriptive
    message, and a proposed solution.

    Attributes:
        severity (str): The severity level of the defect, constrained to 'critical',
            'major', or 'minor'.
        type (str): The category of the defect (e.g., 'Security', 'Performance').
        message (str): A human-readable message detailing the defect.
        suggested_fix (str): A recommended action or code modification to resolve the
            defect.
    """
    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str


class ToBeReview(BaseModel):
    """Represents the structured outcome of a review for a proposed 'To-Be' process design.

    This data model encapsulates the evaluation status, a summary assessment, and
    lists of identified defects, approval conditions, or general observations
    following the evaluation of a future-state process.

    Attributes:
        section_id (str): A fixed identifier for this review section, defaulting to
            'tobe'.
        status (str): The final status of the review. Must be one of 'approve',
            'revise', or 'human_validation_required'.
        overall_assessment (str): A high-level, human-readable summary of the
            review findings.
        defects (List[Defect]): A list of specific, structured defects identified
            during the review. Defaults to an empty list.
        approval_conditions (List[str]): A list of conditions that must be met for
            the 'To-Be' design to be formally approved. Defaults to an empty list.
        review_notes (List[str]): A list of general notes, comments, or
            observations from the reviewer. Defaults to an empty list.
    """
    section_id: str = "tobe"
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []
