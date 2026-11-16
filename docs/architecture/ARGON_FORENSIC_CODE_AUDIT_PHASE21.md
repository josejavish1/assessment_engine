# ARGON PHASE 21: DEEP-DIVE FORENSIC CODE AUDIT REPORT

**Document ID:** `ARGON_FORENSIC_CODE_AUDIT_PHASE21`  
**Target Path:** `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE21.md`  
**Auditor:** Gemini-4-Argon (Global Chief Systems Architect, Principal Compiler Engineer & Fellow of the Society of Actuaries)  
**Audit Scope:** Commit Range `b8ccde4^..HEAD` (`src/assessment_engine/domain/ingestion/*`, `tests/unit/*`, `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE20.md`)  
**Classification:** MANDATORY ARCHITECTURAL GATEWAY REVIEW  

---

## 1. EXECUTIVE AUDIT SUMMARY & VERDICT

### **OVERALL AUDIT VERDICT: PASS WITH MANDATORY MINOR REMEDIATIONS (CONDITIONAL RELEASE GATE)**

The Phase 21 engineering cycle successfully remediated the most severe structural defects identified during the Phase 20 forensic audit:
1. **100% Technical English Compliance in Source & Tests:** All Spanish string literals (`"Exploratoria"`, `"NO_EVIDENCIADO"`, `"cpd"`, and Spanish test narratives) have been purged from production logic (`missing_data_circuit_breaker.py`, `context_router.py`) and unit test suites (`test_upstream_ingestion_gating.py`, `test_epistemic_fact_registry.py`).
2. **Elimination of Client-Name Branching & Substring Routing Bugs:** The explicit `"molins"` branch and `"prenet"` token in `EpistemicContextRouter` have been removed. Word-boundary regex compilation (`\b...\b`) and strict fail-closed routing (`return ""`) are now verified and enforced.
3. **Concurrency Locking & Boolean Trap Protection:** `MissingDataCircuitBreaker` now explicitly rejects Python `bool` instances (`not isinstance(raw_val, bool)`), and `EpistemicFactRegistry` now wraps state mutations in a reentrant lock (`threading.RLock()`) with `frozen=True` on `ActuarialFactTuple`.

However, our forensic inspection uncovered **five residual architectural and compliance defects** that prevent an unconditional clean bill of health and require immediate surgical remediation:

1. **Invariant #2 Residual Violations (Client-Specific Numbers & Vendor Term Leakage):**
   - `src/assessment_engine/domain/ingestion/context_router.py:39` still retains `"metrocluster"` (a proprietary NetApp ONTAP technology) inside `TOWER_DOMAIN_KEYWORDS["T4"]`.
   - `tests/unit/test_upstream_ingestion_gating.py:62` still retains the engagement-specific `"10 Gbps"` literal (`"dark fiber 10 Gbps interconnect"`).
   - `tests/unit/test_epistemic_fact_registry.py:29, 31, 41, 43, 57, 59` still hardcodes the engagement-specific metric `613` (`"613 days without a reboot"`, `value_scalar=613`), which was explicitly flagged in Phase 20 Remediation Patch 4 (`450`) but left unpatched in the revised test file.
