"""Provides the core logic and utility functions for the Assessment Engine's automated editorial correction pipeline."""

import json
import re

EDITORIAL_REPLACEMENTS = {
    "todavia": "todavía",
    "Todavia": "Todavía",
    "aun no": "aún no",
    "Aun no": "Aún no",
    "basico": "básico",
    "Basico": "Básico",
    "tecnico": "técnico",
    "Tecnico": "Técnico",
    "tecnica": "técnica",
    "Tecnica": "Técnica",
    "tecnicas": "técnicas",
    "Tecnicas": "Técnicas",
    "tecnicos": "técnicos",
    "Tecnicos": "Técnicos",
    "metodologica": "metodológica",
    "Metodologica": "Metodológica",
    "metodologico": "metodológico",
    "Metodologico": "Metodológico",
    "critica": "crítica",
    "Critica": "Crítica",
    "criticas": "críticas",
    "Criticas": "Críticas",
    "valida": "válida",
    "Valida": "Válida",
    "validacion": "validación",
    "Validacion": "Validación",
}


def _replace_text(text: str) -> tuple[str, int]:
    updated = text
    replacements = 0
    for source, target in EDITORIAL_REPLACEMENTS.items():
        pattern = rf"(?<!\w){re.escape(source)}(?!\w)"
        updated, count = re.subn(pattern, target, updated)
        replacements += count
    return updated, replacements


def _walk(value):
    if isinstance(value, str):
        updated, replacements = _replace_text(value)
        return updated, replacements
    if isinstance(value, list):
        out = []
        replacements = 0
        for item in value:
            updated_item, count = _walk(item)
            out.append(updated_item)
            replacements += count
        return out, replacements
    if isinstance(value, dict):
        out = {}
        replacements = 0
        for key, item in value.items():
            updated_item, count = _walk(item)
            out[key] = updated_item
            replacements += count
        return out, replacements
    return value, 0


def should_autofix_editorial(defects: list[dict]) -> bool:
    """Assess whether a list of defects exclusively comprises minor editorial issues.

    This function evaluates a list of defect dictionaries to determine if the
    entire set qualifies for an automated editorial fix. A list qualifies only if
    it is non-empty and every defect within it satisfies two conditions:

    1. The 'severity' of the defect must be 'minor'.
    2. The 'type' or 'message' string must contain one of the following
       substrings: "orthograph", "ortograf", "editorial", or "estilo".

    The checks are performed in a case-insensitive manner after stripping
    leading and trailing whitespace from the relevant string values.

    Args:
        defects: A list of dictionaries, where each dictionary represents a
            single defect. The function defensively handles missing or non-string
            values for 'severity', 'type', and 'message' keys.

    Returns:
        True if the list is non-empty and all defects meet the specified
        editorial criteria, False otherwise. This includes returning False
        for an empty or None input list.
    """
    for defect in defects or []:
        severity = str(defect.get("severity", "")).strip().lower()
        defect_type = str(defect.get("type", "")).strip().lower()
        message = str(defect.get("message", "")).strip().lower()
        if severity != "minor":
            return False
        if not any(
            token in defect_type or token in message
            for token in ("orthograph", "ortograf", "editorial", "estilo")
        ):
            return False
    return bool(defects)


def apply_editorial_autofix(draft: dict) -> tuple[dict, int]:
    r"""{'docstring': 'Apply automated editorial fixes to a document draft.\n\n    Performs a deep copy of the input `draft` via JSON serialization and\n    deserialization to ensure the original object is not mutated. The function\n    then recursively traverses the copied data structure, applying a set of\n    predefined editorial corrections to all string values.\n\n    Args:\n        draft: A JSON-serializable dictionary representing the document to be\n            processed.\n\n    Returns:\n        A tuple containing the modified dictionary with all fixes applied and an\n        integer count of the total number of replacements made.\n\n    Raises:\n        TypeError: If the input `draft` contains non-JSON-serializable types.'}."""
    cloned = json.loads(json.dumps(draft, ensure_ascii=False))
    updated, replacements = _walk(cloned)
    return updated, replacements
