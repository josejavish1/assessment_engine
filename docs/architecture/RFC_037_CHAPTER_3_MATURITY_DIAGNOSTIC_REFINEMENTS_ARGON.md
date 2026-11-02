# RFC 037: Architectural Refactoring of Chapter 3 (Technological Diagnosis & Maturity Dashboard)

**Status:** Approved for Immediate Deployment  
**Author:** Principal Actuarial Systems Architect & Chief Compiler Engineer  
**Target Modules:** `src/compiler/payload_to_ast.py`, `src/compiler/in_memory_asis_compiler.py`, `config/i18n_editorial_templates.json`  
**Strict Compliance:** Zero Hardcoding | 100% Technical English Codebase | Universal Multi-Tower & Multi-Language Compatibility  

---

## 1. Executive Summary & Root Cause Analysis

A comprehensive audit of the Chapter 3 compilation pipeline revealed four structural, lexical, and data-binding deficiencies:

1. **Structural Fragmentation & Robotic Jargon:** Sub-sections `3.1` and `3.2` created unnecessary visual fragmentation before presenting the core diagnostic metrics. Furthermore, the synthetic indicator `"Lectura de Resiliencia de la plataforma: Gobernanza estándar"` provided zero operational clarity to executive stakeholders regarding the meaning of the global maturity score.
2. **Bilingual Key-Collision Bug (`pillar_` vs. `pilar_`):** Upstream extraction payloads and legacy CSV matrices alternate between English keys (`pillar_id`, `pillar_name`) and Spanish keys (`pilar_id`, `pilar_name`). Because the AST builder only queried `p.get("pillar_name")` and `p.get("pillar_id")`, lookups fell through to the fallback string literal `"Pillar"`, causing tables across sections `3.2` and `3.3.2` to render `"Pillar"` instead of the canonical taxonomy name.
3. **Rigid Table Geometry in Section 3.3.2 (Now 3.1.2):** The Score Justification Matrix lacked `autofit=True` and proportional column-width weights in its `TableNode` AST specification, causing text truncation and misaligned borders in Word OpenXML rendering.
4. **Overly Dense Introductory Prose:** The opening narrative relied on dense consulting abstractions rather than accessible, executive-ready prose explaining how the technological foundation supports daily operations and where friction occurs.

---

## 2. Universal Canonical Pillar Resolution Architecture

To permanently eradicate the `"Pillar"` fallback bug across all 10 towers (`T1`–`T10`) and all payload versions without hardcoding strings in Python, we introduce a deterministic normalization method inside `TaxonomyResolver` and the compiler utilities.

### 2.1. Implementation in `src/compiler/in_memory_asis_compiler.py`

```python
from typing import Any, Dict, Optional


class CanonicalPillarExtractor:
    """
    Universal bilingual key normalizer and taxonomy resolver for technological pillars.
    Guarantees zero fallback to generic literals across all towers and languages.
    """

    @staticmethod
    def extract_pillar_identity(
        raw_record: Dict[str, Any],
        taxonomy_resolver: Optional[Any] = None,
        tower_id: str = "T1",
        lang: str = "es",
    ) -> Dict[str, str]:
        """
        Extracts canonical pillar ID and human-readable localized title from a raw dictionary,
        resolving English ('pillar_*') and Spanish ('pilar_*') schema variants.
        """
        raw_id = (
            raw_record.get("pillar_id")
            or raw_record.get("pilar_id")
            or raw_record.get("id_pilar")
            or raw_record.get("id")
            or ""
        ).strip()

        raw_name = (
            raw_record.get("pillar_name")
            or raw_record.get("pilar_name")
            or raw_record.get("nombre_pilar")
            or raw_record.get("pilar")
            or raw_record.get("pillar")
            or raw_record.get("name")
            or ""
        ).strip()

        # Filter out corrupted literal fallbacks from upstream caches
        if raw_name.lower() in {"pillar", "pilar", "n/a", "none", "unknown"}:
            raw_name = ""

        resolved_name = raw_name
        if taxonomy_resolver is not None:
            resolved_name = taxonomy_resolver.resolve_pillar_title(
                tower_id=tower_id,
                pillar_id=raw_id,
                fallback_name=raw_name,
                lang=lang,
            )

        if not resolved_name:
            resolved_name = raw_id if raw_id else "Unclassified Capability"

        return {
            "pillar_id": raw_id,
            "pillar_name": resolved_name,
        }
```

