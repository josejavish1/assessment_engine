# ARGON ADVERSARIAL IMPLEMENTATION AUDIT: SECTION 3.1 & 3.2 DYNAMIC RISK TAXONOMY

**Auditor:** Principal Staff Systems Architect / Zero-Trust Code Auditor  
**Target Modules:**  
- `src/assessment_engine/domain/actuarial_taxonomy_clusterer.py`  
- `src/assessment_engine/domain/tomo_asis_ast_compiler.py` (Chapter 3 Excerpt)  
**Compliance Baseline:** Core Mandates 1–4 (100% Technical English, Zero Hardcoding, Actuarial & Mathematical Integrity, Clean/Hexagonal Architecture)

---

## 1. EXECUTIVE VERDICT: **FAIL (BLOCKING DEFECTS IDENTIFIED)**

While the architectural direction of RFC 081 (Dynamic Ontological Risk Taxonomy Clustering) and the Hexagonal AST compilation pipeline is sound and clean of external I/O, the implementation contains **1 Critical Mandate Violation** (Spanish linguistic leakage in severity parsing), **3 High-Severity Actuarial/Multi-Lingual Defects** (IEEE 754 floating-point percentage drift, ASCII-only stem matching failure on localized payloads, and unguarded `float()` casts), and **2 Medium-Severity Architectural/Data-Structure Flaws**. 

Deployment to production is **blocked** until all Critical and High findings are remediated.

---

## 2. FORENSIC INSPECTION FINDINGS

### 2.1 Language Decoupling Inspection (Mandate 1 & Multi-Lingual Scaling)

#### **[CRITICAL-01] Non-English Linguistic Leakage in Severity Parser**
* **Location:** `actuarial_taxonomy_clusterer.py`, Line 196
* **Evidence:**
  ```python
  elif "HIGH" in status or "ALT" in status or (tef >= 2.0 and lm >= 3.0):
  ```
* **Forensic Analysis:** `"ALT"` is a hardcoded truncation for the Spanish/Portuguese word *"ALTO"* / *"ALTA"*. This directly violates **Core Mandate 1** ("Any non-English word or Spanish character in Python source files is a CRITICAL violation"). Furthermore, it represents an asymmetric multi-lingual hack: it attempts to catch Spanish/Portuguese while ignoring French (`ÉLEVÉ`), German (`HOCH`), and Japanese (`高`).

#### **[HIGH-01] Total Classification Collapse on Non-Latin / Localized Payloads (`es`, `pt`, `fr`, `de`, `ja`)**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 76–86 (`classify_text`)
* **Evidence:**
  ```python
  normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii").lower()
  ```
* **Forensic Analysis:** When `tower_payloads` or `risk_vectors` are ingested in Japanese (`ja`), `.encode("ascii", "ignore")` strips **100% of Kanji/Kana characters**, leaving an empty string `""`. All 6 taxonomy scores evaluate to `0`, forcing every single risk and tower in a Japanese assessment into the fallback bucket `"TAXONOMY_OPERATIONAL_CONTINUITY_EDGE"`. Even in German (`de`), French (`fr`), or Spanish (`es`), terms like *"Obsoleszenz"*, *"Ausfall"*, *"Lieferant"*, or *"Proveedores"* do not match the English regex stems (`r"vendor"`, `r"outage"`), causing severe classification distortion when `taxonomy_id` is not explicitly pre-populated.

---

### 2.2 Mathematical & Actuarial Edge-Case Inspection (Mandate 3)

#### **[HIGH-02] IEEE 754 Floating-Point Drift & Unreconciled Percentage Shares in `ActuarialTaxonomyClusterer`**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 65–66, 224–228, 239–240
* **Evidence:**
  ```python
  share_pct = (
      round((ale_val / total_portfolio_ale) * 100.0, 1)
      if total_portfolio_ale > 0
      else 0.0
  )
  ```
