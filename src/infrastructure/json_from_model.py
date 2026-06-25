import json
import re
from typing import Any


def parse_json_from_text(text: str) -> Any:
    """Extracts and parses the first valid JSON object from a string.

    Robustly finds and decodes a JSON object from a string that may contain
    surrounding text or markdown code fences. The function applies a sequence
    of heuristics to locate a parsable JSON substring:
    1.  It searches for a markdown JSON code block (e.g., ```json) and
        extracts its content. If no block is found, the entire string is
        processed.
    2.  It attempts to parse the resulting string directly.
    3.  If parsing fails, it finds the first opening brace '{' or bracket '['
        and scans to find the corresponding balanced closing character, then
        attempts to parse that substring.
    4.  As a final fallback for potentially truncated or malformed inputs, it
        attempts to parse the substring from the first opening character to the
        last closing character ('}' or ']').

    Args:
        text: The input string from which to extract JSON. A value of `None` is
            treated as an empty string.

    Returns:
        The parsed Python object, typically a `dict` or a `list`.

    Raises:
        json.JSONDecodeError: If the input string is empty, lacks any JSON
            object or array start characters ('{' or '['), or if no valid JSON
            object can be decoded after all heuristics are attempted.
    """
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
