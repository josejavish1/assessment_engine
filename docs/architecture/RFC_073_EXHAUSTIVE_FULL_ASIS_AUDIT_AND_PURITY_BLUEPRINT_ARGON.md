# RFC 073: Architectural Audit & Multi-Tenant Certification of the AS-IS Assessment Generation Pipeline

**Document ID:** ARCH-AUDIT-RFC-073  
**Classification:** Tier-1 Architecture Gatekeeper Review (Strictly Confidential)  
**Target Subsystem:** AS-IS Assessment Engine (Per-Tower AST Compilers `T1..TN` & Consolidated Volume 1 Compiler)  
**Auditor:** Principal Global Systems Architect & Chief Quality Gatekeeper  

---

## 1. Executive Verdict & Risk Heatmap

### 1.1 Overall Architectural Purity Score: **6.4 / 10.0** *(CONDITIONAL FAIL — BLOCKED FOR GLOBAL MULTI-TENANT PRODUCTION)*

While the assessment engine demonstrates a sophisticated transition toward a declarative OpenXML Abstract Syntax Tree (`DocumentAST`) and deterministic actuarial risk modeling (Open FAIR), **it currently fails the Zero Single-Tenant Bias and Universal Polymorphism mandates.** 

Beneath the clean AST surface, the codebase harbors structural assumptions inherited from its initial industrial/manufacturing prototype ("Molins"). If deployed tomorrow for a megabank in Tokyo (`JPY`, 3 contracted custom towers `SEC-01`, `CLOUD-02`, `DATA-03`) or a regional hospital network in Stockholm (`SEK`, healthcare vertical), the pipeline will suffer from **actuarial scale distortion, silent domain drops, Spanish lexical leakage, and manufacturing bias injection.**

### 1.2 Architectural Risk Heatmap

| Architectural Dimension | Mandate Reference | Risk Severity | Purity Score | Primary Systemic Vulnerability |
| :--- | :--- | :---: | :---: | :--- |
| **Universal Multi-Tenancy & Scale** | Law 1 (Verticals & Currencies) | **CRITICAL** | 4.5 / 10 | Hardcoded `LM` currency brackets (`1,000`–`250,000`) and `"Enterprise & Industrial Technology"` vertical fallback. |
| **Dynamic N-Domain Polymorphism** | Law 2 (`T1..TN` & Custom IDs) | **CRITICAL** | 5.0 / 10 | Hardcoded `1 <= idx <= 10` bounds, `CANONICAL_DOMAIN_SCENARIO_BASELINE` (`T1..T10`), and brittle `x.parent.name[1:]` sorting. |
| **100% Technical English Codebase** | Law 3 (Zero Spanish in Code) | **HIGH** | 6.5 / 10 | Spanish variable `pilar`, file/key prefixes `tomo_`, and legacy Spanish financial/labor keys in payload schemas. |
| **Pure SSOT & Zero Split-Brain** | Law 4 (Dynamic Binding) | **HIGH** | 7.5 / 10 | Direct disk I/O (`locales.json` re-parsed per call) inside AST synthesizers and dual rendering pipelines (`docx` vs `DocumentAST`). |
| **Concurrency & Runtime Resilience** | Enterprise Scalability | **MEDIUM** | 8.5 / 10 | Unbounded exception silencing (`except Exception: return None`) and stateful `matplotlib` figure bleed risks in Ch. 2 Radar generation. |

---

## 2. Exhaustive Forensic Finding Log

### 2.1 CRITICAL SEVERITY FINDINGS

---

#### [CRIT-01] Hardcoded Loss Magnitude (LM) Currency Brackets & Unvalidated `rate_mult` Scaling
* **Location:** `assessment_engine/adapters/compilers/asis_fair_chapter.py` — `_render_fair_heatmap()`
* **Exact Code Citation:**
  ```python
  rate_mult = float(ctx.get("rate_mult", 1.0))
  for col_idx in range(1, 6):
      if is_critical:
          lm_ranges = {
              1: f"< {format_number(1000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
              ...
              5: f"> {format_number(250000.0 * rate_mult, locale=doc_lang, decimals=0)} {currency}",
          }
  ```
