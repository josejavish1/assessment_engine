import logging

logger = logging.getLogger(__name__)
import json
import re
import sys
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, ns, parse_xml
from docx.shared import Inches, Pt, RGBColor

"""
Module render_global_report_from_template.py.
Contains core orchestration and rendering logic for Assessment Engine pipeline.
"""

from assessment_engine.domain.schemas.global_report import (
    BoardMemoDraft,
    BurningPlatformItem,
    CrossTowerNexusDraft,
    ExecutionRoadmapDraft,
    ExecutiveCalloutItem,
    ExecutiveDecisionsDraft,
    ExecutiveSummaryDraft,
    GlobalReportPayload,
    TargetVisionDraft,
    TowerBottomLineItem,
)
from assessment_engine.infrastructure.docx_render_utils import (
    add_body_paragraph,
    add_heading_paragraph,
    autofit_table_to_contents,
    clear_paragraph,
    finalize_table,
    set_cell_text,
    shade_cell,
)
from assessment_engine.infrastructure.global_maturity_policy import (
    safe_float,
    status_color_for_score,
)
from assessment_engine.infrastructure.localization import get_localized_list, t


def load_json(path) -> Any:
    """Read and deserialize a JSON file from a given path object."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clean_t_codes(text) -> Any:
    """Sanitize a string by removing specific internal annotation patterns.

    Removes several patterns from an input string: T-codes within parentheses
    (e.g., `(T1...)`), standalone T-codes that form a whole word (e.g., `T12`),
    and internal reference tags (e.g., `[[REF:...]]` or `[REF:...]`). The
    resulting string has leading and trailing whitespace stripped.

    If the input is not a string, it is returned without modification.

    Args:
        text (Any): The input value to be sanitized.

    Returns:
        Any: A sanitized string with patterns removed, or the original input value
            if it was not a string.
    """
    if not isinstance(text, str):
        return text
    text = re.sub(r"\(T\d{1,2}[^\)]*\)", "", text)
    text = re.sub(r"\bT\d{1,2}\b", "", text)
    # Strips internal reference tags (e.g., `[[REF:...]]`, `[REF:...]`) from the text content to sanitize it for final presentation.
    text = re.sub(r"\[\[?REF:[^\]]*\]\]?", "", text)
    return text.strip()


def sanitize_client_name(text, client_name, doc_lang: str) -> Any:
    """Ensures clean vocabulary and formatting for client-facing narratives."""
    if not isinstance(text, str):
        return text

    from assessment_engine.infrastructure.localization import (
        apply_vocabulary_substitutions,
    )

    return apply_vocabulary_substitutions(text, locale=doc_lang)


def clear_document_body(doc) -> Any:
    """Removes all content from a document's body while preserving section properties.

    This function operates on the underlying lxml element of the document body. It
    iterates through all child elements and removes them, with the sole exception
    of the `w:sectPr` (section properties) element. This approach allows for
    clearing all visible content, such as paragraphs and tables, while retaining
    critical page formatting like margins, orientation, and paper size.

    The modification is performed in-place.

    Args:
        doc (docx.document.Document): The python-docx Document object to be cleared.

    Returns:
        None.

    Raises:
        AttributeError: If the `doc` object does not conform to the expected
            internal structure of the `python-docx` library, specifically
            lacking a `_body._element` attribute path.
    """
    body = doc._body._element
    for child in list(body):
        if (
            child.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr"
        ):
            body.remove(child)


def add_spacer(doc, points=12) -> Any:
    """Add a vertical spacer of a specified point height to a document."""
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(points)


def add_smart_bullet_list(container, items, color_rgb=None, bold_prefix=True) -> Any:
    """Renders a list of strings as a formatted bulleted list within a python-docx container.

    This function iterates through each string in the provided list, adding it as a
    new paragraph to the container. It first attempts to apply the "List Bullet"
    style from the document template. If this style is not found (resulting in a
    KeyError), it falls back to a manually formatted list entry by prepending a
    "•" character and setting paragraph indentation programmatically.

    The function also supports prefix-based formatting. If an item string contains
    a ": " or " - " separator, the text preceding the separator can be
    conditionally bolded. If no separator is present, the entire item is treated
    as the prefix for formatting purposes.

    Args:
        container (Any): A python-docx object that supports the `add_paragraph`
            method, such as a `Document` or `_Cell` object.
        items (Union[str, List[str]]): A single string or a list of strings to be
            rendered as bullet points. A single string is treated as a single-item list.
        color_rgb (Optional[docx.shared.RGBColor]): The `RGBColor` to apply to the
            text. If None, the default text color of the container is used.
        bold_prefix (bool): If True, bolds the text preceding a separator (": "
            or " - ") or the entire line if no separator is found. Defaults to
            True.

    Returns:
        None: The container object is modified in-place.
    """
    # Ensures robustness by wrapping a string input in a list if a list is expected. This prevents unintended character-wise iteration over the string.
    if isinstance(items, str):
        items = [items]
    if not items:
        return

    for item in items:
        p = container.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p.style = "List Bullet"
        except KeyError:
            # Implements a fallback mechanism to a default style if the specified style name does not exist in the document template, preventing rendering failures.
            p.paragraph_format.left_indent = Pt(20)
            p.paragraph_format.first_line_indent = Pt(-15)
            b = p.add_run("• ")
            b.font.size = Pt(10.5)
            if color_rgb:
                b.font.color.rgb = color_rgb

        p.paragraph_format.space_after = Pt(6)
        text = clean_t_codes(str(item).strip())

        sep = ": " if ": " in text else (" - " if " - " in text else None)
        if sep:
            parts = text.split(sep, 1)
            r1 = p.add_run(parts[0] + sep)
            r1.bold = bold_prefix
            r1.font.size = Pt(10.5)
            r2 = p.add_run(parts[1])
            r2.font.size = Pt(10.5)
            if color_rgb:
                r1.font.color.rgb = color_rgb
                r2.font.color.rgb = color_rgb
        else:
            r = p.add_run(text)
            r.bold = bold_prefix
            r.font.size = Pt(10.5)
            if color_rgb:
                r.font.color.rgb = color_rgb


def render_cover(doc, payload: GlobalReportPayload, doc_lang: str) -> Any:
    """Renders a formatted cover page into a `docx.Document` object."""
    doc.add_paragraph().paragraph_format.space_after = Pt(60)
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = title_p.add_run(t("global_report_cover_title", locale=doc_lang))
    run.font.size = Pt(34)
    run.font.name = "Georgia"
    run.font.color.rgb = RGBColor(0, 114, 188)
    run.bold = False

    # Reduces the vertical spacing between the report title and client name paragraphs to achieve a more compact and visually integrated header block.
    add_spacer(doc, 30)

    client_p = doc.add_paragraph()
    client_run = client_p.add_run(payload.meta.client.upper())
    client_run.font.size = Pt(24)
    client_run.font.name = "Arial"
    client_run.bold = True

    # The vertical spacing for this paragraph block is substantially reduced to prevent its content from being pushed down the page, ensuring proper alignment.
    doc.add_paragraph().paragraph_format.space_after = Pt(100)

    version_p = doc.add_paragraph()
    v_text = f"Fecha: {payload.meta.date}\nReferencia: {payload.meta.version}"
    version_run = version_p.add_run(v_text)
    version_run.font.size = Pt(14)
    version_run.font.name = "Arial"
    version_run.font.color.rgb = RGBColor(127, 127, 127)

    # A 150-point vertical spacer is applied to anchor the legal disclaimer to the bottom margin of the final page, preventing premature page breaks and ensuring consistent document layout.
    add_spacer(doc, 150)

    disclaimer_p1 = doc.add_paragraph()
    disclaimer_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p1.paragraph_format.space_after = Pt(
        2
    )  # Sets a minimum paragraph spacing for the legal disclaimer block to ensure readability and compliance with formatting standards.
    from assessment_engine.infrastructure.config_loader import (
        get_consultant_company_name,
        get_localized_disclaimer,
    )

    company = get_consultant_company_name()
    disclaimer_raw = get_localized_disclaimer(doc_lang)

    disclaimer_p1 = doc.add_paragraph()
    disclaimer_p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p1.paragraph_format.space_after = Pt(2)
    disclaimer_title_run = disclaimer_p1.add_run(t("legal_notice_confidentiality", locale=doc_lang) + " ")
    disclaimer_title_run.font.size = Pt(8)
    disclaimer_title_run.font.name = "Arial"
    disclaimer_title_run.font.color.rgb = RGBColor(127, 127, 127)
    disclaimer_title_run.bold = True

    if disclaimer_raw:
        paragraphs = [p.strip() for p in disclaimer_raw.split("\n\n") if p.strip()]
        for idx, p_text in enumerate(paragraphs):
            p_text_fmt = (
                p_text.format(company_name=company)
                if "{company_name}" in p_text
                else p_text
            )
            if idx == 0:
                r = disclaimer_p1.add_run(p_text_fmt)
            else:
                p_next = doc.add_paragraph()
                p_next.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p_next.paragraph_format.space_after = Pt(0) if idx == len(paragraphs) - 1 else Pt(2)
                r = p_next.add_run(p_text_fmt)
            r.font.size = Pt(8)
            r.font.name = "Arial"
            r.font.color.rgb = RGBColor(127, 127, 127)
    else:
        p1_text = t("global_disclaimer_p1", locale=doc_lang, company=company)
        r1 = disclaimer_p1.add_run(p1_text)
        r1.font.size = Pt(8)
        r1.font.name = "Arial"
        r1.font.color.rgb = RGBColor(127, 127, 127)

    doc.add_page_break()


def render_global_toc(doc: Document, doc_lang: str, scope: str | None = None) -> None:
    """Renders a formal Table of Contents (TOC) with pre-populated fallback entries."""
    from assessment_engine.adapters.compilers.asis_docx_primitives import (
        add_heading,
        add_toc,
        set_update_fields,
    )

    toc_title = t("toc_title", locale=doc_lang)
    add_heading(doc, toc_title, level=1, primary_color_rgb=(0, 114, 188))

    entries_map = {
        "asis": [
            (t("toc_asis_1", locale=doc_lang), "4"),
            (t("toc_asis_2", locale=doc_lang), "6"),
            (t("toc_asis_3", locale=doc_lang), "10"),
            (t("toc_asis_4", locale=doc_lang), "15"),
            (t("toc_asis_5", locale=doc_lang), "22"),
        ],
        "tobe": [
            (t("toc_tobe_1", locale=doc_lang), "4"),
            (t("toc_tobe_2", locale=doc_lang), "8"),
            (t("toc_tobe_3", locale=doc_lang), "14"),
            (t("toc_tobe_4", locale=doc_lang), "38"),
            (t("toc_tobe_5", locale=doc_lang), "45"),
        ],
        "todo": [
            (t("toc_todo_1", locale=doc_lang), "4"),
            (t("toc_todo_2", locale=doc_lang), "8"),
            (t("toc_todo_3", locale=doc_lang), "12"),
            (t("toc_todo_4", locale=doc_lang), "55"),
            (t("toc_todo_5", locale=doc_lang), "62"),
        ],
        "master": [
            (t("toc_master_1", locale=doc_lang), "3"),
            (t("toc_master_2", locale=doc_lang), "5"),
            (t("toc_master_3", locale=doc_lang), "8"),
            (t("toc_master_4", locale=doc_lang), "12"),
            (t("toc_master_5", locale=doc_lang), "16"),
            (t("toc_master_6", locale=doc_lang), "20"),
            (t("toc_master_7", locale=doc_lang), "24"),
        ],
    }

    selected_scope = scope if scope in entries_map else "master"
    entries = entries_map[selected_scope]

    for title_text, page_hint in entries:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.space_before = Pt(2)
        r_title = p.add_run(title_text)
        r_title.font.name = "Arial"
        r_title.font.size = Pt(10.5)
        r_title.font.color.rgb = RGBColor(46, 64, 77)

        r_dots = p.add_run(f"  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .  {page_hint}")
        r_dots.font.name = "Arial"
        r_dots.font.size = Pt(9.5)
        r_dots.font.color.rgb = RGBColor(127, 127, 127)

    add_toc(doc)
    set_update_fields(doc)
    doc.add_page_break()


def set_callout_border(cell: Any, color: str = "0072BC", size: int = 24) -> None:
    """Sets a prominent accent left border on a cell while clearing top, bottom, and right."""
    tcPr = cell._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="{size}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)


def render_executive_callout(
    doc: Any,
    callout: ExecutiveCalloutItem,
    doc_lang: str,
    client_name: str = "",
) -> Any:
    """Renders a shaded callout block with a thick left accent border in OpenXML."""
    color_styles = {
        "legal": {
            "border": "C00000",
            "fill": "FFF5F5",
            "title_color": RGBColor(192, 0, 0),
            "prefix_key": "callout_legal_prefix",
        },
        "factory": {
            "border": "0072BC",
            "fill": "F2F6FA",
            "title_color": RGBColor(0, 114, 188),
            "prefix_key": "callout_factory_prefix",
        },
        "decision": {
            "border": "7030A0",
            "fill": "F9F5FF",
            "title_color": RGBColor(112, 48, 160),
            "prefix_key": "callout_decision_prefix",
        },
        "strategic": {
            "border": "1F497D",
            "fill": "F2F4F7",
            "title_color": RGBColor(31, 73, 125),
            "prefix_key": "callout_strategic_prefix",
        },
    }
    style = color_styles.get(callout.callout_type, color_styles["strategic"])

    table = doc.add_table(rows=1, cols=1)
    finalize_table(table)
    cell = table.cell(0, 0)
    set_callout_border(cell, color=style["border"], size=36)
    shade_cell(cell, style["fill"])

    p_title = cell.paragraphs[0]
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(2)
    p_title.paragraph_format.left_indent = Pt(10)
    p_title.paragraph_format.right_indent = Pt(10)

    prefix_text = t(style["prefix_key"], locale=doc_lang)
    r_prefix = p_title.add_run(prefix_text)
    r_prefix.font.name = "Arial"
    r_prefix.font.size = Pt(10.0)
    r_prefix.bold = True
    r_prefix.font.color.rgb = style["title_color"]

    r_title = p_title.add_run(
        sanitize_client_name(clean_t_codes(callout.title), client_name, doc_lang=doc_lang)
    )
    r_title.bold = True
    r_title.font.name = "Arial"
    r_title.font.size = Pt(10.5)
    r_title.font.color.rgb = style["title_color"]

    p_msg = cell.add_paragraph()
    p_msg.paragraph_format.space_before = Pt(2)
    p_msg.paragraph_format.space_after = Pt(4)
    p_msg.paragraph_format.left_indent = Pt(10)
    p_msg.paragraph_format.right_indent = Pt(10)

    r_msg = p_msg.add_run(
        sanitize_client_name(clean_t_codes(callout.message), client_name, doc_lang=doc_lang)
    )
    r_msg.font.name = "Arial"
    r_msg.font.size = Pt(9.5)
    r_msg.font.color.rgb = RGBColor(46, 64, 77)

    if callout.key_metric:
        p_metric = cell.add_paragraph()
        p_metric.paragraph_format.space_before = Pt(0)
        p_metric.paragraph_format.space_after = Pt(6)
        p_metric.paragraph_format.left_indent = Pt(10)
        p_metric.paragraph_format.right_indent = Pt(10)
        r_lbl = p_metric.add_run(t("key_metric_label", locale=doc_lang) + " ")
        r_lbl.bold = True
        r_lbl.font.size = Pt(9.0)
        r_lbl.font.color.rgb = style["title_color"]
        r_met = p_metric.add_run(callout.key_metric)
        r_met.bold = True
        r_met.font.size = Pt(9.0)
        r_met.font.color.rgb = RGBColor(46, 64, 77)

    autofit_table_to_contents(table)
    add_spacer(doc, 10)


def render_board_memo(
    doc: Any,
    board_memo: BoardMemoDraft,
    doc_lang: str,
    client_name: str = "",
) -> Any:
    """Renders a self-contained 1-page Board Memo table for Executive Committee / Board."""
    from assessment_engine.infrastructure.localization import t

    BASE_TEXT_COLOR = RGBColor(46, 64, 77)
    add_heading_paragraph(doc, t("board_memo_title", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        sanitize_client_name(board_memo.summary, client_name, doc_lang=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )

    table = doc.add_table(rows=1, cols=4)
    finalize_table(table)
    headers = get_localized_list("board_memo_table_headers", locale=doc_lang)
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            font_size=10.0,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)

    color_map = {"E06666": "F4CCCC", "FFD966": "FFF2CC", "93C47D": "D9EAD3"}

    for item in board_memo.items:
        row = table.add_row()
        cell_0 = row.cells[0]
        score_lbl = t("lbl_score_prefix", locale=doc_lang)
        set_cell_text(
            cell_0,
            f"{item.domain}\n{score_lbl} {item.score} ({item.band})",
            bold=True,
            font_size=9.5,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )
        fill_color = color_map.get(item.status_color.upper(), "F4CCCC")
        shade_cell(cell_0, fill_color)

        cell_1 = row.cells[1]
        set_cell_text(
            cell_1,
            item.fair_exposure_3y,
            font_size=9.5,
            bold=True,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )

        cell_2 = row.cells[2]
        set_cell_text(
            cell_2,
            sanitize_client_name(clean_t_codes(item.critical_decision), client_name, doc_lang=doc_lang),
            font_size=9.5,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )

        cell_3 = row.cells[3]
        set_cell_text(
            cell_3,
            item.budget_estimate,
            font_size=9.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )

        for cell in (cell_1, cell_2, cell_3):
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR

    autofit_table_to_contents(table)
    add_spacer(doc, 10)

    fin_strat = getattr(board_memo, "financial_stratification", None)
    if fin_strat and isinstance(fin_strat, dict):
        add_spacer(doc, 14)
        add_heading_paragraph(
            doc,
            fin_strat.get("title", t("financial_stratification_title", locale=doc_lang)),
            level=2,
        )

        strat_table = doc.add_table(rows=1, cols=3)
        finalize_table(strat_table)

        headers_strat = [
            t("strat_header_layer", locale=doc_lang),
            t("strat_header_amount", locale=doc_lang),
            t("strat_header_nature", locale=doc_lang),
        ]
        for i, h in enumerate(headers_strat):
            set_cell_text(
                strat_table.rows[0].cells[i],
                h,
                bold=True,
                font_size=9.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(strat_table.rows[0].cells[i], "0072BC")
            for r in strat_table.rows[0].cells[i].paragraphs[0].runs:
                r.font.color.rgb = RGBColor(255, 255, 255)

        layers_keys = [
            ("layer_1_cash_inefficiency", "F4CCCC"),
            ("layer_2_operational_friction", "FFF2CC"),
            ("layer_3_actuarial_tail_risk", "F2F2F2"),
        ]

        for l_key, shade_col in layers_keys:
            layer_data = fin_strat.get(l_key, {})
            if layer_data:
                s_row = strat_table.add_row()
                set_cell_text(
                    s_row.cells[0],
                    layer_data.get("title", ""),
                    bold=True,
                    font_size=9.0,
                    align=WD_ALIGN_PARAGRAPH.LEFT,
                )
                shade_cell(s_row.cells[0], shade_col)

                set_cell_text(
                    s_row.cells[1],
                    layer_data.get("amount_display", "-"),
                    bold=True,
                    font_size=9.5,
                    align=WD_ALIGN_PARAGRAPH.CENTER,
                )

                bullets_txt = " • ".join(layer_data.get("bullets", []))
                set_cell_text(
                    s_row.cells[2],
                    bullets_txt,
                    font_size=8.5,
                    align=WD_ALIGN_PARAGRAPH.LEFT,
                )

        autofit_table_to_contents(strat_table)
        add_spacer(doc, 8)

        roi_data = fin_strat.get("return_on_investment", {})
        if roi_data:
            p_roi = doc.add_paragraph()
            p_roi.paragraph_format.space_before = Pt(6)
            p_roi.paragraph_format.space_after = Pt(8)
            run_roi_lbl = p_roi.add_run(roi_data.get("title", t("roi_statement_label", locale=doc_lang)))
            run_roi_lbl.bold = True
            run_roi_lbl.font.size = Pt(9.5)
            run_roi_lbl.font.color.rgb = RGBColor(0, 114, 188)

            run_roi = p_roi.add_run(roi_data.get("body", ""))
            run_roi.font.size = Pt(9.5)
            run_roi.font.color.rgb = BASE_TEXT_COLOR

    add_spacer(doc, 10)
    doc.add_page_break()


def render_cross_tower_nexus(
    doc: Any,
    nexus: CrossTowerNexusDraft,
    doc_lang: str,
    client_name: str = "",
) -> Any:
    """Renders the Cross-Tower Nexus dependency matrix."""
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)
    add_heading_paragraph(
        doc, "4. Matriz de Interdependencias Cruzadas (Cross-Tower Nexus)", level=1
    )
    add_body_paragraph(
        doc,
        sanitize_client_name(nexus.description, client_name, doc_lang=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )

    table = doc.add_table(rows=1, cols=5)
    finalize_table(table)
    headers = [
        "Dominio Habilitador",
        "Dominio Impactado",
        "Tipo Dependencia",
        "Architectural Rationale",
        "Impacto si se Posterga",
    ]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            font_size=9.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)

    for dep in nexus.dependencies:
        row = table.add_row()
        set_cell_text(
            row.cells[0],
            clean_t_codes(dep.source_tower),
            bold=True,
            font_size=9.0,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )
        set_cell_text(
            row.cells[1],
            clean_t_codes(dep.target_tower),
            bold=True,
            font_size=9.0,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )
        set_cell_text(
            row.cells[2],
            dep.dependency_type,
            bold=True,
            font_size=9.0,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        if "Blocker" in dep.dependency_type or "Critical" in dep.dependency_type or "Bloqueante" in dep.dependency_type:
            shade_cell(row.cells[2], "F4CCCC")
        else:
            shade_cell(row.cells[2], "FFF2CC")

        set_cell_text(
            row.cells[3],
            sanitize_client_name(clean_t_codes(dep.architectural_rationale), client_name, doc_lang=doc_lang),
            font_size=9.0,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )
        set_cell_text(
            row.cells[4],
            sanitize_client_name(clean_t_codes(dep.delay_impact), client_name, doc_lang=doc_lang),
            font_size=9.0,
            align=WD_ALIGN_PARAGRAPH.LEFT,
        )

        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR

    autofit_table_to_contents(table)
    add_spacer(doc, 15)

def render_executive_summary(
    doc,
    data: ExecutiveSummaryDraft,
    heatmap: list | None = None,
    visuals: dict | None = None,
    client_dir: Any = None,
    doc_lang: str | None = None,
    client_name: str = "",
) -> None:
    """Renders the executive summary section into a `docx.document.Document` object.

    Constructs and populates the executive summary by sequentially adding several
    components to the document. This includes a main score and headline table, a
    prose narrative with bullet points, a table of key business impacts, and an
    optional radar chart image. The function calculates an average score from
    heatmap data and sanitizes text by replacing client name placeholders. The
    input `doc` object is modified in place.

    Args:
        doc (docx.document.Document): The `python-docx` document object to be
            modified.
        data (ExecutiveSummaryDraft): A data object containing the textual content
            for the summary, including the headline, narrative, and key business
            impacts.
        heatmap (list[dict]): A list of dictionaries, where each dictionary
            represents a finding. Each is expected to contain a 'score' key with a
            value convertible to a float for calculating the overall average score.
        visuals (dict[str, str]): A dictionary mapping visual identifiers to their
            filenames. This function uses the 'radar_chart' key to locate the
            image file.
        client_dir (pathlib.Path): The base directory for the client's report,
            used as the root for resolving paths to visual assets.
        client_name (str): The client's name, used to replace placeholders within
            the textual content. Defaults to an empty string if not provided.

    Returns:
        None
    """
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  #
    add_heading_paragraph(doc, t("global_ch1_exec_summary", locale=doc_lang), level=1)
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False

    # Configures table column widths to a 35% (2.1") and 65% (3.9") distribution. This ratio is optimized for content balance and readability on A4 paper.
    table.columns[0].width = Inches(2.1)
    table.columns[1].width = Inches(3.9)

    score_cell = table.rows[0].cells[0]
    score_cell.width = Inches(2.1)
    score_val = "N/A"
    if heatmap:
        try:
            score_val = str(
                round(
                    sum(float(t.get("score", 0)) for t in heatmap) / len(heatmap),
                    1,
                )
            )
        except (OSError, ValueError, KeyError, AttributeError) as ex:

            logger.debug(f"[Fallback] Handled exception: {ex}")

    # Applies specific styling to the score display: formats as '[X] / 5', sets a #0072BC background fill, and uses a 36pt white font.
    set_cell_text(
        score_cell,
        f"{score_val} / 5",
        bold=True,
        font_size=36,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(score_cell, "0072BC")
    for r in score_cell.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    desc_cell = table.rows[0].cells[1]
    desc_cell.width = Inches(3.9)
    desc_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    shade_cell(desc_cell, "F2F2F2")

    headline = sanitize_client_name(clean_t_codes(data.headline), client_name, doc_lang=doc_lang)

    # Applies bold formatting exclusively to the substring of the headline that precedes the first colon, creating a visual distinction for the primary label.
    clear_paragraph(desc_cell.paragraphs[0])
    p = desc_cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    if ":" in headline:
        parts = headline.split(":", 1)
        r1 = p.add_run(parts[0] + ":")
        r1.bold = True
        r1.font.size = Pt(12)
        r1.font.name = "Arial"
        r2 = p.add_run(parts[1])
        r2.bold = False
        r2.font.size = Pt(12)
        r2.font.name = "Arial"
    else:
        r = p.add_run(headline)
        r.bold = False
        r.font.size = Pt(12)
        r.font.name = "Arial"

    add_spacer(doc, 15)

    # The narrative is rendered cleanly as cohesive executive paragraphs
    narrative = sanitize_client_name(clean_t_codes(data.narrative), client_name, doc_lang=doc_lang)
    for paragraph_block in narrative.split("\n\n"):
        clean_block = paragraph_block.strip()
        if not clean_block:
            continue
        p_block = doc.add_paragraph()
        p_block.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_block.paragraph_format.space_before = Pt(6)
        p_block.paragraph_format.space_after = Pt(6)
        p_block.paragraph_format.line_spacing = 1.15
        r_block = p_block.add_run(clean_block)
        r_block.font.name = "Arial"
        r_block.font.size = Pt(10.5)
        r_block.font.color.rgb = BASE_TEXT_COLOR

    add_spacer(doc, 15)

    #
    impact_table = doc.add_table(rows=1, cols=1)
    finalize_table(impact_table)

    header_cell = impact_table.rows[0].cells[0]
    set_cell_text(
        header_cell,
        t("key_business_impacts_lbl", locale=doc_lang),
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(header_cell, "0072BC")
    for r in header_cell.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    impacts = [sanitize_client_name(i, client_name, doc_lang=doc_lang) for i in data.key_business_impacts]
    for impact in impacts:
        row = impact_table.add_row()
        body_cell = row.cells[0]
        shade_cell(body_cell, "F2F2F2")

        # Modifies the cell's first paragraph (index 0) in-place. This avoids creating a new paragraph, which would introduce unwanted vertical spacing and disrupt table layout.
        p_bull = body_cell.paragraphs[0]
        clear_paragraph(p_bull)
        p_bull.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p_bull.style = "List Bullet"
        except KeyError:
            p_bull.paragraph_format.left_indent = Pt(20)
            p_bull.paragraph_format.first_line_indent = Pt(-15)
            b_run = p_bull.add_run("• ")
            b_run.font.size = Pt(10.5)
            b_run.font.color.rgb = BASE_TEXT_COLOR

        p_bull.paragraph_format.space_before = Pt(4)
        p_bull.paragraph_format.space_after = Pt(4)

        text = clean_t_codes(str(impact).strip())
        r_text = p_bull.add_run(text)
        r_text.bold = False
        r_text.font.size = Pt(10.5)
        r_text.font.color.rgb = BASE_TEXT_COLOR

    radar_path = client_dir / visuals.get("radar_chart", "")
    if radar_path.exists():
        add_spacer(doc, 15)
        doc.add_picture(str(radar_path), width=Inches(6.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def render_burning_platform(
    doc, platform_risks: list[BurningPlatformItem], doc_lang: str, client_name: str = ""
):
    r"""{'docstring': "Renders a section detailing systemic threats into a `python-docx` document.\n\nThis function appends a titled section for systemic threats to an existing\n`python-docx` document. For each threat provided in `platform_risks`, it\nconstructs a dedicated, formatted three-row table. The table's first row\nserves as a header with the threat's theme, the second row details the\nassociated business risk, and the third row enumerates the root causes as\na bulleted list. All text content is sanitized to process special codes\nand substitute placeholders with the specified client's name.\n\nArgs:\n    doc (docx.document.Document): The `python-docx` Document object to which\n        the content will be appended.\n    platform_risks (list[BurningPlatformItem]): A list of objects, each\n        representing a systemic threat. Each object must expose `theme` (str),\n        `business_risk` (str), and `root_causes` (list[str]) attributes.\n    client_name (str): The name of the client, used for substituting\n        placeholders in the text. Defaults to an empty string.\n\nRaises:\n    AttributeError: If an object in the `platform_risks` list lacks the\n        required `theme`, `business_risk`, or `root_causes` attributes."}."""
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  #
    add_heading_paragraph(doc, t("global_ch2_threats", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        t("global_ch2_intro", locale=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )
    for i, risk in enumerate(platform_risks, start=1):
        table = doc.add_table(rows=3, cols=1)
        finalize_table(table)

        #
        h_cell = table.rows[0].cells[0]
        theme = sanitize_client_name(clean_t_codes(risk.theme), client_name, doc_lang=doc_lang)
        theme = theme[0].upper() + theme[1:] if theme else ""
        set_cell_text(
            h_cell,
            f"Amenaza {i}: {theme}",
            bold=True,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(h_cell, "0072BC")
        for r in h_cell.paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)

        #
        r_cell = table.rows[1].cells[0]
        shade_cell(r_cell, "F2F2F2")
        clear_paragraph(r_cell.paragraphs[0])
        p1 = r_cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1_label = p1.add_run(t("business_risk_label", locale=doc_lang) + " ")
        r1_label.bold = True
        r1_label.font.color.rgb = BASE_TEXT_COLOR
        r1_label.font.size = Pt(10.5)
        r1_text = p1.add_run(
            sanitize_client_name(clean_t_codes(risk.business_risk), client_name, doc_lang=doc_lang)
        )
        r1_text.bold = False
        r1_text.font.color.rgb = BASE_TEXT_COLOR
        r1_text.font.size = Pt(10.5)

        #
        c_cell = table.rows[2].cells[0]
        shade_cell(c_cell, "F2F2F2")
        clear_paragraph(c_cell.paragraphs[0])
        p2 = c_cell.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r2_label = p2.add_run(t("root_causes_label", locale=doc_lang) + " ")
        r2_label.bold = True
        r2_label.font.color.rgb = BASE_TEXT_COLOR
        r2_label.font.size = Pt(10.5)
        causes_list = risk.root_causes
        sanitized_causes = [
            sanitize_client_name(clean_t_codes(c), client_name, doc_lang=doc_lang) for c in causes_list
        ]
        r2_text = p2.add_run("\n" + "\n".join([f"  • {c}" for c in sanitized_causes]))
        r2_text.bold = False
        r2_text.font.color.rgb = BASE_TEXT_COLOR
        r2_text.font.size = Pt(10.5)

        add_spacer(doc, 10)


def render_tower_bottom_lines(
    doc, heatmap: list, tower_texts: list[TowerBottomLineItem], doc_lang: str, client_name=""
):
    """Populates a Word document with a technology area diagnosis table."""
    from assessment_engine.infrastructure.localization import t

    BASE_TEXT_COLOR = RGBColor(46, 64, 77)
    title = t("section_domain_assessment", locale=doc_lang)
    add_heading_paragraph(doc, title, level=1)
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = [
        t("header_domain_area", locale=doc_lang),
        t("header_domain_maturity", locale=doc_lang),
        t("header_executive_diagnosis", locale=doc_lang),
    ]
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=False,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
    color_map = {"E06666": "F4CCCC", "FFD966": "FFF2CC", "93C47D": "D9EAD3"}
    for item in heatmap:
        # The color value is explicitly recalculated here to enforce strict document-wide consistency, overriding any inherited or default template styles.
        strict_color = status_color_for_score(safe_float(item.get("score"), 0.0))

        row = table.add_row()
        set_cell_text(
            row.cells[0],
            f"{item.get('id', '')}\n{item.get('name', '')}",
            bold=False,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text(
            row.cells[1],
            f"{item.get('score', '')}\n({item.get('band', '')})",
            align=WD_ALIGN_PARAGRAPH.CENTER,
            font_size=10.5,
            bold=False,
        )
        shade_cell(row.cells[1], color_map.get(strict_color, "FFFFFF"))

        tower_id = item.get("id", "")
        text_val = ""
        for bottom_line_item in tower_texts:
            if bottom_line_item.id == tower_id:
                text_val = bottom_line_item.bottom_line
                break

        if not text_val:
            text_val = item.get("executive_message", "")

        set_cell_text(
            row.cells[2],
            sanitize_client_name(clean_t_codes(str(text_val)), client_name, doc_lang=doc_lang),
            font_size=10.5,
        )
        #
        for p in row.cells[2].paragraphs:
            for r in p.runs:
                r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)
    add_spacer(doc, 20)


def render_target_vision(doc, vision: TargetVisionDraft, doc_lang: str, client_name="") -> Any:
    """Renders the 'Target State Vision' section into a `docx.document.Document`.

    This function populates the provided Document object with a formatted section
    detailing the strategic vision. It constructs a primary heading, a table for
    the value proposition, and bulleted lists for evolution principles and
    strategic pillars. Text content is sanitized, and client-specific
    placeholders are replaced.

    Args:
        doc (docx.document.Document): The document object to be modified in-place.
        vision (TargetVisionDraft): A data object containing the target state
            vision details. It must possess `value_proposition`,
            `evolution_principles`, and `strategic_pillars` attributes.
        client_name (str): The name of the client to substitute into text
            placeholders. Defaults to an empty string.

    Returns:
        None. The `doc` object is modified directly.

    Raises:
        AttributeError: If the `vision` object is missing one or more of the
            required attributes.
    """
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  #
    add_heading_paragraph(doc, t("global_ch5_tobe", locale=doc_lang), level=1)

    table = doc.add_table(rows=2, cols=1)
    finalize_table(table)

    #
    v_cell_header = table.rows[0].cells[0]
    set_cell_text(
        v_cell_header,
        t("strategic_value_proposition_header", locale=doc_lang),
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(v_cell_header, "0072BC")
    for r in v_cell_header.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    #
    v_cell_body = table.rows[1].cells[0]
    shade_cell(v_cell_body, "F2F2F2")
    clear_paragraph(v_cell_body.paragraphs[0])
    p_body = v_cell_body.paragraphs[0]
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    prop = sanitize_client_name(clean_t_codes(vision.value_proposition), client_name, doc_lang=doc_lang)
    prop = prop[0].upper() + prop[1:] if prop else ""
    prop = prop.replace("─", "").replace("—", "").replace(";", ",")
    r_body = p_body.add_run(prop)
    r_body.font.color.rgb = BASE_TEXT_COLOR
    r_body.font.size = Pt(10.5)
    r_body.bold = False

    add_spacer(doc, 10)
    if vision.evolution_principles:
        add_heading_paragraph(doc, t("maturity_evolution_principles", locale=doc_lang), level=2)
        p_list = [
            f"{p.principle}: {sanitize_client_name(p.description, client_name, doc_lang=doc_lang)}"
            for p in vision.evolution_principles
        ]
        add_smart_bullet_list(doc, p_list, color_rgb=BASE_TEXT_COLOR)
    add_heading_paragraph(doc, t("strategic_enablers_pillars", locale=doc_lang), level=2)
    pillars = vision.strategic_pillars
    pillar_texts = []
    for p in pillars:
        p_name = sanitize_client_name(p.pillar, client_name, doc_lang=doc_lang)
        p_desc = sanitize_client_name(p.description, client_name, doc_lang=doc_lang)
        pillar_texts.append(f"{p_name}: {p_desc}")

    add_smart_bullet_list(
        doc, pillar_texts, color_rgb=BASE_TEXT_COLOR, bold_prefix=True
    )
    add_spacer(doc, 20)


def render_execution_roadmap(
    doc,
    roadmap: ExecutionRoadmapDraft,
    visuals: dict,
    client_dir,
    doc_lang: str,
    client_name="",
):
    """Renders the execution roadmap section into a Word document. This function constructs the "Implementation Plan and Time Horizons" section of the report. It first generates a table listing the defined transversal programs and their descriptions. It then iterates through the time horizons specified in the roadmap data (e.g., "Quick Wins", "Year 1"). For each horizon that contains initiatives, a detailed table is created, listing each initiative's associated program, title, business case, start month, and duration. Args: doc (docx.document.Document): The python-docx Document object to be modified. roadmap (ExecutionRoadmapDraft): A data object containing the structured roadmap information, including programs and initiatives per time horizon. visuals (dict): This parameter is currently unused. client_dir (str): This parameter is currently unused. client_name (str): The client's name, used for placeholder substitution in text content. Defaults to an empty string. Returns: None: The function modifies the `doc` object in place."""
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  #
    add_heading_paragraph(
        doc, t("global_ch6_roadmap_title", locale=doc_lang), level=1
    )
    add_body_paragraph(
        doc,
        t("global_ch6_intro", locale=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )
    table_p = doc.add_table(rows=1, cols=1)
    finalize_table(table_p)

    #
    p_cell_header = table_p.rows[0].cells[0]
    set_cell_text(
        p_cell_header,
        t("header_transversal_programs", locale=doc_lang),
        bold=True,
        font_size=10.5,
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    shade_cell(p_cell_header, "0072BC")
    for r in p_cell_header.paragraphs[0].runs:
        r.font.color.rgb = RGBColor(255, 255, 255)

    #
    programs = roadmap.programs
    for p in programs:
        row = table_p.add_row()
        body_cell = row.cells[0]
        shade_cell(body_cell, "F2F2F2")

        p_bull = body_cell.paragraphs[0]
        clear_paragraph(p_bull)
        p_bull.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        try:
            p_bull.style = "List Bullet"
        except KeyError:
            p_bull.paragraph_format.left_indent = Pt(20)
            p_bull.paragraph_format.first_line_indent = Pt(-15)
            b_run = p_bull.add_run("• ")
            b_run.font.size = Pt(10.5)
            b_run.font.color.rgb = BASE_TEXT_COLOR

        p_bull.paragraph_format.space_before = Pt(6)
        p_bull.paragraph_format.space_after = Pt(6)

        program_name = clean_t_codes(p.name)
        program_desc = sanitize_client_name(clean_t_codes(p.description), client_name, doc_lang=doc_lang)
        # Avoid massive walls of text in table cells by taking concise executive summary sentences
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u017F])", program_desc.strip())
        concise_desc = " ".join(sentences[:2]) if len(sentences) > 2 else program_desc

        r_name = p_bull.add_run(f"{program_name}: ")
        r_name.bold = True
        r_name.font.size = Pt(10.5)
        r_name.font.color.rgb = BASE_TEXT_COLOR

        r_desc = p_bull.add_run(concise_desc)
        r_desc.bold = False
        r_desc.font.size = Pt(10.5)
        r_desc.font.color.rgb = BASE_TEXT_COLOR

    add_spacer(doc, 15)
    horizons = roadmap.horizons
    mapping = [
        (t("roadmap_horizon_quick_wins", locale=doc_lang), horizons.quick_wins_0_3_months),
        (t("roadmap_horizon_year_1", locale=doc_lang), horizons.year_1_3_12_months),
        (t("roadmap_horizon_year_2", locale=doc_lang), horizons.year_2_12_24_months),
        (t("roadmap_horizon_year_3", locale=doc_lang), horizons.year_3_24_36_months),
    ]
    for title, initiatives in mapping:
        if not initiatives:
            continue
        add_heading_paragraph(doc, title, level=3)
        table = doc.add_table(rows=1, cols=5)
        finalize_table(table)
        headers = get_localized_list("roadmap_table_headers", locale=doc_lang)
        for i, h in enumerate(headers):
            set_cell_text(
                table.rows[0].cells[i],
                h,
                bold=False,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(table.rows[0].cells[i], "0072BC")
            for r in table.rows[0].cells[i].paragraphs[0].runs:
                r.font.color.rgb = RGBColor(255, 255, 255)
        for init in initiatives:
            row = table.add_row()
            set_cell_text(
                row.cells[0],
                clean_t_codes(init.program),
                bold=False,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(
                row.cells[1],
                sanitize_client_name(clean_t_codes(init.title), client_name, doc_lang=doc_lang),
                bold=False,
                font_size=10.5,
            )
            set_cell_text(
                row.cells[2],
                sanitize_client_name(clean_t_codes(init.business_case), client_name, doc_lang=doc_lang),
                font_size=10.5,
            )
            set_cell_text(
                row.cells[3],
                f"M{init.start_month}",
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(
                row.cells[4],
                f"{init.duration_months}m",
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            #
            for cell in row.cells:
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.color.rgb = BASE_TEXT_COLOR
        autofit_table_to_contents(table)
        add_spacer(doc, 15)


def render_executive_decisions(
    doc, decisions: ExecutiveDecisionsDraft, doc_lang: str, client_name=""
) -> Any:
    r"""{'docstring': "Populates a `python-docx` document with a formatted executive decisions section.\n\nModifies the provided document object by adding a main heading, a descriptive\nparagraph, and a table listing priority decisions. The table includes columns\nfor the decision's scope, the required action, and the impact of a delay.\nCell text is sanitized based on the provided client name.\n\nArgs:\n    doc (docx.document.Document): The document object to be modified.\n    decisions (ExecutiveDecisionsDraft): A data object containing the list of\n        executive decisions to render.\n    client_name (str): The name of the client, used to sanitize text content\n        in the table.\n\nReturns:\n    None: The function modifies the `doc` object in-place."}."""
    BASE_TEXT_COLOR = RGBColor(46, 64, 77)  #
    add_heading_paragraph(doc, t("global_ch7_decisions", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        t("global_ch7_decisions_intro", locale=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )
    table = doc.add_table(rows=1, cols=3)
    finalize_table(table)
    headers = get_localized_list("board_decision_headers", locale=doc_lang)
    for i, h in enumerate(headers):
        set_cell_text(
            table.rows[0].cells[i],
            h,
            bold=True,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(table.rows[0].cells[i], "0072BC")
        for r in table.rows[0].cells[i].paragraphs[0].runs:
            r.font.color.rgb = RGBColor(255, 255, 255)
    for d in decisions.immediate_decisions:
        row = table.add_row()
        set_cell_text(
            row.cells[0],
            sanitize_client_name(clean_t_codes(d.decision_type), client_name, doc_lang=doc_lang),
            bold=False,
            font_size=10.5,
        )
        set_cell_text(
            row.cells[1],
            sanitize_client_name(clean_t_codes(d.action_required), client_name, doc_lang=doc_lang),
            font_size=10.5,
        )
        set_cell_text(
            row.cells[2],
            sanitize_client_name(clean_t_codes(d.impact_if_delayed), client_name, doc_lang=doc_lang),
            font_size=10.5,
        )
        shade_cell(row.cells[2], "FFFFFF")
        #
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.color.rgb = BASE_TEXT_COLOR
    autofit_table_to_contents(table)


def render_tobe_domain_architectures(
    doc: Document, client_dir: Path, doc_lang: str, client_name: str = ""
) -> None:
    """Renders the comprehensive Target State Architecture for each technological domain, matching FNMT Volume 2."""
    from assessment_engine.infrastructure.text_utils import CANONICAL_TOWER_NAMES

    BASE_TEXT_COLOR = RGBColor(46, 64, 77)
    add_heading_paragraph(doc, t("global_tobe_domain_architectures_heading", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        t("global_tobe_domain_architectures_intro", locale=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )
    add_spacer(doc, 10)

    for i in range(1, 11):
        t_id = f"T{i}"
        bp_path = client_dir / t_id / f"blueprint_{t_id.lower()}_payload.json"
        if not bp_path.exists():
            continue
        try:
            bp_data = json.loads(bp_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, KeyError) as ex:
            logger.debug("[Blueprint] Blueprint payload parsing failed for %s: %s", t_id, ex)
            continue

        num, dom_name = CANONICAL_TOWER_NAMES.get(t_id, (str(i).zfill(2), t_id))
        tower_loc = t(f"tower_{t_id.lower()}_name", locale=doc_lang)
        dom_display = tower_loc if tower_loc and tower_loc != f"tower_{t_id.lower()}_name" else dom_name.replace("_", " ")
        add_heading_paragraph(doc, f"{num}. {dom_display}", level=2)

        snap = bp_data.get("executive_snapshot", {})
        bottom_line = snap.get("bottom_line", "") if isinstance(snap, dict) else ""
        if bottom_line:
            clean_bl = sanitize_client_name(bottom_line, client_name, doc_lang=doc_lang)
            sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\u00C0-\u017F])", clean_bl.strip())
            if len(sentences) > 2:
                p1_text = " ".join(sentences[:2])
                p2_text = " ".join(sentences[2:])
                add_body_paragraph(doc, p1_text, color_rgb=BASE_TEXT_COLOR)
                add_body_paragraph(doc, p2_text, color_rgb=BASE_TEXT_COLOR)
            else:
                add_body_paragraph(doc, clean_bl, color_rgb=BASE_TEXT_COLOR)

        add_heading_paragraph(doc, t("tobe_transitional_horizons_heading", locale=doc_lang), level=3)
        trans_bullets = [
            t("tobe_transitional_h1", locale=doc_lang),
            t("tobe_transitional_h2", locale=doc_lang),
        ]
        add_smart_bullet_list(doc, trans_bullets, color_rgb=BASE_TEXT_COLOR)

        principles = bp_data.get("design_principles", [])
        if principles:
            add_heading_paragraph(doc, t("strategic_enablers_pillars", locale=doc_lang), level=3)
            add_smart_bullet_list(doc, [sanitize_client_name(p, client_name, doc_lang=doc_lang) for p in principles], color_rgb=BASE_TEXT_COLOR)

        # 2. Pillars Target Architecture (FNMT Schema)
        for p_idx, pillar in enumerate(bp_data.get("pillars_analysis", []), start=1):
            p_name = pillar.get("pilar_name", f"Pillar {p_idx}")
            tobe = pillar.get("target_architecture_tobe", {})
            if not isinstance(tobe, dict):
                tobe = {}

            vision = tobe.get("vision", "")
            vis_3y = tobe.get("vision_3_years", "")
            vis_5y = tobe.get("vision_5_years", "")
            levers_tech = tobe.get("levers_technology", [])
            levers_proc = tobe.get("levers_process", [])
            benefits = tobe.get("expected_benefits", [])
            risks_inaction = tobe.get("cost_of_inaction_risks", [])

            add_heading_paragraph(doc, p_name, level=3)
            if vision:
                add_body_paragraph(doc, sanitize_client_name(vision, client_name, doc_lang=doc_lang), color_rgb=BASE_TEXT_COLOR)

            if vis_3y or vis_5y:
                h_table = doc.add_table(rows=3, cols=2)
                finalize_table(h_table)
                set_cell_text(h_table.rows[0].cells[0], t("tobe_horizon_table_horizon_header", locale=doc_lang), bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                shade_cell(h_table.rows[0].cells[0], "0072BC")
                set_cell_text(h_table.rows[0].cells[1], t("tobe_horizon_table_objectives_header", locale=doc_lang), bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                shade_cell(h_table.rows[0].cells[1], "0072BC")

                set_cell_text(h_table.rows[1].cells[0], t("tobe_horizon_table_3y_label", locale=doc_lang), bold=True, font_size=9.5)
                shade_cell(h_table.rows[1].cells[0], "F2F2F2")
                set_cell_text(h_table.rows[1].cells[1], sanitize_client_name(vis_3y, client_name, doc_lang=doc_lang), font_size=9.5)

                set_cell_text(h_table.rows[2].cells[0], t("tobe_horizon_table_5y_label", locale=doc_lang), bold=True, font_size=9.5)
                shade_cell(h_table.rows[2].cells[0], "F2F2F2")
                set_cell_text(h_table.rows[2].cells[1], sanitize_client_name(vis_5y, client_name, doc_lang=doc_lang), font_size=9.5)

                autofit_table_to_contents(h_table)
                add_spacer(doc, 10)

            tech_prefix = t("tobe_levers_technology_prefix", locale=doc_lang)
            proc_prefix = t("tobe_levers_process_prefix", locale=doc_lang)
            all_levers = []
            if isinstance(levers_tech, list):
                all_levers.extend([f"{tech_prefix}{lev}" for lev in levers_tech])
            elif isinstance(levers_tech, str):
                all_levers.append(f"{tech_prefix}{levers_tech}")

            if isinstance(levers_proc, list):
                all_levers.extend([f"{proc_prefix}{lev}" for lev in levers_proc])
            elif isinstance(levers_proc, str):
                all_levers.append(f"{proc_prefix}{levers_proc}")

            if all_levers:
                add_heading_paragraph(doc, t("tobe_evolution_levers_heading", locale=doc_lang), level=4)
                add_smart_bullet_list(doc, [sanitize_client_name(lev_item, client_name, doc_lang=doc_lang) for lev_item in all_levers[:4]], color_rgb=BASE_TEXT_COLOR)

            if benefits or risks_inaction:
                b_table = doc.add_table(rows=2, cols=2)
                finalize_table(b_table)
                set_cell_text(b_table.rows[0].cells[0], t("tobe_benefits_table_benefits_header", locale=doc_lang), bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                shade_cell(b_table.rows[0].cells[0], "0072BC")
                set_cell_text(b_table.rows[0].cells[1], t("tobe_benefits_table_risks_header", locale=doc_lang), bold=True, font_size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
                shade_cell(b_table.rows[0].cells[1], "0072BC")

                b_text = "\n* ".join([str(b) for b in benefits]) if isinstance(benefits, list) else str(benefits)
                r_text = "\n* ".join([str(r) for r in risks_inaction]) if isinstance(risks_inaction, list) else str(risks_inaction)

                set_cell_text(b_table.rows[1].cells[0], ("* " + sanitize_client_name(b_text, client_name, doc_lang=doc_lang)) if b_text else t("tobe_benefits_table_optimization_fallback", locale=doc_lang), font_size=9.5)
                set_cell_text(b_table.rows[1].cells[1], ("* " + sanitize_client_name(r_text, client_name, doc_lang=doc_lang)) if r_text else t("tobe_benefits_table_tech_debt_fallback", locale=doc_lang), font_size=9.5)
                autofit_table_to_contents(b_table)
                add_spacer(doc, 10)

        add_spacer(doc, 15)


def render_todo_detailed_project_charters(
    doc: Document, client_dir: Path, doc_lang: str, client_name: str = ""
) -> None:
    """Renders all detailed project charters with SMART goals, WBS, CapEx/OpEx, matching FNMT Volume 3."""
    from assessment_engine.infrastructure.text_utils import CANONICAL_TOWER_NAMES

    BASE_TEXT_COLOR = RGBColor(46, 64, 77)
    add_heading_paragraph(doc, t("global_todo_project_catalog_heading", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        t("global_todo_project_catalog_intro", locale=doc_lang),
        color_rgb=BASE_TEXT_COLOR,
    )
    add_spacer(doc, 10)

    proj_counter = 1
    for i in range(1, 11):
        t_id = f"T{i}"
        bp_path = client_dir / t_id / f"blueprint_{t_id.lower()}_payload.json"
        if not bp_path.exists():
            continue
        try:
            bp_data = json.loads(bp_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, KeyError) as ex:
            logger.debug("[Blueprint] Blueprint payload parsing failed for %s: %s", t_id, ex)
            continue

        num, dom_name = CANONICAL_TOWER_NAMES.get(t_id, (str(i).zfill(2), t_id))
        tower_loc = t(f"tower_{t_id.lower()}_name", locale=doc_lang)
        dom_display = tower_loc if tower_loc and tower_loc != f"tower_{t_id.lower()}_name" else dom_name.replace("_", " ")

        projects = []
        for p in bp_data.get("pillars_analysis", []):
            projects.extend(p.get("projects_todo", []))

        if not projects:
            continue

        program_heading = t(
            "program_projects_heading_template",
            locale=doc_lang,
            num=num,
            name=dom_display,
            count=len(projects),
        )
        add_heading_paragraph(doc, program_heading, level=2)

        for proj in projects:
            p_name = proj.get("name", f"Initiative {proj_counter}")
            typology = proj.get("transformation_typology", "Core Modernization")
            sizing = proj.get("sizing", "M")
            b_case = proj.get("business_case", "")
            t_obj = proj.get("tech_objective", "")
            capex = proj.get("capex_estimate", "Parametric CapEx")
            opex = proj.get("opex_estimate", "Parametric OpEx")
            roi = proj.get("roi_justification", "")
            horizon = proj.get("duration", "H2 (M3-12)")

            add_heading_paragraph(doc, f"PRJ-{proj_counter:03d}: {p_name}", level=3)

            c_table = doc.add_table(rows=6, cols=2)
            finalize_table(c_table)

            sizing_horizon_lbl = t(
                "sizing_horizon_template",
                locale=doc_lang,
                typology=typology,
                sizing=sizing,
                horizon=horizon,
            )
            wbs_phases_lbl = t(
                "wbs_phases_coordinated_template",
                locale=doc_lang,
                count=len(proj.get("wbs_tasks", [])),
            )

            rows_data = [
                (t("charter_row_typology_sizing", locale=doc_lang), sizing_horizon_lbl),
                (t("charter_row_smart_objective", locale=doc_lang), sanitize_client_name(t_obj, client_name, doc_lang=doc_lang)),
                (t("charter_row_business_case", locale=doc_lang), sanitize_client_name(b_case, client_name, doc_lang=doc_lang)),
                (t("charter_row_finops_budget", locale=doc_lang), f"CapEx: {capex} | OpEx: {opex}"),
                (t("charter_row_roi", locale=doc_lang), sanitize_client_name(roi, client_name, doc_lang=doc_lang)),
                (t("charter_row_wbs", locale=doc_lang), wbs_phases_lbl),
            ]

            for r_idx, (k, v) in enumerate(rows_data):
                set_cell_text(c_table.rows[r_idx].cells[0], k, bold=True, font_size=9.5)
                shade_cell(c_table.rows[r_idx].cells[0], "F2F2F2")
                set_cell_text(c_table.rows[r_idx].cells[1], v, font_size=9.5)

            autofit_table_to_contents(c_table)
            add_spacer(doc, 10)
            proj_counter += 1

        add_spacer(doc, 15)


def create_page_number_footer(section, doc_lang: str) -> Any:
    """Adds a 'Page X of Y' footer to a document section, clearing the first page's footer.    This function configures a document section to have a distinct footer for its    first page, which is typically a cover page. It sets the    `different_first_page_header_footer` property to True and clears all content    from the first page's footer.    For all subsequent pages within the section, a centered footer is added with    the format "Page {PAGE} of {NUMPAGES}". The implementation directly    manipulates the underlying Office Open XML (OOXML) structure to insert the    dynamic `PAGE` and `NUMPAGES` fields. The footer text is styled as 9pt    grey Arial.    Args:        section (docx.section.Section): The `python-docx` Section object to be            modified in-place.    Returns:        None. The section object is modified directly.    Raises:        AttributeError: If the section object lacks expected attributes like            `first_page_footer` or `footer`.        IndexError: If the section's default footer does not contain at least one            paragraph to modify."""
    # Enables a distinct footer for the first page. This setting is required to treat the cover page layout independently from subsequent pages.
    section.different_first_page_header_footer = True

    # The first-page footer is intentionally cleared. This is necessary to maintain a clean cover page layout free of standard footer content.
    first_page_footer = section.first_page_footer
    for p in first_page_footer.paragraphs:
        clear_paragraph(p)

    # Configures the standard footer for all pages following the cover page. This footer is distinct from the first-page footer to accommodate different content requirements.
    footer = section.footer
    paragraph = footer.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    #
    clear_paragraph(paragraph)

    def add_field(p, field_code):
        """Manually constructs the OOXML for a complex Word field and appends it to a paragraph.

        This function provides a low-level mechanism to insert Word fields that are
        not natively supported by the `python-docx` high-level API. It operates
        by directly creating and arranging the required OOXML elements (`w:fldChar`,
        `w:instrText`) within a new run (`w:r`) added to the paragraph.

        The field is initialized with a placeholder result of '0'. The entire run
        containing the field is styled with a 9pt, grey Arial font.

        Args:
            p (docx.paragraph.Paragraph): The paragraph to which the field will be
                added. This object is modified in-place.
            field_code (str): The field code string that defines the field's behavior
                (e.g., 'PAGE', 'DOCPROPERTY "Author"').

        Returns:
            None
        """
        run = p.add_run()
        run.font.size = Pt(9)
        run.font.name = "Arial"
        run.font.color.rgb = RGBColor(127, 127, 127)

        fldChar1 = OxmlElement("w:fldChar")
        fldChar1.set(ns.qn("w:fldCharType"), "begin")
        run._r.append(fldChar1)

        instrText = OxmlElement("w:instrText")
        instrText.set(ns.qn("xml:space"), "preserve")
        instrText.text = field_code
        run._r.append(instrText)

        fldChar2 = OxmlElement("w:fldChar")
        fldChar2.set(ns.qn("w:fldCharType"), "separate")
        run._r.append(fldChar2)

        #
        t = OxmlElement("w:t")
        t.text = "0"
        run._r.append(t)

        fldChar3 = OxmlElement("w:fldChar")
        fldChar3.set(ns.qn("w:fldCharType"), "end")
        run._r.append(fldChar3)

    r = paragraph.add_run(t("page_number_label", locale=doc_lang) + " ")
    r.font.size = Pt(9)
    r.font.name = "Arial"
    r.font.color.rgb = RGBColor(127, 127, 127)

    add_field(paragraph, "PAGE")

    r2 = paragraph.add_run(" " + t("page_of_label", locale=doc_lang) + " ")
    r2.font.size = Pt(9)
    r2.font.name = "Arial"
    r2.font.color.rgb = RGBColor(127, 127, 127)

    add_field(paragraph, "NUMPAGES")


