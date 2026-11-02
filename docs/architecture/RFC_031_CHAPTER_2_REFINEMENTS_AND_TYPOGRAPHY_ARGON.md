# RFC 031: Chapter 2 Editorial & Typographic Harmonization (Platform Narrative Synthesis, Removal of Fabricated Outcomes, Universal Slate Palette, and Uniform 10.5pt Scale)

**Status:** APPROVED FOR IMPLEMENTATION  
**Author:** Principal Systems Architect & Chief Compiler Engineer  
**Target Modules:** `locales.json`, `payload_to_ast.py`, `ast_appendices_builder.py`, `docx_compiler.py`  
**Compliance:** Universal Global Enterprise Readiness (Zero Hardcoding, 100% Technical English Codebase)

---

## 1. Executive Summary & Architectural Objectives

An executive editorial audit of Chapter 2 (*"Objetivo, Alcance y Marco Metodológico"*) across multiple technology towers revealed four structural and typographic inconsistencies:
1. **Unnatural Section 2.2 Title & Raw Domain String Dump:** The heading *"2.2. Descripción de la Plataforma y Topología Unificada"* is overly verbose, and immediately dumping the raw English tower title (`Physical Data Center & Facilities`) beneath it without narrative context breaks editorial flow. Furthermore, the regulatory framework table requires strict OpenXML window-width and content auto-fitting.
2. **Overstated Diagnostic Claims in Section 2.3:** Section *"2.3. Tres Resultados Ejecutivos del Diagnóstico"* asserts deep empirical audits (obsolescence quantification, CapEx/OpEx financial modeling) that misrepresent an interview-based maturity assessment. It must be completely excised, shifting subsequent section numbering cleanly (`2.4` $\rightarrow$ `2.3`, `2.5` $\rightarrow$ `2.4`).
3. **Inconsistent Text Chromatics (`#000000` vs `#2E404D`):** Fallback body text defaults to pure black (`#000000`), clashing visually with sections styled in Executive Slate (`#2E404D`). All body copy, list items, and table cells must default universally to `#2E404D` (`RGB(46, 64, 77)`).
4. **Fragmented Typographic Scale in Methodology Sections:** `ast_appendices_builder.py` currently renders CMMI scale descriptions and capability allocations at micro-scales (`9.0pt` and `8.5pt`), creating a jarring visual step-down from the `10.5pt` standard body prose.

---

## 2. Detailed Architectural Design

### 2.1. Section 2.2 Narrative Synthesis & OpenXML Auto-Fit Table
Instead of emitting the raw `tower_name` string beneath Heading 2.2, the AST builder will synthesize a cohesive introductory block derived from the payload's `domain_introduction` object:
* **Heading:** Streamlined via `locales.json` to `"2.2. Descripción de la Plataforma"` (ES) / `"2.2. Platform Description"` (EN).
* **Contextual Narrative:** Extracts `domain_introduction.introduction_paragraph`. If `domain_introduction.included_components` is populated, it appends a localized transitional lead-in followed by an executive bulleted list of the evaluated physical/digital components, grounding the scope before presenting the methodological table.
* **OpenXML Auto-Fit Specification:** The Regulatory/Methodological Framework table (`ASTTable`) will enforce `autofit=True` and `width_pct=100.0`, which the compiler translates into `<w:tblW w:w="5000" w:type="pct"/>` and `<w:tblLayout w:type="autofit"/>`.

### 2.2. Excision of Section 2.3 & Automatic Section Renumbering
* Remove the AST generation block for *"2.3. Tres Resultados Ejecutivos del Diagnóstico"* from `payload_to_ast.py`.
* Purge the corresponding keys (`sec_2_3_title`, `sec_2_3_bullets`) from `locales.json`.
* Re-index the localized headings for the CMMI 5-Level Scale and Evaluated Capabilities to **2.3** and **2.4** respectively in `locales.json`.