* **Root Cause:** The 5x5 Open FAIR Risk Heatmap hardcodes base monetary thresholds (`1,000`, `10,000`, `50,000`, `250,000`) calibrated for a mid-market European EUR/USD engagement, relying on an optional, unvalidated `rate_mult` context key (defaulting to `1.0`). Furthermore, this table is built imperatively in `asis_fair_chapter.py` while `ast_table_builders.py` maintains a separate `build_heatmap_mosaic` implementation (split-brain).
* **Concrete Failure Scenario (Tokyo Megabank / Global Fortune 500):**
  1. **Currency Distortion:** When compiling for a Japanese Megabank in `JPY` (¥) where `rate_mult` is omitted from `ctx` (defaulting to `1.0`), `LM 5` (Catastrophic Loss) renders as `> 250,000 JPY` (~$1,650 USD). Every trivial operational hiccup is classified as a catastrophic `LM 5` event.
  2. **Revenue Scale Distortion:** For a $100B Fortune 500 bank in `USD`, a $250,000 loss is rounding noise, yet the matrix caps the highest severity column at `> 250,000 USD` instead of dynamically calibrating against the tenant's Annual Revenue / Hourly Burn Rate in `financial_telemetry`.

---

#### [CRIT-02] Rigid 10-Tower (`T1..T10`) Bounding & Custom Domain Identifier Erasure
* **Location:**
  1. `assessment_engine/adapters/compilers/payload_to_ast.py` — `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs()`
  2. `assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py` — `Volume1AsisASTCompiler.CANONICAL_DOMAIN_SCENARIO_BASELINE` & `_build_chapter_4_forensic_diagnostics()`
  3. `assessment_engine/application/build_global_report_payload.py` — `_aggregate_tower_blueprints()`
* **Exact Code Citations:**
  ```python
  # 1. payload_to_ast.py
  canonical_key = "DEFAULT"
  match = re.search(r"(\d+)", str(tower_id))
  if match:
      idx = int(match.group(1))
      if 1 <= idx <= 10:
          canonical_key = f"T{idx}"

  # 2. tomo_asis_ast_compiler.py
  CANONICAL_DOMAIN_SCENARIO_BASELINE: Dict[str, int] = {
      "T1": 3, "T2": 4, "T3": 3, "T4": 2, "T5": 4,
      "T6": 3, "T7": 2, "T8": 3, "T9": 2, "T10": 3,
  }

  # 3. build_global_report_payload.py
  for bp in sorted(
      blueprint_files,
      key=lambda x: int(x.parent.name[1:]) if x.parent.name[1:].isdigit() else 99,
  ):
  ```
* **Root Cause:** The architecture assumes every enterprise assessment consists of the exact 10 canonical towers (`T1` through `T10`) named with a single character prefix followed by an integer.
* **Concrete Failure Scenario (Chicago Retail Giant / London Public Transit):**
  1. A client contracts a 3-domain assessment using custom enterprise identifiers (`SEC-01`, `CLOUD-02`, `DATA-03`) or expands to a 12-tower healthcare model (`T11` Biomedical IoT, `T12` Clinical EHR).
  2. In `payload_to_ast.py`, `SEC-01` is regex-coerced into `T1` (inheriting Infrastructure/Compute semantics instead of Cybersecurity), while `T11` fails `1 <= idx <= 10` and falls back to generic `"DEFAULT"`, losing its domain semantics.
  3. In `build_global_report_payload.py`, `x.parent.name[1:]` on `"SEC-01"` evaluates `"EC-01".isdigit() -> False`, dumping all custom-named towers into bucket `99` in arbitrary filesystem order.
  4. In `tomo_asis_ast_compiler.py`, `CANONICAL_DOMAIN_SCENARIO_BASELINE` hardcodes scenario counts for `T1..T10`, causing actuarial reconciliations or coverage tables to miscalculate expected risk scenarios when fewer, more, or differently keyed towers are provided.

