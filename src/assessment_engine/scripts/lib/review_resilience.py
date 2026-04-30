"""
Módulo review_resilience.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import json


def _to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return obj


def build_corrective_feedback(review: dict) -> list[str]:
    review = _to_dict(review)
    defects = review.get("defects", []) or []
    approval_conditions = review.get("approval_conditions", []) or []
    feedback = [
        " ".join(
            part for part in [
                str(item.get("type", "")).strip(),
                str(item.get("message", "")).strip(),
                str(item.get("suggested_fix", "")).strip(),
            ] if part
        ).strip()
        for item in defects
    ]
    feedback.extend(str(item).strip() for item in approval_conditions if str(item).strip())
    return [item for item in feedback if item]


def inject_manual_revision_note(draft: dict, review: dict, note_field: str) -> dict:
    approved = json.loads(json.dumps(draft, ensure_ascii=False))
    review_issues = build_corrective_feedback(review)
    issue_text = review_issues[0] if review_issues else "Persisten observaciones editoriales o de calidad no resueltas automáticamente."
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
    review = _to_dict(review)
    normalized = json.loads(json.dumps(review, ensure_ascii=False))
    normalized["status"] = "approve"
    notes = normalized.get("review_notes", [])
    if not isinstance(notes, list):
        notes = []
    notes.append(reason)
    normalized["review_notes"] = notes
    return normalized
