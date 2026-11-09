# RFC 030: Executive Summary Architecture Redesign, Locale Deterministic Propagation & C-Level Narrative Calibration

**Status:** Approved for Immediate Implementation  
**Author:** Principal Systems Architect & Executive Editorial Director  
**Target Subsystem:** `annex_executive_synthesizer` (LLM Synthesis Engine, AST Document Compiler, Localization Registry)  
**Compliance:** Universal Enterprise Readiness (Zero Hardcoding, 100% Technical English Codebase, Multi-Locale / Multi-Currency / Multi-Industry Agnostic)

---

## 1. Executive Summary & Architectural Diagnosis

A forensic audit of Chapter 1 (*Executive Summary*) across the generated Tower 1 and Tower 2 technical annexes revealed five structural and editorial deficiencies that degrade the C-level reading experience:

| Critique ID | Observed Symptom | Forensic Root Cause | Architectural Remediation |
| :--- | :--- | :--- | :--- |
| **C-01: Robotic Prose** | Choppy, telegraphic sentences lacking executive flow and persuasive narrative cadence. | `annex_executive_synthesizer.yaml` enforces an artificial constraint: *"STRICTLY PROHIBITED from writing sentences longer than 25 words. Average 15–18 words."* | Replace rigid word-count caps with **Pyramid Principle (Minto) Cadence Rules**: fluid, cohesive multi-clause analytical prose with natural transitions and varied sentence rhythm. |
| **C-02: Split-Brain Locale Anomaly** | Tower 1 outputs *"banda Definida"* (Spanish), while Tower 2 outputs *"banda Repeatable"* (English) inside a Spanish document. | In `run_executive_annex_synthesizer.py`, `build_executive_handover()` invokes `derive_maturity_band(average(scores))` without passing `locale=doc_lang`. It defaults to `None` (`en`), injecting `"Repeatable"` into the prompt context. | Thread `doc_lang` deterministically into `build_executive_handover()` and `derive_maturity_band(score, locale=doc_lang)`. Enforce strict prompt localization guards. |
| **C-03: Opaque Financial Exposure** | Quantitative risk metrics (ALE, P90) are buried mid-paragraph using dense actuarial jargon. | Financial exposure lacks a dedicated structural container in the AST and schema, forcing the LLM to cram actuarial figures into the general overview paragraph. | Promote Financial Exposure to a dedicated subsection (**1.2 Financial Exposure & Operational Risk**) backed by plain-language C-level explanations of *Expected Annual Friction* vs. *Tail-Risk Stress Scenarios*. |
| **C-04: Archaic Lexical Register** | Repeated use of archaic/bookish terms like *"fabril"* (*"operativa fabril"*, *"pesaje fabril"*). | Prompt lacked regional register calibration for modern European versus Latin American Spanish, causing the LLM to over-index on literary industrial adjectives. | Implement a **Locale Register Calibration Matrix** in the prompt configuration that bans archaic industrial adjectives (*"fabril"*) in favor of contemporary executive terminology (*"operaciones de planta"*, *"instalaciones productivas"*). |
| **C-05: Weak Visual Hierarchy** | Raw bullet list of "Business Impacts" feels tacked on; lacks scannable executive summary tables. | AST compiler (`payload_to_ast.py`) renders a flat paragraph stack + bullet list instead of structured executive scorecards and diagnostic synthesis tables. | Introduce a **4-Tier Executive Visual Architecture** in Chapter 1: (1) KPI Snapshot Scorecard Table, (2) Strategic Narrative & Diagnostic Thesis, (3) Executive Triad Table (*Strength / Gap / Bottleneck*), and (4) Dedicated Financial Exposure Subsection. |

---

## 2. Target Chapter 1 Visual & Structural Architecture

To meet Tier-1 management consulting standards (McKinsey / Gartner), Chapter 1 is restructured into four distinct, high-impact visual components rendered deterministically by the AST compiler:

```text
================================================================================
1. EXECUTIVE SUMMARY (RESUMEN EJECUTIVO)
================================================================================

[COMPONENT A: EXECUTIVE KPI SNAPSHOT TABLE (3-Column High-Contrast Scorecard)]
+---------------------------+---------------------------+----------------------+
| CURRENT MATURITY SCORE    | MATURITY BAND             | ANNUALIZED EXPOSURE  |
| 2.5 / 5.0                 | Repetible (Nivel 2)       | EUR 142,500 / yr     |
+---------------------------+---------------------------+----------------------+

[COMPONENT B: 1.1 SITUATION & DIAGNOSTIC THESIS (Prose Narrative)]
  • Paragraph 1: Operational Role & Strategic Context (Fluid prose explaining how
    the domain supports core enterprise operations and revenue continuity).
  • Paragraph 2: Structural Diagnosis & Maturity Reality (Cohesive synthesis of
    why the domain sits at its current maturity band and how architectural gaps
    manifest in day-to-day operations).

[COMPONENT C: EXECUTIVE DIAGNOSTIC TRIAD TABLE (Structured Synthesis)]
+---------------------------+--------------------------------------------------+
| DIAGNOSTIC DIMENSION      | EXECUTIVE ASSESSMENT & OPERATIONAL IMPACT        |
+---------------------------+--------------------------------------------------+
| Primary Structural        | Consolidated virtualization cluster with         |
| Strength                  | standardized hypervisor baseline...              |
+---------------------------+--------------------------------------------------+
| Primary Architectural     | Absence of automated cross-site failover and     |
| Gap                       | manual configuration drift across nodes...       |
+---------------------------+--------------------------------------------------+
| Primary Operational       | Single-point-of-failure dependency on legacy     |
| Bottleneck                | storage fabrics during peak plant shifts...      |
+---------------------------+--------------------------------------------------+

[COMPONENT D: 1.2 FINANCIAL EXPOSURE & OPERATIONAL RISK (Plain-Language Subsection)]
  • Plain-Language Risk Narrative: Explains the financial exposure without
    actuarial jargon. Clearly distinguishes between:
    1. Expected Annual Operational Friction (ALE): The recurring annual cost of
       incidents, micro-outages, and manual recovery hours.
    2. Severe Stress Scenario (P90 Tail Risk): The financial impact of a worst-case
       concurrent outage affecting critical business operations.
  • Financial Breakdown Callout / Mini-Table: Clean comparison of Expected Annual
    Cost vs. Severe Contingency Exposure, plus the primary risk driver.
================================================================================
```

---

## 3. Data Contract & Schema Evolution (`executive_summary_schema.py`)

We update the Pydantic contract for `ExecutiveSummaryBlock` to support the **Executive Diagnostic Triad** and the **Dedicated Financial Exposure Narrative**, eliminating ambiguous "forced bullet lists" while maintaining strict backwards compatibility.

```python
# src/annex_synthesizer/schemas/executive_summary_schema.py
from typing import List, Optional
from pydantic import BaseModel, Field


class ExecutiveTriadModel(BaseModel):
    """Structured diagnostic synthesis triad for C-level scannability."""

    primary_strength: str = Field(
        ...,
        description=(
            "The single most resilient architectural capability or operational asset "
            "currently protecting the domain, grounded in verified evidence."
        ),
    )
    primary_structural_gap: str = Field(
        ...,
        description=(
            "The core architectural deficiency or design vulnerability that prevents "
            "the domain from scaling or achieving higher resilience."
        ),
    )
    primary_operational_bottleneck: str = Field(
        ...,
        description=(
            "The immediate day-to-day operational friction point or single point of "
            "failure that degrades service delivery or recovery speed."
        ),
    )


class FinancialExposureNarrativeModel(BaseModel):
    """Plain-language C-level explanation of quantitative risk exposure."""

    plain_language_synthesis: str = Field(
        ...,
        description=(
            "Cohesive, accessible narrative (80-130 words) explaining the financial "
            "risk in plain business terms without dense actuarial acronyms. Must "
            "explain what drives the recurring annual cost and what a severe outage "
            "looks like in real operational terms."
        ),
    )
    expected_annual_friction_summary: str = Field(
        ...,
        description=(
            "One-sentence plain-language explanation of the Expected Annual Loss "
            "(recurring operational drag, downtime, and manual remediation)."
        ),
    )
    severe_stress_scenario_summary: str = Field(
        ...,
        description=(
            "One-sentence plain-language explanation of the 90th percentile tail-risk "
            "scenario (impact of a prolonged or concurrent failure during peak load)."
        ),
    )


class ExecutiveSummarySection(BaseModel):
    """Complete data contract for Chapter 1 (Executive Summary)."""

    situation_and_thesis_narrative: List[str] = Field(
        ...,
        min_length=2,
        max_length=3,
        description=(
            "2 to 3 cohesive, fluid executive paragraphs covering: (1) Strategic role "
            "of the technological domain within the enterprise, and (2) Diagnostic "
            "thesis explaining the current maturity score and structural reality."
        ),
    )
    diagnostic_triad: ExecutiveTriadModel = Field(
        ...,
        description="Structured 3-part synthesis of strength, gap, and bottleneck.",
    )
    financial_exposure_section: FinancialExposureNarrativeModel = Field(
        ...,
        description="Dedicated subsection explaining financial risk in plain language.",
    )
    key_business_impacts: Optional[List[str]] = Field(
        default_factory=list,
        description="Optional supplementary bullet points if needed for legacy compatibility.",
    )
```