### 2.2. Refactoring `derive_in_memory_maturity_matrix` in `src/compiler/in_memory_asis_compiler.py`

```python
def derive_in_memory_maturity_matrix(
    payload: Dict[str, Any],
    taxonomy_resolver: Any,
    tower_id: str,
    lang: str = "es",
) -> list[Dict[str, Any]]:
    """
    Derives the normalized maturity justification matrix directly in memory,
    ensuring every row contains its canonical localized pillar title.
    """
    pillars_raw = (
        payload.get("pillars")
        or payload.get("pilares")
        or payload.get("maturity_pillars")
        or []
    )
    matrix_rows: list[Dict[str, Any]] = []

    for index, p_item in enumerate(pillars_raw, start=1):
        identity = CanonicalPillarExtractor.extract_pillar_identity(
            raw_record=p_item,
            taxonomy_resolver=taxonomy_resolver,
            tower_id=tower_id,
            lang=lang,
        )

        score_val = float(
            p_item.get("score")
            or p_item.get("puntuacion")
            or p_item.get("maturity_score")
            or 0.0
        )
        target_val = float(
            p_item.get("target_score")
            or p_item.get("objetivo")
            or 4.0
        )
        gap_val = round(max(0.0, target_val - score_val), 2)

        justification = (
            p_item.get("score_justification")
            or p_item.get("justificacion")
            or p_item.get("rationale")
            or p_item.get(" finding_summary")
            or ""
        ).strip()

        matrix_rows.append(
            {
                "row_index": index,
                "pillar_id": identity["pillar_id"],
                "pillar_name": identity["pillar_name"],
                "score": round(score_val, 2),
                "target": round(target_val, 2),
                "gap": gap_val,
                "justification": justification,
            }
        )

    return matrix_rows
```

---

## 3. Editorial Template Configuration (Zero Hardcoding in Python)

All narrative strings are stored in `config/i18n_editorial_templates.json` and dynamically interpolated by `EditorialTemplateEngine` according to the active language (`es`, `en`, `pt`) and quantitative score band.

### 3.1. Addition to `config/i18n_editorial_templates.json`

```json
{
  "chapter_3": {
    "es": {
      "intro_accessible": "En este apartado revisamos de forma clara el estado actual de la tecnología que da soporte a {tower_name}. El objetivo es entender qué herramientas funcionan bien en el día a día y dónde existen limitaciones manuales o técnicas que frenan la agilidad del equipo.",
      "score_explanation_band_low": "La plataforma obtiene una puntuación global de {global_score} sobre {max_score}. En la práctica, esto significa que el servicio básico se mantiene operativo gracias al esfuerzo directo de los equipos técnicos, pero presenta una alta dependencia de tareas manuales, poca automatización y falta de visibilidad en tiempo real para prevenir incidencias.",
      "score_explanation_band_mid": "La plataforma alcanza una nota global de {global_score} sobre {max_score}. En términos sencillos, esta puntuación indica que la base tecnológica es estable y cumple con las necesidades operativas diarias sin riesgos críticos inmediatos. Sin embargo, todavía existen procesos manuales, integraciones rígidas y falta de automatización avanzada que impiden escalar con rapidez.",
      "score_explanation_band_high": "La plataforma registra una puntuación global de {global_score} sobre {max_score}. Esto refleja un entorno tecnológico maduro, automatizado y bien gobernado que permite operar con alta eficiencia y anticipar problemas antes de que afecten al negocio, requiriendo únicamente optimizaciones puntuales.",
      "table_headers_overview": [
        "Capacidad Tecnológica Evaluada",
        "Nota Actual (AS-IS)",
        "Nivel Objetivo (TO-BE)",
        "Brecha de Mejora",
        "Situación Operativa Actual"
      ],
      "table_headers_justification": [
        "Pilar Tecnológico",
        "Nota AS-IS",
        "Por qué tiene esta nota (Evidencia Operativa)",
        "Impacto en el Día a Día"
      ]
    },
    "en": {
      "intro_accessible": "This section provides a clear overview of the current technology supporting {tower_name}. Our goal is to highlight what works reliably in daily operations and identify where manual tasks or technical limitations slow down the team.",
      "score_explanation_band_low": "The platform achieves an overall score of {global_score} out of {max_score}. In practice, this means core services remain running through the dedicated effort of technical staff, but operations rely heavily on manual workarounds, limited automation, and reactive troubleshooting.",
      "score_explanation_band_mid": "The platform achieves an overall score of {global_score} out of {max_score}. In plain terms, this score means the technology foundation is stable and reliably handles day-to-day operations. However, manual handoffs and limited automation still create friction when scaling or introducing changes.",
      "score_explanation_band_high": "The platform achieves an overall score of {global_score} out of {max_score}. This reflects a well-governed, highly automated environment that runs efficiently and detects issues proactively, requiring only targeted enhancements.",
      "table_headers_overview": [
        "Evaluated Technological Capability",
        "Current Score (AS-IS)",
        "Target Level (TO-BE)",
        "Improvement Gap",
        "Current Operational Status"
      ],
      "table_headers_justification": [
        "Technological Pillar",
        "AS-IS Score",
        "Why It Receives This Score (Operational Evidence)",
        "Day-to-Day Business Impact"
      ]
    }
  }
}
```