---

#### [CRIT-03] Industrial/Manufacturing Sector Bias Hardcoded in Fallback Defaults
* **Location:** `assessment_engine/adapters/compilers/asis_fair_chapter.py` — `_render_fair_heatmap()`
* **Exact Code Citation:**
  ```python
  industry_name = ctx.get("industry", "Enterprise & Industrial Technology")
  ...
  sec_intro_p2 = t(
      "fair_heatmap_sec_p2",
      locale=doc_lang,
      client_name=client_name,
      industry_name=industry_name,
  )
  ```
* **Root Cause:** Direct residual bias from the industrial manufacturing prototype ("Molins"). Furthermore, `industry_name` is hardcoded in English (`"Enterprise & Industrial Technology"`), bypassing the localization catalog entirely when `ctx.get("industry")` is unset.
* **Concrete Failure Scenario (Stockholm Regional Hospital — `sv-SE` or `es-ES`):**
  If the `industry` key is omitted or nested under `meta.vertical` instead of top-level `ctx["industry"]`, a Swedish or Spanish hospital report injects the literal English string `"Enterprise & Industrial Technology"` directly into the localized narrative of Chapter 4.

---

### 2.2 HIGH SEVERITY FINDINGS

---

#### [HIGH-01] Violation of Law 3: Residual Spanish Identifiers in Python Source & Localization Keys
* **Location:**
  1. `assessment_engine/application/build_global_report_payload.py` (Line: `for pilar in data.get("pillars_analysis", []):`)
  2. `assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py` (Module filename `tomo_asis_ast_compiler.py` and localization keys `tomo_cover_title`, `tomo_cover_scope_default`, `tomo_cover_division_default`)
* **Exact Code Citations:**
  ```python
  # build_global_report_payload.py
  for pilar in data.get("pillars_analysis", []):
      for hc in pilar.get("health_check_asis", []):
  ```
  ```python
  # tomo_asis_ast_compiler.py
  scope_title = str(meta.get("scope_title") or meta.get("document_scope") or t("tomo_cover_scope_default", locale=doc_lang)).strip()
  ```
* **Root Cause:** Incomplete lexical refactoring from Spanish (`pilar`, `tomo`) to 100% Technical English (`pillar`, `volume`). Additionally, downstream financial and labor rate schemas across the repository remain vulnerable to legacy Spanish payload keys (`tarifas_hora`, `tecnico_medio`).
* **Concrete Failure Scenario:** Violates Law 3 (100% Technical English Codebase) and creates cognitive split-brain for global engineering teams maintaining `Volume1AsisASTCompiler` inside a file named `tomo_asis_ast_compiler.py`.

---

#### [HIGH-02] Split-Brain Document Compilation (Direct `python-docx` Mutation vs. Declarative `DocumentAST`)
* **Location:** `assessment_engine/adapters/compilers/asis_fair_chapter.py` vs. `assessment_engine/adapters/compilers/payload_to_ast.py` & `tomo_asis_ast_compiler.py`
* **Root Cause:** While `payload_to_ast.py` and `tomo_asis_ast_compiler.py` construct pure declarative `DocumentAST` trees (`TableNode`, `CellNode`, `ParagraphNode`), `asis_fair_chapter.py` directly mutates a live `python-docx` `Document` object (`doc.add_table(rows=6, cols=6)`, `shade_cell`, `set_cell_border_white`).
* **Concrete Failure Scenario:** Formatting changes, table border rules, or localization fixes applied to `ast_table_builders.py` (`build_heatmap_mosaic`) do not propagate to `asis_fair_chapter.py` (`_render_fair_heatmap`), producing visual and quantitative discrepancies between the per-tower annexes and Volume 1.

---

