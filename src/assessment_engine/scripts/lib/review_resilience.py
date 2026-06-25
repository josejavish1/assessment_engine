"""Encapsulates the core business logic and utility functions for the Assessment Engine pipeline."""

import json


def _to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


def build_corrective_feedback(review: dict) -> list[str]:
    """Constructs a flattened list of corrective feedback strings from a review.

    This function processes a review dictionary by extracting and formatting
    feedback from two primary sources: 'defects' and 'approval_conditions'.
    Each entry in the 'defects' list, assumed to be a dictionary, is converted
    into a single string by concatenating its 'type', 'message', and
    'suggested_fix' values. Entries from the 'approval_conditions' list are
    included directly. The final result is a single list containing all
    non-empty, whitespace-stripped feedback messages.

    Args:
        review: A dictionary representing a code review. It is expected to contain
            optional keys: 'defects' (a list of dictionaries, where each
            dictionary may contain 'type', 'message', and 'suggested_fix' keys)
            and 'approval_conditions' (a list of strings).

    Returns:
        A list of formatted, non-empty feedback strings.

    Raises:
        AttributeError: If an element within the 'defects' list is not a
            dictionary-like object and lacks a `.get()` method.
        TypeError: If the value associated with 'defects' or
            'approval_conditions' is not an iterable (e.g., an integer
            instead of a list).
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


def inject_manual_revision_note(draft: dict, review: dict, note_field: str) -> dict:
    """Injects a manual revision note into a copy of a content draft.

    This function generates a note based on review feedback and inserts it into
    a specified field of a content draft. It operates on a deep copy of the
    input `draft`, ensuring the original dictionary remains unmodified. The deep
    copy is created using JSON serialization and deserialization.

    If the target `note_field` already exists and contains a non-empty string,
    the new note is appended, separated by a space. The append operation is
    idempotent; the note is not added if it is already a substring of the
    existing content. If the field does not exist or is empty, it is set to
    the generated note's value.

    Args:
        draft: The source content dictionary. This object is not mutated.
        review: A dictionary containing review feedback used to generate the
            note's text content.
        note_field: The dictionary key under which the revision note will be
            stored in the output draft.

    Returns:
        A new dictionary instance representing a deep copy of the original
        draft, modified to include the manual revision note.
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
    """Updates a review's status to 'approve' and appends a justification note.

    This function performs a non-mutating update by creating a deep copy of the
    input `review` dictionary through JSON serialization and deserialization. It
    sets the `status` key to the literal string 'approve'.

    The provided `reason` is appended to the `review_notes` list. If the
    `review_notes` key does not exist or its value is not a list, it will be
    initialized as a new list before the reason is appended.

    Args:
        review (dict): The review object to be approved. The contents of this
            dictionary must be JSON-serializable.
        reason (str): The justification for the force-approval action.

    Returns:
        dict: A new dictionary representing the approved review.

    Raises:
        TypeError: If the input `review` dictionary contains non-JSON-serializable
            types.
    """
    review = _to_dict(review)
    normalized = json.loads(json.dumps(review, ensure_ascii=False))
    normalized["status"] = "approve"
    notes = normalized.get("review_notes", [])
    if not isinstance(notes, list):
        notes = []
    notes.append(reason)
    normalized["review_notes"] = notes
    return normalized
