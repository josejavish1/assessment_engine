"""Defines generic prompt templates for dynamically generating standardized report sections, such as 'AS-IS' and 'Risks'."""


def get_section_writer_prompt(
    section_cfg: dict,
    findings_pretty: str,
    scoring_pretty: str,
    document_profile: dict,
    corrective_feedback: list[str] | None = None,
) -> str:
    """Constructs a prompt for the 'Writer' AI agent to generate a document section.

    This function assembles a multi-component prompt by integrating section-
    specific rules, document-level forbidden phrases, optional corrective
    feedback, and primary input data (findings and scoring). For specific
    section IDs, such as 'asis' and 'risks', it injects a predefined JSON schema
    into the prompt to enforce a structured, machine-parsable output from the
    language model.

    Args:
        section_cfg: A dictionary containing the configuration for the target
            document section. Must contain 'writer_rules' (an iterable) and
            'writer_description' (a string). The 'id' key is used to look up
            forbidden phrases and determine if a JSON schema is required.
        findings_pretty: A pre-formatted string representing analytical findings
            to be included as input in the prompt.
        scoring_pretty: A pre-formatted string representing scoring data to be
            included as input in the prompt.
        document_profile: A dictionary representing the profile of the overall
            document, used to retrieve constraints such as section-specific
            forbidden phrases.
        corrective_feedback: An optional list of strings containing feedback
            from a previous generation attempt to guide regeneration. Defaults
            to None.

    Returns:
        A complete, formatted prompt string ready for submission to the
        Writer AI agent.

    Raises:
        KeyError: If 'writer_rules' or 'writer_description' keys are missing
            from the `section_cfg` dictionary.
        TypeError: If the 'writer_rules' value in `section_cfg` or the
            `corrective_feedback` argument (if provided) is not an iterable.
    """
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

    # Enforces a strict JSON output format to guarantee schema compliance from the Vertex AI model, preventing downstream parsing failures or data corruption.
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
    r"""[{'docstring': "Assembles a formatted prompt in Spanish for an AI section reviewer agent.\n\nThis function builds a detailed prompt that instructs a language model on\nhow to review a specific document section. The prompt specifies the agent's\nrole, a list of checks to perform, strict JSON output formatting rules,\nand provides the full context including the draft text, related findings,\nscoring data, and the authoritative tower definition.\n\nArgs:\n    section_cfg: A dictionary containing the configuration for the section\n        review. Expected to contain the keys 'review_description' (str)\n        and 'review_checks' (iterable of strings).\n    draft_pretty: A pre-formatted string representing the current draft\n        of the section.\n    findings_pretty: A pre-formatted string of findings relevant to the\n        section.\n    scoring_pretty: A pre-formatted string containing scoring information.\n    tower_definition_pretty: A pre-formatted string of the tower definition,\n        which serves as the source of truth for the review criteria.\n\nReturns:\n    A complete prompt string in Spanish, ready for submission to the AI\n    reviewer.\n\nRaises:\n    KeyError: If 'review_description' or 'review_checks' are not present\n        in `section_cfg`.\n    TypeError: If the value of `section_cfg['review_checks']` is not an\n        iterable."}]."""
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