#### [HIGH-03] Repeated Synchronous Disk I/O & Uncached Parsing of `locales.json` Inside Narrative Synthesizer
* **Location:** `assessment_engine/adapters/compilers/payload_to_ast.py` — `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs()`
* **Exact Code Citation:**
  ```python
  from assessment_engine.infrastructure.runtime_paths import ROOT
  loc_file = ROOT / "engine_config" / "locales.json"
  loc_data = {}
  if loc_file.exists():
      try:
          loc_data = json.loads(loc_file.read_text(encoding="utf-8-sig"))
      except Exception:
          loc_data = {}
  ```
* **Root Cause:** Even though `load_locales_catalog` is imported at the top of `payload_to_ast.py`, `ExecutiveNarrativeSynthesizer` bypasses the infrastructure layer, imports `ROOT` inline, and reads/parses `engine_config/locales.json` from disk on every single invocation, silencing JSON syntax errors via `except Exception: loc_data = {}`.
* **Concrete Failure Scenario:** In a multi-tenant cloud worker compiling 10+ towers concurrently, redundant disk I/O degrades throughput, and if `locales.json` is locked or malformed, the synthesizer silently produces empty `operational_mission`, `dilemma_anchor`, and `posture_modernization_focus` strings without raising a build error.

---

### 2.3 MEDIUM & LOW SEVERITY FINDINGS

---

#### [MED-01] Silent Exception Swallowing in `load_json` Masking Corrupted Tenant Blueprints
* **Location:** `assessment_engine/application/build_global_report_payload.py` — `load_json()` & `_aggregate_tower_blueprints()`
* **Exact Code Citation:**
  ```python
  try:
      return json.loads(path.read_text(encoding="utf-8-sig"))
  except Exception:
      return None
  ```
* **Root Cause:** `load_json` silences all `JSONDecodeError` and `OSError` exceptions without logging a warning or error. In `_aggregate_tower_blueprints()`, `if not data: continue` silently skips the corrupted tower blueprint.
* **Concrete Failure Scenario:** If Tower `T3` (Cybersecurity) for a bank has a trailing comma in its JSON blueprint, `_aggregate_tower_blueprints` silently drops Cybersecurity from Volume 1. The client receives a board report claiming 9 towers were assessed with zero indication that Cybersecurity was omitted due to a parse error.

---

#### [MED-02] Hardcoded English Fallback `"Client"` / `"CLIENT"` Instead of Localized Token or Strict Validation
* **Location:** `payload_to_ast.py` (`clean_client_name`) and `tomo_asis_ast_compiler.py` (`compile`)
* **Root Cause:** Both modules fallback to English `"Client"` / `"CLIENT"` if the client name is missing from metadata, rather than raising a `MissingTenantMetadataError` or resolving a localized fallback via `t("default_client_name", locale=doc_lang)`.

---

#### [MED-03] Thread-Safety & Global State Contention in Chart Generation (Chapter 2 Radar Chart)
* **Location:** `assessment_engine/adapters/compilers/tomo_asis_ast_compiler.py` — `_build_chapter_2_maturity_radiography()`
* **Root Cause:** Passing `output_docx_path` into `_build_chapter_2_maturity_radiography` to write temporary chart PNGs to the same directory (often using static filenames like `radar_chart.png` or global `matplotlib.pyplot` state `plt.figure()`) creates race conditions when two tenants compile reports concurrently in the same worker process.

---

## 3. The Definitive Elimination Plan

Below are the production-grade Python architectural remediations adhering strictly to **100% Technical English**, **Zero Hardcoding**, **Dynamic N-Domain Polymorphism**, and **Pure SSOT**.

### 3.1 Eradicating [CRIT-01] & [CRIT-03]: Dynamic Actuarial Loss Magnitude Calibration & Vertical-Agnostic Localization

Replace hardcoded `1,000`–`250,000` brackets and the hardcoded `"Enterprise & Industrial Technology"` string with a deterministic logarithmic scale anchored to the tenant's actual financial telemetry (`annual_revenue` or `hourly_burn_rate`), or currency-aware base units when telemetry is absent.

