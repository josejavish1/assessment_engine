"""
Módulo editorial_autofix.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

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
    cloned = json.loads(json.dumps(draft, ensure_ascii=False))
    updated, replacements = _walk(cloned)
    return updated, replacements
