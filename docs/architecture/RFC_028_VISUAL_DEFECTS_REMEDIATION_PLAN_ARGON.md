# RFC 028: Visual Forensic Remediation & Word OpenXML Layout Perfection

**Status:** APPROVED FOR IMMEDIATE IMPLEMENTATION  
**Author:** Principal Systems Architect & Chief Compiler Engineer  
**Target Modules:**
- `assessment_engine/domain/schemas/ast.py`
- `assessment_engine/adapters/transformers/payload_to_ast.py`
- `assessment_engine/adapters/compilers/docx_compiler.py`
- `assessment_engine/domain/taxonomy_resolver.py`
- `assessment_engine/i18n/locales.json`

---

## 1. Executive Summary

A visual forensic audit of the generated Word/PDF deliverables revealed five structural and typographic defects that compromise C-level editorial polish:

1. **Cover Page Split Across Two Pages:** Cover subtitles are emitted as `HeadingNode(level=1)`, which triggers a hard `page_break_before = True` in `docx_compiler.py` and pollutes the Word outline/numbering sequence.
2. **Non-Native Table of Contents & Desynchronized Page Numbers:** The Table of Contents is rendered as static paragraphs using hardcoded page strings from `locales.json` instead of a native OpenXML `<w:sdt>` (Structured Document Tag) + `TOC \o "1-3" \h \z \u` complex field with `w:dirty="true"` and `<w:updateFields w:val="true"/>`.
3. **Duplicate Heading Numbering (`2. 1. Resumen Ejecutivo`):** `tower_annex_template.docx` already configures multi-level auto-numbering on `Heading 1`, `Heading 2`, and `Heading 3`. Passing strings with pre-baked numeric prefixes (`"1. Resumen..."`) causes double-numbering AND increments the `Heading 1` counter on the cover page.
4. **Pillar Name Resolution Collapse (`Pillar`):** Section 3.2 looks up `pillar_id` and `pillar_name`, whereas upstream payloads also emit `pilar_id` and `pilar_name` (single `'l'`).
5. **Raw KPI Codes in Risk Card Headers (`[RVS03] T1.P2.K1`):** `TaxonomyResolver.resolve_capability_name()` checks `_capabilities_index` and `_pillars_index`, but fails to index and resolve KPI/sub-capability codes (`T1.P2.K1`) from `taxonomy_multilingual.json`.

This RFC specifies deterministic, zero-hardcoding, OpenXML-compliant fixes for all five defects in 100% Technical English.

---

## 2. Surgical Architectural Design & Code Specifications

### 2.1. Defect 1: Cover Page Containment on Page 1

#### Root Cause Analysis
In `payload_to_ast.py` (`_build_cover_and_toc`), the cover page subtitle (`"Technical Annex: Physical Data Center..."`) is emitted as `HeadingNode(level=1)`. In `docx_compiler.py` (`_compile_heading`), every `level == 1` heading sets `p.paragraph_format.page_break_before = True` and applies the `Heading 1` style. This has two destructive side effects:
1. It forces a page break right in the middle of the cover page, pushing the subtitle and client metadata onto Page 2.
2. Because `Heading 1` has automatic numbering in `tower_annex_template.docx`, the cover subtitle consumes number `1.`, causing Chapter 1 ("Resumen Ejecutivo") to be numbered `2.`!

#### Architectural Fix
1. Replace the cover subtitle `HeadingNode(level=1)` in `_build_cover_and_toc()` with a dedicated `ParagraphNode(style="cover_subtitle")`.
2. In `docx_compiler.py` (`_compile_paragraph`), handle `style == "cover_subtitle"` with executive typography (18pt, bold, primary corporate navy `#002060`, `page_break_before = False`, `keep_with_next = True`, and zero outline level so it never enters the TOC or increments `Heading 1` counters).

#### Production Code (`payload_to_ast.py` & `docx_compiler.py`)