```python
# File: assessment_engine/domain/actuarial_scale_calibrator.py
"""Dynamic Loss Magnitude (LM) scale calibrator for universal multi-tenant currencies and revenue scales."""
from __future__ import annotations

import math
from decimal import Decimal
from typing import Dict, Tuple

from assessment_engine.infrastructure.localization import format_number, t

# Zero-decimal and high-denomination currency baseline multipliers relative to USD/EUR
CURRENCY_BASE_PARITY: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.0,
    "GBP": 0.8,
    "CHF": 0.9,
    "SEK": 10.5,
    "NOK": 10.5,
    "JPY": 150.0,
    "KRW": 1350.0,
}


def compute_dynamic_lm_brackets(
    currency: str,
    locale: str,
    annual_revenue: float | None = None,
    hourly_burn_rate: float | None = None,
    is_critical_domain: bool = True,
) -> Dict[int, str]:
    """Computes 5-tier Loss Magnitude (LM 1..5) monetary brackets dynamically.

    Anchors brackets to the tenant's actual financial scale (hourly_burn_rate or annual_revenue).
    Falls back to currency-parity-adjusted enterprise baselines if telemetry is not provided,
    preventing JPY/SEK scale distortion.
    """
    clean_currency = currency.strip().upper()
    parity_factor = CURRENCY_BASE_PARITY.get(clean_currency, 1.0)

    # Determine base unit (LM1 upper threshold) from live SSOT telemetry
    if hourly_burn_rate and hourly_burn_rate > 0:
        # Anchor LM1 to ~2 hours of operational burn
        base_threshold = float(hourly_burn_rate) * 2.0
    elif annual_revenue and annual_revenue > 0:
        # Anchor LM1 to 0.001% (1 basis point / 100) of annual revenue
        base_threshold = float(annual_revenue) * 0.00001
    else:
        base_threshold = 1000.0 * parity_factor

    # Round base threshold to clean significant figure
    exponent = math.floor(math.log10(max(base_threshold, 1.0)))
    clean_base = round(base_threshold / (10**exponent)) * (10**exponent)

    if is_critical_domain:
        multipliers = (1.0, 10.0, 50.0, 250.0)
    else:
        multipliers = (1.0, 5.0, 25.0, 100.0)

    t1, t2, t3, t4 = [clean_base * m for m in multipliers]

    fmt = lambda val: format_number(val, locale=locale, decimals=0)
    return {
        1: f"< {fmt(t1)} {clean_currency}",
        2: f"{fmt(t1)} - {fmt(t2)} {clean_currency}",
        3: f"{fmt(t2)} - {fmt(t3)} {clean_currency}",
        4: f"{fmt(t3)} - {fmt(t4)} {clean_currency}",
        5: f"> {fmt(t4)} {clean_currency}",
    }
```

And inside `asis_fair_chapter.py`, replace the hardcoded fallback:
```python
# Inside _render_fair_heatmap() in asis_fair_chapter.py:
industry_name = (
    str(ctx.get("industry") or "").strip()
    or t("default_enterprise_vertical", locale=doc_lang)
)
```

---

### 3.2 Eradicating [CRIT-02] & [HIGH-03]: Polymorphic N-Domain Resolution & Cached Localization Catalog

Refactor `ExecutiveNarrativeSynthesizer` in `payload_to_ast.py` and `_aggregate_tower_blueprints` in `build_global_report_payload.py` to support arbitrary domain identifiers (`SEC-01`, `CLOUD-02`, `T1..T15`) and eliminate inline disk I/O.