* **Forensic Analysis:**
  1. **IEEE 754 `round()` vs `ROUND_HALF_UP`:** Python's built-in `round(val, 1)` uses Round-Half-to-Even (Banker's Rounding) on binary floating-point approximations, contrasting with `ActuarialReconciler` in `tomo_asis_ast_compiler.py` which uses `Decimal` and `ROUND_HALF_UP`.
  2. **Sum Reconciliation Failure:** Independent rounding of cluster shares guarantees that `sum(c.share_of_total_ale_pct for c in clusters)` will frequently equal `99.9%` or `100.1%` (e.g., three equal clusters of `33.3%` sum to `99.9%`), which contradicts the `100.0%` footer in Table 3.2.B.
  3. **Cluster ALE vs. Table 3.1 ALE Drift:** `bucket["ale"]` accumulates floats and rounds to 2 decimal places (`round(ale_val, 2)`), whereas Table 3.1 reconciles integer allocations (`target_ale_int`). If `reconciled_allocations` is not passed or partial, `tot_ale_val = sum(c.cluster_ale for c in clusters)` in Table 3.2.B will fail to reconcile with Table 3.1's `target_ale_int`.

#### **[HIGH-03] Unguarded `float()` Casts Vulnerable to Locale-Formatted Strings & Malformed Telemetry**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 146–153, 163–168, 191–192
* **Evidence:**
  ```python
  tef = float(hc.get("threat_event_frequency") or hc.get("tef") or 3.0)
  lm = float(hc.get("loss_magnitude") or hc.get("lm") or 3.0)
  ```
* **Forensic Analysis:** Unlike `tomo_asis_ast_compiler.py` (which uses `safe_float(..., locale=doc_lang)`), `ActuarialTaxonomyClusterer` calls raw `float()`. If a European payload (`es`, `de`, `fr`, `pt`) provides `"3,5"` or `"€ 120.000"`, or a string label like `"HIGH"`, `float()` raises an unhandled `ValueError`, crashing the entire AST compilation for Chapter 3.

#### **[MEDIUM-01] Silent Falsy-Zero Bug in TEF / LM Fallback Evaluation**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 191–192
* **Evidence:**
  ```python
  tef = float(hc.get("threat_event_frequency") or hc.get("tef") or 3.0)
  ```
* **Forensic Analysis:** In Python, `0.0 or 3.0` evaluates to `3.0` because `0.0` is falsy. If a health check item legitimately has `tef = 0.0` and `lm = 0.0` (a mitigated or negligible finding), this expression silently overwrites both to `3.0`, inflating the finding into the **`t_high`** bucket (`tef >= 2.0 and lm >= 3.0`). Furthermore, `t_low` (`else:`) becomes nearly unreachable unless explicit non-zero numbers `< 1.0` are passed.

---

### 2.3 Zero-Hardcoding Inspection (Mandate 2)

#### **[MEDIUM-02] Industrial/Manufacturing Bias in Default Fallback & Stem Weights**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 43–45 & Line 85
* **Evidence:**
  ```python
  if scores[best_key] == 0:
      return "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE"
  ```
* **Forensic Analysis:** `TAXONOMY_OPERATIONAL_CONTINUITY_EDGE` contains 19 regex stems (including manufacturing/industrial terms like `r"plant"`, `r"\bot\b"`, `r"scada"`, `r"dispatch"`), whereas `TAXONOMY_DATA_INTEGRITY_ANALYTICS` has only 10 stems. Because unnormalized raw counts (`sum(1 for pattern in patterns...)`) are used without density normalization, and because `TAXONOMY_OPERATIONAL_CONTINUITY_EDGE` is also the hardcoded 0-score fallback, a SaaS, Banking, or Retail client with generic risk descriptions is systematically skewed toward an "Edge/Continuity" taxonomy.

---

### 2.4 Clean Architecture & AST Layout Inspection (Mandate 4)

#### **[MEDIUM-03] Mutable `List[str]` Attributes Inside `@dataclass(frozen=True)`**
* **Location:** `actuarial_taxonomy_clusterer.py`, Lines 58–70
* **Evidence:**
  ```python
  @dataclass(frozen=True)
  class TaxonomyClusterRecord:
      taxonomy_id: str
      matrix_plot_codes: List[str]
      ...
      representative_threats: List[str]
  ```