```python
# In assessment_engine/adapters/transformers/payload_to_ast.py

def _build_cover_and_toc(
    self,
    payload: dict[str, Any],
    tower_id: str,
    lang: str,
) -> list[ASTNode]:
    """Build strictly contained Page 1 Cover and Page 2 Native TOC."""
    nodes: list[ASTNode] = []

    raw_client = payload.get("client_name") or payload.get("client") or ""
    client_display = clean_client_name(str(raw_client))
    title_main = t("cover.main_title", lang)
    subtitle_text = self._resolve_tower_subtitle(payload, tower_id, lang)

    # Main Cover Title (Strictly on Page 1, no outline level)
    nodes.append(
        ParagraphNode(
            text=title_main,
            style="cover_title",
            bold=True,
        )
    )

    # Cover Subtitle (ParagraphNode with 'cover_subtitle' instead of HeadingNode)
    nodes.append(
        ParagraphNode(
            text=subtitle_text,
            style="cover_subtitle",
            bold=True,
        )
    )

    nodes.append(SpacerNode(height_pt=24))

    # Client & Date Metadata Block (Remains on Page 1)
    if client_display:
        client_label = t("cover.client_label", lang)
        nodes.append(
            ParagraphNode(
                text=f"{client_label}: {client_display}",
                style="cover_meta",
                bold=True,
            )
        )

    date_str = format_date_localized(payload.get("assessment_date"), lang)
    if date_str:
        date_label = t("cover.date_label", lang)
        nodes.append(
            ParagraphNode(
                text=f"{date_label}: {date_str}",
                style="cover_meta",
            )
        )

    # Explicit Page Break after Cover Page so TOC begins cleanly on Page 2
    nodes.append(PageBreakNode())

    # Native Word Table of Contents on Page 2
    toc_title = t("toc.title", lang)
    toc_entries = self._build_dynamic_toc_entries(payload, lang)
    nodes.append(TOCNode(title=toc_title, entries=toc_entries))

    return nodes
```

```python
# In assessment_engine/adapters/compilers/docx_compiler.py

def _compile_paragraph(self, doc: Any, node: ParagraphNode) -> None:
    """Compile a ParagraphNode with specialized handling for cover page typography."""
    if node.style == "cover_title":
        p = doc.add_paragraph()
        p.paragraph_format.page_break_before = False
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(72)
        p.paragraph_format.space_after = Pt(18)
        run = p.add_run(node.text)
        set_run_font_comprehensive(
            run,
            font_name=self.font_family,
            size_pt=26,
            bold=True,
            color_rgb=RGBColor(0x00, 0x20, 0x60),
        )
        return

    if node.style == "cover_subtitle":
        p = doc.add_paragraph()
        p.paragraph_format.page_break_before = False
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(24)
        run = p.add_run(node.text)
        set_run_font_comprehensive(
            run,
            font_name=self.font_family,
            size_pt=16,
            bold=True,
            color_rgb=RGBColor(0x1F, 0x4E, 0x79),
        )
        return

    if node.style == "cover_meta":
        p = doc.add_paragraph()
        p.paragraph_format.page_break_before = False
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(node.text)
        set_run_font_comprehensive(
            run,
            font_name=self.font_family,
            size_pt=12,
            bold=bool(node.bold),
            color_rgb=RGBColor(0x33, 0x33, 0x33),
        )
        return

    # Standard paragraph compilation continues here...
```

---

### 2.2. Defect 2: Native Word Table of Contents (`<w:sdt>` + Dynamic Field Engine)

#### Root Cause Analysis
Currently, `_compile_toc()` in `docx_compiler.py` loops over `TOCEntryNode` items and writes static text paragraphs with hardcoded page numbers pulled from `locales.json` (`"Pág. 3"`, `"Pág. 18"`).
1. It is not a native Word Table of Contents block (`<w:sdt>` with `<w:docPartGallery w:val="Table of Contents"/>`).
2. Clicking on entries does not navigate to headings.
3. Static page numbers in `locales.json` are an architectural anti-pattern and desynchronize whenever content length changes.

#### Architectural Fix
1. Construct a genuine OpenXML Structured Document Tag (`<w:sdt>`) wrapping a Word complex field (`w:fldCharType="begin"`, `w:instrText` with `TOC \o "1-3" \h \z \u`, `w:fldCharType="separate"`, cached entries, and `w:fldCharType="end"`).
2. Set `w:dirty="true"` on the `begin` field character and inject `<w:updateFields w:val="true"/>` into the document's `settings.xml` so Microsoft Word and LibreOffice Writer automatically recalculate exact physical page numbers upon opening or PDF conversion.
3. For the initial cached view (before field update), render clean hyperlinks/entries **without** fake static page numbers from `locales.json`.
4. Ensure the TOC title itself uses a non-indexed paragraph style (outline level Body Text) so the TOC does not include itself.

