"""Provides the collection of prompts required for generating the Gap Analysis and Proposal (GAP) section."""


def get_gap_writer_prompt(
    findings_pretty: str,
    scoring_pretty: str,
    asis_pretty: str,
    tobe_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
    feedback_block: str,
) -> str:
    """Constructs the prompt for the GAP analysis Writer agent.

    This function populates a predefined Spanish-language template to generate a
    prompt for a Large Language Model (LLM). The prompt directs the LLM to act
    as a 'Writer' agent, synthesizing multiple inputs related to a technical
    assessment. The goal is to produce a structured JSON object containing a
    detailed GAP analysis for a specific assessment tower.

    Args:
        findings_pretty: String representation of the assessment's findings.
        scoring_pretty: String representation of the scoring details for the tower.
        asis_pretty: String representation of the current ('as-is') state.
        tobe_pretty: String representation of the target ('to-be') state.
        tower_definition_pretty: String representation of the tower's
            methodological definition.
        tower_label: The display name of the assessment tower (e.g., 'Security').
        feedback_block: An optional string containing corrective feedback from prior
            generation attempts to guide the LLM.

    Returns:
        The complete, formatted prompt string in Spanish, ready for use with an
        LLM.
    """
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


def get_gap_reviewer_prompt(
    draft_pretty: str,
    findings_pretty: str,
    scoring_pretty: str,
    asis_pretty: str,
    tobe_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
) -> str:
    r"""{'docstring': "Constructs the prompt for an AI agent to review a GAP analysis section.\n\nGenerates a detailed prompt in Spanish that instructs an AI agent to review\nthe GAP analysis section of a technical assessment. The prompt assembles\ncontextual data from the assessment (findings, scoring, AS-IS/TO-BE states),\nthe official tower methodology, and a set of explicit review rules. It also\ndefines the exact JSON schema required for the agent's output.\n\nArgs:\n    draft_pretty: A string representation of the draft GAP section to be\n        reviewed.\n    findings_pretty: A string representation of the findings section, used for\n        contextual consistency validation.\n    scoring_pretty: A string representation of the scoring section, used for\n        contextual consistency validation.\n    asis_pretty: A string representation of the AS-IS state description.\n    tobe_pretty: A string representation of the TO-BE state description.\n    tower_definition_pretty: A string representation of the tower's\n        methodological definition, serving as the ground truth for the review.\n    tower_label: The label of the tower under review, used to scope the\n        agent's task.\n\nReturns:\n    A formatted string containing the complete prompt in Spanish for the AI\n    reviewer agent."}."""
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