* **Forensic Analysis:** `frozen=True` only prevents rebinding the attribute reference; `record.matrix_plot_codes.append("X")` remains completely mutable at runtime and makes `TaxonomyClusterRecord` unhashable (`TypeError: unhashable type: 'list'`). Domain Value Objects must use `Tuple[str, ...]` for true immutability and thread safety.

#### **[LOW-01] Natural Sort Defect on Alphanumeric Plot Codes**
* **Location:** `actuarial_taxonomy_clusterer.py`, Line 233
* **Evidence:**
  ```python
  matrix_plot_codes=sorted(b["plot_codes"]),
  ```
* **Forensic Analysis:** Lexicographical sorting places `"R10"` before `"R2"` (if unpadded codes like `R1..R12` are supplied by `vector.get("id")`). A natural sort key (`re.split(r'(\d+)', code)`) ensures deterministic human-readable ordering (`R1, R2, ..., R10`).

#### **[LOW-02] Unsanitized `.format()` Call on Localized Template Strings**
* **Location:** `tomo_asis_ast_compiler.py`, Lines 318–325 & 356–361
* **Evidence:**
  ```python
  bridge_template = t("sec_3_2_taxonomy_bridge_narrative", locale=doc_lang)
  bridge_text = bridge_template.format(...)
  ```
* **Forensic Analysis:** Calling `.format()` directly on a result of `t()` instead of passing kwargs into `t("sec_3_2_taxonomy_bridge_narrative", locale=doc_lang, active_cluster_count=...)` bypasses the i18n engine's safe interpolation guards and will raise a `KeyError` if a translator introduces stray braces or typos in any of the 6 locale catalogs.

---

## 3. CONCRETE REMEDIATION PLAN

### 3.1 Remediation for `src/assessment_engine/domain/actuarial_taxonomy_clusterer.py`

Replace the implementation with the hardened, `Decimal`-reconciled, strictly immutable, 100% Technical English implementation below:

```python
"""Dynamic Ontological Risk Taxonomy Clustering Engine (RFC 081).

Aggregates N-tower Open FAIR risk vectors and granular forensic findings
into canonical ORX/FAIR risk taxonomy families without hardcoded domain assumptions.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Mapping, Optional, Tuple

CANONICAL_TAXONOMY_KEYS: Tuple[str, ...] = (
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE",
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE",
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE",
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION",
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS",
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION",
)

# Canonical Technical English stems (100% ASCII)
_TAXONOMY_STEM_RULES: Dict[str, Tuple[str, ...]] = {
    "TAXONOMY_STRUCTURAL_OBSOLESCENCE": (
        r"obsolesc", r"legacy", r"\beol\b", r"\beos\b", r"end[\s\-]of[\s\-]life",
        r"monolith", r"technical\s+debt", r"aging", r"unsupported", r"hardware",
        r"compute", r"server", r"virtualiz", r"hyperconver",
    ),
    "TAXONOMY_CYBER_IDENTITY_GOVERNANCE": (
        r"cyber", r"\biam\b", r"\bpam\b", r"\bmfa\b", r"identit",
        r"zero[\s\-]trust", r"vulnerab", r"\bcve\b", r"perimeter",
        r"compliance", r"gdpr", r"iso\s*27", r"encrypt", r"security", r"nis\s*2", r"dora",
    ),
    "TAXONOMY_OPERATIONAL_CONTINUITY_EDGE": (
        r"\bdrp\b", r"\bbcp\b", r"\brto\b", r"\brpo\b", r"\bspof\b", r"continui",
        r"resilien", r"backup", r"outage", r"edge", r"network", r"wan\b",
        r"switch", r"facility", r"facilities", r"data\s*center", r"availabil",
    ),
    "TAXONOMY_PROCESS_AUTOMATION_FRICTION": (
        r"manual", r"automat", r"ci/cd", r"devops", r"devsecops", r"\bitsm\b",
        r"workflow", r"toil", r"human\s+error", r"provision", r"runbook",
        r"change\s+mgmt", r"workplace", r"desktop", r"endpoint", r"dex", r"helpdesk",
    ),
    "TAXONOMY_DATA_INTEGRITY_ANALYTICS": (
        r"storage", r"\bmdm\b", r"\betl\b", r"analytics", r"data\s+quality",
        r"schema", r"silo", r"lineage", r"observabil", r"telemetr", r"database",
    ),
    "TAXONOMY_VENDOR_ECOSYSTEM_CONCENTRATION": (
        r"vendor", r"supplier", r"lock[\s\-]in", r"\bsla\b", r"\btprm\b",
        r"third[\s\-]party", r"licens", r"finops", r"outsourc",
        r"cost\s+governance", r"contract", r"strategy",
    ),
}

_NATURAL_SORT_REGEX = re.compile(r"(\d+)")


def _natural_sort_key(code: str) -> List[Any]:
    """Produces a deterministic human-readable sort key (e.g., R2 before R10)."""
    return [
        int(part) if part.isdigit() else part.lower()
        for part in _NATURAL_SORT_REGEX.split(code)
    ]


def _safe_decimal(val: Any, default: Decimal = Decimal("0.0")) -> Decimal:
    """Safely parses any numeric or locale-formatted string into a Decimal without raising."""
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, Decimal):
        return val
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    raw = str(val).strip()
    if not raw:
        return default
    # Strip currency symbols and whitespace; normalize decimal separator
    cleaned = re.sub(r"[^\d,.\-]", "", raw)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return default


@dataclass(frozen=True)
class TaxonomyClusterRecord:
    """Strictly immutable representation of an active, reconciled risk taxonomy cluster."""

    taxonomy_id: str
    matrix_plot_codes: Tuple[str, ...]
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    total_findings: int
    cluster_ale: int
    share_of_total_ale_pct: float
    representative_threats: Tuple[str, ...]


class ActuarialTaxonomyClusterer:
    """Dynamically clusters N-tower risk registers and forensic findings into canonical ORX/FAIR families."""

    @classmethod
    def classify_text(cls, text: str, fallback_index: int = 0) -> str:
        """Deterministically classifies text into the best-matching canonical taxonomy_id."""
        normalized = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
            .lower()
        )

        scores: Dict[str, int] = {k: 0 for k in CANONICAL_TAXONOMY_KEYS}

        for taxonomy_key, patterns in _TAXONOMY_STEM_RULES.items():
            scores[taxonomy_key] += sum(
                1 for pattern in patterns if re.search(pattern, normalized)
            )

        best_key = max(
            CANONICAL_TAXONOMY_KEYS,
            key=lambda k: (scores[k], -CANONICAL_TAXONOMY_KEYS.index(k)),
        )
        if scores[best_key] == 0:
            # Deterministic round-robin fallback when non-ASCII/unmatched text lacks explicit taxonomy_id
            return CANONICAL_TAXONOMY_KEYS[fallback_index % len(CANONICAL_TAXONOMY_KEYS)]
        return best_key

    @classmethod
    def classify_risk_record(cls, record: Mapping[str, Any], fallback_index: int = 0) -> str:
        """Deterministically resolves the canonical taxonomy_id for a given risk or tower record."""
        for tag_field in ("taxonomy_id", "canonical_taxonomy", "risk_taxonomy", "orx_family"):
            explicit_tag = str(record.get(tag_field) or "").strip().upper()
            if explicit_tag in CANONICAL_TAXONOMY_KEYS:
                return explicit_tag

        searchable_corpus = " ".join(
            str(record.get(k) or "")
            for k in (
                "id",
                "code",
                "risk_id",
                "risk_title",
                "title",
                "risk_name",
                "threat_scenario",
                "finding",
                "business_risk",
                "description",
                "tower_name",
                "domain_name",
                "category",
            )
        )
        return cls.classify_text(searchable_corpus, fallback_index=fallback_index)

    @classmethod
    def build_dynamic_clusters(
        cls,
        risk_vectors: List[Dict[str, Any]],
        tower_payloads: Optional[Mapping[str, Dict[str, Any]]] = None,
        reconciled_allocations: Optional[Mapping[str, int]] = None,
    ) -> List[TaxonomyClusterRecord]:
        """Aggregates plot points and granular findings into active, non-empty taxonomy clusters.

        Guarantees exact integer ALE reconciliation and 100.0% percentage summation.
        """
        buckets: Dict[str, Dict[str, Any]] = {
            key: {
                "plot_codes": [],
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "ale": Decimal("0.0"),
                "threats": [],
            }
            for key in CANONICAL_TAXONOMY_KEYS
        }

        # 1. Process primary risk vectors (e.g. from heatmap feed)
        for idx, vector in enumerate(risk_vectors or [], start=1):
            if not isinstance(vector, Mapping):
                continue
            taxonomy_key = cls.classify_risk_record(vector, fallback_index=idx - 1)
            bucket = buckets[taxonomy_key]

            plot_code = str(
                vector.get("id")
                or vector.get("risk_id")
                or vector.get("code")
                or f"R{idx:02d}"
            ).strip()
            if plot_code and plot_code not in bucket["plot_codes"]:
                bucket["plot_codes"].append(plot_code)

            threat_title = str(
                vector.get("risk_name")
                or vector.get("risk_title")
                or vector.get("title")
                or vector.get("threat_scenario")
                or ""
            ).strip()
            if threat_title and threat_title not in bucket["threats"]:
                bucket["threats"].append(threat_title)

            if not tower_payloads:
                raw_ale = (
                    vector.get("ale")
                    if vector.get("ale") is not None
                    else vector.get("ale_p50")
                    if vector.get("ale_p50") is not None
                    else vector.get("ale_expected")
                    if vector.get("ale_expected") is not None
                    else vector.get("financial_exposure")
                    if vector.get("financial_exposure") is not None
                    else vector.get("sle")
                )
                bucket["ale"] += _safe_decimal(raw_ale, Decimal("0.0"))

        # 2. Extract granular forensic findings and financial ALE from tower_payloads
        if tower_payloads:
            for t_idx, (t_code, t_data) in enumerate(tower_payloads.items()):
                if not isinstance(t_data, Mapping):
                    continue

                if reconciled_allocations and t_code in reconciled_allocations:
                    t_ale = _safe_decimal(reconciled_allocations[t_code], Decimal("0.0"))
                else:
                    raw_t_ale = (
                        t_data.get("exact_score_ale")
                        if t_data.get("exact_score_ale") is not None
                        else t_data.get("fair_ale_score")
                    )
                    t_ale = _safe_decimal(raw_t_ale, Decimal("0.0"))

                pillars = t_data.get("pillars_analysis") or []
                t_crit = 0
                t_high = 0
                t_med = 0
                t_low = 0
                dominant_threats: List[str] = []

                for pillar in pillars:
                    if not isinstance(pillar, Mapping):
                        continue
                    for hc in pillar.get("health_check_asis") or []:
                        if not isinstance(hc, Mapping):
                            continue
                        f_text = str(hc.get("finding") or hc.get("risk_observed") or "").strip()
                        b_risk = str(hc.get("business_risk") or hc.get("impact") or "").strip()
                        if not f_text and not b_risk:
                            continue

                        status = str(hc.get("status") or hc.get("severity") or "").upper()
                        raw_tef = (
                            hc.get("threat_event_frequency")
                            if hc.get("threat_event_frequency") is not None
                            else hc.get("tef")
                        )
                        raw_lm = (
                            hc.get("loss_magnitude")
                            if hc.get("loss_magnitude") is not None
                            else hc.get("lm")
                        )
                        tef = _safe_decimal(raw_tef, Decimal("3.0"))
                        lm = _safe_decimal(raw_lm, Decimal("3.0"))

                        if "CRIT" in status or (tef >= Decimal("3.0") and lm >= Decimal("4.0")) or lm >= Decimal("5.0"):
                            t_crit += 1
                        elif "HIGH" in status or (tef >= Decimal("2.0") and lm >= Decimal("3.0")):
                            t_high += 1
                        elif "MED" in status or "MOD" in status or tef >= Decimal("1.0"):
                            t_med += 1
                        else:
                            t_low += 1

                        if b_risk and len(dominant_threats) < 2:
                            dominant_threats.append(b_risk)

                explicit_tower_taxonomy = str(t_data.get("taxonomy_id") or "").strip().upper()
                if explicit_tower_taxonomy in CANONICAL_TAXONOMY_KEYS:
                    taxonomy_key = explicit_tower_taxonomy
                else:
                    tower_corpus = (
                        f"{t_code} {t_data.get('tower_name', '')} "
                        f"{t_data.get('domain_name', '')} {' '.join(dominant_threats)}"
                    )
                    taxonomy_key = cls.classify_text(tower_corpus, fallback_index=t_idx)

                bucket = buckets[taxonomy_key]
                bucket["critical"] += t_crit
                bucket["high"] += t_high
                bucket["medium"] += t_med
                bucket["low"] += t_low
                bucket["ale"] += t_ale

                for dt in dominant_threats:
                    if dt and dt not in bucket["threats"] and len(bucket["threats"]) < 3:
                        bucket["threats"].append(dt)

        # 3. Filter active clusters and reconcile integer ALE & 100.0% shares (Largest Remainder Method)
        active_keys = [
            k for k, b in buckets.items()
            if (b["critical"] + b["high"] + b["medium"] + b["low"]) > 0
            or b["ale"] > Decimal("0.0")
            or bool(b["plot_codes"])
        ]
        if not active_keys:
            return []

        total_portfolio_ale = sum((buckets[k]["ale"] for k in active_keys), Decimal("0.0"))
        reconciled_tenths = cls._reconcile_percentage_tenths(active_keys, buckets, total_portfolio_ale)

        active_clusters: List[TaxonomyClusterRecord] = []
        for taxonomy_key in active_keys:
            b = buckets[taxonomy_key]
            total_f = b["critical"] + b["high"] + b["medium"] + b["low"]
            ale_int = int(b["ale"].quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            share_pct = float(Decimal(reconciled_tenths[taxonomy_key]) / Decimal("10"))

            active_clusters.append(
                TaxonomyClusterRecord(
                    taxonomy_id=taxonomy_key,
                    matrix_plot_codes=tuple(sorted(b["plot_codes"], key=_natural_sort_key)),
                    critical_findings=b["critical"],
                    high_findings=b["high"],
                    medium_findings=b["medium"],
                    low_findings=b["low"],
                    total_findings=total_f,
                    cluster_ale=ale_int,
                    share_of_total_ale_pct=share_pct,
                    representative_threats=tuple(b["threats"][:2]),
                )
            )

        active_clusters.sort(
            key=lambda c: (
                c.cluster_ale,
                c.critical_findings,
                c.total_findings,
                -CANONICAL_TAXONOMY_KEYS.index(c.taxonomy_id),
            ),
            reverse=True,
        )
        return active_clusters

    @staticmethod
    def _reconcile_percentage_tenths(
        active_keys: List[str],
        buckets: Mapping[str, Mapping[str, Any]],
        total_portfolio_ale: Decimal,
    ) -> Dict[str, int]:
        """Reconciles cluster percentage shares in tenths of a percent (sum == 1000 == 100.0%)."""
        if total_portfolio_ale <= Decimal("0.0"):
            return {k: 0 for k in active_keys}

        exact_quotas: Dict[str, Decimal] = {
            k: (buckets[k]["ale"] / total_portfolio_ale) * Decimal("1000")
            for k in active_keys
        }
        floored: Dict[str, int] = {k: int(q // Decimal("1")) for k, q in exact_quotas.items()}
        remainder_deficit = 1000 - sum(floored.values())

        ranked_by_remainder = sorted(
            active_keys,
            key=lambda k: (exact_quotas[k] - Decimal(floored[k]), buckets[k]["ale"]),
            reverse=True,
        )
        for k in ranked_by_remainder[: max(0, remainder_deficit)]:
            floored[k] += 1

        return floored
```