---

## 4. Surgical Fix for Locale Split-Brain (`run_executive_annex_synthesizer.py`)

### Forensic Root Cause Analysis
In `run_executive_annex_synthesizer.py`, `build_executive_handover()` previously called `derive_maturity_band(avg_score)` without passing `locale=doc_lang`. Consequently:
1. `derive_maturity_band()` defaulted to `locale="en"`, returning `"Repeatable"` or `"Defined"`.
2. In Tower 1, the LLM happened to translate `"Defined"` into `"Definida"`. In Tower 2, the LLM treated `"Repeatable"` as an immutable technical token from the JSON payload and output *"banda Repeatable"* inside a Spanish sentence.

### Production Code Implementation

```python
# src/annex_synthesizer/run_executive_annex_synthesizer.py
from typing import Any, Dict, List, Optional
from src.common.localization import derive_maturity_band, get_localized_ui_labels


def calculate_arithmetic_mean(scores: List[float]) -> float:
    """Computes the deterministic arithmetic mean of domain sub-scores."""
    valid_scores = [float(s) for s in scores if s is not None]
    if not valid_scores:
        return 0.0
    return round(sum(valid_scores) / len(valid_scores), 1)


def format_currency_metric(
    amount: Optional[float],
    currency_code: str,
    locale: str,
) -> str:
    """Formats a monetary value deterministically according to ISO 4217 and locale conventions."""
    if amount is None:
        return "N/A"
    rounded_val = int(round(amount))
    # Locale-aware thousand separator formatting without hardcoded symbols
    if locale.lower().startswith(("es", "de", "it", "pt", "fr")):
        formatted_number = f"{rounded_val:,}".replace(",", ".")
    else:
        formatted_number = f"{rounded_val:,}"
    return f"{currency_code.upper()} {formatted_number}"


def build_executive_handover(
    domain_payload: Dict[str, Any],
    quantitative_risk_payload: Dict[str, Any],
    doc_lang: str,
    currency_code: str = "EUR",
) -> Dict[str, Any]:
    """
    Constructs the deterministic ground-truth context injected into the Executive Synthesizer LLM.
    Guarantees 100% locale consistency across all maturity bands and financial figures.
    """
    sub_scores: List[float] = [
        item.get("score", 0.0)
        for item in domain_payload.get("dimension_scores", [])
        if item.get("score") is not None
    ]
    global_score: float = domain_payload.get("global_score") or calculate_arithmetic_mean(sub_scores)

    # SURGICAL FIX (Critique 2): Explicitly pass `locale=doc_lang` so maturity bands
    # are deterministically resolved in the target document language (never defaulting to English).
    localized_band: str = derive_maturity_band(
        score=global_score,
        locale=doc_lang,
    )

    ale_value: Optional[float] = quantitative_risk_payload.get("annualized_loss_expectancy")
    p90_value: Optional[float] = quantitative_risk_payload.get("tail_risk_p90")

    return {
        "document_locale": doc_lang,
        "currency_code": currency_code,
        "domain_id": domain_payload.get("domain_id", ""),
        "domain_name": domain_payload.get("domain_name", ""),
        "global_score": f"{global_score:.1f}",
        "scale_max": "5.0",
        "global_band": localized_band,
        "financial_exposure": {
            "expected_annual_loss_formatted": format_currency_metric(ale_value, currency_code, doc_lang),
            "severe_stress_p90_formatted": format_currency_metric(p90_value, currency_code, doc_lang),
            "raw_ale": ale_value,
            "raw_p90": p90_value,
            "primary_risk_scenarios": quantitative_risk_payload.get("top_scenarios", []),
        },
        "verified_strengths": domain_payload.get("verified_strengths", []),
        "verified_gaps": domain_payload.get("verified_gaps", []),
        "operational_bottlenecks": domain_payload.get("operational_bottlenecks", []),
    }
```

---

## 5. Localization Registry Upgrade (`localization.py`)

To satisfy **Law 2 (Zero Hardcoding / Universal Enterprise Readiness)**, all section headers, table column headers, and maturity band labels are resolved dynamically from a central locale registry supporting any enterprise language.