#### Production Code (`docx_compiler.py`)

```python
# In assessment_engine/adapters/compilers/docx_compiler.py
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_TAB_ALIGNMENT, WD_TAB_LEADER


def _enable_auto_update_fields(doc: Any) -> None:
    """Ensure Word settings.xml contains <w:updateFields w:val='true'/>."""
    settings_element = doc.settings.element
    update_fields = settings_element.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings_element.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def _compile_toc(self, doc: Any, node: TOCNode) -> None:
    """Compile a native OpenXML Structured Document Tag (SDT) Table of Contents."""
    _enable_auto_update_fields(doc)

    # 1. Create the top-level <w:sdt> container recognized by Microsoft Word
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

    # 2. Add TOC Heading inside SDT (Not using 'Heading 1' so it doesn't self-index)
    toc_title_p = doc.add_paragraph()
    toc_title_p.paragraph_format.space_before = Pt(0)
    toc_title_p.paragraph_format.space_after = Pt(18)
    toc_title_p.paragraph_format.keep_with_next = True
    title_run = toc_title_p.add_run(node.title)
    set_run_font_comprehensive(
        title_run,
        font_name=self.font_family,
        size_pt=18,
        bold=True,
        color_rgb=RGBColor(0x00, 0x20, 0x60),
    )
    sdt_content.append(toc_title_p._p)

    # 3. Create the TOC Field Paragraph (begin + instrText + separate)
    field_p = doc.add_paragraph()
    field_p.paragraph_format.space_before = Pt(4)
    field_p.paragraph_format.space_after = Pt(4)

    r_begin = field_p.add_run()
    fld_char_begin = OxmlElement("w:fldChar")
    fld_char_begin.set(qn("w:fldCharType"), "begin")
    fld_char_begin.set(qn("w:dirty"), "true")
    r_begin._r.append(fld_char_begin)

    r_instr = field_p.add_run()
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = ' TOC \\o "1-3" \\h \\z \\u '
    r_instr._r.append(instr_text)

    r_sep = field_p.add_run()
    fld_char_sep = OxmlElement("w:fldChar")
    fld_char_sep.set(qn("w:fldCharType"), "separate")
    r_sep._r.append(fld_char_sep)

    sdt_content.append(field_p._p)

    # 4. Populate clean initial preview entries inside SDT (no fake hardcoded pages)
    for idx, entry in enumerate(node.entries, start=1):
        entry_p = doc.add_paragraph()
        level = getattr(entry, "level", 1)
        left_indent_pt = (level - 1) * 14
        entry_p.paragraph_format.left_indent = Pt(left_indent_pt)
        entry_p.paragraph_format.space_before = Pt(3 if level == 1 else 1)
        entry_p.paragraph_format.space_after = Pt(3 if level == 1 else 1)
        entry_p.paragraph_format.tab_stops.add_tab_stop(
            Pt(450), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )

        clean_title = self._strip_manual_heading_number(entry.title)
        display_label = f"{idx}. {clean_title}" if level == 1 else clean_title

        r_text = entry_p.add_run(display_label)
        set_run_font_comprehensive(
            r_text,
            font_name=self.font_family,
            size_pt=11 if level == 1 else 10,
            bold=(level == 1),
            color_rgb=RGBColor(0x00, 0x20, 0x60) if level == 1 else RGBColor(0x33, 0x33, 0x33),
        )
        sdt_content.append(entry_p._p)

    # 5. Close the complex TOC field (w:fldCharType="end")
    end_p = doc.add_paragraph()
    end_p.paragraph_format.space_before = Pt(0)
    end_p.paragraph_format.space_after = Pt(0)
    r_end = end_p.add_run()
    fld_char_end = OxmlElement("w:fldChar")
    fld_char_end.set(qn("w:fldCharType"), "end")
    r_end._r.append(fld_char_end)
    sdt_content.append(end_p._p)

    # Append complete SDT block to document body
    doc._body._body.append(sdt)
```

---

### 2.3. Defect 3: Elimination of Duplicate Heading Numbering (`2. 1. Resumen Ejecutivo`)

