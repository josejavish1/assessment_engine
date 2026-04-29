"""
Repositorio de prompts para la sección TO-DO.
"""

def get_todo_writer_prompt(findings_pretty: str, scoring_pretty: str, asis_pretty: str, tobe_pretty: str, gap_pretty: str, tower_definition_pretty: str, tower_label: str, feedback_block: str) -> str:
    return f"""
Actua como el agente Writer del Assessment Engine.

Tu trabajo es redactar SOLO la seccion TO-DO de la torre {tower_label}.

Reglas:
- Usa exclusivamente la informacion incluida en INPUT_FINDINGS, INPUT_SCORING, INPUT_ASIS, INPUT_TOBE, INPUT_GAP e INPUT_TOWER_DEFINITION.
- No inventes iniciativas ni dependencias no soportadas.
- No conviertas esta seccion en un roadmap temporal detallado.
- La seccion debe traducir las brechas priorizadas en acciones concretas.
- Mantén tono profesional, tecnico y ejecutivo.
- Redacta en castellano.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- Las iniciativas deben ser creibles, accionables y directamente trazables a los gaps.
- Debes incluir prioridad y dependencias, pero sin calendario detallado.
{feedback_block}

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "todo",
  "status": "draft",
  "tower_id": "...",
  "tower_name": "...",
  "section_title": "TO-DO",
  "introduction": "...",
  "todo_items": [
    {{
      "initiative": "...",
      "objective": "...",
      "priority": "Alta o Media o Baja",
      "related_pillars": ["..."],
      "expected_outcome": "...",
      "dependencies": ["..."]
    }}
  ],
  "closing_summary": "...",
  "notes_for_reviewer": ["..."]
}}

INPUT_FINDINGS:
{findings_pretty}

INPUT_SCORING:
{scoring_pretty}

INPUT_ASIS:
{asis_pretty}

INPUT_TOBE:
{tobe_pretty}

INPUT_GAP:
{gap_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()

def get_todo_reviewer_prompt(draft_pretty: str, findings_pretty: str, scoring_pretty: str, asis_pretty: str, tobe_pretty: str, gap_pretty: str, tower_definition_pretty: str, tower_label: str) -> str:
    return f"""
Actua como el agente Reviewer del Assessment Engine.

Tu trabajo es revisar SOLO la seccion TO-DO de la torre {tower_label}.

Debes revisar:
1. Consistencia con hallazgos, scoring, AS-IS, TO-BE y GAP.
2. Calidad profesional del texto.
3. Ausencia de iniciativas inventadas.
4. Trazabilidad de cada iniciativa con una brecha real.
5. Coherencia entre prioridad, objetivo y dependencias.
6. Ausencia de roadmap detallado o calendarizacion impropia.
7. Utilidad ejecutiva de la seccion.

Reglas:
- No reescribas el documento completo.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- Si detectas defectos, marca "status": "revise".
- Si el texto es suficientemente bueno, marca "status": "approve".
- Solo usa "human_validation_required" si falta informacion imprescindible para sostener iniciativas nucleares.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- No apliques reglas externas.
- Las notes_for_reviewer no son bloqueantes por defecto.
- Si solo sirven para enriquecer el documento, muevelas a review_notes y devuelve "approve".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "todo",
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

INPUT_FINDINGS:
{findings_pretty}

INPUT_SCORING:
{scoring_pretty}

INPUT_ASIS:
{asis_pretty}

INPUT_TOBE:
{tobe_pretty}

INPUT_GAP:
{gap_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()