### 2.3. Universal Executive Slate Palette (`#2E404D`)
* Define a single source of truth constant in `docx_compiler.py`: `DEFAULT_TEXT_COLOR_HEX = "2E404D"` (`RGBColor(0x2E, 0x40, 0x4D)`).
* Update the Normal style initialization, `add_markdown_runs()`, paragraph builders, and table cell renderers so that any text node lacking an explicit semantic override (such as alert red or accent navy) inherits `#2E404D` instead of `#000000`.

### 2.4. Uniform 10.5pt Typographic Scale in `ast_appendices_builder.py`
* Refactor `build_cmmi_methodology_and_capabilities()` to eliminate hardcoded `font_size=9.0` and `font_size=8.5` overrides.
* Standardize all introductory paragraphs, CMMI level definitions, and capability domain bullets to `font_size=10.5` and `color="2E404D"`.

---

## 3. Production Implementation Specifications

### 3.1. Localization Dictionary Updates (`locales.json`)

Update the Chapter 2 keys in `locales.json` to streamline Section 2.2, introduce the component scope lead-in, remove Section 2.3, and re-index Sections 2.3 and 2.4:

```json
{
  "es": {
    "ch2_sec_2_2_title": "2.2. Descripción de la Plataforma",
    "ch2_sec_2_2_components_lead": "El alcance técnico evaluado dentro de este dominio comprende los siguientes componentes y subsistemas críticos:",
    "ch2_sec_2_3_cmmi_title": "2.3. Escala Analítica de Madurez (CMMI 1.00 a 5.00)",
    "ch2_sec_2_4_capabilities_title": "2.4. Asignación de Capacidades Evaluadas por Dominio"
  },
  "en": {
    "ch2_sec_2_2_title": "2.2. Platform Description",
    "ch2_sec_2_2_components_lead": "The technical scope evaluated within this domain encompasses the following critical components and subsystems:",
    "ch2_sec_2_3_cmmi_title": "2.3. Analytical Maturity Scale (CMMI 1.00 to 5.00)",
    "ch2_sec_2_4_capabilities_title": "2.4. Evaluated Capabilities Allocation by Domain"
  }
}
```
*(Note: Deprecated keys for "Tres Resultados Ejecutivos del Diagnóstico" are permanently removed from the localization schema).*

---

### 3.2. Platform Narrative Synthesis & Section 2.3 Removal (`payload_to_ast.py`)

Refactor the Chapter 2 builder method in `payload_to_ast.py` to synthesize the domain introduction, enforce table auto-fitting, and remove the deprecated diagnostic outcomes section:

```python
# File: payload_to_ast.py

from typing import Dict, Any, List
from ast_nodes import (
    ASTNode, ASTHeading, ASTParagraph, ASTList, ASTTable, ASTTableCell
)

DEFAULT_SLATE_HEX = "2E404D"
STANDARD_BODY_FONT_PT = 10.5


def build_section_2_2_platform_description(
    payload: Dict[str, Any],
    i18n: Dict[str, Any]
) -> List[ASTNode]:
    """
    Synthesizes Section 2.2 (Platform Description) using the rich domain introduction
    narrative, evaluated component scope, and an auto-fitted methodological table.
    """
    nodes: List[ASTNode] = []

    # 1. Streamlined Section 2.2 Heading
    nodes.append(
        ASTHeading(
            text=i18n.get("ch2_sec_2_2_title", "2.2. Platform Description"),
            level=2
        )
    )

    # 2. Rich Introductory Narrative Synthesis (No raw English tower name dump)
    domain_intro: Dict[str, Any] = payload.get("domain_introduction", {}) or {}
    intro_paragraph: str = domain_intro.get("introduction_paragraph", "").strip()
    included_components: List[str] = domain_intro.get("included_components", []) or []

    if intro_paragraph:
        nodes.append(
            ASTParagraph(
                text=intro_paragraph,
                font_size=STANDARD_BODY_FONT_PT,
                color=DEFAULT_SLATE_HEX,
                space_after=6.0
            )
        )

    if included_components:
        lead_text = i18n.get("ch2_sec_2_2_components_lead", "")
        if lead_text:
            nodes.append(
                ASTParagraph(
                    text=lead_text,
                    font_size=STANDARD_BODY_FONT_PT,
                    color=DEFAULT_SLATE_HEX,
                    space_after=4.0
                )
            )
        nodes.append(
            ASTList(
                items=included_components,
                ordered=False,
                font_size=STANDARD_BODY_FONT_PT,
                color=DEFAULT_SLATE_HEX,
                space_after=8.0
            )
        )

    # 3. Regulatory & Methodological Framework Table (Auto-fit to window and contents)
    frameworks: List[Dict[str, Any]] = domain_intro.get("regulatory_frameworks", []) or []
    if frameworks:
        headers = [
            i18n.get("table_header_standard", "Standard / Framework"),
            i18n.get("table_header_scope", "Analytical Scope & Application")
        ]
        rows: List[List[ASTTableCell]] = []
        for fw in frameworks:
            std_name = str(fw.get("name", "")).strip()
            std_desc = str(fw.get("description", "")).strip()
            rows.append([
                ASTTableCell(
                    text=f"**{std_name}**",
                    font_size=9.5,
                    color=DEFAULT_SLATE_HEX
                ),
                ASTTableCell(
                    text=std_desc,
                    font_size=9.5,
                    color=DEFAULT_SLATE_HEX
                )
            ])

        nodes.append(
            ASTTable(
                headers=headers,
                rows=rows,
                width_pct=100.0,
                autofit=True  # Enforces OpenXML window + content auto-fitting
            )
        )

    # NOTE: Former Section 2.3 ("Three Executive Diagnostic Outcomes") is intentionally
    # omitted per architectural governance to ensure strict alignment with interview-based scope.

    return nodes
```

---

### 3.3. Typographic Scale & Color Normalization (`ast_appendices_builder.py`)

Update `build_cmmi_methodology_and_capabilities` in `ast_appendices_builder.py` so that both the CMMI scale (now Section 2.3) and Evaluated Capabilities (now Section 2.4) render at a uniform `10.5pt` font size and `#2E404D` slate color:

```python
# File: ast_appendices_builder.py

from typing import Dict, Any, List
from ast_nodes import ASTNode, ASTHeading, ASTParagraph, ASTList

DEFAULT_SLATE_HEX = "2E404D"
STANDARD_BODY_FONT_PT = 10.5


def build_cmmi_methodology_and_capabilities(
    payload: Dict[str, Any],
    i18n: Dict[str, Any]
) -> List[ASTNode]:
    """
    Builds Section 2.3 (CMMI 1.00-5.00 Analytical Scale) and Section 2.4
    (Evaluated Capabilities Allocation) with uniform 10.5pt typography and
    Executive Slate (#2E404D) color governance.
    """
    nodes: List[ASTNode] = []
    methodology: Dict[str, Any] = payload.get("methodology_framework", {}) or {}

    # --- SECTION 2.3: CMMI ANALYTICAL MATURITY SCALE ---
    nodes.append(
        ASTHeading(
            text=i18n.get("ch2_sec_2_3_cmmi_title", "2.3. Analytical Maturity Scale"),
            level=2
        )
    )

    cmmi_intro: str = methodology.get(
        "scale_introduction",
        i18n.get("cmmi_scale_default_intro", "")
    ).strip()

    if cmmi_intro:
        nodes.append(
            ASTParagraph(
                text=cmmi_intro,
                font_size=STANDARD_BODY_FONT_PT,  # Standardized from 9.0pt -> 10.5pt
                color=DEFAULT_SLATE_HEX,
                space_after=6.0
            )
        )

    scale_levels: List[Dict[str, Any]] = methodology.get("scale_levels", []) or []
    level_items: List[str] = []
    for lvl in scale_levels:
        level_label = str(lvl.get("level", "")).strip()
        level_name = str(lvl.get("name", "")).strip()
        level_desc = str(lvl.get("description", "")).strip()
        level_items.append(f"**{level_label} - {level_name}:** {level_desc}")

    if level_items:
        nodes.append(
            ASTList(
                items=level_items,
                ordered=False,
                font_size=STANDARD_BODY_FONT_PT,  # Standardized from 8.5pt -> 10.5pt
                color=DEFAULT_SLATE_HEX,
                space_after=10.0
            )
        )

    # --- SECTION 2.4: EVALUATED CAPABILITIES ALLOCATION ---
    nodes.append(
        ASTHeading(
            text=i18n.get("ch2_sec_2_4_capabilities_title", "2.4. Evaluated Capabilities Allocation"),
            level=2
        )
    )

    cap_intro: str = methodology.get(
        "capabilities_introduction",
        i18n.get("capabilities_default_intro", "")
    ).strip()

    if cap_intro:
        nodes.append(
            ASTParagraph(
                text=cap_intro,
                font_size=STANDARD_BODY_FONT_PT,  # Standardized from 9.0pt -> 10.5pt
                color=DEFAULT_SLATE_HEX,
                space_after=6.0
            )
        )

    capability_domains: List[Dict[str, Any]] = methodology.get("capability_domains", []) or []
    cap_items: List[str] = []
    for dom in capability_domains:
        dom_name = str(dom.get("domain_name", "")).strip()
        dom_weight = str(dom.get("weight_pct", "")).strip()
        dom_desc = str(dom.get("description", "")).strip()
        weight_suffix = f" ({dom_weight}%)" if dom_weight else ""
        cap_items.append(f"**{dom_name}{weight_suffix}:** {dom_desc}")

    if cap_items:
        nodes.append(
            ASTList(
                items=cap_items,
                ordered=False,
                font_size=STANDARD_BODY_FONT_PT,  # Standardized from 8.5pt -> 10.5pt
                color=DEFAULT_SLATE_HEX,
                space_after=10.0
            )
        )

    return nodes
```

---

### 3.4. Universal Slate Color Governance & OpenXML Auto-Fit (`docx_compiler.py`)

In `docx_compiler.py`, replace all fallback `#000000` color definitions with `EXECUTIVE_SLATE_HEX = "2E404D"` and implement the low-level OpenXML table auto-fit routine:

