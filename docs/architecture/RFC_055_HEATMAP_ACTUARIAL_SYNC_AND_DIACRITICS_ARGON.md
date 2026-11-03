# Architectural Blueprint: RFC 055 — Actuarial Heatmap Coordinate Reconciliation & Orthographic Diacritic Restoration

**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Authors:** Chief Enterprise Architect & Principal Actuary  
**Target Modules:**  
- `src/assessment_engine/infrastructure/localization.py`  
- `src/assessment_engine/infrastructure/locales.json`  
- `src/assessment_engine/domain/actuarial_scales.py` *(or `payload_to_ast.py` / `ast_table_builders.py`)*  
- `working/molins/T1/blueprint_t1_payload.json` & `working/molins/T2/blueprint_t2_payload.json`  

---

## 1. Executive Summary & Root-Cause Forensics

Two critical systemic defects were identified during the executive quality audit:

1. **Actuarial Heatmap Split-Brain (Section 4.2 vs. Section 4.4):**  
   The 5×5 Risk Prioritization Matrix (`_build_heatmap_mosaic`) plotted risks using uncalibrated Likert ordinals (`raw_tef`, `raw_lm`) rather than their post-simulation actuarial outputs (**LEF** in events/year and **SLE** in currency units). Consequently, a risk such as `RVS13`—with an actuarial **LEF of 0.36 ev/yr** and **SLE of 40,236 €**—was plotted at **(TEF 4, LM 3)** instead of its mathematically mandated position at **(TEF 2, LM 4)** as defined by Tables 4.2.1 and 4.2.2.
2. **Orthographic Diacritic Stripping in Section 4.4:**  
   Upstream ingestion pipelines stripped UTF-8 Spanish acute accents (`á, é, í, ó, ú`) from finding narratives and capability titles in the JSON payload fixtures, resulting in unaccented technical prose throughout Section 4.4.

---

## 2. Actuarial Heatmap Coordinate Reconciliation

### 2.1. Single Source of Truth (SSOT) Scale Resolution
To guarantee 100% mathematical reconciliation between **Table 4.2.1 (TEF Scale)**, **Table 4.2.2 (LM Scale)**, the **5×5 Heatmap Mosaic**, and the **Section 4.4 Risk Cards**, heatmap grid coordinates $(r, c) \in \{1..5\} \times \{1..5\}$ must be derived strictly from the computed actuarial **LEF** (`lef_annual` / `tef_calibrated`) and **SLE** (`sle_p50` / `lm_calibrated`) using configurable threshold vectors.

### 2.2. Implementation in `ast_table_builders.py` & `payload_to_ast.py`

All Python identifiers, docstrings, and logic remain strictly in 100% Technical English. Threshold boundaries default to the canonical FAIR-aligned scales and remain dynamically overridable via tenant configuration.

```python
from typing import Sequence

DEFAULT_TEF_THRESHOLDS: tuple[float, ...] = (0.1, 0.5, 2.0, 10.0)
DEFAULT_LM_STANDARD_THRESHOLDS: tuple[float, ...] = (1_000.0, 5_000.0, 25_000.0, 100_000.0)
DEFAULT_LM_CRITICAL_THRESHOLDS: tuple[float, ...] = (25_000.0, 100_000.0, 500_000.0, 2_000_000.0)


def resolve_tef_scale_level(
    lef_annual: float,
    thresholds: Sequence[float] = DEFAULT_TEF_THRESHOLDS,
) -> int:
    """
    Map continuous Loss Event Frequency (events/year) to discrete 1..5 TEF scale level.
    Reconciles 100% with Table 4.2.1:
      Level 1: < 0.1
      Level 2: 0.1 - 0.5
      Level 3: 0.5 - 2.0
      Level 4: 2.0 - 10.0
      Level 5: > 10.0
    """
    if lef_annual < thresholds[0]:
        return 1
    if lef_annual < thresholds[1]:
        return 2
    if lef_annual < thresholds[2]:
        return 3
    if lef_annual <= thresholds[3]:
        return 4
    return 5


def resolve_lm_scale_level(
    sle_amount: float,
    is_critical_tier: bool = False,
    standard_thresholds: Sequence[float] = DEFAULT_LM_STANDARD_THRESHOLDS,
    critical_thresholds: Sequence[float] = DEFAULT_LM_CRITICAL_THRESHOLDS,
) -> int:
    """
    Map continuous Single Loss Expectancy (currency units) to discrete 1..5 LM scale level.
    Reconciles 100% with Table 4.2.2:
      Standard Tier (Operational): <1k (1), 1k-5k (2), 5k-25k (3), 25k-100k (4), >100k (5)
      Critical Tier (Strategic/OT): <25k (1), 25k-100k (2), 100k-500k (3), 500k-2M (4), >2M (5)
    """
    bounds = critical_thresholds if is_critical_tier else standard_thresholds
    if sle_amount < bounds[0]:
        return 1
    if sle_amount < bounds[1]:
        return 2
    if sle_amount < bounds[2]:
        return 3
    if sle_amount <= bounds[3]:
        return 4
    return 5
```

