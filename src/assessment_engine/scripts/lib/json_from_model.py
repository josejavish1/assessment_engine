"""
Módulo json_from_model.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import json
import re


def parse_json_from_text(text: str):
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

    # Fallback: extraer el primer bloque JSON razonable
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