2. **Invariant #3 Defect (Corrupted Markdown Wrapper & Truncation in `ARGON_FORENSIC_CODE_AUDIT_PHASE20.md`):**
   - `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE20.md` opens with a literal ```` ```markdown ```` code-fence on Line 1 and truncates mid-line at Line 621 (`do`), leaving unclosed code blocks and broken documentation in the repository history.
3. **Invariant #3 Defect (Duplicate Domain Lease Bypass & Case-Sensitivity Bug in `EpistemicFactRegistry`):**
   - `ActuarialFactTuple` omitted the `@model_validator(mode="after")` uniqueness check on `domain_leases` and failed to normalize `lease.domain_id.upper()`. Consequently, `acquire_lease` (`if lease.domain_id == domain_id.upper():`) fails altogether if a `DomainPerspective` is constructed with a lowercase `domain_id` (e.g., `"t2"`), and duplicate domain leases for the same domain bypass single-redemption invariants.
4. **Invariant #3 Defect (`OverflowError` & `inf` Vulnerability in `MissingDataCircuitBreaker`):**
   - `missing_data_circuit_breaker.py` replaced `math.isfinite(float(raw_val))` with `not math.isnan(float(raw_val))` and hardcoded `1.0 <= float(raw_val) <= 5.0` and `.PR1` instead of parameterizing scale bounds (`min_score`, `max_score`, `question_suffix`). Furthermore, passing an out-of-range integer (> $10^{308}$) raises an unhandled `OverflowError` on `float(raw_val)`.
5. **Unverified Compiler & Orchestrator Gates in Commit Diff:**
   - The Chapter 4 FAIR vulnerability derivation fix (`payload_to_ast.py`), the removal of hardcoded `"CMMI for Infrastructure"` (`run_tower_blueprint_engine.py`), and OpenXML layout guards (`w:pageBreakBefore` / `w:keepNext` / `w:tblHeader`) were **not included in commit range `b8ccde4^..HEAD`** and must be verified in the compiler layer.

---

## 2. COMPLIANCE AUDIT AGAINST CORE INVARIANTS

### 2.1 Invariant #1: 100% Technical English (Language Decoupling Law) — **PASS (PRODUCTION & TESTS)**

Every token, identifier, docstring, log string, exception message, and unit test fixture across the four revised Python modules was lexically scanned:

| Module Path | Lexical Scan Result | Status | Notes |
| :--- | :--- | :--- | :--- |
| `src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py` | 100% Technical English | **PASS** | `"Exploratoria"` $\rightarrow$ `"EXPLORATORY"`; `"NO_EVIDENCIADO"` $\rightarrow$ `"UNOBSERVED"`. |
| `src/assessment_engine/domain/ingestion/context_router.py` | 100% Technical English | **PASS** | Spanish acronym `"cpd"` removed from `T1`. |
| `src/assessment_engine/domain/ingestion/epistemic_fact_registry.py` | 100% Technical English | **PASS** | All docstrings, enums, and error messages are in 100% Technical English. |
| `tests/unit/test_upstream_ingestion_gating.py` | 100% Technical English | **PASS** | All Spanish sentences (`"En la sala técnica del CPD..."`, `"básculas de pesaje"`) replaced with English fixtures. |
| `tests/unit/test_epistemic_fact_registry.py` | 100% Technical English | **PASS** | Spanish `verbatim_quote` and `semantic_framing` strings replaced with English equivalents. |
| `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE20.md` | Contains Historical Audit Quotes | **EXEMPT (AUDIT LOG)** | Quotes historical Phase 20 Spanish violations strictly as forensic evidence, though file is truncated at Line 621. |

---

### 2.2 Invariant #2: Zero Hardcoding & Total Scale Agnosticism — **CONDITIONAL FAIL (MINOR RESIDUALS)**

While all client names (`"molins"`, `"prenet"`, `"simplivity"`, `"huawei"`, `"broadcom"`, `"nagstamon"`) were removed from production code, the following hardcoded vendor/engagement residuals remain:

| File Path | Line(s) | Offending Token / Assumption | Severity | Required Action |
| :--- | :--- | :--- | :--- | :--- |
| `src/assessment_engine/domain/ingestion/context_router.py` | `39` | `"metrocluster"` in `TOWER_DOMAIN_KEYWORDS["T4"]` | **MEDIUM** | Replace proprietary NetApp product name `"metrocluster"` with vendor-neutral `"synchronous replication"` or `"stretched cluster"`. |
| `src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py` | `34, 42` | Hardcoded `.PR1` suffix (`qid = f"{kpi['kpi_id']}.PR1"`) and fixed `1.0 <= float(raw_val) <= 5.0` | **LOW** | Parameterize `min_score: float = 1.0`, `max_score: float = 5.0`, and `question_suffix: str = "PR1"` to support diverse assessment schemas without code modification. |
| `tests/unit/test_epistemic_fact_registry.py` | `29, 31, 41, 43, 57, 59` | Hardcoded client-specific uptime number `613` (`"613 days without a reboot"`, `value_scalar=613`) | **MEDIUM** | Replace `613` with a synthetic test constant (e.g., `450`) to comply strictly with Invariant #2 (`No specific numbers e.g. '613'`). |
| `tests/unit/test_upstream_ingestion_gating.py` | `62` | `"dark fiber 10 Gbps interconnect"` | **LOW** | Replace engagement-specific `"10 Gbps"` with generic `"high-capacity dark fiber interconnect"`. |

---

## 3. IN-DEPTH DEFECT ANALYSIS (BUGS, EDGE CASES & ANTIPATTERNS)

### Defect 3.1: Case-Sensitivity Mismatch & Duplicate Domain Lease Vulnerability in `EpistemicFactRegistry`
* **Location:** `src/assessment_engine/domain/ingestion/epistemic_fact_registry.py:62–76` and `155–186`
* **Mechanism:**
  In `register_fact()`, the registry indexes domains using uppercase normalization:
  ```python
  for lease in fact.domain_leases:
      d_id = lease.domain_id.upper()
      ...
      self._domain_index[d_id].add(fact.fact_id)
  ```
  However, in `acquire_lease()`, the comparison against `lease.domain_id` does **not** normalize `lease.domain_id` to uppercase:
  ```python
  for lease in fact.domain_leases:
      if lease.domain_id == domain_id.upper():
  ```
  Furthermore, `ActuarialFactTuple` does not validate that `domain_leases` contains at most one `DomainPerspective` per `domain_id`.
* **Failure Modes:**
  1. **Silent Lease Denial on Lowercase `domain_id`:** If a `DomainPerspective` is instantiated with `domain_id="t2"`, `register_fact` indexes it under `"T2"`, `get_facts_for_domain("T2")` returns it, but `acquire_lease(fact_id, "T2", ...)` evaluates `"t2" == "T2"` (`False`) and permanently rejects lease acquisition with `"Domain 'T2' possesses no lease authority"`.
  2. **Multiple Lease Bypass:** If `domain_leases` inadvertently contains two `DomainPerspective(domain_id="T2", ...)` entries, `acquire_lease` redeems the first on the first call, and on the second call skips the first (`status == LeaseStatus.CONSUMED` returns `False` immediately—or if ordered differently, creates ambiguous state). Adding a Pydantic `@model_validator(mode="after")` on `ActuarialFactTuple` to enforce unique uppercase `domain_id` entries eliminates both bugs at construction time.

### Defect 3.2: Mutable `DomainPerspective` Inside `frozen=True` `ActuarialFactTuple`
* **Location:** `src/assessment_engine/domain/ingestion/epistemic_fact_registry.py:62–88`
* **Mechanism:**
  `ActuarialFactTuple` is marked `frozen=True` and stores `domain_leases: Tuple[DomainPerspective, ...]`. However, `DomainPerspective` itself is **mutable** (`model_config = ConfigDict(extra="forbid")` without `frozen=True`), and `acquire_lease` mutates `lease.status = LeaseStatus.CONSUMED` directly on the object inside `fact.domain_leases` and returns `lease` to the caller.
* **Impact:**
  Any external caller holding the returned `DomainPerspective` reference (or accessing `fact.domain_leases[0]` via `get_fact()`) can mutate `lease.status = LeaseStatus.AVAILABLE` or `lease.lease_type = LeaseType.PRIMARY_OWNER` outside `self._lock`, bypassing both thread safety and single-redemption enforcement.
* **Architectural Fix:** `acquire_lease` should return a shallow copy (`lease.model_copy(deep=True)`) to external callers so internal registry state cannot be mutated outside `self._lock`.

### Defect 3.3: `Boolean` Trap in `ActuarialFactTuple.value_scalar` Type Union
* **Location:** `src/assessment_engine/domain/ingestion/epistemic_fact_registry.py:78`
* **Mechanism:**
  ```python
  value_scalar: Optional[Union[float, int, bool]] = Field(default=None, ...)
  ```
* **Impact:** In Pydantic v2 (non-strict mode), `Union[float, int, bool]` attempts type coercion in left-to-right order. Because `float` and `int` precede `bool`, passing a boolean `True` or `False` can be coerced to `1.0` or `1` (`float` or `int`) in certain validation modes unless `bool` is placed first (`Union[bool, int, float]`) or `StrictBool` is used. Placing `bool` first in `Union[bool, int, float]` guarantees `bool` is never coerced into `int`/`float`.

### Defect 3.4: Word-Boundary Regex Edge Case with Non-Word Characters & Hyphens in `EpistemicContextRouter`
* **Location:** `src/assessment_engine/domain/ingestion/context_router.py:78–89`
* **Mechanism:**
  `EpistemicContextRouter._get_patterns_for_tower` compiles keywords via `re.compile(rf"\b{re.escape(kw.lower())}\b")`.
* **Edge Case Analysis:**
  1. All current keywords in `TOWER_DOMAIN_KEYWORDS` begin and end with alphanumeric word characters (`[a-z0-9]`), so `\b...\b` works cleanly for the default set (including `"on-call"`, `"zero trust"`, `"s3"`, `"k8s"`).
  2. However, if a caller passes `custom_keywords` containing leading/trailing punctuation or symbols (e.g., `".net"`, `"c++"`, `"wi-fi"`), `\b` before `.` or after `+` will **never match** when preceded or followed by whitespace because `.` and `+` are non-word characters (`\W`), and a word boundary `\b` requires a transition between `\w` and `\W`.
  3. Furthermore, if a transcript writes `"on-premises"`, `"cloud-spend"`, or `"backup/restore"`, `\b` treats `-` and `/` as non-word boundaries, which works as intended—except if a keyword is `"dr"` and the text contains `"dr-site"` (matches) vs `"vdi-endpoint"`. Using lookaround assertions `(?<!\w){re.escape(kw.lower())}(?!\w)` is strictly superior to `\b...\b` because it works identically for alphanumeric tokens while also matching tokens with leading/trailing symbols (like `".net"` or `"c++"`).

### Defect 3.5: Truncated Commit File `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE20.md`
* **Location:** `docs/architecture/ARGON_FORENSIC_CODE_AUDIT_PHASE20.md:1` and `621`
* **Mechanism:**
  The newly committed file `ARGON_FORENSIC_CODE_AUDIT_PHASE20.md` starts with ```` ```markdown ```` on Line 1 (causing Markdown renderers to render the entire document as a raw code block) and terminates abruptly at Line 621 mid-token (`do`).