```python
# src/common/localization.py
from typing import Dict

MATURITY_BAND_REGISTRY: Dict[str, Dict[str, str]] = {
    "en": {
        "band_1": "Initial",
        "band_2": "Repeatable",
        "band_3": "Defined",
        "band_4": "Managed",
        "band_5": "Optimized",
    },
    "es": {
        "band_1": "Inicial",
        "band_2": "Repetible",
        "band_3": "Definida",
        "band_4": "Gestionada",
        "band_5": "Optimizada",
    },
    "pt": {
        "band_1": "Inicial",
        "band_2": "Repetível",
        "band_3": "Definido",
        "band_4": "Gerenciado",
        "band_5": "Otimizado",
    },
    "de": {
        "band_1": "Initial",
        "band_2": "Wiederholbar",
        "band_3": "Definiert",
        "band_4": "Gesteuert",
        "band_5": "Optimiert",
    },
    "fr": {
        "band_1": "Initial",
        "band_2": "Répétable",
        "band_3": "Défini",
        "band_4": "Géré",
        "band_5": "Optimisé",
    },
}

CHAPTER_1_UI_LABELS: Dict[str, Dict[str, str]] = {
    "en": {
        "ch1_title": "1. Executive Summary",
        "sub_1_1_title": "1.1 Strategic Context & Diagnostic Thesis",
        "sub_1_2_title": "1.2 Financial Exposure & Operational Risk",
        "kpi_score_header": "CURRENT SCORE",
        "kpi_band_header": "MATURITY BAND",
        "kpi_exposure_header": "EXPECTED ANNUAL EXPOSURE",
        "triad_col_dimension": "DIAGNOSTIC DIMENSION",
        "triad_col_finding": "EXECUTIVE ASSESSMENT & OPERATIONAL REALITY",
        "triad_row_strength": "Primary Structural Strength",
        "triad_row_gap": "Primary Architectural Gap",
        "triad_row_bottleneck": "Primary Operational Bottleneck",
        "fin_col_metric": "RISK SCENARIO",
        "fin_col_figure": "ESTIMATED IMPACT",
        "fin_col_meaning": "BUSINESS & OPERATIONAL INTERPRETATION",
        "fin_row_ale": "Expected Annual Operational Friction",
        "fin_row_p90": "Severe Stress Scenario (Tail Risk)",
        "per_year_suffix": "/ yr",
    },
    "es": {
        "ch1_title": "1. Resumen Ejecutivo",
        "sub_1_1_title": "1.1 Contexto Estratégico y Tesis Diagnóstica",
        "sub_1_2_title": "1.2 Exposición Financiera y Riesgo Operativo",
        "kpi_score_header": "PUNTUACIÓN ACTUAL",
        "kpi_band_header": "BANDA DE MADUREZ",
        "kpi_exposure_header": "EXPOSICIÓN ANUAL ESPERADA",
        "triad_col_dimension": "DIMENSIÓN DIAGNÓSTICA",
        "triad_col_finding": "EVALUACIÓN EJECUTIVA Y REALIDAD OPERATIVA",
        "triad_row_strength": "Fortaleza Estructural Principal",
        "triad_row_gap": "Brecha Arquitectónica Principal",
        "triad_row_bottleneck": "Cuello de Botella Operativo",
        "fin_col_metric": "ESCENARIO DE RIESGO",
        "fin_col_figure": "IMPACTO ESTIMADO",
        "fin_col_meaning": "INTERPRETACIÓN DE NEGOCIO Y OPERACIONES",
        "fin_row_ale": "Fricción Operativa Anual Esperada",
        "fin_row_p90": "Escenario de Estrés Severo (Riesgo Extremo)",
        "per_year_suffix": "/ año",
    },
}


def normalize_locale_key(locale: Optional[str]) -> str:
    """Extracts the primary ISO 639-1 language code (e.g., 'es-ES' -> 'es')."""
    if not locale:
        return "en"
    base_lang = locale.strip().lower().split("_")[0].split("-")[0]
    return base_lang if base_lang in MATURITY_BAND_REGISTRY else "en"


def derive_maturity_band(score: float, locale: Optional[str] = "en") -> str:
    """
    Deterministically maps a numeric maturity score (1.0 - 5.0) to its localized band name.
    Eliminates cross-language token leakage.
    """
    lang_key = normalize_locale_key(locale)
    bands = MATURITY_BAND_REGISTRY[lang_key]

    if score < 1.8:
        return bands["band_1"]
    if score < 2.6:
        return bands["band_2"]
    if score < 3.4:
        return bands["band_3"]
    if score < 4.2:
        return bands["band_4"]
    return bands["band_5"]


def get_localized_ui_labels(locale: Optional[str] = "en") -> Dict[str, str]:
    """Returns the localized UI label dictionary for Chapter 1 AST compilation."""
    lang_key = normalize_locale_key(locale)
    return CHAPTER_1_UI_LABELS.get(lang_key, CHAPTER_1_UI_LABELS["en"])
```