HORIZON_DEFAULTS = {
    "quick_wins_0_3_months": (1, 3),
    "year_1_3_12_months": (3, 9),
    "year_2_12_24_months": (12, 12),
    "year_3_24_36_months": (24, 12),
}


def _normalize_single_horizon_item(item: dict, h_key: str) -> dict:
    """Normalize fallback fields for a single initiative in a roadmap horizon."""
    item_copy = item.copy()

    # Maps the `program_id` and `program_name` source fields into the `program` composite destination field.
    if "program" not in item_copy or not item_copy["program"]:
        p_val = (
            item_copy.get("program_id")
            or item_copy.get("program_name")
            or item_copy.get("program_title")
            or item_copy.get("program")
            or ""
        )
        item_copy["program"] = p_val

    # Maps the `objective`, `description`, `business_impact`, and `impact` source fields into the `business_case` composite destination field.
    if (
        "business_case" not in item_copy
        or not item_copy["business_case"]
    ):
        bc_val = (
            item_copy.get("objective")
            or item_copy.get("description")
            or item_copy.get("business_impact")
            or item_copy.get("impact")
            or "Technical debt mitigation."
        )
        item_copy["business_case"] = bc_val

    def_start, def_duration = HORIZON_DEFAULTS.get(h_key, (1, 6))

    if "start_month" not in item_copy or item_copy["start_month"] == 0:
        item_copy["start_month"] = def_start

    if "duration_months" not in item_copy or item_copy["duration_months"] == 0:
        item_copy["duration_months"] = def_duration

    return item_copy


