from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


def collect_all_strings(data: Any) -> List[str]:
    """Recursively traverses a data structure to collect all string values.

    This function performs a depth-first traversal of a nested structure
    composed of dictionaries and lists. It extracts all string literals it
    encounters and aggregates them into a single list. Non-string,
    non-collection scalar values (e.g., integers, booleans, floats) are ignored.

    Args:
        data (Any): The data structure to traverse, which may be a nested
            combination of dictionaries, lists, and other Python objects.

    Returns:
        List[str]: A flattened list containing all string values found within
            the input data structure. The order of strings corresponds to a
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
    r"""{'BaseDraftModel': "A Pydantic base model for content sections with phrase-based validation.\n\nProvides common fields for section identification and reviewer notes. Includes a\nbuilt-in validation mechanism that disallows specified phrases within the model's\ndata. Subclasses must override the `get_forbidden_phrases` method to define a\nlist of disallowed strings for validation to occur.\n\nAttributes:\n    section_id: The unique identifier for the content section.\n    notes_for_reviewer: A list of textual notes for a reviewer. Any note\n        containing a forbidden phrase is silently removed during validation.", 'BaseDraftModel.get_forbidden_phrases': "Return a list of forbidden phrases for validation.\n\nThis method serves as an extension point for subclasses to specify disallowed\nstrings. The base implementation returns an empty list, which disables phrase\nvalidation.\n\nReturns:\n    List[str]: A list of phrases that are forbidden within the model's fields.", 'BaseDraftModel.validate_forbidden_phrases': 'Validate model fields against a list of forbidden phrases.\n\nA Pydantic `model_validator` that executes post-initialization. This validator\nperforms a case-insensitive search for forbidden phrases obtained from the\n`get_forbidden_phrases` method.\n\nThe validation process consists of two steps:\n1.  The `notes_for_reviewer` list is filtered, silently removing any entry\n    that contains a forbidden phrase.\n2.  All other string-based fields within the model are recursively scanned.\n    Validation fails upon finding the first forbidden phrase.\n\nReturns:\n    The validated instance of the model (`self`), with the\n    `notes_for_reviewer` attribute potentially modified.\n\nRaises:\n    ValueError: If a forbidden phrase is detected in any string field,\n        excluding those in `notes_for_reviewer`.'}."""
    section_id: str
    notes_for_reviewer: List[str] = []

    def get_forbidden_phrases(self) -> List[str]:
        """Retrieve the list of phrases forbidden in a document.

        This method serves as an interface for subclasses to specify disallowed
        phrases. This base implementation returns an empty list, indicating that
        no phrases are forbidden by default.

        Returns:
            List[str]: A list of forbidden phrases.
        """
        return []

    @model_validator(mode="after")
    def validate_forbidden_phrases(self) -> "BaseDraftModel":
        """Validate model fields against a list of forbidden phrases.

        This Pydantic `model_validator` performs a case-insensitive check for
        forbidden phrases across all string fields of the model instance.

        The validation process has two distinct behaviors:
        1.  Filtering: The `notes_for_reviewer` field, expected to be a list
            of strings, is silently filtered. Any note containing a forbidden
            phrase is removed from the list.
        2.  Strict Validation: All other string fields within the model are
            recursively scanned. If a forbidden phrase is found, a `ValueError`
            is raised.

        Returns:
            The validated model instance. The `notes_for_reviewer` list may be
            modified as a result of the filtering process.

        Raises:
            ValueError: If a forbidden phrase is found in any string field of the
                model, excluding the elements of the `notes_for_reviewer` list.
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
    """Represents a single defect identified during analysis.

    This class uses Pydantic for data validation and serialization, ensuring
    that defect records conform to a predefined structure.

    Args:
        severity: The severity level, constrained to 'critical', 'major', or 'minor'.
        type: A category classifying the defect (e.g., 'Security', 'Style').
        message: A human-readable description of the identified issue.
        suggested_fix: A proposed solution or guidance for resolving the defect.
    """
    severity: str = Field(..., pattern="^(critical|major|minor)$")
    type: str
    message: str
    suggested_fix: str


class SectionReview(BaseModel):
    """Represents a single review for a specific section of a document.

    This model captures the outcome, identified defects, and any notes or conditions
    related to the review of a document section.

    Attributes:
        section_id (str): The unique identifier of the section under review.
        status (str): The review outcome, constrained to 'approve', 'revise', or
            'human_validation_required'.
        overall_assessment (str): A high-level summary of the reviewer's findings.
        defects (List[Defect]): A list of specific defects found in the section,
            defaulting to an empty list.
        approval_conditions (List[str]): Conditions that must be met for final
            approval, defaulting to an empty list.
        review_notes (List[str]): Additional notes or comments from the reviewer,
            defaulting to an empty list.
    """
    section_id: str
    status: str = Field(..., pattern="^(approve|revise|human_validation_required)$")
    overall_assessment: str
    defects: List[Defect] = []
    approval_conditions: List[str] = []
    review_notes: List[str] = []


class VersionMetadata(BaseModel):
    """A data model for capturing versioning and provenance metadata.

    This model standardizes metadata for artifacts such as models or datasets,
    providing a clear record of their origin and version history.

    Attributes:
        artifact_type (str): The category of the artifact (e.g., 'model', 'dataset').
        artifact_version (str): The semantic version of the artifact. Defaults to "1.0.0".
        source_version (Optional[str]): The version of the source code or data used
            to generate the artifact. Defaults to None.
        timestamp_utc (str): The UTC timestamp in ISO 8601 format indicating when the
            artifact was created. Defaults to the current time upon instantiation.
        run_id (Optional[str]): A unique identifier for the specific execution or run
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
    """A base Pydantic model for data payloads with optional versioning metadata.

    This model establishes a standard structure for data payloads that embed their
    own generation or versioning information. It utilizes Pydantic's aliasing
    mechanism, enabled by `populate_by_name=True`, to map the input data key
    `_generation_metadata` to the `generation_metadata` attribute. This allows
    for a more idiomatic attribute name in Python code while accommodating
    pseudo-private keys in serialized data sources.

    Attributes:
        generation_metadata: An optional `VersionMetadata` object containing details
            about the payload's origin or version. During model instantiation, this
            attribute is populated from the `_generation_metadata` key. Defaults
            to `None` if the key is absent.
    """
    model_config = ConfigDict(populate_by_name=True)

    generation_metadata: Optional[VersionMetadata] = Field(
        default=None, alias="_generation_metadata"
    )