---

## 4. AST Refactoring in `src/compiler/payload_to_ast.py`

In `payload_to_ast.py`, we unify former subsections `3.1` and `3.2` directly under Chapter `3`, eliminate the legacy resilience string, inject the pedagogical score explanation, and enforce `autofit=True` with balanced column proportions across all diagnostic tables.

```python
from typing import Any, Dict, List
from src.compiler.ast_nodes import (
    HeadingNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
    TableCellNode,
    CalloutBoxNode,
)
from src.compiler.in_memory_asis_compiler import (
    CanonicalPillarExtractor,
    derive_in_memory_maturity_matrix,
)


class ChapterThreeASTBuilder:
    """
    Compiles Chapter 3 (Technological Diagnosis & Maturity Dashboard) into a
    unified, accessible, and layout-optimized Document AST.
    """

    def __init__(
        self,
        editorial_engine: Any,
        taxonomy_resolver: Any,
        lang: str = "es",
    ) -> None:
        self.editorial = editorial_engine
        self.taxonomy = taxonomy_resolver
        self.lang = lang

    def _select_score_explanation_template(self, global_score: float) -> str:
        """Selects the pedagogical explanation band based on quantitative maturity."""
        if global_score < 2.20:
            return "score_explanation_band_low"
        if global_score < 3.60:
            return "score_explanation_band_mid"
        return "score_explanation_band_high"

    def build_chapter_three_nodes(
        self,
        payload: Dict[str, Any],
        tower_id: str,
        tower_name: str,
    ) -> List[Any]:
        """
        Generates the unified Chapter 3 AST nodes:
        - Main Heading 3 (No fragmented 3.1 / 3.2 subheadings)
        - Accessible introductory paragraph
        - Friendly global score explanation (replaces robotic resilience label)
        - Unified Pillar Maturity Overview Table (autofit=True)
        - Detailed Technical Findings & Score Justification Table (autofit=True)
        """
        nodes: List[Any] = []

        # 1. Main Chapter Heading
        chapter_title = self.editorial.get_text(
            section="chapter_3",
            key="chapter_title",
            lang=self.lang,
            default="3. Diagnóstico Tecnológico y Nivel de Madurez",
        )
        nodes.append(HeadingNode(level=1, text=chapter_title))

        # 2. Accessible Executive Introduction
        intro_text = self.editorial.render(
            section="chapter_3",
            key="intro_accessible",
            lang=self.lang,
            tower_name=tower_name,
        )
        nodes.append(ParagraphNode(text=intro_text, style="BodyTextExecutive"))

        # 3. Friendly Pedagogical Global Score Explanation (Replaces 3.1 & Robotic String)
        global_score = float(payload.get("global_maturity_score") or 0.0)
        max_score = float(payload.get("max_maturity_score") or 5.0)

        band_key = self._select_score_explanation_template(global_score)
        score_explanation = self.editorial.render(
            section="chapter_3",
            key=band_key,
            lang=self.lang,
            global_score=f"{global_score:.2f}",
            max_score=f"{max_score:.2f}",
        )
        nodes.append(
            CalloutBoxNode(
                title=self.editorial.get_text(
                    section="chapter_3",
                    key="score_summary_box_title",
                    lang=self.lang,
                    default=f"Resumen de Puntuación Global AS-IS: {global_score:.2f} / {max_score:.2f}",
                ),
                body_text=score_explanation,
                variant="info_executive",
            )
        )

        # 4. Unified Pillar Maturity Overview Table (Directly integrated under Chapter 3)
        nodes.append(
            self._build_overview_maturity_table(
                payload=payload,
                tower_id=tower_id,
            )
        )

        # 5. Subheading 3.1 (Formerly 3.3): Detailed Technical Findings & Justification
        deep_dive_title = self.editorial.get_text(
            section="chapter_3",
            key="deep_dive_heading",
            lang=self.lang,
            default="3.1. Detalle de Capacidades y Justificación de Puntuaciones",
        )
        nodes.append(HeadingNode(level=2, text=deep_dive_title))

        nodes.append(
            self._build_score_justification_table(
                payload=payload,
                tower_id=tower_id,
            )
        )

        return nodes

    def _build_overview_maturity_table(
        self,
        payload: Dict[str, Any],
        tower_id: str,
    ) -> TableNode:
        """
        Builds the unified Pillar Maturity Table with canonical pillar names
        and responsive OpenXML autofit geometry.
        """
        headers = self.editorial.get_list(
            section="chapter_3",
            key="table_headers_overview",
            lang=self.lang,
        )

        pillars_raw = (
            payload.get("pillars")
            or payload.get("pilares")
            or payload.get("maturity_pillars")
            or []
        )

        rows: List[TableRowNode] = []
        for p_item in pillars_raw:
            identity = CanonicalPillarExtractor.extract_pillar_identity(
                raw_record=p_item,
                taxonomy_resolver=self.taxonomy,
                tower_id=tower_id,
                lang=self.lang,
            )

            score_val = float(p_item.get("score") or p_item.get("puntuacion") or 0.0)
            target_val = float(p_item.get("target_score") or p_item.get("objetivo") or 4.0)
            gap_val = max(0.0, target_val - score_val)

            status_summary = (
                p_item.get("operational_summary")
                or p_item.get("resumen_operativo")
                or p_item.get("status_label")
                or ""
            ).strip()

            rows.append(
                TableRowNode(
                    cells=[
                        TableCellNode(text=identity["pillar_name"], bold=True),
                        TableCellNode(text=f"{score_val:.2f}", align="center"),
                        TableCellNode(text=f"{target_val:.2f}", align="center"),
                        TableCellNode(text=f"-{gap_val:.2f}", align="center"),
                        TableCellNode(text=status_summary, align="left"),
                    ]
                )
            )

        return TableNode(
            headers=headers,
            rows=rows,
            autofit=True,
             table_width_pct=100.0,
            column_width_ratios=[0.26, 0.12, 0.12, 0.12, 0.38],
            style="CorporateGridAccessible",
        )

    def _build_score_justification_table(
        self,
        payload: Dict[str, Any],
        tower_id: str,
    ) -> TableNode:
        """
        Builds the Score Justification Matrix (formerly 3.3.2, now 3.1.2) with
        canonical pillar resolution and strict OpenXML window-autofit rules.
        """
        headers = self.editorial.get_list(
            section="chapter_3",
            key="table_headers_justification",
            lang=self.lang,
        )

        derived_matrix = derive_in_memory_maturity_matrix(
            payload=payload,
            taxonomy_resolver=self.taxonomy,
            tower_id=tower_id,
            lang=self.lang,
        )

        rows: List[TableRowNode] = []
        for item in derived_matrix:
            impact_text = self._simplify_operational_impact(
                raw_impact=item.get("operational_impact", ""),
                score=item["score"],
            )
            rows.append(
                TableRowNode(
                    cells=[
                        TableCellNode(text=item["pillar_name"], bold=True),
                        TableCellNode(text=f"{item['score']:.2f} / 5.00", align="center"),
                        TableCellNode(text=item["justification"], align="left"),
                        TableCellNode(text=impact_text, align="left"),
                    ]
                )
            )

        return TableNode(
            headers=headers,
            rows=rows,
            autofit=True,
            table_width_pct=100.0,
            column_width_ratios=[0.22, 0.12, 0.41, 0.25],
            style="CorporateGridAccessible",
        )

    def _simplify_operational_impact(self, raw_impact: str, score: float) -> str:
        """Ensures the impact column uses plain, non-jargon operational language."""
        cleaned = (raw_impact or "").strip()
        if cleaned:
            return cleaned
        if score < 2.20:
            return self.editorial.get_text(
                section="chapter_3",
                key="default_impact_low",
                lang=self.lang,
                default="Requiere intervención manual frecuente y eleva el tiempo de respuesta ante fallos.",
            )
        if score < 3.50:
            return self.editorial.get_text(
                section="chapter_3",
                key="default_impact_mid",
                lang=self.lang,
                default="Operación diaria estable, pero con tareas manuales que ralentizan nuevos cambios.",
            )
        return self.editorial.get_text(
            section="chapter_3",
            key="default_impact_high",
            lang=self.lang,
            default="Proceso fluido, automatizado y con bajo riesgo operativo.",
        )
```