def _normalize_programs_list(programs: list) -> list:
    """Ensure each program in programs list has a valid description."""
    normalized_programs = []
    for p in programs:
        if isinstance(p, dict):
            p_copy = p.copy()
            if "description" not in p_copy or not p_copy["description"]:
                p_copy["description"] = (
                    p_copy.get("name")
                    or p_copy.get("id")
                    or "Technology transformation program."
                )
            normalized_programs.append(p_copy)
        else:
            normalized_programs.append(p)
    return normalized_programs


def _normalize_roadmap_section(roadmap: dict) -> None:
    """Normalize programs and horizons inside the execution_roadmap dictionary."""

    # Coalesces a null or missing program description to an empty string to ensure type consistency and prevent downstream processing errors.
    if "programs" in roadmap and isinstance(roadmap["programs"], list):
        roadmap["programs"] = _normalize_programs_list(roadmap["programs"])

    # Validates the presence and structural integrity of the `horizons` field, asserting that it is a list before proceeding with iteration.
    if "horizons" not in roadmap or not roadmap["horizons"]:
        roadmap["horizons"] = {
            "quick_wins_0_3_months": [],
            "year_1_3_12_months": [],
            "year_2_12_24_months": [],
            "year_3_24_36_months": [],
        }

    if "horizons" in roadmap and isinstance(roadmap["horizons"], dict):
        h_dict = roadmap["horizons"]
        if (
            "quick_wins_0_6_months" in h_dict
            and "quick_wins_0_3_months" not in h_dict
        ):
            h_dict["quick_wins_0_3_months"] = h_dict["quick_wins_0_6_months"]
        if "year_1_6_12_months" in h_dict and "year_1_3_12_months" not in h_dict:
            h_dict["year_1_3_12_months"] = h_dict["year_1_6_12_months"]

        for h_key in [
            "quick_wins_0_3_months",
            "year_1_3_12_months",
            "year_2_12_24_months",
            "year_3_24_36_months",
        ]:
            if h_key not in h_dict or h_dict[h_key] is None:
                h_dict[h_key] = []

            if isinstance(h_dict[h_key], list):
                h_dict[h_key] = [
                    _normalize_single_horizon_item(item, h_key)
                    if isinstance(item, dict)
                    else item
                    for item in h_dict[h_key]
                ]



