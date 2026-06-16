"""
Repositorio de prompts genéricos para secciones configurables (AS-IS, Riesgos).
"""


def get_section_writer_prompt(
    section_cfg: dict,
    findings_pretty: str,
    scoring_pretty: str,
    document_profile: dict,
    corrective_feedback: list[str] | None = None,
) -> str:
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

    # Forzar la estructura del JSON para evitar alucinaciones en Vertex AI
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