---

## 6. Upstream Prompt Rewrite (`annex_executive_synthesizer.yaml`)

This rewrite directly resolves **Critique 1 (Robotic Prose)**, **Critique 2 (Language Purity)**, **Critique 3 (Plain-Language Financial Subsection)**, and **Critique 4 (Eliminating archaic terms like "fabril")**.

```yaml
# src/annex_synthesizer/prompts/annex_executive_synthesizer.yaml
version: "3.0.0"
id: "annex_executive_synthesizer_v3"
description: >
  Tier-1 Executive Summary Synthesizer (McKinsey / Gartner Editorial Standard).
  Generates fluid, authoritative C-level prose, a structured Diagnostic Triad,
  and an accessible Plain-Language Financial Exposure narrative.

system_prompt: |
  You are a Senior Partner at a Tier-1 Global Management & Technology Consulting Firm.
  Your task is to author Chapter 1 (Executive Summary) of a Board-level Technical Annex
  evaluating a specific enterprise technology domain.

  ==============================================================================
  1. EDITORIAL CADENCE & PROSE ARCHITECTURE (ANTI-ROBOTIC MANDATE)
  ==============================================================================
  - WRITE FLUID, PERSUASIVE EXECUTIVE PROSE: Write with the natural rhythm, cohesion,
    and analytical depth of a McKinsey or Gartner executive briefing.
  - VARIED SENTENCE CADENCE: Combine crisp declarative topic sentences with richer,
    multi-clause analytical sentences (typically 18 to 32 words) that connect cause,
    architectural mechanism, and business consequence using natural logical transitions.
  - NO TELEGRAPHIC OR STILTED CHOPPINESS: Never write robotic chains of short,
    disconnected sentences. Every paragraph must read as a unified, flowing argument.
  - ZERO META-LANGUAGE: Never mention "this report", "the diagnostic", "the rubric",
    or "the assessment". Speak directly about the technology domain and enterprise reality.

  ==============================================================================
  2. LANGUAGE PURITY & REGIONAL REGISTER CALIBRATION
  ==============================================================================
  - TARGET LOCALE: You must write 100% of your output in the exact language and
    regional standard specified by `document_locale` ({{ document_locale }}).
  - ZERO SPLIT-BRAIN / ZERO UNTRANSLATED TOKENS: Never leak English maturity band
    names (such as "Repeatable", "Defined", "Managed") into non-English text. Always
    use the exact localized `global_band` provided in the ground-truth payload
    (e.g., "{{ global_band }}").
  - NATURAL CONTEMPORARY REGISTER:
    * If `document_locale` is `es` or `es-ES` (European / Castilian Spanish): Use
      clear, natural, contemporary corporate Spanish.
    * STRICT LEXICAL BAN ON ARCHAIC ADJECTIVES: In Spanish, NEVER use the archaic/bookish
      word "fabril" (e.g., do NOT write "operativa fabril", "entorno fabril", "pesaje fabril").
      Instead, use natural modern executive expressions: "operaciones de planta",
      "instalaciones productivas", "entornos industriales", "centros de producción",
      or "líneas de fabricación".
    * If `document_locale` is `es-LA` / `es-MX` / `es-CO`: Use natural Latin American
      executive Spanish ("operaciones de planta", "instalaciones industriales").

  ==============================================================================
  3. STRUCTURAL REQUIREMENTS FOR CHAPTER 1
  ==============================================================================
  You must populate the JSON schema with three coordinated analytical blocks:

  A. `situation_and_thesis_narrative` (2 paragraphs of fluid executive prose):
     - Paragraph 1 (Strategic Role & Operational Reality): Explain the mission-critical
       role this technology domain plays in supporting the organization's core operations,
       revenue continuity, and service delivery.
     - Paragraph 2 (Diagnostic Thesis & Maturity Reality): State the current maturity
       score ({{ global_score }} / {{ scale_max }}) and its localized maturity band
       ({{ global_band }}) naturally within the prose. Explain *why* the domain sits at
       this level by connecting its architectural design to its day-to-day operational
       stability—without dumping raw financial numbers here (reserve financial figures
       for the dedicated financial section).

  B. `diagnostic_triad` (Structured Executive Synthesis):
     - `primary_strength`: The foundational capability or architectural asset currently
       anchoring operational stability (1–2 crisp sentences, grounded in verified facts).
     - `primary_structural_gap`: The core architectural design flaw or missing control
       preventing higher maturity (1–2 crisp sentences).
     - `primary_operational_bottleneck`: The concrete operational point of friction,
       manual dependency, or single point of failure that slows daily operations or
       incident recovery (1–2 crisp sentences).

  C. `financial_exposure_section` (Accessible C-Level Risk Narrative):
     - Explain the financial risk in clear, plain business language so a CEO, CFO, or
       COO immediately grasps the economic stakes without needing a background in
       actuarial science.
     - STRICT JARGON BAN IN FINANCIAL NARRATIVE: Do NOT use raw acronyms like "ALE",
       "P90", "Monte Carlo", or "Open FAIR".
     - Instead, clearly contrast two plain-language concepts using the exact figures
       provided in `financial_exposure`:
       1. Expected Annual Operational Friction ({{ financial_exposure.expected_annual_loss_formatted }}):
          Explain that this represents the recurring yearly cost caused by operational
          degradations, micro-outages, manual firefighting, and productivity drag.
       2. Severe Stress Scenario ({{ financial_exposure.severe_stress_p90_formatted }}):
          Explain that this represents the financial impact of a severe, compounding
          contingency (such as a prolonged outage hitting critical operational windows).

user_prompt: |
  Synthesize Chapter 1 (Executive Summary) strictly adhering to the system instructions
  and the following verified ground-truth payload:

  ```json
  {{ executive_handover_json }}
  ```text
```

