from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def collect_all_strings(data: Any) -> List[str]:
    """Recursively extracts all string values from a nested data structure.

    Performs a depth-first traversal of a data structure composed of
    dictionaries and lists. All encountered string literals are collected into a
    single flat list. Non-string primitive types and other unhandled collection
    types are ignored.

    Args:
        data (Any): The data structure to traverse. The function recursively
            descends into dictionary values and list items.

    Returns:
        List[str]: A flat list containing all string values found, ordered by the
            depth-first traversal.
    """
    out = []
    if isinstance(data, dict):
        for v in data.values():
            out.extend(collect_all_strings(v))
    elif isinstance(data, list):
        for item in data:
            out.extend(collect_all_strings(item))
    elif isinstance(data, str):
        out.append(data)
    return out


class BaseDraftModel(BaseModel):
    r"""{'BaseDraftModel': 'A base Pydantic model for draftable content sections.\n\nProvides common fields and validation logic for content sections that undergo a\ndraft and review process. It incorporates a mechanism to sanitize reviewer\nnotes and enforce content restrictions by disallowing a configurable list of\nforbidden phrases in other fields.\n\nAttributes:\n    section_id: The unique string identifier for the content section.\n    notes_for_reviewer: A list of strings containing notes for a reviewer.\n        During validation, any note containing a forbidden phrase is silently\n        removed.', 'get_forbidden_phrases': "Return a list of phrases forbidden for use in the model's fields.", 'validate_forbidden_phrases': 'Sanitizes reviewer notes and validates string fields against forbidden phrases.\n\nThis Pydantic `model_validator` is executed after model initialization to\nenforce content restrictions. It performs two distinct operations:\n\n1.  It filters the `notes_for_reviewer` list, silently removing any note\n    that contains a forbidden phrase (case-insensitively).\n2.  It inspects all other string-type fields in the model. If a forbidden\n    phrase is found within any of these other fields, validation fails.\n\nThe list of forbidden phrases is sourced from `get_forbidden_phrases()`.\n\nReturns:\n    The validated model instance (`self`), with the `notes_for_reviewer` list\n    potentially sanitized.\n\nRaises:\n    ValueError: If a case-insensitive match for a forbidden phrase is found\n        in any string field of the model, excluding `notes_for_reviewer`.'}."""
    section_id: str
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Return a list of forbidden phrases.

        This base implementation returns an empty list and is intended to be
        overridden by subclasses.

        Returns:
            A list of forbidden phrases.
        """
        return []

    @model_validator(mode="after")
    def validate_forbidden_phrases(self) -> "BaseDraftModel":
        """Validates model data against a list of forbidden phrases.

        A Pydantic model validator that enforces content policies after initialization.

        The validator sources a list of forbidden phrases from the instance's
        `get_forbidden_phrases` method. The validation process is case-insensitive
        and involves two distinct actions:

        1.  It filters the `notes_for_reviewer` list, silently removing any
            entries that contain a forbidden phrase.
        2.  It inspects all other string-based fields in the model. If a
            forbidden phrase is found, it raises a `ValueError` that includes
            the problematic phrase and the section identifier (`section_title` or
            `section_id`).

        Returns:
            The validated and potentially modified model instance.

        Raises:
            ValueError: If a forbidden phrase is found in any string field of the
                model, excluding the `notes_for_reviewer` field.
        """
        forbidden = self.get_forbidden_phrases()
        if not forbidden:
            return self

        cleaned_notes = []
        for note in self.notes_for_reviewer:
            if not any(phrase.lower() in note.lower() for phrase in forbidden):
                cleaned_notes.append(note)
        self.notes_for_reviewer = cleaned_notes

        data = self.model_dump(exclude={"notes_for_reviewer"})
        all_strings = collect_all_strings(data)

        for phrase in forbidden:
            for text in all_strings:
                if phrase.lower() in text.lower():
                    section_name = getattr(self, "section_title", self.section_id)
                    raise ValueError(
                        f"La seccion {section_name} contiene una frase prohibida: '{phrase}'."
                    )

        return self


class Defect(BaseModel):
    """Models a single defect identified during static or dynamic analysis.

    This class serves as a Pydantic data model, providing validation and
    serialization for structured defect information.

    Attributes:
        severity: The severity level of the defect. Must be one of 'critical',
            'major', or 'minor'.
        type: A machine-readable string identifier for the defect category (e.g.,
            'security/sql-injection').
        message: A human-readable description of the specific issue detected.
        suggested_fix: A human-readable description of the recommended action
            or code modification to resolve the defect.
    """
    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str


class SectionReview(BaseModel):
    """A data model for a single review of a document section.

    This model encapsulates the review status, a summary assessment, identified
    defects, and other metadata for a specific section of a document.

    Attributes:
        section_id (str): The unique identifier of the section under review.
        status (str): The final review status. Must be one of 'approve', 'revise',
            or 'human_validation_required'.
        overall_assessment (str): A high-level textual summary of the review
            findings.
        defects (List[Defect]): A list of specific `Defect` objects identified in
            the section. Defaults to an empty list.
        approval_conditions (List[str]): A list of conditions that must be met for
            section approval. Defaults to an empty list.
        review_notes (List[str]): A list of general textual notes from the
            reviewer. Defaults to an empty list.
    """
    section_id: str
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []


class VersionMetadata(BaseModel):
    """Encapsulates versioning and provenance metadata for a generated artifact.

    This Pydantic model provides a structured representation for tracking the
    lineage of artifacts such as machine learning models, datasets, or other
    processed data. It captures essential information regarding the artifact's
    version, source, and creation context.

    Attributes:
        artifact_type: The category or type of the artifact (e.g., 'model',
            'dataset').
        artifact_version: The semantic version string of the artifact. Defaults
            to "1.0.0".
        source_version: An optional version identifier for the source from which
            the artifact was generated, such as a Git commit hash.
            Defaults to None.
        timestamp_utc: The UTC timestamp of metadata creation in ISO 8601 format.
            Defaults to the current time via `datetime.now(timezone.utc)`.
        run_id: An optional unique identifier for the specific execution or run
            that produced the artifact. Defaults to None.
    """
    artifact_type: str
    artifact_version: str = "1.0.0"
    source_version: Optional[str] = None
    timestamp_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    run_id: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)


class VersionedPayload(BaseModel):
    """A base Pydantic model for data payloads with versioning metadata.

    This model serves as a standard base class for other Pydantic models that
    require a common structure for tracking data provenance. It introduces a
    single optional field, `generation_metadata`, to store information about the
    payload's creation context.

    The class is configured with `populate_by_name=True`, and the
    `generation_metadata` field is assigned the alias `_generation_metadata`.
    This configuration enables flexible model initialization from data sources
    that may use either `generation_metadata` or `_generation_metadata` as the
    field name.

    Attributes:
        generation_metadata: An optional container for metadata about the payload's
            generation, such as software version and creation timestamp.
    """
    model_config = ConfigDict(populate_by_name=True)

    generation_metadata: Optional[VersionMetadata] = Field(
        default=None, alias="_generation_metadata"
    )
