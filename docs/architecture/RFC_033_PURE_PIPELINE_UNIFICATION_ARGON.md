# RFC 033: Unified Single-Payload Contract (`EnrichedTowerPayload`), Pure Upstream Lexical Governance, and Single-Page Executive Summary Architecture

**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Classification:** Tier-1 Core Compiler & Pipeline Architecture  
**Target Modules:**  
- `src/domain/contracts/types_payload.py`  
- `src/application/services/blueprint_service.py`  
- `src/infrastructure/adapters/rendering/ast/payload_to_ast.py`  
- `src/infrastructure/prompts/annex_executive_synthesizer.yaml`  

---

## 1. Architectural Post-Mortem & Resolution of the Two Dialectical Challenges

### 1.1 Challenge 1: Why `approved_annex_{tower}.template_payload.json` is a Split-Brain Anti-Pattern

Your instinct is 100% architecturally sound. Maintaining two parallel JSON artifacts per tower (`blueprint_{tower}_payload.json` and `approved_annex_{tower}.template_payload.json`) is a classic **Split-Brain State Anti-Pattern** and a leftover from an earlier transitional phase of the codebase:

1. **Violation of the Single Source of Truth (SSOT):**  
   In a pure compiler pipeline, each stage must have a strict, bijective contract:
   $$\text{Raw Forensics} \xrightarrow{\text{Enrichment}} \text{EnrichedTowerPayload (JSON)} \xrightarrow{\text{AST Compiler}} \text{DocumentAST} \xrightarrow{\text{Renderer}} \text{DOCX}$$
   Having `payload_to_ast.py` consume a secondary file (`approved_annex_{tower}.template_payload.json`) creates state divergence. If `blueprint_t2_payload.json` is updated or regenerated, the template payload can become stale or require a separate synchronization step.
2. **Non-Reproducibility of Manual JSON Edits:**  
   Touching or patching a serialized JSON artifact on disk (`approved_annex_t2.template_payload.json`) to fix a word is a manual hack. The moment the pipeline runs for T3, T4, or a new enterprise client (e.g., a multinational hospital or a Tier-1 investment bank), any manual disk edit is overwritten or absent.
3. **Uniformity Across All Towers (T1–T10):**  
   All towers must share the exact same canonical data contract: `EnrichedTowerPayload` (the strict 21-key schema). There should be **zero** structural distinction between a "blueprint payload" and a "template payload."

#### Architectural Resolution: Single Canonical Payload Pipeline
We deprecate and eliminate the split-brain dependency on `approved_annex_{tower}.template_payload.json`:
- **`EnrichedTowerPayload` (`blueprint_{tower}_payload.json`) is the single, immutable source of truth** across all towers (T1–T10).
- `BlueprintService.compile_tower_payload()` writes the validated 21-key `EnrichedTowerPayload` directly to `blueprint_{tower}_payload.json`. (If legacy CLI scripts still look for `approved_annex_{tower}.template_payload.json`, the service simply symlinks or mirrors the exact same canonical dict at save time, never diverging in schema or content).
- `PayloadToAstCompiler` ingests `EnrichedTowerPayload` directly and deterministically compiles Chapters 1 through 6 without any intermediate translation artifact.

---

### 1.2 Challenge 2: Why Regex Word-Patching (`re.sub(r"\bfabril\b", ...)`) in Python is an Anti-Pattern

Your second objection hits at the heart of **Universal Enterprise Architecture**:
- **Domain & Language Leakage in the Compiler:**  
  `payload_to_ast.py` is a **deterministic structural compiler**, not a Spanish copy-editor for manufacturing plants. Hardcoding `re.sub(r"\bfabril\b", "de planta", ...)` inside Python code violates Separation of Concerns (SoC) and Zero Hardcoding laws. What happens when the engine evaluates a Swiss pharmaceutical conglomerate in German, a Wall Street clearinghouse in English, or a retail bank in Spanish? A hardcoded replacement of `"fabril" -> "de planta"` in the compiler is dead weight at best and corrupts legitimate terminology at worst.
