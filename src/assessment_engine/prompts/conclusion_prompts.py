"""Specifies prompts for synthesizing the 'Conclusion' section of a generated report."""


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
    r"""{'docstring': "Constructs the prompt for the LLM-based Conclusion Writer agent.\n\n    Assembles a prompt instructing a language model to generate the 'Conclusion'\n    section for a specific assessment tower. The function interpolates\n    pre-formatted strings representing various assessment sections (e.g., scoring,\n    as-is, risks) into a master template. The resulting prompt directs the model\n    to return a structured JSON object.\n\n    Args:\n        scoring_pretty: A string containing the pre-formatted scoring data.\n        asis_pretty: A string containing the pre-formatted 'As-Is' section data.\n        risks_pretty: A string containing the pre-formatted 'Risks' section data.\n        tobe_pretty: A string containing the pre-formatted 'To-Be' section data.\n        gap_pretty: A string containing the pre-formatted gap analysis data.\n        todo_pretty: A string containing the pre-formatted 'To-Do' section data.\n        tower_definition_pretty: A string containing the pre-formatted tower\n            definition.\n        tower_label: The name or label of the assessment tower being processed.\n        feedback_block: A string containing additional rules or feedback to be\n            injected into the prompt's instruction set.\n\n    Returns:\n        A fully-formed string prompt for the Conclusion Writer agent."}."""
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
    """Constructs a prompt for an AI agent to review an assessment's conclusion.

    This function assembles a multi-part prompt in Spanish that instructs a
    large language model to act as a technical reviewer for the 'Conclusion'
    section of an assessment report. It integrates various report sections as
    context to ensure a comprehensive and coherent review. The resulting prompt
    specifies the review criteria, required JSON output schema, and operational
    rules for the AI agent.

    Args:
        draft_pretty: A formatted string representation of the draft conclusion
            to be reviewed.
        scoring_pretty: A formatted string representation of the report's
            scoring section.
        asis_pretty: A formatted string representation of the report's AS-IS
            analysis section.
        risks_pretty: A formatted string representation of the report's risks
            section.
        tobe_pretty: A formatted string representation of the report's TO-BE
            state section.
        gap_pretty: A formatted string representation of the report's GAP
            analysis section.
        todo_pretty: A formatted string representation of the report's TO-DO or
            action plan section.
        tower_definition_pretty: A formatted string representation of the tower's
            methodological definition, which serves as the ground truth for the
            review.
        tower_label: The name or identifier for the assessment tower being
            evaluated.

    Returns:
        A single string containing the complete, formatted prompt in Spanish,
        ready for submission to the AI model.
    """
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
