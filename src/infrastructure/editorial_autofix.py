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
    cloned = json.loads(json.dumps(draft, ensure_ascii=False))
    updated, count = _walk(cloned)
    return cast(Dict[str, Any], updated) if isinstance(updated, dict) else {}, count


def should_autofix_editorial(review: Any) -> bool:
    return False
