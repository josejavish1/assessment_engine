import csv
import html
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor, Cm

from assessment_engine.infrastructure.docx_render_utils import (
    autofit_table_to_contents,
    finalize_table,
    set_cell_text,
)
from assessment_engine.infrastructure.text_utils import clean_text_for_word, format_date_spanish

# Define constants for branding and document styling.
COLOR_BLUE = "0072BC"
COLOR_HEADER_BG = "D9EAF7"
COLOR_ROW_ALT = "F2F2F2"


def format_currency_custom(value: float, thousands_sep: str, decimal_sep: str) -> str:
    """Formats a float into a string with custom thousands and decimal separators.

    The input value is first formatted to a string with exactly two decimal
    places. The integer part is then grouped by thousands using the provided
    separator, and the standard decimal point is replaced with the custom
    decimal separator.

    Args:
        value: The numeric value to format.
        thousands_sep: The character to use as the thousands separator.
        decimal_sep: The character to use as the decimal separator.

    Returns:
        The formatted numeric string.
    """
    parts = f"{value:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]
    reversed_integer = integer_part[::-1]
    grouped = [reversed_integer[i : i + 3] for i in range(0, len(reversed_integer), 3)]
    formatted_integer = thousands_sep.join(grouped)[::-1]
    return f"{formatted_integer}{decimal_sep}{decimal_part}"


def clean_client_name(client_name: str) -> str:
    """Cleans a raw client name (which might be a slug or directory name) for reporting.

    Removes version tags (e.g. _v3, _v2, -v4), replaces underscores/hyphens with spaces,
    strips trailing whitespace, and ensures Proper Noun Title Case capitalization.
    """
    if not client_name:
        return "Cliente"
    import re
    # Remove version endings like _v3, _V2, -v4, etc.
    cleaned = re.sub(r'[_-][vV]\d+\b', '', client_name)
    # Replace underscores/hyphens with spaces
    cleaned = cleaned.replace('_', ' ').replace('-', ' ')
    cleaned = cleaned.strip()
    
    # Elite Capitalization: Ensure it is a Proper Noun (Title Case)
    # If the cleaned string is all lowercase, convert it to Title Case (e.g., 'cliente' -> 'Cliente')
    # If it has uppercase, preserve the client's custom branding (e.g., 'CLIENTE' stays 'CLIENTE')
    if cleaned.islower():
        return cleaned.title()
    return cleaned


# Use an internationalization (i18n) dictionary to support multiple locales.
LANG_VOCAB = {
    "es": {
        "title": "Informe de Situación Actual (AS-IS)",
        "project": "Consultoría para el rediseño de infraestructura tecnológica",
        "client_lbl": "Cliente:\n",
        "proj_lbl": "\nProyecto:\n",
        "toc_title": "Contenido",
        "dashboard_title": "Cuadro de Mando de Madurez Global de la Torre",
        "dashboard_intro": "La evaluación integral del estado actual consolida una valoración cuantitativa que sitúa a la torre en su banda de madurez correspondiente, justificando el grado de adopción de prácticas de resiliencia:",
        "score_lbl": "PUNTUACIÓN AS-IS",
        "maturity_lbl": "NIVEL DE MADUREZ CUALITATIVO",
        "resilience_reading": "Lectura de Resiliencia de la Plataforma:",
        "radar_title": "Análisis Comparativo de Madurez por Pilar",
        "justification_table_headers": [
            "Pilar / Capacidad Tecnológica Evaluada",
            "Score AS-IS",
            "Análisis de Brechas y Calibración del Diagnóstico",
        ],
        "platform_overview_title": "Descripción de la Plataforma de Infraestructura Actual",
        "swot_title": "Fortalezas y Brechas Clave",
        "swot_headers": [
            "Fortalezas Clave de la Plataforma",
            "Brechas y Deudas Operativas Críticas",
        ],
        "transversal_title": "Análisis Transversal de Capacidades",
        "risk_matrix_title": "Exposición Financiera al Riesgo y Resiliencia Operativa",
        "risk_intro_1": "El análisis cuantitativo del estado actual establece que las deudas técnicas operativas y las vulnerabilidades detectadas exclusivamente dentro del perímetro de esta torre tecnológica exponen ",
        "risk_intro_2": " a una Expectativa de Pérdida Anualizada (ALE) real de ",
        "risk_intro_3": " anuales bajo el estándar internacional FAIR.",
        "risk_mosaic_intro": "Esta matriz de mosaico consolida la distribución de esta exposición a partir de la frecuencia de amenazas (TEF) y magnitud de pérdidas (LM) de cada hallazgo forense:",
        "exposure_summary_title": "Matriz de Riesgos Cuantitativa",
        "methodology_chapter_title": "Objetivo, Alcance y Marco Metodológico",
        "tef_title": "Criterios de Frecuencia de la Amenaza (TEF)",
        "tef_headers": ["Nivel TEF", "Denominación", "Frecuencia Anualizada Estimada"],
        "lm_title": "Criterios de Magnitud de Pérdida Directa/Indirecta (LM)",
        "lm_headers": [
            "Nivel LM",
            "Clasificación de Impacto",
            "Límite de Pérdida Financiera",
        ],
        "top_risks_title": "Top de Riesgos Prioritarios de la Torre",
        "top_risks_intro": "Top de riesgos priorizados por su impacto directo en la resiliencia del servicio y el coste de inacción (ALE):",
        "motivo_priorizacion": "Motivo de priorización: ",
        "top_risks_fallbacks": {
            "compute": "El modelo reactivo en el cómputo on-premise arriesga directamente la continuidad del servicio y bloquea el despliegue del Gemelo Digital y la IA estratégica.",
            "container": "La falta de plataforma corporativa de contenedores estanca la innovación, genera silos aislados en desarrollo y multiplica la deuda de modernización.",
            "cloud": "La remediación manual de las Landing Zones impide verificar el cumplimiento normativo en tiempo real, exponiendo al negocio a severas sanciones regulatorias.",
            "automation": "La dependencia de tickets y validaciones manuales retarda semanas el time-to-market y genera cuellos de botella severos en la provisión.",
            "default": "La fragmentación e inconsistencia en las monitorizaciones imposibilita correlar alertas y predecir fallas complejas que detienen las operaciones.",
        },
        "detailed_risks_title": "Inventario Analítico de Riesgos y Exposiciones",
        "detailed_risks_pilar_title": "Análisis de Vulnerabilidades: ",
        "detailed_risks_headers": [
            "ID",
            "Vulnerabilidad y Evidencias de Auditoría",
            "Exposición y Riesgo de Negocio",
        ],
        "next_steps_title": "Siguientes Pasos y Coste de Inacción",
        "appendix_a_title": "Lista de Abreviaturas",
        "appendix_a_intro": "A continuación, se define el glosario de términos técnicos y acrónimos utilizados en este diagnóstico técnico actual:",
        "appendix_a_headers": ["Abreviatura", "Significado / Descripción Técnica"],
        "appendix_b_title": "Cláusula de Limitación de Responsabilidad",
        "appendix_c_title": "Registro de Custodia de Fuentes de Información",
        "appendix_c_intro": "Para garantizar la transparencia, veracidad e inmutabilidad de la información recopilada en este diagnóstico técnico, a continuación, se listan y codifican las fuentes documentales utilizadas bajo custodia de auditoría:",
        "appendix_c_headers": [
            "Código de Referencia",
            "Documento Fuente / Origen de Datos",
            "Descripción y Ámbito de Custodia",
        ],
        "vulnerability_lbl": "Vulnerabilidad Identificada:\n",
        "evidence_lbl": "Evidencia Forense Literal:\n",
        "impact_lbl": "Impacto Operativo:\n",
        "exposure_lbl": "Exposición Cuantitativa (FAIR):\n",
        "ale_proyectado": "ALE Proyectado: ",
        "v_lbl": "Versión ",
        "disclaimer_text_1": "Este informe de diagnóstico técnico (el Documento) constituye un ejercicio de evaluación rápida (Fast Assessment) preparado por la consultora únicamente para el uso interno y exclusivo de la organización cliente, sobre una base estrictamente confidencial. El lector y la organización cliente aceptan y declaran conocer que el Documento se fundamenta de manera única y exclusiva en las declaraciones verbales, narrativas, explicaciones de arquitectura y autoevaluaciones facilitadas por el personal del cliente durante las entrevistas técnicas y reuniones de contexto mantenidas, sin que se haya procedido a realizar ninguna auditoría de campo, revisión directo de código, análisis de configuraciones en sistemas, captura de tráfico de red, ni contraste o validación independiente de evidencias físicas o documentales por parte de la consultora. En consecuencia, la consultora no asume obligación, deber ni responsabilidad alguna de verificar, validar o contrastar la veracidad, exactitud, completitud o vigencia de la información facilitada por el cliente, estando completamente exenta de cualquier responsabilidad o culpa profesional contractual o extracontractual en caso de que los datos o narrativas proporcionados por los equipos del cliente resulten ser incompletos, inexactos, desactualizados o erróneos. El Documento no constituye, bajo ningún concepto, una garantía de rendimiento, ciberresiliencia, seguridad continua o indemnidad frente a incidentes operacionales o regulatorios.",
        "disclaimer_text_2": "Las proyecciones de impacto financiero, simulación actuarial de riesgos, y los valores de Expectativa de Pérdida Anualizada (ALE) y peor caso (CVaR) calculados mediante la metodología estándar de Open FAIR™ y modelos estocásticos de Monte Carlo, representan únicamente estimaciones estadísticas y modelos matemáticos de probabilidad basados en distribuciones de incertidumbre. Dichas valoraciones monetarias constituyen herramientas analíticas exclusivas de priorización estratégica de inversiones y coste de inacción (Business Case). Bajo ninguna circunstancia deben interpretarse, utilizarse ni asimilarse a auditorías financieras o contables formales, provisiones de pasivos contables, garantías de impacto directo o indirecto en el balance de la compañía, ni como compromisos de pasivos exigibles legalmente o judicialmente.",
        "disclaimer_text_3": "Cualquier referencia contenida en el Documento a normativas, leyes, regulaciones o esquemas de cumplimiento sectorial se expone con un propósito estrictamente ilustrativo, técnico y de buenas prácticas de ingeniería para mitigar la superficie de exposición al riesgo. Dichas menciones no constituyen, bajo ningún concepto, asesoramiento legal, jurídico, fiscal o regulatorio formal. La interpretación, implantación, verificación y cumplimiento final de las obligaciones normativas y requerimientos legales aplicables recaen de manera estricta, directa e intransferible en los administradores, asesores legales, oficiales de cumplimiento y directivos de la organización cliente.",
        "disclaimer_text_4": "Queda expresamente prohibido distribuir, divulgar, reproducir, citar o facilitar el acceso a este Documento, de forma total o parcial, a cualquier tercero ajeno a la organización cliente sin el consentimiento previo y por escrito de la consultora. La consultora no asume, acepta ni adquiere responsabilidad alguna, contractual o extracontractual, frente a ningún tercero que acceda, lea o tome decisiones de cualquier naturaleza basadas en el contenido de este Documento, asumiendo dicho tercero todo el riesgo de forma exclusiva. El cliente se compromete a mantener indemne a la consultora, sus socios, empleados y subcontratistas frente a cualquier reclamación, demanda, daño, coste o perjuicio derivado de la distribución, uso inapropiado o divulgación no autorizada de este Documento a terceros.",
        "disclaimer_text_5": "En ningún caso la consultora será responsable por daños indirectos, incidentales, consecuenciales, lucro cesante, pérdida de ingresos, interrupción de negocio o daños reputacionales.",
        "bib_cues": "Cuestionarios consolidados de autoevaluación técnica de la torre de ",
        "bib_cues_desc": ", recopilando las respuestas oficiales del equipo de ingeniería de ",
        "bib_contexto": "Dossier estratégico de contexto de arquitectura de ",
        "bib_contexto_desc": " que define la volumetría del patrimonio, centros de datos y criticidad operativa.",
        "bib_minutas": "Minutas y registros tomados durante las sesiones presenciales de contexto de arquitectura mantenidas entre los líderes técnicos de ",
        "bib_minutas_desc": " y el equipo consultor.",
        "default_overview_text": "El inventario consolidado y la evaluación de la plataforma de ",
    },
    "en": {
        "title": "Current State Assessment Report (AS-IS)",
        "project": "Technology infrastructure redesign consultancy",
        "client_lbl": "Client:\n",
        "proj_lbl": "\nProject:\n",
        "toc_title": "Contents",
        "dashboard_title": "Global Tower Maturity Dashboard",
        "dashboard_intro": "The comprehensive current state assessment consolidates a quantitative valuation that positions the tower in its corresponding maturity band, justifying the adoption of resilience practices:",
        "score_lbl": "AS-IS SCORE",
        "maturity_lbl": "QUALITATIVE MATURITY LEVEL",
        "resilience_reading": "Platform Resilience Reading:",
        "radar_title": "Weighted Maturity Visual Profile",
        "justification_table_headers": [
            "Pilar / Evaluated Technology Capability",
            "AS-IS Score",
            "Gap Analysis and Diagnostic Calibration",
        ],
        "platform_overview_title": "Current Infrastructure Platform Description",
        "swot_title": "Key Strengths and Gaps",
        "swot_headers": [
            "Key Platform Strengths",
            "Critical Gaps and Operational Debts",
        ],
        "transversal_title": "Cross-Cutting Capabilities Analysis",
        "risk_matrix_title": "Financial Risk Exposure and Operational Resilience",
        "risk_intro_1": "The quantitative current state analysis establishes that the technical operational debts and identified vulnerabilities exclusively within the perimeter of this technological tower expose ",
        "risk_intro_2": " to a real Annual Loss Exposure (ALE) of ",
        "risk_intro_3": " annually under the international FAIR standard.",
        "risk_mosaic_intro": "This mosaic matrix consolidates the distribution of this exposure based on the Threat Event Frequency (TEF) and Loss Magnitude (LM) of each forensic finding:",
        "exposure_summary_title": "Quantitative Risk Matrix",
        "methodology_chapter_title": "Assessment Objectives, Scope, and Reference Framework",
        "tef_title": "Threat Event Frequency Criteria (TEF)",
        "tef_headers": ["TEF Level", "Denomination", "Estimated Annualized Frequency"],
        "lm_title": "Direct/Indirect Loss Magnitude Criteria (LM)",
        "lm_headers": ["LM Level", "Impact Classification", "Financial Loss Limit"],
        "top_risks_title": "Top Prioritized Risks for the Tower",
        "top_risks_intro": "Top risks prioritized by their direct impact on service resilience and the cost of inaction (ALE):",
        "motivo_priorizacion": "Prioritization rationale: ",
        "top_risks_fallbacks": {
            "compute": "The reactive model in on-premise compute directly risks service continuity and blocks the deployment of the Digital Twin and strategic AI.",
            "container": "The lack of an enterprise container platform stalls innovation, creates isolated development silos, and multiplies modernization debt.",
            "cloud": "The manual remediation of Landing Zones prevents verifying compliance in real-time, exposing the business to severe regulatory penalties.",
            "automation": "Dependence on manual tickets and approvals delays time-to-market by weeks and generates severe provisioning bottlenecks.",
            "default": "Fragmentation and inconsistency in monitoring systems make it impossible to correlate alerts and predict complex outages.",
        },
        "detailed_risks_title": "Analytical Inventory of Risks and Exposures",
        "detailed_risks_pilar_title": "Vulnerability Analysis: ",
        "detailed_risks_headers": [
            "ID",
            "Vulnerability and Audit Evidence",
            "FAIR Exposure and Business Risk",
        ],
        "next_steps_title": "Next Steps and Cost of Inaction",
        "appendix_a_title": "List of Abbreviations",
        "appendix_a_intro": "The following defines the glossary of technical terms and acronyms used in this current technical diagnosis:",
        "appendix_a_headers": ["Abbreviation", "Significado / Technical Description"],
        "appendix_b_title": "Limitation of Liability Disclaimer",
        "appendix_c_title": "Registry of Custody of Information Sources",
        "appendix_c_intro": "To ensure the transparency, veracity, and immutability of the information collected in this technical diagnosis, the document sources used under audit custody are listed and coded below:",
        "appendix_c_headers": [
            "Reference Code",
            "Source Document / Data Origin",
            "Custody Scope and Description",
        ],
        "vulnerability_lbl": "Identified Vulnerability:\n",
        "evidence_lbl": "Literal Forensic Evidence:\n",
        "impact_lbl": "Operational Impact:\n",
        "exposure_lbl": "Quantitative Exposure (FAIR):\n",
        "ale_proyectado": "Projected ALE: ",
        "v_lbl": "Version ",
        "disclaimer_text_1": "This technical diagnosis report (the Document) represents a retrospective evaluation of the current state (AS-IS) of the evaluated tower based exclusively on the information, telemetries, and self-assessment responses provided by the client in good faith. The recommendations, qualitative assessments, and infrastructure inventories presented reflect a current diagnosis and do not constitute guarantees of performance, continuous security, or service availability commitments by the consultant.",
        "disclaimer_text_2": "The quantitative financial risk projections and the Annual Loss Exposure (ALE) calculated through the O-FAIR methodology and Monte Carlo simulations are statistical probability estimates based on standard uncertainty models for the critical infrastructure sector. These figures are provided solely for prioritization and illustrative purposes of cost of inaction, and should not be interpreted in any case as formal balance sheet accounting audits, asset guarantees, or legally enforceable liabilities.",
        "disclaimer_text_3": "References to legal and compliance regulations are framed as guidelines and best engineering practices to mitigate the attack surface, and do not constitute formal legal advice. The final interpretation and implementation of compliance requirements remain strictly and non-transferably with the compliance, security, and governance officers of the client organization.",
        "disclaimer_text_4": "Any distribution, disclosure, reproduction, quotation, or access to this Document, in whole or in part, to any third party outside the client organization is strictly prohibited without the prior written consent of the consultant. The consultant does not assume, accept, or acquire any liability, contractual or extra-contractual, towards any third party accessing, reading, or making decisions of any nature based on the content of this Document, with such third party assuming all risk exclusively. The client agrees to hold harmless and indemnify the consultant, its partners, employees, and subcontractors against any claim, demand, damage, cost, or loss arising from the distribution, inappropriate use, or unauthorized disclosure of this Document to third parties.",
        "disclaimer_text_5": "In no event shall the consultant be liable for any indirect, incidental, consequential, special, or punitive damages, including but not limited to loss of profits, loss of revenue, business interruption, or reputational damage.",
        "bib_cues": "Consolidated technical self-assessment questionnaires of the ",
        "bib_cues_desc": " tower, gathering official responses from the engineering team of ",
        "bib_contexto": "Strategic architecture context dossier of ",
        "bib_contexto_desc": " defining inventory volumes, data centers, and operational criticality.",
        "bib_minutas": "Minutes and records taken during the on-site architecture sessions between the technical leaders of ",
        "bib_minutas_desc": " and the consulting team.",
        "default_overview_text": "The consolidated inventory and evaluation of the ",
    },
}


def shade_cell(cell, color_hex):
    """Applies a background color shading to a table cell.

    This function directly manipulates the underlying Open Office XML (OOXML)
    of the cell's properties to set its background fill color.

    Args:
        cell (docx.table._Cell): The table cell object to modify.
        color_hex (str): A six-character RRGGBB hexadecimal string representing
            the background color (e.g., 'FFC000').
    """
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tcPr.append(shd)