---

## 4. VERIFICATION OF REMEDIATIONS (PHASE 20 $\rightarrow$ PHASE 21)

| Remediation Item | Phase 20 Status | Phase 21 Verification Status | Forensic Evidence & Notes |
| :--- | :--- | :--- | :--- |
| **1. Substring Matching with Word Boundaries (`\b...\b`)** | **FAILED** (`kw in frag_lower`) | **VERIFIED FIXED** | `context_router.py:75–89` caches compiled regexes (`re.compile(rf"\b{re.escape(kw.lower())}\b")`) and tests them in `test_epistemic_context_router_prevents_substring_false_positives` against `"not"`, `"both"`, and `"protocol"`. |
| **2. Fail-Closed Context Router Behavior** | **FAILED** (Returned `raw_fragments[:5]`) | **VERIFIED FIXED** | `context_router.py:106, 121` now returns `""` when `not patterns` or `not relevant_frags`. Verified via unit test assertion `assert t10_context == ""`. |
| **3. Boolean-as-Integer Guard in `MissingDataCircuitBreaker`** | **FAILED** (`isinstance(True, (int, float))`) | **VERIFIED FIXED** | `missing_data_circuit_breaker.py:39` explicitly checks `and not isinstance(raw_val, bool)`. Verified by `T4.P4.K4.PR1: True` test case in `test_upstream_ingestion_gating.py:21, 47–50`. |
| **4. Thread-Safety (`RLock`) & Immutability (`frozen=True`) in `EpistemicFactRegistry`** | **FAILED** (No lock, mutable AFT) | **PARTIALLY FIXED** | `threading.RLock()` added to `EpistemicFactRegistry` (`epistemic_fact_registry.py:117`) and `frozen=True` added to `ActuarialFactTuple` (`line 73`). Needs `domain_id.upper()` normalization in `DomainPerspective` and `model_copy()` return in `acquire_lease`. |
| **5. Elimination of FAIR 60–85% vs 80–95% Contradiction in `payload_to_ast.py`** | **FLAGGED** | **NOT IN DIFF (`b8ccde4^..HEAD`)** | `payload_to_ast.py` was not modified in commit range `b8ccde4^..HEAD`. Must be verified in the compiler layer to confirm `vulnerability_ratio` is dynamically bound from `strategic_risk_cards` rather than hardcoded narrative bands. |
| **6. Elimination of Hardcoded `"CMMI for Infrastructure"` in `run_tower_blueprint_engine.py`** | **FLAGGED** | **NOT IN DIFF (`b8ccde4^..HEAD`)** | `run_tower_blueprint_engine.py` was not modified in commit range `b8ccde4^..HEAD`. Must be verified in the orchestrator layer before final release. |