def _normalize_target_vision(target_v: dict) -> None:
    """Ensure evolution principles and strategic pillars have required field names."""
    if "evolution_principles" in target_v and isinstance(
        target_v["evolution_principles"], list
    ):
        for item in target_v["evolution_principles"]:
            if (
                isinstance(item, dict)
                and "title" in item
                and "principle" not in item
            ):
                item["principle"] = item["title"]
    if "strategic_pillars" in target_v and isinstance(
        target_v["strategic_pillars"], list
    ):
        for item in target_v["strategic_pillars"]:
            if isinstance(item, dict) and "title" in item and "pillar" not in item:
                item["pillar"] = item["title"]


def _normalize_burning_platform(bp_list: list) -> None:
    """Ensure root_causes is a list for every burning platform item."""
    for item in bp_list:
        if isinstance(item, dict) and "root_causes" in item and isinstance(item["root_causes"], str):
            item["root_causes"] = [item["root_causes"]]


def _normalize_tower_bottom_lines(tbl_list: list) -> None:
    """Ensure default score, band, and status_color in tower bottom lines."""
    for item in tbl_list:
        if isinstance(item, dict):
            item.setdefault("score", 4.0)
            item.setdefault("band", "Managed")
            item.setdefault("status_color", "green")


def _normalize_global_report_dict(payload_dict: dict) -> None:
    """Pre-emptively normalize and adjust legacy JSON fields before Pydantic validation."""
    # Sovereign Data Normalization: Pre-emptive schema adjustments are performed to ensure data consistency and validity prior to rendering.
    if "burning_platform" in payload_dict and isinstance(
        payload_dict["burning_platform"], list
    ):
        _normalize_burning_platform(payload_dict["burning_platform"])

    if "tower_bottom_lines" in payload_dict and isinstance(
        payload_dict["tower_bottom_lines"], list
    ):
        _normalize_tower_bottom_lines(payload_dict["tower_bottom_lines"])

    if "target_vision" in payload_dict and isinstance(
        payload_dict["target_vision"], dict
    ):
        _normalize_target_vision(payload_dict["target_vision"])

    if "execution_roadmap" in payload_dict and isinstance(
        payload_dict["execution_roadmap"], dict
    ):
        _normalize_roadmap_section(payload_dict["execution_roadmap"])

    if "executive_decisions" in payload_dict and isinstance(
        payload_dict["executive_decisions"], list
    ):
        payload_dict["executive_decisions"] = {
            "immediate_decisions": payload_dict["executive_decisions"]
        }
    elif "executive_decisions" in payload_dict and isinstance(
        payload_dict["executive_decisions"], dict
    ):
        if "immediate_decisions" not in payload_dict["executive_decisions"]:
            payload_dict["executive_decisions"]["immediate_decisions"] = []