def set_cell_border_white(cell):
    r"""{'docstring': 'Set a 2.0 pt white border on a table cell.\n\nDirectly manipulates the underlying Office Open XML (OOXML) representation\nof a table cell to apply a single, white, 2.0 pt border to all four sides.\nThis effect is typically used to create visual separation between cells in\na heatmap-style table, giving them a tiled appearance.\n\nArgs:\n    cell (docx.table.Cell): The target table cell object whose borders will\n        be modified in-place.\n\nRaises:\n    AttributeError: If the provided `cell` object does not conform to the\n        expected internal OOXML structure.'}."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")

    for border_name in ["top", "left", "bottom", "right"]:
        border = OxmlElement(f"w:{border_name}")
        border.set(qn("w:val"), "single")
        border.set(
            qn("w:sz"), "16"
        )  # The OpenXML value of 16 corresponds to a 2.0 pt border thickness (16 / 8 = 2.0 pt).
        border.set(qn("w:space"), "0")
        border.set(qn("w:color"), "FFFFFF")  #
        tcBorders.append(border)

    tcPr.append(tcBorders)


def set_cell_text_custom(
    cell, text, bold=False, font_size=9, align=WD_ALIGN_PARAGRAPH.LEFT, color_rgb=None, no_bullets=False
):
    r"""Populates a `docx` table cell with richly formatted, multi-line text.

    This function processes an input string by clearing the target cell and then
    inserting the string as a series of formatted paragraphs. It applies several
    formatting rules:

    - Sanitization: Removes markdown emphasis characters (`*`, `_`, `**`, `__`).
    - Paragraphs: Each line in the input string (separated by `\n` or `\n`)
      becomes a separate paragraph in the cell.
    - Bullet Points: Lines are prefixed with bullet points (`•` for top-level,
      `-` for indented sub-points).
    - Hierarchy: Indentation is applied to lines that start with leading
      whitespace or a hyphen.
    - Label Highlighting: Lines containing a colon (e.g., "Gaps: ...") are split,
      with the text before the colon rendered in bold.
    - Citation Formatting: Source citations matching the pattern `[Ref: ...]` are
      extracted and appended with a distinct style (smaller, italic, gray font).

    For single-line input without newlines, processing is delegated to the
    `set_cell_text` helper function.

    Args:
        cell (docx.table._Cell): The `python-docx` table cell object to modify.
            Any existing content in the cell will be cleared.
        text (str): The content to insert into the cell. Newline characters are
            interpreted as paragraph breaks.
        bold (bool): If True, applies bold formatting to entire lines that do not
            contain a formatting label (i.e., a colon). Defaults to False.
        font_size (int): The font size in points (Pt). Defaults to 9.
        align (WD_ALIGN_PARAGRAPH): An alignment constant from the
            `docx.enum.text.WD_ALIGN_PARAGRAPH` enumeration. Defaults to
            `WD_ALIGN_PARAGRAPH.LEFT`.
        color_rgb (docx.shared.RGBColor or None): An `RGBColor` object for the
            primary text color. If None, the style's default color is used.
            Defaults to None.
        no_bullets (bool): If True, skips prepending any bullets to lines. Defaults to False.

    Returns:
        None. The `cell` object is modified in-place.
    """
    # Sanitization: Replace non-standard Spanish 'sistémico/sistémica' with 'estructural/estructurales'
    if isinstance(text, str):
        # Plural forms (longer) must be replaced BEFORE singular forms (shorter) to prevent substring corruptions like "estructurals"
        text = text.replace("sistémicas", "estructurales")
        text = text.replace("sistémicos", "estructurales")
        text = text.replace("Sistémicas", "Estructurales")
        text = text.replace("Sistémicos", "Estructurales")
        text = text.replace("sistémica", "estructural")
        text = text.replace("sistémico", "estructural")
        text = text.replace("Sistémica", "Estructural")
        text = text.replace("Sistémico", "Estructural")

        # Centralized spelling sanitization for LLM output typos on 'múltiples'
        text = text.replace("mùltiples", "múltiples")
        text = text.replace("Mùltiples", "Múltiples")
        text = text.replace("móltiples", "múltiples")
        text = text.replace("Móltiples", "Múltiples")
        text = text.replace("multiples", "múltiples")
        text = text.replace("Multiples", "Múltiples")

    # Sanitization: Remove markdown emphasis characters from body text.
    clean_txt = (
        str(text).replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    )

    # Handle multi-line input by splitting the text into separate paragraphs at each newline character.
    if "\n" in clean_txt or "\\n" in clean_txt:
        # Remove the default empty paragraph that `python-docx` adds on cell creation to avoid unwanted vertical space.
        for p in list(cell.paragraphs):
            cell._tc.remove(p._element)

        raw_lines = clean_txt.replace("\\n", "\n").split("\n")
        for line in raw_lines:
            # Preserve leading whitespace for subsequent hierarchy detection; it will be stripped later.
            is_subpoint = line.startswith("   ") or line.strip().startswith("-")

            clean_line = line.strip()
            if not clean_line:
                continue

            p = cell.add_paragraph()
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.alignment = align

            # Clear any existing list formatting from the paragraph to ensure a consistent state before applying a new style.
            if clean_line.startswith("•") or clean_line.startswith("-"):
                clean_line = clean_line[1:].strip()

            if no_bullets:
                bullet_prefix = ""
            elif is_subpoint:
                # Define the style for an indented, secondary bullet point, per requirement 2.
                p.paragraph_format.left_indent = Inches(0.25)
                bullet_prefix = "- "
            else:
                #
                p.paragraph_format.left_indent = Inches(0.0)
                bullet_prefix = "• "

            # Implement detection and extraction of user-provided citations (e.g., '[Ref: ...]').
            ref_text = ""
            if "[Ref:" in clean_line:
                clean_line, ref_part = clean_line.split("[Ref:", 1)
                ref_text = "[Ref:" + ref_part

            # Detect and apply bold formatting to leading labels (e.g., 'Gaps:') to enhance scannability.
            if ":" in clean_line:
                label, desc = clean_line.split(":", 1)
                run_lbl = p.add_run(f"{bullet_prefix}{label.strip()}: ")
                run_lbl.bold = True
                run_lbl.font.name = "Arial"
                run_lbl.font.size = Pt(font_size)
                if color_rgb:
                    run_lbl.font.color.rgb = color_rgb

                run_desc = p.add_run(desc.strip())
                run_desc.font.name = "Arial"
                run_desc.font.size = Pt(font_size)
                if color_rgb:
                    run_desc.font.color.rgb = color_rgb
            else:
                run = p.add_run(f"{bullet_prefix}{clean_line.strip()}")
                run.bold = bold
                run.font.name = "Arial"
                run.font.size = Pt(font_size)
                if color_rgb:
                    run.font.color.rgb = color_rgb

            # Append the source reference to the paragraph with distinct formatting (italic, gray, smaller font size).
            if ref_text:
                run_ref = p.add_run(f" {ref_text.strip()}")
                run_ref.font.name = "Arial"
                run_ref.font.size = Pt(font_size - 1)  #
                run_ref.font.italic = True
                run_ref.font.color.rgb = RGBColor(120, 130, 140)  #
    else:
        #
        set_cell_text(cell, clean_txt, bold=bold, align=align, font_size=font_size)
        p = cell.paragraphs[0]
        for r in p.runs:
            if color_rgb:
                r.font.color.rgb = color_rgb


def add_body_paragraph(
    doc,
    text,
    bold=False,
    italic=False,
    space_after=6,
    text_color_rgb=(46, 64, 77),
    style="Normal",
) -> Any:
    r"""{'docstring': "Adds a sanitized and formatted paragraph to a `docx.Document` object.\n\n    The input text is first sanitized by removing markdown emphasis markers\n    (`*`, `_`, `**`, `__`). The function then adds the cleaned text as a new,\n    justified paragraph formatted with a consistent 'Arial' 10pt font.\n\n    For bulleted styles (e.g., 'List Bullet', 'Bullet'), any text preceding\n    the first colon is automatically rendered in bold to enhance readability;\n    this behavior overrides the `bold` parameter.\n\n    If a specified style name does not exist in the document's template, the\n    function falls back to the 'Normal' style. For a non-existent bulleted\n    style, it also manually prepends a '•' character to simulate a list item.\n\n    Args:\n        doc (docx.document.Document): The document instance to which the\n            paragraph will be added.\n        text (str): The raw string content for the paragraph. Markdown emphasis\n            characters will be removed.\n        bold (bool, optional): If True, applies bold formatting to the entire\n            paragraph. This parameter is ignored for bulleted styles containing\n            a colon. Defaults to False.\n        italic (bool, optional): If True, applies italic formatting to the\n            entire paragraph. Defaults to False.\n        space_after (int, optional): The spacing in points (Pt) to apply after\n            the paragraph. Defaults to 6.\n        text_color_rgb (tuple[int, int, int], optional): An RGB tuple specifying\n            the font color. Each value must be in the range 0-255. Defaults\n            to (46, 64, 77).\n        style (str, optional): The name of the paragraph style to apply from\n            the document template. Defaults to 'Normal'.\n\n    Returns:\n        docx.text.paragraph.Paragraph: The newly created paragraph object that was\n            added to the document.\n\n    Raises:\n        ValueError: If any value in the `text_color_rgb` tuple is outside the\n            valid 0-255 range."}."""
    # Sanitization: Replace non-standard Spanish 'sistémico/sistémica' with 'estructural/estructurales'
    if isinstance(text, str):
        # Plural forms (longer) must be replaced BEFORE singular forms (shorter) to prevent substring corruptions like "estructurals"
        text = text.replace("sistémicas", "estructurales")
        text = text.replace("sistémicos", "estructurales")
        text = text.replace("Sistémicas", "Estructurales")
        text = text.replace("Sistémicos", "Estructurales")
        text = text.replace("sistémica", "estructural")
        text = text.replace("sistémico", "estructural")
        text = text.replace("Sistémica", "Estructural")
        text = text.replace("Sistémico", "Estructural")

        # Centralized spelling sanitization for LLM output typos on 'múltiples'
        text = text.replace("mùltiples", "múltiples")
        text = text.replace("Mùltiples", "Múltiples")
        text = text.replace("móltiples", "múltiples")
        text = text.replace("Móltiples", "Múltiples")
        text = text.replace("multiples", "múltiples")
        text = text.replace("Multiples", "Múltiples")

    # Sanitization: Remove markdown emphasis characters from body text.
    # Keep underscores to prevent breaking uppercase identifiers like CRITICAL_INFRASTRUCTURE.
    clean_txt = (
        text.replace("**", "").replace("*", "")
    )

    is_bullet = style == "List Bullet" or style == "Bullet"
    target_style = "Bullet" if is_bullet else style

    try:
        p = doc.add_paragraph(style=target_style)
    except KeyError:
        p = doc.add_paragraph(style="Normal")
        if is_bullet:
            run_b = p.add_run("• ")
            run_b.font.name = "Arial"
            run_b.font.size = Pt(10)
            run_b.font.color.rgb = RGBColor(*text_color_rgb)

    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Programmatically bold the leading words of each bullet point to improve scannability.
    if is_bullet and ":" in clean_txt:
        parts = clean_txt.split(":", 1)
        run_bold = p.add_run(parts[0] + ":")
        run_bold.bold = True
        run_bold.font.name = "Arial"
        run_bold.font.size = Pt(10)
        run_bold.font.color.rgb = RGBColor(*text_color_rgb)

        run_rest = p.add_run(parts[1])
        run_rest.font.name = "Arial"
        run_rest.font.size = Pt(10)
        run_rest.font.color.rgb = RGBColor(*text_color_rgb)
    else:
        run = p.add_run(clean_txt)
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = RGBColor(*text_color_rgb)
    return p


def add_callout_box(doc, text, bg_color_hex="F2F2F2", border_color_hex=None, text_color_rgb=(46, 64, 77), italic=False, bold=False):
    """Adds a beautiful 1x1 table representing an executive callout box with optional left border."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    
    # Enforce width
    cell = tbl.rows[0].cells[0]
    cell.width = Inches(6.5)
    
    # Shade cell background
    shade_cell(cell, bg_color_hex)
    
    # Set text
    p = cell.paragraphs[0]
    p.paragraph_format.left_indent = Inches(0.15)
    p.paragraph_format.right_indent = Inches(0.15)
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # Sanitization
    clean_txt = str(text).replace("**", "").replace("*", "")
    
    # Check if text contains bold indicator
    is_bold = bold or ("**" in str(text))
    
    run = p.add_run(clean_txt)
    run.font.name = "Arial"
    run.font.size = Pt(9.5)
    run.font.bold = is_bold
    run.font.italic = italic or ("*" in str(text))
    run.font.color.rgb = RGBColor(*text_color_rgb)
    
    # Clear borders and add a custom left border if requested
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    
    for b_name in ['top', 'right', 'bottom']:
        b = OxmlElement(f'w:{b_name}')
        b.set(qn('w:val'), 'none')
        tcBorders.append(b)
        
    if border_color_hex:
        left_b = OxmlElement('w:left')
        left_b.set(qn('w:val'), 'single')
        left_b.set(qn('w:sz'), '36') # 4.5 pt width
        left_b.set(qn('w:space'), '0')
        left_b.set(qn('w:color'), border_color_hex)
        tcBorders.append(left_b)
    else:
        left_b = OxmlElement('w:left')
        left_b.set(qn('w:val'), 'none')
        tcBorders.append(left_b)
        
    tcPr.append(tcBorders)
    add_spacer(doc, 10)


def add_heading(doc, text, level, primary_color_rgb=(0, 114, 188)):
    r"""{'docstring': "Adds a sanitized and styled heading to a document.\n\n    Sanitizes the input text by removing markdown emphasis characters ('*', '_')\n    before adding it as a heading. The function applies specific paragraph\n    and font styles based on the heading level. Paragraph formatting includes\n    spacing adjustments and ensuring headings are not separated from subsequent\n    paragraphs. Level 1 headings are configured to start on a new page via the\n    'Page break before' style property, preventing the creation of extraneous\n    blank pages.\n\n    Args:\n        doc (docx.document.Document): The document object to which the heading\n            will be added.\n        text (str): The raw heading text from which markdown emphasis will be\n            removed.\n        level (int): The heading level, where 0 represents a title and 1-9\n            represent heading levels.\n        primary_color_rgb (Tuple[int, int, int]): An RGB tuple for the text\n            color. Defaults to (0, 114, 188).\n\n    Returns:\n        docx.text.paragraph.Paragraph: The newly created and styled heading\n            paragraph object.\n\n    Raises:\n        ValueError: If `level` is not an integer between 0 and 9, or if any\n            value in `primary_color_rgb` is outside the 0-255 range."}."""
    # Sanitization: Remove markdown emphasis characters from heading text.
    clean_txt = (
        text.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
    )

    h = doc.add_heading(clean_txt, level)
    h.paragraph_format.space_before = Pt(12)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.keep_with_next = True

    # Each chapter styled with 'Heading 1' is configured to begin on a new page.
    # Using the 'Page break before' style property prevents the creation of empty pages that can result from explicit `add_page_break()` calls.
    if level == 1:
        h.paragraph_format.page_break_before = True

    # Define color palettes and dimensional parameters for document elements.
    for run in h.runs:
        run.font.color.rgb = RGBColor(*primary_color_rgb)
        run.font.name = "Arial"
        if level == 1:
            run.font.size = Pt(16)
        elif level == 2:
            run.font.size = Pt(14)
        elif level == 3:
            run.font.size = Pt(12)
        else:
            run.font.size = Pt(11)
    return h


