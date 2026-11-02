---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# Architectural Blueprint & Implementation Specification: Executive AS-IS Diagnostic Engine

This document establishes the architectural analysis, exact code design, localization schema updates, and verification oracles for the 8 engineering tasks. Every design decision adheres to Hexagonal Architecture (Ports & Adapters), Single Responsibility Principle (SRP), ISO/IEC 29500-1 OpenXML strict schema compliance, and 100% Technical English source code hygiene.

---

## Task 1: Cover Page Hygiene & Native Bottom Footer Metadata

### A. Architectural Analysis & Problem Decomposition
The current cover page implementation suffers from vertical layout fragility: it uses empty paragraph carriage returns (`w:p`) to push the metadata table toward the bottom margin and injects unnecessary narrative filler blocks beneath the subtitle. If a client's title wraps across multiple lines, the metadata table overflows onto Page 2, breaking the document's visual structure.

**Architectural Solution:**
1. **Decouple Body from Anchor Metadata:** The cover page body (`w:body`) will exclusively render the primary brand header, document category badge, main title, and clean subtitle. All narrative filler is stripped.
2. **Native First-Page Footer Port (`w:ftr`):** Enable `section.different_first_page_header_footer = True` on the primary document section. Route the 4-column executive metadata grid (Client, Scope, Date, Classification) directly into `section.first_page_footer`. Word's layout engine natively pins `w:ftr` to the bottom margin (`section.footer_distance`), guaranteeing zero page-overflow regardless of title length.
3. **Strict OpenXML Table Sequence:** Enforce ISO/IEC 29500-1 schema order inside `CT_TblPr` (`tblStyle` -> `tblW` -> `tblBorders` -> `tblLayout` -> `tblCellMar`) and `CT_TcPr` (`tcW` -> `tcBorders` -> `shd` -> `tcMar` -> `vAlign`).

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/builders/cover_builder.py
from dataclasses import dataclass
from docx.document import Document as DocxDocument
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from src.domain.models.report_context import CoverPageMetadata
from src.infrastructure.docx_adapter.xml_primitives import OpenXmlPrimitives
from src.infrastructure.i18n.translator import Translator


@dataclass(frozen=True)
class CoverTypographySpec:
    category_size_pt: float = 10.0
    title_size_pt: float = 26.0
    subtitle_size_pt: float = 13.0
    meta_label_size_pt: float = 8.0
    meta_value_size_pt: float = 9.0
    footer_distance_cm: float = 1.8