```python
# File: docx_compiler.py

import re
from typing import Optional
from docx.shared import Pt, RGBColor
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Universal Executive Slate Palette (#2E404D -> RGB: 46, 64, 77)
EXECUTIVE_SLATE_HEX = "2E404D"
EXECUTIVE_SLATE_RGB = RGBColor(0x2E, 0x40, 0x4D)
DEFAULT_BODY_SIZE_PT = 10.5


def parse_hex_color(hex_str: Optional[str]) -> RGBColor:
    """
    Resolves a 6-character hex string into a python-docx RGBColor.
    Defaults universally to Executive Slate (#2E404D) instead of pure black (#000000).
    """
    if not hex_str:
        return EXECUTIVE_SLATE_RGB
    cleaned = hex_str.strip().lstrip("#").upper()
    if len(cleaned) != 6 or cleaned == "000000":
        return EXECUTIVE_SLATE_RGB
    return RGBColor.from_string(cleaned)


def add_markdown_runs(
    paragraph: Paragraph,
    text: str,
    font_name: str = "Segoe UI",
    font_size_pt: float = DEFAULT_BODY_SIZE_PT,
    color_hex: str = EXECUTIVE_SLATE_HEX,
    default_bold: bool = False,
    default_italic: bool = False
) -> None:
    """
    Parses inline Markdown (**bold**, *italic*) and emits formatted OpenXML runs.
    Enforces #2E404D Executive Slate across all text runs unless overridden.
    """
    target_color = parse_hex_color(color_hex)
    tokens = re.split(r"(\*\*.*?\*\*|\*.*?\*)", text or "")

    for token in tokens:
        if not token:
            continue
        is_bold = default_bold
        is_italic = default_italic
        clean_text = token

        if token.startswith("**") and token.endswith("**") and len(token) > 4:
            is_bold = True
            clean_text = token[2:-2]
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            is_italic = True
            clean_text = token[1:-1]

        run = paragraph.add_run(clean_text)
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        run.font.bold = is_bold
        run.font.italic = is_italic
        run.font.color.rgb = target_color


def apply_openxml_table_autofit(table: Table, width_pct: float = 100.0) -> None:
    """
    Configures OpenXML table properties (<w:tblPr>) to simultaneously:
    1. Span 100% of the page margins (w:tblW w:type="pct" w:w="5000").
    2. Dynamically auto-fit column widths to their cell contents (w:tblLayout w:type="autofit").
    """
    tbl_pr = table._tbl.tblPr
    if tbl_pr is None:
        tbl_pr = OxmlElement("w:tblPr")
        table._tbl.insert(0, tbl_pr)

    # 1. Remove existing width or layout declarations to prevent schema collisions
    for tag in ("w:tblW", "w:tblLayout"):
        existing = tbl_pr.find(qn(tag))
        if existing is not None:
            tbl_pr.remove(existing)

    # 2. Set Table Width in fiftieths of a percent (100% = 5000)
    pct_units = int(round(width_pct * 50))
    tbl_w = OxmlElement("w:tblW")
    tbl_w.set(qn("w:w"), str(pct_units))
    tbl_w.set(qn("w:type"), "pct")
    tbl_pr.append(tbl_w)

    # 3. Set Table Layout to Autofit contents
    tbl_layout = OxmlElement("w:tblLayout")
    tbl_layout.set(qn("w:type"), "autofit")
    tbl_pr.append(tbl_layout)

    # 4. Ensure python-docx internal flag aligns with OpenXML state
    table.autofit = True
```

---

## 4. Verification & Acceptance Criteria Matrix

| Audit Requirement | Architectural Resolution | Verification Check |
| :--- | :--- | :--- |
| **1a. Section 2.2 Title** | Updated `ch2_sec_2_2_title` in `locales.json` to `"2.2. Descripción de la Plataforma"` / `"2.2. Platform Description"`. | Inspect generated Heading 2 text in Chapter 2. |
| **1b/c. Domain Intro Prose** | Removed raw `tower_name` dump; synthesized `domain_introduction.introduction_paragraph` + `included_components` list. | Verify cohesive introductory narrative and bulleted scope precede the framework table. |
| **1d. Table Auto-Fit** | Applied `w:tblW w:type="pct" w:w="5000"` and `w:tblLayout w:type="autofit"` via `apply_openxml_table_autofit()`. | Inspect `word/document.xml` to confirm `<w:tblLayout w:type="autofit"/>` and 100% margin span. |
| **2. Remove Section 2.3** | Deleted Section 2.3 AST builder and renumbered CMMI & Capabilities sections to `2.3` and `2.4`. | Verify zero occurrences of *"Tres Resultados Ejecutivos del Diagnóstico"* in output DOCX. |
| **3. Uniform `#2E404D` Color** | Replaced `#000000` fallback with `RGBColor(0x2E, 0x40, 0x4D)` in `parse_hex_color()` and `add_markdown_runs()`. | Inspect `w:color w:val="2E404D"` across all body runs, bullets, and table cells in `word/document.xml`. |
| **4. Uniform `10.5pt` Scale** | Standardized `font_size=10.5` across all paragraphs and lists in `build_cmmi_methodology_and_capabilities()`. | Confirm `<w:sz w:val="21"/>` (`10.5pt` in half-points) across Sections 2.3 and 2.4. |