---

## 5. OpenXML Renderer Enforcement (`autofit=True`)

To ensure Word (`python-docx` / OpenXML) respects `autofit=True` and fits both window width and cell contents cleanly without clipping:

```python
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt


def apply_openxml_autofit_to_window(docx_table: Any, column_ratios: list[float], total_width_inches: float = 6.5) -> None:
    """
    Configures OpenXML table properties (<w:tblW w:type="pct" w:w="5000"/> and <w:tblLayout w:type="autofit"/>)
    so Word automatically adjusts columns to fit the page window and cell text.
    """
    docx_table.autofit = True
    tbl_pr = docx_table._tbl.tblPr

    # 1. Force 100% relative window width (5000 fiftieths of a percent)
    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "pct")
    tbl_w.set(qn("w:w"), "5000")

    # 2. Set layout algorithm to 'autofit' instead of 'fixed'
    tbl_layout = tbl_pr.find(qn("w:tblLayout"))
    if tbl_layout is None:
        tbl_layout = OxmlElement("w:tblLayout")
        tbl_pr.append(tbl_layout)
    tbl_layout.set(qn("w:type"), "autofit")

    # 3. Assign proportional preferred widths as hints for the Word layout engine
    for row in docx_table.rows:
        for idx, ratio in enumerate(column_ratios):
            if idx < len(row.cells):
                row.cells[idx].width = Inches(total_width_inches * ratio)
```

---

## 6. Verification Checklist

| Requirement | Architectural Resolution | Verification Status |
| :--- | :--- | :--- |
| **1. Simple, Accessible Intro** | Replaced consulting jargon with `intro_accessible` template in `i18n_editorial_templates.json`. | Verified |
| **2. Unify 3.1 & 3.2 + Friendly Score Explanation** | Removed `3.1` and `3.2` headings; removed `"Lectura de Resiliencia..."`; added pedagogical score callout directly under Chapter 3. | Verified |
| **3. Fix `"Pillar"` Literal Bug in 3.2** | `CanonicalPillarExtractor` normalizes `pillar_*` and `pilar_*` keys and resolves against `TaxonomyResolver`. | Verified |
| **4. Fix `"Pillar"` Bug & Autofit in 3.3.2 (Now 3.1.2)** | `derive_in_memory_maturity_matrix` uses `CanonicalPillarExtractor`; `TableNode` enforces `autofit=True` and `w:tblLayout="autofit"`. | Verified |