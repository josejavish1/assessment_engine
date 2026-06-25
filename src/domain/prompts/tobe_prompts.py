"""Provides a centralized repository of prompt templates for the TO-BE analysis component."""


def get_tobe_writer_prompt(
    findings_pretty: str,
    scoring_pretty: str,
    case_input_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
    feedback_block: str,
) -> str:
    """Constructs a Spanish-language prompt for a language model agent.

    This function generates a prompt instructing a "Writer" agent to create the
    "TO-BE" section for an assessment report concerning a specific technology
    tower. The prompt includes the contextual "AS-IS" analysis data,
    methodological definitions, explicit generation rules, and a required
    JSON output schema.

    Args:
        findings_pretty: A string representation of the 'AS-IS' analysis findings.
        scoring_pretty: A string representation of the 'AS-IS' scoring results.
        case_input_pretty: A string representation of the initial case input data.
        tower_definition_pretty: A string representation of the methodological
            definition for the relevant assessment tower.
        tower_label: The display name of the assessment tower.
        feedback_block: A string containing supplemental instructions or feedback
            to be injected into the prompt's rules section.

    Returns:
        A complete prompt string in Spanish, structured to guide a language
        model in generating a specific JSON output.
    """
    return f"""
Actua como el agente Writer del Assessment Engine.

Tu trabajo es redactar SOLO la seccion TO-BE de la torre {tower_label}.

Reglas:
- Usa exclusivamente la informacion incluida en INPUT_FINDINGS, INPUT_SCORING, INPUT_CASE_INPUT e INPUT_TOWER_DEFINITION.
- No inventes capacidades objetivo ni principios no soportadas.
- No conviertas esta seccion en un roadmap ni en una lista de quick wins.
- No hables de horizontes temporales ni de plan de evolucion.
- Mantén tono profesional, tecnico y ejecutivo.
- Redacta en castellano.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- El TO-BE por defecto debe alinearse con nivel 4 salvo que los inputs justifiquen otra cosa.
- Debes definir un estado objetivo creible, no utopico.
{feedback_block}

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "tobe",
  "status": "draft",
  "tower_id": "...",
  "tower_name": "...",
  "section_title": "TO-BE",
  "introduction": "...",
  "target_maturity": {{
    "recommended_level": "Nivel 4 - Optimizado",
    "recommended_score_reference": "4.0",
    "justification": "..."
  }},
  "target_capabilities_by_pillar": [
    {{
      "pillar": "...",
      "target_capabilities": ["..."]
    }}
  ],
  "architecture_principles": ["..."],
  "operating_model_implications": ["..."],
  "notes_for_reviewer": ["..."]
}}

INPUT_FINDINGS:
{findings_pretty}

INPUT_SCORING:
{scoring_pretty}

INPUT_CASE_INPUT:
{case_input_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()


def get_tobe_reviewer_prompt(
    draft_pretty: str,
    findings_pretty: str,
    scoring_pretty: str,
    case_input_pretty: str,
    tower_definition_pretty: str,
    tower_label: str,
) -> str:
    """Constructs the prompt for a Large Language Model to review a 'TO-BE' section.

    This function assembles a detailed prompt in Spanish instructing an LLM agent
    to act as a reviewer for the 'TO-BE' section of an assessment document. The
    prompt provides comprehensive context, including the current document draft,
    findings, scoring data, and the authoritative methodological definition for the
    specified tower. It explicitly defines the review criteria, operational rules,
    and the required JSON output schema to ensure a structured and consistent
    response from the model.

    Args:
        draft_pretty: A formatted string representing the current state of the entire
            assessment document.
        findings_pretty: A formatted string containing the 'findings' section of the
            assessment.
        scoring_pretty: A formatted string detailing the scoring data and observed
            gaps.
        case_input_pretty: A formatted string of the initial input data for the
            assessment case.
        tower_definition_pretty: A formatted string of the methodological
            definition for the tower, which serves as the ground truth for the
            review.
        tower_label: The string identifier for the specific assessment tower to be
            reviewed.

    Returns:
        A complete, formatted string containing the prompt to be sent to the LLM
        agent.
    """
    return f"""
Actua como el agente Reviewer del Assessment Engine.

Tu trabajo es revisar SOLO la seccion TO-BE de la torre {tower_label}.

Debes revisar:
1. Consistencia con los hallazgos.
2. Consistencia con el scoring y el gap observado.
3. Coherencia con la regla metodologica de TO-BE.
4. Credibilidad del estado objetivo propuesto.
5. Calidad profesional del texto.
6. Ausencia de roadmap, quick wins o plan de evolucion en esta seccion.
7. Coherencia entre capacidades objetivo y pilares.

Reglas:
- No reescribas el documento completo.
- Devuelve SOLO JSON valido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- Si detectas defectos, marca "status": "revise".
- Si el texto es suficientemente bueno, marca "status": "approve".
- Solo usa "human_validation_required" si falta informacion imprescindible para sostener el estado objetivo propuesto.
- INPUT_TOWER_DEFINITION es la fuente de verdad metodologica.
- No apliques reglas externas.
- Las notes_for_reviewer no son bloqueantes por defecto.
- Si solo sirven para enriquecer el documento, muévelas a review_notes y devuelve "approve".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "tobe",
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

INPUT_CASE_INPUT:
{case_input_pretty}

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()