---

## 5. FINAL ARCHITECTURAL RATING & ACTIONABLE RECOMMENDATIONS

### 5.1 Architectural Scorecard

| Dimension | Score | Rating | Commentary |
| :--- | :---: | :---: | :--- |
| **Language Decoupling Law (Invariant #1)** | **10.0 / 10** | **EXEMPLARY** | Zero Spanish tokens remain in production or test Python modules. |
| **Zero Hardcoding & Scale Agnosticism (Invariant #2)** | **8.5 / 10** | **GOOD (Minor Residuals)** | Client names removed; must purge `"metrocluster"`, `"10 Gbps"`, and `613` from tests/keywords. |
| **Epistemic Integrity & Concurrency (Invariant #3)** | **9.0 / 10** | **STRONG** | Fail-closed routing, `RLock`, and polarity-aware claim gating are solid; fix lowercase `domain_id` lookup and `DomainPerspective` copy semantics. |
| **Documentation Hygiene** | **7.0 / 10** | **NEEDS CLEANUP** | `ARGON_FORENSIC_CODE_AUDIT_PHASE20.md` is truncated at Line 621. |

---

### 5.2 Actionable Remediation Patches (Apply Before Release Tagging)

#### Patch 1: `src/assessment_engine/domain/ingestion/context_router.py`
*Replaces proprietary `"metrocluster"` with vendor-neutral `"synchronous replication"` and upgrades `\b` to `(?<!\w)...(?!\w)` for universal symbol safety.*

```diff
--- a/src/assessment_engine/domain/ingestion/context_router.py
+++ b/src/assessment_engine/domain/ingestion/context_router.py
@@ -36,7 +36,7 @@ class EpistemicContextRouter:
             "dns", "dhcp", "firewall", "bgp", "vlan", "bandwidth", "telemetry link", "dci",
         },
         "T4": {
-            "storage", "disk", "san", "nas", "storage array", "metrocluster", "iops",
+            "storage", "disk", "san", "nas", "storage array", "synchronous replication", "iops",
             "throughput", "tiering", "nvme", "flash", "block storage", "object storage",
             "volume", "snapshot", "nfs", "iscsi", "s3", "data tier",
         },
@@ -80,11 +80,11 @@ class EpistemicContextRouter:
     ) -> List[Pattern[str]]:
         """Compiles regex patterns with word boundaries to prevent substring matching defects."""
         if custom_keywords is not None:
-            return [re.compile(rf"\b{re.escape(kw.lower())}\b") for kw in custom_keywords]
+            return [re.compile(rf"(?<!\w){re.escape(kw.lower())}(?!\w)") for kw in custom_keywords]
         if tower_id not in cls._COMPILED_PATTERNS:
             kws = cls.TOWER_DOMAIN_KEYWORDS.get(tower_id, set())
             cls._COMPILED_PATTERNS[tower_id] = [
-                re.compile(rf"\b{re.escape(kw.lower())}\b") for kw in sorted(kws)
+                re.compile(rf"(?<!\w){re.escape(kw.lower())}(?!\w)") for kw in sorted(kws)
             ]
         return cls._COMPILED_PATTERNS[tower_id]
```

#### Patch 2: `src/assessment_engine/domain/ingestion/epistemic_fact_registry.py`
*Normalizes `domain_id` to uppercase on `DomainPerspective`, prevents duplicate domain leases per fact, fixes `Union[bool, int, float]` ordering, and returns an isolated copy on `acquire_lease`.*

```diff
--- a/src/assessment_engine/domain/ingestion/epistemic_fact_registry.py
+++ b/src/assessment_engine/domain/ingestion/epistemic_fact_registry.py
@@ -16,7 +16,7 @@ import hashlib
 import threading
 from enum import Enum
 from typing import Any, Dict, List, Optional, Set, Tuple, Union
-from pydantic import BaseModel, Field, ConfigDict
+from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
 import logging
 
 logger = logging.getLogger(__name__)
@@ -68,6 +68,11 @@ class DomainPerspective(BaseModel):
     status: LeaseStatus = Field(default=LeaseStatus.AVAILABLE, description="Lease consumption state")
     consumed_in_section: Optional[str] = Field(default=None, description="Section ID where lease was redeemed")
 
+    @field_validator("domain_id")
+    @classmethod
+    def _normalize_domain_id(cls, v: str) -> str:
+        return v.strip().upper()
+
 
 class ActuarialFactTuple(BaseModel):
     """Immutable, typed actuarial fact with cryptographic provenance."""
@@ -76,7 +81,7 @@ class ActuarialFactTuple(BaseModel):
     fact_id: str = Field(..., description="Deterministic SHA-256 hash of subject + predicate + span")
     canonical_subject: str = Field(..., description="Ontology entity ID, e.g., 'SYS_COMPUTE_HOST_01'")
     predicate: str = Field(..., description="Ontology relationship verb, e.g., 'HAS_CONTINUOUS_UPTIME'")
-    value_scalar: Optional[Union[float, int, bool]] = Field(default=None, description="Canonical scalar value")
+    value_scalar: Optional[Union[bool, int, float]] = Field(default=None, description="Canonical scalar value")
     value_text: Optional[str] = Field(default=None, description="Descriptive textual value")
     unit_iso: Optional[str] = Field(default=None, description="Standardized ISO unit, e.g., 'DAYS', 'HOURS', 'EUR'")
     modality: EpistemicModality = Field(..., description="Verification degree")
@@ -86,6 +91,15 @@ class ActuarialFactTuple(BaseModel):
     verbatim_quote: str = Field(..., description="Exact raw text snippet from evidence corpus")
     domain_leases: Tuple[DomainPerspective, ...] = Field(default_factory=tuple, description="Assigned domain perspective leases")
 
+    @model_validator(mode="after")
+    def _enforce_unique_domain_leases(self) -> "ActuarialFactTuple":
+        seen: Set[str] = set()
+        for lease in self.domain_leases:
+            if lease.domain_id in seen:
+                raise ValueError(f"Duplicate DomainPerspective for domain '{lease.domain_id}' in fact '{self.fact_id}'.")
+            seen.add(lease.domain_id)
+        return self
+
     @classmethod
     def create(
         cls,
@@ -167,19 +181,20 @@ class EpistemicFactRegistry:
             if not fact:
                 return False, f"Fact '{fact_id}' not found in registry.", None
 
+            target_domain = domain_id.strip().upper()
             for lease in fact.domain_leases:
-                if lease.domain_id == domain_id.upper():
+                if lease.domain_id == target_domain:
                     if lease.status == LeaseStatus.CONSUMED:
                         return (
                             False,
                             f"Lease for domain '{domain_id}' on fact '{fact_id}' already consumed in '{lease.consumed_in_section}'. Restatement prohibited.",
-                            lease,
+                            lease.model_copy(deep=True),
                         )
                     # Redeem lease
                     lease.status = LeaseStatus.CONSUMED
                     lease.consumed_in_section = section_id
-                    return True, "Lease acquired successfully.", lease
+                    return True, "Lease acquired successfully.", lease.model_copy(deep=True)
 
             return False, f"Domain '{domain_id}' possesses no lease authority over fact '{fact_id}'.", None
```

#### Patch 3: `src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py`
*Uses `math.isfinite()` (blocking both `NaN` and `±Inf`), guards against `OverflowError`, and parameterizes `min_score`, `max_score`, and `question_suffix`.*

```diff
--- a/src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py
+++ b/src/assessment_engine/domain/ingestion/missing_data_circuit_breaker.py
@@ -20,6 +20,9 @@ class MissingDataCircuitBreaker:
         tower_id: str,
         expected_kpis: List[Dict[str, Any]],
         parsed_scores: Dict[str, float],
+        min_score: float = 1.0,
+        max_score: float = 5.0,
+        question_suffix: str = "PR1",
     ) -> List[Dict[str, Any]]:
         """Validates all expected KPIs from the tower definition against parsed responses.
 
@@ -29,17 +32,20 @@ class MissingDataCircuitBreaker:
         """
         inspected_answers = []
         for kpi in expected_kpis:
-            qid = f"{kpi['kpi_id']}.PR1"
+            qid = f"{kpi['kpi_id']}.{question_suffix}" if question_suffix else str(kpi["kpi_id"])
             raw_val = parsed_scores.get(qid)
 
-            # Strict numeric guard: disallow booleans (subclass of int in Python) and NaNs
-            is_valid_numeric = (
-                raw_val is not None
-                and not isinstance(raw_val, bool)
-                and isinstance(raw_val, (int, float))
-                and not math.isnan(float(raw_val))
-                and 1.0 <= float(raw_val) <= 5.0
-            )
+            # Strict numeric guard: disallow booleans (subclass of int in Python), NaNs, and Infinities
+            is_valid_numeric = False
+            if raw_val is not None and not isinstance(raw_val, bool) and isinstance(raw_val, (int, float)):
+                try:
+                    f_val = float(raw_val)
+                    is_valid_numeric = math.isfinite(f_val) and (min_score <= f_val <= max_score)
+                except OverflowError:
+                    is_valid_numeric = False
 
             if is_valid_numeric:
                 val = float(raw_val)
```

#### Patch 4: `tests/unit/test_epistemic_fact_registry.py` & `tests/unit/test_upstream_ingestion_gating.py`
*Replaces engagement-specific numbers (`613`, `"10 Gbps"`) with generic synthetic constants (`450`, `"high-capacity"`).*

```diff
--- a/tests/unit/test_epistemic_fact_registry.py
+++ b/tests/unit/test_epistemic_fact_registry.py
@@ -26,9 +26,9 @@ def test_actuarial_fact_tuple_deterministic_provenance():
         predicate="HAS_CONTINUOUS_UPTIME",
         source_document_id="transcript_20261014.docx",
         source_char_span=(12450, 12580),
-        verbatim_quote="this host has been continuously operating for 613 days without a reboot",
+        verbatim_quote="this host has been continuously operating for 450 days without a reboot",
         modality=EpistemicModality.MANAGEMENT_ASSERTION,
-        value_scalar=613,
+        value_scalar=450,
         unit_iso="DAYS",
     )
     assert aft.fact_id.startswith("AFT-")
@@ -39,9 +39,9 @@ def test_actuarial_fact_tuple_deterministic_provenance():
         predicate="HAS_CONTINUOUS_UPTIME",
         source_document_id="transcript_20261014.docx",
         source_char_span=(12450, 12580),
-        verbatim_quote="this host has been continuously operating for 613 days without a reboot",
+        verbatim_quote="this host has been continuously operating for 450 days without a reboot",
         modality=EpistemicModality.MANAGEMENT_ASSERTION,
-        value_scalar=613,
+        value_scalar=450,
         unit_iso="DAYS",
     )
     assert aft.fact_id == aft2.fact_id
@@ -54,9 +54,9 @@ def test_perspective_lease_allocation_prevents_narrative_duplication():
         predicate="HAS_CONTINUOUS_UPTIME",
         source_document_id="transcript_20261014.docx",
         source_char_span=(12450, 12580),
-        verbatim_quote="this host has been continuously operating for 613 days without a reboot",
+        verbatim_quote="this host has been continuously operating for 450 days without a reboot",
         modality=EpistemicModality.MANAGEMENT_ASSERTION,
-        value_scalar=613,
+        value_scalar=450,
         unit_iso="DAYS",
         domain_leases=[
             DomainPerspective(
```

```diff
--- a/tests/unit/test_upstream_ingestion_gating.py
+++ b/tests/unit/test_upstream_ingestion_gating.py
@@ -59,7 +59,7 @@ def test_epistemic_context_router_isolates_tower_domains():
     raw_fragments = [
         "The primary data center facilities utilize two redundant chillers and diesel backup generators.",
         "Cloud spend in public cloud and operating budget constraints directly impact the annual IT strategy.",
-        "The core network backbone leverages redundant switches and a point to point dark fiber 10 Gbps interconnect.",
+        "The core network backbone leverages redundant switches and a point to point high-capacity dark fiber interconnect.",
         "Industrial SCADA telemetry controllers and shop floor weighbridge systems feed the legacy ERP database.",
     ]
```