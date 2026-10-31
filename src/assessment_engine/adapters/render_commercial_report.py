import logging

logger = logging.getLogger(__name__)
import json
import re
import sys
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from assessment_engine.adapters.emitters.docx_style_resolver import DocxStyleResolver
from assessment_engine.domain.theme_registry import SemanticColorRole

"""
Module render_commercial_report.py.
Contains core orchestration and rendering logic for Assessment Engine pipeline.
"""

from assessment_engine.adapters.render_global_report_from_template import (
    add_smart_bullet_list,
    add_spacer,
    clean_t_codes,
    create_page_number_footer,
)
from assessment_engine.domain.schemas.commercial import (
    CommercialPayload,
    CommercialSummaryDraft,
    GtmStrategy,
    OpportunityPipelineItem,
    ProposalDraft,
)
from assessment_engine.infrastructure.contract_utils import robust_load_payload
from assessment_engine.infrastructure.docx_render_utils import (
    add_body_paragraph,
    add_heading_paragraph,
    autofit_table_to_contents,
    clear_paragraph,
    finalize_table,
    set_cell_text,
    shade_cell,
)
from assessment_engine.infrastructure.localization import get_localized_list, t

BASE_TEXT_COLOR = DocxStyleResolver.get_default().resolve_rgb(SemanticColorRole.TEXT_PRIMARY)


def _resolve_company() -> str:
    try:
        from assessment_engine.infrastructure.config_loader import (
            get_consultant_company_name,
        )

        return get_consultant_company_name()
    except Exception:
        return "Nuestra Firma"


def clean_commercial_text(text) -> Any:
    """Clean and standardize a string for commercial reporting.

    Applies a sequence of cleaning and normalization operations to an input string.

    The operations are executed in the following order:
    1.  Removes 't-codes' via the `clean_t_codes` helper function.
    2.  Strips unresolved reference tags matching the pattern `[[REF:...]]`.
    3.  Removes em-dash (—) and box-drawing horizontal (─) characters.
    4.  Normalizes semicolons to commas.
    5.  Removes leading and trailing whitespace.

    If the input is not a string, it is returned unmodified. This provides a
    safe pass-through for non-string data types.

    Args:
        text (Any): The input value to process.

    Returns:
        Any: The cleaned string, or the original input if it was not a string.
    """
    if not isinstance(text, str):
        return text
    cleaned = clean_t_codes(text)
    # Post-processes the document to remove unresolved reference tags. This is a safeguard against rendering artifacts that can result from upstream data inconsistencies or an incomplete template context.
    cleaned = re.sub(r"\[\[REF:[^\]]*\]\]", "", cleaned)
    return cleaned.replace("─", "").replace("—", "").replace(";", ",").strip()


def load_json(path) -> Any:
    """Deserialize a UTF-8 encoded JSON file from a path into a Python object."""
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clear_document_body(doc) -> Any:
    """Removes all content from the document body while preserving section properties.

    Iterates through the top-level XML elements within the document's body and
    removes all content elements (e.g., paragraphs, tables). The final section
    properties element (`w:sectPr`) is explicitly preserved. This is primarily
    used to clear a template document while retaining its page layout settings
    (e.g., margins, orientation). The input `Document` object is modified
    in-place.

    Args:
        doc (docx.document.Document): The `python-docx` Document object to modify.

    Returns:
        None
    """
    body = doc._body._element
    for child in list(body):
        if (
            child.tag
            != "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}sectPr"
        ):
            body.remove(child)


def load_payload(payload_path: Path) -> CommercialPayload:
    """Load and strictly validate a 'Commercial Account Plan' payload from a file."""
    return robust_load_payload(
        payload_path,
        CommercialPayload,
        "Commercial Account Plan",
        mode="strict",
    )


