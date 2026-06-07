import json
import re
from typing import Any


def parse_json_from_text(text: str) -> Any:
    raw = (text or "").strip()
    if not raw:
        raise json.JSONDecodeError("Empty", raw, 0)
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    cleaned = match.group(1).strip() if match else raw
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start = -1
    for i, c in enumerate(cleaned):
        if c in ("{", "["):
            start = i
            break
    if start == -1:
        raise json.JSONDecodeError("No JSON", cleaned, 0)
    oc, cc = cleaned[start], ("}" if cleaned[start] == "{" else "]")
    cnt, end = 0, -1
    for i in range(start, len(cleaned)):
        if cleaned[i] == oc:
            cnt += 1
        elif cleaned[i] == cc:
            cnt -= 1
        if cnt == 0:
            end = i
            break
    if end != -1:
        try:
            return json.loads(cleaned[start : end + 1])
        except Exception:
            pass
    last_end = max(cleaned.rfind("}"), cleaned.rfind("]"))
    if last_end == -1 or last_end <= start:
        raise json.JSONDecodeError("Incomplete", cleaned, start)
    return json.loads(cleaned[start : last_end + 1])
