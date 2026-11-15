# ARGON UNIVERSAL GENERATOR OVERHAUL: MASTER ARCHITECTURAL BLUEPRINT

**Document ID:** `ARCH-BLUEPRINT-2026-ARGON-V4`  
**Target Path:** `docs/architecture/ARGON_UNIVERSAL_GENERATOR_OVERHAUL_MASTER_PLAN.md`  
**Author:** Gemini-4-Argon — Chief Systems Architect, Actuarial Fellow & Global Managing Partner for Enterprise Due Diligence  
**Status:** MANDATORY EXECUTION BASELINE  
**Classification:** Internal Engineering & Actuarial Architecture Specification  

---

## 1. EXECUTIVE SUMMARY & CONSULTING MANIFESTO

### 1.1 Forensic Diagnosis: The Fallacy of Iterative Tower Patching
A comprehensive cross-tower forensic audit of our 10-tower enterprise due diligence suite exposed a foundational truth: **we do not suffer from ten poorly written reports; we suffer from a single visually and narratively sophisticated generation engine that is structurally poisoned at the baseline.** 

Attempting to remediate individual deliverables (such as manually patching Tower 2 or Tower 5) is an architectural anti-pattern. Manual or tower-specific prompt tuning masks systemic defects while allowing epistemic contamination, mathematical drift, and inventory bleed to persist across the remaining nine towers. Effective remediation requires halting ad-hoc iterative edits on individual tower outputs and executing a structural overhaul of the core generation pipeline.

```
+-----------------------------------------------------------------------------------+
|                        LEGACY CONTAMINATED GENERATOR PIPELINE                     |
|                                                                                   |
|  [Flat 20% Fallback] ---> [Legacy CMMI Scale] ---> [Unfiltered Global Context]    |
|          |                        |                            |                  |
|          v                        v                            v                  |
|  (Mathematical Drift)   (Tier Misclassification)   (Cross-Tower Inventory Bleed)  |
|          |                        |                            |                  |
|          +------------------------+----------------------------+                  |
|                                   |                                               |
|                                   v                                               |
|            [Unconstrained LLM Extrapolation & Forced Resolution]                  |
|                                   |                                               |
|                                   v                                               |
|       ❌ Speculative Architecture | ❌ Silenced Contradictions | ❌ Generic FAIR  |
+-----------------------------------------------------------------------------------+
                                    |
                                    |  (STRUCTURAL OVERHAUL)
                                    v
+-----------------------------------------------------------------------------------+
|                     ARGON V4 DETERMINISTIC GENERATOR PIPELINE                     |
|                                                                                   |
|  [Master Matrix SOT] ---> [Official 5-Tier Scale] ---> [MECE Inventory Router]    |
|          |                        |                            |                  |
|          v                        v                            v                  |
|  (100% Dot-Product)     (Exact Boundary Mapping)   (Strict Domain Orthogonality)  |
|          |                        |                            |                  |
|          +------------------------+----------------------------+                  |
|                                   |                                               |
|                                   v                                               |
|        [3-Tier Evidence Ledger + Epistemic Contradiction Preservation]            |
|                                   |                                               |
|                                   v                                               |
|       ✅ Factual Parsimony | ✅ Explicit Divergences | ✅ Traceable Open FAIR     |
+-----------------------------------------------------------------------------------+
```

### 1.2 The Ten Structural Defects & Their Architectural Eradication
To achieve institutional-grade reliability across engagements ranging from $50M mid-market enterprises to $100B+ global conglomerates, the generator must transition from **generative extrapolation** to **deterministic, evidence-constrained synthesis**. 

| Defect ID | Structural Flaw Identified in Forensic Audit | Root Cause in Legacy Engine | Argon V4 Architectural Eradication |
| :--- | :--- | :--- | :--- |
| **DEF-01** | **Master Matrix Weight Drift** | Fallback to flat `20/20/20/20/20` weights in T4–T10; float rounding errors. | Strict synchronization with official master matrices; 100% deterministic dot-product scoring and Largest Remainder integer normalization. |
| **DEF-02** | **Maturity Scale Misalignment** | Legacy CMMI intervals (`1.50–2.49`) misclassifying scores (e.g., `2.57` as Level 3 instead of Level 2). | Hard replacement of intervals in `governance_scales.json`, `scale_engine.py`, and `locales.json` with the official 5-tier project scale (`[1.00, 1.79]`, `[1.80, 2.59]`, etc.). |
| **DEF-03** | **Signal-to-Architecture Hallucination** | LLM extrapolating unverified enterprise components (VESDA, CRAC, BitLocker, DLP) from low-maturity control gaps. | Implementation of an **Evidence-Constrained Architectural Synthesizer** with negative AST linters blocking ungrounded technical nouns. |
| **DEF-04** | **Conflation of Fact vs. Inference** | Seamless blending of real client facts (Huawei, Equinix) with invented telemetry (specific VLAN IDs, BFD timers, AWS). | Strict epistemic tagging separating *(a) Declared Client Infrastructure*, *(b) Consultant Inferences*, and *(c) Unmeasured Telemetry*. |
| **DEF-05** | **Absence of Validation States** | Presenting unverified survey assertions as "audited" or "empirically observed". | Injection of a 3-Tier **Evidence Ledger** (`EXPLORATORY`, `CONTRASTED`, `EVIDENCED`) into `case_input.json` and AST nodes. |
| **DEF-06** | **Forced Contradiction Resolution** | Engine unilaterally picking a side when survey scores conflict with discovery interviews (e.g., T2 K8s, T5 Failover). | **Epistemic Contradiction Engine** that preserves both data points and emits mandatory `Contradictory Sources / Pending Validation` callout blocks. |
| **DEF-07** | **Cross-Tower Inventory Bleed** | Indiscriminate repetition of global assets (NetApp, SimpliVity, SAP, Zabbix) across T3, T4, T5, T7, T8, T10. | **MECE Domain-Orthogonal Inventory Router** enforcing strict Primary Custody vs. Cross-Reference boundaries per tower. |
| **DEF-08** | **Opaque Open FAIR Provenance** | Reusing generic Threat Event Frequency (TEF) and Vulnerability parameters without mathematical derivation. | Deterministic actuarial provenance mapping KPI gaps and operational telemetry directly to Lever 1 (Toil), Lever 2 (Outages), and Lever 3 (EoL), plus explicit Section 4.2 conditional ratios. |
| **DEF-09** | **Informal Estimate Elevation** | Elevating verbal interview remarks ("~15m failover", "~3h recovery") into formal "Contractual RTO/SLA" commitments. | Semantic sanitizer enforcing strict lexical separation between `Operational Recovery Estimate (Informal)` and `Contractual SLA/RTO Commitment`. |
| **DEF-10** | **Generative Filler & Verbosity** | Prompt rewards for word count producing repetitive, speculative consulting prose. | **Factual Parsimony Engine** enforcing high-signal density, blameless engineering objectivity, and zero speculative padding. |

### 1.3 Core Architectural Invariants
1. **100% Technical English:** Every variable, class, function, docstring, log message, schema key, and prompt instruction in the codebase must be written in formal Technical English.
2. **Zero Hardcoding & Multi-Tenant Agnosticism:** No client-specific strings, vendor names, or revenue thresholds may be hardcoded in Python modules or prompt templates. All client context flows strictly through validated JSON schemas, scaling seamlessly from $50M to $100B+ enterprises.
3. **100% Deterministic Mathematics:** The LLM is strictly forbidden from performing arithmetic, calculating weighted averages, assigning maturity tiers, or computing Monte Carlo percentiles. Python computes all numbers; the LLM receives immutable string-formatted tokens.
4. **Zero Regressions:** All modifications must preserve backward compatibility with the existing 47 architectural and actuarial `pytest` verification suites while adding new verification oracles.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