def _safe_construct(model_cls, data, default_fields):
    """Constructs a model instance from input data using defaults and fallback logic.

    This function creates a model instance by merging default fields with provided
    data. It initializes the model's fields from `default_fields`, then
    overrides these with any non-`None` values from the `data` dictionary.
    A specific fallback logic is applied: if 'principle', 'pillar', or 'program'
    are specified in `default_fields` but absent in the input `data`, their values
    are populated from the 'title' field of the merged data.

    The function utilizes `model_cls.model_construct` for instantiation, which
    bypasses data validation for performance. This assumes the input data is
    pre-validated and trusted.

    Args:
        model_cls: The model class to instantiate, which must expose a
            `model_construct` class method (e.g., a Pydantic BaseModel).
        data: The input data payload. If this value is not a dictionary, it is
            returned immediately without modification.
        default_fields: A mapping of field names to their default values.

    Returns:
        An instance of `model_cls` populated with the merged data if `data` is a
        dictionary; otherwise, the original `data` object.
    """
    if not isinstance(data, dict):
        return data
    data_copy = default_fields.copy()
    for k, v in data.items():
        if v is not None:
            data_copy[k] = v
    if "title" in data_copy:
        if "principle" in default_fields and "principle" not in data:
            data_copy["principle"] = data_copy["title"]
        if "pillar" in default_fields and "pillar" not in data:
            data_copy["pillar"] = data_copy["title"]
        if "program" in default_fields and "program" not in data:
            data_copy["program"] = data_copy["title"]
    return model_cls.model_construct(**data_copy)



