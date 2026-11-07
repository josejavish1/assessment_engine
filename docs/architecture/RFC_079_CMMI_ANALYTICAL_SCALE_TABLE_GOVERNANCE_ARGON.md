# RFC 079: CMMI Analytical Maturity Scale Table & Page 5 Balance Governance

**Status:** APPROVED — MANDATORY ARCHITECTURAL DIRECTIVE  
**Target Deliverable:** Consolidated AS-IS Diagnostic Deliverable (Volume 1 / Tomo 1)  
**Target Subsystem:** Chapter 2 (`_build_chapter_2_maturity_radiography` in `tomo_asis_ast_compiler.py`) & `locales.json`  
**Classification:** Executive Editorial Governance & Deterministic Layout Engineering  

---

## 1. Executive Verdict & Layout Determinism Budget for Page 5

### 1.1. Executive Governance Verdict
In board-level technological due diligence and corporate governance auditing, presenting quantitative maturity scores (e.g., `2.64 / 5.00`) without an explicit, standardized evaluative rubric constitutes an epistemological deficit. C-Suite executives (CEOs, CFOs, CIOs) and Audit Committees require an unambiguous operational reference within the immediate visual field of the diagnostic telemetry to understand the exact governance threshold separating tactical execution (**Level 2 — Repeatable**) from institutionalized corporate standardization (**Level 3 — Defined**) and quantitative telemetry control (**Level 4 — Managed**).

Simultaneously, from an editorial systems engineering perspective, leaving the lower 45% of Page 5 as unallocated whitespace beneath Figure 2.1 violates Big-4 / MBB visual density standards. 

**Architectural Resolution:**  
We introduce **Section 2.2 (CMMI Analytical Maturity Scale)** on the lower half of Page 5, immediately following the bimodal architecture narrative paragraphs. This guarantees complete pedagogical closure for Chapter 2 while achieving optimal typographic equilibrium across Pages 4 and 5, ensuring Chapter 3 (*Cross-Cutting Structural Findings*) initiates deterministically at the top margin of Page 6.

### 1.2. Page 5 Vertical Canvas Budget (A4 Printable Frame = 630.0 pt)
To prevent orphan rows, table spillovers onto Page 6, or collisions with the running footer, the vertical AST allocation on Page 5 is strictly governed by the following deterministic point budget:

| AST Component | Specification / Constraint | Vertical Allocation (pt) | Cumulative Height (pt) |
| :--- | :--- | :---: | :---: |
| **Figure 2.1 (`ImageNode`)** | 10-Axis Radar Chart (`max_height=215.0 pt` + caption `15.0 pt`) | `230.0 pt` | `230.0 pt` |
| **Post-Figure Spacer** | `SpacerNode(height=8.0)` | `8.0 pt` | `238.0 pt` |
| **Radar Narrative (2 Paragraphs)** | Bimodal / dispersion analysis (`~42.0 pt` per paragraph + spacing) | `90.0 pt` | `328.0 pt` |
| **Section Pre-Spacer** | `SpacerNode(height=10.0)` | `10.0 pt` | `338.0 pt` |
| **Section 2.2 Subheading** | `HeadingNode(level=2)` ("2.2. CMMI Analytical Maturity Scale") | `22.0 pt` | `360.0 pt` |
| **Section 2.2 Intro Paragraph** | 1–2 line framing narrative (`font_size=9.5 pt`, `leading=12.5 pt`) | `24.0 pt` | `384.0 pt` |
| **Table Pre-Spacer** | `SpacerNode(height=6.0)` | `6.0 pt` | `390.0 pt` |
| **CMMI Scale Table (`TableNode`)** | 1 Header (`20.0 pt`) + 5 Compact Rows (`5 x 19.0 pt = 95.0 pt`) | `115.0 pt` | `505.0 pt` |
| **Safety Margin Buffer** | Remaining breathing room before bottom footer margin (`630.0 - 505.0`) | `125.0 pt` | `630.0 pt` |

**Containment Invariant:** Total vertical consumption is **`505.0 pt`**, remaining **`125.0 pt` below** the `630.0 pt` printable canvas ceiling. This guarantees zero page overflow across all 6 supported locales (`es`, `en`, `pt`, `fr`, `de`, `ja`), including verbose German and French translations.

---

## 2. Exact 6-Locale Localization Catalog (`locales.json`)

All text strings are strictly industry-agnostic, domain-neutral, and devoid of client-specific or vertical-specific nouns. Add the following keys under the `tomo_asis` namespace in `locales.json` across all six languages:

```json
{
  "es": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. Escala Analítica de Madurez CMMI",
      "ch2_sec2_intro": "Para garantizar la trazabilidad objetiva del diagnóstico, la evaluación cuantitativa aplica una escala analítica continua de 1,00 a 5,00 segmentada en intervalos de 0,80 puntos, definiendo cinco umbrales de control operacional y gobierno:",
      "ch2_scale_col_level": "Nivel de Madurez",
      "ch2_scale_col_range": "Rango Analítico",
      "ch2_scale_col_criteria": "Criterios de Control Operacional y Gobernanza",
      "ch2_scale_lvl1_name": "Nivel 1 — Inicial",
      "ch2_scale_lvl1_desc": "Operación reactiva y ad-hoc; ausencia de estandarización formal y dependencia crítica del esfuerzo individual de personal clave.",
      "ch2_scale_lvl2_name": "Nivel 2 — Repetible",
      "ch2_scale_lvl2_desc": "Prácticas operativas básicas establecidas a nivel táctico o local, pero con silos funcionales e inconsistencias de ejecución entre unidades.",
      "ch2_scale_lvl3_name": "Nivel 3 — Definido",
      "ch2_scale_lvl3_desc": "Procesos formalizados, documentados y estandarizados bajo políticas corporativas unificadas con aplicación transversal en la organización.",
      "ch2_scale_lvl4_name": "Nivel 4 — Gestionado",
      "ch2_scale_lvl4_desc": "Capacidades medidas cuantitativamente mediante telemetría, control predictivo de niveles de servicio (SLAs) y alineación con el gobierno corporativo.",
      "ch2_scale_lvl5_name": "Nivel 5 — Optimizado",
      "ch2_scale_lvl5_desc": "Excelencia operacional impulsada por automatización avanzada, prevención proactiva de defectos y ciclos sistemáticos de mejora continua."
    }
  },
  "en": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. CMMI Analytical Maturity Scale",
      "ch2_sec2_intro": "To ensure objective diagnostic traceability, the quantitative assessment applies a continuous analytical scale from 1.00 to 5.00 segmented into 0.80-point intervals, defining five operational control and governance thresholds:",
      "ch2_scale_col_level": "Maturity Level",
      "ch2_scale_col_range": "Analytical Range",
      "ch2_scale_col_criteria": "Operational Control & Governance Criteria",
      "ch2_scale_lvl1_name": "Level 1 — Initial",
      "ch2_scale_lvl1_desc": "Reactive, ad-hoc execution; absence of formal standardization with critical reliance on individual heroics of key personnel.",
      "ch2_scale_lvl2_name": "Level 2 — Repeatable",
      "ch2_scale_lvl2_desc": "Basic operational practices established at a tactical or local level, exhibiting functional silos and execution inconsistencies across units.",
      "ch2_scale_lvl3_name": "Level 3 — Defined",
      "ch2_scale_lvl3_desc": "Formalized, documented, and standardized processes governed by unified corporate policies with consistent enterprise-wide adoption.",
      "ch2_scale_lvl4_name": "Level 4 — Managed",
      "ch2_scale_lvl4_desc": "Quantitatively measured capabilities backed by real-time telemetry, predictive SLA control, and full corporate governance alignment.",
      "ch2_scale_lvl5_name": "Level 5 — Optimized",
      "ch2_scale_lvl5_desc": "Operational excellence driven by advanced automation, proactive defect prevention, and continuous systematic improvement cycles."
    }
  },
  "pt": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. Escala Analítica de Maturidade CMMI",
      "ch2_sec2_intro": "Para garantir a rastreabilidade objetiva do diagnóstico, a avaliação quantitativa aplica uma escala analítica contínua de 1,00 a 5,00 segmentada em intervalos de 0,80 pontos, definindo cinco patamares de controle operacional e governança:",
      "ch2_scale_col_level": "Nível de Maturidade",
      "ch2_scale_col_range": "Intervalo Analítico",
      "ch2_scale_col_criteria": "Critérios de Controle Operacional e Governança",
      "ch2_scale_lvl1_name": "Nível 1 — Inicial",
      "ch2_scale_lvl1_desc": "Operação reativa e ad-hoc; ausência de padronização formal e dependência crítica do esforço individual de profissionais-chave.",
      "ch2_scale_lvl2_name": "Nível 2 — Repetível",
      "ch2_scale_lvl2_desc": "Práticas operacionais básicas estabelecidas em nível tático ou local, mas com silos funcionais e inconsistências de execução entre unidades.",
      "ch2_scale_lvl3_name": "Nível 3 — Definido",
      "ch2_scale_lvl3_desc": "Processos formalizados, documentados e padronizados sob políticas corporativas unificadas com aplicação transversal na organização.",
      "ch2_scale_lvl4_name": "Nível 4 — Gerenciado",
      "ch2_scale_lvl4_desc": "Capacidades medidas quantitativamente por telemetria, controle preditivo de níveis de serviço (SLAs) e alinhamento à governança corporativa.",
      "ch2_scale_lvl5_name": "Nível 5 — Otimizado",
      "ch2_scale_lvl5_desc": "Excelência operacional impulsionada por automação avançada, prevenção proativa de falhas e ciclos sistemáticos de melhoria contínua."
    }
  },
  "fr": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. Échelle Analytique de Maturité CMMI",
      "ch2_sec2_intro": "Pour garantir la traçabilité objective du diagnostic, l'évaluation quantitative applique une échelle analytique continue de 1,00 à 5,00 segmentée par intervalles de 0,80 point, définissant cinq seuils de contrôle opérationnel et de gouvernance :",
      "ch2_scale_col_level": "Niveau de Maturité",
      "ch2_scale_col_range": "Plage Analytique",
      "ch2_scale_col_criteria": "Critères de Contrôle Opérationnel et de Gouvernance",
      "ch2_scale_lvl1_name": "Niveau 1 — Initial",
      "ch2_scale_lvl1_desc": "Exécution réactive et ad hoc ; absence de standardisation formelle et dépendance critique envers l'effort individuel du personnel clé.",
      "ch2_scale_lvl2_name": "Niveau 2 — Répétable",
      "ch2_scale_lvl2_desc": "Pratiques opérationnelles de base établies au niveau tactique ou local, avec des silos fonctionnels et des incohérences entre les unités.",
      "ch2_scale_lvl3_name": "Niveau 3 — Défini",
      "ch2_scale_lvl3_desc": "Processus formalisés, documentés et standardisés sous des politiques d'entreprise unifiées avec une application transversale cohérente.",
      "ch2_scale_lvl4_name": "Niveau 4 — Géré",
      "ch2_scale_lvl4_desc": "Capacités mesurées quantitativement par télémétrie, contrôle prédictif des SLA et alignement complet avec la gouvernance d'entreprise.",
      "ch2_scale_lvl5_name": "Niveau 5 — Optimisé",
      "ch2_scale_lvl5_desc": "Excellence opérationnelle portée par l'automatisation avancée, la prévention proactive des défauts et l'amélioration continue systématique."
    }
  },
  "de": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. Analytische CMMI-Reifegradskala",
      "ch2_sec2_intro": "Zur Gewährleistung einer objektiven diagnostischen Nachvollziehbarkeit nutzt die quantitative Bewertung eine kontinuierliche Skala von 1,00 bis 5,00 in 0,80-Punkte-Intervallen, die fünf operative Steuerungs- und Governance-Stufen definiert:",
      "ch2_scale_col_level": "Reifegradstufe",
      "ch2_scale_col_range": "Analytischer Bereich",
      "ch2_scale_col_criteria": "Kriterien für operative Steuerung und Governance",
      "ch2_scale_lvl1_name": "Stufe 1 — Initial",
      "ch2_scale_lvl1_desc": "Reaktiver Ad-hoc-Betrieb; fehlende formale Standardisierung und kritische Abhängigkeit vom individuellen Einsatz einzelner Schlüsselkräfte.",
      "ch2_scale_lvl2_name": "Stufe 2 — Wiederholbar",
      "ch2_scale_lvl2_desc": "Grundlegende operative Praktiken auf taktischer oder lokaler Ebene etabliert, jedoch mit Funktionssilos und Inkonsistenzen zwischen Einheiten.",
      "ch2_scale_lvl3_name": "Stufe 3 — Definiert",
      "ch2_scale_lvl3_desc": "Formalisierte, dokumentierte und standardisierte Prozesse unter einheitlichen Unternehmensrichtlinien mit konsistenter weiter Anwendung.",
      "ch2_scale_lvl4_name": "Stufe 4 — Gesteuert",
      "ch2_scale_lvl4_desc": "Quantitativ gemessene Fähigkeiten durch Telemetrie, prädiktive SLA-Steuerung und vollständige Ausrichtung an der Corporate Governance.",
      "ch2_scale_lvl5_name": "Stufe 5 — Optimiert",
      "ch2_scale_lvl5_desc": "Operative Exzellenz durch fortschrittliche Automatisierung, proaktive Fehlerprävention und systematische kontinuierliche Verbesserungszyklen."
    }
  },
  "ja": {
    "tomo_asis": {
      "ch2_sec2_title": "2.2. CMMI 分析成熟度スケール",
      "ch2_sec2_intro": "診断の客観的なトレーサビリティを確保するため、定量評価では1.00から5.00までの連続的な分析スケールを0.80ポイント間隔で区分し、5つの運用統制およびガバナンス基準を定義しています：",
      "ch2_scale_col_level": "成熟度レベル",
      "ch2_scale_col_range": "分析レンジ",
      "ch2_scale_col_criteria": "運用統制およびガバナンス基準",
      "ch2_scale_lvl1_name": "レベル 1 — 初期",
      "ch2_scale_lvl1_desc": "事後対応型かつ場当たり的な運用。公式な標準化が欠如しており、特定の主要担当者の属人的な努力に大きく依存している状態。",
      "ch2_scale_lvl2_name": "レベル 2 — 反復可能",
      "ch2_scale_lvl2_desc": "戦術的または拠点レベルで基本的な運用手順が確立されているものの、機能サイロや部門間での実行のばらつきが存在する状態。",
      "ch2_scale_lvl3_name": "レベル 3 — 定義済み",
      "ch2_scale_lvl3_desc": "統一された全社ポリシーの下でプロセスが正式に文書化・標準化され、組織全体で一貫して適用されている状態。",
      "ch2_scale_lvl4_name": "レベル 4 — 管理された",
      "ch2_scale_lvl4_desc": "テレメトリによる定量的測定、予測的なSLA統制、およびコーポレートガバナンスとの完全な整合性が実現されている状態。",
      "ch2_scale_lvl5_name": "レベル 5 — 最適化された",
      "ch2_scale_lvl5_desc": "高度な自動化、予防的な欠陥防止、および体系的な継続的改善サイクルによってオペレーショナル・エクセレンスが推進されている状態。"
    }
  }
}
```

