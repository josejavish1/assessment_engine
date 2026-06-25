"""JSON Extraction and Parsing Utilities.

Provides highly robust parsing and recovery logic for JSON payloads generated
by AI agents, ensuring deterministic data retrieval under malformed text.
"""

import json
import re


def parse_json_from_text(text: str):
    """Extracts and parses a JSON object or array from a raw text string.

    This function is designed to robustly locate and decode a JSON payload
    embedded within a larger string, a common scenario when processing outputs from
    language models. It first strips common Markdown code fences (e.g., ```json)
    from the input. It then attempts a direct parse. If this fails, it employs a
    fallback heuristic to find and isolate the first-occurring, outermost balanced
    JSON object ('{...}') or array ('[...]') within the string before attempting
    to parse it again.

    Args:
        text (str): The input string potentially containing an embedded JSON object
            or array.

    Returns:
        Any: The deserialized Python object (e.g., dict, list) from the parsed
        JSON.

    Raises:
        json.JSONDecodeError: If the input text is empty, contains no discernible
            JSON structure, or if the final extracted candidate string is not
            valid JSON.
    """
    raw = (text or "").strip()
    if not raw:
        raise json.JSONDecodeError("Empty model output", raw, 0)

    # Caso típico: ```json ... ```
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned, flags=re.IGNORECASE).strip()

    # Intento directo
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback heuristic: isolate and extract the first balanced JSON object or array structure.
    obj_start = cleaned.find("{")
    arr_start = cleaned.find("[")
    starts = [x for x in [obj_start, arr_start] if x != -1]
    if not starts:
        raise json.JSONDecodeError(
            "No JSON object/array found in model output", cleaned, 0
        )

    start = min(starts)
    end_obj = cleaned.rfind("}")
    end_arr = cleaned.rfind("]")
    end = max(end_obj, end_arr)

    if end == -1 or end <= start:
        raise json.JSONDecodeError(
            "Incomplete JSON block in model output", cleaned, start
        )

    candidate = cleaned[start : end + 1]
    return json.loads(candidate)