def _construct_fallback_roadmap(er_dict: dict) -> Any:
    """Construct ExecutionRoadmapDraft with safe nested models."""
    from assessment_engine.domain.schemas.global_report import (
        ExecutionRoadmapDraft,
        HorizonsDef,
        InitiativeDef,
        ProgramDef,
    )
    er_dict = er_dict.copy() if hasattr(er_dict, "copy") else dict(er_dict)
    if "programs" in er_dict and isinstance(er_dict["programs"], list):
        er_dict["programs"] = [
            _safe_construct(ProgramDef, p, {"name": "", "description": ""})
            if isinstance(p, dict)
            else p
            for p in er_dict["programs"]
        ]
    if "horizons" in er_dict and isinstance(er_dict["horizons"], dict):
        h_dict = er_dict["horizons"].copy()
        if (
            "quick_wins_0_6_months" in h_dict
            and "quick_wins_0_3_months" not in h_dict
        ):
            h_dict["quick_wins_0_3_months"] = h_dict["quick_wins_0_6_months"]
        if (
            "year_1_6_12_months" in h_dict
            and "year_1_3_12_months" not in h_dict
        ):
            h_dict["year_1_3_12_months"] = h_dict["year_1_6_12_months"]

        for h_key in [
            "quick_wins_0_3_months",
            "year_1_3_12_months",
            "year_2_12_24_months",
            "year_3_24_36_months",
        ]:
            if h_key in h_dict and isinstance(h_dict[h_key], list):
                h_dict[h_key] = [
                    _safe_construct(
                        InitiativeDef,
                        init,
                        {
                            "program": "",
                            "title": "",
                            "business_case": "",
                            "start_month": 0,
                            "duration_months": 0,
                        },
                    )
                    if isinstance(init, dict)
                    else init
                    for init in h_dict[h_key]
                ]
        er_dict["horizons"] = _safe_construct(
            HorizonsDef,
            h_dict,
            {
                "quick_wins_0_3_months": [],
                "year_1_3_12_months": [],
                "year_2_12_24_months": [],
                "year_3_24_36_months": [],
            },
        )
    return _safe_construct(
        ExecutionRoadmapDraft, er_dict, {"programs": [], "horizons": None}
    )