#### Root Cause Analysis
Two compounding issues produce `'2. 1. Resumen Ejecutivo'`:
1. As identified in Defect 1, the cover subtitle was using `Heading 1`, which consumed auto-number `1.` on Page 1.
2. `locales.json` and `payload_to_ast.py` pass strings with hardcoded numeric prefixes (`"1. Resumen Ejecutivo..."`, `"3.1. Mapa de Calor..."`, `"1. Objetivo y Alcance"`). Because `tower_annex_template.docx` already attaches a multi-level `<w:numPr>` numbering definition to `Heading 1`, `Heading 2`, and `Heading 3`, Word prepends its own automatic counter (`1.`, `1.1.`) in front of the hardcoded string prefix.

#### Architectural Fix
1. Introduce a deterministic sanitizer `strip_heading_number_prefix(text: str) -> str` using a compiled regular expression that strips leading chapter/section numbering tokens (e.g., `"1. "`, `"3.1. "`, `"4.2.1 "`, `"A.1. "`) while preserving legitimate text (such as years or ISO standards like `"ISO 27001"`).
2. Apply `strip_heading_number_prefix()` both in `payload_to_ast.py` when constructing `HeadingNode` instances and defensively in `docx_compiler.py` (`_compile_heading`) when binding to numbered Word heading styles.

#### Production Code (`payload_to_ast.py` & `docx_compiler.py`)

```python
# Shared utility / method in payload_to_ast.py and docx_compiler.py
import re

_HEADING_NUMBER_PREFIX_RE = re.compile(
    r"^\s*(?:(?:cap[íi]tulo|chapter|secci[óo]n|section)\s+)?\d+(?:\.\d+)*\.?\s*[-–—:]?\s+",
    re.IGNORECASE,
)


def strip_heading_number_prefix(title: str) -> str:
    """Strip manual leading numeric prefixes (e.g. '1. ', '3.1. ') from heading text.

    Prevents duplicate numbering when compiled into Word templates that enforce
    native OpenXML multi-level list numbering on Heading 1..3 styles.
    """
    if not title:
        return ""
    cleaned = _HEADING_NUMBER_PREFIX_RE.sub("", title.strip())
    return cleaned if cleaned else title.strip()
```

```python
# In assessment_engine/adapters/compilers/docx_compiler.py

def _compile_heading(self, doc: Any, node: HeadingNode) -> None:
    """Compile a HeadingNode using native template styles without duplicate prefixes."""
    clean_text = strip_heading_number_prefix(node.text)
    level = max(1, min(node.level, 4))
    style_name = f"Heading {level}"

    p = add_heading_paragraph(doc, clean_text, level=level, style_name=style_name)

    # Level 1 chapters start on a new page; sub-headings flow naturally
    if level == 1:
        p.paragraph_format.page_break_before = True
        p.paragraph_format.keep_with_next = True
    else:
        p.paragraph_format.page_break_before = False
        p.paragraph_format.keep_with_next = True
```

---

### 2.4. Defect 4: Resilient Pillar Name Resolution in Section 3.2

#### Root Cause Analysis
In `payload_to_ast.py` (around line 703, inside Section 3.2 Maturity Dashboard Table construction), the dictionary lookup strictly queries `p.get("pillar_id")` and `p.get("pillar_name")`. However, the synthesized JSON blueprints (`blueprint_t1_payload.json` and `blueprint_t2_payload.json`) serialize these keys as `"pilar_id"` and `"pilar_name"` (single `'l'`). Both lookups evaluate to `None`, triggering the fallback literal `"Pillar"`.

#### Architectural Fix
Implement a resilient multi-key extraction helper `_resolve_pillar_display_name(pillar_dict, resolver, tower_id, lang)` that checks all canonical and legacy key variants (`pillar_id`, `pilar_id`, `id`, `code` and `pillar_name`, `pilar_name`, `pillar_label`, `pilar_label`, `name`, `label`, `title`), and cross-references `TaxonomyResolver.resolve_pillar_name()` to guarantee localized, human-readable pillar names across all languages.

#### Production Code (`payload_to_ast.py`)

