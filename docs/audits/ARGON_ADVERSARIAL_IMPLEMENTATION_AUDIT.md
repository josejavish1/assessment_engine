---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

### Executive Audit Summary — `gemini-4-argon`

**Target:** `src/assessment_engine/adapters/compilers/in_memory_asis_compiler.py`
**Audit Status:** **PARTIAL PAYLOAD / ACTIONABLE DEFECTS IDENTIFIED IN VISIBLE HUNK**

*(Note: Both the code snippet and the `git diff` provided in the prompt are truncated at line 107 inside `_build_evidence_footnote`. Below is the uncompromising line-by-line audit of the visible code, followed by architectural invariants that must be enforced on the truncated remainder of the +429 line diff).*

---

### 1. Prioritized Defects in the Visible Diff (Lines 1–107)

#### 🔴 DEFECT-01 (High — State Mutation & Cache Poisoning Hazard): Mutable `dict` Returned from `@lru_cache(maxsize=1)`
* **Location:**
  * `_load_cmmi_progression_matrix()` (Lines 40–51)
  * `_load_sota_industry_benchmarks()` (Lines 54–65)
  * `_load_cross_domain_nexus()` (Lines 78–89)
* **Law Violated:** Law 3 (Algorithmic & Numerical Integrity) & Thread/Tenant Isolation.
* **Forensic Analysis:**
  `functools.lru_cache` caches the exact object reference returned by the function. Returning a raw, mutable `dict[str, Any]` means that if any downstream consumer mutates a nested key (e.g., `.pop()`, `.setdefault()`, or in-place tenant interpolation) during one compilation run, **the cached singleton is permanently mutated in-memory for all subsequent tenant compilations**. Notice that `MappingProxyType` was imported at Line 14 (`from types import MappingProxyType`), yet it was never applied to these cached loaders.
* **Surgical Fix:**
  Wrap the top-level dictionary in `MappingProxyType` (or recursively freeze it) and change the return type annotation to `Mapping[str, Any]`.

```python
@lru_cache(maxsize=1)
def _load_cmmi_progression_matrix() -> Mapping[str, Any]:
    """Cached loader for deterministic CMMI progression milestones."""
    repo_root = _find_repo_root()
    matrix_path = repo_root / "engine_config" / "policies" / "cmmi_progression_matrix.json"
    if matrix_path.exists():
        try:
            with matrix_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return MappingProxyType(data)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed reading cmmi_progression_matrix at %s: %s", matrix_path, exc)
    return MappingProxyType({})
```
*(Apply the identical pattern to `_load_sota_industry_benchmarks` and `_load_cross_domain_nexus`).*

---

#### 🟠 DEFECT-02 (Medium — Silent Failure / Observability Blindness & Over-Broad Exception Catching)
* **Location:** Lines 49–50, 63–64, 87–88 (`except Exception as exc: logger.debug(...)`)
* **Law Violated:** Law 3 (Algorithmic & Numerical Integrity).
* **Forensic Analysis:**
  1. Catching bare `Exception` masks programming bugs (`TypeError`, `NameError` if `_find_repo_root()` fails or is undefined in scope at call time).
  2. Logging a corrupted JSON configuration file (`json.JSONDecodeError`) at `logger.debug` level means that a syntax error introduced into `cmmi_progression_matrix.json`, `sota_industry_benchmarks.json`, or `cross_domain_nexus_map.json` in production will silently degrade the output document (returning `{}` and omitting entire benchmark/nexus sections) with zero visibility in standard `INFO`/`WARNING` production logs.
  3. Furthermore, if the file is temporarily missing or unreadable during startup, `@lru_cache(maxsize=1)` will permanently cache the empty `{}` result for the lifetime of the worker process.
* **Surgical Fix:**
  Catch `(OSError, json.JSONDecodeError)` specifically, and log at `logger.warning` (or `logger.error`) so malformed configuration files are immediately surfaced in telemetry.

---

#### 🟠 DEFECT-03 (Medium — Locale Normalization & Type-Safety Hazard in JSON Lookups)
* **Location:**
  * `_build_sota_benchmark_paragraph()` (Lines 68–75)
  * `_build_cross_domain_nexus()` (Lines 92–99)