def _construct_fallback_payload(payload_dict: dict) -> GlobalReportPayload:
    """Construct a GlobalReportPayload with recursive safe defaults when validation fails."""
    from assessment_engine.domain.schemas.global_report import (
        BurningPlatformItem,
        EvolutionPrinciple,
        ExecutiveDecisionItem,
        ExecutiveDecisionsDraft,
        ExecutiveSummaryDraft,
        GlobalReportDocumentMeta,
        StrategicPillar,
        TargetVisionDraft,
        TowerBottomLineItem,
    )

    payload = GlobalReportPayload.model_construct(**payload_dict)

    payload.meta = _safe_construct(
        GlobalReportDocumentMeta,
        payload.meta if isinstance(payload.meta, dict) else {},
        {"client": "", "date": "", "version": ""},
    )

    payload.executive_summary = _safe_construct(
        ExecutiveSummaryDraft,
        payload.executive_summary
        if isinstance(payload.executive_summary, dict)
        else {},
        {"headline": "", "narrative": "", "key_business_impacts": []},
    )

    if isinstance(payload.burning_platform, list):
        payload.burning_platform = [
            _safe_construct(
                BurningPlatformItem,
                item,
                {"theme": "", "business_risk": "", "root_causes": []},
            )
            if isinstance(item, dict)
            else item
            for item in payload.burning_platform
        ]

    if isinstance(payload.tower_bottom_lines, list):
        payload.tower_bottom_lines = [
            _safe_construct(
                TowerBottomLineItem,
                item,
                {
                    "id": "",
                    "name": "",
                    "score": "",
                    "band": "",
                    "status_color": "",
                    "bottom_line": "",
                },
            )
            if isinstance(item, dict)
            else item
            for item in payload.tower_bottom_lines
        ]

    if isinstance(payload.target_vision, dict):
        tv_dict = payload.target_vision.copy()
        if "evolution_principles" in tv_dict and isinstance(
            tv_dict["evolution_principles"], list
        ):
            tv_dict["evolution_principles"] = [
                _safe_construct(
                    EvolutionPrinciple, ep, {"principle": "", "description": ""}
                )
                if isinstance(ep, dict)
                else ep
                for ep in tv_dict["evolution_principles"]
            ]
        if "strategic_pillars" in tv_dict and isinstance(
            tv_dict["strategic_pillars"], list
        ):
            tv_dict["strategic_pillars"] = [
                _safe_construct(
                    StrategicPillar, sp, {"pillar": "", "description": ""}
                )
                if isinstance(sp, dict)
                else sp
                for sp in tv_dict["strategic_pillars"]
            ]
        payload.target_vision = _safe_construct(
            TargetVisionDraft,
            tv_dict,
            {
                "value_proposition": "",
                "evolution_principles": [],
                "strategic_pillars": [],
            },
        )

    if isinstance(payload.execution_roadmap, dict):
        payload.execution_roadmap = _construct_fallback_roadmap(payload.execution_roadmap.copy())

    if isinstance(payload.executive_decisions, dict):
        ed_dict = payload.executive_decisions.copy()
        if "immediate_decisions" in ed_dict and isinstance(
            ed_dict["immediate_decisions"], list
        ):
            ed_dict["immediate_decisions"] = [
                _safe_construct(
                    ExecutiveDecisionItem,
                    item,
                    {
                        "decision_type": "",
                        "action_required": "",
                        "impact_if_delayed": "",
                    },
                )
                if isinstance(item, dict)
                else item
                for item in ed_dict["immediate_decisions"]
            ]
        payload.executive_decisions = _safe_construct(
            ExecutiveDecisionsDraft, ed_dict, {"immediate_decisions": []}
        )

    return payload