- **Where Lexical Register Actually Belongs:**  
  Why did the LLM emit the overly literary adjective *"fabril"* in the first place? Because the prompt in `annex_executive_synthesizer.yaml` lacked an explicit **Lexical Register Constraint** instructing the model to use standard, direct corporate and operational terminology native to the client's industry vertical, rather than archaic or poetic synonyms.

#### Architectural Resolution: Pure Upstream Prompt Governance + Dynamic Financial Grounding
1. **Zero Regex Word-Patching in Python:** We completely forbid hardcoded vocabulary regexes inside `payload_to_ast.py`.
2. **Upstream Prompt Engineering (`annex_executive_synthesizer.yaml`):** We govern tone at the source by adding a universal, industry-agnostic **Lexical Register Rule** to the system prompt:
   - *Use direct, modern corporate and engineering terminology standard to the client's sector (`{{ industry_vertical }}`). Avoid archaic, poetic, or overly ornate adjectives (e.g., prefer standard operational terms over literary synonyms).*
3. **Deterministic Inline CIO Financial Justification:** Rather than relying on the LLM to guess or omit how the financial figures were derived, the compiler deterministically synthesizes or injects the exact actuarial grounding clause using the structured fields already present in `financial_exposure` (`expected_annual_loss`, `ale_p90`, `downtime_cost_per_hour`, `currency_symbol`, and the count of quantified risks in `risk_register`), ensuring 100% mathematical transparency for the CIO across any client, currency, or industry.

---

## 2. Target Architecture for Chapter 1 (Single-Page Executive Summary)

To guarantee that Chapter 1 fits cleanly on **Page 1** and gives the CIO immediate, self-explanatory clarity without visual clutter:

1. **Single Heading Only:**  
   Render **only** Heading 1: `1. Resumen Ejecutivo` (or localized equivalent via `DocumentLocaleConfig`). Eliminate subheadings `1.1`, `1.2`, and `1.3`, and eliminate the redundant standalone financial table.
2. **Self-Explanatory Executive Narrative (with Inline Actuarial Justification):**  
   Render two concise executive paragraphs:
   - **Paragraph 1 (Operational & Architectural Thesis):** Synthesizes the operational state of the tower and the primary structural vulnerability.
   - **Paragraph 2 (Quantified Financial Exposure & Actuarial Justification for the CIO):** Directly states the Expected Annual Loss (ALE) and the P90 Tail Risk, and **explicitly explains their derivation inline**:
     - *Expected Annual Loss (ALE):* Calculated from the annualized failure probability across the `N` audited risk vectors multiplied by the validated operational downtime cost rate (`downtime_cost_per_hour`).
     - *Stress Scenario (ALE P90):* Quantifies the 90th-percentile tail-risk exposure during peak operational concurrency or extended recovery windows (MTTR exceedance).
3. **Executive Scorecard Table:**  
   Compact 5-column KPI strip (`Madurez Global`, `Pérdida Anual Esperada (ALE)`, `Escenario Estrés (ALE P90)`, `Hallazgos Críticos`, `Inversión Estimada`).
4. **Executive Diagnostic Triad Table:**  
   Clean 2-column executive synthesis (` Fortaleza Principal`, ` Brecha Crítica`, ` Cuello de Botella Operativo`).
5. **Hard Page Break:**  
   Immediately closes Page 1 so Chapter 2 (`2. Alcance y Evidencia Analizada`) begins cleanly at the top of Page 2.