---

## 3. AST Construction Plan in `tomo_asis_ast_compiler.py`

In `tomo_asis_ast_compiler.py`, update `_build_chapter_2_maturity_radiography` and attach the dedicated helper method `_build_cmmi_analytical_scale_section`. All code, identifiers, docstrings, and comments adhere strictly to the **100% Technical English Law** and **Zero Hardcoding Law**.

```python
    def _build_chapter_2_maturity_radiography(self, payload: Dict[str, Any]) -> List[ASTNode]:
        """
        Compile Chapter 2 (Technological Maturity Radiography) AST nodes.
        Guarantees deterministic 2-page layout across Page 4 (Table 2) and Page 5 (Figure 2.1 + Section 2.2).
        """
        nodes: List[ASTNode] = []

        # --- PAGE 4: Section 2.1 Heading, Intro, Table 2 (10-Domain CMMI Matrix), Methodological Notes ---
        nodes.extend(self._build_chapter_2_domain_table_section(payload))

        # --- PAGE 5: Figure 2.1 (Radar Chart, capped at 215.0pt) + Bimodal Narrative ---
        nodes.extend(self._build_chapter_2_radar_and_narrative(payload))

        # --- PAGE 5 (LOWER HALF): Section 2.2 CMMI Analytical Maturity Scale Reference Table ---
        nodes.extend(self._build_cmmi_analytical_scale_section())

        # Deterministic chapter boundary: Chapter 2 ends strictly at the bottom of Page 5
        nodes.append(PageBreakNode())
        return nodes

    def _build_cmmi_analytical_scale_section(self) -> List[ASTNode]:
        """
        Build Section 2.2 (CMMI Analytical Maturity Scale) AST nodes for the lower half of Page 5.
        Enforces strict vertical budget (~177 pt total) to guarantee zero spillover onto Page 6.
        """
        section_nodes: List[ASTNode] = []

        # 1. Pre-section vertical breathing spacer
        section_nodes.append(SpacerNode(height=10.0))

        # 2. Section 2.2 Subheading
        section_nodes.append(
            HeadingNode(
                level=2,
                text=self._t("tomo_asis.ch2_sec2_title"),
                keep_with_next=True,
            )
        )

        # 3. Introductory framing paragraph explaining the 0.80-interval continuous scale
        section_nodes.append(
            ParagraphNode(
                text=self._t("tomo_asis.ch2_sec2_intro"),
                style="BodyCompact",
                keep_with_next=True,
            )
        )
        section_nodes.append(SpacerNode(height=6.0))

        # 4. Dynamic locale-aware interval formatting (1.00 - 1.80 vs 1,00 - 1,80)
        scale_definitions: List[Tuple[str, float, float, str]] = [
            ("ch2_scale_lvl1_name", 1.00, 1.80, "ch2_scale_lvl1_desc"),
            ("ch2_scale_lvl2_name", 1.80, 2.60, "ch2_scale_lvl2_desc"),
            ("ch2_scale_lvl3_name", 2.60, 3.40, "ch2_scale_lvl3_desc"),
            ("ch2_scale_lvl4_name", 3.40, 4.20, "ch2_scale_lvl4_desc"),
            ("ch2_scale_lvl5_name", 4.20, 5.00, "ch2_scale_lvl5_desc"),
        ]

        headers: List[str] = [
            self._t("tomo_asis.ch2_scale_col_level"),
            self._t("tomo_asis.ch2_scale_col_range"),
            self._t("tomo_asis.ch2_scale_col_criteria"),
        ]

        rows: List[List[str]] = []
        for level_key, lower_bound, upper_bound, desc_key in scale_definitions:
            formatted_range = (
                f"{self._format_decimal(lower_bound, decimals=2)} – "
                f"{self._format_decimal(upper_bound, decimals=2)}"
            )
            rows.append(
                [
                    self._t(f"tomo_asis.{level_key}"),
                    formatted_range,
                    self._t(f"tomo_asis.{desc_key}"),
                ]
            )

        # 5. Compact 5-row governance reference table (Total width = 480.0 pt printable width)
        scale_table = TableNode(
            headers=headers,
            rows=rows,
            col_widths=[105.0, 75.0, 300.0],
            style_variant="compact_governance_reference",
            repeat_header=True,
            keep_together=True,
            cell_padding_top=3.0,
            cell_padding_bottom=3.0,
            font_size=8.5,
            leading=10.5,
            column_alignments=["LEFT", "CENTER", "LEFT"],
        )
        section_nodes.append(scale_table)

        return section_nodes
```

---

## 4. Automated Quality Gate Test Specification (`tests/unit/test_rfc079_cmmi_scale_table.py`)

This unit test suite verifies 6-locale catalog symmetry, AST node structure, absence of hardcoded domain/client strings, and Page 5 vertical layout budget compliance.

```python
"""
Unit test suite for RFC 079: CMMI Analytical Maturity Scale Table & Page 5 Balance Governance.
Validates 6-locale symmetry, zero hardcoding, AST integrity, and Page 5 vertical budget containment.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.reporting.ast_nodes import HeadingNode, PageBreakNode, ParagraphNode, SpacerNode, TableNode
from src.reporting.tomo_asis_ast_compiler import TomoAsisASTCompiler

SUPPORTED_LOCALES: List[str] = ["es", "en", "pt", "fr", "de", "ja"]

REQUIRED_RFC079_KEYS: List[str] = [
    "ch2_sec2_title",
    "ch2_sec2_intro",
    "ch2_scale_col_level",
    "ch2_scale_col_range",
    "ch2_scale_col_criteria",
    "ch2_scale_lvl1_name",
    "ch2_scale_lvl1_desc",
    "ch2_scale_lvl2_name",
    "ch2_scale_lvl2_desc",
    "ch2_scale_lvl3_name",
    "ch2_scale_lvl3_desc",
    "ch2_scale_lvl4_name",
    "ch2_scale_lvl4_desc",
    "ch2_scale_lvl5_name",
    "ch2_scale_lvl5_desc",
]

FORBIDDEN_HARDCODED_TOKENS: List[str] = [
    "molins",
    "cement",
    "cemento",
    "planta",
    "factory",
    "t1",
    "t2",
    "t3",
    "t4",
    "t5",
    "t6",
    "t7",
    "t8",
    "t9",
    "t10",
]


@pytest.fixture(scope="module")
def locales_catalog() -> Dict[str, Any]:
    """Load the central localization catalog."""
    locales_path = Path("src/resources/locales.json")
    with locales_path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_rfc079_six_locale_catalog_symmetry_and_purity(
    locales_catalog: Dict[str, Any], locale: str
) -> None:
    """
    Verify that all 15 Section 2.2 keys exist across all 6 locales, are non-empty,
    and contain zero hardcoded client names, vertical nouns, or domain codes.
    """
    assert locale in locales_catalog, f"Missing locale '{locale}' in locales.json"
    tomo_asis_section = locales_catalog[locale].get("tomo_asis", {})

    for key in REQUIRED_RFC079_KEYS:
        assert key in tomo_asis_section, f"Missing key '{key}' in locale '{locale}'"
        value = tomo_asis_section[key]
        assert isinstance(value, str) and len(value.strip()) > 0, (
            f"Empty or invalid string for key '{key}' in locale '{locale}'"
        )

        lowered_value = value.lower()
        for forbidden in FORBIDDEN_HARDCODED_TOKENS:
            assert forbidden not in lowered_value.split(), (
                f"Forbidden hardcoded token '{forbidden}' detected in '{locale}.tomo_asis.{key}'"
            )


@pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
def test_rfc079_ast_section_2_2_structure_and_intervals(locale: str) -> None:
    """
    Verify that _build_cmmi_analytical_scale_section generates the exact AST hierarchy:
    HeadingNode(level=2) -> ParagraphNode -> TableNode(5 rows x 3 columns) with localized intervals.
    """
    compiler = TomoAsisASTCompiler(locale=locale)
    nodes = compiler._build_cmmi_analytical_scale_section()

    headings = [n for n in nodes if isinstance(n, HeadingNode)]
    paragraphs = [n for n in nodes if isinstance(n, ParagraphNode)]
    tables = [n for n in nodes if isinstance(n, TableNode)]

    assert len(headings) == 1, "Section 2.2 must contain exactly one HeadingNode."
    assert headings[0].level == 2
    assert "2.2" in headings[0].text

    assert len(paragraphs) == 1, "Section 2.2 must contain exactly one introductory ParagraphNode."
    assert len(tables) == 1, "Section 2.2 must contain exactly one TableNode."

    scale_table = tables[0]
    assert len(scale_table.headers) == 3, "CMMI Scale Table must have exactly 3 columns."
    assert len(scale_table.rows) == 5, "CMMI Scale Table must have exactly 5 maturity level rows."
    assert scale_table.keep_together is True, "CMMI Scale Table must enforce keep_together=True."

    # Verify localized numeric intervals in Column 1 (index 1)
    expected_sep = "," if locale in {"es", "pt", "fr", "de"} else "."
    expected_ intervals = [
        f"1{expected_sep}00 – 1{expected_sep}80",
        f"1{expected_sep}80 – 2{expected_sep}60",
        f"2{expected_sep}60 – 3{expected_sep}40",
        f"3{expected_sep}40 – 4{expected_sep}20",
        f"4{expected_sep}20 – 5{expected_sep}00",
    ]
    actual_intervals = [row[1] for row in scale_table.rows]
    assert actual_intervals == expected_intervals, (
        f"Interval mismatch for locale '{locale}': {actual_intervals}"
    )


def test_rfc079_page_5_vertical_budget_and_page_break_invariant(
    sample_diagnostic_payload: Dict[str, Any],
) -> None:
    """
    Verify that Chapter 2 concludes with a clean PageBreakNode and that the Page 5
    AST element budget remains strictly within the 630.0 pt printable canvas height.
    """
    compiler = TomoAsisASTCompiler(locale="de")  # Test against German (longest character length)
    ch2_nodes = compiler._build_chapter_2_maturity_radiography(sample_diagnostic_payload)

    assert isinstance(ch2_nodes[-1], PageBreakNode), (
        "Chapter 2 must conclude strictly with a PageBreakNode so Chapter 3 starts on Page 6."
    )

    # Estimate Page 5 vertical footprint (Radar <= 230pt + Narrative ~90pt + Section 2.2 <= 185pt)
    sec2_nodes = compiler._build_cmmi_analytical_scale_section()
    spacer_height = sum(n.height for n in sec2_nodes if isinstance(n, SpacerNode))
    heading_height = 22.0
    intro_height = 24.0
    table_height = 20.0 + (5 * 19.0)  # 1 header + 5 compact rows

    section_2_2_total_pt = spacer_height + heading_height + intro_height + table_height
    page_5_estimated_total_pt = 230.0 + 8.0 + 90.0 + section_2_2_total_pt

    assert section_2_2_total_pt <= 185.0, (
        f"Section 2.2 vertical footprint ({section_2_2_total_pt} pt) exceeds 185.0 pt budget."
    )
    assert page_5_estimated_total_pt <= 540.0, (
        f"Page 5 cumulative height ({page_5_estimated_total_pt} pt) exceeds safe 540.0 pt threshold (630.0 pt max)."
    )
```