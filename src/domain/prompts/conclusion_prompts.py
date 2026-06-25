"""Provides prompts for generating the 'Conclusion' section of a document."""


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
    """Assembles the prompt for the Conclusion Writer agent.

    This function constructs a detailed prompt for a language model tasked with
    generating the conclusion section of a technology assessment. It integrates
    various analytical inputs, such as scoring, state analysis (AS-IS and TO-BE),
    risks, gap analysis, and action items, into a structured set of instructions.

    Args:
        scoring_pretty: A string containing the formatted scoring data.
        asis_pretty: A string containing the formatted "As-Is" (current state)
            analysis.
        risks_pretty: A string containing the formatted risk analysis.
        tobe_pretty: A string containing the formatted "To-Be" (desired future
            state) description.
        gap_pretty: A string containing the formatted gap analysis between the
            current and future states.
        todo_pretty: A string containing the formatted action items.
        tower_definition_pretty: A string containing the formatted definition of
            the technology assessment tower.
        tower_label: The display label for the assessment tower, used for
            contextualization within the prompt.
        feedback_block: A string containing supplementary instructions or feedback
            to guide the agent's output.

    Returns:
        A complete, formatted prompt string to be sent to a language model.
    """
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

    The generated prompt instructs an AI agent to act as a reviewer for the
    conclusion section of a technical assessment. The agent is directed to
    evaluate the conclusion's consistency with other report sections (e.g.,
    scoring, AS-IS, risks, TO-BE), its overall quality, and its adherence to
    the provided methodological definition. The agent's findings are expected
    to be returned in a structured JSON format.

    Args:
        draft_pretty: A string containing the formatted conclusion draft for
            review.
        scoring_pretty: A string containing the formatted scoring section for
            consistency validation.
        asis_pretty: A string containing the formatted AS-IS section for
            contextual reference.
        risks_pretty: A string containing the formatted risks section for
            contextual reference.
        tobe_pretty: A string containing the formatted TO-BE section for
            contextual reference.
        gap_pretty: A string containing the formatted GAP analysis section for
            contextual reference.
        todo_pretty: A string containing the formatted TO-DO section for
            contextual reference.
        tower_definition_pretty: A string containing the formatted methodological
            definition for the specified tower, used as the ground truth for
            review.
        tower_label: The string identifier for the specific assessment tower.

    Returns:
        A complete, formatted prompt string to be sent to the AI reviewer
        agent.
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