---

## 7. AST Document Compiler Redesign (`payload_to_ast.py`)

This update implements the 4-part visual layout in the Document Compiler AST, addressing **Critique 3 (Dedicated Financial Subsection)** and **Critique 5 (Scorecard & Executive Triad Tables)**.

```python
# src/document_compiler/payload_to_ast.py
from typing import Any, Dict, List
from src.common.localization import get_localized_ui_labels
from src.document_compiler.ast_nodes import (
    ASTNode,
    HeadingNode,
    ParagraphNode,
    TableNode,
    TableRowNode,
    TableCellNode,
)


def compile_chapter_1_executive_summary_ast(
    synthesized_exec_summary: Dict[str, Any],
    handover_context: Dict[str, Any],
    doc_lang: str,
) -> List[ASTNode]:
    """
    Compiles Chapter 1 (Executive Summary) into a Tier-1 consulting visual hierarchy:
      1. Chapter 1 Main Heading
      2. Component A: 3-Column Executive KPI Snapshot Scorecard Table
      3. Component B: Subsection 1.1 (Strategic Context & Diagnostic Thesis Prose)
      4. Component C: Executive Diagnostic Triad Table (Strength / Gap / Bottleneck)
      5. Component D: Subsection 1.2 (Financial Exposure & Operational Risk + Summary Table)
    """
    labels = get_localized_ui_labels(doc_lang)
    ast_nodes: List[ASTNode] = []

    # 1. Chapter Heading
    ast_nodes.append(
        HeadingNode(level=1, text=labels["ch1_title"], style="ChapterHeading")
    )

    # 2. Component A: Executive KPI Snapshot Table (Score | Maturity Band | Annual Exposure)
    score_display = f"{handover_context.get('global_score', '0.0')} / {handover_context.get('scale_max', '5.0')}"
    band_display = handover_context.get("global_band", "")
    fin_ctx = handover_context.get("financial_exposure", {})
    ale_display = (
        f"{fin_ctx.get('expected_annual_loss_formatted', 'N/A')} {labels['per_year_suffix']}"
    )

    kpi_snapshot_table = TableNode(
        style="ExecutiveKpiScorecard",
        column_widths_pct=[33.3, 33.3, 33.4],
        headers=[
            TableCellNode(text=labels["kpi_score_header"], is_header=True),
            TableCellNode(text=labels["kpi_band_header"], is_header=True),
            TableCellNode(text=labels["kpi_exposure_header"], is_header=True),
        ],
        rows=[
            TableRowNode(
                cells=[
                    TableCellNode(text=score_display, emphasis="bold_large"),
                    TableCellNode(text=band_display, emphasis="bold_accent"),
                    TableCellNode(text=ale_display, emphasis="bold_warning"),
                ]
            )
        ],
    )
    ast_nodes.append(kpi_snapshot_table)

    # 3. Component B: 1.1 Strategic Context & Diagnostic Thesis
    ast_nodes.append(
        HeadingNode(level=2, text=labels["sub_1_1_title"], style="SectionHeading")
    )

    narrative_paragraphs: List[str] = synthesized_exec_summary.get(
        "situation_and_thesis_narrative", []
    )
    for paragraph_text in narrative_paragraphs:
        if paragraph_text and paragraph_text.strip():
            ast_nodes.append(
                ParagraphNode(text=paragraph_text.strip(), style="ExecutiveBodyProse")
            )

    # 4. Component C: Executive Diagnostic Triad Table (Strength / Gap / Bottleneck)
    triad_data: Dict[str, str] = synthesized_exec_summary.get("diagnostic_triad", {})
    if triad_data:
        triad_table = TableNode(
            style="ExecutiveTriadTable",
            column_widths_pct=[30.0, 70.0],
            headers=[
                TableCellNode(text=labels["triad_col_dimension"], is_header=True),
                TableCellNode(text=labels["triad_col_finding"], is_header=True),
            ],
            rows=[
                TableRowNode(
                    cells=[
                        TableCellNode(
                            text=labels["triad_row_strength"], emphasis="bold_positive"
                        ),
                        TableCellNode(text=triad_data.get("primary_strength", "")),
                    ]
                ),
                TableRowNode(
                    cells=[
                        TableCellNode(
                            text=labels["triad_row_gap"], emphasis="bold_warning"
                        ),
                        TableCellNode(
                            text=triad_data.get("primary_structural_gap", "")
                        ),
                    ]
                ),
                TableRowNode(
                    cells=[
                        TableCellNode(
                            text=labels["triad_row_bottleneck"], emphasis="bold_critical"
                        ),
                        TableCellNode(
                            text=triad_data.get("primary_operational_bottleneck", "")
                        ),
                    ]
                ),
            ],
        )
        ast_nodes.append(triad_table)

    # 5. Component D: 1.2 Financial Exposure & Operational Risk (Plain-Language Subsection)
    fin_section: Dict[str, str] = synthesized_exec_summary.get(
        "financial_exposure_section", {}
    )
    if fin_section:
        ast_nodes.append(
            HeadingNode(level=2, text=labels["sub_1_2_title"], style="SectionHeading")
        )

        plain_synthesis = fin_section.get("plain_language_synthesis", "").strip()
        if plain_synthesis:
            ast_nodes.append(
                ParagraphNode(text=plain_synthesis, style="ExecutiveBodyProse")
            )

        p90_display = fin_ctx.get("severe_stress_p90_formatted", "N/A")

        financial_summary_table = TableNode(
            style="FinancialRiskExecutiveTable",
            column_widths_pct=[28.0, 22.0, 50.0],
            headers=[
                TableCellNode(text=labels["fin_col_metric"], is_header=True),
                TableCellNode(text=labels["fin_col_figure"], is_header=True),
                TableCellNode(text=labels["fin_col_meaning"], is_header=True),
            ],
            rows=[
                TableRowNode(
                    cells=[
                        TableCellNode(text=labels["fin_row_ale"], emphasis="bold"),
                        TableCellNode(text=ale_display, emphasis="bold_warning"),
                        TableCellNode(
                            text=fin_section.get(
                                "expected_annual_friction_summary", ""
                            )
                        ),
                    ]
                ),
                TableRowNode(
                    cells=[
                        TableCellNode(text=labels["fin_row_p90"], emphasis="bold"),
                        TableCellNode(text=p90_display, emphasis="bold_critical"),
                        TableCellNode(
                            text=fin_section.get("severe_stress_scenario_summary", "")
                        ),
                    ]
                ),
            ],
        )
        ast_nodes.append(financial_summary_table)

    return ast_nodes
```

