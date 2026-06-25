from typing import List

from pydantic import BaseModel, Field, field_validator

from .common import BaseDraftModel


class TargetMaturity(BaseModel):
    """Represent a recommended target maturity level with its corresponding score and justification."""

    recommended_level: str = Field(
        ...,
        description="The target maturity level designation (e.g., 'Level 4 - Optimized').",
    )
    recommended_score_reference: str = Field(
        ...,
        description="The numerical score corresponding to the target level (e.g., 4.0).",
    )
    justification: str = Field(
        ..., description="A detailed rationale for the selected target level."
    )


class PillarCapability(BaseModel):
    """Represents the required capabilities for a target level within an engineering pillar."""

    pillar: str = Field(..., description="The name of the pillar.")
    target_capabilities: List[str] = Field(
        ..., description="A list of capabilities required to attain the target level."
    )


class ToBeDraft(BaseDraftModel):
    r"""[{'path': 'ToBeDraft', 'docstring': 'A data model for the \'To-Be\' section of a document draft.\n\nDefines the desired future state, including target maturity, capabilities,\narchitectural principles, and operational implications.\n\nAttributes:\n    section_id: The unique identifier for this section, fixed to "tobe".\n    status: The current status of the draft, fixed to "draft".\n    tower_id: The unique identifier for the associated tower.\n    tower_name: The human-readable name of the tower.\n    section_title: The title of this section, fixed to "TO-BE".\n    introduction: An introductory text describing the future state.\n    target_maturity: The desired maturity level for the tower.\n    target_capabilities_by_pillar: A list of target capabilities, grouped by\n        their respective pillars.\n    architecture_principles: A list of key architectural principles that\n        define the target state.\n    operating_model_implications: A list of implications for the operating\n        model resulting from the proposed changes.\n    notes_for_reviewer: An optional list of internal notes for reviewers.'}, {'path': 'ToBeDraft.get_forbidden_phrases', 'docstring': "Return a list of forbidden phrases for the 'To-Be' section."}, {'path': 'ToBeDraft.validate_pillars_not_empty', 'docstring': 'Validate that `target_capabilities_by_pillar` is not an empty list.\n\nThis is a Pydantic validator ensuring the field is a non-empty collection.\n\nArgs:\n    v: The input list for the `target_capabilities_by_pillar` field.\n\nReturns:\n    The original list `v` if it is not empty.\n\nRaises:\n    ValueError: If the input list `v` is empty.'}]."""

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
        """Return a static list of forbidden phrases."""
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
    def validate_pillars_not_empty(cls, v):
        """Validate that the `target_capabilities_by_pillar` field is not empty.

        This Pydantic class method validator ensures that the associated field is
        not an empty collection.

        Args:
            cls: The Pydantic model class.
            v (dict): The input dictionary for `target_capabilities_by_pillar`.

        Returns:
            dict: The validated input dictionary `v` if it is not empty.

        Raises:
            ValueError: If the input dictionary `v` is empty.
        """
        if not v:
            raise ValueError("Debe haber al menos un pilar con capacidades objetivo")
        return v


class Defect(BaseModel):
    """Represents a single, structured defect with validated severity.

    This Pydantic model provides a schema for structuring and validating data
    pertaining to an identified issue, such as one discovered during static
    analysis or a code review. It enforces a strict schema, including a
    constrained set of values for the defect's severity.

    Attributes:
        severity: The severity level of the defect. Must be one of 'critical',
            'major', or 'minor'.
        type: The category or type identifier for the defect (e.g., 'Security',
            'Performance').
        message: A human-readable description of the specific issue.
        suggested_fix: A detailed recommendation for resolving the defect.
    """

    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str


class ToBeReview(BaseModel):
    """Represents the structured outcome of a 'To-Be' section review.

    This Pydantic model captures all structured feedback from the review of a
    proposed future state ('To-Be') design or document section.

    Attributes:
        section_id (str): A unique identifier for the section. Defaults to "tobe".
        status (str): The overall review status. Must be one of 'approve',
            'revise', or 'human_validation_required'.
        overall_assessment (str): A high-level summary of the review findings.
        defects (List[Defect]): A list of specific defects or issues identified
            during the review. Defaults to an empty list.
        approval_conditions (List[str]): A list of conditions that must be met
            before the section can be approved. Defaults to an empty list.
        review_notes (List[str]): A list of general notes or comments from the
            reviewer. Defaults to an empty list.
    """

    section_id: str = "tobe"
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []
