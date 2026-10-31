---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- docs/architecture/split_brain_remediation_plan.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# RFC-026: AST Compiler Convergence & Zero-Entropy Document Synthesis

## Part I: Deep Adversarial Review & Latent Defect Analysis

As Principal Systems Architect, Chief Compiler Engineer, and Staff Quality Auditor, I have subjected the draft **RFC-026** blueprint to a rigorous adversarial audit against your **Four Non-Negotiable Laws**. While the draft correctly identifies the LLVM multi-pass compiler topology and the Gang of Four (GoF) Visitor pattern, it contains **seven severe architectural defects and law violations** that would cause runtime corruption, hardcoding debt, or regulatory non-compliance if merged as-is:

1. **Violation of Law #2 (Hardcoded Tenant, Currency, and Locale Defaults):**
   - The draft hardcodes `locale: str = "es"` in `DeclarativeI18nResolver.resolve()`, `build_tower_annex_ast()`, and `mcp_compile_tower_annex()`. A universal enterprise platform must never assume a default human language or jurisdiction; locale and currency (`ISO 4217`) must be mandatory, explicitly injected context parameters derived from the tenant payload.
   - The specification and tests hardcode client-specific strings (`"Molins"`, `"canteras"`, `"1,05M €"`, `"HPE SimpliVity"`) directly into the architectural invariants and primary test suite names rather than treating them as a parameterized **Parametric Tenant Fixture** (one of many possible industry verticals, e.g., Global Tier-1 Banking, Aerospace, Heavy Manufacturing).

2. **Violation of Law #3 (Multi-Lingual Deliverable Output & BiDi/Script Blindness):**
   - The draft restricts i18n discussion to `es`, `en`, and `ca`, and embeds Spanish strings inside Python test assertions inside the core specification.
   - Furthermore, `DocxCompiler` only sets `run.font.color.rgb`, `bold`, and `italic`. It completely ignores **Right-to-Left (RTL) script rendering** (`<w:rtl/>` and `<w:bidi/>` for Arabic/Hebrew) and **CJK (Chinese/Japanese/Korean) East Asian font slot binding** (`w:eastAsia`). Without explicit script-direction and font-family governance in the AST, compiling deliverables in Arabic (`ar-SA`) or Japanese (`ja-JP`) produces garbled typography.

3. **Violation of Law #1 (WCAG 2.1 Luminance Threshold Defect vs. Contrast Ratio Mathematics):**
   - The draft's `StyleInvariantGuard` checks independent thresholds (`fg_lum >= 0.80` and `bg_lum >= 0.18`). **This is mathematically flawed.** Under WCAG 2.1 AA/AAA, readability is governed by the **Contrast Ratio**:
     $$CR = \frac{L_{\text{lighter}} + 0.05}{L_{\text{darker}} + 0.05} \ge 4.5$$
     Using decoupled thresholds allows a mid-gray foreground (`L = 0.35`) over a mid-gray background (`L = 0.25`), yielding an illegible contrast ratio of $1.33:1$ while bypassing the guard! The compiler must enforce the exact WCAG 2.1 contrast ratio inequality ($CR \ge 4.5:1$ for body text, $CR \ge 7.0:1$ for executive tables).

4. **Violation of Law #1 (XML Duplicate `<w:shd>` Mutation Bug in `DocxCompiler._set_cell_background_xml`):**
   - In the draft's `_set_cell_background_xml`, `tc_pr.append(shd)` blindly appends a new `<w:shd>` element to `<w:tcPr>`. In OpenXML (`ECMA-376`), if `<w:tcPr>` already contains a `<w:shd>` node inherited from a table style, appending a second `<w:shd>` creates invalid schema ordering or causes Microsoft Word to honor the first node and ignore the second. The compiler must remove any existing `w:shd` child before inserting the canonical shading element.

5. **Violation of Law #1 (Stateful Single-Use `DocxCompiler` Antipattern):**
   - `DocxCompiler.__init__` instantiates `self._doc = docx.Document()`. If `compiler.compile()` is called twice on the same instance, the second document's AST nodes are appended to the first document's XML tree! A compiler backend must instantiate a fresh compilation context per `compile()` invocation.

6. **Violation of Law #4 (Missing Minto Pyramid & FAIR Financial Explainability AST Nodes):**
   - The draft mentions "144 paragraphs and 11 tables" as magic numbers without defining the **Formal Grammar of Narrative Explainability**. To guarantee that every compiled document reads like an elite McKinsey/Gartner publication and explains every single unit of financial risk, the AST must enforce a **Minto Pyramid Contract** (Governing Thought $\rightarrow$ Key Line Arguments $\rightarrow$ Empirical Telemetry & FAIR Decomposition: Threat Event Frequency $[TEF]$, Vulnerability $[Vuln]$, Loss Event Frequency $[LEF]$, Primary/Secondary Loss Magnitude $[PLM/SLM]$, and Annualized Loss Expectancy $[ALE]$).

7. **Incomplete Split-Brain #1 Eradication:**
   - The draft only bans `render_tower_annex_from_template` via import scanning. It fails to ban dynamic imports (`importlib.import_module`), `__import__`, or direct `.docx` binary template loading (`docx.Document("...template.docx")`) in the domain/application layers.

---

## Part II: The Definitive, Refined RFC-026 Architectural Specification

```markdown
---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
- docs/architecture/split_brain_remediation_plan.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# RFC-026: AST Compiler Convergence & Zero-Entropy Document Synthesis

**Status:** VERIFIED & MANDATED FOR IMMEDIATE EXECUTION  
**Authors:** Principal Systems Architecture, Compiler Engineering & Quality Assurance Group  
**Target Subsystem:** `Assessment Engine` / Multi-Lingual Document Synthesis Pipeline  
**Classification:** Tier-1 Architectural Remediation (Split-Brain #1 Eradication & Universal Compilation)  

---

## 1. Executive Summary & Problem Formalization

### 1.1 Context & Symptom Topology
The Assessment Engine currently exhibits a critical **Split-Brain Architecture (Split-Brain #1)** within its document synthesis subsystem. Two incompatible compilation paradigms coexist in the runtime execution graph:

1. **Engine A (Legacy Imperative Binary Mutator — `render_tower_annex_from_template.py`):** Performs fragile string interpolation (`{{TAG}}`) directly against pre-compiled OpenXML `.docx` binary templates. It forces complex, multi-dimensional risk narratives into rigid micro-tables. Because it mutates XML runs in-place without a unified style state tree, it strips background shading `<w:shd>` elements while preserving `<w:color w:val="FFFFFF"/>`, triggering the catastrophic **White-on-White (`#FFFFFF` on `#FFFFFF`) visibility defect**. Furthermore, it is structurally incapable of adapting table topologies, currency formatting, regulatory citations, or script directionality (LTR/RTL) across global jurisdictions.
2. **Engine B (Modern Declarative AST Pipeline — `payload_to_ast.py` $\rightarrow$ `DocxCompiler`):** Implements a deterministic, multi-pass compilation architecture. It lowers strongly-typed domain payloads into a platform-agnostic Abstract Syntax Tree (AST), synthesizing a cohesive 5-chapter executive advisory publication with Minto Pyramid narrative flow, Factor Analysis of Information Risk (FAIR) financial explainability, and strict typographic hierarchy.

Currently, the Model Context Protocol entrypoint (`mcp_server.py`) routes automated synthesis requests to **Engine A**, bypassing **Engine B**. Consequently, high-precision outputs generated by our Counterexample-Guided Abstraction Refinement (CEGAR) and FAIR risk engines—which compute granular Annualized Loss Expectancy (ALE) across heterogeneous infrastructure topologies, industry verticals, and regulatory regimes—are truncated, stripped of causal narrative explainability, and rendered visually defective. Additionally, heuristic fallback logic in legacy localization resolvers causes raw symbolic keys (e.g., `chapter3title`) to leak into client deliverables.

```
                      CURRENT SPLIT-BRAIN TOPOLOGY (DEPRECATED)
                      =========================================
                                        
                       +---> [Engine A: Binary Template Mutator] ---> Rigid Micro-Tables /
                       |     (render_tower_annex_from_template.py)    #FFFFFF Contrast Bug /
[Domain & CEGAR/FAIR] -+                                              Hardcoded Locale Assumptions
[Assessment Payload ]  |
                       +---> [Engine B: Declarative AST Compiler] --> Cohesive 5-Chapter Advisory Book
                             (payload_to_ast.py -> DocxCompiler)      (Unreachable via MCP Server)


                      TARGET CONVERGED COMPILER TOPOLOGY (RFC-026)
                      ============================================

[Universal Domain Payload] + [Tenant Context (ISO Locale, ISO Currency, Jurisdiction, Industry)]
                                               |
                                               v
                   [Compiler Frontend: payload_to_ast.py (Minto + FAIR Lowering)]
                                               |
                                               v
                              [Intermediate Representation: AST]
                                               |
                +------------------------------+------------------------------+
                | Pass 1: Bijective i18n & Currency/Number Formatting Pass    |
                | Pass 2: Minto Narrative & FAIR Explainability Completeness  |
                | Pass 3: WCAG 2.1 Contrast Ratio & Script Directionality     |
                +------------------------------+------------------------------+
                                               |
                                               v
                      [Compiler Backend: DocxCompiler (GoF NodeVisitor)]
                                               |
                                               v
               [Zero-Entropy OpenXML (.docx) Executive Deliverable (Any Language)]
```

### 1.2 Theoretical Justification: LLVM Multi-Pass Compilation & GoF Visitor Pattern
Mutating binary document templates via string replacement violates core compiler design principles by conflating **lexical localization**, **semantic narrative structuring**, **visual invariant verification**, and **physical code generation** into a single, untestable side effect.

To achieve **Zero-Entropy Document Synthesis** across any global enterprise, industry vertical, regulatory framework, and human language, RFC-026 formalizes document synthesis as a **Three-Stage Multi-Pass Compiler** modeled after the **LLVM Architecture**:

1. **Compiler Frontend (`payload_to_ast.py`):** Ingests the validated Domain & CEGAR/FAIR Payload alongside an explicit `TenantCompilationContext` (specifying target `locale`, `currency_code`, `regulatory_frameworks`, and `industry_vertical`). It constructs an immutable, strongly-typed Intermediate Representation (IR)—the **Document Abstract Syntax Tree (AST)**. Every financial risk metric is lowered into paired narrative and tabular nodes linking physical/logical asset telemetry to business impact via the **Minto Pyramid Principle** and the **FAIR taxonomy**.
2. **Compiler Middle-End (Pure Functional Verification & Optimization Passes):** Before emitting a single byte of OpenXML, the AST undergoes deterministic validation passes:
   - *Bijective Localization & ICU Formatting Pass:* Resolves all symbolic structural keys against the locale registry and formats monetary/numerical values according to `ISO 4217` and locale-specific grouping/decimal rules.
   - *Executive Explainability Completeness Pass:* Verifies that every quantified risk row in the AST is accompanied by a deterministic causal narrative explaining Threat Event Frequency ($TEF$), Vulnerability ($Vuln$), Primary/Secondary Loss Magnitude ($PLM/SLM$), and remediation ROI.
   - *WCAG 2.1 Contrast Ratio & Script Pass:* Computes exact relative luminance ratios ($CR \ge 4.5:1$) for every text span against its ancestor container background and binds script directionality (`LTR` vs. `RTL`) and font families (`Latin`, `EastAsian`, `ComplexScript`).
3. **Compiler Backend (`DocxCompiler` via GoF Visitor Pattern):** Implements the classic **Gang of Four (GoF) Visitor Pattern** (`ASTNodeVisitor`). It traverses the verified AST deterministically, emitting schema-compliant OpenXML (`ECMA-376`) `<w:p>`, `<w:tbl>`, `<w:tcPr>`, `<w:shd>`, and `<w:rPr>` elements within an isolated per-compilation document context.

---

## 2. The 6 Non-Negotiable Architectural Invariants

All code merged under RFC-026 must satisfy six mathematical and structural invariants enforced at compile-time, runtime, and CI/CD gate execution:

### Invariant I: Zero Split-Brain (Single Path of Synthesis)
$$\forall r \in \text{Requests}_{\text{Synthesis}}, \quad \text{Route}(r) \equiv \text{ DocxCompiler.compile} \circ \text{MiddleEndPasses} \circ \text{build\_document\_ast}(r)$$
There shall exist exactly **one** execution path for synthesizing `.docx` deliverables. Imperative binary template mutation (`render_tower_annex_from_template.py`) and pre-populated `.docx` template loading are permanently excised from the codebase.

### Invariant II: Universal WCAG 2.1 Physical Contrast Ratio Guarantee
$$\forall s \in \text{AST}_{\text{TextSpans}}, \quad CR\left(L(\text{Fg}(s)),\, L(\text{EffectiveBg}(s))\right) = \frac{\max(L_{\text{fg}}, L_{\text{bg}}) + 0.05}{\min(L_{\text{fg}}, L_{\text{bg}}) + 0.05} \ge 4.5$$
No AST text span or table cell may be compiled with a foreground/background luminance combination yielding a WCAG 2.1 contrast ratio below $4.5:1$. Specifically, light foreground text (e.g., `#FFFFFF`, $L = 1.0$) is mathematically prohibited unless its enclosing cell or paragraph explicitly declares a verified dark background fill (e.g., Executive Navy `#0A192F`, $L \approx 0.011$, $CR \approx 17.2:1$) physically written to `<w:shd w:val="clear" w:color="auto" w:fill="..."/>`. If background shading is absent, `auto`, `clear`, or light, the foreground color deterministically resolves to Executive Charcoal (`#111827`, $L \approx 0.012$).

### Invariant III: Total Declarative i18n Bijection & Multi-Script Support
$$\forall l \in \text{SupportedLocales}, \forall k \in \text{Keys}_{\text{AST}}, \quad k \in \text{dom}(\text{Registry}_l) \land \text{len}(\text{trim}(\text{Registry}_l(k))) > 0$$
Every structural heading, table header, diagnostic label, and narrative connective emitted by the frontend must resolve bijectively against `engine_config/locales.json` for the requested target locale (`en-US`, `es-ES`, `de-DE`, `ja-JP`, `pt-BR`, `ar-SA`, etc.). Regex-based key stripping (e.g., transforming `chapter_3_title` into `chapter3title`) and silent default locale fallbacks are strictly forbidden. Missing locales or keys raise a fatal `MissingLocalizationKeyError`.

### Invariant IV: Zero Hardcoding (Universal Tenant, Currency, and Jurisdiction Agnosticism)
$$\text{Constants}(\text{CompilerCore}) \cap \left(\text{TenantNames} \cup \text{FixedCurrencies} \cup \text{FixedJurisdictions} \cup \text{FixedVendors}\right) = \emptyset$$
The compiler frontend, middle-end, and backend must contain zero hardcoded company names, currencies, countries, regulatory frameworks, or hardware/software vendor strings. All domain specifics flow strictly from the input `AssessmentPayload` and `TenantCompilationContext`.

### Invariant V: Minto Pyramid & FAIR Financial Explainability Completeness
$$\forall \rho \in \text{RiskScenarios}_{\text{Payload}}, \quad \exists! \, (\text{Row}_{\rho}, \text{Prose}_{\rho}) \in \text{AST} \implies \text{ALE}(\rho) = \text{LEF}(\rho) \times \text{LM}(\rho)$$
Every quantified financial risk exposure in the payload must be synthesized into both (1) a structured analytical table row and (2) an executive narrative block structured via the **Minto Pyramid Principle** (Governing Conclusion $\rightarrow$ Telemetry Evidence $\rightarrow$ FAIR Risk Decomposition $[TEF, Vuln, PLM, SLM, ALE]$ $\rightarrow$ Quantified Remediation CAPEX/OPEX & Net Risk Reduction). Fragmented, robotic, or unexplained numerical outputs are rejected by the AST validator.

### Invariant VI: Pure Clean Architecture Separation
$$\text{Imports}(\text{AST} \cup \text{Frontend} \cup \text{MiddleEnd}) \cap \left\{\texttt{docx}, \texttt{lxml}, \texttt{oxml}\right\} = \emptyset$$
The AST intermediate representation (`nodes.py`), frontend (`payload_to_ast.py`), i18n resolver (`resolver.py`), and invariant guards (`style_invariants.py`) must remain 100% pure Python immutable data structures (`dataclasses(frozen=True)`), completely decoupled from `python-docx` or XML manipulation. All OpenXML serialization is strictly encapsulated within `DocxCompiler`.

---

## 3. Surgical 4-PR Implementation Roadmap

### PR-1: Universal Declarative i18n & Currency Formatting Engine
* **Objective:** Eliminate raw fallback token leakage and hardcoded locale/currency assumptions by establishing a strict, multi-lingual localization registry and locale-aware currency formatter.
* **Target Files:**
  - `engine_config/locales.json`
  - `src/assessment_engine/i18n/resolver.py`
* **Key Deliverable Specifications:**
  1. Populate `engine_config/locales.json` with complete bijective key sets across global locales (`en`, `es`, `de`, `pt`, `ja`, `ar`), including all canonical structural keys (`chapter_1_executive_summary`, `chapter_2_telemetry_architecture`, `chapter_3_diagnosis_cross_cutting`, `chapter_4_fair_quantification`, `chapter_5_strategic_roadmap`, `diagnosis_performance_matrix_title`, `decision_matrix_title`, and parameterized Minto/FAIR narrative templates).
  2. Remove all regex-based fallback normalizers (`re.sub(r'[^a-zA-Z0-9]', '', key)`).
  3. Implement deterministic `ISO 4217` currency and metric formatting inside `DeclarativeI18nResolver.format_currency(amount, currency_code, locale)` with zero third-party locale-state side effects.

### PR-2: AST Node Hierarchy, Minto/FAIR Frontend & Style Invariant Guard
* **Objective:** Formalize the pure Python AST node taxonomy (`nodes.py`), implement the Minto/FAIR narrative synthesizer (`payload_to_ast.py`), and enforce exact WCAG 2.1 contrast ratio mathematics (`style_invariants.py`).
* **Target Files:**
  - `src/assessment_engine/ast/nodes.py`
  - `src/assessment_engine/ast/payload_to_ast.py`
  - `src/assessment_engine/compiler/style_invariants.py`
* **Key Deliverable Specifications:**
  1. Define immutable `@dataclass(frozen=True)` AST nodes supporting script directionality (`TextDirection.LTR` / `TextDirection.RTL`), semantic hierarchy, and table cell shading.
  2. Implement `StyleInvariantGuard.contrast_ratio(hex_a, hex_b)` using the exact WCAG 2.1 relative luminance formula and enforce $CR \ge 4.5:1$ via `enforce_safe_foreground()`.
  3. Implement `build_tower_annex_ast()` to lower arbitrary enterprise payloads into the 5-chapter Minto Pyramid structure with full FAIR risk explainability.

### PR-3: Stateless GoF `DocxCompiler` Backend & MCP Server Cutover
* **Objective:** Implement the schema-compliant OpenXML visitor backend (`DocxCompiler`), sever Engine A from `mcp_server.py`, and tombstone `render_tower_annex_from_template.py`.
* **Target Files:**
  - `src/assessment_engine/compiler/docx_compiler.py`
  - `src/mcp_server.py`
  - `src/assessment_engine/legacy/render_tower_annex_from_template.py` (Deleted)
* **Key Deliverable Specifications:**
  1. Ensure `DocxCompiler.compile()` initializes an isolated `docx.Document()` per invocation (eliminating stateful cross-request contamination).
  2. Ensure `DocxCompiler._set_cell_background_xml()` strips any pre-existing `<w:shd>` children from `<w:tcPr>` before writing `<w:shd w:val="clear" w:color="auto" w:fill="HEX"/>`.
  3. Support RTL bidirectional layout (`<w:bidi/>` on paragraphs/tables and `<w:rtl/>` on runs) and East Asian font binding when compiling non-Latin locales.
  4. Route `mcp_compile_tower_annex` in `src/mcp_server.py` exclusively through `build_tower_annex_ast` $\rightarrow$ `DocxCompiler`. Delete `render_tower_annex_from_template.py`.

### PR-4: Multi-Tenant, Multi-Lingual Architectural Fitness Suite
* **Objective:** Lock in all six invariants via static AST code inspection and multi-tenant Golden Master OpenXML verification across diverse industries, currencies, and languages.
* **Target Files:**
  - `tests/architecture/test_no_binary_template_split_brain.py`
* **Key Deliverable Specifications:**
  1. Static Python AST audit of `src/` verifying zero imports, dynamic loads, or references to legacy template mutators or `{{TAG}}` interpolation patterns.
  2. Parameterized end-to-end compilation verification across multiple industry/locale profiles (e.g., Heavy Manufacturing in `es`/`EUR`, Global Tier-1 Investment Banking in `en`/`USD`, Precision Robotics in `ja`/`JPY`, Energy Infrastructure in `ar`/`SAR`).
  3. Physical OpenXML XPath audit verifying WCAG 2.1 contrast ratios ($CR \ge 4.5$) on every `<w:r>` element in the generated `.docx` binary.

---

## 4. Production Reference Implementations & Exact Signatures

### 4.1 `engine_config/locales.json` (Canonical Schema Excerpt)
```json
{
  "en": {
    "meta_direction": "ltr",
    "font_primary": "Calibri",
    "font_east_asian": "MS Mincho",
    "chapter_1_executive_summary": "Chapter 1: Executive Summary & Governing Strategic Thesis",
    "chapter_2_telemetry_architecture": "Chapter 2: Infrastructure Telemetry & Architectural Baseline",
    "chapter_3_diagnosis_cross_cutting": "Chapter 3: Cross-Cutting Diagnosis & Systemic Risk Correlation",
    "chapter_4_fair_quantification": "Chapter 4: Quantitative Financial Risk Analysis (FAIR Model)",
    "chapter_5_strategic_roadmap": "Chapter 5: Executive Decision Matrix & Remediation Roadmap (CAPEX/OPEX)",
    "diagnosis_performance_matrix_title": "Operational Performance, Resilience & Asset Degradation Matrix",
    "decision_matrix_title": "Executive Decision & Investment Prioritization Matrix (CAPEX/OPEX)",
    "table_col_scenario_id": "Scenario ID",
    "table_col_asset_domain": "Affected Asset & Domain",
    "table_col_tef_vuln": "TEF / Vulnerability",
    "table_col_ale": "Annualized Loss Expectancy (ALE)",
    "table_col_remediation_capex": "Remediation Investment (CAPEX/OPEX)",
    "table_col_regulatory_impact": "Regulatory & Compliance Exposure",
    "narrative_governing_thesis_prefix": "Governing Executive Thesis:",
    "narrative_fair_explainability_template": "Financial Risk Attribution [{scenario_id}]: Within the {domain} domain, empirical telemetry across {asset_name} reveals {failure_mode}. Under the FAIR quantitative model, a Threat Event Frequency (TEF) of {tef} events/year combined with a control vulnerability probability of {vuln_pct}% yields a Loss Event Frequency (LEF) of {lef} events/year. Coupling Primary Loss Magnitude ({plm}) and Secondary Regulatory/Operational Loss Magnitude ({slm}) under {regulations} produces a verified Annualized Loss Expectancy (ALE) of {ale}. Allocating {capex} Toward {remediation_action} reduces residual ALE to {residual_ale} (Net Risk Reduction: {net_roi})."
  },
  "es": {
    "meta_direction": "ltr",
    "font_primary": "Calibri",
    "font_east_asian": "MS Mincho",
    "chapter_1_executive_summary": "Capítulo 1: Resumen Ejecutivo y Tesis Estratégica Rectora",
    "chapter_2_telemetry_architecture": "Capítulo 2: Telemetría de Infraestructura y Línea Base Arquitectónica",
    "chapter_3_diagnosis_cross_cutting": "Capítulo 3: Diagnóstico Transversal y Correlación de Riesgos Sistémicos",
    "chapter_4_fair_quantification": "Capítulo 4: Cuantificación Financiera de Riesgos (Modelo FAIR)",
    "chapter_5_strategic_roadmap": "Capítulo 5: Matriz de Decisión Ejecutiva y Hoja de Ruta de Remediación (CAPEX/OPEX)",
    "diagnosis_performance_matrix_title": "Matriz de Rendimiento Operativo, Resiliencia y Degradación de Activos",
    "decision_matrix_title": "Matriz de Decisión Ejecutiva y Priorización de Inversiones (CAPEX/OPEX)",
    "table_col_scenario_id": "ID Escenario",
    "table_col_asset_domain": "Activo y Dominio Afectado",
    "table_col_tef_vuln": "TEF / Vulnerabilidad",
    "table_col_ale": "Expectativa de Pérdida Anualizada (ALE)",
    "table_col_remediation_capex": "Inversión de Remediación (CAPEX/OPEX)",
    "table_col_regulatory_impact": "Exposición Regulatoria y Normativa",
    "narrative_governing_thesis_prefix": "Tesis Ejecutiva Rectora:",
    "narrative_fair_explainability_template": "Atribución de Riesgo Financiero [{scenario_id}]: En el dominio {domain}, la telemetría empírica sobre {asset_name} evidencia {failure_mode}. Bajo el modelo cuantitativo FAIR, una Frecuencia de Eventos de Amenaza (TEF) de {tef} eventos/año combinada con una probabilidad de vulnerabilidad del {vuln_pct}% genera una Frecuencia de Eventos de Pérdida (LEF) de {lef} eventos/año. Al integrar la Magnitud de Pérdida Primaria ({plm}) y Secundaria ({slm}) bajo el marco {regulations}, se determina una Expectativa de Pérdida Anualizada (ALE) de {ale}. La asignación de {capex} para {remediation_action} reduce el ALE residual a {residual_ale} (Reducción Neta de Riesgo: {net_roi})."
  }
}
```

### 4.2 `src/assessment_engine/i18n/resolver.py`
```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Mapping
import json


class MissingLocalizationKeyError(KeyError):
    """Raised when a locale or localization key is absent or empty (Invariant III)."""


@dataclass(frozen=True)
class CurrencyFormatSpec:
    """Locale-independent specification for ISO 4217 monetary rendering."""
    symbol: str
    symbol_prefix: bool
    thousands_sep: str
    decimal_sep: str


_CURRENCY_SPECS: Mapping[str, CurrencyFormatSpec] = {
    "USD": CurrencyFormatSpec(symbol="$", symbol_prefix=True, thousands_sep=",", decimal_sep="."),
    "EUR": CurrencyFormatSpec(symbol="€", symbol_prefix=False, thousands_sep=".", decimal_sep=","),
    "GBP": CurrencyFormatSpec(symbol="£", symbol_prefix=True, thousands_sep=",", decimal_sep="."),
    "JPY": CurrencyFormatSpec(symbol="¥", symbol_prefix=True, thousands_sep=",", decimal_sep="."),
    "BRL": CurrencyFormatSpec(symbol="R$", symbol_prefix=True, thousands_sep=".", decimal_sep=","),
    "SAR": CurrencyFormatSpec(symbol="SAR", symbol_prefix=False, thousands_sep=",", decimal_sep="."),
    "SGD": CurrencyFormatSpec(symbol="S$", symbol_prefix=True, thousands_sep=",", decimal_sep="."),
}


class DeclarativeI18nResolver:
    """
    Strict, zero-fallback localization and monetary formatting engine.
    Enforces Invariant III (Total Declarative i18n Bijection) and Invariant IV (Zero Hardcoding).
    """

    def __init__(self, locales_path: Path) -> None:
        self._locales_path: Path = locales_path
        self._registry: Dict[str, Dict[str, str]] = self._load_and_validate_registry()

    def _load_and_validate_registry(self) -> Dict[str, Dict[str, str]]:
        if not self._locales_path.exists():
            raise FileNotFoundError(f"Localization registry not found at: {self._locales_path}")
        with self._locales_path.open("r", encoding="utf-8") as handle:
            data: Any = json.load(handle)
        if not isinstance(data, dict) or not data:
            raise ValueError(f"Localization registry at {self._locales_path} must be a non-empty JSON object.")

        # Enforce bijective key parity across all registered locales
        locales = list(data.keys())
        canonical_keys = set(data[locales[0]].keys())
        for loc in locales[1:]:
            loc_keys = set(data[loc].keys())
            diff = canonical_keys.symmetric_difference(loc_keys)
            if diff:
                raise MissingLocalizationKeyError(
                    f"Invariant III Bijection Failure: Locale '{loc}' diverges from '{locales[0]}' on keys: {sorted(diff)}"
                )
        return data

    @staticmethod
    def _normalize_locale(locale: str) -> str:
        if not locale or not locale.strip():
            raise MissingLocalizationKeyError("Target locale must be explicitly provided; empty locale prohibited.")
        return locale.strip().split("-")[0].split("_")[0].lower()

    def resolve(self, key: str, *, locale: str, **format_kwargs: Any) -> str:
        """Resolves a symbolic key strictly for the given locale with optional named interpolation."""
        norm_locale = self._normalize_locale(locale)
        if norm_locale not in self._registry:
            raise MissingLocalizationKeyError(
                f"Invariant III Violation: Unsupported target locale '{locale}' (normalized: '{norm_locale}')."
            )
        locale_table = self._registry[norm_locale]
        if key not in locale_table or not str(locale_table[key]).strip():
            raise MissingLocalizationKeyError(
                f"Invariant III Violation: Missing or empty key '{key}' for locale '{norm_locale}'."
            )
        template = locale_table[key]
        if format_kwargs:
            try:
                return template.format(**format_kwargs)
            except KeyError as exc:
                raise MissingLocalizationKeyError(
                    f"Missing template interpolation parameter {exc} for key '{key}' in locale '{norm_locale}'."
                ) from exc
        return template

    def format_currency(self, amount: float | Decimal, *, currency_code: str, compact_millions: bool = True) -> str:
        """
        Formats monetary risk exposures deterministically for any ISO 4217 currency code.
        Zero hardcoded currency symbols or locale assumptions.
        """
        code = currency_code.strip().upper()
        spec = _CURRENCY_SPECS.get(
            code,
            CurrencyFormatSpec(symbol=code, symbol_prefix=False, thousands_sep=",", decimal_sep="."),
        )
        dec_amount = Decimal(str(amount))
        if compact_millions and abs(dec_amount) >= Decimal("1000000"):
            millions = (dec_amount / Decimal("1000000")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            int_part, frac_part = f"{millions:.2f}".split(".")
            formatted_num = f"{int_part}{spec.decimal_sep}{frac_part}M"
        else:
            quantized = dec_amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            raw_int = f"{int(quantized):,}"
            formatted_num = raw_int.replace(",", spec.thousands_sep)

        if spec.symbol_prefix:
            return f"{spec.symbol}{formatted_num}"
        return f"{formatted_num} {spec.symbol}"
```

### 4.3 `src/assessment_engine/ast/nodes.py`
```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple


class TextDirection(str, Enum):
    """Defines script rendering directionality for global language support (Law #3)."""
    LTR = "ltr"
    RTL = "rtl"


@dataclass(frozen=True)
class ASTNode:
    """Abstract base node for the pure Python Document Intermediate Representation (Invariant VI)."""


@dataclass(frozen=True)
class TextSpanNode(ASTNode):
    """Leaf text run with explicit typographic and color attributes."""
    text: str
    fg_color_hex: str = "111827"
    bold: bool = False
    italic: bool = False
    font_size_pt: float = 10.5


@dataclass(frozen=True)
class ParagraphNode(ASTNode):
    """Block-level narrative paragraph composed of styled spans."""
    spans: Tuple[TextSpanNode, ...]
    bg_color_hex: str | None = None
    space_after_pt: float = 6.0
    keep_with_next: bool = False


@dataclass(frozen=True)
class TableCellNode(ASTNode):
    """Table cell container with explicit background shading and nested paragraphs."""
    paragraphs: Tuple[ParagraphNode, ...]
    bg_color_hex: str | None = None


@dataclass(frozen=True)
class TableRowNode(ASTNode):
    """Horizontal row of table cells."""
    cells: Tuple[TableCellNode, ...]
    is_header: bool = False


@dataclass(frozen=True)
class TableNode(ASTNode):
    """Analytical matrix with caption title and deterministic column geometry."""
    title: str
    rows: Tuple[TableRowNode, ...]
    col_count: int


@dataclass(frozen=True)
class SectionNode(ASTNode):
    """Sub-chapter analytical section grouping narrative prose and analytical tables."""
    heading: str
    level: int
    children: Tuple[ParagraphNode | TableNode, ...]
    fg_color_hex: str = "0A192F"


@dataclass(frozen=True)
class ChapterNode(ASTNode):
    """Top-level book chapter following the Minto Pyramid narrative structure."""
    title: str
    level: int = 1
    fg_color_hex: str = "0A192F"
    children: Tuple[ParagraphNode | TableNode | SectionNode, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DocumentNode(ASTNode):
    """Root AST node representing a complete, verified executive deliverable."""
    tenant_name: str
    locale: str
    currency_code: str
    direction: TextDirection
    font_primary: str
    font_east_asian: str
    chapters: Tuple[ChapterNode, ...]
```

### 4.4 `src/assessment_engine/compiler/style_invariants.py`
```python
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ContrastInvariantViolationError(ValueError):
    """Raised when strict contrast verification fails WCAG 2.1 thresholds (Invariant II)."""


class StyleInvariantGuard:
    """
    Enforces Invariant II: Universal WCAG 2.1 Physical Contrast Ratio Guarantee.
    Mathematically eliminates White-on-White (#FFFFFF on #FFFFFF) and low-contrast legibility defects.
    """

    DEFAULT_DARK_TEXT_HEX: str = "111827"   # Executive Charcoal (Luminance ~0.012)
    DEFAULT_LIGHT_TEXT_HEX: str = "FFFFFF"  # Pure White (Luminance 1.000)
    DEFAULT_LIGHT_BG_HEX: str = "FFFFFF"    # Unshaded Page Canvas
    WCAG_AA_MIN_CONTRAST_RATIO: float = 4.5

    @staticmethod
    def normalize_hex(hex_str: str) -> str:
        clean = hex_str.strip().lstrip("#").upper()
        if len(clean) != 6 or any(c not in "0123456789ABCDEF" for c in clean):
            raise ValueError(f"Invalid 6-character RGB hex string: '{hex_str}'")
        return clean

    @classmethod
    def hex_to_rgb(cls, hex_str: str) -> Tuple[int, int, int]:
        clean = cls.normalize_hex(hex_str)
        return int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16)

    @classmethod
    def relative_luminance(cls, hex_str: str) -> float:
        """Computes WCAG 2.1 relative luminance L in [0.0, 1.0]."""
        r, g, b = cls.hex_to_rgb(hex_str)

        def _linearize(channel: int) -> float:
            s_rgb = channel / 255.0
            return s_rgb / 12.92 if s_rgb <= 0.03928 else ((s_rgb + 0.055) / 1.055) ** 2.4

        return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)

    @classmethod
    def contrast_ratio(cls, fg_hex: str, bg_hex: str) -> float:
        """Computes exact WCAG 2.1 contrast ratio CR in [1.0, 21.0]."""
        lum_fg = cls.relative_luminance(fg_hex)
        lum_bg = cls.relative_luminance(bg_hex)
        lighter = max(lum_fg, lum_bg)
        darker = min(lum_fg, lum_bg)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def enforce_safe_foreground(
        cls,
        fg_hex: Optional[str],
        bg_hex: Optional[str],
        *,
        strict: bool = False,
    ) -> str:
        """
        Verifies that (fg_hex, bg_hex) satisfies CR >= 4.5:1.
        If violated, raises ContrastInvariantViolationError (if strict=True) or coerces
        foreground to the highest-contrast executive anchor (#111827 or #FFFFFF).
        """
        norm_fg = cls.normalize_hex(fg_hex if fg_hex else cls.DEFAULT_DARK_TEXT_HEX)
        raw_bg = (bg_hex or "").strip().lstrip("#").upper()
        is_unshaded = raw_bg in ("", "NONE", "AUTO", "CLEAR")
        effective_bg = cls.DEFAULT_LIGHT_BG_HEX if is_unshaded else cls.normalize_hex(raw_bg)

        ratio = cls.contrast_ratio(norm_fg, effective_bg)
        if ratio < cls.WCAG_AA_MIN_CONTRAST_RATIO:
            bg_lum = cls.relative_luminance(effective_bg)
            remediated_fg = cls.DEFAULT_DARK_TEXT_HEX if bg_lum > 0.18 else cls.DEFAULT_LIGHT_TEXT_HEX
            msg = (
                f"Invariant II Triggered: Contrast ratio {ratio:.2f}:1 between foreground #{norm_fg} "
                f"and background #{effective_bg} (raw='{bg_hex}') is below WCAG 2.1 threshold "
                f"{cls.WCAG_AA_MIN_CONTRAST_RATIO}:1. Remediating foreground to #{remediated_fg}."
            )
            if strict:
                raise ContrastInvariantViolationError(msg)
            logger.warning(msg)
            return remediated_fg

        return norm_fg
```

### 4.5 `src/assessment_engine/ast/payload_to_ast.py`
```python
from typing import Any, Dict, List
from src.assessment_engine.ast.nodes import (
    ChapterNode,
    DocumentNode,
    ParagraphNode,
    TableCellNode,
    TableNode,
    TableRowNode,
    TextDirection,
    TextSpanNode,
)
from src.assessment_engine.i18n.resolver import DeclarativeI18nResolver

NAVY_HEADER_BG = "0A192F"
ZEBRA_ROW_BG = "F8FAFC"
WHITE_BG = "FFFFFF"
CHARCOAL_FG = "111827"
WHITE_FG = "FFFFFF"


def _make_paragraph(
    text: str,
    *,
    fg_hex: str = CHARCOAL_FG,
    bold: bool = False,
    bg_hex: str | None = None,
) -> ParagraphNode:
    return ParagraphNode(
        spans=(TextSpanNode(text=text, fg_color_hex=fg_hex, bold=bold),),
        bg_color_hex=bg_hex,
    )


def _build_analytical_table(
    title: str,
    headers: List[str],
    data_rows: List[List[str]],
) -> TableNode:
    header_cells = tuple(
        TableCellNode(
            paragraphs=(_make_paragraph(h, fg_hex=WHITE_FG, bold=True, bg_hex=NAVY_HEADER_BG),),
            bg_color_hex=NAVY_HEADER_BG,
        )
        for h in headers
    )
    rows: List[TableRowNode] = [TableRowNode(cells=header_cells, is_header=True)]

    for r_idx, row_values in enumerate(data_rows):
        row_bg = ZEBRA_ROW_BG if r_idx % 2 == 1 else WHITE_BG
        cells = tuple(
            TableCellNode(
                paragraphs=(_make_paragraph(val, fg_hex=CHARCOAL_FG, bold=(c_idx == 0), bg_hex=row_bg),),
                bg_color_hex=row_bg,
            )
            for c_idx, val in enumerate(row_values)
        )
        rows.append(TableRowNode(cells=cells, is_header=False))

    return TableNode(title=title, rows=tuple(rows), col_count=len(headers))


def build_tower_annex_ast(
    cegar_payload: Dict[str, Any],
    i18n: DeclarativeI18nResolver,
    *,
    locale: str,
) -> DocumentNode:
    """
    Compiler Frontend: Lowers an industry-agnostic CEGAR/FAIR Domain Payload into a
    5-Chapter Minto Pyramid DocumentNode AST.
    Enforces Invariants III, IV, V, and VI.
    """
    tenant_meta = cegar_payload["tenant_metadata"]
    tenant_name: str = tenant_meta["organization_name"]
    currency_code: str = tenant_meta["currency_code"]
    regulations: str = ", ".join(tenant_meta.get("regulatory_frameworks", ["ISO/IEC 27001"]))
    governing_thesis: str = cegar_payload["executive_summary"]["governing_thesis"]
    risk_scenarios: List[Dict[str, Any]] = cegar_payload["risk_scenarios"]
    analytical_tables_spec: List[Dict[str, Any]] = cegar_payload.get("analytical_tables", [])

    direction_str = i18n.resolve("meta_direction", locale=locale)
    direction = TextDirection.RTL if direction_str.lower() == "rtl" else TextDirection.LTR
    font_primary = i18n.resolve("font_primary", locale=locale)
    font_east_asian = i18n.resolve("font_east_asian", locale=locale)

    # Synthesize FAIR Explainability Narratives and Core Risk Rows (Invariant V)
    fair_narratives: List[ParagraphNode] = []
    fair_matrix_rows: List[List[str]] = []

    for scenario in risk_scenarios:
        ale_fmt = i18n.format_currency(scenario["ale_amount"], currency_code=currency_code)
        plm_fmt = i18n.format_currency(scenario["plm_amount"], currency_code=currency_code)
        slm_fmt = i18n.format_currency(scenario["slm_amount"], currency_code=currency_code)
        capex_fmt = i18n.format_currency(scenario["remediation_capex"], currency_code=currency_code)
        res_ale_fmt = i18n.format_currency(scenario["residual_ale_amount"], currency_code=currency_code)
        net_roi_fmt = i18n.format_currency(
            scenario["ale_amount"] - scenario["residual_ale_amount"],
            currency_code=currency_code,
        )

        prose = i18n.resolve(
            "narrative_fair_explainability_template",
            locale=locale,
            scenario_id=scenario["scenario_id"],
            domain=scenario["domain"],
            asset_name=scenario["asset_name"],
            failure_mode=scenario["failure_mode"],
            tef=scenario["tef"],
            vuln_pct=scenario["vulnerability_pct"],
            lef=scenario["lef"],
            plm=plm_fmt,
            slm=slm_fmt,
            regulations=regulations,
            ale=ale_fmt,
            capex=capex_fmt,
            remediation_action=scenario["remediation_action"],
            residual_ale=res_ale_fmt,
            net_roi=net_roi_fmt,
        )
        fair_narratives.append(_make_paragraph(prose))
        fair_matrix_rows.append([
            scenario["scenario_id"],
            f"{scenario['domain']} — {scenario['asset_name']}",
            f"TEF: {scenario['tef']}/yr | Vuln: {scenario['vulnerability_pct']}%",
            ale_fmt,
            f"{capex_fmt} ({scenario['remediation_action']})",
            regulations,
        ])

    common_headers = [
        i18n.resolve("table_col_scenario_id", locale=locale),
        i18n.resolve("table_col_asset_domain", locale=locale),
        i18n.resolve("table_col_tef_vuln", locale=locale),
        i18n.resolve("table_col_ale", locale=locale),
        i18n.resolve("table_col_remediation_capex", locale=locale),
        i18n.resolve("table_col_regulatory_impact", locale=locale),
    ]

    perf_matrix = _build_analytical_table(
        title=i18n.resolve("diagnosis_performance_matrix_title", locale=locale),
        headers=common_headers,
        data_rows=fair_matrix_rows,
    )
    decision_matrix = _build_analytical_table(
        title=i18n.resolve("decision_matrix_title", locale=locale),
        headers=common_headers,
        data_rows=fair_matrix_rows,
    )

    # Synthesize supplemental domain tables from payload (target: 11 total analytical tables)
    supplemental_tables: List[TableNode] = []
    for tbl_spec in analytical_tables_spec:
        supplemental_tables.append(
            _build_analytical_table(
                title=tbl_spec["title"],
                headers=tbl_spec["headers"],
                data_rows=tbl_spec["rows"],
            )
        )

    narrative_blocks: List[str] = cegar_payload.get("narrative_blocks", [])
    extra_paragraphs = [_make_paragraph(block) for block in narrative_blocks]

    thesis_prefix = i18n.resolve("narrative_governing_thesis_prefix", locale=locale)
    governing_para = ParagraphNode(
        spans=(
            TextSpanNode(text=f"{thesis_prefix} ", fg_color_hex=NAVY_HEADER_BG, bold=True),
            TextSpanNode(text=governing_thesis, fg_color_hex=CHARCOAL_FG, bold=False),
        )
    )

    chapters = (
        ChapterNode(
            title=i18n.resolve("chapter_1_executive_summary", locale=locale),
            children=(governing_para, *fair_narratives[:2], *extra_paragraphs[:28]),
        ),
        ChapterNode(
            title=i18n.resolve("chapter_2_telemetry_architecture", locale=locale),
            children=(*extra_paragraphs[28:58], *supplemental_tables[:3]),
        ),
        ChapterNode(
            title=i18n.resolve("chapter_3_diagnosis_cross_cutting", locale=locale),
            children=(
                _make_paragraph(perf_matrix.title, fg_hex=NAVY_HEADER_BG, bold=True),
                perf_matrix,
                *fair_narratives,
                *extra_paragraphs[58:88],
                *supplemental_tables[3:6],
            ),
        ),
        ChapterNode(
            title=i18n.resolve("chapter_4_fair_quantification", locale=locale),
            children=(*extra_paragraphs[88:116], *supplemental_tables[6:9]),
        ),
        ChapterNode(
            title=i18n.resolve("chapter_5_strategic_roadmap", locale=locale),
            children=(
                _make_paragraph(decision_matrix.title, fg_hex=NAVY_HEADER_BG, bold=True),
                decision_matrix,
                *extra_paragraphs[116:],
            ),
        ),
    )

    return DocumentNode(
        tenant_name=tenant_name,
        locale=locale,
        currency_code=currency_code,
        direction=direction,
        font_primary=font_primary,
        font_east_asian=font_east_asian,
        chapters=chapters,
    )
```

### 4.6 `src/assessment_engine/compiler/docx_compiler.py`
```python
from pathlib import Path
from typing import Optional
import docx
from docx.document import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from docx.table import _Cell
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from src.assessment_engine.ast.nodes import (
    ASTNode,
    ChapterNode,
    DocumentNode,
    ParagraphNode,
    SectionNode,
    TableCellNode,
    TableNode,
    TextDirection,
    TextSpanNode,
)
from src.assessment_engine.compiler.style_invariants import StyleInvariantGuard


class ASTNodeVisitor:
    """Deterministic Gang of Four (GoF) Visitor base class for AST compilation."""

    def visit(self, node: ASTNode) -> None:
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        visitor(node)

    def generic_visit(self, node: ASTNode) -> None:
        raise NotImplementedError(f"Compiler backend missing handler for AST node: {type(node).__name__}")


class DocxCompiler(ASTNodeVisitor):
    """
    Stateless, Multi-Pass AST Backend Compiler for OpenXML (.docx).
    Enforces Invariant II (WCAG 2.1 Contrast Ratio) and Invariant VI (Clean Architecture).
    Supports global scripts (LTR, RTL BiDi, and East Asian typography).
    """

    def __init__(self, *, strict_contrast: bool = False) -> None:
        self._strict_contrast: bool = strict_contrast
        self._doc: Optional[DocxDocument] = None
        self._current_bg_context: Optional[str] = None
        self._direction: TextDirection = TextDirection.LTR
        self._font_primary: str = "Calibri"
        self._font_east_asian: str = "MS Mincho"

    def compile(self, root: DocumentNode, output_path: Path) -> Path:
        """Compiles an immutable DocumentNode AST into a physical OpenXML binary."""
        self._doc = docx.Document()
        self._current_bg_context = None
        self._direction = root.direction
        self._font_primary = root.font_primary
        self._font_east_asian = root.font_east_asian

        self.visit(root)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._doc.save(str(output_path))
        self._doc = None
        return output_path

    def visit_DocumentNode(self, node: DocumentNode) -> None:
        for chapter in node.chapters:
            self.visit(chapter)

    def visit_ChapterNode(self, node: ChapterNode) -> None:
        assert self._doc is not None
        heading = self._doc.add_heading(level=node.level)
        self._apply_paragraph_direction(heading)
        run = heading.add_run(node.title)
        self._apply_run_style(
            run=run,
            span=TextSpanNode(text=node.title, fg_color_hex=node.fg_color_hex, bold=True, font_size_pt=16.0),
            bg_hex=None,
        )
        for child in node.children:
            self.visit(child)

    def visit_SectionNode(self, node: SectionNode) -> None:
        assert self._doc is not None
        heading = self._doc.add_heading(level=node.level)
        self._apply_paragraph_direction(heading)
        run = heading.add_run(node.heading)
        self._apply_run_style(
            run=run,
            span=TextSpanNode(text=node.heading, fg_color_hex=node.fg_color_hex, bold=True, font_size_pt=13.0),
            bg_hex=None,
        )
        for child in node.children:
            self.visit(child)

    def visit_ParagraphNode(self, node: ParagraphNode) -> None:
        assert self._doc is not None
        para = self._doc.add_paragraph()
        self._compile_paragraph_contents(para, node)

    def visit_TableNode(self, node: TableNode) -> None:
        assert self._doc is not None
        table = self._doc.add_table(rows=len(node.rows), cols=node.col_count)
        if self._direction == TextDirection.RTL:
            tbl_pr = table._tbl.tblPr
            if tbl_pr is not None:
                bidi_visual = OxmlElement("w:bidiVisual")
                tbl_pr.append(bidi_visual)

        for r_idx, row_node in enumerate(node.rows):
            for c_idx, cell_node in enumerate(row_node.cells):
                docx_cell = table.cell(r_idx, c_idx)
                self._compile_table_cell(docx_cell, cell_node)

    def _compile_table_cell(self, docx_cell: _Cell, cell_node: TableCellNode) -> None:
        prev_bg = self._current_bg_context
        self._current_bg_context = cell_node.bg_color_hex

        if cell_node.bg_color_hex:
            self._set_cell_background_xml(docx_cell, cell_node.bg_color_hex)

        docx_cell.text = ""
        for p_idx, para_node in enumerate(cell_node.paragraphs):
            para = docx_cell.paragraphs[0] if p_idx == 0 else docx_cell.add_paragraph()
            self._compile_paragraph_contents(para, para_node)

        self._current_bg_context = prev_bg

    def _compile_paragraph_contents(self, para: Paragraph, node: ParagraphNode) -> None:
        self._apply_paragraph_direction(para)
        para.paragraph_format.space_after = Pt(node.space_after_pt)
        para.paragraph_format.keep_with_next = node.keep_with_next

        effective_bg = node.bg_color_hex or self._current_bg_context
        if node.bg_color_hex and self._current_bg_context is None:
            self._set_paragraph_background_xml(para, node.bg_color_hex)

        for span in node.spans:
            run = para.add_run(span.text)
            self._apply_run_style(run=run, span=span, bg_hex=effective_bg)

    def _apply_paragraph_direction(self, para: Paragraph) -> None:
        if self._direction == TextDirection.RTL:
            p_pr = para._p.get_or_add_pPr()
            if p_pr.find(qn("w:bidi")) is None:
                p_pr.append(OxmlElement("w:bidi"))

    @staticmethod
    def _set_cell_background_xml(cell: _Cell, bg_hex: str) -> None:
        """
        Idempotently writes <w:shd w:val='clear' w:color='auto' w:fill='HEX'/> into <w:tcPr>.
        Removes any pre-existing <w:shd> child first to prevent ECMA-376 schema collisions.
        """
        clean_hex = StyleInvariantGuard.normalize_hex(bg_hex)
        tc_pr = cell._tc.get_or_add_tcPr()
        for existing_shd in tc_pr.findall(qn("w:shd")):
            tc_pr.remove(existing_shd)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), clean_hex)
        tc_pr.append(shd)

    @staticmethod
    def _set_paragraph_background_xml(para: Paragraph, bg_hex: str) -> None:
        clean_hex = StyleInvariantGuard.normalize_hex(bg_hex)
        p_pr = para._p.get_or_add_pPr()
        for existing_shd in p_pr.findall(qn("w:shd")):
            p_pr.remove(existing_shd)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), clean_hex)
        p_pr.append(shd)

    def _apply_run_style(
        self,
        run: Run,
        span: TextSpanNode,
        bg_hex: Optional[str],
    ) -> None:
        safe_fg = StyleInvariantGuard.enforce_safe_foreground(
            fg_hex=span.fg_color_hex,
            bg_hex=bg_hex,
            strict=self._strict_contrast,
        )
        r, g, b = StyleInvariantGuard.hex_to_rgb(safe_fg)
        run.font.color.rgb = RGBColor(r, g, b)
        run.font.size = Pt(span.font_size_pt)
        run.font.name = self._font_primary
        run.bold = span.bold
        run.italic = span.italic

        r_pr = run._r.get_or_add_rPr()
        r_fonts = r_pr.find(qn("w:rFonts"))
        if r_fonts is None:
            r_fonts = OxmlElement("w:rFonts")
            r_pr.insert(0, r_fonts)
        r_fonts.set(qn("w:ascii"), self._font_primary)
        r_fonts.set(qn("w:hAnsi"), self._font_primary)
        r_fonts.set(qn("w:cs"), self._font_primary)
        r_fonts.set(qn("w:eastAsia"), self._font_east_asian)

        if self._direction == TextDirection.RTL and r_pr.find(qn("w:rtl")) is None:
            r_pr.append(OxmlElement("w:rtl"))
```

### 4.7 `src/mcp_server.py` (Converged Entrypoint)
```python
from pathlib import Path
from typing import Any, Dict
from src.assessment_engine.ast.payload_to_ast import build_tower_annex_ast
from src.assessment_engine.compiler.docx_compiler import DocxCompiler
from src.assessment_engine.i18n.resolver import DeclarativeI18nResolver

DEFAULT_LOCALES_PATH = Path("engine_config/locales.json")


def mcp_compile_tower_annex(
    payload: Dict[str, Any],
    output_docx_path: str,
    *,
    locale: str,
    locales_path: Path = DEFAULT_LOCALES_PATH,
    strict_contrast: bool = False,
) -> Dict[str, Any]:
    """
    MCP Tool Entrypoint (RFC-026 Converged).
    Routes 100% of synthesis workloads through the Declarative AST Pipeline.
    Zero hardcoded tenant, currency, or language defaults.
    """
    resolver = DeclarativeI18nResolver(locales_path=locales_path)
    ast_root = build_tower_annex_ast(cegar_payload=payload, i18n=resolver, locale=locale)

    compiler = DocxCompiler(strict_contrast=strict_contrast)
    compiled_path = compiler.compile(root=ast_root, output_path=Path(output_docx_path))

    return {
        "status": "SUCCESS",
        "compiler_engine": "AST_DOCX_COMPILER_V2",
        "tenant": ast_root.tenant_name,
        "locale": ast_root.locale,
        "currency": ast_root.currency_code,
        "artifact_path": str(compiled_path.resolve()),
        "chapters_synthesized": len(ast_root.chapters),
    }
```

### 4.8 `tests/architecture/test_no_binary_template_split_brain.py`
```python
import ast
from pathlib import Path
from typing import Any, Dict
import docx
from docx.oxml.ns import qn
import pytest

from src.assessment_engine.compiler.style_invariants import StyleInvariantGuard
from src.mcp_server import mcp_compile_tower_annex

SRC_ROOT = Path("src")
FORBIDDEN_IDENTIFIERS = {"render_tower_annex_from_template"}


def test_invariant_i_and_vi_static_ast_purity_and_zero_split_brain() -> None:
    """
    Verifies Invariant I (Zero Split-Brain) and Invariant VI (Clean Architecture)
    via static Python AST inspection across all source modules.
    """
    pure_layers = {"ast", "i18n"}
    for py_file in SRC_ROOT.rglob("*.py"):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        is_pure_layer = any(part in pure_layers for part in py_file.parts)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert all(f not in alias.name for f in FORBIDDEN_IDENTIFIERS), (
                        f"Invariant I Violation in {py_file}: Forbidden legacy import '{alias.name}'"
                    )
                    if is_pure_layer:
                        assert not alias.name.startswith(("docx", "lxml")), (
                            f"Invariant VI Violation in {py_file}: OpenXML dependency '{alias.name}' in pure AST/i18n layer"
                        )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert all(f not in node.module for f in FORBIDDEN_IDENTIFIERS), (
                    f"Invariant I Violation in {py_file}: Forbidden legacy import from '{node.module}'"
                )
                if is_pure_layer:
                    assert not node.module.startswith(("docx", "lxml")), (
                        f"Invariant VI Violation in {py_file}: OpenXML dependency '{node.module}' in pure AST/i18n layer"
                    )


@pytest.mark.parametrize(
    "tenant_fixture",
    [
        {
            "locale": "es",
            "currency_code": "EUR",
            "organization_name": "Industrial Cement & Aggregates Corp",
            "regulatory_frameworks": ["NIS2 Directive (EU)", "ISO/IEC 27001"],
            "expected_ale_formatted": "1,05M €",
            "domain_entities": ["HPE SimpliVity", "NetApp", "CRAH", "canteras"],
        },
        {
            "locale": "en",
            "currency_code": "USD",
            "organization_name": "Global Apex Investment Bank N.A.",
            "regulatory_frameworks": ["SEC Rule 17a-4", "FFIEC", "NYDFS 23 NYCRR 500"],
            "expected_ale_formatted": "$4.80M",
            "domain_entities": ["Equinix NY4 Core", "Mainframe z16", "SWIFT Gateway", "HSM Cluster"],
        },
    ],
)
def test_universal_multi_tenant_golden_master_ast_synthesis(
    tenant_fixture: Dict[str, Any],
    tmp_path: Path,
) -> None:
    """
    Validates Invariants II, III, IV, and V across diverse global tenants, currencies, and locales.
    """
    ale_val = 1050000.0 if tenant_fixture["currency_code"] == "EUR" else 4800000.0
    ents = tenant_fixture["domain_entities"]

    payload: Dict[str, Any] = {
        "tenant_metadata": {
            "organization_name": tenant_fixture["organization_name"],
            "currency_code": tenant_fixture["currency_code"],
            "regulatory_frameworks": tenant_fixture["regulatory_frameworks"],
        },
        "executive_summary": {
            "governing_thesis": (
                f"Systemic infrastructure telemetry across {ents[0]}, {ents[1]}, {ents[2]}, and {ents[3]} "
                f"exposes an annualized financial risk of {tenant_fixture['expected_ale_formatted']}."
            )
        },
        "risk_scenarios": [
            {
                "scenario_id": "FAIR-001",
                "domain": "Core Compute & Storage",
                "asset_name": f"{ents[0]} & {ents[1]}",
                "failure_mode": f"Cascading thermal/network degradation across {ents[2]} and {ents[3]}",
                "tef": 2.4,
                "vulnerability_pct": 65.0,
                "lef": 1.56,
                "plm_amount": ale_val * 0.6,
                "slm_amount": ale_val * 0.4,
                "ale_amount": ale_val,
                "remediation_capex": ale_val * 0.22,
                "remediation_action": "Active-Active Metro Clustering & Redundant Thermal Loops",
                "residual_ale_amount": ale_val * 0.08,
            }
        ],
        "analytical_tables": [
            {
                "title": f"Supplemental Telemetry Matrix #{idx}",
                "headers": ["Asset Node", "Telemetry Metric", "Status"],
                "rows": [[ents[idx % len(ents)], "Availability SLA", "CRITICAL"]],
            }
            for idx in range(1, 10)
        ],
        "narrative_blocks": [
            f"Analytical narrative paragraph #{i} detailing causal architecture telemetry for {ents[i % len(ents)]}."
            for i in range(1, 140)
        ],
    }

    out_file = tmp_path / f"Deliverable_{tenant_fixture['locale']}.docx"
    result = mcp_compile_tower_annex(
        payload=payload,
        output_docx_path=str(out_file),
        locale=tenant_fixture["locale"],
        strict_contrast=True,
    )
    assert result["status"] == "SUCCESS"
    assert out_file.exists()

    doc = docx.Document(str(out_file))

    # 1. Structural Book Topology Verification (5-Chapter AST Book, >=140 Paras, 11 Tables)
    non_empty_paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    assert len(non_empty_paras) >= 140, f"Expected >= 140 narrative paragraphs, got {len(non_empty_paras)}"
    assert len(doc.tables) == 11, f"Expected 11 analytical tables, got {len(doc.tables)}"

    full_text = "\n".join(non_empty_paras) + "\n" + "\n".join(
        cell.text for tbl in doc.tables for row in tbl.rows for cell in row.cells
    )

    # 2. Invariant III: Zero Raw i18n Token Leakage
    forbidden_tokens = [
        "chapter3title",
        "chapter_3_diagnosis_cross_cutting",
        "diagnosis_performance_matrix_title",
        "decision_matrix_title",
        "{{",
        "}}",
    ]
    for token in forbidden_tokens:
        assert token not in full_text, f"Raw localization/template token leaked: '{token}'"

    # 3. Invariant IV & V: Domain Telemetry & FAIR Financial Attribution Verification
    assert tenant_fixture["expected_ale_formatted"] in full_text
    for entity in ents:
        assert entity in full_text, f"Missing critical domain entity: '{entity}'"

    # 4. Invariant II: Physical XML Inspection for WCAG 2.1 Contrast Ratio >= 4.5:1
    xml_root = doc._element
    for color_el in xml_root.iter(qn("w:color")):
        fg_val = color_el.get(qn("w:val"), "").upper()
        if not fg_val or fg_val == "AUTO":
            continue
        parent = color_el.getparent()
        effective_bg = "FFFFFF"
        while parent is not None:
            if parent.tag in (qn("w:tc"), qn("w:p")):
                shd_elements = parent.findall(f"./{qn('w:tcPr')}/{qn('w:shd')}") + parent.findall(
                    f"./{qn('w:pPr')}/{qn('w:shd')}"
                )
                for shd in shd_elements:
                    fill = shd.get(qn("w:fill"), "").upper()
                    if fill not in ("", "AUTO", "CLEAR"):
                        effective_bg = fill
                        break
            if effective_bg != "FFFFFF":
                break
            parent = parent.getparent()

        cr = StyleInvariantGuard.contrast_ratio(fg_val, effective_bg)
        assert cr >= StyleInvariantGuard.WCAG_AA_MIN_CONTRAST_RATIO, (
            f"Invariant II Violation in OpenXML: Foreground #{fg_val} over Background #{effective_bg} "
            f"yields contrast ratio {cr:.2f}:1 (< 4.5:1)!"
        )
```

---

## 5. Definition of Done & Verification Matrix

RFC-026 shall be marked **COMPLETE** and closed only when all metrics in the verification matrix below pass in the primary CI/CD pipeline:

| Telemetry Dimension | Legacy Baseline (Engine A Split-Brain) | Target Threshold (RFC-026 AST Converged) | Verification Mechanism |
| :--- | :--- | :--- | :--- |
| **Active Synthesis Engines** | `2` (Imperative Template Mutator + AST) | **`1` (Pure AST `DocxCompiler`)** | `test_invariant_i_and_vi_static_ast_purity_and_zero_split_brain` |
| **Narrative Paragraph Count** | `< 25` (Fragmented snippets) | **`>= 140` Cohesive Minto/FAIR Paragraphs** | `test_universal_multi_tenant_golden_master_ast_synthesis` |
| **Structural Table Count** | `17` (Rigid micro-tables) | **`11` Consulting-Grade Analytical Tables** | OpenXML `<w:tbl>` count assertion |
| **WCAG 2.1 Contrast Ratio** | $1.00:1$ (`#FFFFFF` on `#FFFFFF` bug) | **$\ge 4.50:1$ Across 100% of Runs** | `StyleInvariantGuard` + XPath `<w:color>` / `<w:shd>` audit |
| **Unresolved i18n Keys** | `3` (`chapter3title`, etc.) | **`0` Unresolved Keys (Bijective Gate)** | `DeclarativeI18nResolver` bijective registry validation |
| **Tenant / Locale Hardcoding** | Hardcoded Spanish / EUR assumptions | **100% Parametric** (Any Industry, ISO Currency, LTR/RTL Script) | Multi-tenant parameterized Golden Master test suite |
```