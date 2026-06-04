"""
Repositorio de prompts para la sección Conclusion.
"""


def get_conclusion_writer_prompt(
    scoring_pretty: str,
    asis_pretty: str,
    risks_pretty: str,
    tobe_pretty: str,
    gap_pretty: str,
    todo_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
    feedback_block: str,
) -> str:
    return f"""
Actua como el agente Writer del Assessment Engine.

Tu trabajo es redactar SOLO la seccion Conclusion de la torre {tower_label}.

Reglas:
- Usa exclusivamente la informacion incluida en INPUT_SCORING, INPUT_ASIS, INPUT_RISKS, INPUT_TOBE, INPUT_GAP, INPUT_TODO e INPUT_TOWER_DEFINITION.
- No inventes afirmaciones no soportadas.
- No conviertas esta seccion en un roadmap detallado.
- Mantén tono profesional, tecnico y ejecutivo.
- Redacta en castellano.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- La conclusion debe sintetizar el mensaje ejecutivo final de la torre.
- Debe dejar claro el punto de partida, la brecha dominante y la direccion de evolucion.
{feedback_block}

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "conclusion",
  "status": "draft",
  "tower_id": "...",
  "tower_name": "...",
  "section_title": "Conclusion",
  "final_assessment": "...",
  "executive_message": "...",
  "priority_focus_areas": ["..."],
  "closing_statement": "...",
  "notes_for_reviewer": ["..."]
}}

INPUT_SCORING:
{scoring_pretty}

INPUT_ASIS:
{asis_pretty}

INPUT_RISKS:
{risks_pretty}

INPUT_TOBE:
{tobe_pretty}

INPUT_GAP:
{gap_pretty}

INPUT_TODO:
{todo_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()


def get_conclusion_reviewer_prompt(
    draft_pretty: str,
    scoring_pretty: str,
    asis_pretty: str,
    risks_pretty: str,
    tobe_pretty: str,
    gap_pretty: str,
    todo_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
) -> str:
    return f"""
Actua como el agente Reviewer del Assessment Engine.

Tu trabajo es revisar SOLO la seccion Conclusion de la torre {tower_label}.

Debes revisar:
1. Consistencia con el scoring.
2. Coherencia con AS-IS, Riesgos, TO-BE, GAP y TO-DO.
3. Calidad profesional del texto.
4. Ausencia de afirmaciones inventadas.
5. Utilidad ejecutiva real de la conclusion.
6. Claridad del mensaje final.
7. Coherencia metodologica.

Reglas:
- No reescribas el documento completo.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- Si detectas defectos, marca "status": "revise".
- Si el texto es suficientemente bueno, marca "status": "approve".
- Solo usa "human_validation_required" si falta informacion imprescindible para sostener la conclusion.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- No apliques reglas externas.
- Las notes_for_reviewer no son bloqueantes por defecto.
- Si solo sirven para enriquecer el documento, muevelas a review_notes y devuelve "approve".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "conclusion",
  "status": "approve o revise o human_validation_required",
  "overall_assessment": "Texto del resumen de la revisión.",
  "defects": [
    {{
      "severity": "critical o major o minor",
      "type": "tipo_de_error",
      "message": "Descripción del error.",
      "suggested_fix": "Solución propuesta."
    }}
  ],
  "approval_conditions": ["Condición 1"],
  "review_notes": ["Nota general 1 (solo strings)"]
}}

INPUT_DRAFT:
{draft_pretty}

INPUT_SCORING:
{scoring_pretty}

INPUT_ASIS:
{asis_pretty}

INPUT_RISKS:
{risks_pretty}

INPUT_TOBE:
{tobe_pretty}

INPUT_GAP:
{gap_pretty}

INPUT_TODO:
{todo_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()