```python
# File: assessment_engine/adapters/compilers/payload_to_ast.py (Refactored Excerpt)

def resolve_domain_semantics_key(tower_id: str, available_keys: set[str]) -> str:
    """Resolves a tower identifier to its localization semantics key without rigid T1..T10 truncation."""
    raw_id = str(tower_id or "").strip().upper()
    if not raw_id:
        return "DEFAULT"

    # 1. Exact match (supports custom keys like "SEC-01", "CLOUD", "T12" if defined in catalog)
    if raw_id in available_keys:
        return raw_id

    # 2. Canonical T<N> match only if the prefix is explicitly 'T' or 'TOWER'
    canonical_match = re.match(r"^(?:T|TOWER[-_\s]*)(\d+)$", raw_id)
    if canonical_match:
        candidate = f"T{int(canonical_match.group(1))}"
        if candidate in available_keys:
            return candidate

    return "DEFAULT"
```

And in `ExecutiveNarrativeSynthesizer.synthesize_chapter_one_paragraphs()`:
```python
        # Load narrative templates via cached infrastructure catalog (Zero inline disk I/O)
        loc_data = load_locales_catalog()
        loc_branch = loc_data.get(self._locale_code, {})
        tower_semantics_map: Dict[str, Any] = loc_branch.get("tower_domain_semantics", {})

        canonical_key = resolve_domain_semantics_key(
            tower_id=tower_id,
            available_keys=set(tower_semantics_map.keys()),
        )
        tower_semantics = tower_semantics_map.get(
            canonical_key, tower_semantics_map.get("DEFAULT", {})
        )
```

---

### 3.3 Eradicating [CRIT-02], [HIGH-01], & [MED-01] in `build_global_report_payload.py`

Eliminate the Spanish variable `pilar`, implement natural alphanumeric domain sorting (`T1, T2, ..., T10, SEC-01`), and replace silent `except Exception: return None` with structured diagnostic logging.

```python
# File: assessment_engine/application/build_global_report_payload.py (Refactored Excerpt)

def _natural_tower_sort_key(blueprint_path: Path) -> tuple[int, int | str, str]:
    """Deterministic natural sort key supporting both canonical (T1..TN) and custom (SEC-01) tower IDs."""
    folder_name = blueprint_path.parent.name.strip().upper()
    canonical_match = re.match(r"^T(\d+)$", folder_name)
    if canonical_match:
        return (0, int(canonical_match.group(1)), folder_name)

    # Custom alphanumeric domain identifiers sort deterministically after canonical T-domains
    num_match = re.search(r"(\d+)", folder_name)
    if num_match:
        prefix = folder_name[: num_match.start()]
        return (1, int(num_match.group(1)), prefix)
    return (2, 0, folder_name)


def load_json(path: Path, *, strict: bool = False) -> dict[str, Any] | None:
    """Safely loads and parses a JSON file with explicit diagnostic telemetry on failure."""
    if not path.exists():
        logger.debug("JSON file does not exist at path: %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        logger.error("Failed to parse JSON payload at %s: %s", path, exc)
        if strict:
            raise ValueError(f"Corrupted SSOT JSON blueprint at {path}") from exc
        return None
```

And inside `_aggregate_tower_blueprints`:
```python
    for bp in sorted(blueprint_files, key=_natural_tower_sort_key):
        data = load_json(bp, strict=True)
        if not data:
            continue
        ...
        r_idx = 1
        p_idx = 1
        for pillar in data.get("pillars_analysis", []):
            for hc in pillar.get("health_check_asis", []):
                ...
            for proj in pillar.get("projects_todo", []):
                ...
```

---

### 3.4 Eradicating [CRIT-02] & [HIGH-01] in `Volume1AsisASTCompiler` (`volume1_asis_ast_compiler.py`)

1. Rename `tomo_asis_ast_compiler.py` $\rightarrow$ `volume1_asis_ast_compiler.py` (preserving a deprecated re-export shim only if required by external callers during migration) and migrate localization keys from `tomo_cover_*` $\rightarrow$ `vol1_cover_*`.
2. Replace the static `CANONICAL_DOMAIN_SCENARIO_BASELINE` dictionary lookup with a dynamic resolver that inspects the actual `tower_payloads` scenarios first, using the baseline dictionary strictly as an optional heuristic for standard `T1..T10` IDs.