```text
+-----------------------------------------------------------------------+
| 1. Resumen Ejecutivo                                      [Heading 1] |
|                                                                       |
| [Paragraph 1: Executive Operational & Architectural Synthesis]        |
|                                                                       |
| [Paragraph 2: Financial Risk & Explicit CIO Actuarial Justification   |
|  explaining ALE (probabilistic frequency x hourly downtime cost rate) |
|  vs. P90 Tail Risk (concurrent peak-load outage & MTTR extension).]   |
|                                                                       |
| +-------------+-------------+-------------+-------------+-----------+ |
| | Madurez     | Pérdida     | Escenario   | Hallazgos   | Inversión | |
| | Global      | Anual (ALE) | Estrés (P90)| Críticos    | Estimada  | |
| +-------------+-------------+-------------+-------------+-----------+ |
| | 2.1 / 5.0   | 395.000 €   | 810.000 €   | 4 Críticos  | 117.500 € | |
| +-------------+-------------+-------------+-------------+-----------+ |
|                                                                       |
| +-------------------------------+-----------------------------------+ |
| | Dimensión Ejecutiva           | Síntesis de Diagnóstico           | |
| +-------------------------------+-----------------------------------+ |
| | Fortaleza Principal           | ...                               | |
| | Brecha Crítica                | ...                               | |
| | Cuello de Botella Operativo   | ...                               | |
| +-------------------------------+-----------------------------------+ |
|                                                                       |
| ======================== [ HARD PAGE BREAK ] ======================== |
+-----------------------------------------------------------------------+
```

---

## 3. Production Implementation Specification (100% Technical English)

### 3.1 Pure Upstream Prompt Specification (`src/infrastructure/prompts/annex_executive_synthesizer.yaml`)

Instead of regex-patching words in Python, we enforce natural executive register and explicit actuarial clarity directly in the prompt contract:

```yaml
# src/infrastructure/prompts/annex_executive_synthesizer.yaml
version: "2.1.0"
task_id: "annex_executive_synthesizer"
description: "Synthesizes the single-page executive summary narrative and diagnostic triad for any enterprise tower."

system_prompt: |
  You are a Principal Enterprise Architect and CIO Advisory Director conducting a forensic technical due diligence.
  Your objective is to synthesize the Executive Summary for Tower {{ tower_id }} ({{ tower_name }}).

  UNIVERSAL LEXICAL & REGISTER LAWS (NON-NEGOTIABLE):
  1. NATURAL CORPORATE REGISTER: Use clear, modern, institutional business and engineering terminology standard to the client's industry vertical ({{ industry_vertical }}).
  2. ZERO ARCHAIC OR POETIC ADJECTIVES: Strictly avoid literary, archaic, or overly ornate adjectives when referring to facilities, operations, or infrastructure. Use standard operational terms (e.g., "operación de planta", "entorno productivo", "infraestructura crítica", "centro operativo").
  3. CIO-LEVEL ACTUARIAL TRANSPARENCY: In the second paragraph of `narrative_synthesis`, you MUST explicitly justify the financial exposure figures so the CIO understands their exact mathematical origin:
     - State the Expected Annual Loss (ALE: {{ ale_formatted }}) and explain that it derives from the annualized probability of occurrence across the {{ risk_count }} quantified technical risks multiplied by the validated operational downtime cost rate ({{ downtime_cost_formatted }}/hour).
     - State the P90 Stress Scenario (ALE P90: {{ ale_p90_formatted }}) and explain that it represents the 90th-percentile tail risk under severe outage concurrency or extended recovery times (MTTR exceedance) during peak operational windows.
  4. CONCISENESS FOR SINGLE-PAGE FIT: `narrative_synthesis` must consist of exactly two dense, high-impact paragraphs (140 to 190 words total) separated by `\n\n`. Do not include markdown headings or bullet lists inside `narrative_synthesis`.
```

---

### 3.2 Canonical Data Contract (`src/domain/contracts/types_payload.py`)

We ensure `FinancialExposure` and `ExecutiveSummary` carry all structured parameters required to render Chapter 1 deterministically without secondary files:

```python
# src/domain/contracts/types_payload.py
from typing import List, Optional, TypedDict


class FinancialExposure(TypedDict, total=False):
    """Canonical actuarial exposure metrics for a single tower."""
    expected_annual_loss: float
    ale_p90: float
    estimated_remediation_capex: float
    downtime_cost_per_hour: float
    currency_code: str
    currency_symbol: str
    actuarial_methodology_note: str


class ExecutiveDiagnosticTriad(TypedDict):
    """Structured executive synthesis triad for the Page-1 summary table."""
    primary_strength: str
    critical_gap: str
    operational_bottleneck: str


class ExecutiveSummary(TypedDict):
    """Canonical schema for Chapter 1 (Executive Summary)."""
    narrative_synthesis: str
    overall_maturity_score: float
    maturity_target_score: float
    critical_findings_count: int
    high_findings_count: int
    diagnostic_triad: ExecutiveDiagnosticTriad
```