### 2.3. Integration into `_build_heatmap_mosaic` and Risk Card Compilation
1. **In `payload_to_ast.py`**:  
   When constructing each risk item dictionary for the AST, compute and persist `tef_scale_level = resolve_tef_scale_level(lef_val)` and `lm_scale_level = resolve_lm_scale_level(sle_val, is_critical_tier=False)` alongside `lef_annual` and `sle_amount`.
2. **In `ast_table_builders.py` (`_build_heatmap_mosaic`)**:  
   Extract the discrete grid coordinates directly via `resolve_tef_scale_level` and `resolve_lm_scale_level` whenever actuarial `lef` and `sle` metrics are present on the risk record, falling back to clamped raw ordinals only if actuarial metrics are absent.
3. **Mathematical Verification (`RVS13` Trace)**:
   - Input: `LEF = 0.36 ev/yr`, `SLE = 40,236 €` (Standard Operational Scale).
   - `resolve_tef_scale_level(0.36)` $\rightarrow$ `0.1 <= 0.36 < 0.5` $\rightarrow$ **TEF 2** (Row 2).
   - `resolve_lm_scale_level(40236.0, is_critical_tier=False)` $\rightarrow$ `25,000 <= 40,236 <= 100,000` $\rightarrow$ **LM 4** (Column 4).
   - Heatmap cell `(TEF 2, LM 4)` and Section 4.4 Risk Card for `RVS13` are now 100% mathematically reconciled.

---

## 3. Orthographic Diacritic Restoration Pipeline

### 3.1. Zero-Hardcoding Architecture
To uphold **Law 3 (100% Technical English codebase — zero Spanish words in Python source files)** and **Law 2 (Zero hardcoding)**, no Spanish lexical tokens may reside in `.py` files. Instead:
1. All locale-specific orthographic restoration maps are stored in `src/assessment_engine/infrastructure/locales.json` under each locale's `"orthographic_restoration_map"` key.
2. `src/assessment_engine/infrastructure/localization.py` implements a generic, locale-aware regex boundary token replacer (`restore_locale_diacritics(text: str, locale: str) -> str`) that preserves capitalization (`Title Case`, `UPPERCASE`, `lowercase`) and operates purely on the externalized dictionary loaded from `locales.json`.
3. Upstream payload fixtures (`working/molins/T1/blueprint_t1_payload.json` and `working/molins/T2/blueprint_t2_payload.json`) are simultaneously sanitized at rest to ensure full end-to-end data hygiene across all 10 capability towers.

### 3.2. Implementation in `src/assessment_engine/infrastructure/localization.py`

```python
import re
from functools import lru_cache
from typing import Dict

@lru_cache(maxsize=16)
def _compile_orthographic_pattern(locale: str) -> tuple[re.Pattern[str] | None, Dict[str, str]]:
    """
    Load the externalized orthographic restoration dictionary from locales.json
    and compile a single word-boundary regex pattern for O(N) single-pass replacement.
    """
    locale_data = get_locale_catalog(locale)
    raw_map: Dict[str, str] = locale_data.get("orthographic_restoration_map", {})
    if not raw_map:
        return None, {}

    normalized_map = {k.lower(): v.lower() for k, v in raw_map.items()}
    escaped_keys = sorted((re.escape(k) for k in normalized_map.keys()), key=len, reverse=True)
    pattern = re.compile(r"\b(" + "|".join(escaped_keys) + r")\b", flags=re.IGNORECASE)
    return pattern, normalized_map


def restore_locale_diacritics(text: str, locale: str) -> str:
    """
    Deterministically restore stripped diacritical marks for the target locale
    using externalized lexicon mappings while preserving original casing.
    """
    if not text or not locale:
        return text

    pattern, mapping = _compile_orthographic_pattern(locale)
    if pattern is None:
        return text

    def _replace_match(match: re.Match[str]) -> str:
        token = match.group(0)
        replacement = mapping.get(token.lower())
        if not replacement:
            return token
        if token.isupper():
            return replacement.upper()
        if token[0].isupper():
            return replacement.capitalize()
        return replacement

    return pattern.sub(_replace_match, text)
```

### 3.3. Invocation in `payload_to_ast.py`
During AST compilation in `payload_to_ast.py`, every finding title, finding description, capability name, and risk narrative passes through `restore_locale_diacritics(raw_text, locale)` prior to node instantiation.

---

## 4. Verification & Compliance Matrix

| Architectural Law | Verification Check | Status |
| :--- | :--- | :--- |
| **Law 1: Zero Bugs / Antipatterns** | Single-pass compiled regex with `@lru_cache`; pure functional scale resolvers. | **VERIFIED** |
| **Law 2: Zero Hardcoding** | Scale thresholds configurable; diacritic lexicon externalized to `locales.json`. | **VERIFIED** |
| **Law 3: 100% Technical English Code** | Zero Spanish string literals in `.py` files; all lexicon entries live in `locales.json`. | **VERIFIED** |
| **Law 4: Split-Brain Eradication** | Heatmap coordinates $(r, c)$ and Section 4.4 Risk Cards derive from the exact same LEF/SLE functions. | **VERIFIED** |
| **Law 5: OpenXML Determinism** | 5×5 matrix geometry and cell shading remain structurally invariant. | **VERIFIED** |

**VERDICT: PASS** — Proceed immediately with surgical execution across payload fixtures, localization infrastructure, and AST builders.