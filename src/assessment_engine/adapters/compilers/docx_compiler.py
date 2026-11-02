import logging
logger = logging.getLogger(__name__)
import os
import re
from pathlib import Path
from typing import Any, List, Optional

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from assessment_engine.domain.schemas.ast import (
    CellNode,
    DocumentAST,
    HeadingNode,
    PageBreakNode,
    ParagraphNode,
    PictureNode,
    SpacerNode,
    TableNode,
    TableRowNode,
    TOCNode,
)
from assessment_engine.infrastructure.docx_render_utils import (
    add_heading_paragraph,
    apply_bullet_list_format,
    finalize_table,
)
from assessment_engine.ports.document_compiler import DocumentCompiler


def set_run_font_comprehensive(
    run: Any,
    font_name: str = "Arial",
    east_asia_fallback: str = "Meiryo",
    cs_fallback: str = "Arial",
) -> None:
    """Sets comprehensive multi-script fonts (ASCII, High-ANSI, Complex Script, East Asia) per ISO/IEC 29500 to prevent tofu boxes."""
    run.font.name = font_name
    rPr = run._r.get_or_add_rPr()
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rStyle = rPr.find(qn("w:rStyle"))
        if rStyle is not None:
            rStyle.addnext(rFonts)
        else:
            rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font_name)
    rFonts.set(qn("w:hAnsi"), font_name)
    rFonts.set(qn("w:cs"), cs_fallback)
    rFonts.set(qn("w:eastAsia"), east_asia_fallback)


def _insert_in_tblpr(tblPr: Any, element: Any, tag_name: str) -> None:
    """Inserts a child element into w:tblPr adhering strictly to the OpenXML CT_TblPr XSD sequence."""
    order = [
        "tblStyle",
        "tblpPr",
        "tblOverlap",
        "bidiVisual",
        "tblStyleRowBandSize",
        "tblStyleColBandSize",
        "tblW",
        "jc",
        "tblCellSpacing",
        "tblInd",
        "tblBorders",
        "shd",
        "tblLayout",
        "tblCellMar",
        "tblLook",
        "tblCaption",
        "tblDescription",
    ]
    if tag_name in order:
        target_idx = order.index(tag_name)
        for child in list(tblPr):
            c_tag = child.tag.split("}")[-1]
            if c_tag in order and order.index(c_tag) > target_idx:
                child.addprevious(element)
                return
    tblPr.append(element)


def _insert_in_tcpr(tcPr: Any, element: Any, tag_name: str) -> None:
    """Inserts a child element into w:tcPr adhering strictly to the OpenXML CT_TcPr XSD sequence."""
    order = [
        "cnfStyle",
        "tcW",
        "gridSpan",
        "hMerge",
        "vMerge",
        "tcBorders",
        "shd",
        "noWrap",
        "tcMar",
        "textDirection",
        "tcFitText",
        "vAlign",
        "hideMark",
        "headers",
    ]
    if tag_name in order:
        target_idx = order.index(tag_name)
        for child in list(tcPr):
            c_tag = child.tag.split("}")[-1]
            if c_tag in order and order.index(c_tag) > target_idx:
                child.addprevious(element)
                return
    tcPr.append(element)


def safe_shade_cell(cell: Any, fill: str) -> None:
    """Apply a solid color shading to a table cell, ensuring XML schema validity.

    Adds a `w:shd` (shading) element to the cell's `w:tcPr` (table cell
    properties). Any pre-existing `w:shd` element is removed before the new
    shading is applied.

    The function inserts the new `w:shd` element at the correct position as
    defined by the Office Open XML schema for the `CT_TcPr` complex type.
    This prevents document corruption that can result from improperly ordered
    child elements within the cell's properties.

    Args:
        cell (Any): The `python-docx` cell object, which must expose the
            underlying `lxml` element through a `_tc` attribute.
        fill (str): The RRGGBB hex string for the fill color (e.g., "FFA500").

    Raises:
        AttributeError: If `cell` does not have the expected `_tc` attribute.
    """
    tcPr = cell._tc.get_or_add_tcPr()
    for child in list(tcPr):
        if child.tag.endswith("shd"):
            tcPr.remove(child)

    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    _insert_in_tcpr(tcPr, shd, "shd")


def safe_autofit_table_to_contents(table: Any) -> None:
    """Manipulates a table's OOXML to reliably autofit column widths.

    This function directly modifies the Office Open XML (OOXML) of a table to
    enforce robust column autofit behavior, bypassing potential inconsistencies
    with higher-level library properties. It systematically resets table- and
    cell-level width properties to ensure document validity and predictable rendering.

    Args:
        table (Any): The python-docx Table object to be modified in-place.
    """
    table.autofit = True
    tbl = table._tbl

    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)

    for child in list(tblPr):
        tag = child.tag.split("}")[-1]
        if tag in {"tblW", "tblLayout"}:
            tblPr.remove(child)

    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "pct")
    tblW.set(qn("w:w"), "5000")
    _insert_in_tblpr(tblPr, tblW, "tblW")

    tblLayout = OxmlElement("w:tblLayout")
    tblLayout.set(qn("w:type"), "autofit")
    _insert_in_tblpr(tblPr, tblLayout, "tblLayout")

    visited_tcs = set()
    for row in table.rows:
        for cell in row.cells:
            tc_id = id(cell._tc)
            if tc_id in visited_tcs:
                continue
            visited_tcs.add(tc_id)
            tcPr = cell._tc.get_or_add_tcPr()
            for child in list(tcPr):
                if child.tag.endswith("tcW"):
                    tcPr.remove(child)

            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:type"), "auto")
            tcW.set(qn("w:w"), "0")
            _insert_in_tcpr(tcPr, tcW, "tcW")


