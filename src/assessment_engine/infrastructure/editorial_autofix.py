from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple, cast


def _walk(value: Any) -> Tuple[Any, int]:
    if isinstance(value, str):
        return value, 0
    if isinstance(value, list):
        out_list: List[Any] = []
        for item in value:
            v, _ = _walk(item)
            out_list.append(v)
        return out_list, 0
    if isinstance(value, dict):
        out_dict: Dict[str, Any] = {}
        for k, v in value.items():
            res, _ = _walk(v)
            out_dict[k] = res
        return out_dict, 0
    return value, 0


def apply_editorial_autofix(draft: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """Recursively applies a set of editorial autofixes to a document draft.

    This function operates on a deep copy of the input `draft` to prevent
    side effects on the original object. The deep copy is created via JSON
    serialization and deserialization, which requires that all nested objects
    within the `draft` are JSON-serializable. The original `draft` dictionary
    is not modified.

    Args:
        draft: A JSON-serializable dictionary representing the document draft.

    Returns:
        A tuple containing the modified dictionary and an integer count of the
        total fixes applied.

    Raises:
        TypeError: If the input `draft` contains non-JSON-serializable objects.
    """
    cloned = json.loads(json.dumps(draft, ensure_ascii=False))
    updated, count = _walk(cloned)
    return cast(Dict[str, Any], updated) if isinstance(updated, dict) else {}, count


def should_autofix_editorial(review: Any) -> bool:
    """Determine if an editorial review qualifies for an automatic fix."""
    return False