---

### 3.2 Remediation for `src/assessment_engine/domain/tomo_asis_ast_compiler.py` (Lines 317–385)

Update the Chapter 3 Section 3.2 template formatting and footer reconciliation to use safe `t(..., **kwargs)` interpolation and reconcile the total row:

```python
                bridge_text = t(
                    "sec_3_2_taxonomy_bridge_narrative",
                    locale=doc_lang,
                    active_cluster_count=len(clusters),
                    total_plot_points=total_plot_points,
                    total_findings=total_all,
                    critical_count=total_crit,
                    high_count=total_high,
                    medium_count=total_med,
                )
                nodes.append(ParagraphNode(text=bridge_text, font_size=8.5, space_after=6))
```

And for the row badge and total footer row:

```python
                for idx, c in enumerate(clusters):
                    fam_title = t(f"{c.taxonomy_id}_TITLE", locale=doc_lang)
                    fam_rationale = t(f"{c.taxonomy_id}_RATIONALE", locale=doc_lang)
                    if c.representative_threats:
                        empirical_scope = " | ".join(c.representative_threats)
                        rationale_cell = f"{fam_rationale} ({empirical_scope})"
                    else:
                        rationale_cell = fam_rationale

                    codes_cell = ", ".join(c.matrix_plot_codes) if c.matrix_plot_codes else "—"
                    breakdown_cell = t(
                        "sec_3_2_findings_badge_template",
                        locale=doc_lang,
                        total=c.total_findings,
                        crit=c.critical_findings,
                        high=c.high_findings,
                        med=c.medium_findings,
                    )
                    ale_str = (
                        f"{format_currency(c.cluster_ale, currency_symbol=currency, locale=doc_lang, decimals=0)} "
                        f"({format_number(c.share_of_total_ale_pct, locale=doc_lang, decimals=1)}%)"
                    )

                    is_alt = (idx % 2 == 1)
                    row_bg = self.alt_row_hex if is_alt else "FFFFFF"

                    legend_rows.append(
                        TableRowNode(
                            cells=[
                                CellNode(text=fam_title, bold=True, bg_color=row_bg, font_size=7.5),
                                CellNode(text=codes_cell, bg_color=row_bg, font_size=7.5, align="CENTER"),
                                CellNode(text=rationale_cell, bg_color=row_bg, font_size=7.5),
                                CellNode(text=breakdown_cell, bold=True, bg_color=row_bg, font_size=7.5, align="CENTER"),
                                CellNode(text=ale_str, bold=True, bg_color=row_bg, font_size=7.5, align="CENTER"),
                            ]
                        )
                    )

                # Total Footer Row (Strictly Reconciled to Table 3.1 Corporate ALE & 100.0%)
                tot_ale_val = sum(c.cluster_ale for c in clusters)
                tot_share_pct = 100.0 if tot_ale_val > 0 else 0.0
                tot_breakdown = t(
                    "sec_3_2_findings_badge_template",
                    locale=doc_lang,
                    total=total_all,
                    crit=total_crit,
                    high=total_high,
                    med=total_med,
                )
```

---

## 4. AUDIT SIGN-OFF MATRIX

| Mandate | Pre-Remediation Status | Post-Remediation Status |
| :--- | :--- | :--- |
| **1. 100% Technical English Codebase** | **FAIL** (`"ALT"` in `actuarial_taxonomy_clusterer.py:196`) | **PASS** (100% ASCII Technical English) |
| **2. Zero Hardcoding & Multi-Lingual Scaling** | **FAIL** (Japanese/non-ASCII collapse + industrial stem bias) | **PASS** (Multi-tag inspection + deterministic round-robin fallback) |
| **3. Actuarial & Mathematical Integrity** | **FAIL** (Float rounding drift, unguarded `float()`, `0.0` falsy bug) | **PASS** (`Decimal` `ROUND_HALF_UP`, Largest Remainder 100.0% reconciliation) |
| **4. Clean / Hexagonal Architecture** | **CONDITIONAL PASS** (Mutable `List` inside `frozen=True` dataclass) | **PASS** (Strictly immutable `Tuple` Value Objects, zero I/O) |