def add_markdown_runs(
    paragraph: Any,
    text: str,
    default_bold: bool = False,
    default_italic: bool = False,
    font_size: float = 10.5,
    font_name: str = "Arial",
    color_rgb: Any = None,
) -> None:
    """Parses a string with Markdown-style bold syntax into formatted docx runs.

    This function processes an input string to identify and format text enclosed
    in double asterisks (`**`) or double underscores (`__`), treating both as
    indicators for bold formatting. The function segments the string into a
    series of runs and adds them to a provided `docx.paragraph.Paragraph`
    object.

    Each generated run is configured with the specified font name, size, and color.
    Text not enclosed in bold markers is formatted according to the `default_bold`
    flag, while the `default_italic` flag is applied uniformly to all runs.

    Args:
        paragraph ('docx.paragraph.Paragraph'): The paragraph object to which
            the formatted runs will be added.
        text (str): The input string containing text with potential Markdown-style
            bold formatting.
        default_bold (bool): If True, non-bolded segments of text are also
            rendered in bold. Defaults to False.
        default_italic (bool): If True, all generated runs (both bold and regular)
            are rendered in italics. Defaults to False.
        font_size (float): The font size in points for all runs. Defaults to 10.5.
        font_name (str): The font face name for all runs. Defaults to "Arial".
        color_rgb (Optional[Tuple[int, int, int]]): A 3-tuple of integers (0-255)
            representing the RGB color for the font. If None, the default document
            font color is used. Defaults to None.

    Returns:
        None: This function modifies the `paragraph` object in place.

    Raises:
        AttributeError: If the `paragraph` object lacks the required `add_run`
            method or its subsequent font properties.
        TypeError: If `color_rgb` is not a 3-tuple of integers compatible with
            `docx.shared.RGBColor`.
    """
    sanitized = str(text or "").replace("__", "**")
    bold_parts = re.split(r"(\*\*.*?\*\*)", sanitized)

    for b_part in bold_parts:
        if not b_part:
            continue
        is_bold_part = b_part.startswith("**") and b_part.endswith("**") and len(b_part) >= 4
        clean_text = b_part[2:-2] if is_bold_part else b_part
        effective_bold = True if is_bold_part else default_bold

        # Parse single-asterisk italics within the segment
        italic_parts = re.split(r"(\*.*?\*)", clean_text)
        for i_part in italic_parts:
            if not i_part:
                continue
            is_italic = i_part.startswith("*") and i_part.endswith("*") and len(i_part) >= 2
            run_text = i_part[1:-1] if is_italic else i_part
            run = paragraph.add_run(run_text)
            run.bold = effective_bold
            run.italic = True if is_italic else default_italic
            set_run_font_comprehensive(run, font_name=font_name)
            run.font.size = Pt(font_size)
            if color_rgb:
                run.font.color.rgb = RGBColor(*color_rgb)
            else:
                run.font.color.rgb = RGBColor(46, 64, 77)