def add_spacer(doc, points=12):
    """Add a vertical spacer to a document via an empty paragraph."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(points)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.line_spacing = Pt(1)
    return p


def add_toc(doc):
    r"""Inserts an Office Open XML field code to generate a Table of Contents (TOC).

    This function directly manipulates the underlying OOXML structure of the
    document to add a complex field for a TOC. It constructs the necessary
    `w:fldChar` (field character) and `w:instrText` (instruction text)
    elements. The generated field code is `TOC \\o "1-2" \\h \\z \\u`, which
    instructs a word processing application to build a hyperlinked TOC using
    heading levels 1 through 2.

    The inserted TOC is a placeholder that must be updated by the end-user in a
    host application (e.g., by right-clicking the field and selecting 'Update
    Field' in Microsoft Word) to populate its content.

    Args:
        doc (docx.document.Document): The `python-docx` document object to which
            the TOC field will be added.

    Returns:
        None. The `doc` object is modified in-place.

    Raises:
        AttributeError: If `doc` is not a valid `docx.document.Document` object
            or lacks the required methods for manipulation.
    """
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(12)
    run = p.add_run()
    fldChar = OxmlElement("w:fldChar")
    fldChar.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = 'TOC \\o "1-2" \\h \\z \\u'
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")
    r_element = run._r
    r_element.append(fldChar)
    r_element.append(instrText)
    r_element.append(fldChar2)
    r_element.append(fldChar3)


def set_update_fields(doc):
    """Configures the document to automatically update fields upon opening.

    Injects a `w:updateFields` element with its `w:val` attribute set to "true"
    into the document's core settings XML part (`/word/settings.xml`). This
    instructs consuming applications, such as Microsoft Word, to regenerate all
    dynamic fields (e.g., Table of Contents, page number references) when the
    document is next opened.

    This function modifies the `doc` object in-place.

    Args:
        doc (docx.document.Document): The `python-docx` document object to be
            modified.

    Returns:
        None
    """
    settings = doc.settings.element
    update_fields = OxmlElement("w:updateFields")
    update_fields.set(qn("w:val"), "true")
    settings.append(update_fields)


def parse_and_append_markdown_section(
    doc,
    md_path: Path,
    p_color_rgb,
    text_color_rgb,
    start_header=None,
    end_header=None,
    skip_level_1=False,
):
    r"""{'docstring': "Parses a specified section of a Markdown file and appends it to a DOCX document.\n\nReads a Markdown file and converts its syntax into formatted DOCX elements.\nThe function handles headings (levels 1-4), bullet points (`*` or `-`), and\nblockquotes (`>`). HTML entities within the source file are unescaped.\n\nParsing can be constrained to a specific section by providing `start_header`\nand `end_header` substrings. These are matched case-insensitively against\nlevel 2 headings to start and stop the inclusion process. If the specified\nMarkdown file does not exist, the function returns silently. Certain\nhardcoded placeholder lines for tables are also ignored.\n\nArgs:\n    doc (docx.document.Document): The document object to which content will be\n        appended. This object is modified in-place.\n    md_path (pathlib.Path): The path to the source Markdown file.\n    p_color_rgb (tuple[int, int, int]): An RGB tuple for primary heading styles.\n    text_color_rgb (tuple[int, int, int]): An RGB tuple for body text styles.\n    start_header (Optional[str]): A case-insensitive substring that, when found\n        in a level 2 heading, starts content parsing. If None, parsing\n        begins from the file's start. Defaults to None.\n    end_header (Optional[str]): A case-insensitive substring that, when found\n        in a level 2 heading, terminates content parsing. Defaults to None.\n    skip_level_1 (bool): If True, level 1 headings are skipped and not added\n        to the document. Defaults to False.\n\nReturns:\n    None. The `doc` object is modified in-place.\n\nRaises:\n    IOError: If the file at `md_path` exists but cannot be opened or read."}."""
    if not md_path.exists():
        return

    with open(md_path, "r", encoding="utf-8") as f:
        lines = [html.unescape(line) for line in f.readlines()]

    recording = start_header is None
    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue

        if (
            start_header
            and cleaned.startswith("## ")
            and start_header.lower() in cleaned.lower()
        ):
            recording = True
            continue

        if (
            end_header
            and cleaned.startswith("## ")
            and end_header.lower() in cleaned.lower()
        ):
            recording = False
            break

        if not recording:
            continue

        # Skip processing for lines that are markers for table placeholders.
        if (
            "--- TABLA COMPARATIVA" in cleaned
            or "FORTALEZAS_CLAVE:" in cleaned
            or "BRECHAS_CLAVE:" in cleaned
            or "--- FIN TABLA" in cleaned
        ):
            continue

        # Assemble and render Section 1: Chapter Headings.
        if cleaned.startswith("# "):
            if skip_level_1:
                continue
            add_heading(doc, cleaned[2:], level=1, primary_color_rgb=p_color_rgb)
        elif cleaned.startswith("## "):
            add_heading(doc, cleaned[3:], level=2, primary_color_rgb=p_color_rgb)
        elif cleaned.startswith("### "):
            add_heading(doc, cleaned[4:], level=3, primary_color_rgb=p_color_rgb)
        elif cleaned.startswith("#### "):
            add_heading(doc, cleaned[5:], level=4, primary_color_rgb=p_color_rgb)
        elif cleaned.startswith("* ") or cleaned.startswith("- "):
            add_body_paragraph(
                doc, cleaned[2:], style="Bullet", text_color_rgb=text_color_rgb
            )
        elif cleaned.startswith("> "):
            text_val = cleaned[2:]
            # Detect key metrics and format it as a beautiful card with a thick blue left border
            if "Métricas de Diagnóstico Clave" in text_val:
                text_val = text_val.replace("Métricas de Diagnóstico Clave", "Resumen de Exposición y Madurez Operativa")
                add_callout_box(doc, text_val, bg_color_hex="F4F8FA", border_color_hex="0072BC", bold=True)
            else:
                add_callout_box(doc, text_val, bg_color_hex="F4F8FA", border_color_hex="0072BC", bold=False)
        elif "Bottom Line (Mensaje de Impacto):" in cleaned:
            # Render the high-impact strategic headline inside a soft gray 1x1 table (no borders)
            text_val = cleaned.replace("Bottom Line (Mensaje de Impacto):", "").strip()
            add_callout_box(doc, text_val, bg_color_hex="EAEAEA", border_color_hex=None, bold=True)
        else:
            add_body_paragraph(doc, cleaned, text_color_rgb=text_color_rgb)


def add_appendix_heading(doc, text: str, primary_color_rgb: Any) -> Any:
    """Adds a styled paragraph to a document, formatted as an appendix heading."""
    p = doc.add_paragraph()
    try:
        p.style = "Appendix Heading 1"
    except Exception:
        pass
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Century Gothic"
    run.font.size = Pt(16)
    run.font.bold = True
    if isinstance(primary_color_rgb, tuple):
        run.font.color.rgb = RGBColor(*primary_color_rgb)
    else:
        run.font.color.rgb = primary_color_rgb
    return p


def add_appendix_subheading(doc, text: str, primary_color_rgb: Any) -> Any:
    """Adds a styled paragraph to a document, formatted as an appendix subheading."""
    p = doc.add_paragraph()
    try:
        p.style = "Appendix Heading 2"
    except Exception:
        pass
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.size = Pt(14)
    run.font.bold = True
    if isinstance(primary_color_rgb, tuple):
        run.font.color.rgb = RGBColor(*primary_color_rgb)
    else:
        run.font.color.rgb = primary_color_rgb
    return p


def extract_key_bullets_from_md(md_path: Path, section_marker: str) -> list[str]:
    """Extracts bullet point text from a designated section of a Markdown file.

    Parses a Markdown file to locate a section beginning after a specific marker.
    The function initiates content extraction upon finding a line containing
    `section_marker`. It then collects all subsequent lines formatted as bullet
    points (i.e., starting with `* ` or `- `), stripping the marker itself
    from the captured text. The process also applies HTML entity unescaping to
    each line read from the source file.

    Extraction is terminated if a line begins with "BRECHAS_CLAVE:",
    "FORTALEZAS_CLAVE:", contains "--- FIN TABLA", or if the end of the file is
    reached.

    Args:
        md_path (pathlib.Path): The file system path to the input Markdown file.
        section_marker (str): A substring used to identify the line that immediately
            precedes the target bullet points.

    Returns:
        list[str]: A list containing the text of each extracted bullet point.
            Returns an empty list if the file does not exist, the section marker
            is not found, or the section contains no qualifying bullet points.
    """
    if not md_path.exists():
        return []
    with open(md_path, "r", encoding="utf-8") as f:
        lines = [html.unescape(line) for line in f.readlines()]
    bullets = []
    recording = False
    for line in lines:
        cleaned = line.strip()
        if section_marker in cleaned:
            recording = True
            continue
        if recording:
            if (
                cleaned.startswith("BRECHAS_CLAVE:")
                or cleaned.startswith("FORTALEZAS_CLAVE:")
                or "--- FIN TABLA" in cleaned
            ):
                break
            if cleaned.startswith("* ") or cleaned.startswith("- "):
                bullets.append(cleaned[2:])
    return bullets


def compile_docx(tower_dir: str, output_path: str):
    """Assembles a DOCX report from modular source files and assessment data.

    Generates a styled DOCX report by orchestrating content from a structured
    directory of source files. The function integrates corporate branding profiles,
    internationalization (i18n) locales, assessment data (JSON, CSV), and
    narrative sections (Markdown) into a Word template. The final document
    includes a cover page, table of contents, executive summary, maturity
    analysis, quantitative risk matrix, and appendices.

    Args:
        tower_dir: The root directory path for a specific assessment. This
            directory must contain an `asis_modules` subdirectory with Markdown
            and CSV content, along with root-level JSON files for the assessment
            payload (e.g., `blueprint_*.json`) and scoring results
            (`scoring_output.json`).
        output_path: The full destination file path for the compiled DOCX document.
            The parent directory will be created if it does not exist.

    Returns:
        None. The document is generated and saved to the specified `output_path`.

    Raises:
        FileNotFoundError: If required input files or directories are not found.
        json.JSONDecodeError: If a JSON configuration or data file is malformed.
        ValueError: If data within a source file cannot be parsed into the
            expected numeric type.
    """
    tower_dir_obj = Path(tower_dir)
    modules_dir = tower_dir_obj / "asis_modules"

    print(f"📦 Compilando Anexo Técnico AS-IS Word desde módulos en: {modules_dir}")

    # Dynamically load corporate brand profiles based on the operational context.
    from assessment_engine.infrastructure.config_loader import load_brand_profile

    brand = load_brand_profile()

    company_name = brand.get("company_name", "NTT DATA")
    classification = brand.get("default_classification", "Confidencial")
    disclaimer_text = brand.get("disclaimer_text", "")

    styling = brand.get("styling", {})
    p_color_hex = styling.get("primary_color_hex", "0072BC")
    alt_row_hex = styling.get("alternate_row_color_hex", "F2F2F2")
    text_color_rgb = styling.get("text_dark_color_rgb", [46, 64, 77])

    #
    r_color = int(p_color_hex[0:2], 16)
    g_color = int(p_color_hex[2:4], 16)
    b_color = int(p_color_hex[4:6], 16)
    p_color_rgb = (r_color, g_color, b_color)

    #
    from assessment_engine.infrastructure.runtime_paths import (
        resolve_tower_annex_template_path,
    )

    template_path = resolve_tower_annex_template_path()
    try:
        doc = Document(str(template_path))
        print("   ├─ Plantilla Word pre-estilizada cargada correctamente.")
    except Exception:
        doc = Document()
        print("   ⚠️ No se encontró plantilla. Inicializando documento en blanco.")

    # Initialize the document by removing all placeholder paragraphs and tables from the template.
    for p in list(doc.paragraphs):
        p._element.getparent().remove(p._element)
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    # The `blueprint_payload` file path is resolved dynamically to support a multi-tenant architecture.
    payload_path = next(tower_dir_obj.glob("blueprint_*_payload.json"), None)
    if not payload_path:
        payload_path = tower_dir_obj / "blueprint_t2_payload.json"  #

    scoring_path = tower_dir_obj / "scoring_output.json"

    tower_name = "Desconocida"
    client_name = "Cliente"
    global_fair_ale = 0.0
    global_score = 3.0
    global_band = "Definido"
    global_reading = "Prácticas operativas consolidadas."
    client_group = None
    custom_overview_intro = None

    #
    doc_lang = "es"  #
    doc_date = format_date_spanish()
    doc_version = "1.0"
    currency = "€"
    is_critical = False

    # Local inline Markdown parser to cleanly render bold (**) and italics (_) inside bullet points.
    # Defined early here so it is in scope for any calls inside compile_docx.
    def add_markdown_bullet_local(text, space_after=4):
        p = doc.add_paragraph(style='Bullet')
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Split on the first colon to find the heading label
        if ":" in text:
            label, body = text.split(":", 1)
            run_lbl = p.add_run(label + ":")
            run_lbl.bold = True
            run_lbl.font.name = "Arial"
            run_lbl.font.size = Pt(9.5)
            run_lbl.font.color.rgb = RGBColor(*text_color_rgb)
        else:
            body = text

        # Parse bold parts (**) and italic parts (_)
        bold_parts = body.split("**")
        for b_idx, b_part in enumerate(bold_parts):
            is_bold = b_idx % 2 == 1

            italic_parts = b_part.split("_")
            for i_idx, i_part in enumerate(italic_parts):
                is_italic = i_idx % 2 == 1

                run = p.add_run(i_part)
                run.bold = is_bold
                run.italic = is_italic
                run.font.name = "Arial"
                run.font.size = Pt(9.5)
                run.font.color.rgb = RGBColor(*text_color_rgb)
        return p

    if payload_path.exists():
        with open(payload_path, "r", encoding="utf-8-sig") as f:
            b_data = json.load(f)
            tower_meta = b_data.get("document_meta", {})
            tower_name = tower_meta.get("tower_name", "Desconocida")
            tower_id = tower_meta.get("tower_code", tower_meta.get("tower_id", "TXX"))
            raw_client_name = tower_meta.get("client_name", "Cliente")
            client_name = clean_client_name(raw_client_name)
            
            # Dynamically detect organizational scale to apply customized calibration.
            is_critical = brand.get("styling", {}).get("is_critical", None)
            if is_critical is None:
                is_critical = False # default fallback

            client_group = tower_meta.get("client_parent_group")  #
            global_fair_ale = b_data.get("total_fair_ale", 0.0)
            custom_overview_intro = b_data.get("platform_overview_intro")  #

            # Load internationalization (i18n) parameters from the input payload. The implementation avoids using default or hardcoded locales.
            doc_lang = tower_meta.get("language", "es").lower()

            vocab_fallback = LANG_VOCAB.get(doc_lang, LANG_VOCAB.get("es", {}))
            from assessment_engine.infrastructure.config_loader import resolve_localized_vocabulary
            vocab_loaded = resolve_localized_vocabulary(doc_lang)
            vocab = {**vocab_fallback, **vocab_loaded}

            doc_date = format_date_spanish(tower_meta.get("date"))
            doc_version = tower_meta.get("version", doc_version)
            currency = tower_meta.get("currency", currency)

            # Resolve localized brand attributes
            if "locales" in brand:
                lang_brand = brand["locales"].get(
                    doc_lang, brand["locales"].get("es", {})
                )
                classification = lang_brand.get(
                    "default_classification", classification
                )
                disclaimer_text = lang_brand.get("disclaimer_text", disclaimer_text)

    # Load client_intelligence.json
    intel_data = {}
    client_intel_file = tower_dir_obj.parent / "client_intelligence.json"
    if client_intel_file.exists():
        try:
            with open(client_intel_file, "r", encoding="utf-8-sig") as cif:
                intel_data = json.load(cif)
        except Exception:
            pass

    profile_sec = intel_data.get("profile", {}) if isinstance(intel_data, dict) else {}
    industry = profile_sec.get("industry", "Standard")
    industry_name = (
        profile_sec.get("industry_type_es", "Sector Estándar")
        if doc_lang == "es"
        else profile_sec.get("industry_type_en", "Standard Industry")
    )

    # SOTA Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    # The regulatory framework narrative is mapped dynamically to the client's industry sector.
    if "Financial" in industry or "Banking" in industry:
        reg_name = "las regulaciones vigentes de resiliencia operativa financiera (v.g. DORA o normativas de banca central)" if doc_lang == "es" else "financial operational resilience regulations (e.g. DORA or central bank mandates)"
        reg_fine_limit = f"15.000.000 {currency}"
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = "los marcos normativos de protección de infraestructuras críticas (v.g. Directiva NIS2 o leyes de seguridad nacional)" if doc_lang == "es" else "critical infrastructure protection frameworks (e.g. NIS2 Directive or national security laws)"
        reg_fine_limit = f"10.000.000 {currency}"
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = "los marcos regulatorios sectoriales de Telecomunicaciones, Media y soberanía de datos" if doc_lang == "es" else "sectoral regulatory frameworks for Telecommunications, Media, and data sovereignty"
        reg_fine_limit = f"5.000.000 {currency}"
    elif "Healthcare" in industry:
        reg_name = "las regulaciones de protección de datos de salud y privacidad (v.g. HIPAA o marcos locales equivalentes)" if doc_lang == "es" else "healthcare data protection and privacy regulations (e.g. HIPAA or equivalent local frameworks)"
        reg_fine_limit = f"5.000.000 {currency}"
    else:
        reg_name = "los marcos generales de protección de datos y privacidad (v.g. RGPD o legislación sectorial estándar)" if doc_lang == "es" else "general data protection and privacy frameworks (e.g. GDPR or standard sectoral legislation)"
        reg_fine_limit = f"2.000.000 {currency}"

    if scoring_path.exists():
        with open(scoring_path, "r", encoding="utf-8-sig") as f:
            s_data = json.load(f)
            global_score = s_data.get("tower_score_exact", 3.0)
            global_band = s_data.get("maturity_band_from_exact", {}).get(
                "label", "Definido"
            )
            global_reading = s_data.get("maturity_band_from_exact", {}).get(
                "reading", "Gobernanza estándar."
            )

    org_label = (
        "holding" if client_group else ("group" if doc_lang == "en" else "organización")
    )

    #
    # Assemble and render Section 0: Corporate Cover Page.
    #
    add_spacer(doc, 200)

    p_title = doc.add_paragraph()
    run_title = p_title.add_run(vocab["title"])
    run_title.bold = True
    run_title.font.name = "Arial"
    run_title.font.size = Pt(36)
    run_title.font.color.rgb = RGBColor(*text_color_rgb)

    p_sub = doc.add_paragraph()
    run_sub = p_sub.add_run(f"Anexo Técnico: {tower_name}")
    run_sub.font.name = "Arial"
    run_sub.font.size = Pt(20)
    run_sub.font.color.rgb = RGBColor(*p_color_rgb)

    add_spacer(doc, 140)

    p_client = doc.add_paragraph()
    run_cli_lbl = p_client.add_run(vocab["client_lbl"])
    run_cli_lbl.bold = True
    run_cli_lbl.font.name = "Arial"
    run_cli_lbl.font.size = Pt(28)
    run_cli_lbl.font.color.rgb = RGBColor(*text_color_rgb)

    # Data Sanitization: Avoid hardcoding client-specific holding company names on the cover page to prevent data leakage, per requirement 1.
    if client_group:
        run_cli = p_client.add_run(f"{client_name.upper()} ({client_group})")
    else:
        run_cli = p_client.add_run(f"{client_name.upper()}")
    run_cli.bold = True
    run_cli.font.name = "Arial"
    run_cli.font.size = Pt(28)
    run_cli.font.color.rgb = RGBColor(0, 114, 188)

    add_spacer(doc, 140)

    classification_clean = classification.replace(" (Tier-1 Assessment)", "")

    p_footer = doc.add_paragraph()
    run_date = p_footer.add_run(
        f"{doc_date} | {vocab['v_lbl']}{doc_version} | {classification_clean}"
    )
    run_date.font.name = "Arial"
    run_date.font.size = Pt(9.5)
    run_date.font.color.rgb = RGBColor(150, 150, 150)

    #
    doc.add_page_break()

    #
    # Assemble and render Section 0.1: Table of Contents (TOC).
    #
    add_heading(doc, vocab["toc_title"], level=4, primary_color_rgb=p_color_rgb)
    add_toc(doc)

    # Manual page breaks are not used. Page breaks between chapters are controlled by the 'Page break before' property of the 'Heading 1' style.
    # A page break is automatically inserted before this element. The underlying 'Heading 1' style in the document template is configured with the 'Page break before' property.
    # The `page_break_before` property is enabled on this style to ensure each chapter begins on a new page.

    #
    # Assemble and render Chapter 1: Executive Summary and Business Context.
    #
    parse_and_append_markdown_section(
        doc, modules_dir / "02_resumen_ejecutivo.md", p_color_rgb, text_color_rgb
    )

    #
    # Assemble and render Chapter 2: Objective, Scope, and Assessment Methodology.
    #
    add_heading(
        doc,
        vocab.get("methodology_chapter_title", "Marco de Referencia, Objetivos y Alcance del Assessment"),
        level=1,
        primary_color_rgb=p_color_rgb,
    )
    parse_and_append_markdown_section(
        doc,
        modules_dir / "01_introduccion.md",
        p_color_rgb,
        text_color_rgb,
        skip_level_1=True,
    )

    # Section 2.3 (Contexto Estratégico de Negocio) has been removed from tower-specific reports, as strategic alignment and traceability registry belong exclusively in the Global Consolidated Report, per Gartner standards.

    #
    # Assemble and render Chapter 3: Maturity Profile and General Evaluation.
    #
    chapter_3_title = "Evaluación y Madurez Tecnológica" if doc_lang == "es" else "Technology Maturity and Evaluation"
    add_heading(doc, chapter_3_title, level=1, primary_color_rgb=p_color_rgb)

    # Assemble and render Section 3.1: Global Maturity Dashboard; centered, 2-column layout per requirement 2.
    add_heading(doc, vocab["dashboard_title"], level=2, primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["dashboard_intro"], text_color_rgb=text_color_rgb)

    dash_table = doc.add_table(rows=2, cols=2)
    dash_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(dash_table)

    # Data Sanitization: Ensure data integrity by dynamically resolving scores and qualitative bands from the canonical scoring output.
    formatted_global_score = (
        f"{global_score:.2f}".replace(".", ",")
        if doc_lang == "es"
        else f"{global_score:.2f}"
    )
    display_score_str = (
        f"{formatted_global_score} / 5,00"
        if doc_lang == "es"
        else f"{formatted_global_score} / 5.00"
    )
    display_band_str = f"{global_band}"

    #
    for i, h_txt in enumerate([vocab["score_lbl"], vocab["maturity_lbl"]]):
        set_cell_text_custom(
            dash_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=9,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(dash_table.rows[0].cells[i], p_color_hex)
        dash_table.rows[0].cells[i].width = Inches(3.25)  #

    set_cell_text_custom(
        dash_table.rows[1].cells[0],
        display_score_str,
        bold=True,
        font_size=16,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    set_cell_text_custom(
        dash_table.rows[1].cells[1],
        display_band_str,
        bold=True,
        font_size=12,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )

    # Apply conditional cell shading based on the final severity score. A score below 3.40 receives a yellow background.
    shade_cell(
        dash_table.rows[1].cells[0], "FFF3CD" if global_score < 3.4 else "D9F2D9"
    )
    shade_cell(
        dash_table.rows[1].cells[1], "FFF3CD" if global_score < 3.4 else "D9F2D9"
    )

    # Set data cells to expand to the full table width to maintain a fixed layout.
    dash_table.rows[1].cells[0].width = Inches(3.25)
    dash_table.rows[1].cells[1].width = Inches(3.25)  #

    # Disable the `autofit` property to enforce a fixed table width of 6.5 inches.
    dash_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    add_spacer(doc, 5)

    # Insert a structured, compact reference table detailing the maturity levels, with the client's current level highlighted dynamically.
    add_spacer(doc, 10)
    add_heading(doc, "Marco de Referencia de Niveles de Madurez", level=3, primary_color_rgb=p_color_rgb)

    p_ref_intro = add_body_paragraph(
        doc,
        "La evaluación del nivel de madurez de las capacidades técnicas se fundamenta en un marco de cinco niveles "
        "escalonados (escala de 1,00 a 5,00), alineados con las mejores prácticas de la industria y la ingeniería de software. "
        "La siguiente tabla describe los criterios de valoración y resalta el estado operativo actual de la organización:",
        text_color_rgb=text_color_rgb
    )
    add_spacer(doc, 5)

    ref_table = doc.add_table(rows=1, cols=3)
    ref_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    ref_table.style = "Table Grid"
    
    headers_ref = ["Nivel de Madurez", "Rango", "Descripción de Estado de Prácticas"]
    for i, h_txt in enumerate(headers_ref):
        set_cell_text_custom(ref_table.rows[0].cells[i], h_txt, bold=True, font_size=8.5, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(ref_table.rows[0].cells[i], p_color_hex)
        
    levels_data = [
        ("Nivel 1 - Inicial", "1,00 a 1,79", "Procesos ad-hoc, manuales e individualizados. No existe consistencia en la ejecución ni documentación de soporte."),
        ("Nivel 2 - Repetible", "1,80 a 2,59", "Las tareas básicas se repiten pero dependen del conocimiento de personas clave. Bajo nivel de estandarización."),
        ("Nivel 3 - Definido", "2,60 a 3,39", "Procesos formalizados, documentados e implantados de manera coherente en toda la organización."),
        ("Nivel 4 - Gestionado", "3,40 a 4,19", "Existencia de monitorización continua, telemetrías y KPIs cuantitativos de rendimiento y calidad para controlar el servicio."),
        ("Nivel 5 - Optimizado", "4,20 a 5,00", "Mejora continua automatizada, autorremediación de desviaciones y optimización proactiva de la infraestructura.")
    ]
    
    try:
        gs_val = float(global_score)
    except Exception:
        gs_val = 3.0

    for l_idx, (lvl_name, lvl_range, lvl_desc) in enumerate(levels_data):
        row = ref_table.add_row()
        bg_col = alt_row_hex if l_idx % 2 == 1 else "FFFFFF"
        
        is_active_lvl = False
        if l_idx == 0 and 1.00 <= gs_val <= 1.79:
            is_active_lvl = True
        elif l_idx == 1 and 1.80 <= gs_val <= 2.59:
            is_active_lvl = True
        elif l_idx == 2 and 2.60 <= gs_val <= 3.39:
            is_active_lvl = True
        elif l_idx == 3 and 3.40 <= gs_val <= 4.19:
            is_active_lvl = True
        elif l_idx == 4 and 4.20 <= gs_val <= 5.00:
            is_active_lvl = True
            
        if is_active_lvl:
            # Highlight the active maturity level row to represent the current state dynamically
            row_bg_color = "FFF3CD" if gs_val < 3.4 else "D9F2D9"  # Dynamically synchronized with previous table score band color
            set_cell_text_custom(row.cells[0], f"{lvl_name} (ACTUAL)", bold=True, font_size=8, color_rgb=RGBColor(*p_color_rgb), align=WD_ALIGN_PARAGRAPH.LEFT)
            set_cell_text_custom(row.cells[1], lvl_range, bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            set_cell_text_custom(row.cells[2], lvl_desc, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            for cell in row.cells:
                shade_cell(cell, row_bg_color)
        else:
            set_cell_text_custom(row.cells[0], lvl_name, bold=True, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            shade_cell(row.cells[0], alt_row_hex)
            set_cell_text_custom(row.cells[1], lvl_range, font_size=8, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[1], bg_col)
            set_cell_text_custom(row.cells[2], lvl_desc, font_size=8, align=WD_ALIGN_PARAGRAPH.LEFT)
            shade_cell(row.cells[2], bg_col)
            
    # Set explicit column widths to narrow 'Nivel de Madurez' and widen 'Rango' slightly
    ref_table.allow_autofit = False
    ref_table.autofit = False
    col_widths = [Inches(1.5), Inches(1.2), Inches(3.8)]
    for row in ref_table.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w
            
    add_spacer(doc, 15)

    # Narrative explanation linking the score with the environment context
    score_formatted = f"{gs_val:.2f}".replace(".", ",") if doc_lang == "es" else f"{gs_val:.2f}"
    explanation_str = (
        f"La calificación cuantitativa obtenida de **{score_formatted} sobre 5,00** sitúa a la plataforma en la banda de **{global_band}**. "
        f"Este resultado consolida una situación donde {global_reading.strip()} "
        f"Para avanzar hacia el siguiente umbral de madurez, se requiere corregir de manera prioritaria "
        f"las brechas estructurales de control, los cuellos de botella y la deuda técnica, "
        f"los cuales se detallan analíticamente en los sub-dominios técnicos evaluados a continuación."
    )
    add_body_paragraph(doc, explanation_str, text_color_rgb=text_color_rgb)
    add_spacer(doc, 15)

    # McKinsey/Accenture Style: Matriz de Diagnóstico y Desempeño por Dominio Tecnológico
    health_title = "Matriz de Diagnóstico y Desempeño por Dominio Tecnológico" if doc_lang == "es" else "Diagnosis and Performance Matrix by Technology Domain"
    add_heading(doc, health_title, level=2, primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, "A continuación, se detalla el perfil de desempeño operativo y de gobierno para cada uno de los sub-dominios técnicos evaluados dentro de esta torre:", text_color_rgb=text_color_rgb)
    add_spacer(doc, 5)

    health_table = doc.add_table(rows=1, cols=3)
    health_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    health_table.style = "Table Grid"

    for i, h_txt in enumerate([
        "Pilar / Capacidad Tecnológica Evaluada",
        "Score AS-IS",
        "Nivel de Madurez" if doc_lang == "es" else "Maturity Level"
    ]):
        set_cell_text_custom(health_table.rows[0].cells[i], h_txt, bold=True, font_size=10, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER)
        shade_cell(health_table.rows[0].cells[i], p_color_hex)

    if b_data and "pillars_analysis" in b_data:
        for s_idx, p in enumerate(sorted(b_data.get("pillars_analysis", []), key=lambda item: item.get("score", 0.0))):
            bg = alt_row_hex if s_idx % 2 == 1 else "FFFFFF"
            p_name = p.get("pilar_name", "Pilar")
            p_score = float(p.get("score", 3.0))

            score_formatted = f"{p_score:.2f}".replace(".", ",") if doc_lang == "es" else f"{p_score:.2f}"

            # Map score to status and color
            if p_score >= 4.20:
                p_status = "Optimizado" if doc_lang == "es" else "Optimized"
                p_bg_color = "D9F2D9"
            elif p_score >= 3.40:
                p_status = "Gestionado y Medido" if doc_lang == "es" else "Managed"
                p_bg_color = "E2F0D9"
            elif p_score >= 2.60:
                p_status = "Definido" if doc_lang == "es" else "Defined"
                p_bg_color = "FFF3CD"
            elif p_score >= 1.80:
                p_status = "Repetible" if doc_lang == "es" else "Repeatable"
                p_bg_color = "FCE4D6"
            else:
                p_status = "Inicial" if doc_lang == "es" else "Initial"
                p_bg_color = "F2D9D9"

            row = health_table.add_row()
            set_cell_text_custom(row.cells[0], p_name, bold=True, font_size=10)
            shade_cell(row.cells[0], alt_row_hex)
            
            set_cell_text_custom(row.cells[1], score_formatted, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[1], bg)
            
            set_cell_text_custom(row.cells[2], p_status, bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
            shade_cell(row.cells[2], p_bg_color)
            
    autofit_table_to_contents(health_table)
    add_spacer(doc, 20)

    # Assemble and render Section 3.2: Full-Page Radar Chart; custom dimensions per user request.
    add_heading(doc, vocab["radar_title"], level=2, primary_color_rgb=p_color_rgb)
    radar_path = tower_dir_obj / "pillar_radar_chart.generated.png"
    if not radar_path.exists() and b_data and "pillars_analysis" in b_data:
        try:
            from assessment_engine.application.generate_tower_radar_chart import generate_radar_chart_from_pillars
            chart_pillars = []
            for p in b_data.get("pillars_analysis", []):
                chart_pillars.append({
                    "pillar_label": p.get("pilar_name", p.get("pilar_id", "Pilar")),
                    "score_display": p.get("score", 0.0)
                })
            if chart_pillars:
                generate_radar_chart_from_pillars(chart_pillars, radar_path)
                print(f"✅ Gráfico radial auto-generado con éxito en: {radar_path}")
        except Exception as ex:
            print(f"⚠️ No se pudo auto-generar el gráfico radial: {ex}")

    if radar_path.exists():
        add_spacer(doc, 5)
        doc.add_picture(str(radar_path), width=Cm(11.11), height=Cm(9.18))  #
        p_img = doc.paragraphs[-1]
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_spacer(doc, 15)

    # RAGE Forensic Verification Injection
    snapshot_file = tower_dir_obj.parent / "benchmarks_snapshot.json"
    if snapshot_file.exists():
        try:
            with open(snapshot_file, "r", encoding="utf-8-sig") as sf:
                snap_data = json.load(sf)
            snapshots = snap_data.get("snapshots", {})
            if snapshots:
                # Silent Drop: Filter and find valid, verified benchmarks for the current tower
                valid_snapshots = []
                for t_id, t_snap in sorted(snapshots.items()):
                    if t_id != tower_id:
                        continue
                    verif_status = t_snap.get("verification_status", "failed")
                    quote = t_snap.get("evidence_quote", "")
                    if verif_status == "verified" and quote and "no se encontraron" not in quote.lower() and "no se ha encontrado" not in quote.lower():
                        valid_snapshots.append((t_id, t_snap))

                if valid_snapshots:
                    add_heading(doc, "Justificación de Estándares Sectoriales (Trazabilidad RAGE)", level=2, primary_color_rgb=p_color_rgb)
                    intro_text = (
                        "Los estándares de mercado del gráfico radial anterior se han calibrado y verificado en tiempo "
                        "de ejecución mediante el motor RAGE (Runtime Agentic Grounding & Evaluation). Cada benchmark "
                        "está respaldado por evidencias factoperativas y copias de seguridad de documentos oficiales:"
                    )
                    add_body_paragraph(doc, intro_text, text_color_rgb=text_color_rgb)
                    add_spacer(doc, 10)

                    for t_id, t_snap in valid_snapshots:
                        framework_name = t_snap.get("framework_name", "Estándar Sectorial")
                        score = t_snap.get("dynamic_score", 4.0)
                        quote = t_snap.get("evidence_quote", "")
                        url = t_snap.get("evidence_source_url", "")
                        local_path = t_snap.get("local_snapshot_path", "")

                        header_p = f"**Torre {t_id} ({framework_name}) - Estándar: {score:,.1f}**"
                        add_body_paragraph(doc, header_p, text_color_rgb=text_color_rgb)

                        quote_p = f"✓ Evidencia extraída: \"{quote}\""
                        add_body_paragraph(doc, quote_p, italic=True, text_color_rgb=text_color_rgb)

                        source_p = f"Referencia: {url}"
                        if local_path:
                            source_p += f" | Bóveda local: {local_path}"
                        add_body_paragraph(doc, source_p, text_color_rgb=RGBColor(120, 130, 140))
                        add_spacer(doc, 10)
        except Exception as ex:
            print(f"⚠️  [RAGE] Failed to inject RAGE report into main document: {ex}")

    # Assemble and render Section 3.3: Score Justification Matrix; left-aligned, omits 'TO-BE Target' column.
    csv_mat_path = modules_dir / "04_matriz_madurez.csv"
    if csv_mat_path.exists():
        mat_table = doc.add_table(rows=1, cols=3)
        mat_table.alignment = WD_TABLE_ALIGNMENT.LEFT
        mat_table.style = "Table Grid"

        headers_mat = vocab["justification_table_headers"]
        for i, h_txt in enumerate(headers_mat):
            set_cell_text_custom(
                mat_table.rows[0].cells[i],
                h_txt,
                bold=True,
                font_size=9,
                color_rgb=RGBColor(255, 255, 255),
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(mat_table.rows[0].cells[i], p_color_hex)

        with open(csv_mat_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)  #

            for r_idx, row_data in enumerate(reader):
                row = mat_table.add_row()
                set_cell_text_custom(
                    row.cells[0], row_data[0], bold=True, font_size=8.5
                )
                set_cell_text_custom(
                    row.cells[1],
                    row_data[1],
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                
                # Sanitize the third column text to remove "(X,XX)" from the "Justificación de la Nota" heading
                justification_cell_text = row_data[2]
                import re
                justification_cell_text = re.sub(
                    r"\*\*Justificación de la Nota\s*\(\d+[,.]\d+\):\*\*",
                    "**Justificación de la Nota:**",
                    justification_cell_text
                )
                justification_cell_text = re.sub(
                    r"Justificación de la Nota\s*\(\d+[,.]\d+\):",
                    "Justificación de la Nota:",
                    justification_cell_text
                )
                
                set_cell_text_custom(
                    row.cells[2],
                    justification_cell_text,
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.JUSTIFY,
                )

                if r_idx % 2 == 1:
                    for cell in row.cells:
                        shade_cell(cell, alt_row_hex)

        autofit_table_to_contents(mat_table)
        add_spacer(doc, 20)

    # 3.4 Assemble and render Section: Cross-Cutting Analysis and Systemic Risk
    transversal_title = "Análisis Transversal de Deuda Tecnológica y Patrones de Riesgo Estructural" if doc_lang == "es" else "Cross-Cutting Analysis of Technological Debt and Structural Risk Patterns"
    add_heading(doc, transversal_title, level=2, primary_color_rgb=p_color_rgb)
    parse_and_append_markdown_section(
        doc,
        modules_dir / "05_transversal.md",
        p_color_rgb,
        text_color_rgb,
        skip_level_1=True,
    )

    # 3.5 Indicadores de Riesgo Estructural y Contexto de Decisión
    if intel_data:
        try:
            overrides = intel_data.get("tower_overrides", {}).get(tower_id, {})
            metrics = overrides.get("metrics", {}) if isinstance(overrides, dict) else {}
            business_criticality = metrics.get("business_criticality") if isinstance(metrics, dict) else None
            regulatory_compliance = metrics.get("regulatory_compliance") if isinstance(metrics, dict) else None
            implementation_feasibility = metrics.get("implementation_feasibility") if isinstance(metrics, dict) else None
            
            sensitivity = overrides.get("sensitivity_analysis", {}) if isinstance(overrides, dict) else {}
            dii_03 = None
            if isinstance(sensitivity, dict):
                dii_03 = sensitivity.get("decision_instability_indices", {}).get("dii_threshold_03_pct")
            
            epistemic = intel_data.get("epistemic_graph", {}) if isinstance(intel_data, dict) else {}
            audits = epistemic.get("audits", {}) if isinstance(epistemic, dict) else {}
            erc_dict = audits.get("eigenvector_risk_centrality", {}) if isinstance(audits, dict) else {}
            erc = erc_dict.get(tower_id) if isinstance(erc_dict, dict) else None
            
            spof_by_cascade = audits.get("single_point_of_failure_by_cascade", "") if isinstance(audits, dict) else ""
            spof_by_centrality = audits.get("single_point_of_failure_by_centrality", "") if isinstance(audits, dict) else ""
            
            if business_criticality is not None:
                add_heading(doc, "Análisis de Interdependencias Tecnológicas y Negocio", level=2, primary_color_rgb=p_color_rgb)
                
                # Introductory paragraph (un-italicized, justified, size 10)
                if doc_lang == "es":
                    intro_text_inter = (
                        "La infraestructura tecnológica no opera de manera aislada; un evento en un dominio específico puede "
                        "propagar riesgos y afectar la continuidad de los servicios de negocio de forma inmediata. Por ello, "
                        "esta sección conecta el diagnóstico técnico de la plataforma con su impacto estratégico real. Para lograrlo, "
                        "el motor de evaluación analiza de forma integrada tres dimensiones clave:"
                    )
                else:
                    intro_text_inter = (
                        "Technology infrastructure does not operate in isolation; an event in a specific domain can propagate "
                        "risks and immediately impact business service continuity. Therefore, this section connects the technical "
                        "diagnosis of the platform with its real strategic impact. To achieve this, the evaluation engine integrates "
                        "three key dimensions:"
                    )
                add_body_paragraph(doc, intro_text_inter, text_color_rgb=text_color_rgb)
                
                # Three clear bullet points
                if doc_lang == "es":
                    add_body_paragraph(doc, "Criticidad Operativa y Presión Regulatoria: Determina el nivel de dependencia directa de los procesos de negocio y la exigencia de conformidad legal y normativa (v.g. NIS2, ENS Categoría Alta) sobre este dominio.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Viabilidad de la Transformación: Estima la complejidad técnica y facilidad operativa para ejecutar los proyectos del plan de acción propuesto.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Propagación Topológica y SPOF: Cuantifica el riesgo de que un incidente crítico se propague en cascada a otras torres y determina si el dominio actúa como un Punto Único de Fallo.", style="List Bullet", text_color_rgb=text_color_rgb)
                else:
                    add_body_paragraph(doc, "Operational Criticality and Regulatory Pressure: Assesses the level of direct business process dependency and legal compliance requirements (e.g., NIS2, ENS High Category) on this domain.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Transformation Feasibility: Estimates the technical complexity and operational ease of executing the projects in the proposed action plan.", style="List Bullet", text_color_rgb=text_color_rgb)
                    add_body_paragraph(doc, "Topological Propagation and SPOF: Quantifies the risk of critical incident cascade propagation to other towers and determines if the domain acts as a Single Point of Failure.", style="List Bullet", text_color_rgb=text_color_rgb)
                
                # Concluding paragraph (size 10, justified)
                if doc_lang == "es":
                    desc_rest = "Estos indicadores proporcionan un contexto de decisión cuantitativo y objetivo, permitiendo priorizar las inversiones de transformación en base a su retorno estratégico y resiliencia para la organización:"
                else:
                    desc_rest = "These indicators provide an objective, quantitative decision context, allowing strategic investments to be prioritized based on transformation viability and overall resilience:"
                add_body_paragraph(doc, desc_rest, text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 5)

                spof_status = "SÍ" if (tower_id == spof_by_cascade or tower_id == spof_by_centrality) else "NO"
                dii_val = f"{dii_03:.1f}%" if dii_03 is not None else "0,0%"
                erc_val = f"{erc:.3f}" if erc is not None else "0,000"

                inter_table = doc.add_table(rows=1, cols=3)
                inter_table.alignment = WD_TABLE_ALIGNMENT.CENTER
                inter_table.style = "Table Grid"

                headers_inter = ["Indicador Estratégico", "Valor / Score", "Estado y Clasificación"]
                for i, h_txt in enumerate(headers_inter):
                    set_cell_text_custom(
                        inter_table.rows[0].cells[i], h_txt, bold=True, font_size=10, color_rgb=RGBColor(255, 255, 255), align=WD_ALIGN_PARAGRAPH.CENTER
                    )
                    shade_cell(inter_table.rows[0].cells[i], p_color_hex)

                inter_data = [
                    ("Criticidad de Negocio (MCDA)", f"{business_criticality:.1f}%", "Extrema (Pilar Crítico)" if business_criticality >= 80.0 else "Alta" if business_criticality >= 50.0 else "Media"),
                    ("Presión Regulatoria (MCDA)", f"{regulatory_compliance:.1f}%", "Crítica (NIS2/ENS/PIC)" if regulatory_compliance >= 80.0 else "Alta" if regulatory_compliance >= 50.0 else "Estándar"),
                    ("Viabilidad Operativa (MCDA)", f"{implementation_feasibility:.1f}%", "Viable" if implementation_feasibility >= 60.0 else "Complejo (Requiere mitigación)"),
                    ("Consistencia del Diagnóstico (DII)", dii_val, "Estable (Diagnóstico Robusto)" if (dii_03 or 0) < 15.0 else "Moderado" if (dii_03 or 0) < 30.0 else "Sensible"),
                    ("Propagación de Fallos en Cascada (ERC)", erc_val, "Alta Influencia" if (erc or 0) >= 0.50 else "Media" if (erc or 0) >= 0.20 else "Baja/Aislada"),
                    ("Punto Único de Fallo (SPOF)", spof_status, "Cuello de Botella Estructural" if spof_status == "SÍ" else "Estable en Red Causal")
                ]

                for r_idx, row_vals in enumerate(inter_data):
                    row = inter_table.add_row()
                    set_cell_text_custom(row.cells[0], row_vals[0], bold=True, font_size=10)
                    
                    if row_vals[0] == "Punto Único de Fallo (SPOF)":
                        set_cell_text_custom(row.cells[1], row_vals[1], bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        shade_cell(row.cells[1], "F2D9D9" if spof_status == "SÍ" else "D9F2D9")
                    else:
                        set_cell_text_custom(row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                        
                    set_cell_text_custom(row.cells[2], row_vals[2], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

                    if r_idx % 2 == 0:
                        for cell in row.cells:
                            if cell != row.cells[1] or row_vals[0] != "Punto Único de Fallo (SPOF)":
                                shade_cell(cell, alt_row_hex)

                autofit_table_to_contents(inter_table)
                add_spacer(doc, 10)

                # Add Glossary / Legend
                p_gloss = doc.add_paragraph()
                p_gloss.paragraph_format.space_before = Pt(8)
                p_gloss.paragraph_format.space_after = Pt(2)
                run_g_title = p_gloss.add_run("Análisis Ejecutivo de Indicadores de Interdependencia:")
                run_g_title.bold = True
                run_g_title.font.name = "Arial"
                run_g_title.font.size = Pt(10)
                run_g_title.font.color.rgb = RGBColor(*text_color_rgb)

                glossary_items = []
                
                # Business Criticality
                if business_criticality >= 80.0:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Extrema]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. En este caso, este valor extremo confirma que los procesos operativos core de la organización dependen críticamente de esta plataforma, y su indisponibilidad causaría una interrupción inmediata de servicios esenciales."
                    )
                elif business_criticality >= 50.0:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Alta]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El score alto refleja una fuerte dependencia operativa, si bien existe un margen de tolerancia temporal antes de que impacte directamente en la continuidad del negocio."
                    )
                else:
                    glossary_items.append(
                        f"**Criticidad de Negocio (MCDA) [{business_criticality:.1f}% - Media]:** Evalúa el nivel de dependencia directa que tienen los procesos operativos clave de la organización sobre esta torre, determinando el impacto de negocio en caso de indisponibilidad del servicio. El impacto medio sugiere que la torre provee servicios de soporte o back-office cuya indisponibilidad temporal es asumible mediante planes de contingencia estándar."
                    )

                # Regulatory Compliance
                if regulatory_compliance >= 80.0:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Crítica]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo directivas críticas como NIS2, ENS Categoría Alta o PIC) que aplica sobre el perímetro de esta plataforma. Este score revela una exposición regulatoria crítica, donde las brechas de seguridad se traducen directamente en riesgo de sanciones económicas elevadas y responsabilidad legal corporativa."
                    )
                elif regulatory_compliance >= 50.0:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Moderada]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo directivas críticas como NIS2, ENS Categoría Alta o PIC) que aplica sobre el perímetro de esta plataforma. Existen requerimientos de cumplimiento y políticas de seguridad corporativas estrictas, requiriendo auditorías periódicas de los controles de TI."
                    )
                else:
                    glossary_items.append(
                        f"**Presión Regulatoria (MCDA) [{regulatory_compliance:.1f}% - Estándar]:** Mide la exigencia de conformidad legal y normativa obligatoria (bajo directivas críticas como NIS2, ENS Categoría Alta o PIC) que aplica sobre el perímetro de esta plataforma. Exposición regulatoria estándar basada en el cumplimiento de buenas prácticas de ingeniería sin un escrutinio normativo crítico directo."
                    )

                # Implementation Feasibility
                if implementation_feasibility >= 60.0:
                    glossary_items.append(
                        f"**Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Favorable]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La viabilidad de transformación es favorable. Los proyectos de modernización se pueden abordar con tecnologías maduras y recursos disponibles en el mercado sin generar disrupciones críticas."
                    )
                else:
                    glossary_items.append(
                        f"**Viabilidad Operativa (MCDA) [{implementation_feasibility:.1f}% - Compleja]:** Estima el nivel de complejidad operativa y facilidad técnica para ejecutar los proyectos del plan de acción propuesto, considerando recursos, ventanas de mantenimiento y dependencias previas. La baja calificación actual refleja que existe una alta complejidad para la transformación debido a la presencia de deudas estructurales profundas, cuellos de botella en el mantenimiento o falta de talento especializado."
                    )

                # DII
                dii_pct = dii_03 if dii_03 is not None else 0.0
                if dii_pct < 15.0:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Alta Estabilidad]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). En este caso, el índice extremadamente bajo garantiza de forma objetiva que el diagnóstico es altamente robusto y representativo de la realidad de la plataforma, impidiendo que fluctuaciones puntuales alteren las conclusiones estratégicas."
                    )
                elif dii_pct < 30.0:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Estabilidad Moderada]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El índice registrado indica una sensibilidad moderada; el diagnóstico es sustancialmente estable, si bien ciertas puntuaciones dependen en parte de interpretaciones técnicas que requieren consolidación técnica futura."
                    )
                else:
                    glossary_items.append(
                        f"**Consistencia del Diagnóstico (Índice DII) [{dii_pct:.1f}% - Sensibilidad Alta (Volátil)]:** Este indicador (Decision Instability Index) mide la robustez matemática del diagnóstico frente a cambios en la información de partida. Evalúa cuál es la probabilidad de que una variación menor en las evidencias documentales o en las respuestas de las entrevistas provoque una alteración o inestabilidad en la calificación final de madurez de la torre (valores bajos garantizan un diagnóstico altamente consistente y fiable). El valor registrado muestra una sensibilidad alta, sugiriendo que la escasez de evidencias o variaciones de criterio podrían alterar la nota asignada, por lo que se recomienda un análisis de contraste de evidencias confirmatorio."
                    )

                # ERC
                erc_val_num = erc if erc is not None else 0.0
                if erc_val_num >= 0.50:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Alta]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. El índice confirma una influencia estructural alta, donde una degradación de servicio desestabilizaría de manera en cadena gran parte de la plataforma corporativa."
                    )
                elif erc_val_num >= 0.20:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Media]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor elevado indica que un incidente crítico en este perímetro se propagaría con gran facilidad hacia otras áreas conectadas. La influencia estructural registrada es media; un incidente tendría un efecto moderado o contenido, afectando solo a sistemas inmediatamente adyacentes."
                    )
                else:
                    glossary_items.append(
                        f"**Propagación de Fallos (ERC) [{erc_val_num:.3f} - Baja/Aislada]:** Cuantifica el grado de influencia de esta torre sobre el resto de dominios tecnológicos. Un valor de propagación bajo indica una influencia estructural baja; un fallo técnico se contendría dentro de su propio perímetro sin arrastrar a otras torres tecnológicas clave."
                    )

                # SPOF
                if spof_status == "SÍ":
                    glossary_items.append(
                        "**Punto Único de Fallo (SPOF) [SÍ - Crítico]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación alerta de manera inequívoca que esta plataforma representa un cuello de botella o eslabón débil crítico sin redundancia suficiente, requiriendo acción de mitigación inmediata."
                    )
                else:
                    glossary_items.append(
                        "**Punto Único de Fallo (SPOF) [NO - Estable]:** Identifica si el dominio tecnológico actúa como un cuello de botella o eslabón débil de la infraestructura que, en caso de caída o compromiso técnico, detendría inmediatamente los flujos de servicio esenciales de la organización. La evaluación confirma que esta torre no actúa como un cuello de botella o eslabón débil único en la topología de la red operativa general."
                    )
                
                for item in glossary_items:
                    add_body_paragraph(doc, item, style="Bullet", text_color_rgb=text_color_rgb)
                
                add_spacer(doc, 20)
        except Exception as e:
            print(f"⚠️ Error injecting systemic risk metrics: {e}")

    #
    # Assemble and render Chapter 4: Quantitative Risk Matrix.
    #
    add_heading(doc, vocab["risk_matrix_title"], level=1, primary_color_rgb=p_color_rgb)

    # Format the Annualized Loss Expectancy (ALE) value. Localization logic is isolated in a separate function, per requirement 2.
    t_sep = vocab.get("thousands_sep", ".")
    d_sep = vocab.get("decimal_sep", ",")
    formatted_ale = format_currency_custom(global_fair_ale, t_sep, d_sep)

    # Load dynamic SRE hourly rate and currency symbol from custom calibration if available (FAIR-MAM)
    import os
    client_id = os.environ.get("ASSESSMENT_CLIENT_ID", "generic_client")
    tower_id = b_data.get("document_meta", {}).get("tower_code", "T2")
    custom_profile_path = Path(f"working/{client_id}/{tower_id}/custom_risk_profile.json")
    if not custom_profile_path.exists():
        for t_code in ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]:
            temp_path = Path(f"working/{client_id}/{t_code}/custom_risk_profile.json")
            if temp_path.exists():
                custom_profile_path = temp_path
                break

    custom_calibration = {}
    if custom_profile_path.exists():
        try:
            with open(custom_profile_path, "r", encoding="utf-8-sig") as cf:
                custom_calibration = json.load(cf)
        except Exception:
            pass

    sre_rate = round(float(custom_calibration.get("hourly_rate_sre_eur", 36.0)))
    currency = custom_calibration.get("currency_symbol", "€" if doc_lang == "es" else "$")

    # Calculate aggregate Tail Risk (P90 and Max Probable Loss)
    total_p90 = 0.0
    total_max = 0.0
    try:
        for pillar in b_data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                total_p90 += hc.get("fair_p90_score", 0.0) or 0.0
                total_max += hc.get("fair_max_score", 0.0) or 0.0
    except Exception:
        pass
    
    formatted_p90 = format_currency_custom(total_p90, t_sep, d_sep).split(d_sep)[0]
    formatted_max = format_currency_custom(total_max, t_sep, d_sep).split(d_sep)[0]

    if doc_lang == "es":
        intro_prose_p1 = (
            f"Los riesgos identificados en este análisis han sido modelados y evaluados utilizando el modelo de "
            f"**Análisis Cuantitativo de Riesgo Tecnológico** basado en el estándar internacional **O-FAIR (Open Factor Analysis of Information Risk)**, "
            f"una metodología estándar reconocida globalmente para traducir deudas técnicas en impacto financiero real para el negocio."
        )
        intro_prose_p2 = (
            f"El análisis cuantitativo del estado actual establece que las deudas técnicas operativas y las vulnerabilidades detectadas exclusivamente "
            f"dentro del perímetro de esta torre tecnológica exponen a {client_name} a una **Expectativa de Pérdida Anualizada (ALE - Annual Loss Exposure)** "
            f"de **{formatted_ale} {currency}** anuales. Es fundamental entender que esta métrica representa el impacto económico promedio latente (fricción operativa, "
            f"coste de horas de ticketing manual e ineficiencias de procesos rutinarios) que la organización asume de manera ordinaria como el 'coste de hacer negocio' si decide mantener el statu quo."
        )
        intro_prose_p3 = (
            f"Por el contrario, el verdadero caso de negocio y la justificación de la inversión tecnológica no reside en mitigar esa ineficiencia promedio, "
            f"sino en proteger el balance frente a escenarios de estrés operativo y regulatorio severo. Para ello, el modelo calcula los escenarios más "
            f"extremos en la cola de la distribución mediante el llamado **Déficit Esperado Condicional o CVaR al 97.5% (Expected Shortfall)**. "
            f"En un escenario de alta adversidad anual (donde los procesos manuales colapsen por saturación de incidentes concurrentes o se active la exposición "
            f"a sanciones bajo {reg_name}), la exposición de la plataforma podría promediar los **{formatted_p90} {currency}**, "
            f"llegando a un límite máximo estimado (P99) de **{formatted_max} {currency}**."
        )
        intro_prose_p4 = (
            f"Es crítico destacar que, ante esta exposición, la opción de añadir recursos humanos adicionales (tales como la incorporación de "
            f"personal de soporte operativo extraordinario) no mitiga el riesgo, sino que multiplica la probabilidad de error humano, el cual constituye "
            f"estadísticamente la causa raíz de más del 80% de los fallos de configuración. Adicionalmente, las intervenciones manuales no escalan físicamente "
            f"ante picos de demanda o incidentes de gran escala (provocando la violación de los RTOs exigidos por la red de transporte eléctrico), "
            f"y mantener un proceso crítico sin controles automatizados puede ser catalogado como negligencia regulatoria estructural bajo las estrictas "
            f"exigencias de debida diligencia de la directiva {reg_name}, exponiendo a la compañía a sanciones de rango máximo. Por tanto, estas cifras reflejan "
            f"la asunción de riesgo implícita de mantener el estado actual (coste de inacción)."
        )
        intro_prose_p5 = (
            f"*(Nota: Para garantizar que estas proyecciones financieras sean objetivas y auditables, el modelo de cálculo no emplea estimaciones subjetivas "
            f"arbitrarias, sino que opera bajo un proceso riguroso de tres etapas: 1) Los rangos iniciales se calibran con bases de datos de siniestralidad reales del sector de "
            f"infraestructuras críticas (específicamente el **Verizon Data Breach Investigations Report - DBIR** y el estudio **IBM Cost of a Data Breach** de Ponemon Institute); "
            f"2) Estos rangos promedio se ajustan aplicando un factor de escala bayesiano derivado de la madurez real de {client_name} y de vuestra tarifa horaria de convenio en `rate_card.json` ({sre_rate} {currency}/hora); "
            f"y 3) Se ejecuta una simulación estocástica de Monte Carlo de 10.000 iteraciones truncada al percentil 99.0% para descartar outliers por causas de fuerza mayor. "
            f"Para una comprensión detallada de los principios estadísticos, se recomienda consultar el Apéndice Metodológico situado al final de este informe).*"
        )
    else:
        intro_prose_p1 = (
            f"The risks identified in this assessment have been modeled and evaluated using the **Quantitative Technology Risk Analysis** "
            f"model based on the international **O-FAIR (Open Factor Analysis of Information Risk)** standard, a globally recognized methodology "
            f"to translate technical debts directly into real financial impact for the business."
        )
        intro_prose_p2 = (
            f"The quantitative current state analysis establishes that the technical operational debts and identified vulnerabilities exclusively "
            f"within the perimeter of this technological tower expose {client_name} to a real **Annual Loss Exposure (ALE)** "
            f"of **{formatted_ale} {currency}** annually. It is crucial to understand that this metric represents the average latent economic "
            f"impact (operational friction, manual ticketing support salary costs, and routine process inefficiencies) that the organization assumes ordinarily as the 'cost of doing business' "
            f"if it chooses to maintain the status quo."
        )
        intro_prose_p3 = (
            f"On the contrary, the true business case and justification for technological investment does not lie in mitigating that average inefficiency, "
            f"but in protecting the balance sheet against severe operational and regulatory stress scenarios. To do this, the model calculates extreme tail scenarios using "
            f"**Conditional Value at Risk (CVaR) or Expected Shortfall at 97.5%**. In a highly adverse annual scenario (where manual processes "
            f"collapse under the strain of concurrent incidents or exposure to severe penalties under {reg_name} is triggered), the financial "
            f"exposure of the platform will average **{formatted_p90} {currency}**, potentially reaching an estimated maximum plausible limit (P99) of up to **{formatted_max} {currency}**."
        )
        intro_prose_p4 = (
            f"It is critical to note that, in the face of this exposure, the option of adding additional human resources (such as the incorporation of "
            f"extraordinary operational support personnel) does not mitigate the risk, but rather multiplies the probability of human error, which statistically constitutes the "
            f"root cause of over 80% of configuration failures. Additionally, manual interventions do not physically scale under stress or large-scale "
            f"incidents (leading to the violation of RTOs required by the electrical grid), and maintaining a critical process without automated controls "
            f"can be classified as structural regulatory negligence under the strict due diligence requirements of the {reg_name} directive, exposing the company to maximum-range "
            f"sancions. Therefore, these figures reflect the implicit risk assumption of maintaining the status quo (cost of inaction)."
        )
        intro_prose_p5 = (
            f"*(Note: To ensure these financial projections are objective and auditable, the calculation model does not employ subjective estimates "
            f"arbitrarily, but operates under a rigorous three-stage process: 1) Initial ranges are calibrated with actual loss databases of the "
            f"critical infrastructure sector, specifically the **Verizon Data Breach Investigations Report - DBIR** and the **IBM Cost of a Data Breach** study; "
            f"2) These average industry ranges are adjusted using a Bayesian scale factor derived from {client_name}'s real maturity and your agreement hourly rate in `rate_card.json` ({sre_rate} {currency}/hour); "
            f"and 3) A Monte Carlo stochastic simulation of 10,000 iterations truncated at the 99.0th percentile is run to discard extreme force majeure outliers. "
            f"For a detailed understanding of the statistical principles, please refer to the Methodological Appendix at the end of this report).*"
        )

    add_body_paragraph(doc, intro_prose_p1, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p2, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p3, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p4, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, intro_prose_p5, text_color_rgb=text_color_rgb, italic=True)

    # El Hexágono de Valor de NTT DATA (SME & TBM Framework)
    add_appendix_subheading(doc, "El Hexágono de Valor: Palancas de Retorno de Resiliencia y Eficiencia (RoRE)", primary_color_rgb=p_color_rgb)
    
    if doc_lang == "es":
        lever_intro = (
            "Para proporcionar una visión empresarial de 360 grados que justifique las decisiones de modernización tecnológica, "
            "este diagnóstico complementa la cuantificación de riesgos de Open FAIR con el marco internacional de gestión de valor "
            "**TBM (Technology Business Management)** y **FinOps**. Toda ineficiencia o proceso manual identificado en esta torre "
            "se analiza de manera agregada bajo seis dimensiones o palancas de valor diferenciadas:"
        )
        add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
        
        add_markdown_bullet_local(
            "Palanca 1 - Recuperación de Capital Laboral (Lean IT): Cuantifica el coste salarial directo perdido de forma recurrente "
            "por los ingenieros sénior al ejecutar tareas manuales rutinarias que un sistema programático realizaría en segundos.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 2 - Coste de Oportunidad del Talento: El valor marginal que la organización deja de percibir al mantener a sus "
            "arquitectos e ingenieros sénior haciendo mantenimiento reactivo en lugar de dedicarlos a proyectos de innovación estratégica.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 3 - Coste de Demora de Proyectos (Demora de Proyectos): La pérdida económica indirecta que sufre el negocio debido a que "
            "los proyectos estratégicos se retrasan semanas esperando el aprovisionamiento o la configuración manual de Sistemas.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 4 - Eliminación de Desperdicio de Infraestructura (Capacity Waste): El sobrecoste derivado de la sobredimensión "
            "de almacenamiento o servidores 'por si acaso' en procesos manuales, así como la acumulación de recursos huérfanos encendidos.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 5 - Evitación de Costes de Soporte por Obsolescencia: El sobreprecio extraordinario de mantenimiento (Extended Support) "
            "que se paga a fabricantes para mantener con vida asistida hardware o software legacy que carece de soporte estándar.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Palanca 6 - Mitigación de Riesgos de Cola de Balance: La reducción real de la probabilidad de sufrir incidentes catastróficos "
            "por error humano (causa del 80% de caídas de red) o severas sanciones legales por negligencia regulatoria bajo NIS2 (CVaR P99).",
            space_after=12
        )
    else:
        lever_intro = (
            "To provide a 360-degree business view that justifies technological modernization decisions, "
            "this diagnosis complements Open FAIR risk quantification with the international value management frameworks "
            "**TBM (Technology Business Management)** and **FinOps**. Every technical debt or manual process identified in this tower "
            "is analyzed in an aggregated manner under six distinct value levers:"
        )
        add_body_paragraph(doc, lever_intro, text_color_rgb=text_color_rgb)
        
        add_markdown_bullet_local(
            "Lever 1 - Labor Capital Recovery (Lean IT): Quantifies the direct salary cost lost on a recurring basis "
            "by senior engineers executing routine manual tasks that a programmatic system would perform in seconds.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 2 - Talent Opportunity Cost: The marginal value that the organization fails to realize by keeping "
            "its senior architects and engineers on reactive maintenance instead of dedicating them to strategic innovation projects.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 3 - Project Cost of Delay: The indirect financial loss suffered by the business due to "
            "strategic projects being delayed for weeks waiting for manual provisioning or systems configuration.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 4 - Capacity Waste Elimination (FinOps): The extra cost derived from overprovisioning "
            "storage or servers 'just in case' in manual processes, as well as the accumulation of running orphaned resources.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 5 - Extended Support Avoidance: The extraordinary maintenance premium paid to vendors "
            "to keep legacy hardware or software on life support when it lacks standard official support.",
            space_after=3
        )
        add_markdown_bullet_local(
            "Lever 6 - Tail Risk Balance Sheet Mitigation: The real reduction in the probability of suffering catastrophic "
            "incidents due to human error (root cause of 80% of outages) or severe NIS2 penalties under stress (CVaR P99).",
            space_after=12
        )

    #
    csv_risks_path = modules_dir / "06_matriz_riesgos_fair.csv"
    risks_data_list = []
    risks_by_pilar = {}

    if csv_risks_path.exists():
        with open(csv_risks_path, "r", encoding="utf-8") as cf:
            reader = csv.reader(cf, delimiter=";")
            next(reader)
            for r_idx, row_data in enumerate(reader):
                pilar_full_name = row_data[0].split(" - ")[0]
                r_item = {
                    "id": f"RVS{r_idx + 1:02d}",
                    "pilar": pilar_full_name,
                    "capability": row_data[0].split(" - ")[1]
                    if " - " in row_data[0]
                    else row_data[0],
                    "finding": row_data[1],
                    "business_risk": row_data[2],
                    "tef": float(row_data[3]),
                    "lm": float(row_data[4]),
                    "ale": float(row_data[5]),
                    "prioritization_rationale": row_data[6]
                    if len(row_data) > 6
                    else None,  #
                }
                risks_data_list.append(r_item)

                if pilar_full_name not in risks_by_pilar:
                    risks_by_pilar[pilar_full_name] = []
                risks_by_pilar[pilar_full_name].append(r_item)

    # Assemble and render Section 5.1: 5x5 Heatmap as a centered, native table mosaic.
    if risks_data_list:
        add_heading(
            doc, vocab["exposure_summary_title"], level=2, primary_color_rgb=p_color_rgb
        )

        if doc_lang == "es":
            sec_intro_p1 = (
                f"Para facilitar la visualización y priorización de las deudas técnicas y vulnerabilidades identificadas, se presenta a continuación la "
                f"**Matriz de Riesgo Cuantitativa (Mosaico 5x5)**. Este mapa de calor distribuye los riesgos detectados interrelacionando la "
                f"**Frecuencia de Eventos de Amenaza (TEF)** (estimación anualizada de ocurrencias) con la **Magnitud de la Pérdida (LM)** (el impacto financiero de cada evento)."
            )
            sec_intro_p2 = (
                f"La calibración de los rangos de esta Magnitud de Pérdida (LM) para {client_name} se realiza bajo el criterio riguroso de operador de "
                f"{industry_name}. De acuerdo con el estudio de referencia mundial *ITIC Global Server Hardware Downtime Report*, el coste promedio de indisponibilidad "
                f"de sistemas core supera el millón de euros por hora para el 98% de los operadores de su sector, debido a la interrupción en cadena de procesos operativos, "
                f"las severas penalizaciones por acuerdos de nivel de servicio (SLA) y los costes de remediación forense urgente."
            )
            sec_intro_p3 = (
                f"Bajo esta base empírica, los umbrales de pérdida financiera de la matriz se bareman de forma escalonada para modelar con precisión el impacto directivo real en los siguientes cuadrantes:"
            )
        else:
            sec_intro_p1 = (
                f"To facilitate the visualization and prioritization of the identified technical vulnerabilities, the **Quantitative Risk Matrix (5x5 Heatmap)** "
                f"is presented below. This heatmap distributes the risks by cross-referencing the **Threat Event Frequency (TEF)** (annualized frequency of occurrence) "
                f"with the **Loss Magnitude (LM)** (the financial impact of each event)."
            )
            sec_intro_p2 = (
                f"The calibration of these Loss Magnitude (LM) ranges for {client_name} is performed under the rigorous criteria of a "
                f"{industry_name} operator. According to the global benchmark study *ITIC Global Server Hardware Downtime Report*, the average cost "
                f"of core system downtime exceeds one million euros per hour for 98% of operators in its sector, due to cascading process interruptions, "
                f"severe Service Level Agreement (SLA) penalties, and urgent forensic remediation costs."
            )
            sec_intro_p3 = (
                f"Based on this empirical foundation, the financial loss thresholds of the matrix are graduated to accurately model the real management impact across the following quadrants:"
            )
            
        add_body_paragraph(doc, sec_intro_p1, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p2, text_color_rgb=text_color_rgb)
        add_body_paragraph(doc, sec_intro_p3, text_color_rgb=text_color_rgb)
        add_spacer(doc, 15)

        matrix_cells = {r: {c: [] for c in range(1, 6)} for r in range(5, 0, -1)}
        for r in risks_data_list:
            r_tef = min(5, max(1, int(round(r["tef"]))))
            r_lm = min(5, max(1, int(round(r["lm"]))))
            matrix_cells[r_tef][r_lm].append(r["id"])

        # Initialize a 6x6 table (5x5 data grid plus headers). The table is centered and set to full page width.
        heatmap_table = doc.add_table(rows=6, cols=6)
        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        finalize_table(heatmap_table)

        #
        cell_0_0 = heatmap_table.rows[0].cells[0]
        set_cell_text_custom(
            cell_0_0,
            "TEF \\ LM",
            bold=True,
            font_size=9,
            align=WD_ALIGN_PARAGRAPH.CENTER,
            color_rgb=RGBColor(255, 255, 255),
            no_bullets=True,
        )
        shade_cell(cell_0_0, COLOR_BLUE)
        set_cell_border_white(cell_0_0)
        cell_0_0.width = Inches(1.3)  # Slightly wider for inline ranges
        cell_0_0.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        
        for col_idx in range(1, 6):
            if is_critical:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 10k {currency}",
                    3: f"10k - 50k {currency}",
                    4: f"50k - 300k {currency}",
                    5: f"250k - 1.5M {currency}",
                }
            else:
                lm_ranges = {
                    1: f"< 1k {currency}",
                    2: f"1k - 5k {currency}",
                    3: f"5k - 25k {currency}",
                    4: f"25k - 100k {currency}",
                    5: f"100k - 500k {currency}",
                }
            lm_lbl = f"LM {col_idx}\n({lm_ranges[col_idx]})"
            cell = heatmap_table.rows[0].cells[col_idx]
            set_cell_text_custom(
                cell,
                lm_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell, COLOR_BLUE)
            set_cell_border_white(cell)
            cell.width = Inches(1.04)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        # Populate the 5x5 data matrix with content, ensuring it fills the full width of the table.
        for row_idx, tef_val in enumerate(range(5, 0, -1), 1):
            tef_ranges = {
                5: f"> 10/año" if doc_lang == "es" else f"> 10/year",
                4: f"2,0 - 10/año" if doc_lang == "es" else f"2.0 - 10/year",
                3: f"0,5 - 2,0/año" if doc_lang == "es" else f"0.5 - 2.0/year",
                2: f"0,1 - 0,5/año" if doc_lang == "es" else f"0.1 - 0.5/year",
                1: f"< 0,1/año" if doc_lang == "es" else f"< 0.1/year",
            }
            tef_lbl = f"TEF {tef_val}\n({tef_ranges[tef_val]})"
            cell_header = heatmap_table.rows[row_idx].cells[0]
            set_cell_text_custom(
                cell_header,
                tef_lbl,
                bold=True,
                font_size=9,
                align=WD_ALIGN_PARAGRAPH.CENTER,
                color_rgb=RGBColor(255, 255, 255),
                no_bullets=True,
            )
            shade_cell(cell_header, COLOR_BLUE)
            set_cell_border_white(cell_header)
            cell_header.width = Inches(1.3)
            cell_header.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            for col_idx, lm_val in enumerate(range(1, 6), 1):
                cell = heatmap_table.rows[row_idx].cells[col_idx]

                # Configure table dimensions to create a fixed, full-width mosaic layout.
                cell.width = Inches(1.04)
                heatmap_table.rows[row_idx].height = Cm(0.4)

                cell_risks = matrix_cells[tef_val][lm_val]
                cell_text = ", ".join(cell_risks) if cell_risks else "-"

                set_cell_text_custom(
                    cell,
                    cell_text,
                    bold=True,
                    font_size=8,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                set_cell_border_white(cell)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                severity = tef_val * lm_val
                if severity >= 15:
                    shade_cell(cell, "FADBD8")  #
                elif severity >= 8:
                    shade_cell(cell, "FCF3CF")  #
                else:
                    shade_cell(cell, "D5F5E3")  #

        heatmap_table.alignment = WD_TABLE_ALIGNMENT.CENTER  # Recalculate cell content alignment. This is required because the initial auto-fit operation may not apply alignment correctly.
        add_spacer(doc, 20)

    # Build a lookup map from blueprint payload findings for detailed FAIR metrics
    fair_lookup = {}
    if payload_path.exists():
        try:
            for pillar in b_data.get("pillars_analysis", []):
                for hc in pillar.get("health_check_asis", []):
                    cap_name = hc.get("capability")
                    if cap_name:
                        fair_lookup[cap_name] = {
                            "p90": hc.get("fair_p90_score", 0.0),
                            "min": hc.get("fair_min_score", 0.0),
                            "max": hc.get("fair_max_score", 0.0),
                        }
        except Exception:
            pass

    # Assemble and render Section 5.3: Detailed Risk Register; left-aligned content per requirement 4.2.
    add_heading(
        doc, vocab["detailed_risks_title"], level=2, primary_color_rgb=p_color_rgb
    )

    if doc_lang == "es":
        detailed_risks_intro = (
            "El inventario analítico se presenta estructurado en **Portafolios de Priorización de Deuda Técnica** (conforme al estándar Open FAIR™), "
            "agrupando los hallazgos según su impacto económico relativo dentro de la propia torre. Esta clasificación dinámica "
            "establece tres niveles de prioridad basados en la desviación de cada riesgo respecto al coste de inacción promedio de la plataforma."
        )
        guide_intro = "Adicionalmente, para facilitar la lectura y comprensión del impacto financiero en las fichas detalladas, las métricas de exposición proyectada representan:"
    else:
        detailed_risks_intro = (
            "The analytical inventory is structured into **Technical Debt Prioritization Portfolios** (in accordance with the Open FAIR™ standard), "
            "grouping findings based on their relative economic impact within the tower itself. This dynamic classification "
            "establishes three priority levels based on each risk's deviation from the platform's average cost of inaction."
        )
        guide_intro = "Additionally, to facilitate reading and understanding the financial impact in the detailed cards, the projected exposure metrics represent:"

    add_body_paragraph(doc, detailed_risks_intro, text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, guide_intro, text_color_rgb=text_color_rgb)

    if doc_lang == "es":
        b1_text = "Pérdida Anualizada (ALE): El coste económico promedio esperado cada año. Constituye el valor base del coste de inacción operativo."
        b2_text = "Peor Caso (CVaR): El promedio económico del 10% de los peores escenarios posibles. Indica la magnitud del desastre financiero si las amenazas más graves se materializan de forma simultánea en un mismo año."
        b3_text = "Rango Probabilístico: El abanico estadístico de pérdidas posibles, desde un impacto menor hasta el máximo teórico si se detonan sanciones regulatorias o incumplimientos de SLA."
    else:
        b1_text = "Annualized Loss Expectancy (ALE): The average economic cost expected each year. It constitutes the baseline value of the operational cost of inaction."
        b2_text = "Worst Case (CVaR): The economic average of the 10% worst-case scenarios. It indicates the magnitude of the financial disaster if the most severe threats materialize simultaneously in a single year."
        b3_text = "Probabilistic Range: The statistical spectrum of possible losses, from a minor impact up to the theoretical maximum if regulatory sanctions or SLA breaches are triggered."

    add_body_paragraph(doc, b1_text, style="List Bullet", text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, b2_text, style="List Bullet", text_color_rgb=text_color_rgb)
    add_body_paragraph(doc, b3_text, style="List Bullet", text_color_rgb=text_color_rgb)

    add_spacer(doc, 15)

    # Dynamic Relative Materiality Threshold Calculation (Statistical Mean ALE)
    total_risks_count = len(risks_data_list)
    local_mean_ale = (sum(r["ale"] for r in risks_data_list) / total_risks_count) if total_risks_count > 0 else 0.0
    
    tier1_threshold = local_mean_ale * 1.5
    tier2_threshold = local_mean_ale * 0.5

    tier1_risks = [r for r in risks_data_list if r["ale"] >= tier1_threshold]
    tier2_risks = [r for r in risks_data_list if tier2_threshold <= r["ale"] < tier1_threshold]
    tier3_risks = [r for r in risks_data_list if r["ale"] < tier2_threshold]

    # Sort each tier by ALE descending to guarantee standard prioritization
    tier1_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier2_risks.sort(key=lambda x: x["ale"], reverse=True)
    tier3_risks.sort(key=lambda x: x["ale"], reverse=True)

    t_sep1 = format_currency_custom(tier1_threshold, t_sep, d_sep).split(d_sep)[0]
    t_sep2 = format_currency_custom(tier2_threshold, t_sep, d_sep).split(d_sep)[0]
    
    tiers_config = [
        (
            "Tier 1: Prioridad de Modernización",
            "Tier 1: Modernization Priority",
            tier1_risks,
            f"Hallazgos de alto impacto (outliers estadísticos con exposición mayor o igual a {t_sep1} {currency}/año) que concentran la mayor ineficiencia financiera relativa dentro de esta plataforma. Representan las principales prioridades de modernización para mitigar el riesgo de la torre."
            if doc_lang == "es" else
            f"High-impact findings (statistical outliers with exposure greater than or equal to {t_sep1} {currency}/year) that concentrate the highest relative financial inefficiency within this platform. They represent the main modernization priorities to mitigate the tower's risk."
        ),
        (
            "Tier 2: Optimización Operativa",
            "Tier 2: Operational Optimization",
            tier2_risks,
            f"Ineficiencias operativas que se sitúan en torno a la exposición promedio de la torre (entre {t_sep2} y {t_sep1} {currency}/año). Constituyen la fricción técnica y operativa normalizada del ecosistema actual."
            if doc_lang == "es" else
            f"Operational inefficiencies situated around the tower's average exposure (between {t_sep2} and {t_sep1} {currency}/year). They constitute the normalized technical and operational friction of the current ecosystem."
        ),
        (
            "Tier 3: Backlog de Mantenimiento",
            "Tier 3: Maintenance Backlog",
            tier3_risks,
            f"Desviaciones menores (exposición menor a {t_sep2} {currency}/año) cuyo peso estadístico es marginal frente a la deuda técnica total de la torre, representando oportunidades de mejora o mantenimiento ordinario."
            if doc_lang == "es" else
            f"Minor deviations (exposure under {t_sep2} {currency}/year) whose statistical weight is marginal against the tower's total technical debt, representing ordinary maintenance or improvement opportunities."
        ),
    ]

    for title_es, title_en, p_risks, p_desc in tiers_config:
        title = title_es if doc_lang == "es" else title_en
        
        add_heading(
            doc,
            title,
            level=3,
            primary_color_rgb=p_color_rgb,
        )
        add_body_paragraph(doc, p_desc, text_color_rgb=text_color_rgb)
        add_spacer(doc, 10)

        if not p_risks:
            empty_msg = (
                "No se registran vulnerabilidades de esta prioridad de exposición en la evaluación actual."
                if doc_lang == "es" else
                "No vulnerabilities of this exposure priority are registered in the current assessment."
            )
            add_body_paragraph(doc, empty_msg, text_color_rgb=text_color_rgb)
            add_spacer(doc, 15)
            continue

        table_risks = doc.add_table(rows=1, cols=3)
        table_risks.alignment = WD_TABLE_ALIGNMENT.LEFT
        finalize_table(table_risks)
        table_risks.autofit = False
        table_risks.allow_autofit = False

        tblPr = table_risks._tbl.tblPr
        if tblPr is None:
            tblPr = OxmlElement('w:tblPr')
            table_risks._tbl.insert(0, tblPr)

        # Apply robust OXML column widths to guarantee Word doesn't shrink the third column
        tblGrid = table_risks._tbl.find(qn('w:tblGrid'))
        if tblGrid is not None:
            table_risks._tbl.remove(tblGrid)
            
        tblGrid = OxmlElement('w:tblGrid')
        col_widths = [Cm(1.2), Cm(10.45), Cm(5.77)]
        for w in col_widths:
            gridCol = OxmlElement('w:gridCol')
            gridCol.set(qn('w:w'), str(int(w.twips)))
            tblGrid.append(gridCol)
            
        # Insert tblGrid immediately after tblPr to conform to OOXML schema
        tblPr_index = table_risks._tbl.index(tblPr)
        table_risks._tbl.insert(tblPr_index + 1, tblGrid)
        
        # Remove any existing autofit tags and set rigid total width
        for child in list(tblPr):
            if child.tag.endswith('tblLayout') or child.tag.endswith('tblW'):
                tblPr.remove(child)
                
        tblLayout = OxmlElement('w:tblLayout')
        tblLayout.set(qn('w:type'), 'fixed')
        tblPr.append(tblLayout)
        
        tblW = OxmlElement('w:tblW')
        tblW.set(qn('w:type'), 'dxa')
        tblW.set(qn('w:w'), str(sum(int(w.twips) for w in col_widths)))
        tblPr.append(tblW)

        headers_table = vocab["detailed_risks_headers"]
        for i, h_txt in enumerate(headers_table):
            cell = table_risks.rows[0].cells[i]
            set_cell_text_custom(
                cell,
                h_txt,
                bold=True,
                font_size=8.5,
                color_rgb=RGBColor(255, 255, 255),
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            # Force exact width on the cell level in OXML
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
            tcPr.append(tcW)
            shade_cell(cell, p_color_hex)

        for r_idx, r in enumerate(p_risks):
            row = table_risks.add_row()

            #
            set_cell_text_custom(
                row.cells[0],
                r["id"],
                bold=True,
                font_size=8.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(row.cells[0], alt_row_hex)

            # Assemble and render Section 2: Description and Evidence, justified per user request.
            # Clear default paragraph and build explicitly to prevent Shift+Enter stretching bugs
            cell_desc = row.cells[1]
            cell_desc.text = ""
            p_desc_lbl = cell_desc.paragraphs[0]
            p_desc_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_desc_lbl.paragraph_format.space_after = Pt(2)

            finding = r["finding"]
            biz_risk = r["business_risk"]
            cap_name = r["capability"]

            parts_f = finding.split("\n\nEvidencia Forense Literal (Audit RAG):\n")

            import re
            clean_finding_text = clean_text_for_word(parts_f[0]).replace("sistémicas", "estructurales").replace("sistémicos", "estructurales").replace("Sistémicas", "Estructurales").replace("Sistémicos", "Estructurales").replace("sistémica", "estructural").replace("sistémico", "estructural").replace("Sistémica", "Estructural").replace("Sistémico", "Estructural")
            clean_finding_text = re.sub(re.escape(raw_client_name), client_name, clean_finding_text, flags=re.IGNORECASE).strip()
            
            clean_biz_text = clean_text_for_word(biz_risk).replace("sistémicas", "estructurales").replace("sistémicos", "estructurales").replace("Sistémicas", "Estructurales").replace("Sistémicos", "Estructurales").replace("sistémica", "estructural").replace("sistémico", "estructural").replace("Sistémica", "Estructural").replace("Sistémico", "Estructural")
            clean_biz_text = re.sub(re.escape(raw_client_name), client_name, clean_biz_text, flags=re.IGNORECASE).strip()

            run_obs = p_desc_lbl.add_run("Vulnerabilidad Identificada:")
            run_obs.bold = True
            run_obs.font.name = "Arial"
            run_obs.font.size = Pt(8.5)

            p_desc_txt = cell_desc.add_paragraph(clean_finding_text)
            p_desc_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_desc_txt.paragraph_format.space_after = Pt(8)
            for run in p_desc_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            p_biz_lbl = cell_desc.add_paragraph()
            p_biz_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_biz_lbl.paragraph_format.space_after = Pt(2)
            run_biz = p_biz_lbl.add_run("Impacto de TI / Operativo:")
            run_biz.bold = True
            run_biz.font.name = "Arial"
            run_biz.font.size = Pt(8.5)

            p_biz_txt = cell_desc.add_paragraph(clean_biz_text)
            p_biz_txt.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p_biz_txt.paragraph_format.space_after = Pt(0)
            for run in p_biz_txt.runs:
                run.font.name = "Arial"
                run.font.size = Pt(8.5)

            # Assemble and render Section 3: Business Risk and FAIR Impact, left-aligned per user request.
            # Use native paragraphs to avoid Shift+Enter stretching bugs and carriage return issues
            cell_risk = row.cells[2]
            cell_risk.text = ""
            p_fair_lbl = cell_risk.paragraphs[0]
            p_fair_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_lbl.paragraph_format.space_after = Pt(2)
            run_fair_lbl = p_fair_lbl.add_run("Exposición Cuantitativa (FAIR):")
            run_fair_lbl.bold = True

            tef = r["tef"]
            lm = r["lm"]
            ale = r["ale"]

            # Fetch detailed FAIR metrics from lookup map
            fair_metrics = fair_lookup.get(cap_name, {})
            p90_val = fair_metrics.get("p90", 0.0) or 0.0
            min_val = fair_metrics.get("min", 0.0) or 0.0
            max_val = fair_metrics.get("max", 0.0) or 0.0

            p_fair_val = cell_risk.add_paragraph()
            p_fair_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_fair_val.paragraph_format.space_after = Pt(6)
            p_fair_val.add_run(f"• Frecuencia (TEF): {tef:.1f} / 5,0\n• Magnitud (LM): {lm:.1f} / 5,0")

            p_exp_lbl = cell_risk.add_paragraph()
            p_exp_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_lbl.paragraph_format.space_after = Pt(2)
            run_exp_lbl = p_exp_lbl.add_run("Exposición Financiera Proyectada:")
            run_exp_lbl.bold = True

            p_exp_val = cell_risk.add_paragraph()
            p_exp_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p_exp_val.paragraph_format.space_after = Pt(0)

            formatted_p90 = format_currency_custom(p90_val, t_sep, d_sep).split(d_sep)[0]
            formatted_min = format_currency_custom(min_val, t_sep, d_sep).split(d_sep)[0]
            formatted_max = format_currency_custom(max_val, t_sep, d_sep).split(d_sep)[0]
            formatted_ale_item = format_currency_custom(ale, t_sep, d_sep).split(d_sep)[0]

            p_exp_val.add_run("• Pérdida Anualizada (ALE): ")
            run_ale_val = p_exp_val.add_run(f"{formatted_ale_item} {currency}\n")
            run_ale_val.bold = True
            run_ale_val.font.color.rgb = RGBColor(180, 0, 0)
            
            p_exp_val.add_run(f"• Peor Caso (CVaR): {formatted_p90} {currency}\n")
            p_exp_val.add_run(f"• Rango Probabilístico: {formatted_min} {currency} a {formatted_max} {currency}")

            # Apply fonts to all runs in the third cell
            for p_item in cell_risk.paragraphs:
                for r_item in p_item.runs:
                    r_item.font.name = "Arial"
                    r_item.font.size = Pt(8.5)

            # Apply uniform alternating row backgrounds to maintain pure aesthetic logic
            row_bg = alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
            for i in range(3):
                shade_cell(row.cells[i], row_bg)

            # Apply vertical centering to all cells in the row
            row.cells[0].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[1].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            row.cells[2].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # Enforce exact centimeter-based column widths on every cell of every row at the VERY END, 
            # so that previous text injections and shade_cell don't overwrite the tcPr OXML.
            for i in range(3):
                cell = row.cells[i]
                tcPr = cell._tc.get_or_add_tcPr()
                tcW = tcPr.find(qn('w:tcW'))
                if tcW is not None:
                    tcPr.remove(tcW)
                tcW = OxmlElement('w:tcW')
                tcW.set(qn('w:type'), 'dxa')
                tcW.set(qn('w:w'), str(int(col_widths[i].twips)))
                tcPr.append(tcW)

        add_spacer(doc, 15)

    #
    # Assemble and render Chapter 5: Conclusiones y Coste de Inacción.
    #
    add_heading(doc, "Conclusiones y Coste de Inacción", level=1, primary_color_rgb=p_color_rgb)

    # 5.1 Conclusiones del Diagnóstico de Situación
    add_heading(doc, "Conclusiones del Diagnóstico de Situación", level=2, primary_color_rgb=p_color_rgb)
    parse_and_append_markdown_section(
        doc,
        modules_dir / "07_conclusiones.md",
        p_color_rgb,
        text_color_rgb,
        start_header="Implicaciones Operativas Clave",
        end_header="Coste de Inacción",
    )

    # 5.2 El Dilema del Decisor: Matriz de Contraste Estratégico
    add_heading(doc, "El Dilema del Decisor: Matriz de Contraste Estratégico", level=2, primary_color_rgb=p_color_rgb)
    
    matrix_intro = (
        "Para confrontar de manera clara y directa el impacto de las decisiones de gobierno técnico sobre la plataforma, "
        "se presenta la Matriz de Contraste del Decisor. Esta tabla comparativa expone la bifurcación operativa y de negocio "
        "que asume la organización al optar por el inmovilismo frente a un proceso estructurado de modernización técnica:"
    )
    add_body_paragraph(doc, matrix_intro, text_color_rgb=text_color_rgb)

    # Render decision matrix table
    dec_table = doc.add_table(rows=1, cols=3)
    dec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(dec_table)
    dec_table.autofit = False
    dec_table.allow_autofit = False

    dec_col_widths = [Cm(3.0), Cm(6.71), Cm(6.71)] # Sums to 16.42 cm, standard page content area
    
    # Header cells
    dec_headers = [
        "Dimensión de Negocio",
        "Camino A: Inacción (Do Nothing)",
        "Camino B: Modernización Estructural"
    ]
    for i, h_txt in enumerate(dec_headers):
        cell = dec_table.rows[0].cells[i]
        set_cell_text_custom(
            cell,
            h_txt,
            bold=True,
            font_size=8.5,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
            no_bullets=True
        )
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = tcPr.find(qn('w:tcW'))
        if tcW is not None:
            tcPr.remove(tcW)
        tcW = OxmlElement('w:tcW')
        tcW.set(qn('w:type'), 'dxa')
        tcW.set(qn('w:w'), str(int(dec_col_widths[i].twips)))
        tcPr.append(tcW)
        shade_cell(cell, p_color_hex)

    # Data Rows
    matrix_data = [
        (
            "Exposición Económica",
            f"• Consumo anual de la Expectativa de Pérdida Anualizada (**{formatted_ale_item} {currency}** de ALE).\n• Vulnerabilidad latente a pérdidas por Déficit Esperado Condicional de hasta **{formatted_p90} {currency}**.\n• Acumulación de deuda técnica inasumible e incremento exponencial de ineficiencias operativas en 5 años.",
            "• Amortización progresiva de la deuda técnica.\n• Recuperación de la eficiencia operativa y reducción de la exposición al riesgo en un **80%**.\n• Retorno de inversión claro basado en la eliminación de pérdidas."
        ),
        (
            "Resiliencia y SLA",
            "• Operación reactiva en silos técnicos con procesos manuales.\n• Incremento constante del tiempo de resolución de fallos (MTTR).\n• Detección tardía de incidentes críticos por usuarios finales.",
            "• Observabilidad unificada y capacidades proactivas (AIOps).\n• Reducción radical del MTTR y prevención de fallos antes del impacto.\n• Estabilidad y fiabilidad garantizadas mediante SLOs técnicos."
        ),
        (
            "Gobernanza y NIS2",
            "• Incapacidad estructural para demostrar cumplimiento normativo en tiempo real.\n• Exposición activa a severas sanciones administrativas bajo marcos regulatorios (ENS y NIS2, hasta 10M €).",
            "• Cumplimiento continuo y auditable por diseño mediante gobernanza programática (*Policy-as-Code*).\n• Conformidad nativa y automática de la infraestructura."
        ),
        (
            "Talento y Evolución",
            "• Sobrecarga de los equipos de sistemas en tareas repetitivas y manuales.\n• Desgaste del talento, aumento de la rotación y estancamiento del Time-to-Market de proyectos estratégicos.",
            "• Autoservicio unificado (*Platform Self-Service*) que elimina la fricción para desarrolladores.\n• Liberación de la sobrecarga del equipo de IT para centrar el talento en tareas de alto valor estratégico."
        )
    ]

    for r_idx, row_data in enumerate(matrix_data):
        row = dec_table.add_row()
        row_bg = alt_row_hex if r_idx % 2 == 1 else "FFFFFF"
        for i in range(3):
            cell = row.cells[i]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            
            # Format lists in matrix cells using robust inline markdown parser
            lines = row_data[i].split("\n")
            for l_idx, line in enumerate(lines):
                if l_idx > 0:
                    p = cell.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT

                # Clean bullet prefix from parsing
                line_clean = line
                if line_clean.startswith("• "):
                    line_clean = line_clean[2:]

                # Native inline parser for **bold** and *italic*
                bold_parts = line_clean.split("**")
                for b_idx, b_part in enumerate(bold_parts):
                    is_bold = b_idx % 2 == 1
                    italic_parts = b_part.split("*")
                    for i_idx, i_part in enumerate(italic_parts):
                        is_italic = i_idx % 2 == 1
                        run = p.add_run(i_part)
                        run.font.name = "Arial"
                        run.font.size = Pt(8.5)
                        run.bold = is_bold
                        run.italic = is_italic

                p.paragraph_format.space_after = Pt(2) if l_idx < len(lines) - 1 else Pt(0)
                if line.startswith("• "):
                    p.paragraph_format.left_indent = Inches(0.15)
                    # Prepend a bullet character
                    p.paragraph_format.left_indent = Inches(0.15)
            
            shade_cell(cell, row_bg)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

            # Width enforcement
            tcPr = cell._tc.get_or_add_tcPr()
            tcW = tcPr.find(qn('w:tcW'))
            if tcW is not None:
                tcPr.remove(tcW)
            tcW = OxmlElement('w:tcW')
            tcW.set(qn('w:type'), 'dxa')
            tcW.set(qn('w:w'), str(int(dec_col_widths[i].twips)))
            tcPr.append(tcW)

    # 5.3 El Impacto de la Indecisión: Exposición Financiera Acumulada (Cumulative CoI)
    add_heading(doc, "El Impacto de la Indecisión: Exposición Financiera Acumulada", level=2, primary_color_rgb=p_color_rgb)
    
    # SOTA Actuarial Practice: Cumulative Adverse Multi-Year Stress Test (FRTB / Basel III)
    # Instead of multiplying the extreme worst-case annual loss by 3 or 5 (which implies experiencing 
    # 3 or 5 consecutive catastrophic years, an operational impossibility), we model exactly ONE 
    # catastrophic year (the CVaR/Expected Shortfall) plus N-1 average years (ALE) during that horizon.
    coi_adverse_3y = total_p90 + (global_fair_ale * 2)
    coi_adverse_5y = total_p90 + (global_fair_ale * 4)

    # Calculate accumulated costs
    ale_3y = format_currency_custom(global_fair_ale * 3, t_sep, d_sep).split(d_sep)[0]
    ale_5y = format_currency_custom(global_fair_ale * 5, t_sep, d_sep).split(d_sep)[0]
    p90_3y = format_currency_custom(coi_adverse_3y, t_sep, d_sep).split(d_sep)[0]
    p90_5y = format_currency_custom(coi_adverse_5y, t_sep, d_sep).split(d_sep)[0]

    coi_intro = (
        "Retrasar el proceso de modernización o postergar la remediación de la deuda técnica bajo el principio de 'ahorrar costes' "
        "constituye, en términos de Value-at-Risk (VaR), la decisión de balance más costosa para la organización. Al modelar la "
        "Exposición Financiera Acumulada de la torre tecnológica en horizontes temporales de 3 y 5 años, las pérdidas de negocio proyectadas "
        "demuestran el verdadero coste latente de la inacción:"
    )
    add_body_paragraph(doc, coi_intro, text_color_rgb=text_color_rgb)

    # Bullet 1 with native Word Bullet style
    p_coi_1 = doc.add_paragraph(style='Bullet')
    p_coi_1.paragraph_format.space_after = Pt(4)
    p_coi_1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    run_b1_lbl = p_coi_1.add_run("Coste de Inacción Promedio Acumulado (ALE):")
    run_b1_lbl.bold = True
    run_b1_lbl.font.name = "Arial"
    run_b1_lbl.font.size = Pt(9.5)
    run_b1_lbl.font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_1.add_run(" Equivale a una ineficiencia económica absorbida de ")
    p_coi_1.runs[-1].font.name = "Arial"
    p_coi_1.runs[-1].font.size = Pt(9.5)
    p_coi_1.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_1.add_run(f"{ale_3y} {currency}").bold = True
    p_coi_1.runs[-1].font.name = "Arial"
    p_coi_1.runs[-1].font.size = Pt(9.5)
    p_coi_1.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_1.add_run(" a 3 años y hasta ")
    p_coi_1.runs[-1].font.name = "Arial"
    p_coi_1.runs[-1].font.size = Pt(9.5)
    p_coi_1.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_1.add_run(f"{ale_5y} {currency}").bold = True
    p_coi_1.runs[-1].font.name = "Arial"
    p_coi_1.runs[-1].font.size = Pt(9.5)
    p_coi_1.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_1.add_run(" a 5 años.")
    p_coi_1.runs[-1].font.name = "Arial"
    p_coi_1.runs[-1].font.size = Pt(9.5)
    p_coi_1.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)

    # Bullet 2 with native Word Bullet style
    p_coi_2 = doc.add_paragraph(style='Bullet')
    p_coi_2.paragraph_format.space_after = Pt(0)
    p_coi_2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    run_b2_lbl = p_coi_2.add_run("Exposición Estocástica de Estrés Operativo (CVaR):")
    run_b2_lbl.bold = True
    run_b2_lbl.font.name = "Arial"
    run_b2_lbl.font.size = Pt(9.5)
    run_b2_lbl.font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_2.add_run(" Si ocurre exactamente un año de crisis extrema durante el horizonte temporal, la pérdida acumulada escalará a ")
    p_coi_2.runs[-1].font.name = "Arial"
    p_coi_2.runs[-1].font.size = Pt(9.5)
    p_coi_2.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_2.add_run(f"{p90_3y} {currency}").bold = True
    p_coi_2.runs[-1].font.name = "Arial"
    p_coi_2.runs[-1].font.size = Pt(9.5)
    p_coi_2.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_2.add_run(" a 3 años y hasta ")
    p_coi_2.runs[-1].font.name = "Arial"
    p_coi_2.runs[-1].font.size = Pt(9.5)
    p_coi_2.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_2.add_run(f"{p90_5y} {currency}").bold = True
    p_coi_2.runs[-1].font.name = "Arial"
    p_coi_2.runs[-1].font.size = Pt(9.5)
    p_coi_2.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)
    
    p_coi_2.add_run(" a 5 años.")
    p_coi_2.runs[-1].font.name = "Arial"
    p_coi_2.runs[-1].font.size = Pt(9.5)
    p_coi_2.runs[-1].font.color.rgb = RGBColor(*text_color_rgb)

    add_spacer(doc, 15)

    #
    # Assemble and render Appendix A: Metodología Cuantitativa de Riesgos
    #
    add_appendix_heading(doc, "Metodología Cuantitativa de Riesgos", primary_color_rgb=p_color_rgb)
    add_body_paragraph(
        doc,
        "Este apéndice detalla el rigor metodológico, las ecuaciones estadísticas y los supuestos actuariales de "
        "calibración aplicados para sustentar las evaluaciones de riesgo de este informe. El objetivo de esta sección "
        "es blindar la validez de las proyecciones de costes frente a cualquier proceso de auditoría y, a la vez, "
        "explicar de manera sencilla y transparente cómo se conectan las deudas tecnológicas con el impacto financiero real.",
        text_color_rgb=text_color_rgb
    )

    # Detect if the organization operates in a regulated critical sector to apply custom parameters
    is_critical_client = is_critical if is_critical is not None else True
    
    # SOTA Actuarial Practice: Dynamic Regulatory Mapping (Industry Routing)
    # The regulatory framework narrative is mapped dynamically to the client's industry sector.
    if "Financial" in industry or "Banking" in industry:
        reg_name = "las regulaciones vigentes de resiliencia operativa financiera (v.g. DORA o normativas de banca central)"
        reg_fine_limit = f"15.000.000 {currency}"
    elif "Energy" in industry or "Critical Infrastructure" in industry:
        reg_name = "los marcos normativos de protección de infraestructuras críticas (v.g. Directiva NIS2 o leyes de seguridad nacional)"
        reg_fine_limit = f"10.000.000 {currency}"
    elif "Telecommunications" in industry or "Media" in industry:
        reg_name = "los marcos regulatorios sectoriales de Telecomunicaciones, Media y soberanía de datos"
        reg_fine_limit = f"5.000.000 {currency}"
    elif "Healthcare" in industry:
        reg_name = "las regulaciones de protección de datos de salud y privacidad (v.g. HIPAA o marcos locales equivalentes)"
        reg_fine_limit = f"5.000.000 {currency}"
    else:
        reg_name = "los marcos generales de protección de datos y privacidad (v.g. RGPD o legislación sectorial estándar)"
        reg_fine_limit = f"2.000.000 {currency}"

    # Section 1: Por qué cuantificamos
    add_appendix_subheading(doc, "Limitaciones del Análisis Cualitativo frente a Open FAIR™", primary_color_rgb=p_color_rgb)
    p_why = (
        "Las metodologías tradicionales de evaluación de riesgos en TI, fundamentadas en análisis cualitativos de "
        "impacto y probabilidad (como las matrices de rango alto/medio/bajo), constituyen un valioso punto de partida para "
        "identificar y clasificar de forma temprana las superficies de vulnerabilidad de una organización. No obstante, para "
        "facilitar la toma de decisiones presupuestarias y justificar la rentabilidad de las inversiones tecnológicas (ROI), "
        "es necesario complementar estos marcos de referencia con un enfoque cuantitativo avanzado. Este diagnóstico "
        "adopta de forma complementaria la metodología estándar **Open FAIR™ (Factor Analysis of Information Risk)** "
        "(reconocida por *The Open Group* e incorporada en marcos normativos como ISO/IEC 27005), aportando una metodología "
        "rigurosa para modelar e identificar la exposición financiera real de la plataforma ante eventos de riesgo."
    )
    add_body_paragraph(doc, p_why, text_color_rgb=text_color_rgb)

    # Section 2: Modelo de Calibración de Doble Capa
    add_appendix_subheading(doc, "El Modelo de Calibración Actuarial de Doble Capa", primary_color_rgb=p_color_rgb)
    p_layer_intro = (
        "Con el fin de comprender de forma intuitiva cómo una deficiencia técnica se propaga hasta impactar en el "
        "balance de la compañía, resulta de gran utilidad seguir paso a paso la cronología de un único evento de amenaza. "
        "A este recorrido lo denominamos 'La Biografía del Incidente'. Imaginemos, a modo de ejemplo ilustrativo, "
        f"un escenario de crisis en la torre de {tower_name}: un fallo operativo severo originado por una "
        "debilidad técnica previamente diagnosticada en esta auditoría. La propagación financiera "
        "de este incidente se rige por un modelo actuarial de doble capa:"
    )
    add_body_paragraph(doc, p_layer_intro, text_color_rgb=text_color_rgb)

    # Local inline Markdown parser to cleanly render bold (**) and italics (_) inside Appendix D bullet points,
    # completely eliminating raw asterisks and styling math variables beautifully.
    # Note: Function body is defined early in compile_docx to avoid scope conflicts.

    add_markdown_bullet_local(
        "Capa 1: Modelado de Vulnerabilidad (Garantía FAIR-CAM™) - Calibración Estocástica de Eficacia Defensiva: El incidente se inicia "
        "con la materialización de un evento de amenaza (v.g. un fallo operativo o desalineación en la capa de virtualización). En este "
        "instante, el evento choca contra las barreras de control de la organización. La probabilidad de que la amenaza supere estas "
        "salvaguardas y cause una pérdida real se define técnicamente como Vulnerabilidad (_VULN_). Nuestro motor aplica el estándar "
        "**FAIR-CAM™ (Control Analytics Model)** para calibrar esta probabilidad en función de la madurez real auditada en el Capítulo 3. "
        "Si la capacidad se sitúa en un nivel reactivo o inmaduro (Nivel 1 o 2), las barreras de control exhiben fallas estructurales severas, "
        "permitiendo el filtrado de la amenaza y detonando de inmediato **Pérdidas Primarias** (costes de respuesta de emergencia, "
        "horas de ingeniería extraordinaria de restauración e interrupción directa del negocio), cuyo coste de severidad "
        "es modelado estocásticamente mediante curvas continuas lognormales. Con el objetivo de distinguir matemáticamente las vulnerabilidades de riesgo estructural frente a ineficiencias rutinarias, "
        "el modelo aplica una **segregación tipológica**: si la deficiencia es de fricción operativa pura (ej. uso de hojas de cálculo o procesos ITSM lentos), "
        "el impacto se acota a un límite estricto de OPEX, garantizando proyecciones financieras realistas y contenidas.",
        space_after=4
    )

    add_markdown_bullet_local(
        f"Capa 2: Exposición Secundaria y Diligencia Debida (Garantía FAIR-MAM™) - Propagación Condicional de la Exposición Reguladora: "
        f"Una vez materializada la pérdida primaria, se activa de forma secuencial una segunda capa de exposición reguladora y "
        f"contractual basada en la demostración de la 'diligencia debida' (compliance). Utilizando la metodología **FAIR-MAM™ (Materiality Analytics Model)**, "
        f"el motor simula el desencadenamiento de **Pérdidas Secundarias** catastróficas (sanciones bajo {reg_name} de hasta "
        f"{reg_fine_limit} o reclamaciones por incumplimiento severo de SLAs). Esta propagación no utiliza saltos binarios arbitrarios, "
        f"sino que se modela mediante una **curva de transición logística continua** anclada en el nivel de madurez. A medida que la "
        f"madurez técnica decae por debajo del **Nivel 3 (Definido - score < 2,60)**, se asume una omisión estructural de diligencia, "
        f"disparando la probabilidad estocástica de sanción de forma asintótica hacia un techo del **15%**. Por el contrario, a medida que la capacidad "
        f"consolida el Nivel 3 o superior, la organización puede probar documentalmente su debida diligencia ante el regulador, "
        f"desplomando suavemente dicha probabilidad penalizadora hacia un suelo residual del **2%** de manera justificada.",
        space_after=12
    )

    # Section 3: El Núcleo de Simulación Actuarial
    add_appendix_subheading(doc, "El Núcleo de Simulación Actuarial", primary_color_rgb=p_color_rgb)
    p_mc_intro = (
        "Más allá de la lógica conceptual, el verdadero valor diferencial de este diagnóstico reside en su arquitectura matemática. "
        "El motor de riesgo no emplea promedios estáticos, sino que ejecuta una **Simulación de Monte Carlo de 10.000 iteraciones** "
        "impulsada por un **Proceso de Riesgo Colectivo Compuesto de Dos Etapas**. Este núcleo de cálculo, diseñado bajo los "
        "estándares de la banca de inversión (Basilea III), modela la complejidad real del ciberespacio:"
    )
    add_body_paragraph(doc, p_mc_intro, text_color_rgb=text_color_rgb)

    add_markdown_bullet_local(
        "La Elicitación de Expertos (Consenso Adversarial Multi-Agente): Previo a la simulación matemática, el motor aplica un proceso de actualización bayesiana para adaptar las curvas de probabilidad teóricas a la realidad operativa de la organización. Mediante un panel automatizado de Inteligencia Artificial que debate desde perspectivas adversariales (viabilidad operativa vs. riesgo catastrófico), se deducen atenuantes topológicos (como el aislamiento de redes OT) y se separa la fricción técnica ordinaria del riesgo regulatorio. Este proceso simula de forma auditable la Elicitación de Expertos en la Materia (SME Elicitation) requerida por el estándar FAIR™, generando multiplicadores de descuento (Priors Bayesianos) que calibran el modelo y evitan el doble conteo de riesgos antes de inyectarlos en el núcleo estocástico.",
        space_after=4
    )

    add_markdown_bullet_local(
        "La Frecuencia de Amenazas - El Contagio (Distribución Binomial Negativa): En lugar de asumir una frecuencia fija o eventos aleatorios independientes (Poisson), "
        "el motor simula el número de amenazas anuales (_n_) mediante una **Distribución Binomial Negativa**. Este modelo captura la sobre-dispersión empírica de "
        "los ciberataques, donde un intento fallido suele preceder a una oleada concentrada de incidentes (clustering). "
        "La tasa media (_λ_) no es estática; se muestrea de una distribución de incertidumbre calibrada mediante **Elicitación de Expertos (Expert Elicitation)**, "
        "anclada en heurísticas de inteligencia de amenazas sectoriales y taxonomías de vulnerabilidad conocidas.",
        space_after=4
    )

    add_markdown_bullet_local(
        "El Pararrayos de Control - El Éxito o Fallo (Distribución Binomial): Para cada una de las amenazas simuladas (_n_), el ordenador "
        "simula si nuestras defensas reales desvían el impacto o fallan. El número final de pérdidas reales (_k_) sigue una distribución "
        "binomial (expresada matemáticamente como _k ~ Binomial(n, VULN)_). La vulnerabilidad (_VULN_) se correlaciona con la madurez "
        "técnica del Capítulo 3 mediante una **función de decadencia logística**, reflejando matemáticamente el desplome exponencial de eficacia defensiva cuando los controles caen por debajo de los estándares definidos.",
        space_after=4
    )

    add_markdown_bullet_local(
        f"La Severidad de Pérdidas - El Coste (Distribución Lognormal de Colas Pesadas): Para modelar el coste de reparación técnica y las posibles "
        f"multas secundarias, el motor emplea una **Distribución Lognormal**. Ante la ausencia de series temporales empíricas masivas del cliente, esta curva actúa como una "
        f"**Aproximación Conservadora de Valores Extremos (EVT)** para modelar impactos financieros con colas pesadas. Los parámetros de la curva (_μ_, _σ_) se ajustan estocásticamente. "
        f"Para evitar la inestabilidad estadística de simulaciones infinitas, el modelo realiza un truncamiento matemático (soft truncation) en el límite legal correspondiente "
        f"(hasta {reg_fine_limit}), forzando la convergencia estable de la Expectativa de Pérdida Anualizada (ALE) bajo el Teorema del Límite Central.",
        space_after=4
    )

    add_markdown_bullet_local(
        "Correlación Multivariante (Cópula Gaussiana Direccional): En el mundo real, un daño técnico severo eleva de forma casi determinista la probabilidad de sufrir "
        "una sanción regulatoria grave. Para evitar infravalorar eventos catastróficos, el motor no suma costes de forma independiente. Utiliza el Teorema de Sklar "
        "y una **Cópula Gaussiana** para inyectar una Dependencia de Cola asimétrica. Esto vincula causalmente las matrices de pérdida primaria y secundaria, "
        "garantizando que la distribución financiera final refleje el riesgo estructural compuesto con precisión absoluta.",
        space_after=12
    )

    # Section 4: Métricas Decisionales
    add_appendix_subheading(doc, "Definición de Métricas Decisionales de Exposición Financiera", primary_color_rgb=p_color_rgb)
    p_metrics_intro = (
        "Al integrar y ordenar los resultados de las 10.000 iteraciones de simulación virtual, el motor genera la distribución "
        "acumulada de pérdidas de la plataforma. De esta distribución se derivan matemáticamente las tres métricas decisionales "
        "que permiten al Consejo justificar las inversiones de mitigación:"
    )
    add_body_paragraph(doc, p_metrics_intro, text_color_rgb=text_color_rgb)

    p_m1 = add_markdown_bullet_local(
        "Pérdida Anualizada (ALE - Annual Loss Exposure): Representa la media aritmética de todos los escenarios de pérdida anualizada agregados. "
        "Es el impacto económico promedio latente que la organización experimenta cada año si decide mantener el statu quo (coste de inacción).",
        space_after=4
    )

    p_m2 = add_markdown_bullet_local(
        "Déficit Esperado Condicional (CVaR / Expected Shortfall): Representa el promedio matemático del 2.5% de los peores escenarios de la distribución de pérdidas (Expected Shortfall al 97.5%). "
        "Se define como una métrica de riesgo matemáticamente coherente (coherent risk measure) y de referencia bajo los más estrictos estándares internacionales de gestión financiera (como la Fundamental Review of the Trading Book - FRTB de Basilea III), "
        "capturando con rigor la verdadera magnitud de las pérdidas extremas en la cola de la distribución sin sufrir el efecto de dilución de eventos de baja frecuencia. Al agregar los valores, ilustramos el peor caso estructural absoluto "
        "donde las mayores vulnerabilidades convergen simultáneamente, proporcionando el requerimiento de capital de resiliencia necesario para proteger el Valor de la Empresa (Enterprise Value).",
        space_after=4
    )

    p_m3 = add_markdown_bullet_local(
        f"Rango Probabilístico de Pérdidas: Muestra la volatilidad de la exposición del riesgo, ilustrando desde un año virtual benigno (Mín) hasta "
        f"un año catastrófico (Máx) provocado por la ineficiencia acumulada de múltiples fallos y sanciones regulatorias de {reg_name} concurrentes.",
        space_after=12
    )

    p_convergence = (
        "*(Nota de Estabilidad y Exposición de Riesgo Bruto: El volumen de 10.000 iteraciones simuladas garantiza la plena convergencia "
        "y estabilidad matemática de los indicadores económicos bajo el Teorema del Límite Central, proporcionando un estimador de exposición "
        "financiero de alta precisión y máxima fidelidad estadística. Asimismo, todos los valores monetarios aquí expuestos (ALE y CVaR) representan "
        "el Riesgo Bruto Latente (Gross Exposure) antes de la aplicación de posibles mitigaciones de transferencia financiera (como franquicias o topes de pólizas de ciberseguro). "
        "Por consiguiente, deben interpretarse como indicadores de magnitud probabilística para la priorización ejecutiva de inversiones tecnológicas (Business Case), "
        "no como límites absolutos o provisiones directas de pasivos en el balance contable de la organización).*"
    )
    add_body_paragraph(doc, p_convergence, text_color_rgb=text_color_rgb)
    
        # Disable the `autofit` property to enforce a fixed table width of 6.5 inches.

    #
    # Assemble and render Appendix B: Registro de Custodia de Fuentes de Información
    #
    add_appendix_heading(doc, vocab["appendix_c_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_c_intro"], text_color_rgb=text_color_rgb)

    source_table = doc.add_table(rows=1, cols=3)
    source_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    finalize_table(source_table)

    for i, h_txt in enumerate(vocab["appendix_c_headers"]):
        set_cell_text_custom(
            source_table.rows[0].cells[i],
            h_txt,
            bold=True,
            font_size=10,
            color_rgb=RGBColor(255, 255, 255),
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(source_table.rows[0].cells[i], p_color_hex)

    # Set initial column widths for header cells in centimeters
    source_table.rows[0].cells[0].width = Cm(1.5)
    source_table.rows[0].cells[1].width = Cm(4.5)
    source_table.rows[0].cells[2].width = Cm(10.5)

    # Data Sanitization: Prevent generation of invalid source file paths in the bibliography, per requirement 4.
    src_data = []
    source_docs = b_data.get("source_documents") if payload_path.exists() else None

    if source_docs:
        # If source file paths are provided in the payload, use them directly, overriding any dynamic generation logic.
        for doc_item in source_docs:
            src_data.append(
                (
                    doc_item.get("code", "[Doc]"),
                    doc_item.get("name", "Documento"),
                    doc_item.get("desc", "Documento bajo custodia de auditoría."),
                )
            )
    else:
        # Dynamically generate a context-aware bibliography based on the specified technology stack to avoid invalid source file references.
        client_name_slug = client_name.lower().replace(" ", "_")
        src_data = [
            (
                "[Cuestionario de Autoevaluación]",
                f"preguntas_{client_name_slug}.txt",
                f"Cuestionario estructurado de autoevaluación técnica de la torre de {tower_name}, recopilando "
                f"las respuestas oficiales, notas y telemetrías declaradas de buena fe por el equipo de ingeniería de {client_name}.",
            ),
            (
                "[Dossier de Contexto]",
                f"contexto_{client_name_slug}.docx",
                f"Dossier estratégico de contexto de arquitectura de {client_name} que define la volumetría del "
                f"patrimonio, distribución de centros de datos, dependencias y criticidad operativa general.",
            ),
            (
                "[Capa de Inteligencia de la Plataforma]",
                "client_intelligence.json",
                f"Módulo de ingesta y análisis semántico asistido por IA de la plataforma que recopila de forma automatizada "
                f"las regulaciones de cumplimiento (NIS2, ENS Categoría Alta), reclamos corporativos y baselines del sector (ITIC) "
                f"para calibrar y enriquecer los hallazgos técnicos con métricas cuantitativas de riesgo de negocio.",
            ),
            (
                "[ITIC-DOWNTIME]",
                "ITIC Global Server Hardware Downtime Report",
                "Estudio de referencia mundial y métrica estadística industrial que barema el coste promedio por hora de "
                "indisponibilidad de infraestructura core en grandes corporaciones y servicios críticos, utilizado como baseline de calibración de pérdidas primarias.",
            ),
            (
                "[CISA-KEV]",
                "CISA Known Exploited Vulnerabilities Catalog",
                "Catálogo internacional de vulnerabilidades explotadas activamente por agentes de amenaza, mantenido por la Cybersecurity "
                "and Infrastructure Security Agency (CISA) y utilizado como baseline para calibrar la Frecuencia de Eventos de Amenaza (TEF).",
            ),
            (
                "[DIRECTIVA-NIS2]",
                "Directiva (UE) 2022/2555 (NIS2)",
                "Directiva del Parlamento Europeo y del Consejo relativa a medidas destinadas a garantizar un elevado nivel común de ciberseguridad "
                "en toda la Unión, utilizada para calibrar el límite máximo legal de sanciones administrativas por negligencia (pérdidas secundarias).",
            ),
            (
                "[ENS-ALTA]",
                "Esquema Nacional de Seguridad (ENS) de España - Real Decreto 311/2022",
                "Marco regulatorio de seguridad obligatorio para operadores del sector público e infraestructuras críticas nacionales, "
                "utilizado como baseline normativo para modelar los criterios y exigencias de conformidad en la Categoría Alta.",
            ),
            (
                "[DAMA-DMBOK]",
                "DAMA Data Management Body of Knowledge (DAMA-DMBOK v2)",
                "Marco metodológico estándar internacional para la evaluación de madurez del gobierno y gestión de datos corporativos, "
                "utilizado para modelar y auditar la consistencia del pilar de gobierno de datos de la plataforma.",
            ),
            (
                "[GOOGLE-DORA]",
                "Google DevOps Research and Assessment (DORA) Framework",
                "Estándar industrial internacional utilizado para evaluar la madurez de la automatización, entrega continua, "
                "y fiabilidad operacional (SRE) en ecosistemas modernos de desarrollo e infraestructura híbrida.",
            )
        ]

    for s_idx, row_vals in enumerate(src_data):
        row = source_table.add_row()
        set_cell_text_custom(
            row.cells[0],
            row_vals[0],
            bold=True,
            font_size=10,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text_custom(
            row.cells[1], row_vals[1], font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER
        )
        set_cell_text_custom(row.cells[2], row_vals[2], font_size=10)

        row.cells[0].width = Cm(1.5)
        row.cells[1].width = Cm(4.5)
        row.cells[2].width = Cm(10.5)

        if s_idx % 2 == 1:
            shade_cell(row.cells[0], alt_row_hex)
            shade_cell(row.cells[1], alt_row_hex)
            shade_cell(row.cells[2], alt_row_hex)

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix C: Glosario de Términos y Abreviaturas
    #
    add_appendix_heading(doc, vocab["appendix_a_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(doc, vocab["appendix_a_intro"], text_color_rgb=text_color_rgb)

    import re

    from assessment_engine.infrastructure.config_loader import (
        load_abbreviations_glossary,
    )

    try:
        full_glossary = load_abbreviations_glossary()

        # Merge case-specific client abbreviations if they exist in the case directory
        client_glossary_path = tower_dir_obj / "client_abbreviations_glossary.json"
        if client_glossary_path.exists():
            try:
                with open(client_glossary_path, "r", encoding="utf-8-sig") as cgf:
                    client_glossary = json.load(cgf)
                    for lang, terms in client_glossary.items():
                        if lang in full_glossary:
                            full_glossary[lang].update(terms)
                        else:
                            full_glossary[lang] = terms
            except json.JSONDecodeError as ex:
                print(
                    f"⚠️  [Glosario] Error de sintaxis JSON en {client_glossary_path}: {ex}"
                )
            except Exception as ex:
                print(f"⚠️  [Glosario] No se pudo leer {client_glossary_path}: {ex}")

        # Get localized glossary dictionary
        glossary = full_glossary.get(doc_lang, full_glossary.get("es", {}))

        # Gather all text accumulated in paragraphs and tables so far (now fully includes Appendix A and B!)
        all_text_elements = []
        for p in doc.paragraphs:
            if p.text:
                all_text_elements.append(p.text)
        for t in doc.tables:
            for row in t.rows:
                for cell in row.cells:
                    if cell.text:
                        all_text_elements.append(cell.text)
        text_corpus = " ".join(all_text_elements)

        # Filter glossary keys that are actually present in the text corpus
        used_glossary = {}
        for term, desc in glossary.items():
            escaped_term = re.escape(term)
            pattern = rf"(?<![a-zA-Z0-9]){escaped_term}(?![a-zA-Z0-9])"
            if re.search(pattern, text_corpus):
                used_glossary[term] = desc

        # Quality Gate: First-Use Rule Verification
        for term, desc in used_glossary.items():
            # SOTA Bilingual Check: Extract both English form (before parenthesis) and Spanish translation (inside parenthesis)
            # to prevent false positive warnings when compiling documents in different languages
            parts = []
            if "(" in desc:
                main_part = desc.split("(")[0].strip()
                parts.append(main_part)
                sub_part = desc.split("(")[1].split(")")[0].strip()
                parts.append(sub_part)
            else:
                parts.append(desc)

            # Verification passes if either the English or the Spanish full form is located in the text
            if not any(p.lower() in text_corpus.lower() for p in parts if len(p) > 2):
                print(
                    f"⚠️  [Glosario] Calidad: La sigla '{term}' se utiliza pero su definición extendida ('{parts[0]}') no aparece en el informe. Se recomienda expandirla en su primer uso."
                )

        if used_glossary:
            gloss_table = doc.add_table(rows=1, cols=2)
            gloss_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            finalize_table(gloss_table)

            for i, h_txt in enumerate(vocab["appendix_a_headers"]):
                set_cell_text_custom(
                    gloss_table.rows[0].cells[i],
                    h_txt,
                    bold=True,
                    font_size=10,
                    color_rgb=RGBColor(255, 255, 255),
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )
                shade_cell(gloss_table.rows[0].cells[i], p_color_hex)

            #
            gloss_table.rows[0].cells[0].width = Inches(1.5)
            gloss_table.rows[0].cells[1].width = Inches(5.0)  #

            for g_idx, (term, desc) in enumerate(sorted(used_glossary.items())):
                row = gloss_table.add_row()
                set_cell_text_custom(row.cells[0], term, bold=True, font_size=10)
                set_cell_text_custom(row.cells[1], desc, font_size=10)

                #
                row.cells[0].width = Inches(1.5)
                row.cells[1].width = Inches(5.0)

                if g_idx % 2 == 1:
                    shade_cell(row.cells[0], alt_row_hex)
                    shade_cell(row.cells[1], alt_row_hex)
    except Exception as ex:
        print(f"⚠️  [Glosario] Error inesperado en el apéndice de abreviaturas: {ex}")

    add_spacer(doc, 12)

    #
    # Assemble and render Appendix D: Cláusula de Limitación de Responsabilidad
    # Always use the clean, verified vocabulary fallback disclaimers to ensure maximum compliance.
    #
    add_appendix_heading(doc, vocab["appendix_b_title"], primary_color_rgb=p_color_rgb)
    add_body_paragraph(
        doc, vocab.get("disclaimer_text_1", ""), text_color_rgb=text_color_rgb
    )
    add_body_paragraph(
        doc, vocab.get("disclaimer_text_2", ""), text_color_rgb=text_color_rgb
    )
    add_body_paragraph(
        doc, vocab.get("disclaimer_text_3", ""), text_color_rgb=text_color_rgb
    )
    add_body_paragraph(
        doc, vocab.get("disclaimer_text_4", ""), text_color_rgb=text_color_rgb
    )
    add_body_paragraph(
        doc, vocab.get("disclaimer_text_5", ""), text_color_rgb=text_color_rgb
    )

    add_spacer(doc, 20)

    # Insert a field code to instruct the host application to update the Table of Contents upon opening.
    set_update_fields(doc)

    #
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(
        f"🎉 ¡Anexo Técnico AS-IS COMPILADO modularmente con éxito en: {output_path}!"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(
            "Uso: python compile_asis_docx_from_modules.py <tower_dir> <output_doc.docx>"
        )
        sys.exit(1)
    compile_docx(sys.argv[1], sys.argv[2])