---

## 8. Before vs. After Editorial Preview (Spanish `es-ES` Target Output)

To illustrate how these changes transform the output for Tower 2 (Compute / Virtualization), compare the previous output against the new calibrated architecture:

### BEFORE (Defective Output)
> **1. Resumen Ejecutivo**  
> La torre da soporte a la operativa fabril. Centraliza las cargas críticas de pesaje fabril. La evaluación sitúa la madurez de la torre en 2.5 dentro de la banda **Repeatable**. Existe una exposición financiera con un ALE de 142.500 EUR y un P90 de 380.000 EUR según el modelo Open FAIR.  
> **Principales impactos de negocio:**  
> - Parada de contingencia fabril.

### AFTER (RFC 030 Calibrated Output)

> ## 1. Resumen Ejecutivo
>
> | PUNTUACIÓN ACTUAL | BANDA DE MADUREZ | EXPOSICIÓN ANUAL ESPERADA |
> | :---: | :---: | :---: |
> | **2.5 / 5.0** | **Repetible** | **EUR 142.500 / año** |
>
> ### 1.1 Contexto Estratégico y Tesis Diagnóstica
> La plataforma de cómputo y virtualización constituye el núcleo operativo sobre el que descansan los sistemas de gestión empresarial y el control de las líneas de producción en las instalaciones productivas. Su disponibilidad continua resulta indispensable para coordinar la trazabilidad logística, la expedición de mercancías y las operaciones de planta en tiempo real sin interrupciones en la cadena de suministro.
>
> El análisis técnico sitúa la madurez del dominio en **2.5 sobre 5.0**, dentro de la banda **Repetible**. Aunque la organización ha consolidado sus servidores físicos en clústeres de virtualización estandarizados que garantizan la operativa diaria en condiciones normales, la arquitectura carece de mecanismos automatizados de recuperación ante desastres entre emplazamientos y presenta una alta dependencia de intervenciones manuales para absorber picos de demanda o fallos de hardware.
>
> | DIMENSIÓN DIAGNÓSTICA | EVALUACIÓN EJECUTIVA Y REALIDAD OPERATIVA |
> | :--- | :--- |
> | **Fortaleza Estructural Principal** | Consolidación efectiva de cargas críticas sobre hipervisores estandarizados con alta disponibilidad local a nivel de host. |
> | **Brecha Arquitectónica Principal** | Ausencia de orquestación automatizada para la conmutación por error (failover) entre centros de datos y falta de estandarización en el aprovisionamiento. |
> | **Cuello de Botella Operativo** | Dependencia crítica de tareas manuales de administración y reconfiguración durante ventanas de mantenimiento o incidencias en turnos de máxima actividad en planta. |
>
> ### 1.2 Exposición Financiera y Riesgo Operativo
> La vulnerabilidad estructural de la plataforma de cómputo se traduce en un impacto económico directo sobre la cuenta de resultados, derivado tanto de pequeñas interrupciones operativas recurrentes como del riesgo de una parada prolongada en los sistemas centrales de gestión y producción. En lugar de ser un coste teórico, esta exposición refleja el valor de las horas de producción detenidas, los retrasos en expediciones y el esfuerzo técnico dedicado a resolver incidencias de forma reactiva.
>
> | ESCENARIO DE RIESGO | IMPACTO ESTIMADO | INTERPRETACIÓN DE NEGOCIO Y OPERACIONES |
> | :--- | :---: | :--- |
> | **Fricción Operativa Anual Esperada** | **EUR 142.500 / año** | Coste anual previsible generado por micro-cortes del servicio, degradación del rendimiento en aplicaciones de planta y horas de ingeniería dedicadas a tareas correctivas manuales. |
> | **Escenario de Estrés Severo (Riesgo Extremo)** | **EUR 380.000** | Impacto financiero de una caída grave y simultánea de los nodos principales durante un pico de actividad productiva, provocando la paralización temporal de las líneas de expedición y facturación. |