def render_commercial_cover(doc, payload: CommercialPayload, doc_lang: str) -> Any:
    """Render a formatted cover page into a `docx.Document` object.

    Populates the provided document with a standardized commercial report cover page.
    The page includes a main title, client name, date, classification notice, and a
    detailed confidentiality disclaimer in Spanish, applying specific text and
    paragraph formatting. This function modifies the document object in-place and
    concludes by inserting a page break.

    Args:
        doc: The `python-docx.document.Document` object to which the cover page
            content will be added.
        payload: A `CommercialPayload` data object containing the metadata for the
            report, such as the client name and report date.

    Returns:
        None. The function modifies the `doc` object in-place.
    """
    doc.add_paragraph().paragraph_format.space_after = Pt(60)
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = title_p.add_run(t("account_action_plan_title", locale=doc_lang))
    run.font.size = Pt(34)
    run.font.name = "Georgia"
    run.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.BRAND_PRIMARY)
    run.bold = False

    add_spacer(doc, 30)
    client_p = doc.add_paragraph()
    client_run = client_p.add_run(payload.meta.client.upper())
    client_run.font.size = Pt(24)
    client_run.font.name = "Arial"
    client_run.bold = True

    doc.add_paragraph().paragraph_format.space_after = Pt(100)

    lang = getattr(payload.meta, "doc_lang", "en").lower()

    date_lbl = t("commercial_cover_date_lbl", lang)
    class_lbl = t("commercial_cover_class_lbl", lang)

    version_p = doc.add_paragraph()
    v_text = f"{date_lbl}: {payload.meta.date}\n{class_lbl}"
    version_run = version_p.add_run(v_text)
    version_run.font.size = Pt(14)
    version_run.font.name = "Arial"
    version_run.font.color.rgb = DocxStyleResolver.get_default(language_code=lang).resolve_rgb(SemanticColorRole.TEXT_PRIMARY)
    version_run.bold = False

    add_spacer(doc, 150)

    disclaimer_title_p = doc.add_paragraph()
    disclaimer_title_run = disclaimer_title_p.add_run(
        t("commercial_cover_warning_title", lang)
    )
    disclaimer_title_run.font.size = Pt(8)
    disclaimer_title_run.font.name = "Arial"
    disclaimer_title_run.font.color.rgb = DocxStyleResolver.get_default(language_code=lang).resolve_rgb(SemanticColorRole.TEXT_MUTED)
    disclaimer_title_run.bold = True
    disclaimer_title_p.paragraph_format.space_after = Pt(2)

    company = _resolve_company()
    disclaimer_p = doc.add_paragraph()
    disclaimer_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    disclaimer_p.paragraph_format.space_before = Pt(0)
    p1_text = t("commercial_cover_warning_body", lang, company=company)
    r1 = disclaimer_p.add_run(p1_text)
    r1.font.size = Pt(8)
    r1.font.name = "Arial"
    r1.font.color.rgb = DocxStyleResolver.get_default(language_code=lang).resolve_rgb(SemanticColorRole.TEXT_MUTED)

    doc.add_page_break()


