"""
Repositorio de prompts para la sección GAP.
"""

def get_gap_writer_prompt(findings_pretty: str, scoring_pretty: str, asis_pretty: str, tobe_pretty: str, tower_definition_pretty: str, tower_label: str, feedback_block: str) -> str:
    return f"""
Actua como el agente Writer del Assessment Engine.

Tu trabajo es redactar SOLO la seccion GAP de la torre {tower_label}.

Reglas:
- Usa exclusivamente la informacion incluida en INPUT_FINDINGS, INPUT_SCORING, INPUT_ASIS, INPUT_TOBE e INPUT_TOWER_DEFINITION.
- No inventes brechas, capacidades ni implicaciones no soportadas.
- No conviertas esta seccion en un roadmap ni en un plan temporal.
- Mantén tono profesional, tecnico y ejecutivo.
- Redacta en castellano.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- La seccion debe explicar la brecha entre estado actual y estado objetivo por pilar.
- Cada gap debe incluir consecuencia operativa clara.
- En notes_for_reviewer no repitas frases prohibidas ni expliques que las has eliminado; usa solo observaciones metodologicas neutrales si son necesarias.
{feedback_block}

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "gap",
  "status": "draft",
  "tower_id": "...",
  "tower_name": "...",
  "section_title": "GAP Analysis",
  "introduction": "...",
  "gap_items": [
    {{
      "pillar": "...",
      "as_is_summary": "...",
      "target_state": "...",
      "key_gap": "...",
      "operational_implication": "..."
    }}
  ],
  "cross_cutting_gap_summary": ["..."],
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

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()

def get_gap_reviewer_prompt(draft_pretty: str, findings_pretty: str, scoring_pretty: str, asis_pretty: str, tobe_pretty: str, tower_definition_pretty: str, tower_label: str) -> str:
    return f"""
Actua como el agente Reviewer del Assessment Engine.

Tu trabajo es revisar SOLO la seccion GAP de la torre {tower_label}.

Debes revisar:
1. Consistencia con los hallazgos.
2. Consistencia con el scoring.
3. Coherencia entre INPUT_ASIS e INPUT_TOBE.
4. Calidad profesional del texto.
5. Ausencia de gaps o implicaciones inventadas.
6. Claridad metodologica.
7. Calidad de la formulacion de la brecha por pilar.

Reglas:
- No reescribas el documento completo.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- Si detectas defectos, marca "status": "revise".
- Si el texto es suficientemente bueno, marca "status": "approve".
- Solo usa "human_validation_required" si falta informacion imprescindible para sostener un gap central.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- No apliques reglas externas.
- Las notes_for_reviewer no son bloqueantes por defecto.
- Si solo sirven para enriquecer el documento, muevelas a review_notes y devuelve "approve".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "gap",
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

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()