---

### 3.3 Deterministic Chapter 1 AST Compiler (`src/infrastructure/adapters/rendering/ast/payload_to_ast.py`)

Below is the clean, universal implementation of `_compile_chapter_1_executive_summary` inside `PayloadToAstCompiler`.  
- **Zero hardcoded domain regexes.**  
- **Zero subheadings (`1.1`, `1.2`) and zero duplicate financial tables.**  
- **Deterministic Actuarial Grounding Guarantee:** If an upstream payload's `narrative_synthesis` does not yet explicitly cite the hourly downtime rate or explain the ALE vs. P90 derivation, the compiler deterministically appends a localized, mathematically exact actuarial grounding sentence from the structured `financial_exposure` contract.

```python
# src/infrastructure/adapters/rendering/ast/payload_to_ast.py
from typing import Any, Dict, List
from src.domain.contracts.types_ast import (
    ASTNode,
    HeadingNode,
    PageBreakNode,
    ParagraphNode,
    TableCellNode,
    TableNode,
    TableRowNode,
    TextRunNode,
)
from src.domain.contracts.types_payload import EnrichedTowerPayload


class PayloadToAstCompiler:
    """
    Deterministic compiler transforming a canonical 21-key EnrichedTowerPayload
    into a strictly typed DocumentAST.
    Zero domain hardcoding; 100% universal across all towers and verticals.
    """

    def _compile_chapter_1_executive_summary(
        self, payload: EnrichedTowerPayload
    ) -> List[ASTNode]:
        """
        Compiles Chapter 1 (Executive Summary) to fit strictly on Page 1:
        1. Single Heading 1 ("1. Resumen Ejecutivo") - ZERO subheadings.
        2. Executive Narrative paragraphs + explicit CIO actuarial justification.
        3. Compact 5-column Executive Scorecard Table.
        4. Compact 2-column Executive Diagnostic Triad Table.
        5. Hard PageBreakNode isolating Chapter 1 on Page 1.
        """
        nodes: List[ASTNode] = []

        exec_summary: Dict[str, Any] = payload.get("executive_summary", {})
        fin_exposure: Dict[str, Any] = payload.get("financial_exposure", {})
        risk_register: List[Dict[str, Any]] = payload.get("risk_register", [])
        findings: List[Dict[str, Any]] = payload.get("findings", [])

        # 1. Single Main Chapter Heading (No 1.1 or 1.2 subheadings)
        nodes.append(
            HeadingNode(
                level=1,
                text=self._locale.chapter_1_title,  # e.g., "1. Resumen Ejecutivo"
                style_id="Heading1",
            )
        )

        # 2. Executive Narrative & Deterministic CIO Actuarial Grounding
        paragraphs = self._build_executive_narrative_paragraphs(
            exec_summary=exec_summary,
            fin_exposure=fin_exposure,
            risk_count=len(risk_register),
        )
        for paragraph_text in paragraphs:
            nodes.append(
                ParagraphNode(
                    runs=[TextRunNode(text=paragraph_text)],
                    style_id="ExecutiveBody",
                )
            )

        # 3. Executive Scorecard Table (5-Column KPI Strip)
        nodes.append(
            self._build_executive_scorecard_table(
                exec_summary=exec_summary,
                fin_exposure=fin_exposure,
                findings=findings,
            )
        )

        # 4. Executive Diagnostic Triad Table (Strength, Gap, Bottleneck)
        nodes.append(
            self._build_diagnostic_triad_table(
                exec_summary=exec_summary,
            )
        )

        # 5. Strict Page Break to guarantee Chapter 2 starts on Page 2
        nodes.append(PageBreakNode())

        return nodes

    def _build_executive_narrative_paragraphs(
        self,
        exec_summary: Dict[str, Any],
        fin_exposure: Dict[str, Any],
        risk_count: int,
    ) -> List[str]:
        """
        Extracts the executive narrative paragraphs and ensures the CIO has a
        transparent mathematical explanation of how Expected Annual Loss (ALE)
        and P90 Tail Risk are derived from the payload's actuarial parameters.
        """
        raw_narrative: str = (exec_summary.get("narrative_synthesis") or "").strip()
        blocks: List[str] = [
            blk.strip() for blk in raw_narrative.split("\n\n") if blk.strip()
        ]

        # Extract structured actuarial metrics from canonical contract
        ale_val: float = float(fin_exposure.get("expected_annual_loss", 0.0))
        p90_val: float = float(fin_exposure.get("ale_p90", 0.0))
        hourly_cost: float = float(fin_exposure.get("downtime_cost_per_hour", 0.0))
        currency: str = str(fin_exposure.get("currency_symbol", "€"))

        ale_str = self._format_currency(ale_val, currency)
        p90_str = self._format_currency(p90_val, currency)
        hourly_str = self._format_currency(hourly_cost, currency)

        # Verify whether the narrative already contains explicit actuarial grounding
        explicit_methodology_note: str = (
            fin_exposure.get("actuarial_methodology_note") or ""
        ).strip()

        if explicit_methodology_note:
            actuarial_clause = explicit_methodology_note
        else:
            actuarial_clause = self._locale.format_actuarial_justification(
                ale_formatted=ale_str,
                p90_formatted=p90_str,
                hourly_cost_formatted=hourly_str,
                risk_count=max(risk_count, 1),
            )

        if not blocks:
            return [actuarial_clause]

        # Check if the narrative already explains both P90 and the hourly downtime rate
        combined_text = " ".join(blocks)
        has_p90_reference = "P90" in combined_text or p90_str in combined_text
        has_rate_reference = hourly_str in combined_text or "/h" in combined_text

        if not (has_p90_reference and has_rate_reference):
            if len(blocks) == 1:
                blocks.append(actuarial_clause)
            else:
                blocks[-1] = f"{blocks[-1]} {actuarial_clause}"

        # Cap at 2 dense paragraphs to guarantee single-page vertical budget
        if len(blocks) > 2:
            blocks = [blocks[0], " ".join(blocks[1:])]

        return blocks

    def _build_executive_scorecard_table(
        self,
        exec_summary: Dict[str, Any],
        fin_exposure: Dict[str, Any],
        findings: List[Dict[str, Any]],
    ) -> TableNode:
        """
        Builds the compact 5-column KPI Scorecard Table for Page 1.
        """
        currency: str = str(fin_exposure.get("currency_symbol", "€"))
        maturity_score = float(exec_summary.get("overall_maturity_score", 0.0))
        ale_val = float(fin_exposure.get("expected_annual_loss", 0.0))
        p90_val = float(fin_exposure.get("ale_p90", 0.0))
        capex_val = float(fin_exposure.get("estimated_remediation_capex", 0.0))

        critical_count = exec_summary.get("critical_findings_count")
        if critical_count is None:
            critical_count = sum(
                1
                for f in findings
                if str(f.get("severity", "")).upper() in {"CRITICAL", "CRITICO", "CRÍTICO", "ALTO", "HIGH"}
            )

        headers = self._locale.scorecard_headers
        values = [
            f"{maturity_score:.1f} / 5.0",
            self._format_currency(ale_val, currency),
            self._format_currency(p90_val, currency),
            f"{critical_count} ({self._locale.priority_label})",
            self._format_currency(capex_val, currency),
        ]

        header_row = TableRowNode(
            is_header=True,
            cells=[
                TableCellNode(
                    paragraphs=[
                        ParagraphNode(
                            runs=[TextRunNode(text=h, bold=True)],
                            style_id="TableHeader",
                        )
                    ]
                )
                for h in headers
            ],
        )

        value_row = TableRowNode(
            is_header=False,
            cells=[
                TableCellNode(
                    paragraphs=[
                        ParagraphNode(
                            runs=[TextRunNode(text=v, bold=True)],
                            style_id="ScorecardMetric",
                        )
                    ]
                )
                for v in values
            ],
        )

        return TableNode(
            style_id="ExecutiveScorecardTable",
            column_widths_pct=[18.0, 22.0, 22.0, 18.0, 20.0],
            rows=[header_row, value_row],
        )

    def _build_diagnostic_triad_table(
        self, exec_summary: Dict[str, Any]
    ) -> TableNode:
        """
        Builds the 2-column Executive Diagnostic Triad Table (Strength, Gap, Bottleneck).
        """
        triad: Dict[str, Any] = exec_summary.get("diagnostic_triad", {})
        rows_spec = [
            (
                self._locale.triad_strength_label,
                str(triad.get("primary_strength", "")).strip(),
            ),
            (
                self._locale.triad_gap_label,
                str(triad.get("critical_gap", "")).strip(),
            ),
            (
                self._locale.triad_bottleneck_label,
                str(triad.get("operational_bottleneck", "")).strip(),
            ),
        ]

        header_row = TableRowNode(
            is_header=True,
            cells=[
                TableCellNode(
                    paragraphs=[
                        ParagraphNode(
                            runs=[TextRunNode(text=self._locale.triad_col_dimension, bold=True)],
                            style_id="TableHeader",
                        )
                    ]
                ),
                TableCellNode(
                    paragraphs=[
                        ParagraphNode(
                            runs=[TextRunNode(text=self._locale.triad_col_synthesis, bold=True)],
                            style_id="TableHeader",
                        )
                    ]
                ),
            ],
        )

        body_rows: List[TableRowNode] = []
        for label, description in rows_spec:
            body_rows.append(
                TableRowNode(
                    is_header=False,
                    cells=[
                        TableCellNode(
                            paragraphs=[
                                ParagraphNode(
                                    runs=[TextRunNode(text=label, bold=True)],
                                    style_id="TableBodyCompact",
                                )
                            ]
                        ),
                        TableCellNode(
                            paragraphs=[
                                ParagraphNode(
                                    runs=[TextRunNode(text=description)],
                                    style_id="TableBodyCompact",
                                )
                            ]
                        ),
                    ],
                )
            )

        return TableNode(
            style_id="ExecutiveTriadTable",
            column_widths_pct=[28.0, 72.0],
            rows=[header_row, *body_rows],
        )
```

---

### 3.4 Locale Configuration Adapter (`src/domain/contracts/locale_config.py`)

To ensure 100% Technical English in Python code while supporting Spanish, English, or any global language dynamically via configuration, the actuarial justification template lives in the locale configuration object:

```python
# src/domain/contracts/locale_config.py
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DocumentLocaleConfig:
    """Immutable localization contract for AST compilation."""
    language_code: str
    chapter_1_title: str
    scorecard_headers: List[str]
    priority_label: str
    triad_col_dimension: str
    triad_col_synthesis: str
    triad_strength_label: str
    triad_gap_label: str
    triad_bottleneck_label: str
    actuarial_template_with_hourly_rate: str
    actuarial_template_base: str

    def format_actuarial_justification(
        self,
        ale_formatted: str,
        p90_formatted: str,
        hourly_cost_formatted: str,
        risk_count: int,
    ) -> str:
        """Formats the inline CIO financial justification deterministically."""
        if not hourly_cost_formatted.startswith("0"):
            return self.actuarial_template_with_hourly_rate.format(
                ale=ale_formatted,
                p90=p90_formatted,
                hourly_cost=hourly_cost_formatted,
                risk_count=risk_count,
            )
        return self.actuarial_template_base.format(
            ale=ale_formatted,
            p90=p90_formatted,
            risk_count=risk_count,
        )


SPANISH_EXECUTIVE_LOCALE = DocumentLocaleConfig(
    language_code="es-ES",
    chapter_1_title="1. Resumen Ejecutivo",
    scorecard_headers=[
        "Madurez Global",
        "Pérdida Anual (ALE)",
        "Escenario Estrés (P90)",
        "Hallazgos Críticos",
        "Inversión Estimada",
    ],
    priority_label="Prioridad 1",
    triad_col_dimension="Dimensión Ejecutiva",
    triad_col_synthesis="Síntesis de Diagnóstico",
    triad_strength_label="Fortaleza Principal",
    triad_gap_label="Brecha Crítica",
    triad_bottleneck_label="Cuello de Botella Operativo",
    actuarial_template_with_hourly_rate=(
        "Desde una perspectiva actuarial, la Pérdida Anual Esperada (ALE) de {ale} "
        "se calcula a partir de la frecuencia probabilística anualizada de los {risk_count} "
        "vectores de riesgo cuantificados multiplicada por el coste de indisponibilidad "
        "operativa validado ({hourly_cost}/h), mientras que el escenario de estrés P90 ({p90}) "
        "modela el impacto de cola ante indisponibilidades concurrentes o extensión del "
        "tiempo de recuperación (MTTR) en ventanas críticas de operación."
    ),
    actuarial_template_base=(
        "Desde una perspectiva actuarial, la Pérdida Anual Esperada (ALE) de {ale} "
        "agrega la exposición probabilística anualizada de los {risk_count} vectores de riesgo "
        "auditados, mientras que el escenario de estrés P90 ({p90}) modela el impacto severo "
        "de cola ante fallos concurrentes en ventanas críticas de operación."
    ),
)
```

---

### 3.5 Unifying the Pipeline in `BlueprintService` (Deprecating Dual-JSON Split-Brain)

In `src/application/services/blueprint_service.py`, we unify the artifact persistence so that `blueprint_{tower}_payload.json` (`EnrichedTowerPayload`) is the **only** canonical payload generated and consumed across all towers:

```python
# src/application/services/blueprint_service.py
from pathlib import Path
import json
from src.domain.contracts.types_payload import EnrichedTowerPayload


class BlueprintPayloadRepository:
    """
    Canonical repository persisting and loading the single 21-key EnrichedTowerPayload
    across all towers (T1-T10). Eliminates split-brain dual payload files.
    """

    def __init__(self, artifacts_dir: Path) -> None:
        self._artifacts_dir = artifacts_dir

    def get_canonical_path(self, tower_id: str) -> Path:
        normalized = tower_id.lower().strip()
        return self._artifacts_dir / f"blueprint_{normalized}_payload.json"

    def save_canonical_payload(
        self, tower_id: str, payload: EnrichedTowerPayload
    ) -> Path:
        canonical_path = self.get_canonical_path(tower_id)
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        canonical_path.write_text(serialized, encoding="utf-8")
        return canonical_path

    def load_canonical_payload(self, tower_id: str) -> EnrichedTowerPayload:
        canonical_path = self.get_canonical_path(tower_id)
        if not canonical_path.exists():
            raise FileNotFoundError(
                f"Canonical payload not found for tower '{tower_id}' at {canonical_path}"
            )
        return json.loads(canonical_path.read_text(encoding="utf-8"))
```

---

## 4. Summary of Architectural Guarantees

| Architectural Dimension | Legacy State (Anti-Pattern) | RFC 033 Canonical State |
| :--- | :--- | :--- |
| **Payload Source of Truth** | Split-brain: `blueprint_t2_payload.json` vs `approved_annex_t2.template_payload.json`. | **Single Canonical Contract:** `EnrichedTowerPayload` (`blueprint_{tower}_payload.json`) across T1–T10. |
| **Lexical Tone Control** | Hardcoded Spanish regex (`re.sub(r"\bfabril\b", ...)`) inside Python compiler code. | **100% Upstream Prompt Governance** in `annex_executive_synthesizer.yaml` + zero domain regexes in Python. |
| **Chapter 1 Structure** | Multiple subheadings (`1.1`, `1.2`) + redundant financial table overflowing Page 1. | **Single Heading (`1. Resumen Ejecutivo`)** + 2 Narrative Paragraphs + Scorecard Table + Triad Table + Page Break. |
| **CIO Financial Justification** | Unexplained numbers (`395.000 €` vs `810.000 €`) in isolated tables. | **Inline Actuarial Transparency:** Explicitly explains ALE (frequency $\times$ hourly downtime rate) vs. P90 tail risk. |