---

## 9. Verification & Regression Test Suite

```python
# tests/annex_synthesizer/test_rfc030_executive_summary.py
import pytest
from src.common.localization import derive_maturity_band
from src.annex_synthesizer.run_executive_annex_synthesizer import build_executive_handover


def test_derive_maturity_band_strict_locale_isolation():
    """Verifies Critique 2 fix: Maturity bands never leak English tokens into non-English locales."""
    assert derive_maturity_band(2.5, locale="es") == "Repetible"
    assert derive_maturity_band(2.5, locale="es-ES") == "Repetible"
    assert derive_maturity_band(2.6, locale="es") == "Definida"
    assert derive_maturity_band(2.5, locale="en") == "Repeatable"
    assert derive_maturity_band(2.6, locale="en") == "Defined"


def test_build_executive_handover_propagates_locale_and_currency():
    """Verifies zero hardcoding and deterministic locale propagation in handover payload."""
    domain_payload = {
        "domain_id": "T2",
        "domain_name": "Compute & Virtualization",
        "dimension_scores": [{"score": 2.4}, {"score": 2.6}],
    }
    risk_payload = {
        "annualized_loss_expectancy": 142500.0,
        "tail_risk_p90": 380000.0,
    }

    handover_es = build_executive_handover(
        domain_payload=domain_payload,
        quantitative_risk_payload=risk_payload,
        doc_lang="es-ES",
        currency_code="EUR",
    )

    assert handover_es["global_score"] == "2.5"
    assert handover_es["global_band"] == "Repetible"
    assert handover_es["financial_exposure"]["expected_annual_loss_formatted"] == "EUR 142.500"
    assert handover_es["financial_exposure"]["severe_stress_p90_formatted"] == "EUR 380.000"
```