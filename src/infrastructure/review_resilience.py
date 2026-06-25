"""Encapsulates the core business logic and foundational utilities for the Assessment Engine's processing pipeline."""

import json
from typing import Any, cast


def _to_dict(obj: Any) -> Any:
    if hasattr(obj, "model_dump"):
        return cast(dict[str, Any], obj.model_dump())
    if hasattr(obj, "dict"):
        return cast(dict[str, Any], obj.dict())
    if isinstance(obj, dict):
        return cast(dict[str, Any], obj or {})
    return {}.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return cast(dict[str, Any], obj or {})


def build_corrective_feedback(review: dict) -> list[str]:
    """Generates a list of corrective feedback strings from a review dictionary.

    This function processes a review dictionary to extract and format feedback. It
    combines structured information from the 'defects' key with simple string
    feedback from the 'approval_conditions' key into a single list.

    For each defect dictionary, the string values associated with 'type', 'message',
    and 'suggested_fix' keys are stripped of whitespace and joined with a single
    space to form one feedback string. For each approval condition, the string is
    simply stripped of whitespace.

    The function is robust against missing keys and non-string values within the
    data structures, which are coerced to strings. Empty or whitespace-only
    feedback strings are filtered out from the final result.

    Args:
        review: A dictionary representing a code review. The expected (but
            optional) keys are 'defects' and 'approval_conditions'.
            - 'defects' (list[dict]): A list of defect objects.
            - 'approval_conditions' (list[str]): A list of feedback strings.

    Returns:
        list[str]: A consolidated list of formatted feedback strings. Formatted
            strings from 'defects' appear first, in their original order,
            followed by the strings from 'approval_conditions'.

    Raises:
        TypeError: If a value for 'defects' or 'approval_conditions' is provided
            but is not iterable (e.g., an integer instead of a list).
    """
    review = _to_dict(review)
    defects = review.get("defects", []) or []
    approval_conditions = review.get("approval_conditions", []) or []
    feedback = [
        " ".join(
            part
            for part in [
                str(item.get("type", "")).strip(),
                str(item.get("message", "")).strip(),
                str(item.get("suggested_fix", "")).strip(),
            ]
            if part
        ).strip()
        for item in defects
    ]
    feedback.extend(
        str(item).strip() for item in approval_conditions if str(item).strip()
    )
    return [item for item in feedback if item]


def inject_manual_revision_note(
    draft: dict[str, Any], review: dict[str, Any], note_field: str
) -> Any:
    """Injects a manual revision note from review feedback into a deep copy of a document.

    The function first creates a deep copy of the `draft` dictionary using JSON
    serialization to prevent mutation of the original object. It then generates a
    standardized revision note from the `review` data and injects it into the
    specified `note_field` of the new document copy.

    If the target `note_field` already contains a non-empty string, the new
    note is appended to the existing value, but only if the note is not already
    present as a substring. If the field is empty or does not exist, its value
    is set to the generated note.

    Args:
        draft (dict[str, Any]): The document to be annotated. The dictionary must be
            fully JSON-serializable.
        review (dict[str, Any]): The review data containing feedback used to
            construct the revision note.
        note_field (str): The key within the `draft` dictionary where the note
            will be injected.

    Returns:
        dict[str, Any]: A new dictionary containing a deep copy of the original
            draft, augmented with the manual revision note.

    Raises:
        TypeError: If the `draft` dictionary contains non-JSON-serializable
            objects.
    """
    approved = json.loads(json.dumps(draft, ensure_ascii=False))
    review_issues = build_corrective_feedback(review)
    issue_text = (
        review_issues[0]
        if review_issues
        else "Persisten observaciones editoriales o de calidad no resueltas automáticamente."
    )
    note = (
        "Nota de revisión pendiente: este contenido se entrega para no bloquear el flujo, "
        "pero requiere ajuste manual posterior. " + issue_text
    ).strip()

    current = approved.get(note_field)
    if isinstance(current, str) and current.strip():
        if note not in current:
            approved[note_field] = current.rstrip() + " " + note
    else:
        approved[note_field] = note

    return approved


def force_approve_review(review: dict, reason: str) -> dict:
    r"""{'docstring': "Forcefully approves a review by setting its status and appending a note.\n\nA deep copy of the input `review` is created via JSON serialization to\nprevent mutation of the original object. The copy's 'status' field is\nset to 'approve', and the provided `reason` is appended to its\n'review_notes' list.\n\nIf the 'review_notes' key does not exist or its value is not a list,\nit is initialized as a new list before the reason is appended.\n\nArgs:\n    review (dict): The review object to approve. This dictionary is not\n        mutated.\n    reason (str): The justification note to append to the review's notes.\n\nReturns:\n    dict: A new dictionary representing the approved review with an updated\n        status and review note.\n\nRaises:\n    TypeError: If the input `review` dictionary contains values that are not\n        JSON-serializable."}."""
    review = _to_dict(review)
    normalized = json.loads(json.dumps(review, ensure_ascii=False))
    normalized["status"] = "approve"
    notes = normalized.get("review_notes", [])
    if not isinstance(notes, list):
        notes = []
    notes.append(reason)
    normalized["review_notes"] = notes
    return normalized