* **Law Violated:** Law 2 (Universal Tenant Scalability across any target locale) & Law 3 (Algorithmic Integrity).
* **Forensic Analysis:**
  1. **Regional Locale Tag Mismatch:** If `doc_lang` is passed as a regional BCP-47 tag (e.g., `"es-MX"`, `"pt-BR"`, `"en-GB"`, `"fr-CA"`, `"de-CH"`), `p_entry.get(doc_lang)` will miss the base `"es"`, `"pt"`, `"fr"`, or `"de"` key in the JSON catalog and immediately fall back to `"en"`, resulting in mixed-language documents (English paragraphs injected into Spanish/Portuguese/French/German reports).
  2. **Unvalidated Type Assumptions:** `catalog.get("pillars", {})` assumes `"pillars"` maps to a `dict`. If `"pillars"` is `None` in JSON, `None.get(...)` raises an unhandled `AttributeError`.
* **Surgical Fix:**
  Normalize the locale code (extracting base language fallback before falling back to `"en"`) and guard dictionary types:

```python
def _resolve_localized_catalog_entry(
    catalog: Mapping[str, Any], canonical_pillar_id: str, doc_lang: str
) -> str:
    """Safely resolves a localized narrative string from a pillar catalog with BCP-47 fallback."""
    pillars = catalog.get("pillars")
    if not isinstance(pillars, Mapping):
        return ""
    p_entry = pillars.get(canonical_pillar_id)
    if not isinstance(p_entry, Mapping):
        return ""

    normalized_lang = (doc_lang or "en").strip().lower()
    base_lang = normalized_lang.split("-")[0].split("_")[0]

    text = (
        p_entry.get(doc_lang)
        or p_entry.get(normalized_lang)
        or p_entry.get(base_lang)
        or p_entry.get("en")
        or ""
    )
    return str(text).strip()


def _build_sota_benchmark_paragraph(canonical_pillar_id: str, doc_lang: str) -> str:
    """Retrieves and formats the 4th source SOTA empirical benchmark narrative for the pillar."""
    return _resolve_localized_catalog_entry(
        _load_sota_industry_benchmarks(), canonical_pillar_id, doc_lang
    )


def _build_cross_domain_nexus(canonical_pillar_id: str, doc_lang: str) -> str:
    """Retrieves and formats the cross-domain blast radius narrative for the pillar."""
    return _resolve_localized_catalog_entry(
        _load_cross_domain_nexus(), canonical_pillar_id, doc_lang
    )
```

---

#### 🟡 DEFECT-04 (Low — Redundant Local Import & Variable Shadowing)
* **Location:** Line 106 inside `_build_evidence_footnote`:
  ```python
  from assessment_engine.infrastructure.localization import t
  ```
* **Law Violated:** Law 3 (No unintended variable shadowing) & PEP-8 hygiene.
* **Forensic Analysis:**
  `t` is already imported at the module top-level (Line 30). Re-importing `t` inside `_build_evidence_footnote` shadows the module-level symbol locally and adds unnecessary import lock overhead on every invocation.
* **Surgical Fix:**
  Delete `from assessment_engine.infrastructure.localization import t` at Line 106.

---

### 2. Checklist for the Truncated Remainder of the Diff (Lines 108–429)

Because the diff cut off at Line 107 (out of `+429` added lines), please paste the remaining hunks (`lines 105–450`) so I can complete the line-by-line verification of:
1. **`_build_evidence_footnote` implementation:** Checking for hardcoded Spanish/English labels, regex patterns, or magic client strings.
2. **Paragraph Chunking & Sentence Splitting Logic:** Checking for regexes that split on `.` naively (which breaks on decimals like `$2.5M` or abbreviations in German/English/Spanish) or fail on 0-finding / 1-sentence edge cases.
3. **Score Enrouting & Threshold Boundaries:** Checking usage of `LOW_MATURITY_CALIBRATION_THRESHOLD` (`2.20`), `DIVERGENCE_RATIONALE_THRESHOLD` (`0.50`), and `DEFAULT_PILLAR_ASSESSMENT_SCORE` (`2.50`) for floating-point boundary issues or `None` score crashes.

Paste the remaining lines of `in_memory_asis_compiler.py` whenever ready, and I will immediately execute the remainder of the audit.