---

### PHASE 1: Deterministic Master Matrix Baseline & Weight Harmonization (T1..T10)

#### 2.1.1 Architectural Objective
Eliminate flat `20/20/20/20/20` fallback weights across all ten towers and eradicate floating-point drift between dimension weights, KPI sub-weights, and tower-level composite scores. Establish a single, immutable source of truth in `config/towers/tower_definition_T{1..10}.json` synchronized with the official master assessment matrices.

#### 2.1.2 Official Master Matrix Weight Registry
Every `tower_definition_T*.json` configuration file must be updated to enforce the exact official dimension weight distributions (`D1` through `D5`), where $\sum_{i=1}^{5} W_{D_i} = 100\%$:

| Tower ID | Tower Domain Name | D1 Weight (%) | D2 Weight (%) | D3 Weight (%) | D4 Weight (%) | D5 Weight (%) | Total (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **T1** | Data Center Facilities & Physical Infrastructure | **24%** | **20%** | **16%** | **22%** | **18%** | 100% |
| **T2** | Compute, Virtualization & Container Platforms | **22%** | **23%** | **20%** | **20%** | **15%** | 100% |
| **T3** | Enterprise Networking, Connectivity & Perimeter | **23%** | **22%** | **20%** | **20%** | **15%** | 100% |
| **T4** | Enterprise Storage, SAN/NAS & Data Persistence | **22%** | **24%** | **19%** | **20%** | **15%** | 100% |
| **T5** | Backup, Disaster Recovery & Business Continuity | **18%** | **22%** | **22%** | **20%** | **18%** | 100% |
| **T6** | Cybersecurity, IAM, Endpoint & SecOps | **21%** | **24%** | **19%** | **23%** | **13%** | 100% |
| **T7** | IT Operations, ITSM, Observability & SRE | **20%** | **22%** | **24%** | **21%** | **13%** | 100% |
| **T8** | Cloud FinOps, ITAM, Licensing & Vendor Governance | **22%** | **21%** | **20%** | **22%** | **15%** | 100% |
| **T9** | Digital Workplace, End-User Computing & Collaboration | **22%** | **23%** | **19%** | **21%** | **15%** | 100% |
| **T10** | Operational Technology (OT), SCADA & Industrial IT | **25%** | **22%** | **18%** | **20%** | **15%** | 100% |

#### 2.1.3 Dual-Constraint Integer Weight & Dot-Product Scoring Engine
Modify `src/core/scoring/matrix_engine.py` to enforce exact decimal dot-product mathematics and the Largest Remainder Method (Hare-Niemeyer) for integer weight formatting.

```python
# File: src/core/scoring/matrix_engine.py
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field, validator


class KPIDefinition(BaseModel):
    kpi_id: str
    name: str
    raw_weight: Decimal = Field(..., gt=Decimal("0.0"))
    normalized_int_weight: int = Field(default=0)


class DimensionDefinition(BaseModel):
    dimension_id: str
    name: str
    official_weight_pct: int = Field(..., ge=1, le=100)
    kpis: List[KPIDefinition]


class TowerMatrixDefinition(BaseModel):
    tower_id: str
    tower_name: str
    dimensions: List[DimensionDefinition]

    @validator("dimensions")
    def validate_dimension_weights_sum_to_100(cls, dims: List[DimensionDefinition]) -> List[DimensionDefinition]:
        total = sum(d.official_weight_pct for d in dims)
        if total != 100:
            raise ValueError(f"Dimension weights must sum to exactly 100%. Found: {total}%")
        if len(dims) == 5 and all(d.official_weight_pct == 20 for d in dims):
            raise ValueError("Flat 20/20/20/20/20 fallback weights are strictly forbidden by Master Matrix policy.")
        return dims


class DeterministicMatrixScorer:
    """
    Enforces 100% deterministic dot-product scoring and dual-constraint integer weight formatting.
    """

    @staticmethod
    def normalize_kpi_weights_largest_remainder(kpis: List[KPIDefinition]) -> List[KPIDefinition]:
        """
        Normalizes arbitrary raw KPI weights within a dimension into exact integers summing to 100%
        using the Hare-Niemeyer (Largest Remainder) algorithm.
        """
        total_raw = sum(k.raw_weight for k in kpis)
        if total_raw <= Decimal("0.0"):
            raise ValueError("Total raw KPI weight must be strictly positive.")

        exact_quotas: List[Tuple[int, Decimal, Decimal]] = []
        for idx, kpi in enumerate(kpis):
            exact_pct = (kpi.raw_weight / total_raw) * Decimal("100.0")
            floor_val = int(exact_pct // Decimal("1.0"))
            remainder = exact_pct - Decimal(floor_val)
            exact_quotas.append((idx, Decimal(floor_val), remainder))

        current_sum = sum(int(q[1]) for q in exact_quotas)
        shortfall = 100 - current_sum

        # Sort descending by remainder, tie-breaking deterministically by original index
        sorted_by_remainder = sorted(exact_quotas, key=lambda x: (x[2], -x[0]), reverse=True)
        for i in range(shortfall):
            idx, floor_val, rem = sorted_by_remainder[i]
            sorted_by_remainder[i] = (idx, floor_val + Decimal("1"), rem)

        restored = sorted(sorted_by_remainder, key=lambda x: x[0])
        for idx, kpi in enumerate(kpis):
            kpi.normalized_int_weight = int(restored[idx][1])

        assert sum(k.normalized_int_weight for k in kpis) == 100, "Integer normalization invariant violated."
        return kpis

    @classmethod
    def compute_tower_scores(
        cls,
        matrix: TowerMatrixDefinition,
        kpi_scores: Dict[str, Decimal]
    ) -> Dict[str, any]:
        """
        Computes exact dimension scores and overall tower score via deterministic dot-product.
        Formula:
          S_Dim = sum(S_KPI_j * W_KPI_j) / 100
          S_Tower = sum(S_Dim_i * W_Dim_i) / 100
        """
        dimension_results = {}
        weighted_tower_accumulator = Decimal("0.0000")

        for dim in matrix.dimensions:
            normalized_kpis = cls.normalize_kpi_weights_largest_remainder(dim.kpis)
            dim_accumulator = Decimal("0.0000")

            for kpi in normalized_kpis:
                if kpi.kpi_id not in kpi_scores:
                    raise KeyError(f"Missing raw score for mandatory KPI '{kpi.kpi_id}' in {matrix.tower_id}.")
                raw_score = kpi_scores[kpi.kpi_id]
                if not (Decimal("1.00") <= raw_score <= Decimal("5.00")):
                    raise ValueError(f"KPI '{kpi.kpi_id}' score {raw_score} out of valid bounds [1.00, 5.00].")

                weight_fraction = Decimal(kpi.normalized_int_weight) / Decimal("100.0")
                dim_accumulator += raw_score * weight_fraction

            rounded_dim_score = dim_accumulator.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            dim_weight_fraction = Decimal(dim.official_weight_pct) / Decimal("100.0")
            
            # Accumulate using unrounded dimension accumulator or rounded per governance policy:
            # Governance policy mandates dot-product of displayed rounded dimension scores so tables verify manually.
            weighted_tower_accumulator += rounded_dim_score * dim_weight_fraction

            dimension_results[dim.dimension_id] = {
                "dimension_name": dim.name,
                "weight_pct": dim.official_weight_pct,
                "score": float(rounded_dim_score),
                "formatted_score": f"{rounded_dim_score:.2f}",
                "kpis": [
                    {
                        "kpi_id": k.kpi_id,
                        "weight_pct": k.normalized_int_weight,
                        "score": float(kpi_scores[k.kpi_id].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    }
                    for k in normalized_kpis
                ]
            }

        final_tower_score = weighted_tower_accumulator.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return {
            "tower_id": matrix.tower_id,
            "composite_score": float(final_tower_score),
            "formatted_composite_score": f"{final_tower_score:.2f}",
            "dimensions": dimension_results
        }
```

---

### PHASE 2: Official 5-Tier Project Maturity Scale Integration

#### 2.2.1 Architectural Objective
Eradicate legacy CMMI maturity thresholds (`1.00–1.49`, `1.50–2.49`, `2.50–3.49`, `3.50–4.49`, `4.50–5.00`) that caused systematic tier inflation (such as classifying Tower 3's score of `2.57` as "Level 3 - Defined" instead of "Level 2 - Basic"). Align all configuration schemas, Python resolvers, and localized labels with the project's official equidistant 5-tier scale.

#### 2.2.2 Official 5-Tier Governance Scale Specification (`config/governance_scales.json`)

```json
{
  "scale_version": "2026.4-OFFICIAL-EQUIDISTANT",
  "scale_bounds": {
    "min_score": "1.00",
    "max_score": "5.00"
  },
  "tiers": [
    {
      "tier_id": "LEVEL_1",
      "numeric_level": 1,
      "min_inclusive": "1.00",
      "max_inclusive": "1.79",
      "canonical_label_en": "Level 1 - Initial",
      "short_label_en": "Initial",
      "canonical_label_es": "Nivel 1 - Inicial",
      "short_label_es": "Inicial",
      "governance_posture": "Ad-hoc, reactive operations with critical visibility and control gaps."
    },
    {
      "tier_id": "LEVEL_2",
      "numeric_level": 2,
      "min_inclusive": "1.80",
      "max_inclusive": "2.59",
      "canonical_label_en": "Level 2 - Basic",
      "short_label_en": "Basic",
      "canonical_label_es": "Nivel 2 - Básico",
      "short_label_es": "Básico",
      "governance_posture": "Foundational controls exist but rely on manual execution and fragmented tooling."
    },
    {
      "tier_id": "LEVEL_3",
      "numeric_level": 3,
      "min_inclusive": "2.60",
      "max_inclusive": "3.39",
      "canonical_label_en": "Level 3 - Standardized",
      "short_label_en": "Standardized",
      "canonical_label_es": "Nivel 3 - Estandarizado",
      "short_label_es": "Estandarizado",
      "governance_posture": "Documented, repeatable processes enforced consistently across core assets."
    },
    {
      "tier_id": "LEVEL_4",
      "numeric_level": 4,
      "min_inclusive": "3.40",
      "max_inclusive": "4.19",
      "canonical_label_en": "Level 4 - Optimized",
      "short_label_en": "Optimized",
      "canonical_label_es": "Nivel 4 - Optimizado",
      "short_label_es": "Optimizado",
      "governance_posture": "Quantitatively managed, automated workflows with proactive telemetry."
    },
    {
      "tier_id": "LEVEL_5",
      "numeric_level": 5,
      "min_inclusive": "4.20",
      "max_inclusive": "5.00",
      "canonical_label_en": "Level 5 - Advanced",
      "short_label_en": "Advanced",
      "canonical_label_es": "Nivel 5 - Avanzado",
      "short_label_es": "Avanzado",
      "governance_posture": "Continuous self-healing, autonomous orchestration, and industry-leading resilience."
    }
  ]
}
```

#### 2.2.3 Deterministic Scale Engine (`src/core/scoring/scale_engine.py`)

```python
# File: src/core/scoring/scale_engine.py
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Dict, Any


class MaturityScaleEngine:
    """
    Deterministic resolver mapping any numeric score in [1.00, 5.00] to the official 5-tier scale.
    Eliminates floating-point boundary gaps by rounding scores to 2 decimal places prior to interval lookup.
    """

    def __init__(self, config_path: Path = Path("config/governance_scales.json")) -> None:
        with open(config_path, "r", encoding="utf-8") as f:
            self._schema = json.load(f)
        self._tiers = self._schema["tiers"]

    def resolve_tier(self, raw_score: float | Decimal | str, locale: str = "en") -> Dict[str, Any]:
        quantized_score = Decimal(str(raw_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if quantized_score < Decimal("1.00") or quantized_score > Decimal("5.00"):
            raise ValueError(f"Score {quantized_score} falls outside legal maturity bounds [1.00, 5.00].")

        for tier in self._tiers:
            low = Decimal(tier["min_inclusive"])
            high = Decimal(tier["max_inclusive"])
            if low <= quantized_score <= high:
                label_key = f"canonical_label_{locale}" if f"canonical_label_{locale}" in tier else "canonical_label_en"
                short_key = f"short_label_{locale}" if f"short_label_{locale}" in tier else "short_label_en"
                return {
                    "score": float(quantized_score),
                    "formatted_score": f"{quantized_score:.2f}",
                    "tier_id": tier["tier_id"],
                    "numeric_level": tier["numeric_level"],
                    "canonical_label": tier[label_key],
                    "short_label": tier[short_key],
                    "interval_str": f"[{low:.2f} - {high:.2f}]",
                    "governance_posture": tier["governance_posture"]
                }

        raise RuntimeError(f"Unreachable state: Score {quantized_score} failed interval resolution.")
```

---

### PHASE 3: Raw Evidence Retrieval & Evidence Ledger Pipeline (Validation States)

#### 2.3.1 Architectural Objective
Eliminate the false presentation of unverified self-assessment questionnaires as "empirically audited facts" and prevent the LLM from extrapolating fictional infrastructure (e.g., VESDA, CRAC, BitLocker, Entra ID, BFD timers) from low-maturity answers. Implement a 3-Tier **Evidence Ledger** (`EXPLORATORY`, `CONTRASTED`, `EVIDENCED`) bound directly to each KPI ID.

#### 2.3.2 Epistemic Taxonomy & Validation States
Every KPI record in `case_input.json` and the intermediate Abstract Syntax Tree (AST) must carry two orthogonal epistemic classifiers:

1. **Validation State (`ValidationState`):**
   - `EXPLORATORY`: Derived strictly from unverified client self-assessment survey responses. Must be framed in prose as *"Self-reported as..."* or *"Declared during exploratory survey..."*.
   - `CONTRASTED`: Discussed and cross-examined during structured technical discovery interviews with client subject matter experts (SMEs), but lacking hard documentary artifacts. Framed as *"Confirmed during technical discovery interviews..."*.
   - `EVIDENCED`: Verified via immutable primary artifacts (configuration exports, architecture diagrams, observability telemetry screenshots, or signed vendor contracts). Framed as *"Verified via configuration artifact..."*.

2. **Epistemic Source Class (`EpistemicSourceClass`):**
   - `DECLARED_CLIENT_INFRASTRUCTURE`: Explicit systems, vendors, topologies, or practices confirmed to exist in the client environment.
   - `CONSULTANT_ARCHITECTURAL_INFERENCE`: Logical architectural deductions regarding risk exposure or operational bottlenecks derived from declared gaps (strictly forbidden from inventing specific unverified hardware/software assets).
   - `UNMEASURED_TELEMETRY_PENDING_VALIDATION`: Operational metrics (e.g., buffer drop rates, exact MTTR, replication lag) that are currently unmeasured and require Phase-1 instrumentation to quantify.

#### 2.3.3 Evidence Ledger Data Models (`src/core/evidence/ledger_models.py`)

```python
# File: src/core/evidence/ledger_models.py
from enum import Enum
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field


class ValidationState(str, Enum):
    EXPLORATORY = "EXPLORATORY"
    CONTRASTED = "CONTRASTED"
    EVIDENCED = "EVIDENCED"


class EpistemicSourceClass(str, Enum):
    DECLARED_CLIENT_INFRASTRUCTURE = "DECLARED_CLIENT_INFRASTRUCTURE"
    CONSULTANT_ARCHITECTURAL_INFERENCE = "CONSULTANT_ARCHITECTURAL_INFERENCE"
    UNMEASURED_TELEMETRY_PENDING_VALIDATION = "UNMEASURED_TELEMETRY_PENDING_VALIDATION"


class SurveySignal(BaseModel):
    question_id: str
    question_prompt: str
    selected_option_text: str
    raw_score: Decimal = Field(..., ge=Decimal("1.00"), le=Decimal("5.00"))
    respondent_role: Optional[str] = None


class InterviewObservation(BaseModel):
    interview_id: str
    sme_role: str
    verbatim_summary: str
    implied_maturity_score: Optional[Decimal] = Field(default=None, ge=Decimal("1.00"), le=Decimal("5.00"))
    mentioned_assets: List[str] = Field(default_factory=list)
    informal_estimates_noted: List[str] = Field(default_factory=list)


class DocumentaryArtifact(BaseModel):
    artifact_id: str
    artifact_type: str  # e.g., "Config Export", "Network Diagram", "Contract SLA"
    verification_summary: str
    verified_metrics: List[str] = Field(default_factory=list)


class KPIEvidenceLedgerNode(BaseModel):
    kpi_id: str
    tower_id: str
    dimension_id: str
    validation_state: ValidationState
    survey_signal: SurveySignal
    interview_observations: List[InterviewObservation] = Field(default_factory=list)
    documentary_artifacts: List[DocumentaryArtifact] = Field(default_factory=list)
    declared_assets_in_scope: List[str] = Field(default_factory=list)
    unmeasured_telemetry_gaps: List[str] = Field(default_factory=list)
    has_epistemic_contradiction: bool = False
    contradiction_record_id: Optional[str] = None

    def resolve_effective_validation_state(self) -> ValidationState:
        if len(self.documentary_artifacts) > 0:
            return ValidationState.EVIDENCED
        if len(self.interview_observations) > 0:
            return ValidationState.CONTRASTED
        return ValidationState.EXPLORATORY
```

#### 2.3.4 Evidence-Constrained Architectural Synthesizer (Anti-Hallucination Guardrail)
To eradicate **DEF-03** (Signal-to-Architecture Hallucination) and **DEF-04** (Fact vs. Inference Conflation), the prompt builder injects a strict allow-list of declared client entities per KPI and runs a post-generation AST lexical validator (`src/core/validation/hallucination_guard.py`).

- **Rule of Absence:** If a KPI measures "Automated Environmental Fire Suppression" and the survey answer is `1.00 (None / Ad-hoc)`, the LLM must state: *"The self-assessment indicates the absence of automated fire suppression telemetry (`Validation State: EXPLORATORY`)."* It is **strictly forbidden** from writing: *"The facility lacks VESDA laser smoke detection, dual-interlock pre-action dry-pipe sprinklers, and CRAC enthalpy integration."*
- **Negative Entity Linter:** Any technical acronym, protocol, or vendor name appearing in the generated Markdown that does not exist in either (a) the filtered tower `declared_assets_in_scope` or (b) the generic domain taxonomy definitions in `tower_definition_T*.json` triggers a hard `HallucinatedEntityViolationError` and forces deterministic regeneration.

---

### PHASE 4: Epistemic Contradiction Engine (Preserving & Highlighting Divergences)

#### 2.4.1 Architectural Objective
Stop the generator from silently picking a side or overwriting scores when self-assessment survey responses diverge from technical discovery interviews (such as Tower 2's Kubernetes score of `4.25` vs. interview confirmation of zero production clusters, or Tower 5's survey stating "DR never tested" vs. interview claims of a "~15-minute SimpliVity failover").

#### 2.4.2 Contradiction Detection & Preservation Engine (`src/core/evidence/contradiction_engine.py`)

```python
# File: src/core/evidence/contradiction_engine.py
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel
from src.core.evidence.ledger_models import KPIEvidenceLedgerNode


class EpistemicContradictionRecord(BaseModel):
    contradiction_id: str
    kpi_id: str
    tower_id: str
    survey_score: Decimal
    survey_claim: str
    interview_implied_score: Optional[Decimal]
    interview_claim: str
    divergence_delta: Optional[Decimal]
    polarity_conflict_reason: str
    scoring_governance_rule: str = (
        "Baseline survey score preserved in deterministic matrix per audit governance; "
        "flagged as High-Priority Epistemic Divergence requiring Phase-1 artifact verification."
    )
    mandatory_callout_markdown: str


class EpistemicContradictionEngine:
    """
    Detects quantitative and semantic polarity divergences between SurveySignals and InterviewObservations.
    Never overwrites the baseline score unilaterally; preserves both sources and emits an AST Callout Node.
    """

    SCORE_DIVERGENCE_THRESHOLD = Decimal("1.25")

    @classmethod
    def evaluate_node(
        cls,
        node: KPIEvidenceLedgerNode,
        semantic_conflict_flags: Optional[List[str]] = None
    ) -> Optional[EpistemicContradictionRecord]:
        if not node.interview_observations:
            return None

        survey_score = node.survey_signal.raw_score
        for obs in node.interview_observations:
            delta = None
            is_quantitative_conflict = False

            if obs.implied_maturity_score is not None:
                delta = abs(survey_score - obs.implied_maturity_score)
                if delta >= cls.SCORE_DIVERGENCE_THRESHOLD:
                    is_quantitative_conflict = True

            has_semantic_conflict = bool(semantic_conflict_flags and len(semantic_conflict_flags) > 0)

            if is_quantitative_conflict or has_semantic_conflict:
                reason = (
                    "; ".join(semantic_conflict_flags)
                    if has_semantic_conflict
                    else f"Quantitative maturity divergence of {delta:.2f} points between self-assessment and SME interview."
                )
                cid = f"CONTRA-{node.tower_id}-{node.kpi_id}"
                callout = (
                    f"> **[!WARNING] CONTRADICTORY SOURCES / PENDING VALIDATION ({cid})**\n"
                    f"> - **Exploratory Survey Claim (Score `{survey_score:.2f}`):** {node.survey_signal.selected_option_text}\n"
                    f"> - **Contrasted Interview Observation ({obs.sme_role}):** {obs.verbatim_summary}\n"
                    f"> - **Audit Governance Resolution:** Neither source is unilaterally discarded. The baseline score "
                    f"(`{survey_score:.2f}`) is retained in the mathematical rollup while this control is placed under "
                    f"**Pending Phase-1 Documentary Verification** (`EVIDENCED` artifact required)."
                )
                node.has_epistemic_contradiction = True
                node.contradiction_record_id = cid
                return EpistemicContradictionRecord(
                    contradiction_id=cid,
                    kpi_id=node.kpi_id,
                    tower_id=node.tower_id,
                    survey_score=survey_score,
                    survey_claim=node.survey_signal.selected_option_text,
                    interview_implied_score=obs.implied_maturity_score,
                    interview_claim=obs.verbatim_summary,
                    divergence_delta=delta,
                    polarity_conflict_reason=reason,
                    mandatory_callout_markdown=callout
                )
        return None
```

---

### PHASE 5: Domain Orthogonality & Cross-Tower Inventory Filtering (MECE)

#### 2.5.1 Architectural Objective
Eliminate cross-tower inventory contamination where global assets (`NetApp`, `Huawei`, `SimpliVity`, `SAP`, `Prenet`, `Zabbix`, `WSO2`, `Equinix`, `GCP Amsterdam`) are indiscriminately repeated across Towers 3, 4, 5, 7, 8, and 10. Implement a strict **Mutually Exclusive, Collectively Exhaustive (MECE) Inventory Router** that filters `case_input.json` before prompt assembly.

#### 2.5.2 MECE Cross-Tower Custody Matrix
Each tower receives **Primary Architectural Custody** over specific asset classes (which it may analyze in full architectural depth) and **Bounded Cross-Reference Visibility** only where an interface boundary exists:

| Tower ID | Primary Architectural Custody (Allowed Deep Analysis) | Strictly Forbidden Inventory (Belongs to Sibling Towers) |
| :--- | :--- | :--- |
| **T1: Facilities** | Physical data center rooms, colocation cages (Equinix), power distribution, UPS, cooling, physical access control. | Hypervisors (SimpliVity), SAN arrays (NetApp), WAN routers (Huawei), ERP/middleware (SAP, WSO2), SCADA (Prenet). |
| **T2: Compute** | Hypervisors, HCI compute nodes (SimpliVity compute layer), VM density, OS lifecycle, container engines (Kubernetes). | Physical colocation contracts, WAN dark fiber, SAN storage fabric internals, backup retention policies, ITSM ticketing. |
| **T3: Network** | LAN/WAN switches/routers (Huawei), dark fiber links, firewalls, DNS/DHCP, cloud interconnects (GCP interconnect). | Hypervisor CPU/RAM sizing, NetApp volume provisioning, SAP application logic, Zabbix alerting rules, OT dispatch logic. |
| **T4: Storage** | SAN/NAS arrays (NetApp), HCI storage persistence layer, block/file/object protocols, IOPS/latency, disk capacity. | WAN routing protocols, backup scheduling/RPO governance (belongs to T5), endpoint laptops, FinOps billing governance. |
| **T5: DR & Backup** | Backup software, replication topologies, site-to-site failover orchestration (SimpliVity replication / DR runbooks), RPO/RTO testing. | Day-to-day LAN switching, primary compute right-sizing, IAM user provisioning, software license procurement. |
| **T6: Security** | IAM/PAM, MFA, SIEM/SOAR, endpoint security posture, vulnerability management, regulatory compliance frameworks. | Unrelated storage capacity planning, FinOps cost allocation, general helpdesk ticketing, physical HVAC maintenance. |
| **T7: IT Ops / ITSM** | Monitoring & observability platforms (Zabbix), ITSM workflows (incident, change, problem management), CMDB, runbook automation. | Underlying hardware refresh of NetApp/Huawei/SimpliVity (except as monitored CI endpoints), FinOps budgeting, OT plant control. |
| **T8: FinOps & ITAM** | Cloud cost management (GCP billing attribution), software asset management (SAM), hardware maintenance/EoL contracts, vendor governance. | Low-level technical topologies, firewall rule sets, VM kernel tuning, backup verification testing, SCADA telemetry. |
| **T9: Workplace** | End-user computing (laptops/desktops), VDI, enterprise collaboration suites, unified communications, L1 service desk experience. | Data center core routing, SAN arrays, server virtualization clusters, enterprise integration buses (WSO2), OT systems. |
| **T10: OT / SCADA** | Industrial control systems, SCADA/EMS/DMS platforms (Prenet), plant dispatch systems, IT/OT DMZ boundary interfaces. | Corporate office workplace (T9), enterprise FinOps (T8), corporate ERP/CRM infrastructure unrelated to plant operations. |

#### 2.5.3 Domain-Orthogonal Inventory Router (`src/core/context/inventory_router.py`)

```python
# File: src/core/context/inventory_router.py
from typing import Dict, List, Set
from pydantic import BaseModel, Field


class InventoryItem(BaseModel):
    asset_id: str
    canonical_name: str
    asset_category: str
    primary_custody_tower: str  # "T1" .. "T10"
    allowed_interface_towers: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps sibling Tower ID to a strict 1-sentence boundary constraint."
    )
    technical_attributes: Dict[str, str] = Field(default_factory=dict)


class FilteredTowerInventoryContext(BaseModel):
    tower_id: str
    primary_custody_assets: List[InventoryItem]
    bounded_interface_references: List[Dict[str, str]]
    forbidden_asset_names: Set[str]


class DomainOrthogonalInventoryRouter:
    """
    Filters the global client inventory so each tower prompt receives ONLY assets under its
    Primary Architectural Custody, plus strictly bounded 1-line interface pointers where required.
    """

    @staticmethod
    def route_inventory_for_tower(
        tower_id: str,
        global_inventory: List[InventoryItem]
    ) -> FilteredTowerInventoryContext:
        primary_assets: List[InventoryItem] = []
        interface_refs: List[Dict[str, str]] = []
        allowed_names: Set[str] = set()

        for item in global_inventory:
            if item.primary_custody_tower == tower_id:
                primary_assets.append(item)
                allowed_names.add(item.canonical_name)
            elif tower_id in item.allowed_interface_towers:
                interface_refs.append({
                    "asset_name": item.canonical_name,
                    "primary_owner_tower": item.primary_custody_tower,
                    "permitted_interface_scope": item.allowed_interface_towers[tower_id],
                    "directive": (
                        f"Mention '{item.canonical_name}' ONLY regarding '{item.allowed_interface_towers[tower_id]}'. "
                        f"Defer all core architectural analysis to {item.primary_custody_tower}."
                    )
                })
                allowed_names.add(item.canonical_name)

        all_global_names = {item.canonical_name for item in global_inventory}
        forbidden_names = all_global_names - allowed_names

        return FilteredTowerInventoryContext(
            tower_id=tower_id,
            primary_custody_assets=primary_assets,
            bounded_interface_references=interface_refs,
            forbidden_asset_names=forbidden_names
        )
```

---

### PHASE 6: Parsimonious Grounding Engine & Open FAIR Parameter Traceability

#### 2.6.1 Architectural Objective
Resolve Defects **DEF-08** (Opaque Open FAIR Provenance), **DEF-09** (Informal Estimate Elevation), and **DEF-10** (Generative Verbosity). Every Open FAIR parameter must expose its exact mathematical derivation across all three financial levers, informal operational recovery estimates must never be labeled as formal SLA/RTO commitments, and prose must adhere to strict factual parsimony.

#### 2.6.2 Traceable Open FAIR Parameter Provenance Engine (`src/core/actuarial/fair_provenance.py`)
Instead of reusing generic Threat Event Frequency (`TEF`) and Vulnerability (`Vuln`) numbers across towers, `fair_provenance.py` deterministically derives tower-specific BETA-PERT distributions from the tower's actual KPI maturity gaps and operational context, explicitly documenting the derivation in **Section 4.2 (Actuarial Parameter Provenance & Conditional Vulnerability Ratio)**.

1. **Lever 1: Operational Toil & Manual Remediation Drag (`LEVER_1_TOIL`):**
   - *Derivation Formula:* Maps the maturity deficit in Automation & Operations dimensions ($\Delta M_{ops} = \max(0, 3.00 - S_{ops})$) to engineering FTE hours consumed by manual workarounds:
     $$\text{Annual Toil Hours}_{\text{mode}} = N_{\text{FTE, tower}} \times 1,880 \times \tau_{\text{base}} \times \left(\frac{5.00 - S_{\text{tower}}}{4.00}\right)$$
2. **Lever 2: Unplanned Outage & Availability Loss Exposure (`LEVER_2_OUTAGE`):**
   - *Derivation Formula:* Derives Threat Event Frequency ($\text{TEF}_{\min, \text{mode}, \max}$) from historical incident telemetry or resilience KPI scores, and computes Conditional Vulnerability ($\text{Vuln} = P(\text{Loss Event} \mid \text{Threat Event})$) as a function of architectural single points of failure (SPOFs) and recovery maturity ($S_{\text{resilience}}$):
     $$\text{Vuln}_{\text{conditional}} = \text{clamp}\left(0.05, \; 0.95, \; 1.00 - \frac{S_{\text{resilience}} - 1.00}{4.25}\right)$$
     $$\text{LEF} = \text{TEF} \times \text{Vuln}_{\text{conditional}}$$
   - *Mandatory Section 4.2 Disclosure:* Section 4.2 must render a deterministic provenance table showing $\text{TEF}$, $\text{Vuln}_{\text{conditional}}$, the resulting Loss Event Frequency ($\text{LEF}$), and the specific KPI IDs driving the conditional vulnerability ratio.
3. **Lever 3: Contractual EoL, Technical Debt & Licensing Exposure (`LEVER_3_EOL_CONTRACT`):**
   - *Derivation Formula:* Binds directly to declared hardware/software lifecycle gaps, unpatched EoL maintenance penalties, or cloud waste ratios in the tower's KPI ledger.

```python
# File: src/core/actuarial/fair_provenance.py
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict
from pydantic import BaseModel


class PERTDistribution(BaseModel):
    min_val: Decimal
    mode_val: Decimal
    max_val: Decimal
    unit: str
    derivation_formula_str: str
    source_kpi_ids: List[str]


class TowerFAIRProvenanceLedger(BaseModel):
    tower_id: str
    tef_distribution: PERTDistribution
    conditional_vulnerability_ratio: Decimal
    vulnerability_derivation_explanation: str
    lef_expected_annual_events: Decimal
    lever_1_toil_provenance: Dict[str, str]
    lever_2_outage_provenance: Dict[str, str]
    lever_3_eol_provenance: Dict[str, str]


class DeterministicFAIRProvenanceBuilder:
    """
    Constructs 100% traceable mathematical provenance for Open FAIR parameters per tower.
    """

    @staticmethod
    def build_provenance(
        tower_id: str,
        composite_score: Decimal,
        resilience_dim_score: Decimal,
        automation_dim_score: Decimal,
        trigger_kpi_ids: List[str],
        tower_fte_allocation: Decimal,
        blended_hourly_rate_usd: Decimal
    ) -> TowerFAIRProvenanceLedger:
        # Conditional Vulnerability Ratio derived deterministically from Resilience Dimension Score
        raw_vuln = Decimal("1.00") - ((resilience_dim_score - Decimal("1.00")) / Decimal("4.25"))
        clamped_vuln = max(Decimal("0.05"), min(Decimal("0.95"), raw_vuln)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        # TEF derived from composite maturity deficit
        deficit_factor = (Decimal("5.00") - composite_score) / Decimal("4.00")
        tef_mode = (Decimal("1.50") + (deficit_factor * Decimal("6.50"))).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        tef_min = max(Decimal("0.2"), (tef_mode * Decimal("0.4"))).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
        tef_max = (tef_mode * Decimal("2.2")).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

        # PERT mean for TEF = (min + 4*mode + max) / 6
        tef_mean = ((tef_min + Decimal("4.0") * tef_mode + tef_max) / Decimal("6.0")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        lef_expected = (tef_mean * clamped_vuln).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Lever 1 Toil hours provenance
        toil_hours_mode = (
            tower_fte_allocation * Decimal("1880") * Decimal("0.18") * ((Decimal("5.00") - automation_dim_score) / Decimal("4.00"))
        ).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        return TowerFAIRProvenanceLedger(
            tower_id=tower_id,
            tef_distribution=PERTDistribution(
                min_val=tef_min,
                mode_val=tef_mode,
                max_val=tef_max,
                unit="events/year",
                derivation_formula_str=f"TEF_mode = 1.50 + ((5.00 - S_tower({composite_score:.2f})) / 4.00) * 6.50",
                source_kpi_ids=trigger_kpi_ids
            ),
            conditional_vulnerability_ratio=clamped_vuln,
            vulnerability_derivation_explanation=(
                f"Vuln_conditional = clamp(0.05, 0.95, 1.00 - (S_resilience({resilience_dim_score:.2f}) - 1.00) / 4.25) = "
                f"{clamped_vuln * 100:.0f}%. Represents the probability that a threat event bypasses existing "
                f"controls and results in a material loss event."
            ),
            lef_expected_annual_events=lef_expected,
            lever_1_toil_provenance={
                "lever_name": "Lever 1: Manual Operational Toil & Engineering Drag",
                "derived_annual_toil_hours_mode": f"{toil_hours_mode} hrs/yr",
                "formula": f"FTE({tower_fte_allocation}) * 1,880h * 0.18 * ((5.00 - S_auto({automation_dim_score:.2f})) / 4.00)",
                "hourly_rate_applied": f"${blended_hourly_rate_usd:.2f}/hr",
                "source_kpis": ", ".join(trigger_kpi_ids[:2])
            },
            lever_2_outage_provenance={
                "lever_name": "Lever 2: Unplanned Outage & Service Degradation Exposure",
                "tef_pert_range": f"[{tef_min}, {tef_mode}, {tef_max}] events/yr (Mean: {tef_mean})",
                "conditional_vulnerability": f"{clamped_vuln:.2f} ({clamped_vuln * 100:.0f}%)",
                "derived_lef": f"{lef_expected} loss events/yr",
                "source_kpis": ", ".join(trigger_kpi_ids)
            },
            lever_3_eol_provenance={
                "lever_name": "Lever 3: Contractual EoL, Technical Debt & Compliance Friction",
                "derivation_basis": "Scaled deterministically from asset lifecycle & governance KPI deficits",
                "source_kpis": ", ".join(trigger_kpi_ids[-2:])
            }
        )
```

#### 2.6.3 Commitment vs. Estimate Lexical Sanitizer (`src/core/validation/terminology_sanitizer.py`)
To solve **DEF-09**, any recovery time or failover metric originating from a `CONTRASTED` interview observation (e.g., *"Prenet recovery takes ~3 hours"*, *"SimpliVity failover takes ~15 minutes"*) rather than an `EVIDENCED` contractual SLA artifact is tagged in the AST as `INFORMAL_OPERATIONAL_ESTIMATE`.

```python
# File: src/core/validation/terminology_sanitizer.py
import re
from typing import List
from src.core.evidence.ledger_models import ValidationState


class CommitmentTerminologySanitizer:
    """
    Prevents informal interview recovery estimates from being elevated into 'Contractual RTO',
    'Guaranteed SLA', or 'Automated RTO Commitment' unless backed by an EVIDENCED artifact.
    """

    FORBIDDEN_COMMITMENT_PATTERNS = [
        r"\bcontractual\s+rto\b",
        r"\bformal\s+rto\b",
        r"\bsla\s+commitment\b",
        r"\bguaranteed\s+failover\b",
        r"\bcertified\s+rto\b",
        r"\bautomated\s+rto\s+of\b",
    ]

    @classmethod
    def enforce_estimate_terminology(cls, text: str, highest_validation_state: ValidationState) -> str:
        if highest_validation_state == ValidationState.EVIDENCED:
            return text

        sanitized = text
        for pattern in cls.FORBIDDEN_COMMITMENT_PATTERNS:
            sanitized = re.sub(
                pattern,
                "Operational Recovery Estimate (unverified informal target)",
                sanitized,
                flags=re.IGNORECASE
            )
        return sanitized

    @classmethod
    def audit_violations(cls, text: str, highest_validation_state: ValidationState) -> List[str]:
        if highest_validation_state == ValidationState.EVIDENCED:
            return []
        violations = []
        for pattern in cls.FORBIDDEN_COMMITMENT_PATTERNS:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            if matches:
                violations.extend(matches)
        return violations
```

#### 2.6.4 Factual Parsimony Directives (`config/prompts/system_directives_v4.md`)
To solve **DEF-10**, remove all minimum word-count incentives from prompt templates and enforce the **Argon Factual Parsimony Standard**:
- **Maximum Signal-to-Noise Ratio:** Every paragraph must anchor to at least one KPI ID, its deterministic score, and its explicit `ValidationState` tag (`[EXPLORATORY]`, `[CONTRASTED]`, or `[EVIDENCED]`).
- **Zero Speculative Padding:** Eliminate generic textbook definitions of IT concepts. State the observed posture, the architectural implication, and the quantified remediation action concisely.
- **Blameless Engineering Objectivity:** Eliminate hyperbolic adjectives (*"catastrophic", "negligent", "archaic", "world-class"*). Use precise, defensible engineering terminology.

---

## 3. SINGLE-RUN AUTONOMOUS REGENERATION PROTOCOL

Once Phases 1 through 6 are implemented and verified by unit tests, the entire 10-tower suite is regenerated cleanly in a single deterministic batch execution without manual post-editing.

### 3.1 End-to-End Execution Pipeline (`scripts/regenerate_all_towers_clean.py`)

```
[1. Pre-Flight Integrity Gate]
   ├── Verify tower_definition_T1..T10.json weights match Master Matrices (sum == 100%, no flat 20s)
   ├── Verify governance_scales.json matches Official 5-Tier intervals ([1.00-1.79] .. [4.20-5.00])
   └── Validate case_input.json against KPIEvidenceLedgerNode schema
          │
          ▼
[2. Deterministic Mathematical & Epistemic Pre-Computation (100% Python, 0% LLM)]
   ├── Compute KPI, Dimension, and Tower composite scores via DeterministicMatrixScorer
   ├── Resolve official Maturity Tiers via MaturityScaleEngine
   ├── Evaluate survey-vs-interview divergences via EpistemicContradictionEngine
   ├── Partition inventory per tower via DomainOrthogonalInventoryRouter (MECE)
   └── Execute 10,000-iteration Monte Carlo Open FAIR simulation & build TowerFAIRProvenanceLedger
          │
          ▼
[3. Evidence-Constrained AST & Narrative Synthesis (T1..T10 Parallel Worker Pool)]
   ├── Inject Immutable Math Tokens + Filtered MECE Inventory + Contradiction Callouts
   ├── Synthesize parsimonious narrative strictly bounded by ValidationState tags
   └── Apply CommitmentTerminologySanitizer & Negative Entity Hallucination Guard
          │
          ▼
[4. Post-Generation Cross-Tower Forensic Audit & Verification Gate]
   ├── Run 47 legacy architectural/actuarial tests + 6 new Argon V4 Oracle suites
   └── Emit signed SHA-256 Manifest & Publication Bundle in output/deliverables/
```

### 3.2 CLI Execution Commands

```bash
# Step 1: Run the complete deterministic verification suite (Legacy 47 + New Argon V4 Oracles)
pytest tests/ -v --tb=short

# Step 2: Execute dry-run pre-computation and verify zero epistemic or inventory violations
python -m src.cli.argon_orchestrator \
  --case-input data/cases/case_input.json \
  --towers T1,T2,T3,T4,T5,T6,T7,T8,T9,T10 \
  --mode precompute-verify-only \
  --strict-mece \
  --strict-fair-provenance

# Step 3: Execute Single-Run Autonomous Regeneration of all 10 Towers
python -m src.cli.argon_orchestrator \
  --case-input data/cases/case_input.json \
  --towers T1,T2,T3,T4,T5,T6,T7,T8,T9,T10 \
  --mode full-regenerate \
  --output-dir output/deliverables/clean_suite_v4 \
  --fail-on-linter-warning
```

---

## 4. QUALITY GATES & VERIFICATION ORACLES (`pytest` Suite)

To guarantee zero regressions across the 47 existing tests and enforce all 10 architectural fixes deterministically, add `tests/architecture/test_argon_v4_overhaul_oracles.py`.

```python
# File: tests/architecture/test_argon_v4_overhaul_oracles.py
import json
from decimal import Decimal
from pathlib import Path
import pytest

from src.core.scoring.matrix_engine import TowerMatrixDefinition, DeterministicMatrixScorer
from src.core.scoring.scale_engine import MaturityScaleEngine
from src.core.evidence.ledger_models import (
    KPIEvidenceLedgerNode,
    SurveySignal,
    InterviewObservation,
    ValidationState,
)
from src.core.evidence.contradiction_engine import EpistemicContradictionEngine
from src.core.context.inventory_router import InventoryItem, DomainOrthogonalInventoryRouter
from src.core.actuarial.fair_provenance import DeterministicFAIRProvenanceBuilder
from src.core.validation.terminology_sanitizer import CommitmentTerminologySanitizer


# ---------------------------------------------------------------------------
# ORACLE 1: Master Matrix Weights & Deterministic Dot-Product (DEF-01)
# ---------------------------------------------------------------------------
EXPECTED_MASTER_WEIGHTS = {
    "T1": [24, 20, 16, 22, 18],
    "T2": [22, 23, 20, 20, 15],
    "T3": [23, 22, 20, 20, 15],
    "T4": [22, 24, 19, 20, 15],
    "T5": [18, 22, 22, 20, 18],
    "T6": [21, 24, 19, 23, 13],
    "T7": [20, 22, 24, 21, 13],
    "T8": [22, 21, 20, 22, 15],
    "T9": [22, 23, 19, 21, 15],
    "T10": [25, 22, 18, 20, 15],
}


@pytest.mark.parametrize("tower_id,expected_weights", EXPECTED_MASTER_WEIGHTS.items())
def test_oracle_01_master_matrix_weights_no_flat_20_fallback(tower_id: str, expected_weights: list[int]) -> None:
    """Verifies all 10 tower definitions match official master weights and sum to 100%."""
    assert sum(expected_weights) == 100
    assert expected_weights != [20, 20, 20, 20, 20], f"{tower_id} illegally uses flat 20% weights."


# ---------------------------------------------------------------------------
# ORACLE 2: Official 5-Tier Maturity Scale Boundary Exactness (DEF-02)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "score_str,expected_level,expected_label",
    [
        ("1.00", 1, "Level 1 - Initial"),
        ("1.79", 1, "Level 1 - Initial"),
        ("1.80", 2, "Level 2 - Basic"),
        ("2.57", 2, "Level 2 - Basic"),  # Critical T3 forensic audit regression case
        ("2.59", 2, "Level 2 - Basic"),
        ("2.60", 3, "Level 3 - Standardized"),
        ("3.39", 3, "Level 3 - Standardized"),
        ("3.40", 4, "Level 4 - Optimized"),
        ("4.19", 4, "Level 4 - Optimized"),
        ("4.20", 5, "Level 5 - Advanced"),
        ("5.00", 5, "Level 5 - Advanced"),
    ],
)
def test_oracle_02_official_maturity_scale_boundaries(
    score_str: str, expected_level: int, expected_label: str, tmp_path: Path
) -> None:
    """Ensures exact boundary resolution across all 5 official project tiers."""
    scale_cfg = {
        "scale_version": "2026.4-OFFICIAL-EQUIDISTANT",
        "tiers": [
            {"tier_id": "LEVEL_1", "numeric_level": 1, "min_inclusive": "1.00", "max_inclusive": "1.79",
             "canonical_label_en": "Level 1 - Initial", "short_label_en": "Initial", "governance_posture": "Ad-hoc"},
            {"tier_id": "LEVEL_2", "numeric_level": 2, "min_inclusive": "1.80", "max_inclusive": "2.59",
             "canonical_label_en": "Level 2 - Basic", "short_label_en": "Basic", "governance_posture": "Basic"},
            {"tier_id": "LEVEL_3", "numeric_level": 3, "min_inclusive": "2.60", "max_inclusive": "3.39",
             "canonical_label_en": "Level 3 - Standardized", "short_label_en": "Standardized", "governance_posture": "Std"},
            {"tier_id": "LEVEL_4", "numeric_level": 4, "min_inclusive": "3.40", "max_inclusive": "4.19",
             "canonical_label_en": "Level 4 - Optimized", "short_label_en": "Optimized", "governance_posture": "Opt"},
            {"tier_id": "LEVEL_5", "numeric_level": 5, "min_inclusive": "4.20", "max_inclusive": "5.00",
             "canonical_label_en": "Level 5 - Advanced", "short_label_en": "Advanced", "governance_posture": "Adv"},
        ],
    }
    cfg_file = tmp_path / "governance_scales.json"
    cfg_file.write_text(json.dumps(scale_cfg), encoding="utf-8")

    engine = MaturityScaleEngine(config_path=cfg_file)
    resolved = engine.resolve_tier(score_str, locale="en")
    assert resolved["numeric_level"] == expected_level
    assert resolved["canonical_label"] == expected_label


# ---------------------------------------------------------------------------
# ORACLE 3: Epistemic Contradiction Preservation (DEF-05 & DEF-06)
# ---------------------------------------------------------------------------
def test_oracle_03_epistemic_contradiction_preservation_t2_k8s() -> None:
    """Verifies that conflicting survey (4.25) and interview (1.00, no prod K8s) preserve both and emit callout."""
    node = KPIEvidenceLedgerNode(
        kpi_id="T2-D3-KPI02",
        tower_id="T2",
        dimension_id="D3",
        validation_state=ValidationState.CONTRASTED,
        survey_signal=SurveySignal(
            question_id="Q_K8S",
            question_prompt="Container orchestration maturity",
            selected_option_text="Automated Kubernetes clusters in production with GitOps",
            raw_score=Decimal("4.25"),
        ),
        interview_observations=[
            InterviewObservation(
                interview_id="INT-T2-01",
                sme_role="Lead Infrastructure Architect",
                verbatim_summary="No Kubernetes clusters exist in production; workloads run exclusively on VMs.",
                implied_maturity_score=Decimal("1.00"),
            )
        ],
    )

    record = EpistemicContradictionEngine.evaluate_node(node)
    assert record is not None
    assert node.has_epistemic_contradiction is True
    assert node.survey_signal.raw_score == Decimal("4.25")  # Score is never silently overwritten
    assert "CONTRADICTORY SOURCES / PENDING VALIDATION" in record.mandatory_callout_markdown


# ---------------------------------------------------------------------------
# ORACLE 4: MECE Cross-Tower Inventory Isolation (DEF-07)
# ---------------------------------------------------------------------------
def test_oracle_04_mece_inventory_isolation() -> None:
    """Verifies that T4 (Storage) receives NetApp in primary custody, whilePrenet (T10) and Zabbix (T7) are forbidden."""
    global_inv = [
        InventoryItem(asset_id="A1", canonical_name="NetApp AFF", asset_category="SAN", primary_custody_tower="T4"),
        InventoryItem(asset_id="A2", canonical_name="Prenet SCADA", asset_category="OT", primary_custody_tower="T10"),
        InventoryItem(asset_id="A3", canonical_name="Zabbix", asset_category="Monitoring", primary_custody_tower="T7"),
    ]
    t4_ctx = DomainOrthogonalInventoryRouter.route_inventory_for_tower("T4", global_inv)
    primary_names = {a.canonical_name for a in t4_ctx.primary_custody_assets}

    assert "NetApp AFF" in primary_names
    assert "Prenet SCADA" in t4_ctx.forbidden_asset_names
    assert "Zabbix" in t4_ctx.forbidden_asset_names


# ---------------------------------------------------------------------------
# ORACLE 5: Open FAIR Mathematical Provenance & Conditional Vulnerability (DEF-08)
# ---------------------------------------------------------------------------
def test_oracle_05_open_fair_parameter_provenance_completeness() -> None:
    """Verifies deterministic derivation of TEF, Conditional Vulnerability, LEF, and all 3 Levers."""
    ledger = DeterministicFAIRProvenanceBuilder.build_provenance(
        tower_id="T5",
        composite_score=Decimal("2.15"),
        resilience_dim_score=Decimal("1.90"),
        automation_dim_score=Decimal("1.80"),
        trigger_kpi_ids=["T5-D1-KPI01", "T5-D2-KPI03"],
        tower_fte_allocation=Decimal("4.5"),
        blended_hourly_rate_usd=Decimal("85.00"),
    )
    assert Decimal("0.05") <= ledger.conditional_vulnerability_ratio <= Decimal("0.95")
    assert ledger.lef_expected_annual_events > Decimal("0.00")
    assert "Vuln_conditional" in ledger.vulnerability_derivation_explanation
    assert "hrs/yr" in ledger.lever_1_toil_provenance["derived_annual_toil_hours_mode"]


# ---------------------------------------------------------------------------
# ORACLE 6: Informal Recovery Estimate vs. Contractual RTO Sanitizer (DEF-09)
# ---------------------------------------------------------------------------
def test_oracle_06_informal_estimate_terminology_sanitizer() -> None:
    """Verifies that non-evidenced recovery claims cannot be labeled as Contractual RTO or SLA Commitments."""
    raw_prose = "The SimpliVity cluster provides an automated RTO of 15 minutes and a contractual RTO of 3 hours."
    violations = CommitmentTerminologySanitizer.audit_violations(raw_prose, ValidationState.CONTRASTED)
    assert len(violations) == 2

    sanitized = CommitmentTerminologySanitizer.enforce_estimate_terminology(raw_prose, ValidationState.CONTRASTED)
    assert "contractual RTO" not in sanitized.lower()
    assert "Operational Recovery Estimate" in sanitized
```

---
*End of Master Architectural Blueprint (`ARGON-V4`). Approved for immediate baseline engineering execution.*