def safe_set_cell_text(
    cell: Any,
    text: str,
    bold: bool = False,
    align: Any = WD_ALIGN_PARAGRAPH.LEFT,
    font_size: float = 9.0,
    color_rgb: Any = None,
) -> None:
    r"""Replaces the content of a `python-docx` table cell with formatted text.

    This function clears any pre-existing content in the cell and populates it
    based on the input text, applying several formatting heuristics. It handles
    multi-line input by creating distinct paragraphs for each line. The function
    interprets simple list structures (e.g., lines starting with '•', '-', or
    whitespace indentation) and "Label: Description" patterns, where the label
    is rendered in bold. It also parses inline Markdown-style bold syntax
    (e.g., "**text**").

    A critical behavior is ensuring the cell contains at least one paragraph,
    even if empty. This is a safeguard to prevent the generation of a corrupted
    document that cannot be opened by Microsoft Word.

    Args:
        cell (Any): The `python-docx` `_Cell` object to populate. Any existing
            content within this cell will be replaced.
        text (str): The text content to add. Both standard newlines (`\n`) and
            literal escaped newlines (`\\n`) are treated as paragraph breaks.
        bold (bool, optional): If True, applies bold formatting to text that is
            not otherwise styled by other heuristics. Defaults to False.
        align (Any, optional): A `WD_ALIGN_PARAGRAPH` enum member for text
            alignment. Defaults to `WD_ALIGN_PARAGRAPH.LEFT`.
        font_size (float, optional): The font size in points. Defaults to 9.0.
        color_rgb (Any, optional): A tuple or list of three integers (0-255)
            representing an RGB color for the font. Defaults to None.

    Returns:
        None.

    Raises:
        ValueError: If a value in `color_rgb` is outside the valid 0-255 range.
        TypeError: If `color_rgb` is provided with an incompatible type or
            structure (e.g., not a sequence of three numbers).
    """
    clean_txt = str(text or "")

    # If the text contains newlines, it is split into distinct paragraphs. This ensures hard line breaks rather than soft line breaks within a single run.
    if "\n" in clean_txt or "\\n" in clean_txt:
        # Removes the default empty paragraph automatically added by the python-docx library upon cell creation.
        for p in list(cell.paragraphs):
            cell._tc.remove(p._element)

        raw_lines = clean_txt.replace("\\n", "\n").split("\n")
        for line in raw_lines:
            # Leading whitespace is preserved initially as it indicates hierarchical depth; stripping is deferred.
            is_subpoint = line.startswith("   ") or line.strip().startswith("-")

            clean_line = line.strip()
            if not clean_line:
                continue

            p = cell.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.alignment = align

            # Removes any existing bullet formatting to ensure a consistent, uniform reconstruction.
            if clean_line.startswith(("•", "-")) or (clean_line.startswith("* ") and not clean_line.startswith("**")):
                clean_line = clean_line[1:].strip()

            if is_subpoint:
                p.paragraph_format.left_indent = Inches(0.25)
                bullet_prefix = "- "
            else:
                p.paragraph_format.left_indent = Inches(0.0)
                bullet_prefix = (
                    "• "
                    if clean_txt.startswith(("-", "•"))
                    or line.strip().startswith(("-", "•"))
                    else ""
                )

            # Heuristic to detect and structure list items that follow a '• Title: Description' pattern.
            colon_pos = clean_line.find(":")
            has_bullet_or_markdown = bool(bullet_prefix or line.strip().startswith(("*", "•", "-")))
            is_short_label = (
                colon_pos != -1
                and has_bullet_or_markdown
                and not clean_line.startswith("http")
                and colon_pos <= 60
                and "." not in clean_line[:colon_pos]
            )
            if is_short_label:
                clean_label = clean_line[:colon_pos].strip().strip("*").strip("_").strip()
                clean_desc = clean_line[colon_pos + 1:].strip()

                run_lbl = p.add_run(f"{bullet_prefix}{clean_label}: ")
                run_lbl.bold = True
                set_run_font_comprehensive(run_lbl, font_name="Arial")
                run_lbl.font.size = Pt(font_size)
                if color_rgb:
                    run_lbl.font.color.rgb = RGBColor(*color_rgb)
                else:
                    run_lbl.font.color.rgb = RGBColor(46, 64, 77)

                add_markdown_runs(
                    p, clean_desc, default_bold=bold, font_size=font_size, color_rgb=color_rgb
                )
            else:
                if bullet_prefix:
                    run_bp = p.add_run(bullet_prefix)
                    run_bp.bold = bold
                    set_run_font_comprehensive(run_bp, font_name="Arial")
                    run_bp.font.size = Pt(font_size)
                    if color_rgb:
                        run_bp.font.color.rgb = RGBColor(*color_rgb)
                    else:
                        run_bp.font.color.rgb = RGBColor(46, 64, 77)
                add_markdown_runs(
                    p,
                    clean_line,
                    default_bold=bold,
                    font_size=font_size,
                    color_rgb=color_rgb,
                )
    else:
        #
        p = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
        p.alignment = align
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.line_spacing = 1.0

        # Clears any pre-existing text runs from the paragraph to prevent content duplication.
        p.text = ""

        # Heuristic to detect and structure paragraphs that follow a 'Title: Description' pattern.
        colon_pos = clean_txt.find(":")
        is_short_label = (
            colon_pos != -1
            and not clean_txt.startswith("http")
            and colon_pos <= 60
            and "." not in clean_txt[:colon_pos]
        )
        if is_short_label:
            clean_label = clean_txt[:colon_pos].strip().strip("*").strip("_").strip()
            clean_desc = clean_txt[colon_pos + 1:].strip()
            run_lbl = p.add_run(f"{clean_label}: ")
            run_lbl.bold = True
            set_run_font_comprehensive(run_lbl, font_name="Arial")
            run_lbl.font.size = Pt(font_size)
            if color_rgb:
                run_lbl.font.color.rgb = RGBColor(*color_rgb)
            else:
                run_lbl.font.color.rgb = RGBColor(46, 64, 77)

            add_markdown_runs(
                p, clean_desc, default_bold=bold, font_size=font_size, color_rgb=color_rgb
            )
        else:
            add_markdown_runs(
                p,
                clean_txt,
                default_bold=bold,
                font_size=font_size,
                color_rgb=color_rgb,
            )

    # CRITICAL: A table cell must contain at least one paragraph to prevent document corruption, which can cause a fatal error in Microsoft Word.
    if not cell.paragraphs:
        cell.add_paragraph()


