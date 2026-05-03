"""
Pydantic Schemas for MCP Server Contracts.

This module defines the data structures used in the request and response
bodies of the MCP server, acting as a formal contract for API consumers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class PayloadArtifactState(BaseModel):
    """Represents the state of a JSON payload artifact."""

    path: str = Field(..., description="The absolute path to the artifact file.")
    status: Literal["missing", "present", "error", "invalid", "valid"] = Field(
        ..., description="The validation status of the artifact."
    )
    message: Optional[str] = Field(
        None, description="An error message if the status is 'error'."
    )
    validation_errors: Optional[List[str]] = Field(
        None, description="A list of validation errors if the status is 'invalid'."
    )
    generation_metadata: Optional[Any] = Field(
        None, description="Metadata about the generation process if the status is 'valid'."
    )
    tower_code: Optional[str] = Field(
        None, description="The tower code (e.g., 'T1') if the artifact is valid."
    )
    tower_name: Optional[str] = Field(
        None, description="The tower name (e.g., 'Security') if the artifact is valid'."
    )


class DocxArtifactState(BaseModel):
    """Represents the state of a DOCX deliverable."""

    status: Literal["missing", "present"] = Field(
        ..., description="The presence status of the DOCX file."
    )
    path: Optional[str] = Field(
        None, description="The absolute path to the DOCX file if present."
    )


class CanonicalState(BaseModel):
    """Represents the state of artifacts in the canonical (blueprint-first) workflow."""

    mode: str = Field(
        ..., description="The operational mode, e.g., 'blueprint-first'."
    )
    blueprint_payload: PayloadArtifactState = Field(
        ..., description="The state of the master blueprint payload."
    )
    annex_payload: PayloadArtifactState = Field(
        ..., description="The state of the synthesized annex payload."
    )
    deliverables: Dict[str, DocxArtifactState] = Field(
        ..., description="The state of final DOCX deliverables."
    )
    overall_status: Literal["complete", "invalid", "partial", "missing"] = Field(
        ..., description="An aggregated status of the canonical workflow."
    )


class LegacySectionState(BaseModel):
    """Represents the state of a section in the legacy workflow."""

    status: str = Field(
        ...,
        description="The status of the legacy section file (e.g., 'missing', 'approved').",
    )
    message: Optional[str] = Field(
        None, description="An error message if the file could not be loaded."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Approval metadata from the legacy file."
    )
    path: Optional[str] = Field(
        None, description="The absolute path to the legacy section file if present."
    )


class LegacyState(BaseModel):
    """Represents the state of all sections in the legacy workflow."""

    asis: LegacySectionState
    risks: LegacySectionState
    gap: LegacySectionState
    tobe: LegacySectionState
    todo: LegacySectionState
    conclusion: LegacySectionState


class GetTowerStateResponse(BaseModel):
    """
    Defines the contract for the response of the `get_tower_state` tool.
    It provides a comprehensive overview of all artifacts related to a tower.
    """

    canonical: CanonicalState = Field(
        ..., description="State of the modern, blueprint-first workflow."
    )
    legacy: LegacyState = Field(
        ..., description="Aggregated state of the legacy workflow sections."
    )
    asis: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'asis' section."
    )
    risks: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'risks' section."
    )
    gap: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'gap' section."
    )
    tobe: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'tobe' section."
    )
    todo: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'todo' section."
    )
    conclusion: LegacySectionState = Field(
        ..., description="Detailed state of the legacy 'conclusion' section."
    )


class StartPlanGenerationResponse(BaseModel):
    """
    Defines the contract for the response of `start_plan_generation`.
    """
    job_id: str = Field(..., description="The unique identifier for the asynchronous job.")
    status: Literal["started"] = Field(..., description="The initial status of the job.")


class CheckPlanStatusResponse(BaseModel):
    """
    Defines the contract for the response of `check_plan_status`.
    """
    status: Literal["running", "completed", "error", "not_found"] = Field(
        ..., description="The current status of the job."
    )
    result: Optional[str] = Field(
        None, description="The result of the job, present if status is 'completed' or 'error'."
    )