```python
# In assessment_engine/adapters/transformers/payload_to_ast.py

def _resolve_pillar_display_name(
    self,
    pillar_item: dict[str, Any],
    tower_id: str,
    lang: str,
) -> str:
    """Resiliently resolve localized pillar name from heterogeneous payload schemas."""
    raw_id = (
        pillar_item.get("pillar_id")
        or pillar_item.get("pilar_id")
        or pillar_item.get("id")
        or pillar_item.get("code")
        or ""
    )
    raw_name = (
        pillar_item.get("pillar_name")
        or pillar_item.get("pilar_name")
        or pillar_item.get("pillar_label")
        or pillar_item.get("pilar_label")
        or pillar_item.get("name")
        or pillar_item.get("label")
        or pillar_item.get("title")
        or ""
    )

    raw_id_str = str(raw_id).strip()
    raw_name_str = str(raw_name).strip()

    # 1. Attempt authoritative multilingual taxonomy lookup by pillar ID first
    if raw_id_str and self.taxonomy_resolver:
        resolved = self.taxonomy_resolver.resolve_pillar_name(
            pillar_id=raw_id_str,
            fallback_name=raw_name_str,
            tower_id=tower_id,
            lang=lang,
        )
        if resolved and resolved.lower() not in {"pillar", "pilar", raw_id_str.lower()}:
            return resolved

    # 2. If raw_name_str itself is a taxonomy code or valid name, resolve or return it
    if raw_name_str:
        if self.taxonomy_resolver:
            resolved_from_name = self.taxonomy_resolver.resolve_pillar_name(
                pillar_id=raw_name_str,
                fallback_name=raw_name_str,
                tower_id=tower_id,
                lang=lang,
            )
            if resolved_from_name:
                return resolved_from_name
        return raw_name_str

    # 3. Final fallback to ID if no human-readable name is available
    return raw_id_str or t("table.default_pillar_label", lang)
```

---

### 2.5. Defect 5: KPI-to-Capability Taxonomy Resolution in Risk Card Headers

#### Root Cause Analysis
In Chapter 4 (Risk Cards), each card header displays `f"[{risk_id}] {capability_name}"`. In the payload, `hc.get("capability")` or `hc.get("kpi_id")` holds a hierarchical KPI taxonomy code such as `"T1.P2.K1"` (Tower 1, Pillar 2, KPI 1).
Currently, `TaxonomyResolver` indexes towers and pillars/capabilities, but does not index leaf KPI codes (`T{x}.P{y}.K{z}`) or map them back to their localized KPI/capability names in `taxonomy_multilingual.json`. Consequently, `resolve_capability_name("T1.P2.K1")` misses the index and returns the raw code `"T1.P2.K1"`.