class TableLayoutCalculator:
    """Computes deterministic DXA column widths based on statistical cell content distribution."""

    TOTAL_PRINTABLE_WIDTH_DXA: int = 9360  # 6.5 inches in twips (DXA)
    ABS_MIN_COL_WIDTH_DXA: int = 950
    CAP_MIN_COL_WIDTH_DXA: int = 2400
    CHAR_WIDTH_DXA: int = 110
    CELL_PADDING_DXA: int = 240
    DAMPENING_EXPONENT: float = 0.62

    @classmethod
    def compute_column_widths_dxa(cls, node: TableNode, num_cols: Optional[int] = None) -> List[int]:
        if not node.rows:
            return []

        column_widths_dxa = getattr(node, "column_widths_dxa", None)
        if column_widths_dxa:
            return list(column_widths_dxa)

        effective_cols = num_cols if num_cols is not None else max(
            (sum(getattr(c, "grid_span", 1) for c in r.cells) for r in node.rows),
            default=len(node.rows[0].cells) if node.rows else 0,
        )
        if effective_cols == 0:
            return []

        # Explicit width ratios override if provided
        col_widths = getattr(node, "col_widths", None)
        if col_widths and len(col_widths) == effective_cols:
            total_weight = sum(col_widths) or 1.0
            raw_widths = [
                int(round(cls.TOTAL_PRINTABLE_WIDTH_DXA * (w / total_weight)))
                for w in col_widths
            ]
            residual = cls.TOTAL_PRINTABLE_WIDTH_DXA - sum(raw_widths)
            widest_idx = max(range(effective_cols), key=lambda i: raw_widths[i])
            raw_widths[widest_idx] += residual
            return raw_widths

        if getattr(node, "auto_fit_strategy", "CONTENT_PROPORTIONAL") == "EQUAL":
            base_w = cls.TOTAL_PRINTABLE_WIDTH_DXA // effective_cols
            widths = [base_w] * effective_cols
            widths[0] += cls.TOTAL_PRINTABLE_WIDTH_DXA - sum(widths)
            return widths

        # Pass 1: Statistical Content Inspection
        min_bounds_dxa: List[int] = []
        weights: List[float] = []

        import math

        for col_idx in range(effective_cols):
            all_texts: List[str] = []
            for r in node.rows:
                c_cursor = 0
                for c in r.cells:
                    span = getattr(c, "grid_span", 1)
                    if c_cursor <= col_idx < c_cursor + span:
                        txt = str(c.text or "").strip()
                        if txt:
                            if span > 1:
                                all_texts.append(txt[:max(4, len(txt) // span)])
                            else:
                                all_texts.append(txt)
                        break
                    c_cursor += span

            longest_word_len = max(
                (len(word) for text in all_texts for word in text.split()),
                default=4,
            )
            raw_min_dxa = min(longest_word_len, 16) * cls.CHAR_WIDTH_DXA + cls.CELL_PADDING_DXA
            col_min_dxa = max(cls.ABS_MIN_COL_WIDTH_DXA, min(cls.CAP_MIN_COL_WIDTH_DXA, raw_min_dxa))
            min_bounds_dxa.append(col_min_dxa)

            lengths = sorted(len(t) for t in all_texts)
            p90_idx = min(len(lengths) - 1, int(math.floor(len(lengths) * 0.90))) if lengths else 0
            p90_len = lengths[p90_idx] if lengths else 1

            weight = max(longest_word_len * 1.35, math.pow(float(p90_len), cls.DAMPENING_EXPONENT))
            weights.append(weight)

        # Pass 2: Bounded Proportional Normalization
        sum_min_bounds = sum(min_bounds_dxa)
        if sum_min_bounds >= cls.TOTAL_PRINTABLE_WIDTH_DXA:
            return [
                int(round(cls.TOTAL_PRINTABLE_WIDTH_DXA * (m / sum_min_bounds)))
                for m in min_bounds_dxa
            ]

        remaining_dxa = cls.TOTAL_PRINTABLE_WIDTH_DXA - sum_min_bounds
        total_weight = sum(weights) or 1.0

        final_widths = [
            min_bounds_dxa[i] + int(round(remaining_dxa * (weights[i] / total_weight)))
            for i in range(effective_cols)
        ]

        residual = cls.TOTAL_PRINTABLE_WIDTH_DXA - sum(final_widths)
        widest_idx = max(range(effective_cols), key=lambda i: final_widths[i])
        final_widths[widest_idx] += residual

        return final_widths


class DocxCompiler(DocumentCompiler):
    """Compiles a DocumentAST into a Microsoft Word (.docx) document.

    This class implements the visitor pattern to traverse a DocumentAST,
    dispatching each node to a dedicated compilation method that translates it
    into the corresponding python-docx object. It manages document structure,
    text formatting, styles, and embedded objects like tables and images.
    """

    def compile(self, ast: DocumentAST, output_path: str) -> None:
        """Compiles a Document Abstract Syntax Tree (AST) into a .docx file.

        This function performs a single-pass compilation of a `DocumentAST` object
        into a Microsoft Word (.docx) document. It initializes a document object,
        attempting to load from a standard template and falling back to a default
        empty document if the template is not found. Any pre-existing content in the
        document body is cleared, and the base "Normal" style is configured with a
        default font.

        The function then traverses the input AST, delegating the compilation of
        each node to a corresponding handler method (visitor pattern). The resulting
        document is saved to the specified output path, creating parent directories
        as needed.

        Args:
            ast (DocumentAST): The Abstract Syntax Tree representing the document's
                structure and content.
            output_path (str): The destination file path for the generated .docx file.
                Parent directories will be created if they do not exist.

        Raises:
            PermissionError: If the process lacks sufficient permissions to create the
                output directory or write the output file.
            ValueError: If an unsupported or malformed node type is encountered
                during the AST traversal.
        """
        #
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
        from docx.shared import Inches, Pt, RGBColor
        from assessment_engine.infrastructure.runtime_paths import (
            resolve_tower_annex_template_path,
        )

        template_path = resolve_tower_annex_template_path()
        try:
            doc = Document(str(template_path))
        except Exception as ex:
            logger.warning(
                f"[DocxCompiler Warning] Failed to load template from {template_path}, falling back to empty Document(): {ex}"
            )
            doc = Document()

        # Clears all pre-existing paragraphs and tables from the template body.
        for p in list(doc.paragraphs):
            p._element.getparent().remove(p._element)
        for t in list(doc.tables):
            t._element.getparent().remove(t._element)

        #
        style_normal = doc.styles["Normal"]
        font = style_normal.font
        font.name = "Arial"
        font.size = Pt(10.5)

        # Configure corporate footer with native page number field
        try:
            from assessment_engine.infrastructure.localization import t
            section = doc.sections[0]
            section.different_first_page_header_footer = True

            # Clear pre-existing first page footer from template (ensures cover page is pristine)
            first_foot = section.first_page_footer
            for p in list(first_foot.paragraphs):
                p._element.getparent().remove(p._element)
            for t_item in list(first_foot.tables):
                t_item._element.getparent().remove(t_item._element)

            cover_footer_meta = str(ast.metadata.get("cover_footer_metadata") or "").strip()
            if cover_footer_meta:
                p_first = first_foot.add_paragraph()
                p_first.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                p_first.paragraph_format.space_before = Pt(8)
                r_first = p_first.add_run(cover_footer_meta)
                set_run_font_comprehensive(r_first, font_name="Arial")
                r_first.font.size = Pt(8.5)
                r_first.font.italic = True
                r_first.font.color.rgb = RGBColor(100, 116, 139)

            footer = section.footer
            p_foot = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p_foot.paragraph_format.space_before = Pt(8)

            doc_locale = str(ast.metadata.get("language") or "en").lower()
            client_name = str(ast.metadata.get("client_name") or ast.metadata.get("client") or "CLIENT").upper()
            footer_prefix_str = t("corporate_footer_prefix", locale=doc_locale)
            full_footer = f"{client_name} - {footer_prefix_str} "
            r_text = p_foot.add_run(full_footer)
            set_run_font_comprehensive(r_text, font_name="Arial")
            r_text.font.size = Pt(8.5)
            r_text.font.color.rgb = RGBColor(148, 163, 184)

            fldSimple = OxmlElement('w:fldSimple')
            fldSimple.set(qn('w:instr'), 'PAGE')
            p_foot._p.append(fldSimple)
        except (AttributeError, KeyError, IndexError, TypeError) as ex:
            logger.warning("Document footer decoration encountered non-fatal layout exception: %s", ex)

        # Sequentially compiles all AST nodes using a Visitor design pattern.
        for node in ast.nodes:
            self._compile_node(doc, node)

        #
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_file))

    def _compile_node(self, doc: Document, node: Any) -> None:
        """Dispatches the node compilation to the appropriate handler based on its concrete type."""
        node_type = getattr(node, "type", None)

        if node_type == "paragraph" or isinstance(node, ParagraphNode):
            self._compile_paragraph(doc, node)
        elif node_type == "heading" or isinstance(node, HeadingNode):
            self._compile_heading(doc, node)
        elif node_type == "table" or isinstance(node, TableNode):
            self._compile_table(doc, node)
        elif node_type == "spacer" or isinstance(node, SpacerNode):
            self._compile_spacer(doc, node)
        elif node_type == "page_break" or isinstance(node, PageBreakNode):
            doc.add_page_break()
        elif node_type == "picture" or isinstance(node, PictureNode):
            self._compile_picture(doc, node)
        elif node_type == "toc" or isinstance(node, TOCNode):
            self._compile_toc(doc, node)
        else:
            # Unidentified nodes are safely ignored to ensure forward compatibility and operational robustness.
            pass

    def _compile_toc(self, doc: Document, node: Any) -> None:
        """Compiles a native Word OpenXML Table of Contents field inside a Structured Document Tag."""
        # 1. Enable auto-update fields in settings.xml
        settings_element = doc.settings.element
        update_fields = settings_element.find(qn("w:updateFields"))
        if update_fields is None:
            update_fields = OxmlElement("w:updateFields")
            compat = settings_element.find(qn("w:compat"))
            if compat is not None:
                compat.addprevious(update_fields)
            else:
                settings_element.append(update_fields)
        update_fields.set(qn("w:val"), "true")

        # 2. Top-level SDT container recognized by Microsoft Word
        sdt = OxmlElement("w:sdt")
        sdt_pr = OxmlElement("w:sdtPr")
        doc_part_obj = OxmlElement("w:docPartObj")
        doc_part_gallery = OxmlElement("w:docPartGallery")
        doc_part_gallery.set(qn("w:val"), "Table of Contents")
        doc_part_unique = OxmlElement("w:docPartUnique")
        doc_part_obj.append(doc_part_gallery)
        doc_part_obj.append(doc_part_unique)
        sdt_pr.append(doc_part_obj)
        sdt.append(sdt_pr)

        sdt_content = OxmlElement("w:sdtContent")
        sdt.append(sdt_content)

        # 3. TOC Title (not Heading 1 so it does not self-index)
        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(14)
        p_title.paragraph_format.keep_with_next = True
        r_title = p_title.add_run(getattr(node, "title", "Table of Contents"))
        set_run_font_comprehensive(r_title, font_name="Arial")
        r_title.font.size = Pt(16)
        r_title.font.bold = True
        r_title.font.color.rgb = RGBColor(0, 114, 188)
        sdt_content.append(p_title._p)

        # 4. TOC Complex Field Paragraph (begin + instrText + separate)
        field_p = doc.add_paragraph()
        field_p.paragraph_format.space_before = Pt(2)
        field_p.paragraph_format.space_after = Pt(2)

        r_begin = field_p.add_run()
        fld_begin = OxmlElement("w:fldChar")
        fld_begin.set(qn("w:fldCharType"), "begin")
        fld_begin.set(qn("w:dirty"), "true")
        r_begin._r.append(fld_begin)

        r_instr = field_p.add_run()
        instr = OxmlElement("w:instrText")
        instr.set(qn("xml:space"), "preserve")
        depth = getattr(node, "depth", 2)
        instr.text = f' TOC \\o "1-{depth}" \\h \\z \\u '
        r_instr._r.append(instr)

        r_sep = field_p.add_run()
        fld_sep = OxmlElement("w:fldChar")
        fld_sep.set(qn("w:fldCharType"), "separate")
        r_sep._r.append(fld_sep)
        sdt_content.append(field_p._p)

        # 5. Populate initial preview entries with dot leaders (filtered to max depth)
        entries = getattr(node, "entries", [])
        for entry in entries:
            lvl = getattr(entry, "level", 1)
            if lvl > depth:
                continue

            p_e = doc.add_paragraph()
            style_name = f"toc {lvl}"
            if style_name in doc.styles:
                p_e.style = style_name
            p_e.paragraph_format.tab_stops.add_tab_stop(
                Inches(6.4), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
            )
            p_e.paragraph_format.space_after = Pt(3)
            p_e.paragraph_format.space_before = Pt(0)
            lvl = getattr(entry, "level", 1)
            if lvl > 1:
                p_e.paragraph_format.left_indent = Pt((lvl - 1) * 12)

            clean_entry_title = self._strip_heading_number_prefix(getattr(entry, "title", ""))
            r_title_e = p_e.add_run(clean_entry_title)
            set_run_font_comprehensive(r_title_e, font_name="Arial")
            r_title_e.font.size = Pt(9.5)
            r_title_e.font.bold = (lvl == 1)
            r_title_e.font.color.rgb = RGBColor(15, 23, 42)

            p_e.add_run("\t")

            raw_page = str(getattr(entry, "page", "")).strip()
            r_page = p_e.add_run(raw_page)
            set_run_font_comprehensive(r_page, font_name="Arial")
            r_page.font.size = Pt(9.5)
            r_page.font.bold = (lvl == 1)
            r_page.font.color.rgb = RGBColor(100, 116, 139)
            sdt_content.append(p_e._p)

        # Close TOC Complex Field
        end_p = doc.add_paragraph()
        end_p.paragraph_format.space_before = Pt(0)
        end_p.paragraph_format.space_after = Pt(14)
        r_end = end_p.add_run()
        fld_end = OxmlElement("w:fldChar")
        fld_end.set(qn("w:fldCharType"), "end")
        r_end._r.append(fld_end)
        sdt_content.append(end_p._p)

        # Insert complete SDT container at current document sequential position
        p_anchor = doc.add_paragraph()
        p_anchor._p.addprevious(sdt)
        p_anchor._p.getparent().remove(p_anchor._p)

    def _compile_paragraph(self, doc: Document, node: ParagraphNode) -> None:
        if node.style == "cover_subtitle":
            p = doc.add_paragraph()
            p.paragraph_format.page_break_before = False
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(24)
            run = p.add_run(node.text)
            set_run_font_comprehensive(run, font_name="Arial")
            run.font.size = Pt(16.0)
            run.bold = True
            run.font.color.rgb = RGBColor(0, 114, 188)
            return

        if node.text.strip().lower() in ("table of contents", "[toc]"):
            # Inject native Word TOC field (simple field xml)
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(20)
            fldSimple = OxmlElement('w:fldSimple')
            fldSimple.set(qn('w:instr'), 'TOC \\o "1-2" \\h \\z \\u')
            p._p.append(fldSimple)
            return

        # If node.text contains multiple lines, decompose into discrete paragraphs
        # to prevent soft-break <w:br/> justification stretching ("white rivers")
        if "\n" in node.text and not node.text.startswith("```"):
            sub_paragraphs = [sp.strip() for sp in node.text.split("\n") if sp.strip()]
            for sp_idx, sp_text in enumerate(sub_paragraphs):
                sub_node = ParagraphNode(
                    text=sp_text,
                    bold=node.bold,
                    italic=node.italic,
                    style=node.style,
                    space_after=node.space_after if sp_idx == len(sub_paragraphs) - 1 else 6,
                    align=node.align,
                    font_size=node.font_size,
                    text_color_rgb=node.text_color_rgb,
                )
                self._compile_paragraph(doc, sub_node)
            return

        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(node.space_after)

        # Native right-aligned tab stop for TOC dot-leader entries
        if "\t" in node.text:
            from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER
            from docx.shared import Inches
            parts = node.text.split("\t", 1)
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.tab_stops.add_tab_stop(
                Inches(6.4), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
            )
            run_title = p.add_run(parts[0].strip())
            run_title.bold = True
            set_run_font_comprehensive(run_title, font_name="Arial")
            run_title.font.size = Pt(10.0)
            run_title.font.color.rgb = RGBColor(15, 23, 42)

            run_tab = p.add_run("\t")
            set_run_font_comprehensive(run_tab, font_name="Arial")

            run_page = p.add_run(parts[1].strip())
            run_page.bold = True
            set_run_font_comprehensive(run_page, font_name="Arial")
            run_page.font.size = Pt(10.0)
            run_page.font.color.rgb = RGBColor(0, 114, 188)
            return

        # Map string alignment: headers, short labels and bullets must be left-aligned
        clean_text_val = node.text.strip()
        is_short_or_label = (
            len(clean_text_val) < 85
            or clean_text_val.endswith(":")
            or clean_text_val.startswith("#")
            or node.style in ("List Bullet", "Bullet")
        )
        if is_short_or_label:
            align_const = WD_ALIGN_PARAGRAPH.LEFT
        else:
            align_const = WD_ALIGN_PARAGRAPH.JUSTIFY

        align_str = node.align.upper()
        if align_str == "CENTER":
            align_const = WD_ALIGN_PARAGRAPH.CENTER
        elif align_str == "LEFT":
            align_const = WD_ALIGN_PARAGRAPH.LEFT
        elif align_str == "RIGHT":
            align_const = WD_ALIGN_PARAGRAPH.RIGHT

        p.paragraph_format.alignment = align_const

        #
        is_bullet = node.style == "List Bullet" or node.style == "Bullet"
        if is_bullet:
            apply_bullet_list_format(p)

        #
        add_markdown_runs(
            p,
            node.text,
            default_bold=node.bold,
            default_italic=node.italic,
            font_size=node.font_size,
            color_rgb=node.text_color_rgb,
        )

    _HEADING_NUMBER_PREFIX_RE = re.compile(
        r"^\s*(?:[^\W\d_]+\s+)?\d+(?:\.\d+)*\.?\s*[-–—:]?\s*"
    )

    @classmethod
    def _strip_heading_number_prefix(cls, title: str) -> str:
        """Strip manual leading numeric prefixes (e.g. '1. ', '3.1. ') from heading text."""
        if not title:
            return ""
        cleaned = cls._HEADING_NUMBER_PREFIX_RE.sub("", title.strip())
        return cleaned if cleaned else title.strip()

    def _compile_heading(self, doc: Document, node: HeadingNode) -> None:
        import re
        is_appendix_main = getattr(node, "is_appendix", False)
        is_appendix_sub = bool(re.match(r"^[A-Z]\.\d+\s", node.text))

        clean_text = self._strip_heading_number_prefix(node.text)

        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT

        # Assign native Word Heading style from template styles catalog
        try:
            if is_appendix_main and "Appendix Heading 1" in doc.styles:
                p.style = "Appendix Heading 1"
            elif is_appendix_sub and "Appendix Heading 2" in doc.styles:
                p.style = "Appendix Heading 2"
            else:
                heading_style_name = f"Heading {node.level}"
                if heading_style_name in doc.styles:
                    p.style = heading_style_name
        except (KeyError, ValueError, AttributeError) as ex:
            logger.debug("Failed to apply native heading style '%s': %s", getattr(node, "level", 1), ex)

        # Level 1 headings start on a new page unless preceded by an explicit page break
        if node.level == 1 and len(doc.paragraphs) > 5:
            prev_has_br = False
            if len(doc.paragraphs) >= 2:
                prev_p = doc.paragraphs[-2]
                for r in prev_p.runs:
                    for child in r._r:
                        if child.tag.endswith("br") and child.attrib.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}type") == "page":
                            prev_has_br = True
            if not prev_has_br:
                p.paragraph_format.page_break_before = True

        # Executive Spacing and Typographic Scale per heading level
        if node.level == 1:
            p.paragraph_format.space_before = Pt(18)
            p.paragraph_format.space_after = Pt(14)
            font_size_pt = 18.0
        elif node.level == 2:
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(10)
            font_size_pt = 13.0
        else:
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            font_size_pt = 11.0

        # C-Level Typography Hygiene: Prevent orphaned headings at page bottom
        pPr = p._p.get_or_add_pPr()
        pPr.append(OxmlElement("w:keepNext"))
        pPr.append(OxmlElement("w:keepLines"))

        # Inject universal ISO/IEC 29500 OpenXML outlineLvl for Word Navigation Pane and TOC (0-indexed)
        outline_val = max(0, min(8, node.level - 1))
        outlineLvl = OxmlElement("w:outlineLvl")
        outlineLvl.set(qn("w:val"), str(outline_val))
        rPr_elem = pPr.find(qn("w:rPr"))
        if rPr_elem is not None:
            rPr_elem.addprevious(outlineLvl)
        else:
            pPr.append(outlineLvl)

        # Render heading text run with brand color
        brand_color = (
            RGBColor(*node.primary_color_rgb)
            if node.primary_color_rgb
            else RGBColor(0, 114, 188)
        )
        run = p.add_run(clean_text)
        run.bold = True
        set_run_font_comprehensive(run, font_name="Arial")
        run.font.size = Pt(font_size_pt)
        run.font.color.rgb = brand_color

    def _compile_spacer(self, doc: Document, node: SpacerNode) -> None:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(node.points)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = Pt(1)

    def _compile_picture(self, doc: Document, node: PictureNode) -> None:
        if os.path.exists(node.path):
            doc.add_picture(node.path, width=Inches(node.width_inches))
            p_img = doc.paragraphs[-1]
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        else:
            # Defensive fallback to prevent production failures if the image asset failed to generate.
            p = doc.add_paragraph()
            run = p.add_run(f"[Asset unavailable: {Path(node.path).name}]")
            run.italic = True
            run.font.color.rgb = RGBColor(120, 120, 120)

    def _compile_table(self, doc: Document, node: TableNode) -> None:
        effective_rows = list(node.rows)
        if getattr(node, "headers", None) and (not effective_rows or not effective_rows[0].is_header):
            header_cells = [
                CellNode(text=h, bold=True, bg_color="0072BC", text_color_rgb=[255, 255, 255], align="CENTER")
                for h in node.headers
            ]
            effective_rows.insert(0, TableRowNode(cells=header_cells, is_header=True))

        num_rows = len(effective_rows)
        if num_rows == 0:
            return

        required_cols = max(
            (sum(getattr(c, "grid_span", 1) for c in r.cells) for r in effective_rows),
            default=len(effective_rows[0].cells),
        )

        if getattr(node, "column_widths_dxa", None):
            num_cols = max(len(node.column_widths_dxa), required_cols)
        elif getattr(node, "col_widths", None):
            num_cols = max(len(node.col_widths), required_cols)
        else:
            num_cols = required_cols

        if num_cols == 0:
            return

        col_widths_dxa = TableLayoutCalculator.compute_column_widths_dxa(node, num_cols=num_cols)
        while len(col_widths_dxa) < num_cols:
            col_widths_dxa.append(TableLayoutCalculator.TOTAL_PRINTABLE_WIDTH_DXA // num_cols)

        table = doc.add_table(rows=num_rows, cols=num_cols)
        finalize_table(table)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # Enforce table layout
        tbl = table._tbl
        tblPr = tbl.tblPr
        is_autofit = getattr(node, "autofit", False)
        if tblPr is not None:
            for child in list(tblPr):
                tag = child.tag.split("}")[-1]
                if tag in ("tblW", "tblLayout"):
                    tblPr.remove(child)

            if is_autofit:
                tblW = OxmlElement("w:tblW")
                tblW.set(qn("w:type"), "pct")
                tblW.set(qn("w:w"), "5000")
                _insert_in_tblpr(tblPr, tblW, "tblW")
                tblLayout = OxmlElement("w:tblLayout")
                tblLayout.set(qn("w:type"), "autofit")
                _insert_in_tblpr(tblPr, tblLayout, "tblLayout")
                table.autofit = True
            else:
                tblW = OxmlElement("w:tblW")
                tblW.set(qn("w:type"), "dxa")
                tblW.set(qn("w:w"), str(TableLayoutCalculator.TOTAL_PRINTABLE_WIDTH_DXA))
                _insert_in_tblpr(tblPr, tblW, "tblW")
                tblLayout = OxmlElement("w:tblLayout")
                tblLayout.set(qn("w:type"), "fixed")
                _insert_in_tblpr(tblPr, tblLayout, "tblLayout")

        for child in list(tbl):
            if child.tag.endswith("tblGrid"):
                tbl.remove(child)

        tblGrid = OxmlElement("w:tblGrid")
        for w_dxa in col_widths_dxa:
            gridCol = OxmlElement("w:gridCol")
            gridCol.set(qn("w:w"), str(w_dxa))
            tblGrid.append(gridCol)

        if tbl.tblPr is not None:
            tbl.tblPr.addnext(tblGrid)
        else:
            tbl.insert(0, tblGrid)

        for r_idx, row_node in enumerate(effective_rows):
            trPr = table.rows[r_idx]._tr.get_or_add_trPr()
            if getattr(row_node, "cant_split", True):
                trPr.append(OxmlElement("w:cantSplit"))
            if row_node.is_header or (r_idx == 0 and getattr(node, "headers", None)):
                trPr.append(OxmlElement("w:tblHeader"))

            if getattr(row_node, "height_dxa", None):
                trHeight = OxmlElement("w:trHeight")
                trHeight.set(qn("w:val"), str(row_node.height_dxa))
                trHeight.set(qn("w:hRule"), "atLeast")
                trPr.append(trHeight)

            col_cursor = 0
            for cell_node in row_node.cells:
                if col_cursor >= num_cols:
                    break
                span = getattr(cell_node, "grid_span", 1)
                effective_span = min(span, num_cols - col_cursor)

                if effective_span > 1:
                    cell_start = table.rows[r_idx].cells[col_cursor]
                    cell_end = table.rows[r_idx].cells[col_cursor + effective_span - 1]
                    cell_start.merge(cell_end)

                cell = table.rows[r_idx].cells[col_cursor]

                # Apply exact cell width in DXA across the spanned grid columns
                cell_width_dxa = getattr(cell_node, "width_dxa", None) or sum(col_widths_dxa[col_cursor : col_cursor + effective_span])
                tcPr = cell._tc.get_or_add_tcPr()
                for child in list(tcPr):
                    if child.tag.endswith(("tcW", "tcBorders", "vMerge")):
                        tcPr.remove(child)
                tcW = OxmlElement("w:tcW")
                tcW.set(qn("w:type"), "dxa")
                tcW.set(qn("w:w"), str(cell_width_dxa))
                _insert_in_tcpr(tcPr, tcW, "tcW")

                # Handle vertical merge if specified
                if getattr(cell_node, "v_merge", None) in ("restart", "continue"):
                    vMerge = OxmlElement("w:vMerge")
                    if cell_node.v_merge == "restart":
                        vMerge.set(qn("w:val"), "restart")
                    _insert_in_tcpr(tcPr, vMerge, "vMerge")

                # Apply left accent border if specified
                if getattr(cell_node, "border_left_color", None):
                    b_color = cell_node.border_left_color.lstrip("#")
                    b_size = str(getattr(cell_node, "border_left_size", None) or 24)
                    tcBorders = parse_xml(
                        f'<w:tcBorders {nsdecls("w")}><w:left w:val="single" w:sz="{b_size}" w:space="0" w:color="{b_color}"/><w:top w:val="none"/><w:right w:val="none"/><w:bottom w:val="none"/></w:tcBorders>'
                    )
                    _insert_in_tcpr(tcPr, tcBorders, "tcBorders")

                from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                align_const = WD_ALIGN_PARAGRAPH.LEFT
                align_str = cell_node.align.upper()
                if align_str == "CENTER":
                    align_const = WD_ALIGN_PARAGRAPH.CENTER
                elif align_str == "RIGHT":
                    align_const = WD_ALIGN_PARAGRAPH.RIGHT
                elif align_str == "JUSTIFY":
                    align_const = WD_ALIGN_PARAGRAPH.JUSTIFY

                from assessment_engine.compiler.style_invariants import StyleInvariantGuard
                bg_hex = cell_node.bg_color if cell_node.bg_color else None
                if cell_node.text_color_rgb:
                    fg_hex = f"{cell_node.text_color_rgb[0]:02X}{cell_node.text_color_rgb[1]:02X}{cell_node.text_color_rgb[2]:02X}"
                    safe_fg_hex = StyleInvariantGuard.enforce_safe_foreground(fg_hex, bg_hex)
                    safe_rgb = (int(safe_fg_hex[0:2], 16), int(safe_fg_hex[2:4], 16), int(safe_fg_hex[4:6], 16))
                elif bg_hex and bg_hex.upper() in ("0072BC", "0F172A", "00205B", "1E3A8A"):
                    safe_rgb = (255, 255, 255)
                else:
                    safe_rgb = None

                safe_set_cell_text(
                    cell,
                    cell_node.text,
                    bold=cell_node.bold,
                    align=align_const,
                    font_size=cell_node.font_size,
                    color_rgb=safe_rgb,
                )

                if cell_node.bg_color:
                    safe_shade_cell(cell, cell_node.bg_color)

                if getattr(node, "keep_together", False) and r_idx < num_rows - 1:
                    for p in cell.paragraphs:
                        p.paragraph_format.keep_with_next = True

                col_cursor += effective_span