class CoverPageBuilder:
    """Renders a clean executive cover page with native first-page footer metadata."""

    def __init__(
        self,
        translator: Translator,
        xml_primitives: OpenXmlPrimitives,
        spec: CoverTypographySpec = CoverTypographySpec(),
    ) -> None:
        self._i18n = translator
        self._xml = xml_primitives
        self._spec = spec

    def build(self, doc: DocxDocument, metadata: CoverPageMetadata) -> None:
        section = doc.sections[0]
        section.different_first_page_header_footer = True
        section.footer_distance = Cm(self._spec.footer_distance_cm)

        self._render_body_titles(doc, metadata)
        self._render_first_page_footer_metadata(section, metadata)
        doc.add_page_break()

    def _render_body_titles(self, doc: DocxDocument, metadata: CoverPageMetadata) -> None:
        p_cat = doc.add_paragraph()
        p_cat.paragraph_format.space_before = Pt(72)
        p_cat.paragraph_format.space_after = Pt(12)
        r_cat = p_cat.add_run(self._i18n.t("cover.document_category").upper())
        r_cat.font.size = Pt(self._spec.category_size_pt)
        r_cat.font.bold = True
        r_cat.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

        p_title = doc.add_paragraph()
        p_title.paragraph_format.space_before = Pt(0)
        p_title.paragraph_format.space_after = Pt(16)
        r_title = p_title.add_run(metadata.report_title)
        r_title.font.size = Pt(self._spec.title_size_pt)
        r_title.font.bold = True
        r_title.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

        p_sub = doc.add_paragraph()
        p_sub.paragraph_format.space_before = Pt(0)
        p_sub.paragraph_format.space_after = Pt(0)
        r_sub = p_sub.add_run(metadata.report_subtitle)
        r_sub.font.size = Pt(self._spec.subtitle_size_pt)
        r_sub.font.color.rgb = RGBColor(0x47, 0x55, 0x69)

    def _render_first_page_footer_metadata(
        self, section, metadata: CoverPageMetadata
    ) -> None:
        footer = section.first_page_footer
        footer.is_linked_to_previous = False

        # Clear default empty paragraph inside footer
        for p in list(footer.paragraphs):
            p._element.getparent().remove(p._element)

        table = footer.add_table(rows=1, cols=4, width=Cm(17.0))
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        self._xml.enforce_table_fixed_layout(table, total_width_dxa=9639)
        self._xml.set_table_top_border(table, color_hex="CBD5E1", sz_eighths=6)

        items = [
            (self._i18n.t("cover.meta_client"), metadata.organization_name),
            (self._i18n.t("cover.meta_scope"), metadata.assessment_scope),
            (self._i18n.t("cover.meta_date"), metadata.issue_date_iso),
            (self._i18n.t("cover.meta_classification"), metadata.security_classification),
        ]

        col_width_dxa = 9639 // 4
        for idx, (label, value) in enumerate(items):
            cell = table.cell(0, idx)
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP
            self._xml.configure_cell_properties(
                cell,
                width_dxa=col_width_dxa,
                pad_top=120,
                pad_bottom=80,
                pad_left=80 if idx > 0 else 0,
                pad_right=80,
            )
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2)
            r_lbl = p.add_run(f"{label.upper()}\n")
            r_lbl.font.size = Pt(self._spec.meta_label_size_pt)
            r_lbl.font.bold = True
            r_lbl.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

            r_val = p.add_run(value)
            r_val.font.size = Pt(self._spec.meta_value_size_pt)
            r_val.font.bold = False
            r_val.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "cover": {
    "document_category": {
      "es": "Diagnóstico Ejecutivo de Riesgo Operacional y Resiliencia (AS-IS)",
      "en": "Executive Operational Risk & Resilience Diagnostic (AS-IS)"
    },
    "meta_client": {
      "es": "Organización Evaluada",
      "en": "Assessed Organization"
    },
    "meta_scope": {
      "es": "Alcance del Diagnóstico",
      "en": "Diagnostic Scope"
    },
    "meta_date": {
      "es": "Fecha de Emisión",
      "en": "Issue Date"
    },
    "meta_classification": {
      "es": "Clasificación",
      "en": "Classification"
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_cover_builder.py
def test_cover_page_anchors_metadata_in_first_page_footer_and_eliminates_filler(
    docx_document, translator, xml_primitives, sample_cover_metadata
):
    builder = CoverPageBuilder(translator, xml_primitives)
    builder.build(docx_document, sample_cover_metadata)

    section = docx_document.sections[0]
    assert section.different_first_page_header_footer is True

    # Body must contain strictly 4 paragraphs: Category, Title, Subtitle, PageBreak
    body_texts = [p.text.strip() for p in docx_document.paragraphs if p.text.strip()]
    assert len(body_texts) == 3
    assert len(docx_document.tables) == 0  # Zero metadata tables in main body

    # First page footer must contain the 4-column metadata table
    footer_tables = section.first_page_footer.tables
    assert len(footer_tables) == 1
    assert len(footer_tables[0].columns) == 4
    assert sample_cover_metadata.organization_name in footer_tables[0].cell(0, 0).text
```

---

## Task 2: Native Word OpenXML Table of Contents with Dynamic Update

### A. Architectural Analysis & Problem Decomposition
Static tables of contents break when page numbers shift, while bare OpenXML complex fields (`w:fldChar`) display an empty block in non-Word viewers (e.g., macOS QuickLook, LibreOffice headless) until updated.

**Architectural Solution:**
1. **Hybrid Native Field with Pre-Populated Fallback Cache:** Construct a standard ISO/IEC 29500-1 complex field (`w:fldChar fldCharType="begin"` -> `w:instrText` with `TOC \o "1-3" \h \z \u` -> `w:fldChar fldCharType="separate"` -> *Clean Executive Fallback Table* -> `w:fldChar fldCharType="end"`).
2. **Document Settings Flag (`w:updateFields`):** Inject `<w:updateFields w:val="true"/>` into `doc.settings.element`. When Microsoft Word opens the document, it automatically recalculates all page numbers and replaces the fallback cache with live hyperlinked entries; when opened in a passive viewer, the fallback table renders cleanly.

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/builders/toc_builder.py
from typing import Sequence
from dataclasses import dataclass
from docx.document import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from src.infrastructure.i18n.translator import Translator


@dataclass(frozen=True)
class TocEntryPreview:
    section_number: str
    title: str
    level: int


class TableOfContentsBuilder:
    """Builds a native OpenXML TOC field with pre-rendered fallback entries and auto-update flag."""

    def __init__(self, translator: Translator) -> None:
        self._i18n = translator

    def build(self, doc: DocxDocument, preview_entries: Sequence[TocEntryPreview]) -> None:
        self._enable_auto_update_fields(doc)

        h_toc = doc.add_paragraph()
        h_toc.paragraph_format.space_before = Pt(0)
        h_toc.paragraph_format.space_after = Pt(14)
        r_head = h_toc.add_run(self._i18n.t("toc.heading"))
        r_head.font.size = Pt(16)
        r_head.font.bold = True
        r_head.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

        p_field = doc.add_paragraph()
        p_field.paragraph_format.space_after = Pt(6)
        self._inject_toc_field_begin_and_separate(p_field)

        for entry in preview_entries:
            p_item = doc.add_paragraph()
            indent_pt = (entry.level - 1) * 14.0
            p_item.paragraph_format.left_indent = Pt(indent_pt)
            p_item.paragraph_format.space_before = Pt(3 if entry.level == 1 else 1)
            p_item.paragraph_format.space_after = Pt(3 if entry.level == 1 else 1)

            r_num = p_item.add_run(f"{entry.section_number}  ")
            r_num.font.size = Pt(9.5 if entry.level == 1 else 8.5)
            r_num.font.bold = entry.level == 1
            r_num.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

            r_txt = p_item.add_run(entry.title)
            r_txt.font.size = Pt(9.5 if entry.level == 1 else 8.5)
            r_txt.font.bold = entry.level == 1
            r_txt.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

        p_end = doc.add_paragraph()
        self._inject_toc_field_end(p_end)
        doc.add_page_break()

    @staticmethod
    def _inject_toc_field_begin_and_separate(paragraph) -> None:
        run_begin = paragraph.add_run()
        fld_char_begin = OxmlElement("w:fldChar")
        fld_char_begin.set(qn("w:fldCharType"), "begin")
        fld_char_begin.set(qn("w:dirty"), "true")

        instr_text = OxmlElement("w:instrText")
        instr_text.set(qn("xml:space"), "preserve")
        instr_text.text = 'TOC \\o "1-3" \\h \\z \\u'

        fld_char_sep = OxmlElement("w:fldChar")
        fld_char_sep.set(qn("w:fldCharType"), "separate")

        run_begin._r.append(fld_char_begin)
        run_begin._r.append(instr_text)
        run_begin._r.append(fld_char_sep)

    @staticmethod
    def _inject_toc_field_end(paragraph) -> None:
        run_end = paragraph.add_run()
        fld_char_end = OxmlElement("w:fldChar")
        fld_char_end.set(qn("w:fldCharType"), "end")
        run_end._r.append(fld_char_end)

    @staticmethod
    def _enable_auto_update_fields(doc: DocxDocument) -> None:
        settings_el = doc.settings.element
        existing = settings_el.find(qn("w:updateFields"))
        if existing is not None:
            existing.set(qn("w:val"), "true")
            return
        update_fields = OxmlElement("w:updateFields")
        update_fields.set(qn("w:val"), "true")
        settings_el.append(update_fields)
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "toc": {
    "heading": {
      "es": "Índice General de Contenidos",
      "en": "Table of Contents"
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_toc_builder.py
def test_toc_builder_injects_openxml_toc_field_and_update_fields_setting(
    docx_document, translator
):
    builder = TableOfContentsBuilder(translator)
    entries = [
        TocEntryPreview("1.", "Executive Summary", 1),
        TocEntryPreview("4.", "Actuarial Risk Diagnostic", 1),
        TocEntryPreview("A.", "Open FAIR Methodology", 1),
    ]
    builder.build(docx_document, entries)

    xml_body = docx_document._body._body.xml
    assert 'TOC \\o "1-3" \\h \\z \\u' in xml_body
    assert 'w:fldCharType="begin"' in xml_body
    assert 'w:fldCharType="separate"' in xml_body
    assert 'w:fldCharType="end"' in xml_body

    settings_xml = docx_document.settings.element.xml
    assert "<w:updateFields" in settings_xml
    assert 'w:val="true"' in settings_xml
```

---

## Task 3: Chapter 1 (Executive Summary) AS-IS Purity & Actuarial Cross-Reference

### A. Architectural Analysis & Problem Decomposition
Chapter 1 currently contaminates the baseline AS-IS diagnostic with TO-BE investment promises (CAPEX, ROI, Payback) and arbitrary Level 4.0 maturity targets, which belong exclusively to a separate Phase 2 remediation engagement. Furthermore, when the CEO/CFO reads the aggregated Annualized Loss Expectancy (ALE) figure on Page 3, there is no immediate link explaining how that figure was mathematically derived.

**Architectural Solution:**
1. **Pure AS-IS Domain Filtering:** Introduce `ExecutiveSummaryPolicy` in the Domain Layer. Target maturity benchmarks default to industry operational resilience standards (Level 3.0 Defined/Managed) unless `regulatory_mandate_requires_level_4=True` is explicitly set in the tenant profile.
2. **TO-BE Lexicon Sanitization:** Strip all CAPEX, ROI, and Payback metrics from the Chapter 1 data transfer object (`ExecutiveSummaryDto`).
3. **Explicit Actuarial Cross-Reference Banner:** Render a dedicated callout box immediately below the KPI summary table directing the reader to **Chapter 4** (individual asset MTTR and SLE derivations) and **Appendix A** (Open FAIR mathematical taxonomy).

### B. Exact Code Modifications

```python
# File: src/domain/services/executive_summary_policy.py
from dataclasses import dataclass
from decimal import Decimal
from src.domain.models.assessment import AssessmentProfile, ExecutiveSummaryView


@dataclass(frozen=True)
class ExecutiveBenchmarkPolicy:
    DEFAULT_BENCHMARK_LEVEL: Decimal = Decimal("3.0")
    REGULATORY_CRITICAL_LEVEL: Decimal = Decimal("4.0")

    @classmethod
    def resolve_reference_benchmark(cls, profile: AssessmentProfile) -> Decimal:
        if profile.is_nis2_or_dora_critical_entity:
            return cls.REGULATORY_CRITICAL_LEVEL
        return cls.DEFAULT_BENCHMARK_LEVEL


# File: src/infrastructure/docx_adapter/builders/chapter1_executive_builder.py
from docx.document import Document as DocxDocument
from docx.shared import Pt, RGBColor
from src.domain.models.assessment import ExecutiveSummaryView
from src.infrastructure.docx_adapter.xml_primitives import OpenXmlPrimitives
from src.infrastructure.i18n.translator import Translator


class Chapter1ExecutiveSummaryBuilder:
    """Renders Chapter 1 strictly as an AS-IS baseline diagnostic with actuarial cross-referencing."""

    def __init__(self, translator: Translator, xml_primitives: OpenXmlPrimitives) -> None:
        self._i18n = translator
        self._xml = xml_primitives

    def build(self, doc: DocxDocument, summary: ExecutiveSummaryView) -> None:
        self._render_heading(doc)
        self._render_as_is_posture_narrative(doc, summary)
        self._render_kpi_baseline_table(doc, summary)
        self._render_actuarial_cross_reference_callout(doc)

    def _render_actuarial_cross_reference_callout(self, doc: DocxDocument) -> None:
        table = doc.add_table(rows=1, cols=1)
        self._xml.enforce_table_fixed_layout(table, total_width_dxa=9639)
        cell = table.cell(0, 0)
        self._xml.configure_cell_properties(
            cell,
            width_dxa=9639,
            fill_hex="F8FAFC",
            left_border_hex="1E3A8A",
            left_border_sz=18,
            pad_top=100,
            pad_bottom=100,
            pad_left=160,
            pad_right=140,
        )
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)

        r_label = p.add_run(f"{self._i18n.t('ch1.actuarial_xref_title')}: ")
        r_label.font.size = Pt(8.5)
        r_label.font.bold = True
        r_label.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

        r_body = p.add_run(self._i18n.t("ch1.actuarial_xref_body"))
        r_body.font.size = Pt(8.5)
        r_body.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "ch1": {
    "heading": {
      "es": "1. Resumen Ejecutivo: Diagnóstico de Línea Base (AS-IS)",
      "en": "1. Executive Summary: Baseline Diagnostic (AS-IS)"
    },
    "actuarial_xref_title": {
      "es": "Trazabilidad Actuarial y Metodológica",
      "en": "Actuarial & Methodological Traceability"
    },
    "actuarial_xref_body": {
      "es": "Las cifras de exposición financiera anualizada (ALE) reflejan exclusivamente la línea base operativa actual (AS-IS) bajo hipótesis conservadoras de continuidad. El desglose paramétrico por activo (MTTR, coste horario de parada y reposición) se detalla en el Capítulo 4, fundamentado en el modelo cuantitativo Open FAIR descrito en el Apéndice A.",
      "en": "Annualized Loss Expectancy (ALE) figures strictly reflect the current operational baseline (AS-IS) under conservative continuity hypotheses. Asset-level parametric breakdowns (MTTR, hourly downtime cost, and replacement parts) are detailed in Chapter 4, grounded in the Open FAIR quantitative model in Appendix A."
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_chapter1_builder.py
def test_chapter1_contains_zero_to_be_financial_promises_and_includes_xref(
    docx_document, translator, xml_primitives, sample_executive_summary_view
):
    builder = Chapter1ExecutiveSummaryBuilder(translator, xml_primitives)
    builder.build(docx_document, sample_executive_summary_view)

    full_text = "\n".join(p.text for p in docx_document.paragraphs) + "\n".join(
        c.text for t in docx_document.tables for r in t.rows for c in r.cells
    )
    forbidden_terms = ["CAPEX", "ROI", "Payback", "VAN", "NPV", "TIR", "IRR"]
    for term in forbidden_terms:
        assert term not in full_text

    assert translator.t("ch1.actuarial_xref_title") in full_text
    assert "Capítulo 4" in full_text or "Chapter 4" in full_text
    assert "Apéndice A" in full_text or "Appendix A" in full_text
```

---

## Task 4: Chapter 2 (Methodological Framework) Streamlining & Table Typography Harmonization

### A. Architectural Analysis & Problem Decomposition
Chapter 2 previously included a redundant "3-Phase Calibration Roadmap" that duplicated consulting process steps and suffered from inconsistent table font sizes across chapters (ranging from 7.5pt to 11pt).

**Architectural Solution:**
1. **Eliminate 3-Phase Calibration Section:** Restrict Chapter 2 strictly to the Assessment Scope, Maturity Scale Taxonomy (Levels 1–5), and Risk Severity Classification Matrix.
2. **Centralized `TableTypographyStylist`:** Create a single immutable styling service that enforces exact typography across all report tables:
   - Table Headers: **9.0 pt Bold** (`#FFFFFF` on `#0F172A` or `#1E293B`)
   - Standard Data Cells: **8.5 pt Regular** (`#1E293B`)
   - Pill / Status Badges: **8.0 pt Bold**

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/stylists/table_typography_stylist.py
from dataclasses import dataclass
from docx.shared import Pt, RGBColor
from docx.text.run import Run


@dataclass(frozen=True)
class UnifiedTableTypographySpec:
    header_font_pt: float = 9.0
    cell_font_pt: float = 8.5
    badge_font_pt: float = 8.0
    font_family: str = "Calibri"


class TableTypographyStylist:
    """Enforces unified table typography (9.0pt headers, 8.5pt cells, 8.0pt badges) report-wide."""

    def __init__(self, spec: UnifiedTableTypographySpec = UnifiedTableTypographySpec()) -> None:
        self._spec = spec

    def style_header_run(
        self, run: Run, color: RGBColor = RGBColor(0xFF, 0xFF, 0xFF)
    ) -> None:
        run.font.name = self._spec.font_family
        run.font.size = Pt(self._spec.header_font_pt)
        run.font.bold = True
        run.font.color.rgb = color

    def style_cell_run(
        self,
        run: Run,
        bold: bool = False,
        color: RGBColor = RGBColor(0x1E, 0x29, 0x3B),
    ) -> None:
        run.font.name = self._spec.font_family
        run.font.size = Pt(self._spec.cell_font_pt)
        run.font.bold = bold
        run.font.color.rgb = color

    def style_badge_run(
        self, run: Run, color: RGBColor = RGBColor(0x0F, 0x17, 0x2A)
    ) -> None:
        run.font.name = self._spec.font_family
        run.font.size = Pt(self._spec.badge_font_pt)
        run.font.bold = True
        run.font.color.rgb = color
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "ch2": {
    "heading": {
      "es": "2. Marco Metodológico y Escala de Madurez Operativa",
      "en": "2. Methodological Framework & Operational Maturity Scale"
    },
    "maturity_table_headers": {
      "level": { "es": "Nivel", "en": "Level" },
      "designation": { "es": "Denominación", "en": "Designation" },
      "operational_definition": { "es": "Criterio de Evidencia Operativa (AS-IS)", "en": "Operational Evidence Criteria (AS-IS)" }
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_table_typography_stylist.py
from docx.shared import Pt

def test_chapter2_tables_strictly_comply_with_9_0_8_5_8_0_typography_and_omit_calibration(
    docx_document, chapter2_builder, sample_methodology_context
):
    chapter2_builder.build(docx_document, sample_methodology_context)

    body_text = "\n".join(p.text for p in docx_document.paragraphs)
    assert "Calibración en 3 Fases" not in body_text
    assert "3-Phase Calibration" not in body_text

    for table in docx_document.tables:
        for col_idx, cell in enumerate(table.rows[0].cells):
            for p in cell.paragraphs:
                for run in p.runs:
                    assert run.font.size == Pt(9.0)
                    assert run.font.bold is True

        for row in table.rows[1:]:
            for cell in row.cells:
                for p in cell.paragraphs:
                    for run in p.runs:
                        assert run.font.size in (Pt(8.5), Pt(8.0))
```

---

## Task 5: Pre-Flight Actuarial CFO Audit Gate & Grounded Realism

### A. Architectural Analysis & Problem Decomposition
A CFO will immediately reject a diagnostic report if:
1. A cold-boot infrastructure recovery or physical component swap claims an impossible `< 1.5 hour` MTTR.
2. Total Annualized Loss Expectancy (ALE) exceeds reasonable operational revenue ceilings or double-counts shared cascading bottlenecks.
3. The Tower 1 reference dataset exhibits uncalibrated figures instead of the audited **118,500 EUR/yr** baseline.

**Architectural Solution:**
1. **Pure Domain Neuro-Symbolic Validator (`PreFlightActuarialAuditGate`):** Runs before any OpenXML generation begins. It validates every `RiskFindingScenario`:
   - **Physical/Cold-Restart MTTR Floor:** Enforces `1.5h <= MTTR` (and `>= 4.0h` for full bare-metal restoration unless hot-standby is proven in AS-IS evidence).
   - **Exact Parametric Equality:** Verifies $\text{SLE} = (\text{MTTR}_{\text{hours}} \times \text{HourlyDowntimeCost}) + \text{ReplacementCost}$ and $\text{ALE} = \text{SLE} \times \text{ARO}$.
   - **Zero Cascade Double-Counting:** Verifies that shared downstream outage hours are attributed solely to the primary root-cause asset.
   - **Revenue Ceiling Guard:** Enforces $\sum \text{ALE} \le \text{AnnualRevenue} \times \text{MaxExposureRatio}$.
2. **Recalibrated Tower 1 Baseline Fixture:** Sums strictly to **118,500.00 EUR/yr** across the 5 audited operational scenarios.

### B. Exact Code Modifications

```python
# File: src/domain/services/actuarial_audit_gate.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Sequence
from src.domain.exceptions import ActuarialAuditGateViolationError
from src.domain.models.risk_scenario import RiskScenario, RecoveryClass


@dataclass(frozen=True)
class ActuarialAuditPolicy:
    min_hot_swap_mttr_hours: Decimal = Decimal("1.5")
    min_cold_rebuild_mttr_hours: Decimal = Decimal("4.0")
    max_ale_to_revenue_ratio: Decimal = Decimal("0.15")
    forbidden_certainty_tokens: tuple[str, ...] = (
        "garantiza",
        "guarantees",
        "100% seguro",
        "100% certain",
        "inevitablemente causará",
    )


class PreFlightActuarialAuditGate:
    """CFO Pre-Flight Neuro-Symbolic Validator for actuarial realism and mathematical integrity."""

    def __init__(self, policy: ActuarialAuditPolicy = ActuarialAuditPolicy()) -> None:
        self._policy = policy

    def verify_portfolio(
        self,
        scenarios: Sequence[RiskScenario],
        annual_enterprise_revenue: Decimal,
    ) -> None:
        if annual_enterprise_revenue <= Decimal("0"):
            raise ActuarialAuditGateViolationError(
                "Annual enterprise revenue must be strictly positive."
            )

        seen_cascade_domains: set[str] = set()
        total_portfolio_ale = Decimal("0.00")

        for scenario in scenarios:
            self._verify_mttr_floor(scenario)
            self._verify_parametric_formula_identity(scenario)
            self._verify_zero_cascade_double_counting(scenario, seen_cascade_domains)
            self._verify_probabilistic_hypothesis_tone(scenario)
            total_portfolio_ale += scenario.ale_amount

        max_allowed_ale = (
            annual_enterprise_revenue * self._policy.max_ale_to_revenue_ratio
        )
        if total_portfolio_ale > max_allowed_ale:
            raise ActuarialAuditGateViolationError(
                f"Portfolio ALE ({total_portfolio_ale}) exceeds CFO credibility ceiling "
                f"({max_allowed_ale}) for annual revenue {annual_enterprise_revenue}."
            )

    def _verify_mttr_floor(self, scenario: RiskScenario) -> None:
        floor = (
            self._policy.min_cold_rebuild_mttr_hours
            if scenario.recovery_class == RecoveryClass.COLD_REBUILD
            else self._policy.min_hot_swap_mttr_hours
        )
        if scenario.mttr_hours < floor:
            raise ActuarialAuditGateViolationError(
                f"Scenario '{scenario.scenario_id}' violates MTTR realism floor: "
                f"{scenario.mttr_hours}h < {floor}h ({scenario.recovery_class.value})."
            )

    @staticmethod
    def _verify_parametric_formula_identity(scenario: RiskScenario) -> None:
        expected_sle = (
            scenario.mttr_hours * scenario.hourly_downtime_cost
        ) + scenario.direct_replacement_cost
        if expected_sle.quantize(Decimal("0.01")) != scenario.sle_amount.quantize(
            Decimal("0.01")
        ):
            raise ActuarialAuditGateViolationError(
                f"Scenario '{scenario.scenario_id}' SLE mismatch: "
                f"expected {expected_sle}, got {scenario.sle_amount}."
            )

        expected_ale = (scenario.sle_amount * scenario.aro_frequency).quantize(
            Decimal("0.01")
        )
        if expected_ale != scenario.ale_amount.quantize(Decimal("0.01")):
            raise ActuarialAuditGateViolationError(
                f"Scenario '{scenario.scenario_id}' ALE mismatch: "
                f"expected {expected_ale}, got {scenario.ale_amount}."
            )

    @staticmethod
    def _verify_zero_cascade_double_counting(
        scenario: RiskScenario, seen_domains: set[str]
    ) -> None:
        if scenario.primary_cascade_domain_id in seen_domains:
            raise ActuarialAuditGateViolationError(
                f"Double-counted cascade domain '{scenario.primary_cascade_domain_id}' "
                f"in scenario '{scenario.scenario_id}'."
            )
        seen_domains.add(scenario.primary_cascade_domain_id)

    def _verify_probabilistic_hypothesis_tone(self, scenario: RiskScenario) -> None:
        text_lower = scenario.narrative_hypothesis.lower()
        for token in self._policy.forbidden_certainty_tokens:
            if token in text_lower:
                raise ActuarialAuditGateViolationError(
                    f"Scenario '{scenario.scenario_id}' contains deterministic certainty token '{token}'."
                )
```

**Recalibrated Tower 1 Baseline Portfolio (`118,500.00 EUR/yr`):**
- `RSK-01` (Core Switching SPOF): $\text{MTTR} = 4.0\text{h} \times 6,500\text{ EUR/h} + 4,000\text{ EUR parts} = 30,000\text{ EUR SLE} \times 1.2\text{ ARO} = \mathbf{36,000\text{ EUR/yr}}$
- `RSK-02` (Legacy Hypervisor Storage): $\text{MTTR} = 6.0\text{h} \times 5,000\text{ EUR/h} + 5,000\text{ EUR parts} = 35,000\text{ EUR SLE} \times 0.9\text{ ARO} = \mathbf{31,500\text{ EUR/yr}}$
- `RSK-03` (OT/SCADA Flat Network Segmentation): $\text{MTTR} = 5.0\text{h} \times 4,800\text{ EUR/h} + 2,000\text{ EUR parts} = 26,000\text{ EUR SLE} \times 1.0\text{ ARO} = \mathbf{26,000\text{ EUR/yr}}$
- `RSK-04` (Immutable Backup Gap / Cold Restore): $\text{MTTR} = 8.0\text{h} \times 3,500\text{ EUR/h} + 0\text{ EUR parts} = 28,000\text{ EUR SLE} \times 0.5\text{ ARO} = \mathbf{14,000\text{ EUR/yr}}$
- `RSK-05` (Single ISP / Perimeter Gateway SPOF): $\text{MTTR} = 2.5\text{h} \times 4,000\text{ EUR/h} + 1,000\text{ EUR parts} = 11,000\text{ EUR SLE} \times 1.0\text{ ARO} = \mathbf{11,000\text{ EUR/yr}}$
- **Total Audited Portfolio ALE:** $36,000 + 31,500 + 26,000 + 14,000 + 11,000 = \mathbf{118,500.00\text{ EUR/yr}}$.

### C. Universal Localization Keys (`locales.json`)

```json
{
  "actuarial_gate": {
    "hypothesis_disclaimer": {
      "es": "Estimación paramétrica bajo hipótesis conservadora de interrupción operativa (Open FAIR).",
      "en": "Parametric estimate under conservative operational interruption hypothesis (Open FAIR)."
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/domain/test_actuarial_audit_gate.py
import pytest
from decimal import Decimal
from src.domain.services.actuarial_audit_gate import PreFlightActuarialAuditGate
from src.domain.exceptions import ActuarialAuditGateViolationError

def test_tower1_baseline_portfolio_passes_audit_gate_and_equals_118500_eur(
    tower1_calibrated_scenarios,
):
    gate = PreFlightActuarialAuditGate()
    gate.verify_portfolio(
        scenarios=tower1_calibrated_scenarios,
        annual_enterprise_revenue=Decimal("15000000.00"),
    )
    total_ale = sum(s.ale_amount for s in tower1_calibrated_scenarios)
    assert total_ale == Decimal("118500.00")

def test_audit_gate_rejects_unrealistic_sub_1_5h_mttr(tower1_calibrated_scenarios):
    gate = PreFlightActuarialAuditGate()
    corrupted = tower1_calibrated_scenarios[0].with_mttr(Decimal("0.5"))
    with pytest.raises(ActuarialAuditGateViolationError, match="MTTR realism floor"):
        gate.verify_portfolio([corrupted], Decimal("15000000.00"))
```

---

## Task 6: Chapter 4 (Risk Section) Mini-Infographic Card Re-Engineering

### A. Architectural Analysis & Problem Decomposition
The legacy Chapter 4 risk cards suffered from:
1. Visual clutter from a 6-axis radar/hexagon chart repeated per finding.
2. Congested multi-badge card headers and alarming neon red fills.
3. Generic cybersecurity dictionary boilerplate ("What is a SPOF?").
4. Premature TO-BE mitigation directives inside an AS-IS diagnostic card.

**Architectural Solution:**
1. **Remove Per-Card Hexagon Chart:** Eliminate all matplotlib radar chart generation from `RiskCardBuilder`.
2. **Decongested Executive Header & Muted Palette:** Use a clean 2-column header bar (`[ID + Title]` on the left, `[Muted Severity Badge + Annualized ALE]` on the right) with executive slate/navy/ochre tones (`#0F172A`, `#F8FAFC`, `#991B1B` muted crimson text on `#FEF2F2` subtle tint).
3. **Actuarial Derivation Formula Box:** Replace the TO-BE mitigation box with the explicit mathematical proof of the card's financial exposure:
   $$\text{SLE} = (\text{MTTR} \times \text{Coste Horario}) + \text{Reposición} \quad \longrightarrow \quad \text{ALE} = \text{SLE} \times \text{ARO}$$
4. **Plain-Language Operational Cascade Effect:** Replace generic threat definitions with a concrete, business-specific **Efecto Cascada Operativo** block written in probabilistic hypothesis language.

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/builders/risk_card_builder.py
from docx.document import Document as DocxDocument
from docx.shared import Pt, RGBColor
from src.domain.models.risk_scenario import RiskScenario
from src.infrastructure.docx_adapter.stylists.table_typography_stylist import (
    TableTypographyStylist,
)
from src.infrastructure.docx_adapter.xml_primitives import OpenXmlPrimitives
from src.infrastructure.i18n.translator import Translator
from src.infrastructure.formatting.currency_formatter import CurrencyFormatter


class ExecutiveRiskCardBuilder:
    """Renders a clean, single-block AS-IS executive risk card with an Actuarial Derivation Formula Box."""

    def __init__(
        self,
        translator: Translator,
        xml_primitives: OpenXmlPrimitives,
        stylist: TableTypographyStylist,
        currency_formatter: CurrencyFormatter,
    ) -> None:
        self._i18n = translator
        self._xml = xml_primitives
        self._stylist = stylist
        self._currency = currency_formatter

    def render_card(self, doc: DocxDocument, scenario: RiskScenario) -> None:
        card = doc.add_table(rows=4, cols=2)
        self._xml.enforce_table_fixed_layout(card, total_width_dxa=9639)
        self._xml.set_table_outer_border(card, color_hex="CBD5E1", sz_eighths=6)
        self._xml.keep_table_together_on_page(card)

        # Row 0: Decongested Header (Left: ID + Asset Title | Right: Muted Severity Pill + ALE)
        self._render_header_row(card.rows[0], scenario)

        # Row 1: Empirical AS-IS Observation & Plain-Language Operational Cascade Effect
        self._render_evidence_and_cascade_row(card.rows[1], scenario)

        # Row 2: Actuarial Derivation Formula Box (SLE = MTTR * Hourly Cost + Parts -> ALE)
        self._render_actuarial_derivation_box(card.rows[2], scenario)

        # Row 3: Probabilistic Hypothesis Footnote
        self._render_hypothesis_footer(card.rows[3], scenario)

        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after = Pt(10)

    def _render_actuarial_derivation_box(self, row, scenario: RiskScenario) -> None:
        cell = row.cells[0].merge(row.cells[1])
        self._xml.configure_cell_properties(
            cell,
            width_dxa=9639,
            fill_hex="F1F5F9",
            pad_top=90,
            pad_bottom=90,
            pad_left=140,
            pad_right=140,
        )
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)

        r_title = p.add_run(f"{self._i18n.t('risk_card.actuarial_formula_label')}: ")
        self._stylist.style_cell_run(
            r_title, bold=True, color=RGBColor(0x0F, 0x17, 0x2A)
        )

        sle_str = self._currency.format(scenario.sle_amount)
        ale_str = self._currency.format(scenario.ale_amount)
        hr_str = self._currency.format(scenario.hourly_downtime_cost)
        parts_str = self._currency.format(scenario.direct_replacement_cost)

        formula_text = (
            f"SLE = ({scenario.mttr_hours}h MTTR × {hr_str}/h) + {parts_str} = {sle_str}   |   "
            f"ALE = {sle_str} × {scenario.aro_frequency} ARO = {ale_str}/yr"
        )
        r_math = p.add_run(formula_text)
        self._stylist.style_cell_run(
            r_math, bold=False, color=RGBColor(0x1E, 0x3A, 0x8A)
        )
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "risk_card": {
    "empirical_evidence_label": {
      "es": "Evidencia Empírica Observada (AS-IS)",
      "en": "Observed Empirical Evidence (AS-IS)"
    },
    "cascade_effect_label": {
      "es": "Efecto Cascada en Operaciones",
      "en": "Operational Cascade Effect"
    },
    "actuarial_formula_label": {
      "es": "Derivación Actuarial de Exposición (Open FAIR)",
      "en": "Actuarial Exposure Derivation (Open FAIR)"
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_risk_card_builder.py
def test_risk_card_renders_actuarial_formula_box_and_omits_hexagon_and_to_be_directives(
    docx_document, risk_card_builder, tower1_calibrated_scenarios
):
    scenario = tower1_calibrated_scenarios[0]
    risk_card_builder.render_card(docx_document, scenario)

    assert len(docx_document.inline_shapes) == 0  # Zero radar/hexagon images
    card_text = "\n".join(
        c.text for t in docx_document.tables for r in t.rows for c in r.cells
    )
    assert "SLE =" in card_text
    assert "MTTR ×" in card_text
    assert "ALE =" in card_text
    assert "Directiva de Mitigación" not in card_text
    assert "Mitigation Directive" not in card_text
```

---

## Task 7: Chapter 5 (Conclusions) Transformation into Pure AS-IS Diagnostic Synthesis

### A. Architectural Analysis & Problem Decomposition
Chapter 5 previously presented a 3-Horizon Investment & ROI/Payback table, violating the boundary between an independent AS-IS Risk Diagnostic and a commercial TO-BE Remediation Proposal.

**Architectural Solution:**
Replace the investment roadmap with a pure **AS-IS Diagnostic Synthesis** structured into three executive blocks:
1. **Structural Maturity Posture Summary:** Synthesizes the gap between observed AS-IS maturity across domains and the operational resilience baseline.
2. **Critical Vulnerability Concentration Matrix:** Groups the total **118,500 EUR/yr** ALE by failure topology (e.g., Single Points of Failure, Recovery Gap, Network Contagion) showing percentage concentration of financial risk.
3. **Operational Urgency by Asset Criticality:** Categorizes the diagnosed operational bottlenecks by their tolerance window before cascading business interruption occurs, without prescribing commercial product quotes or CAPEX figures.

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/builders/chapter5_conclusions_builder.py
from typing import Sequence
from decimal import Decimal
from docx.document import Document as DocxDocument
from src.domain.models.risk_scenario import RiskScenario
from src.infrastructure.docx_adapter.stylists.table_typography_stylist import (
    TableTypographyStylist,
)
from src.infrastructure.docx_adapter.xml_primitives import OpenXmlPrimitives
from src.infrastructure.i18n.translator import Translator
from src.infrastructure.formatting.currency_formatter import CurrencyFormatter


class Chapter5DiagnosticSynthesisBuilder:
    """Renders Chapter 5 strictly as an AS-IS Diagnostic Synthesis without TO-BE CAPEX/ROI tables."""

    def __init__(
        self,
        translator: Translator,
        xml_primitives: OpenXmlPrimitives,
        stylist: TableTypographyStylist,
        currency_formatter: CurrencyFormatter,
    ) -> None:
        self._i18n = translator
        self._xml = xml_primitives
        self._stylist = stylist
        self._currency = currency_formatter

    def build(self, doc: DocxDocument, scenarios: Sequence[RiskScenario]) -> None:
        self._render_heading(doc)
        self._render_maturity_posture_synthesis(doc, scenarios)
        self._render_vulnerability_concentration_matrix(doc, scenarios)
        self._render_operational_urgency_synthesis(doc, scenarios)

    def _render_vulnerability_concentration_matrix(
        self, doc: DocxDocument, scenarios: Sequence[RiskScenario]
    ) -> None:
        total_ale = sum((s.ale_amount for s in scenarios), Decimal("0.00"))
        # Safe zero-division guard
        denominator = total_ale if total_ale > Decimal("0.00") else Decimal("1.00")

        table = doc.add_table(rows=1, cols=4)
        self._xml.enforce_table_fixed_layout(table, total_width_dxa=9639)
        headers = [
            self._i18n.t("ch5.col_failure_domain"),
            self._i18n.t("ch5.col_finding_count"),
            self._i18n.t("ch5.col_annual_exposure"),
            self._i18n.t("ch5.col_risk_share"),
        ]
        for idx, h_text in enumerate(headers):
            cell = table.rows[0].cells[idx]
            self._xml.configure_cell_properties(
                cell, width_dxa=2409, fill_hex="0F172A"
            )
            r = cell.paragraphs[0].add_run(h_text)
            self._stylist.style_header_run(r)

        for scenario in scenarios:
            row_cells = table.add_row().cells
            share_pct = (scenario.ale_amount / denominator) * Decimal("100.0")
            values = [
                scenario.primary_cascade_domain_id,
                "1",
                self._currency.format(scenario.ale_amount),
                f"{share_pct:.1f}%",
            ]
            for idx, val in enumerate(values):
                self._xml.configure_cell_properties(row_cells[idx], width_dxa=2409)
                r = row_cells[idx].paragraphs[0].add_run(val)
                self._stylist.style_cell_run(r, bold=(idx == 0))
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "ch5": {
    "heading": {
      "es": "5. Conclusiones y Síntesis del Diagnóstico (AS-IS)",
      "en": "5. Conclusions & Baseline Diagnostic Synthesis (AS-IS)"
    },
    "col_failure_domain": {
      "es": "Dominio de Fragilidad Operativa",
      "en": "Operational Fragility Domain"
    },
    "col_finding_count": {
      "es": "Vectores Críticos",
      "en": "Critical Vectors"
    },
    "col_annual_exposure": {
      "es": "Exposición Anualizada (ALE)",
      "en": "Annualized Exposure (ALE)"
    },
    "col_risk_share": {
      "es": "Concentración de Riesgo (%)",
      "en": "Risk Concentration (%)"
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_chapter5_builder.py
def test_chapter5_synthesizes_as_is_concentration_and_excludes_capex_roi_tables(
    docx_document, chapter5_builder, tower1_calibrated_scenarios
):
    chapter5_builder.build(docx_document, tower1_calibrated_scenarios)

    all_text = "\n".join(p.text for p in docx_document.paragraphs) + "\n".join(
        c.text for t in docx_document.tables for r in t.rows for c in r.cells
    )
    for forbidden in ["CAPEX", "ROI", "Payback", "Horizonte 1", "Horizon 1", "Inversión Estimada"]:
        assert forbidden not in all_text

    assert "118.500" in all_text or "118,500" in all_text
    assert "%" in all_text
```

---

## Task 8: Appendices Cleanup & Single Technical Appendix

### A. Architectural Analysis & Problem Decomposition
The document previously included a forensic "Chain of Custody Log" as Appendix A and relegated the Open FAIR Actuarial Methodology to Appendix B. For a C-level operational risk diagnostic, a forensic evidence hash table adds unrequested noise and creates confusion when Chapter 1 cross-references the actuarial methodology.

**Architectural Solution:**
1. **Remove Custody Log Builder:** Delete `AppendixCustodyBuilder` from the document assembly pipeline.
2. **Promote Open FAIR Methodology to Single Primary `Appendix A`:** Re-index the Open FAIR Quantitative Risk Taxonomy (Loss Event Frequency, Threat Event Frequency, Vulnerability, Single Loss Expectancy, MTTR parametric equations, and Annualized Loss Expectancy) as **Appendix A**, aligning with the cross-reference banner in Chapter 1 and the Table of Contents in Task 2.

### B. Exact Code Modifications

```python
# File: src/infrastructure/docx_adapter/builders/appendix_open_fair_builder.py
from docx.document import Document as DocxDocument
from docx.shared import Pt, RGBColor
from src.infrastructure.docx_adapter.stylists.table_typography_stylist import (
    TableTypographyStylist,
)
from src.infrastructure.docx_adapter.xml_primitives import OpenXmlPrimitives
from src.infrastructure.i18n.translator import Translator


class AppendixAOpenFairBuilder:
    """Renders the single primary technical appendix: Appendix A — Open FAIR Actuarial Methodology."""

    def __init__(
        self,
        translator: Translator,
        xml_primitives: OpenXmlPrimitives,
        stylist: TableTypographyStylist,
    ) -> None:
        self._i18n = translator
        self._xml = xml_primitives
        self._stylist = stylist

    def build(self, doc: DocxDocument) -> None:
        doc.add_page_break()
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(0)
        h.paragraph_format.space_after = Pt(12)
        r = h.add_run(self._i18n.t("appendix_a.heading"))
        r.font.size = Pt(16)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

        p_intro = doc.add_paragraph()
        p_intro.paragraph_format.space_after = Pt(10)
        r_intro = p_intro.add_run(self._i18n.t("appendix_a.intro_narrative"))
        r_intro.font.size = Pt(9.5)
        r_intro.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

        self._render_open_fair_taxonomy_table(doc)

    def _render_open_fair_taxonomy_table(self, doc: DocxDocument) -> None:
        table = doc.add_table(rows=1, cols=3)
        self._xml.enforce_table_fixed_layout(table, total_width_dxa=9639)

        headers = [
            self._i18n.t("appendix_a.col_parameter"),
            self._i18n.t("appendix_a.col_formula"),
            self._i18n.t("appendix_a.col_audit_definition"),
        ]
        widths = [2200, 2800, 4639]
        for idx, text in enumerate(headers):
            cell = table.rows[0].cells[idx]
            self._xml.configure_cell_properties(
                cell, width_dxa=widths[idx], fill_hex="0F172A"
            )
            run = cell.paragraphs[0].add_run(text)
            self._stylist.style_header_run(run)

        rows_data = [
            (
                "MTTR",
                "T_detect + T_diagnose + T_restore",
                self._i18n.t("appendix_a.def_mttr"),
            ),
            (
                "SLE",
                "(MTTR × Cost_hr) + Cost_parts",
                self._i18n.t("appendix_a.def_sle"),
            ),
            (
                "ARO",
                "TEF × Vuln_prob",
                self._i18n.t("appendix_a.def_aro"),
            ),
            (
                "ALE",
                "SLE × ARO",
                self._i18n.t("appendix_a.def_ale"),
            ),
        ]
        for param, formula, definition in rows_data:
            row_cells = table.add_row().cells
            for idx, val in enumerate((param, formula, definition)):
                self._xml.configure_cell_properties(
                    row_cells[idx], width_dxa=widths[idx]
                )
                run = row_cells[idx].paragraphs[0].add_run(val)
                self._stylist.style_cell_run(run, bold=(idx == 0))
```

### C. Universal Localization Keys (`locales.json`)

```json
{
  "appendix_a": {
    "heading": {
      "es": "Apéndice A: Metodología Actuarial Open FAIR y Modelo Paramétrico",
      "en": "Appendix A: Open FAIR Actuarial Methodology & Parametric Model"
    },
    "intro_narrative": {
      "es": "La cuantificación financiera de los escenarios de riesgo operativo de este diagnóstico se fundamenta en el estándar internacional Open FAIR (Factor Analysis of Information Risk, ISO/IEC 27005 compatible).",
      "en": "The financial quantification of operational risk scenarios in this diagnostic is grounded in the international Open FAIR standard (Factor Analysis of Information Risk, ISO/IEC 27005 compatible)."
    },
    "col_parameter": { "es": "Parámetro", "en": "Parameter" },
    "col_formula": { "es": "Ecuación Paramétrica", "en": "Parametric Equation" },
    "col_audit_definition": { "es": "Definición Actuarial (AS-IS)", "en": "Actuarial Definition (AS-IS)" },
    "def_mttr": {
      "es": "Tiempo medio empírico de restauración operativa desde el inicio del fallo hasta la verificación funcional.",
      "en": "Empirical mean time to operational restoration from failure onset to functional verification."
    },
    "def_sle": {
      "es": "Pérdida financiera primaria y secundaria estimada por cada evento de interrupción individual.",
      "en": "Estimated primary and secondary financial loss per single interruption event."
    },
    "def_aro": {
      "es": "Frecuencia anualizada estimada de materialización del evento bajo la arquitectura actual.",
      "en": "Estimated annualized rate of occurrence under the current baseline architecture."
    },
    "def_ale": {
      "es": "Exposición financiera anualizada agregada atribuible al vector de fragilidad diagnosticado.",
      "en": "Aggregated annualized financial exposure attributable to the diagnosed fragility vector."
    }
  }
}
```

### D. Verification Oracle

```python
# File: tests/unit/infrastructure/test_appendix_builder.py
def test_single_appendix_a_renders_open_fair_and_excludes_custody_log(
    docx_document, report_orchestrator, sample_report_context
):
    report_orchestrator.generate(docx_document, sample_report_context)

    full_text = "\n".join(p.text for p in docx_document.paragraphs)
    assert "Apéndice A:" in full_text or "Appendix A:" in full_text
    assert "Open FAIR" in full_text
    assert "Apéndice B" not in full_text
    assert "Appendix B" not in full_text
    assert "Cadena de Custodia" not in full_text
    assert "Chain of Custody" not in full_text
```

---

## Execution & Sequential Quality Control Protocol

As instructed, implementation will proceed sequentially from **Task 1 through Task 8**. Upon completing each task, the following automated verification gate will be executed before advancing to the next task:

1. **Static Typing & English-Only Hygiene Check:** `mypy --strict src/ tests/` + AST scanner verifying zero non-English identifiers or string literals in `.py` files.
2. **ISO/IEC 29500-1 OpenXML Schema Validation:** XPath verification ensuring strict child element ordering inside every `<w:tblPr>` and `<w:tcPr>` node.
3. **Unit & CFO Actuarial Gate Suite:** `pytest -v` verifying exact mathematical parity ($\text{ALE} = 118,500.00\text{ EUR/yr}$) and 100% AS-IS purity.