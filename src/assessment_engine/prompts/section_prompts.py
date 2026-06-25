"""Defines generic prompt templates for configurable assessment sections, such as 'AS-IS' and 'Risks'."""


def get_section_writer_prompt(
    section_cfg: dict,
    findings_pretty: str,
    scoring_pretty: str,
    document_profile: dict,
    corrective_feedback: list[str] | None = None,
) -> str:
    r"""{'docstring': "Constructs a structured prompt to guide a large language model in writing a document section.\n\n    This function assembles multiple data sources—section configuration, assessment\n    findings, scoring data, document-wide rules, and optional corrective\n    feedback—into a single prompt string. For sections with an 'id' of 'asis' or\n    'risks', the function injects a mandatory JSON schema into the prompt to enforce\n    a predictable, machine-parseable output structure from the model.\n\n    Args:\n        section_cfg: A dictionary containing the configuration for the target\n            section. Must include 'writer_rules' and 'writer_description' keys.\n        findings_pretty: A pre-formatted string of assessment findings to be used\n            as input for the model.\n        scoring_pretty: A pre-formatted string of assessment scores to be used as\n            input for the model.\n        document_profile: A dictionary defining document-wide rules. The function\n            specifically utilizes the 'forbidden_phrases_by_section' key.\n        corrective_feedback: An optional list of feedback strings to guide the\n            revision of the section content.\n\n    Returns:\n        The complete prompt string to be sent to a language model.\n\n    Raises:\n        KeyError: If 'writer_rules' or 'writer_description' are absent from the\n            `section_cfg` dictionary."}."""
    rules = list(section_cfg["writer_rules"])
    forbidden_phrases_by_section = document_profile.get(
        "forbidden_phrases_by_section", {}
    )
    forbidden_phrases = forbidden_phrases_by_section.get(section_cfg.get("id"), [])

    if forbidden_phrases:
        rules.append(
            "No incluyas ninguna de estas expresiones o contenidos fuera de sección: "
            + ", ".join(forbidden_phrases)
            + "."
        )

    rules_text = "\n".join(f"- {rule}" for rule in rules)

    feedback_block = ""
    if corrective_feedback:
        feedback_text = "\n".join(f"- {item}" for item in corrective_feedback)
        feedback_block = f"""\nCorrecciones obligatorias para esta nueva iteracion:\n{feedback_text}\nDebes corregir completamente esos defectos y volver a generar la seccion.\n"""

    # Constrains model output to a strict JSON schema to mitigate response variability and ensure reliable downstream parsing on platforms such as Vertex AI.
    json_structure = ""
    if section_cfg.get("id") == "asis":
        json_structure = """
        Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
        {{
          "section_id": "asis",
          "status": "draft",
          "tower_id": "T2",
          "tower_name": "...",
          "section_title": "AS-IS",
          "executive_narrative": "...",
          "pillars": [
            {{
              "pillar": "...",
              "score": 3.5,
              "maturity_level": "Nivel 3 - Gestionado",
              "findings_summary": ["Hallazgo 1", "Hallazgo 2"],
              "operational_impact": "..."
            }}
          ],
          "cross_cutting_themes": ["Tema 1"],
          "notes_for_reviewer": ["..."]
        }}        """
    elif section_cfg.get("id") == "risks":
        json_structure = """
        Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
        {{
          "section_id": "risks",
          "status": "draft",
          "tower_id": "T2",
          "tower_name": "...",
          "section_title": "Risks",
          "introduction": "...",
          "risk_items": [
            {{
              "risk_name": "...",
              "severity": "High",
              "business_impact": "...",
              "technical_root_cause": "...",
              "related_pillars": ["Pilar 1"]
            }}
          ],
          "notes_for_reviewer": ["..."]
        }}        """

    return f"""
Actua como el agente Writer del Assessment Engine.

Tu trabajo es {section_cfg["writer_description"]}

Reglas:
{rules_text}
{feedback_block}

{json_structure}

INPUT_FINDINGS:
{findings_pretty}

INPUT_SCORING:
{scoring_pretty}
""".strip()


def get_section_reviewer_prompt(
    section_cfg: dict,
    draft_pretty: str,
    findings_pretty: str,
    scoring_pretty: str,
    tower_definition_pretty: str,
) -> str:
    r"""{'docstring': 'Construct a prompt for the section reviewer agent.\n\n    Assembles a multi-part Spanish-language prompt for a large language model.\n    This function populates a predefined template with section-specific\n    configuration, a document draft, findings, scoring data, and a\n    ground-truth "tower" definition. The prompt instructs the model on its\n    role, review criteria, and required JSON output format.\n\n    Args:\n        section_cfg: Configuration dictionary for the section. Must contain the\n            keys \'review_description\' (a string describing the agent\'s task)\n            and \'review_checks\' (a list of strings detailing specific review\n            points).\n        draft_pretty: A pre-formatted string containing the draft content to be\n            reviewed.\n        findings_pretty: A pre-formatted string containing findings relevant to\n            the section.\n        scoring_pretty: A pre-formatted string containing scoring information.\n        tower_definition_pretty: A pre-formatted string containing the\n            ground-truth "tower" definition, including methodological\n            criteria and scoring rules.\n\n    Returns:\n        A complete prompt string, ready for use with a language model.\n\n    Raises:\n        KeyError: If \'review_description\' or \'review_checks\' are not present\n            in `section_cfg`.'}."""
    checks_text = "\n".join(
        f"{i + 1}. {item}" for i, item in enumerate(section_cfg["review_checks"])
    )

    return f"""
Actua como el agente Reviewer del Assessment Engine.

Tu trabajo es {section_cfg["review_description"]}

Debes revisar:
{checks_text}

Reglas:
- No reescribas el documento completo.
- Devuelve SOLO JSON válido acorde al esquema solicitado.
- No uses markdown.
- No expliques tu proceso.
- Si detectas defectos, marca "status": "revise".
- Si el texto es suficientemente bueno, marca "status": "approve".
- Solo usa "human_validation_required" si falta información imprescindible para validar un elemento nuclear del borrador.
- INPUT_TOWER_DEFINITION es la fuente de verdad para bandas de madurez, reglas de score y criterios metodológicos.
- No apliques reglas metodológicas externas.
- Las notes_for_reviewer no son bloqueantes por defecto.
- Si solo sirven para enriquecer el documento, mueve ese contenido a review_notes y devuelve "approve".

Devuelve ÚNICAMENTE un JSON válido con esta estructura exacta:
{{
  "section_id": "asis_o_risks",
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

INPUT_TOWER_DEFINITION:
{tower_definition_pretty}
""".strip()