def render_commercial_summary(doc, data: CommercialSummaryDraft, matrix: list, doc_lang: str) -> Any:
    """Renders a commercial summary and stakeholder matrix into a `python-docx` document."""
    add_heading_paragraph(doc, t("commercial_ch1_heading", locale=doc_lang), level=1)

    warn_table = doc.add_table(rows=1, cols=1)
    finalize_table(warn_table)
    w_cell = warn_table.rows[0].cells[0]
    shade_cell(w_cell, "F2F2F2")
    clear_paragraph(w_cell.paragraphs[0])
    wp = w_cell.paragraphs[0]
    wp.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    wr1 = wp.add_run(t("commercial_report_context_badge", locale=doc_lang))
    wr1.bold = True
    wr1.font.size = Pt(9)
    wr1.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_MUTED)
    wr2 = wp.add_run(t("commercial_report_disclaimer_body", locale=doc_lang))
    wr2.font.size = Pt(9)
    wr2.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_MUTED)
    add_spacer(doc, 15)

    flash_table = doc.add_table(rows=3, cols=2)
    flash_table.alignment = WD_TABLE_ALIGNMENT.LEFT
    finalize_table(flash_table)
    flash_table.columns[0].width = Inches(2.0)
    flash_table.columns[1].width = Inches(4.5)

    company = _resolve_company()
    set_cell_text(
        flash_table.rows[0].cells[0], f"TAM Estimado {company}:", bold=True, font_size=11
    )
    shade_cell(flash_table.rows[0].cells[0], "0072BC")
    set_cell_text(
        flash_table.rows[0].cells[1],
        f"{clean_commercial_text(data.estimated_tam)} (18-24 meses)",
        bold=True,
        font_size=11,
    )
    shade_cell(flash_table.rows[0].cells[1], "0072BC")
    for r in flash_table.rows[0].cells[0].paragraphs[0].runs:
        r.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)
    for r in flash_table.rows[0].cells[1].paragraphs[0].runs:
        r.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)

    deal_flash = data.deal_flash
    set_cell_text(
        flash_table.rows[1].cells[0],
        "Driver de Compra (Urgencia):",
        bold=True,
        font_size=10.5,
    )
    shade_cell(flash_table.rows[1].cells[0], "F2F2F2")
    set_cell_text(
        flash_table.rows[1].cells[1],
        clean_commercial_text(deal_flash.purchase_driver),
        font_size=10.5,
    )

    set_cell_text(
        flash_table.rows[2].cells[0],
        "Nuestra Ventaja (Win Theme):",
        bold=True,
        font_size=10.5,
    )
    shade_cell(flash_table.rows[2].cells[0], "F2F2F2")
    win_theme_content = clean_commercial_text(
        getattr(deal_flash, "vendor_win_theme", None)
        or getattr(deal_flash, "ntt_win_theme", "")
    )
    set_cell_text(
        flash_table.rows[2].cells[1],
        win_theme_content,
        font_size=10.5,
    )
    autofit_table_to_contents(flash_table)
    add_spacer(doc, 15)

    #
    p_why = doc.add_paragraph()
    r_why = p_why.add_run(t("commercial_the_problem_why_now", locale=doc_lang))
    r_why.bold = True
    r_why.font.color.rgb = BASE_TEXT_COLOR
    r_why.font.size = Pt(11)
    p_why.paragraph_format.space_after = Pt(4)
    add_smart_bullet_list(
        doc,
        data.why_now_bullets,
        color_rgb=BASE_TEXT_COLOR,
        bold_prefix=False,
    )
    add_spacer(doc, 10)

    p_how = doc.add_paragraph()
    r_how = p_how.add_run(t("commercial_how_we_win_label", locale=doc_lang, company=company))
    r_how.bold = True
    r_how.font.color.rgb = BASE_TEXT_COLOR
    r_how.font.size = Pt(11)
    p_how.paragraph_format.space_after = Pt(4)
    add_smart_bullet_list(
        doc,
        data.how_we_win_bullets,
        color_rgb=BASE_TEXT_COLOR,
        bold_prefix=False,
    )
    add_spacer(doc, 20)

    if matrix:
        doc.add_page_break()
        add_heading_paragraph(
            doc, "Matriz de Valor por Interlocutor (Stakeholders)", level=2
        )
        add_body_paragraph(
            doc,
            "Commercial alignment structured around the strategic priorities of each stakeholder role.",
            color_rgb=BASE_TEXT_COLOR,
            space_after=12,
        )

        m_table = doc.add_table(rows=1, cols=3)
        finalize_table(m_table)
        headers = get_localized_list(
            "commercial_messaging_headers",
            locale=doc_lang,
            default=["Executive Role", "Strategic Focus", "Key Elevator Pitch"],
        )
        for i, h in enumerate(headers):
            set_cell_text(
                m_table.rows[0].cells[i],
                h,
                bold=True,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(m_table.rows[0].cells[i], "0072BC")
            for r in m_table.rows[0].cells[i].paragraphs[0].runs:
                r.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)

        for row_data in matrix:
            row = m_table.add_row()
            set_cell_text(
                row.cells[0],
                clean_commercial_text(row_data.role),
                bold=True,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(row.cells[0], "F2F2F2")
            set_cell_text(
                row.cells[1],
                clean_commercial_text(row_data.focus),
                font_size=10.5,
            )
            set_cell_text(
                row.cells[2],
                clean_commercial_text(row_data.message),
                font_size=10.5,
            )
        autofit_table_to_contents(m_table)
        add_spacer(doc, 20)


def render_gtm_strategy(doc, gtm: GtmStrategy, doc_lang: str) -> Any:
    r"""{'docstring': "Adds a 'Go-To-Market' strategy section to a Word document object.\n\nThis function generates a level-1 heading and a formatted two-column table\nsummarizing Go-To-Market strategies. The table populates rows with strategy\nnames and their corresponding descriptions, which are sourced from the `gtm`\ndata object. The table's appearance is customized with specific colors,\nfonts, and alignments, and its columns are auto-fitted to the content.\n\nArgs:\n    doc: The `python-docx` Document object to which the section is added.\n        This object is modified in-place.\n    gtm: An object containing go-to-market strategy descriptions, required\n        to have `trojan_horse`, `self_funded_transformation`, and `lock_in`\n        attributes.\n\nReturns:\n    None. The `doc` object is modified by side effect.\n\nRaises:\n    AttributeError: If the `gtm` object lacks a required strategy attribute."}."""
    add_heading_paragraph(doc, t("commercial_ch2_gtm", locale=doc_lang), level=1)
    table = doc.add_table(rows=1, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    finalize_table(table)
    headers = get_localized_list("commercial_gtm_headers", locale=doc_lang)
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
            r.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)
    vectors = [
        (t("commercial_vector_trojan_horse", locale=doc_lang), gtm.trojan_horse),
        (t("commercial_vector_self_funded", locale=doc_lang), gtm.self_funded_transformation),
        (t("commercial_vector_lock_in", locale=doc_lang), gtm.lock_in),
    ]
    for v_name, v_desc in vectors:
        row = table.add_row()
        set_cell_text(
            row.cells[0],
            v_name,
            bold=True,
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(row.cells[0], "F2F2F2")
        set_cell_text(
            row.cells[1], clean_commercial_text(v_desc), bold=False, font_size=10.5
        )
    autofit_table_to_contents(table)
    add_spacer(doc, 20)


def render_opportunities_pipeline(doc, pipeline: list[OpportunityPipelineItem], doc_lang: str) -> Any:
    """Populates a Word document with a section detailing commercial opportunities.

    This function generates the "Pipeline de Oportunidades" section by first
    adding a primary heading and a descriptive paragraph to the document. It then
    iterates through each `OpportunityPipelineItem` in the `pipeline` list,
    constructing a distinct, formatted table for each one.

    Each table summarizes key details of an opportunity, including the
    initiative name, co-sell vendor, revenue type, estimated Total Contract
    Value (TCV), the client's cost of inaction, and a "Red Team" analysis of
    potential client objections paired with corresponding mitigation strategies.

    Args:
        doc (docx.document.Document): An instance of a `python-docx` Document
            object to which the pipeline section will be appended.
        pipeline (list[OpportunityPipelineItem]): A list of data objects, where
            each object contains the details for a single commercial opportunity.

    Returns:
        None. The function modifies the input `doc` object in-place.
    """
    add_heading_paragraph(doc, t("commercial_ch3_pipeline", locale=doc_lang), level=1)
    add_body_paragraph(
        doc,
        "Financial estimates and Red Team objection mitigation strategies.",
        color_rgb=BASE_TEXT_COLOR,
        space_after=12,
    )
    company = _resolve_company()
    for i, opp in enumerate(pipeline, start=1):
        table = doc.add_table(rows=4, cols=2)
        finalize_table(table)
        h_cell = table.rows[0].cells[0]
        h_cell.merge(table.rows[0].cells[1])
        set_cell_text(
            h_cell,
            f"Oportunidad {i}: {clean_commercial_text(opp.initiative)}",
            bold=True,
            font_size=11,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        shade_cell(h_cell, "0072BC")
        for r in h_cell.paragraphs[0].runs:
            r.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)
        set_cell_text(
            table.rows[1].cells[0],
            f"Vendor Co-Sell: {opp.vendor_cosell}",
            bold=True,
            font_size=10.5,
        )
        set_cell_text(
            table.rows[1].cells[1],
            f"Tipo de Ingreso: {opp.revenue_type}",
            bold=True,
            font_size=10.5,
        )
        shade_cell(table.rows[1].cells[0], "F2F2F2")
        shade_cell(table.rows[1].cells[1], "F2F2F2")
        set_cell_text(
            table.rows[2].cells[0],
            f"TCV Estimado {company}:\n{opp.estimated_tcv}",
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        set_cell_text(
            table.rows[2].cells[1],
            f"{t('commercial_coi_label', locale=doc_lang)}:\n{clean_commercial_text(opp.cost_of_inaction)}",
            font_size=10.5,
            align=WD_ALIGN_PARAGRAPH.CENTER,
        )
        obj_cell = table.rows[3].cells[0]
        obj_cell.merge(table.rows[3].cells[1])
        clear_paragraph(obj_cell.paragraphs[0])
        p1 = obj_cell.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1 = p1.add_run(t("commercial_client_objection_badge", locale=doc_lang))
        r1.bold = False
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.STATUS_CRITICAL)
        r_obj = p1.add_run(clean_commercial_text(opp.client_objection))
        r_obj.bold = False
        r_obj.font.size = Pt(10.5)

        p2 = obj_cell.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r2 = p2.add_run(f"✅ Respuesta {company} (Objection Handling): ")
        r2.bold = False
        r2.font.size = Pt(10.5)
        r2.font.color.rgb = DocxStyleResolver.get_default(language_code=doc_lang).resolve_rgb(SemanticColorRole.STATUS_SUCCESS)
        r_ans = p2.add_run(clean_commercial_text(opp.objection_handling))
        r_ans.bold = False
        r_ans.font.size = Pt(10.5)
        add_spacer(doc, 15)


def render_proactive_proposals(doc, proposals: list[ProposalDraft], lang: str) -> Any:
    """Appends a formatted appendix section for each proactive proposal to a document.

    This function first adds a main heading for the "Proactive Proposals" appendix. It then iterates through each `ProposalDraft` object, inserting a page break before each new proposal to ensure clear separation. For each proposal, it constructs a detailed, multi-part section with specific formatting, including:

    - Numbered title for the proposal.
    - Executive Synthesis, AI Strategy, Context, Solution, and Scope.
    - Delivery model, team composition, and critical assumptions.
    - A formatted table for risk identification and mitigation strategies.
    - Company differentiators and investment/timeline details.

    All text content is cleaned and rendered using specific styles for headings, body text, bullet points, and table cells to maintain document consistency.

    Args:
        doc (docx.document.Document): The `python-docx` document object that will be modified in-place.
        proposals (list[ProposalDraft]): A sequence of data objects, with each object containing the structured content for a single proposal.

    Raises:
        AttributeError: If a `ProposalDraft` object is missing a required attribute, indicating malformed input data.
    """
    add_heading_paragraph(doc, t("commercial_ch4_proposals", locale=lang), level=1)
    add_body_paragraph(
        doc,
        "Detailed proposal drafts ready for client transmission following credential attachment.",
        color_rgb=BASE_TEXT_COLOR,
        space_after=12,
    )
    for idx, prop in enumerate(proposals, 1):
        doc.add_page_break()
        p_title = add_heading_paragraph(
            doc,
            t("commercial_proposal_numbered_title", locale=lang, idx=idx, title=clean_commercial_text(prop.initiative_name)),
            level=2,
        )
        for r in p_title.runs:
            r.font.size = Pt(16)
        add_heading_paragraph(doc, t("commercial_proposal_synthesis", locale=lang), level=3)
        p_syn = doc.add_paragraph()
        p_syn.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r_syn_text = p_syn.add_run(clean_commercial_text(prop.executive_synthesis))
        r_syn_text.bold = False
        r_syn_text.font.color.rgb = BASE_TEXT_COLOR
        p_syn.paragraph_format.space_after = Pt(12)

        ai_strat = prop.ai_transformation_strategy
        if ai_strat:
            add_heading_paragraph(
                doc, t("commercial_transformation_strategy_title", locale=lang), level=3
            )
            p_ai = doc.add_paragraph()
            p_ai.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            r_ai = p_ai.add_run(clean_commercial_text(ai_strat))
            r_ai.font.color.rgb = BASE_TEXT_COLOR
            p_ai.paragraph_format.space_after = Pt(12)

        add_heading_paragraph(
            doc, t("commercial_context_the_why", locale=lang), level=3
        )
        ctx = prop.context_and_why
        orig_lbl = t("commercial_project_origin_label", locale=lang)
        coi_lbl = t("commercial_coi_label", locale=lang)
        add_smart_bullet_list(
            doc,
            [
                f"{orig_lbl}: {clean_commercial_text(ctx.origin)}",
                f"{coi_lbl}: {clean_commercial_text(ctx.cost_of_inaction)}",
            ],
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=True,
        )
        add_spacer(doc, 10)
        add_heading_paragraph(
            doc, t("commercial_solution_the_what", locale=lang), level=3
        )
        sol = prop.solution_and_what
        target_lbl = t("commercial_target_state_label", locale=lang)
        ns_lbl = t("commercial_north_star_label", locale=lang)
        add_smart_bullet_list(
            doc,
            [
                f"{target_lbl}: {clean_commercial_text(sol.target_state)}",
                f"{ns_lbl}: {clean_commercial_text(sol.north_star_metric)}",
            ],
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=True,
        )
        add_spacer(doc, 10)
        add_heading_paragraph(doc, t("commercial_proposal_scope", locale=lang), level=3)
        scope = prop.scope_and_how
        p_phases = doc.add_paragraph()
        r_ph = p_phases.add_run(t("commercial_project_phases", locale=lang))
        r_ph.bold = True
        r_ph.font.color.rgb = BASE_TEXT_COLOR
        p_phases.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            scope.phases,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=True,
        )
        p_del = doc.add_paragraph()
        r_del = p_del.add_run(t("commercial_key_deliverables", locale=lang))
        r_del.bold = True
        r_del.font.color.rgb = BASE_TEXT_COLOR
        p_del.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            scope.deliverables,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=False,
        )
        p_out = doc.add_paragraph()
        r_out = p_out.add_run(t("commercial_out_of_scope", locale=lang))
        r_out.bold = True
        r_out.font.color.rgb = BASE_TEXT_COLOR
        p_out.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            scope.out_of_scope,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=False,
        )
        add_spacer(doc, 10)
        add_heading_paragraph(doc, t("commercial_delivery_model", locale=lang), level=3)
        gov = prop.governance_and_assumptions
        team = prop.delivery_team
        gov_lbl = t("commercial_governance_model_label", locale=lang)
        add_body_paragraph(
            doc,
            f"{gov_lbl}: {clean_commercial_text(gov.governance_model)}",
            color_rgb=BASE_TEXT_COLOR,
            space_after=6,
        )
        p_team = doc.add_paragraph()
        r_team = p_team.add_run(t("commercial_key_profiles", locale=lang))
        r_team.bold = True
        r_team.font.color.rgb = BASE_TEXT_COLOR
        p_team.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            team.team_roles,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=False,
        )
        p_as = doc.add_paragraph()
        r_as = p_as.add_run(t("commercial_critical_assumptions", locale=lang))
        r_as.bold = True
        r_as.font.color.rgb = BASE_TEXT_COLOR
        p_as.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            gov.assumptions,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=False,
        )
        add_spacer(doc, 10)
        add_heading_paragraph(
            doc,
            t("section_project_risk_management", locale=lang),
            level=3,
        )
        risks = prop.risk_management
        if risks:
            company = _resolve_company()
            rtable = doc.add_table(rows=1, cols=2)
            finalize_table(rtable)
            set_cell_text(
                rtable.rows[0].cells[0],
                t("header_identified_risk", locale=lang),
                bold=True,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            set_cell_text(
                rtable.rows[0].cells[1],
                t("header_mitigation_strategy", locale=lang, company=company),
                bold=True,
                font_size=10.5,
                align=WD_ALIGN_PARAGRAPH.CENTER,
            )
            shade_cell(rtable.rows[0].cells[0], "0072BC")
            shade_cell(rtable.rows[0].cells[1], "0072BC")
            for cell in rtable.rows[0].cells:
                for r in cell.paragraphs[0].runs:
                    r.font.color.rgb = DocxStyleResolver.get_default(language_code=lang).resolve_rgb(SemanticColorRole.TEXT_INVERSE)
            for risk_item in risks:
                row = rtable.add_row()
                set_cell_text(
                    row.cells[0],
                    clean_commercial_text(risk_item.risk),
                    font_size=10.5,
                )
                set_cell_text(
                    row.cells[1],
                    clean_commercial_text(risk_item.mitigation),
                    font_size=10.5,
                )
                shade_cell(row.cells[0], "F2F2F2")
                shade_cell(row.cells[1], "F2F2F2")
            add_spacer(doc, 10)
        company = _resolve_company()
        add_heading_paragraph(doc, t("commercial_why_company", locale=lang, company=company), level=3)
        why = prop.why_ntt_data
        add_smart_bullet_list(
            doc,
            why.accelerators,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=False,
        )
        part_lbl = t("commercial_key_partnerships_label", locale=lang)
        add_body_paragraph(
            doc,
            f"{part_lbl}: {clean_commercial_text(why.partnerships)}",
            color_rgb=BASE_TEXT_COLOR,
        )
        p_cred = doc.add_paragraph()
        r_cred = p_cred.add_run(t("commercial_action_required_credentials", locale=lang))
        r_cred.bold = True
        r_cred.font.color.rgb = DocxStyleResolver.get_default(language_code=lang).resolve_rgb(SemanticColorRole.STATUS_CRITICAL)
        p_cred.paragraph_format.space_before = Pt(6)
        p_cred.paragraph_format.space_after = Pt(10)
        add_heading_paragraph(
            doc, t("commercial_investment_activation_title", locale=lang), level=3
        )
        inv = prop.investment_and_timeline
        dur_lbl = t("commercial_estimated_duration_label", locale=lang)
        inv_range_lbl = t("commercial_investment_range_label", locale=lang)
        add_smart_bullet_list(
            doc,
            [
                f"{dur_lbl}: {clean_commercial_text(inv.estimated_duration)}",
                f"{inv_range_lbl}: {clean_commercial_text(inv.tcv_range)}",
            ],
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=True,
        )
        p_act = doc.add_paragraph()
        r_act = p_act.add_run(t("commercial_activation_plan", locale=lang))
        r_act.bold = True
        r_act.font.color.rgb = BASE_TEXT_COLOR
        p_act.paragraph_format.space_after = Pt(4)
        add_smart_bullet_list(
            doc,
            prop.activation_plan,
            color_rgb=BASE_TEXT_COLOR,
            bold_prefix=True,
        )
        add_spacer(doc, 15)


def process_footnotes(doc, dossier) -> Any:
    """Removes unresolved `[[REF:...]]` placeholders from a document object.

    This function performs a final sanitization pass on a document, modifying it
    in-place. It iterates through all paragraphs, both at the top level and
    within table cells, to find and strip any remaining placeholder strings that
    match the pattern `[[REF:...]]`. This cleanup ensures the final output is free
    of internal syntax artifacts that might persist if the corresponding data
    was not found during the rendering process.

    Args:
        doc: The document object to be sanitized. Its paragraphs and tables are
            scanned and modified in-place.
        dossier: Conforms to the standard processing signature; not used in this
            function.

    Returns:
        None. The document object is modified in-place.
    """
    # Executes a final sanitization pass to strip any unresolved `[[REF:...]]` placeholders from the document. This cleanup step ensures the final output is free of internal syntax artifacts that might persist if the corresponding data was not available during rendering.
    ref_pattern = re.compile(r"\[\[REF:[^\]]*\]\]")

    def strip_refs_from_paragraph(p):
        """Removes reference tags (e.g., `[[ref]]`) from a `docx` paragraph in-place.

        Iterates through the `run` objects within the provided paragraph. For each run,
        this function uses a globally-defined `ref_pattern` regular expression to
        find and remove all matching reference tag substrings. The modification is
        applied directly to the `run.text` attribute of each run, effectively
        altering the paragraph object passed as an argument.

        Args:
            p (docx.text.paragraph.Paragraph): The paragraph object to modify in-place.

        Raises:
            NameError: If the global regular expression pattern `ref_pattern` is not
                defined in the calling scope.
        """
        if "[[" in p.text:
            for run in p.runs:
                if "[[" in run.text:
                    run.text = ref_pattern.sub("", run.text)

    for p in doc.paragraphs:
        strip_refs_from_paragraph(p)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    strip_refs_from_paragraph(p)


def render_commercial_report(
    payload: CommercialPayload,
    template_path: Path,
    output_path: Path,
) -> Path:
    r"""{'docstring': 'Generate a commercial report as a Word document from a data payload.\n\nOrchestrates the report generation by loading a specified .docx template,\nclearing its body content, and populating it with data. The function\nconditionally renders sections for a cover page, summary, go-to-market\nstrategy, opportunities pipeline, and proactive proposals based on the\nprovided payload. Finally, it processes footnotes, adds page numbering,\nand saves the completed document to the specified output path.\n\nArgs:\n    payload (CommercialPayload): The data transfer object containing all\n        information to be rendered in the report.\n    template_path (pathlib.Path): The file system path to the .docx\n        template document which provides the base structure and styles.\n    output_path (pathlib.Path): The destination file system path where the\n        generated .docx report will be saved.\n\nReturns:\n    pathlib.Path: The path to the newly created report file, identical to the\n        `output_path` argument.\n\nRaises:\n    docx.opc.exceptions.PackageNotFoundError: If the file at `template_path`\n        does not exist or is not a valid Word document.\n    OSError: If an error occurs while writing the document to `output_path`,\n        such as a permissions issue or an invalid path.'}."""
    doc = Document(str(template_path))
    clear_document_body(doc)

    lang = getattr(payload.meta, "doc_lang", "en").lower()

    if doc.sections:
        create_page_number_footer(doc.sections[0], doc_lang=lang)

    render_commercial_cover(doc, payload, doc_lang=lang)

    if payload.commercial_summary:
        render_commercial_summary(
            doc, payload.commercial_summary, payload.stakeholder_matrix, doc_lang=lang
        )
    if payload.gtm_strategy:
        render_gtm_strategy(doc, payload.gtm_strategy, doc_lang=lang)
    if payload.opportunities_pipeline:
        render_opportunities_pipeline(doc, payload.opportunities_pipeline, doc_lang=lang)
    if payload.proactive_proposals:
        render_proactive_proposals(doc, payload.proactive_proposals, lang=lang)

    process_footnotes(doc, payload.intelligence_dossier)
    doc.save(str(output_path))
    return output_path


def main(argv: list[str] | None = None) -> None:
    """Orchestrates the rendering of a commercial report from the command line.

    This function serves as the main entry point for a command-line utility. It
    parses three required arguments: a path to a JSON payload file, a path to a
    template file, and an output file path. It then loads the data and invokes
    the rendering process.

    Args:
        argv: An optional list of command-line arguments, including the script
            name. Defaults to `sys.argv` if None. Provided primarily for test
            isolation.

    Raises:
        SystemExit: If the number of provided arguments is not four (script name
            plus three required paths).
        FileNotFoundError: If the payload or template file does not exist.
        IOError: If the rendered report cannot be written to the output path.
        json.JSONDecodeError: If the payload file contains malformed JSON.
    """
    if len(argv if argv is not None else sys.argv) != 4:
        sys.exit(1)
    payload_path = Path((argv if argv is not None else sys.argv)[1])
    template_path = Path((argv if argv is not None else sys.argv)[2])
    output_path = Path((argv if argv is not None else sys.argv)[3])
    payload = load_payload(payload_path)

    render_commercial_report(
        payload=payload,
        template_path=template_path,
        output_path=output_path,
    )
    logger.info(f"Account Action Plan renderizado: {output_path}")


if __name__ == "__main__":
    main()