#### Architectural Fix
1. Enhance `TaxonomyResolver` in `assessment_engine/domain/taxonomy_resolver.py` to build a comprehensive `_kpis_index: dict[str, dict[str, str]]` during initialization by traversing all towers, pillars, capabilities, and KPIs in `taxonomy_multilingual.json`, indexing both full paths (`T1.P2.K1`) and local codes (`P2.K1`, `K1`).
2. Update `resolve_capability_name()` to query:
   - `_capabilities_index`
   - `_kpis_index`
   - regex fallback `^T(\d+)\.P(\d+)\.K(\d+)$` (which resolves `"Pillar Name — KPI Name"` or the parent pillar's localized name if the specific KPI node is unindexed).

#### Production Code (`taxonomy_resolver.py`)

```python
# In assessment_engine/domain/taxonomy_resolver.py
import re
from typing import Any

_KPI_CODE_PATTERN = re.compile(
    r"^(?:(T\d+)\.)?(P\d+)\.(K\d+)$",
    re.IGNORECASE,
)


class TaxonomyResolver:
    """Multilingual taxonomy resolver for Towers, Pillars, Capabilities, and KPIs."""

    def __init__(self, taxonomy_data: dict[str, Any]) -> None:
        self._raw = taxonomy_data or {}
        self._towers_index: dict[str, dict[str, str]] = {}
        self._pillars_index: dict[str, dict[str, str]] = {}
        self._capabilities_index: dict[str, dict[str, str]] = {}
        self._kpis_index: dict[str, dict[str, str]] = {}
        self._build_indices()

    def _extract_i18n_map(self, node: dict[str, Any]) -> dict[str, str]:
        """Extract language-keyed label dictionary from a taxonomy node."""
        labels: dict[str, str] = {}
        for field in ("names", "labels", "title", "name", "label"):
            val = node.get(field)
            if isinstance(val, dict):
                for lang_code, text in val.items():
                    if isinstance(text, str) and text.strip():
                        labels[lang_code.lower()] = text.strip()
            elif isinstance(val, str) and val.strip():
                labels.setdefault("es", val.strip())
                labels.setdefault("en", val.strip())
        for lang_code in ("es", "en", "pt", "fr", "de", "ja"):
            if isinstance(node.get(lang_code), str) and node[lang_code].strip():
                labels[lang_code] = node[lang_code].strip()
        return labels

    def _build_indices(self) -> None:
        """Index towers, pillars, capabilities, and leaf KPIs (e.g., T1.P2.K1)."""
        towers = self._raw.get("towers") or self._raw.get("domains") or {}
        if isinstance(towers, list):
            towers_iter = {
                str(t.get("id") or t.get("tower_id") or f"T{i}"): t
                for i, t in enumerate(towers, start=1)
                if isinstance(t, dict)
            }
        elif isinstance(towers, dict):
            towers_iter = towers
        else:
            towers_iter = {}

        for t_key, t_node in towers_iter.items():
            if not isinstance(t_node, dict):
                continue
            t_id = str(t_node.get("id") or t_node.get("tower_id") or t_key).upper()
            self._towers_index[t_id] = self._extract_i18n_map(t_node)

            pillars = (
                t_node.get("pillars")
                or t_node.get("pilares")
                or t_node.get("capabilities")
                or {}
            )
            if isinstance(pillars, list):
                pillars_iter = {
                    str(p.get("id") or p.get("pillar_id") or p.get("pilar_id") or f"P{i}"): p
                    for i, p in enumerate(pillars, start=1)
                    if isinstance(p, dict)
                }
            elif isinstance(pillars, dict):
                pillars_iter = pillars
            else:
                pillars_iter = {}

            for p_key, p_node in pillars_iter.items():
                if not isinstance(p_node, dict):
                    continue
                raw_p_id = str(
                    p_node.get("id")
                    or p_node.get("pillar_id")
                    or p_node.get("pilar_id")
                    or p_key
                ).upper()
                short_p_id = raw_p_id.split(".")[-1]
                composite_p_id = f"{t_id}.{short_p_id}"

                p_labels = self._extract_i18n_map(p_node)
                self._pillars_index[raw_p_id] = p_labels
                self._pillars_index[composite_p_id] = p_labels
                self._pillars_index.setdefault(short_p_id, p_labels)

                # Index nested KPIs / Sub-capabilities under this Pillar
                kpis = (
                    p_node.get("kpis")
                    or p_node.get("capabilities")
                    or p_node.get("sub_capabilities")
                    or p_node.get("questions")
                    or p_node.get("items")
                    or {}
                )
                if isinstance(kpis, list):
                    kpis_iter = {
                        str(k.get("id") or k.get("kpi_id") or k.get("code") or f"K{i}"): k
                        for i, k in enumerate(kpis, start=1)
                        if isinstance(k, dict)
                    }
                elif isinstance(kpis, dict):
                    kpis_iter = kpis
                else:
                    kpis_iter = {}

                for k_key, k_node in kpis_iter.items():
                    if not isinstance(k_node, dict):
                        continue
                    raw_k_id = str(
                        k_node.get("id")
                        or k_node.get("kpi_id")
                        or k_node.get("code")
                        or k_key
                    ).upper()
                    short_k_id = raw_k_id.split(".")[-1]
                    full_kpi_code = f"{t_id}.{short_p_id}.{short_k_id}"
                    pillar_kpi_code = f"{short_p_id}.{short_k_id}"

                    k_labels = self._extract_i18n_map(k_node)
                    self._kpis_index[raw_k_id] = k_labels
                    self._kpis_index[full_kpi_code] = k_labels
                    self._kpis_index.setdefault(pillar_kpi_code, k_labels)
                    self._capabilities_index[full_kpi_code] = k_labels
                    self._capabilities_index[raw_k_id] = k_labels

        # Also index any top-level 'kpis' or 'capabilities' dictionaries in taxonomy
        for top_key in ("kpis", "capabilities", "indicators"):
            top_map = self._raw.get(top_key)
            if isinstance(top_map, dict):
                for code, node in top_map.items():
                    if isinstance(node, dict):
                        norm_code = str(code).strip().upper()
                        labels = self._extract_i18n_map(node)
                        self._kpis_index[norm_code] = labels
                        self._capabilities_index[norm_code] = labels

    def resolve_capability_name(
        self,
        capability_code_or_name: str,
        lang: str = "es",
        tower_id: str | None = None,
    ) -> str:
        """Resolve a capability or KPI code (e.g. 'T1.P2.K1') to its localized title."""
        if not capability_code_or_name:
            return ""

        raw = str(capability_code_or_name).strip()
        norm = raw.upper()
        lang_key = (lang or "es").lower()[:2]

        # 1. Direct hit in capabilities or KPIs index
        for index in (self._kpis_index, self._capabilities_index, self._pillars_index):
            if norm in index:
                labels = index[norm]
                resolved = labels.get(lang_key) or labels.get("es") or labels.get("en")
                if resolved:
                    return resolved

        # 2. If tower_id is provided and code is relative (e.g. 'P2.K1'), prefix tower
        if tower_id and not norm.startswith("T"):
            prefixed = f"{tower_id.strip().upper()}.{norm}"
            for index in (self._kpis_index, self._capabilities_index, self._pillars_index):
                if prefixed in index:
                    labels = index[prefixed]
                    resolved = labels.get(lang_key) or labels.get("es") or labels.get("en")
                    if resolved:
                        return resolved

        # 3. Structural decomposition fallback for 'T1.P2.K1' -> resolve parent Pillar name
        match = _KPI_CODE_PATTERN.match(norm)
        if match:
            t_part, p_part, k_part = match.groups()
            effective_tower = t_part or (tower_id.strip().upper() if tower_id else "")
            composite_pillar = f"{effective_tower}.{p_part}" if effective_tower else p_part

            pillar_labels = (
                self._pillars_index.get(composite_pillar)
                or self._pillars_index.get(p_part)
                or {}
            )
            pillar_name = (
                pillar_labels.get(lang_key)
                or pillar_labels.get("es")
                or pillar_labels.get("en")
            )
            if pillar_name:
                return f"{pillar_name} ({k_part})"

        return raw
```

And in `payload_to_ast.py` where Risk Card headings are constructed:

```python
# In assessment_engine/adapters/transformers/payload_to_ast.py

raw_capability = (
    hc.get("capability_name")
    or hc.get("capability")
    or hc.get("kpi_name")
    or hc.get("kpi_id")
    or hc.get("pillar_name")
    or hc.get("pilar_name")
    or ""
)
resolved_capability = (
    self.taxonomy_resolver.resolve_capability_name(
        str(raw_capability),
        lang=lang,
        tower_id=tower_id,
    )
    if self.taxonomy_resolver
    else str(raw_capability)
)
card_header_title = f"[{risk_id}] {resolved_capability}" if resolved_capability else f"[{risk_id}]"
```

---

## 3. Verification & Quality Assurance Matrix

| Defect ID | Failure Mode Observed | Remediation Mechanism | Verification Assertion |
| :--- | :--- | :--- | :--- |
| **Defect 1** | Cover page splits onto Page 2; Page 2 almost blank | Emit `ParagraphNode(style="cover_subtitle")` instead of `HeadingNode(level=1)` | Cover Title, Subtitle, Client, and Date reside 100% on Page 1; zero `Heading 1` instances on Page 1. |
| **Defect 2** | Static text TOC with wrong hardcoded page numbers | OpenXML `<w:sdt>` + `TOC \o "1-3" \h \z \u` complex field + `<w:updateFields w:val="true"/>` | Word recognizes native TOC widget; page numbers dynamically sync with physical pages on open/convert. |
| **Defect 3** | Duplicate chapter numbering (`2. 1. Resumen Ejecutivo`) | Remove cover `Heading 1` + `strip_heading_number_prefix()` regex before applying `Heading 1..3` | Headings render cleanly as `1. Resumen Ejecutivo`, `2. Objetivo...`, `3.1. Mapa de Calor...`. |
| **Defect 4** | Section 3.2 displays literal `"Pillar"` in all rows | `_resolve_pillar_display_name()` inspects both `pillar_*` and `pilar_*` keys + `TaxonomyResolver` | Section 3.2 displays localized domain names (e.g., *Gobierno y Estrategia*, *Resiliencia Física*). |
| **Defect 5** | Risk card headers show `[RVS03] T1.P2.K1` | Index leaf KPIs (`T1.P2.K1`) in `TaxonomyResolver._kpis_index` with parent-pillar fallback | Risk card headers display human-readable localized titles instead of raw taxonomy codes. |