```python
    @classmethod
    def resolve_expected_scenario_count(
        cls, tower_id: str, tower_payload: Dict[str, Any]
    ) -> int:
        """Dynamically resolves risk scenario count from live SSOT payload without fixed 10-tower assumptions."""
        live_scenarios = (
            tower_payload.get("risk_scenarios")
            or tower_payload.get("fair_scenarios")
            or tower_payload.get("bow_tie_scenarios")
        )
        if isinstance(live_scenarios, list) and len(live_scenarios) > 0:
            return len(live_scenarios)
        return cls.CANONICAL_DOMAIN_SCENARIO_BASELINE.get(tower_id.upper(), 3)
```

---

### 3.5 Eradicating [MED-03]: Thread-Safe Isolated Chart Rendering

Ensure all `matplotlib` figures generated during Chapter 2 Maturity Radiography use the object-oriented `Figure` canvas API (`from matplotlib.figure import Figure`) rather than the global `pyplot` state machine (`plt.gcf()`), and write output artifacts to tenant-scoped temporary paths (`f"radar_{slugify(client_name)}_{uuid4().hex[:8]}.png"`).

---

## 4. Universal Multi-Tenant Certification Checklist

Before promoting the AS-IS generation pipeline to production, the CI/CD Quality Gatekeeper must execute and pass the following 6 automated adversarial verification suites:

| Gate ID | Verification Test Case | Synthetic Tenant Profile | Acceptance Criteria (Zero-Tolerance Invariant) |
| :--- | :--- | :--- | :--- |
| **GATE-01** | **Non-Decimal High-Denomination Currency Stress Test** | **Tokyo Megabank** (`JPY`, Revenue: `¥2,500,000,000,000`, `rate_mult` omitted) | Heatmap LM1..LM5 brackets scale dynamically to Millions/Billions of `¥`. Zero occurrences of `< 1,000 JPY` or `> 250,000 JPY`. |
| **GATE-02** | **Non-Manufacturing Healthcare Vertical Test** | **Stockholm Regional Hospital** (`SEK`, Locale: `en-US` & `es-ES`, `industry` key omitted from `ctx`) | Zero occurrences of `"Enterprise & Industrial Technology"`, `"weighbridge"`, `"bagging"`, `"plant"`, `"kiln"`, or `"Molins"` anywhere in AST or DOCX XML. |
| **GATE-03** | **Polymorphic 3-Domain Custom ID Stress Test** | **Chicago Retail Giant** (3 Towers: `SEC-01`, `CLOUD-02`, `DATA-03`) | Pipeline compiles Volume 1 and 3 Annexes with zero `KeyError`/`IndexError`, zero phantom `T4..T10` rows, and accurate domain semantics for `SEC-01` (not coerced to `T1`). |
| **GATE-04** | **Expanded 12-Domain Infrastructure Stress Test** | **London Public Transit** (12 Towers: `T1` through `T12`) | `T11` and `T12` sort naturally after `T10` (not before `T2`), retain distinct domain semantics in Chapter 1, and appear in the Chapter 2 Radar Chart with 12 vertices. |
| **GATE-05** | **100% Technical English Lexical AST Audit** | Static AST & Token Scanner across `assessment_engine/**/*.py` | Zero matches for regex `\b(pilar|pilares|tomo|tarifas_hora|tecnico_medio|hallazgos|riesgos)\b` in Python identifiers, parameters, comments, or log strings. |
| **GATE-06** | **Unresolved Token & Split-Brain Integrity Gate** | All 6 Target Locales (`en`, `es`, `pt`, `fr`, `de`, `ja`) | Zero matches for `\{[a-zA-Z0-9_]+\}` in compiled `.docx` paragraphs/tables; 100% mathematical reconciliation between Per-Tower ALE/P90 VaR and Volume 1 Chapter 3 Register. |