def load_payload(payload_path: Path) -> GlobalReportPayload:
    """Loads, normalizes, and validates a global report payload from a JSON file."""
    payload_dict = load_json(payload_path)
    _normalize_global_report_dict(payload_dict)
    return GlobalReportPayload.model_validate(payload_dict)


def render_global_report(
    payload: GlobalReportPayload,
    template_path: Path,
    output_path: Path,
    client_dir: Path,
    scope: str | None = None,
) -> Path:
    """Renders a global report by populating a Microsoft Word document template.

    Supports rendering the full master report or individual strategic volumes (ASIS, TOBE, TODO).
    """
    doc = Document(str(template_path))
    clear_document_body(doc)

    doc_lang = getattr(payload.meta, "language", "en") or "en"
    if doc.sections:
        create_page_number_footer(doc.sections[0], doc_lang=doc_lang)

    render_cover(doc, payload, doc_lang=doc_lang)
    render_global_toc(doc, doc_lang=doc_lang, scope=scope)
    client_name = payload.meta.client

    render_all = scope in (None, "full", "master")
    render_asis = render_all or scope == "asis"
    render_tobe = render_all or scope == "tobe"
    render_todo = render_all or scope == "todo"

    if render_all:
        if getattr(payload, "board_memo", None):
            render_board_memo(doc, payload.board_memo, client_name=client_name, doc_lang=doc_lang)

    if render_asis:
        if payload.executive_summary:
            render_executive_summary(
                doc,
                payload.executive_summary,
                payload.heatmap,
                payload.visuals,
                client_dir,
                client_name=client_name,
                doc_lang=doc_lang,
            )

        if getattr(payload, "executive_callouts", None):
            for co in payload.executive_callouts[:2]:
                render_executive_callout(
                    doc, co, client_name=client_name, doc_lang=doc_lang
                )

        if payload.burning_platform:
            render_burning_platform(doc, payload.burning_platform, client_name=client_name, doc_lang=doc_lang)
        if payload.tower_bottom_lines and payload.heatmap:
            render_tower_bottom_lines(
                doc, payload.heatmap, payload.tower_bottom_lines, client_name=client_name, doc_lang=doc_lang
            )

        if getattr(payload, "cross_tower_nexus", None):
            render_cross_tower_nexus(doc, payload.cross_tower_nexus, doc_lang=doc_lang, client_name=client_name)

    if render_tobe:
        if payload.target_vision:
            render_target_vision(doc, payload.target_vision, client_name=client_name, doc_lang=doc_lang)
        if scope in ("tobe", "full"):
            render_tobe_domain_architectures(doc, client_dir, doc_lang=doc_lang, client_name=client_name)

    if render_todo:
        if payload.execution_roadmap:
            render_execution_roadmap(
                doc,
                payload.execution_roadmap,
                payload.visuals,
                client_dir,
                doc_lang=doc_lang,
                client_name=client_name,
            )

        if getattr(payload, "executive_callouts", None) and len(payload.executive_callouts) > 2:
            render_executive_callout(
                doc, payload.executive_callouts[2], client_name=client_name, doc_lang=doc_lang
            )

        if payload.executive_decisions:
            render_executive_decisions(
                doc, payload.executive_decisions, client_name=client_name, doc_lang=doc_lang
            )
        if scope in ("todo", "full"):
            render_todo_detailed_project_charters(doc, client_dir, doc_lang=doc_lang, client_name=client_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    logger.info(f"Informe Global ({scope or 'master'}) renderizado: {output_path}")
    return output_path


def main(argv: list[str] | None = None) -> None:
    """Orchestrates rendering a global report from command-line arguments."""
    args_list = list(argv if argv is not None else sys.argv)[1:]
    if len(args_list) < 3:
        sys.exit(1)
    payload_path = Path(args_list[0])
    template_path = Path(args_list[1])
    output_path = Path(args_list[2])
    scope = args_list[3] if len(args_list) > 3 else None
    client_dir = payload_path.parent
    payload = load_payload(payload_path)
    render_global_report(payload, template_path, output_path, client_dir, scope=scope)


if __name__ == "__main__":
    main()
