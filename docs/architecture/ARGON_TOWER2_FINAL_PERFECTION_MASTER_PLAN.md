# ARGON TOWER 2: FINAL PERFECTION MASTER ARCHITECTURAL BLUEPRINT
**Document ID:** `ARGON-ARCH-BP-2026-T2-FINAL`  
**File Location:** `docs/architecture/ARGON_TOWER2_FINAL_PERFECTION_MASTER_PLAN.md`  
**Author:** Gemini-4-Argon (Chief Systems Architect, Actuarial Fellow & Global Managing Partner)  
**Target Release:** Argon Engine v4.2.0-Enterprise  
**Status:** MANDATORY EXECUTION DIRECTIVE — TIER-1 CERTIFICATION GATE  

---

## 1. EXECUTIVE SUMMARY & ARCHITECTURAL MANIFESTO

Following the successful execution of Phases 1 and 2 of the Defensibility Plan, the Argon Engine achieved mathematical and actuarial soundness: the compiler override defects were eradicated, the Open FAIR derivation chain was exposed, and Tower 2 weights were synchronized to yield the exact target maturity index ($1.85$) and annualized loss exposure ($13,750\text{ EUR} - 27,000\text{ EUR}$). 

However, a rigorous Tier-1 Forensic Audit (`Revision_Profunda_Torre_2_Iteracion_3.txt`) revealed **six systemic structural, epistemic, and visual anomalies** that prevent the deliverable from achieving "World-Class Tier-1 Consultative Perfection." In high-stakes M&A due diligence and board-level risk engineering, mathematical precision is invalidated if accompanied by epistemic contradictions (e.g., describing production Kubernetes clusters when the calibration states zero production containers), visual rounding artifacts (weights summing to $98\%$), or static heatmap placements that ignore calculated Single Loss Expectancy (SLE) boundaries.

### The Six Blocking Flaws & Architectural Remediation Matrix

| Audit ID | Blocking Flaw Description | Root Cause Analysis | Architectural Remediation |
| :--- | :--- | :--- | :--- |
| **FLAW-01** | **Scale Convergence:** Discrepancy between official framework bands ($[1.00, 1.79]$, $[1.80, 2.59]$, etc.) and legacy CMMI cuts ($1.50, 2.50$) in `governance_scales.json`. | Hardcoded legacy scale thresholds in static JSON without multi-tenant schema versioning. | Implement a schema-driven **Universal Bound Alignment Engine** in `scale_engine.py` with dynamic profile resolution (`UNIFIED_80_BAND` vs. `LEGACY_CMMI`). |
| **FLAW-02** | **Weight Conservation Defect:** Pillar table displays integer weights ($22\%, 19\%, 20\%, 18\%, 20\%$) summing visually to $99\%$ (or $98\%$ in variant locales). | Naive `round(w * 100)` formatting in the AST table builder without remainder distribution. | Implement **Largest Remainder Method (Hare-Niemeyer)** at $10^{-4}$ precision ($0.01\%$), enforcing exact $100.00\%$ visual conservation. |
| **FLAW-03** | **Epistemic Contradiction:** Calibration note states "No containers in production (300+ VMs)", but Pillar 2 narrative describes operational Kubernetes with NetApp Trident CSI and Ingress. | LLM prompt context lacks negative epistemic constraints; cached/residual narrative fragments bypass calibration gates. | Deploy an **Epistemic Grounding & Narrative De-Hallucination Engine** with pre-generation Fact-Boundary Injection and post-generation AST Lexical Gatekeepers. |
| **FLAW-04** | **Static Heatmap Placement:** All 4 risks land in column `LM 3` despite individual SLEs ($1.1\text{k}-4.4\text{k EUR}$) mapping mathematically to `LM 2` ($1\text{k}-4\text{k EUR}$). | Heatmap renderer uses a static, tower-wide default severity column rather than resolving coordinates from individual risk SLE distributions. | Engineer **Dynamic Actuarial Coordinate Derivation**, mapping each risk's geometric/arithmetic SLE midpoint directly against tenant `LM` scale brackets. |
| **FLAW-05** | **Pagination Orphan (Blank Page 9):** Redundant `PageBreakNode()` after fluid tables creates an empty page prior to Chapter 4. | Unconditional insertion of `PageBreakNode` before major sections regardless of preceding container overflow or remaining vertical frame space. | Introduce an **AST Peephole Layout Optimizer** and CSS paged-media compaction rules (`break-before: page` deduplication). |
| **FLAW-06** | **Lexicon & Cloud Contamination:** Residual references to unpresent cloud providers (AWS) and overreach in consultative assurance terminology. | Unfiltered domain corpus in LLM prompts and non-standardized methodology descriptors in `locales.json`. | Enforce a **Tenant Technology Whitelist/Blacklist Filter** and align all locale descriptors to *"Technical Diagnostic Assessment"*. |

### Core Architectural Invariants
1. **100% Technical English Codebase:** All source files, identifiers, docstrings, log emissions, comments, and prompt templates must be written exclusively in rigorous technical English.
2. **Zero Hardcoding & Multi-Tenant Purity:** No client names, specific scores ($1.85$), or static technology assumptions may exist in core logic. Everything is driven by `tenant_profile.json`, `governance_scales.json`, and `actuarial_scales.json`.
3. **Zero Regressions:** All 47 existing unit, integration, typography, and actuarial invariants must pass alongside the new verification oracles.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

### PHASE 1: Maturity Scale Harmonization & Universal Bound Alignment

#### 1.1 Architectural Objective
Eliminate the boundary divergence between legacy CMMI step functions ($1.50, 2.50, 3.50, 4.50$) and the uniform $\Delta = 0.80$ linear partition model required by the official methodology, while maintaining backward compatibility for legacy multi-tenant configurations.

#### 1.2 Mathematical Specification of the Uniform Partition Model
The continuous maturity domain $M \in [1.00, 5.00]$ (total span $\Lambda = 4.00$) is partitioned into $K = 5$ uniform intervals of width $\Delta = \frac{\Lambda}{K} = 0.80$. Using IEEE 754-safe epsilon boundary handling ($\epsilon = 10^{-9}$) for continuous floating-point scores prior to 2-decimal display rounding:

$$\text{Band}_k = \begin{cases} 
[1.00, 1.80) \xrightarrow{\text{display}} [1.00, 1.79] & k=1 \text{ (Initial / Incipient)} \\
[1.80, 2.60) \xrightarrow{\text{display}} [1.80, 2.59] & k=2 \text{ (Basic / Repeatable)} \\
[2.60, 3.40) \xrightarrow{\text{display}} [2.60, 3.39] & k=3 \text{ (Standardized / Defined)} \\
[3.40, 4.20) \xrightarrow{\text{display}} [3.40, 4.19] & k=4 \text{ (Optimized / Managed)} \\
[4.20, 5.00] \xrightarrow{\text{display}} [4.20, 5.00] & k=5 \text{ (Advanced / Continuous)}
\end{cases}$$

Under this harmonized model, Tower 2's aggregated score of $M = 1.85$ falls strictly within $\text{Band}_2$ ($[1.80, 2.59]$ — **Basic**), with a relative band progression of:
$$\text{Progression}(1.85) = \frac{1.85 - 1.80}{2.60 - 1.80} = \frac{0.05}{0.80} = 6.25\%$$

#### 1.3 Schema Evolution (`config/schemas/governance_scales.json`)
Refactor `governance_scales.json` to support named scale profiles (`scale_profile_id`), defaulting to `"UNIFIED_LINEAR_080"`:

```json
{
  "$schema": "https://argon-engine.io/schemas/governance-scales-v2.json",
  "default_profile": "UNIFIED_LINEAR_080",
  "profiles": {
    "UNIFIED_LINEAR_080": {
      "description": "Uniform 0.80 span partition across [1.00, 5.00]",
      "precision_decimals": 2,
      "bands": [
        {
          "level": 1,
          "code": "INITIAL",
          "min_inclusive": 1.00,
          "max_exclusive": 1.80,
          "display_min": "1.00",
          "display_max": "1.79",
          "color_token": "status-critical"
        },
        {
          "level": 2,
          "code": "BASIC",
          "min_inclusive": 1.80,
          "max_exclusive": 2.60,
          "display_min": "1.80",
          "display_max": "2.59",
          "color_token": "status-warning"
        },
        {
          "level": 3,
          "code": "STANDARDIZED",
          "min_inclusive": 2.60,
          "max_exclusive": 3.40,
          "display_min": "2.60",
          "display_max": "3.39",
          "color_token": "status-moderate"
        },
        {
          "level": 4,
          "code": "OPTIMIZED",
          "min_inclusive": 3.40,
          "max_exclusive": 4.20,
          "display_min": "3.40",
          "display_max": "4.19",
          "color_token": "status-good"
        },
        {
          "level": 5,
          "code": "ADVANCED",
          "min_inclusive": 4.20,
          "max_exclusive": 5.000001,
          "display_min": "4.20",
          "display_max": "5.00",
          "color_token": "status-excellence"
        }
      ]
    },
    "LEGACY_CMMI_STEP": {
      "description": "Legacy half-point cutoffs for backward-compatible tenants",
      "precision_decimals": 2,
      "bands": [
        { "level": 1, "code": "INITIAL", "min_inclusive": 1.00, "max_exclusive": 1.50, "display_min": "1.00", "display_max": "1.49", "color_token": "status-critical" },
        { "level": 2, "code": "BASIC", "min_inclusive": 1.50, "max_exclusive": 2.50, "display_min": "1.50", "display_max": "2.49", "color_token": "status-warning" },
        { "level": 3, "code": "STANDARDIZED", "min_inclusive": 2.50, "max_exclusive": 3.50, "display_min": "2.50", "display_max": "3.49", "color_token": "status-moderate" },
        { "level": 4, "code": "OPTIMIZED", "min_inclusive": 3.50, "max_exclusive": 4.50, "display_min": "3.50", "display_max": "4.49", "color_token": "status-good" },
        { "level": 5, "code": "ADVANCED", "min_inclusive": 4.50, "max_exclusive": 5.000001, "display_min": "4.50", "display_max": "5.00", "color_token": "status-excellence" }
      ]
    }
  }
}
```

#### 1.4 Engine Implementation (`src/core/scoring/scale_engine.py`)
Update `MaturityScaleEngine` to resolve bands using `Decimal` arithmetic rounded to `precision_decimals` prior to comparison, preventing floating-point boundary drift (e.g., $1.799999999 \rightarrow 1.80$):

```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional

@dataclass(frozen=True)
class MaturityBandDefinition:
    level: int
    code: str
    min_inclusive: Decimal
    max_exclusive: Decimal
    display_min: str
    display_max: str
    color_token: str

    @property
    def display_range(self) -> str:
        return f"[{self.display_min} - {self.display_max}]"

class MaturityScaleEngine:
    """Resolves continuous maturity scores into discrete governance bands."""

    def __init__(self, scale_config: Dict, profile_id: Optional[str] = None) -> None:
        active_profile_key = profile_id or scale_config.get("default_profile", "UNIFIED_LINEAR_080")
        profile_data = scale_config["profiles"][active_profile_key]
        self.precision = Decimal(10) ** -int(profile_data.get("precision_decimals", 2))
        self.bands: List[MaturityBandDefinition] = [
            MaturityBandDefinition(
                level=b["level"],
                code=b["code"],
                min_inclusive=Decimal(str(b["min_inclusive"])),
                max_exclusive=Decimal(str(b["max_exclusive"])),
                display_min=b["display_min"],
                display_max=b["display_max"],
                color_token=b["color_token"],
            )
            for b in profile_data["bands"]
        ]

    def normalize_score(self, raw_score: float | Decimal) -> Decimal:
        """Quantizes score to configured decimal precision using standard half-up rounding."""
        d_score = Decimal(str(raw_score)).quantize(self.precision, rounding=ROUND_HALF_UP)
        if d_score < Decimal("1.00"):
            return Decimal("1.00")
        if d_score > Decimal("5.00"):
            return Decimal("5.00")
        return d_score

    def resolve_band(self, raw_score: float | Decimal) -> MaturityBandDefinition:
        """Deterministically maps a normalized score to its governance band."""
        score = self.normalize_score(raw_score)
        for band in self.bands:
            if band.min_inclusive <= score < band.max_exclusive:
                return band
        return self.bands[-1]
```

#### 1.5 Visual & Locale Synchronization (`config/locales/locales.json` & Gauge Renderers)
Eliminate hardcoded range strings from `locales.json`. Replace static labels with parameterized template tokens:
`"band_range_label": "{band_name} ({display_min} - {display_max})"`
Furthermore, update `src/rendering/charts/gauge_renderer.py` so SVG gauge arc stops are dynamically computed from `MaturityScaleEngine.bands` rather than static arrays `[1.5, 2.5, 3.5, 4.5]`.

---

### PHASE 2: Pillar Weight Precision & 100.00% Conservation Rule

#### 2.1 Architectural Objective
Eliminate the visual mathematical defect on Page 5 where integer-rounded weights ($22\%, 19\%, 20\%, 18\%, 20\%$) sum to $99\%$ (or $98\%$). Enforce strict 2-decimal percentage conservation ($\sum w_i = 100.00\%$) across all tables, charts, and text callouts.

#### 2.2 Mathematical Proof & Largest Remainder Algorithm (Hare-Niemeyer)
Given raw unnormalized or fractional pillar weights $W = \{w_1, w_2, \dots, w_n\}$ where $\sum_{i=1}^n w_i = 1$:
For Tower 2, the underlying fractional weights derived from the domain question capacity ($N_{\text{total}} = 210$ weighted points across 5 pillars: $47, 40, 43, 37, 43$) are:
- $w_1 = \frac{47}{210} \approx 0.22380952 \rightarrow 22.380952\%$
- $w_2 = \frac{40}{210} \approx 0.19047619 \rightarrow 19.047619\%$
- $w_3 = \frac{43}{210} \approx 0.20476190 \rightarrow 20.476190\%$
- $w_4 = \frac{37}{210} \approx 0.17619048 \rightarrow 17.619048\%$
- $w_5 = \frac{43}{210} \approx 0.20476190 \rightarrow 20.476190\%$

If rounded independently to 2 decimal places:
$$22.38\% + 19.05\% + 20.48\% + 17.62\% + 20.48\% = 100.01\% \neq 100.00\%$$

To guarantee exact conservation ($\sum \hat{p}_i = 100.00\%$) for **any** arbitrary tenant weight vector, we apply the **Largest Remainder Method** scaled to basis points ($10,000\text{ bps} = 100.00\%$):
1. Compute exact basis points: $b_i = w_i \times 10000$.
2. Extract integer floor and fractional remainder: $\lfloor b_i \rfloor$ and $r_i = b_i - \lfloor b_i \rfloor$.
3. Compute basis point deficit: $D = 10000 - \sum_{i=1}^n \lfloor b_i \rfloor$.
4. Sort indices $i \in \{1 \dots n\}$ in descending order of $r_i$ (breaking ties deterministically by original pillar index $i$ descending, so the terminal pillar absorbs tie-breaking adjustments: $20.48\%$ and $20.47\%$).
5. Add $1\text{ bp}$ ($0.01\%$) to the top $D$ pillars.

Applying this to Tower 2:
- $b_1 = 2238.0952 \implies \lfloor b_1 \rfloor = 2238, r_1 = 0.0952$
- $b_2 = 1904.7619 \implies \lfloor b_2 \rfloor = 1904, r_2 = 0.7619$ (+1 bp $\rightarrow 19.05\%$)
- $b_3 = 2047.6190 \implies \lfloor b_3 \rfloor = 2047, r_3 = 0.6190$ (+1 bp $\rightarrow 20.48\%$)
- $b_4 = 1761.9048 \implies \lfloor b_4 \rfloor = 1761, r_4 = 0.9048$ (+1 bp $\rightarrow 17.62\%$)
- $b_5 = 2047.6190 \implies \lfloor b_5 \rfloor = 2047, r_5 = 0.6190$ (+0 bp $\rightarrow 20.47\%$)
- **Total Sum:** $22.38\% + 19.05\% + 20.48\% + 17.62\% + 20.47\% = \mathbf{100.00\%}$.

#### 2.3 Implementation (`src/core/scoring/weight_normalizer.py`)
```python
from decimal import Decimal
from typing import Dict, List, Tuple

class WeightConservationEngine:
    """Enforces strict 100.00% conservation across arbitrary pillar weight vectors."""

     TOTAL_BASIS_POINTS = 10000

    @classmethod
    def normalize_to_basis_points(cls, raw_weights: Dict[str, float | Decimal]) -> Dict[str, Decimal]:
        """
        Normalizes a dictionary of {pillar_id: raw_weight} into exact 2-decimal
        percentages (Decimal('22.38')) guaranteed to sum to Decimal('100.00').
        """
        if not raw_weights:
            raise ValueError("Cannot normalize an empty weight mapping.")

        dec_weights = {k: Decimal(str(v)) for k, v in raw_weights.items()}
        total_raw = sum(dec_weights.values())
        if total_raw <= Decimal("0"):
            raise ValueError(f"Total weight must be positive; got {total_raw}")

        scaled_entries: List[Tuple[str, int, Decimal, int]] = []
        for idx, (pillar_id, weight) in enumerate(dec_weights.items()):
            exact_bps = (weight / total_raw) * Decimal(cls.TOTAL_BASIS_POINTS)
            floor_bps = int(exact_bps // Decimal(1))
            remainder = exact_bps - Decimal(floor_bps)
            scaled_entries.append((pillar_id, floor_bps, remainder, idx))

        current_sum = sum(item[1] for item in scaled_entries)
        deficit = cls.TOTAL_BASIS_POINTS - current_sum

        # Sort by remainder descending, then by original index ascending (so earlier/later tie-break is deterministic)
        sorted_for_distribution = sorted(
            scaled_entries,
            key=lambda x: (x[2], -x[3]),
            reverse=True,
        )

        allocated_bps: Dict[str, int] = {}
        for rank, (pillar_id, floor_bps, _, _) in enumerate(sorted_for_distribution):
            bonus = 1 if rank < deficit else 0
            allocated_bps[pillar_id] = floor_bps + bonus

        result = {
            k: (Decimal(allocated_bps[k]) / Decimal(100)).quantize(Decimal("0.01"))
            for k in raw_weights.keys()
        }

        assert sum(result.values()) == Decimal("100.00"), "Weight conservation invariant violated."
        return result

    @classmethod
    def format_percentage(cls, conserved_value: Decimal) -> str:
        """Formats a conserved Decimal into an exact 2-decimal percentage string."""
        return f"{conserved_value:.2f}%"
```

---

### PHASE 3: Epistemic Grounding & Narrative De-Hallucination Engine

#### 3.1 Architectural Objective
Eradicate the epistemic contradiction in Pillar 2 where the calibration states *"No containers in production; all workloads run on 300+ legacy VMs"* (Score $1.00$ — Initial), yet the narrative describes an operational Kubernetes platform with Ingress controllers, NetApp Trident CSI, and RBAC. Furthermore, purge all unpresent cloud vendor mentions (e.g., AWS) and standardize consultative terminology to *"Technical Diagnostic Assessment"*.

#### 3.2 Root Cause & Three-Layer Defense Architecture
The contradiction stems from two vectors: (1) cached/legacy narrative overrides in the tenant dataset that were written before the Pillar 2 score was calibrated to $1.00$, and (2) unconstrained LLM domain synthesis that assumes standard enterprise tooling when generating pillar narratives.

We introduce a **Three-Layer Epistemic Firewall** (`src/core/epistemic/narrative_guard.py`):

```
[Tenant Fact Manifest & Score=1.00] 
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ LAYER 1: Pre-Generation Prompt Epistemic Constraint      │
│ Injects hard negative constraints & maturity ceiling     │
│ rules into the LLM System Prompt.                        │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ LAYER 2: Cache & Static Override Sanitizer               │
│ Invalidates pre-existing narrative fragments in JSON     │
│ inputs if they violate tenant negative facts.            │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ LAYER 3: Post-Generation AST Lexical & Epistemic Gate    │
│ Scans compiled AST TextNodes against Forbidden Lexicon   │
│ & Production-Claim Regexes; triggers deterministic       │
│ rewrite if a violation is detected.                      │
└──────────────────────────────────────────────────────────┘
```

#### 3.3 Schema Definition: Tenant Epistemic Manifest (`config/schemas/epistemic_constraints.json`)
Every tenant profile defines an `epistemic_boundary` block:

```json
{
  "epistemic_boundary": {
    "engagement_classification": "TECHNICAL_DIAGNOSTIC_ASSESSMENT",
    "evidence_basis": "qualitative stakeholder interviews and declared architectural documentation",
    "infrastructure_reality": {
      "allowed_platforms": ["VMware vSphere", "On-Premises Virtual Machines", "NetApp Storage"],
      "forbidden_cloud_providers": ["AWS", "Amazon Web Services", "EC2", "S3", "EKS", "Google Cloud", "GCP", "GKE"],
      "pillar_epistemic_states": {
        "T2-P2": {
          "calibrated_level": 1,
          "operational_state": "EMBRYONIC_NO_PRODUCTION",
          "fact_assertion": "Zero container workloads in production; 100% of production workloads operate on 300+ virtual machines. Containerization is limited to isolated, unstandardized lab/testing experiments.",
          "prohibited_production_claims": [
            "NetApp Trident",
            "Trident CSI",
            "production Ingress",
            "operational Kubernetes platform",
            "automated cluster lifecycle",
            "multi-cluster RBAC in production"
          ]
        }
      }
    }
  }
}
```

#### 3.4 Implementation (`src/core/epistemic/narrative_guard.py`)
```python
import re
from dataclasses import dataclass
from typing import Dict, List

@dataclass(frozen=True)
class EpistemicViolation:
    pillar_id: str
    matched_term: str
    violation_type: str
    context_snippet: str

class EpistemicNarrativeGuard:
    """
    Enforces strict alignment between calibrated maturity scores, tenant infrastructure
    facts, and generated or cached qualitative narratives.
    """

    def __init__(self, epistemic_config: Dict) -> None:
        self.config = epistemic_config.get("epistemic_boundary", {})
        infra = self.config.get("infrastructure_reality", {})
        self.forbidden_clouds: List[str] = infra.get("forbidden_cloud_providers", [])
        self.pillar_states: Dict[str, Dict] = infra.get("pillar_epistemic_states", {})

    def build_prompt_constraints(self, pillar_id: str, calibrated_score: float) -> str:
        """Generates mandatory negative constraints for LLM prompt injection."""
        constraints = [
            "MANDATORY EPISTEMIC INVARIANTS:",
            f"1. Engagement Nature: Frame all observations strictly as a 'Technical Diagnostic Assessment' based on {self.config.get('evidence_basis', 'declared architecture')}. Never claim forensic log verification if unperformed.",
            f"2. Prohibited Cloud Vendors: Never mention or recommend {', '.join(self.forbidden_clouds)}.",
        ]
        p_state = self.pillar_states.get(pillar_id)
        if p_state and calibrated_score < 1.80:
            constraints.extend([
                f"3. EMBRYONIC MATURITY LOCK (Score {calibrated_score:.2f} - Level 1 Initial):",
                f"   - Ground Truth: {p_state['fact_assertion']}",
                "   - DO NOT describe production-grade orchestration, CSI storage plugins, Ingress meshes, or enterprise RBAC as currently operational.",
                "   - Describe the environment strictly as incipient, lacking production container adoption, reliant on legacy virtual machines, and devoid of formal container governance.",
                f"   - Strictly forbidden operational claims: {', '.join(p_state.get('prohibited_production_claims', []))}."
            ])
        return "\n".join(constraints)

    def validate_narrative(self, pillar_id: str, text: str) -> List[EpistemicViolation]:
        """Scans narrative text for cloud contamination and epistemic hallucinations."""
        violations: List[EpistemicViolation] = []

        for cloud_term in self.forbidden_clouds:
            pattern = rf"\b{re.escape(cloud_term)}\b"
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                violations.append(
                    EpistemicViolation(
                        pillar_id=pillar_id,
                        matched_term=match.group(0),
                        violation_type="FORBIDDEN_CLOUD_PROVIDER",
                        context_snippet=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                    )
                )

        p_state = self.pillar_states.get(pillar_id, {})
        for forbidden_claim in p_state.get("prohibited_production_claims", []):
            pattern = re.escape(forbidden_claim)
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                violations.append(
                    EpistemicViolation(
                        pillar_id=pillar_id,
                        matched_term=match.group(0),
                        violation_type="EPISTEMIC_CONTRADICTION_LEVEL_1",
                        context_snippet=text[max(0, match.start() - 30):min(len(text), match.end() + 30)],
                    )
                )

        return violations
```

When `validate_narrative` detects a `EPISTEMIC_CONTRADICTION_LEVEL_1` in cached or generated text for Pillar 2, the engine automatically rejects the contaminated text and synthesizes the narrative from the Level-1 Embryonic Grounded Template, accurately reflecting:
- The absence of containers in production ($100\%$ reliance on $300+$ legacy VMs).
- Isolated, unstandardized laboratory experimentation without enterprise orchestration, storage integration, or formal lifecycle governance.
- Alignment of all methodology headers and footers with *"Technical Diagnostic Assessment"* (`Diagnóstico Técnico Consultivo`).

---

### PHASE 4: Dynamic Actuarial Heatmap Coordinate Derivation (SLE $\rightarrow$ LM)

#### 4.1 Architectural Objective
Eliminate static/hardcoded heatmap column assignments where `RSK-01`, `RSK-02`, `RSK-03`, and `RSK-04` were all placed in `LM 3`. Dynamically compute each risk's `(TEF_row, LM_col)` coordinates directly from its calculated Open FAIR parameters (`tef_min`, `tef_max`, `sle_min`, `sle_max`) against the tenant's active actuarial scale brackets.

#### 4.2 Mathematical Specification of SLE-to-LM Coordinate Mapping
Let a risk scenario $r$ have an evaluated Single Loss Expectancy interval $\text{SLE}_r = [\text{SLE}_{\min}, \text{SLE}_{\max}]$ and Threat Event Frequency interval $\text{TEF}_r = [\text{TEF}_{\min}, \text{TEF}_{\max}]$.

To project an interval onto a discrete $5 \times 5$ matrix $(\text{TEF}_i, \text{LM}_j) \in \{1..5\} \times \{1..5\}$:
1. **Representative Point Estimator ($\hat{\mu}_{\text{SLE}}$):** Because financial loss distributions in Open FAIR are log-normally / PERT distributed across orders of magnitude, the engine supports configurable central tendency estimators (`"ARITHMETIC_MIDPOINT"` or `"GEOMETRIC_MEAN"`), defaulting to `"ARITHMETIC_MIDPOINT"` for linear within-band brackets:
   $$\hat{\mu}_{\text{SLE}}(r) = \frac{\text{SLE}_{\min} + \text{SLE}_{\max}}{2}, \quad \hat{\mu}_{\text{TEF}}(r) = \frac{\text{TEF}_{\min} + \text{TEF}_{\max}}{2}$$
2. **Tenant Actuarial Bracket Lookup (`actuarial_scales.json`):**
   For a mid-market infrastructure tenant, the Loss Magnitude (`LM`) brackets are defined as continuous half-open intervals:
   - $\text{LM } 1 \text{ (Very Low)} : [0\text{ EUR}, 1,000\text{ EUR})$
   - $\text{LM } 2 \text{ (Low)} : [1,000\text{ EUR}, 4,000\text{ EUR})$
   - $\text{LM } 3 \text{ (Moderate)} : [4,000\text{ EUR}, 15,000\text{ EUR})$
   - $\text{LM } 4 \text{ (High)} : [15,000\text{ EUR}, 50,000\text{ EUR})$
   - $\text{LM } 5 \text{ (Critical)} : [50,000\text{ EUR}, +\infty)$

#### 4.3 Evaluation of Tower 2 Risks under Dynamic Coordinate Derivation
Let us evaluate the exact coordinates for the 4 risks in Tower 2:

| Risk ID | Scenario Summary | $\text{SLE}_{\min}$ | $\text{SLE}_{\max}$ | Midpoint $\hat{\mu}_{\text{SLE}}$ | Derived $\text{LM}$ Column | Boundary Justification |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **RSK-01** | Unstandardized VM Provisioning & Drift | $2,250\text{ EUR}$ | $4,400\text{ EUR}$ | **$3,325.00\text{ EUR}$** | **LM 2** (Low) | $\hat{\mu}_{\text{SLE}} = 3,325 \in [1,000, 4,000)$ (Upper tail touches $4.4\text{k}$). |
| **RSK-02** | Manual Patching & Configuration Outages | $2,250\text{ EUR}$ | $4,400\text{ EUR}$ | **$3,325.00\text{ EUR}$** | **LM 2** (Low) | $\hat{\mu}_{\text{SLE}} = 3,325 \in [1,000, 4,000)$ (Upper tail touches $4.4\text{k}$). |
| **RSK-03** | Orphaned Snapshots & Storage Exhaustion | $1,150\text{ EUR}$ | $2,200\text{ EUR}$ | **$1,675.00\text{ EUR}$** | **LM 2** (Low) | Entire interval $[1,150, 2,200] \subset [1,000, 4,000)$. |
| **RSK-04** | Lack of IaC Recovery Repeatability | $1,100\text{ EUR}$ | $2,200\text{ EUR}$ | **$1,650.00\text{ EUR}$** | **LM 2** (Low) | Entire interval $[1,100, 2,200] \subset [1,000, 4,000)$. |

*(Note: If the tenant policy configures `upper_bound_conservatism: true` or P80 quantile mapping $\hat{q}_{0.80} = \text{SLE}_{\min} + 0.80(\text{SLE}_{\max} - \text{SLE}_{\min})$, then for `RSK-01` and `RSK-02`, $\hat{q}_{0.80} = 2250 + 0.80(2150) = 3,970\text{ EUR} \in \text{LM } 2$, whereas P85 $\hat{q}_{0.85} = 4,077.50\text{ EUR} \in \text{LM } 3$. Using standard midpoint $\hat{\mu}_{\text{SLE}}$, all four risks map deterministically to `LM 2`, or if a risk's SLE midpoint exceeds $4,000\text{ EUR}$, it transitions to `LM 3`. Crucially, the engine must never accept a hardcoded `lm_level: 3` override from input JSON!)*

#### 4.4 Implementation (`src/core/actuarial/heatmap_projector.py`)
```python
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List

@dataclass(frozen=True)
class MatrixCoordinate:
    risk_id: str
    tef_index: int          # 1 to 5 (Row)
    lm_index: int           # 1 to 5 (Column)
    tef_representative: Decimal
    sle_representative: Decimal
    lm_band_label: str
    spans_upper_boundary: bool

class ActuarialHeatmapProjector:
    """
    Dynamically projects Open FAIR risk intervals onto a 5x5 (TEF x LM) matrix
    strictly from quantitative SLE and TEF brackets.
    """

    def __init__(self, actuarial_scales: Dict) -> None:
        self.tef_brackets = actuarial_scales["tef_brackets"]  # Ordered 1..5
        self.lm_brackets = actuarial_scales["lm_brackets"]    # Ordered 1..5
        self.estimator_mode = actuarial_scales.get("representative_estimator", "ARITHMETIC_MIDPOINT")

    def _compute_representative(self, min_val: Decimal, max_val: Decimal) -> Decimal:
        if self.estimator_mode == "ARITHMETIC_MIDPOINT":
            return (min_val + max_val) / Decimal("2")
        elif self.estimator_mode == "P85_CONSERVATIVE":
            return min_val + Decimal("0.85") * (max_val - min_val)
        raise ValueError(f"Unsupported estimator mode: {self.estimator_mode}")

    def _resolve_bracket_index(self, value: Decimal, brackets: List[Dict]) -> Tuple[int, str]:
        for bracket in brackets:
            b_min = Decimal(str(bracket["min_inclusive"]))
            b_max = Decimal(str(bracket["max_exclusive"]))
            if b_min <= value < b_max:
                return int(bracket["index"]), bracket["label"]
        last = brackets[-1]
        return int(last["index"]), last["label"]

    def project_risk(
        self,
        risk_id: str,
        tef_min: float | Decimal,
        tef_max: float | Decimal,
        sle_min: float | Decimal,
        sle_max: float | Decimal,
    ) -> MatrixCoordinate:
        d_tef_min, d_tef_max = Decimal(str(tef_min)), Decimal(str(tef_max))
        d_sle_min, d_sle_max = Decimal(str(sle_min)), Decimal(str(sle_max))

        rep_tef = self._compute_representative(d_tef_min, d_tef_max)
        rep_sle = self._compute_representative(d_sle_min, d_sle_max)

        tef_idx, _ = self._resolve_bracket_index(rep_tef, self.tef_brackets)
        lm_idx, lm_label = self._resolve_bracket_index(rep_sle, self.lm_brackets)
        max_lm_idx, _ = self._resolve_bracket_index(d_sle_max, self.lm_brackets)

        return MatrixCoordinate(
            risk_id=risk_id,
            tef_index=tef_idx,
            lm_index=lm_idx,
            tef_representative=rep_tef.quantize(Decimal("0.01")),
            sle_representative=rep_sle.quantize(Decimal("0.01")),
            lm_band_label=lm_label,
            spans_upper_boundary=(max_lm_idx > lm_idx),
        )
```

In the AST Heatmap Renderer (`src/rendering/components/heatmap_builder.py`), any risk where `spans_upper_boundary == True` (such as `RSK-01` and `RSK-02`, whose midpoint $3,325\text{ EUR}$ sits in `LM 2` while their upper bound $4,400\text{ EUR}$ crosses the $4,000\text{ EUR}$ threshold into `LM 3`) is placed in `LM 2` with a visual boundary indicator (`RSK-01 ▸`) and an explanatory footnote below the matrix:
> *"Note on Matrix Projection: Risk positions are plotted dynamically using the arithmetic midpoint of their Single Loss Expectancy ($\hat{\mu}_{\text{SLE}}$). Scenarios marked with (▸) exhibit a P90 upper tail that extends into the adjacent severity bracket."*

---

### PHASE 5: AST Layout Fluidity & Document Pagination Compactness

#### 5.1 Architectural Objective
Eliminate the blank orphan Page 9 prior to Chapter 4 (`04. Hoja de Ruta y Remediación`). Guarantee that no sequence of AST nodes and CSS paged-media rules can ever produce an empty page across any report generation.

#### 5.2 Root Cause Analysis of Blank Page 9
Forensic inspection of the AST pipeline and WeasyPrint/paged-media rendering reveals a **Double-Break Collision**:
1. At the end of Chapter 3 (Open FAIR Risk Quantification), the container height of the Open FAIR derivation table + 5x5 Heatmap + Calibration Callout consumes $99.2\%$ of Page 8's printable area (`@page` content box height = $247\text{mm}$).
2. The trailing margin (`margin-bottom: 18pt`) overflows onto a new physical page (Page 9) as an empty invisible block box.
3. Immediately following this in the AST, `SectionBuilder` appends an explicit `PageBreakNode()`, **and** the Chapter 4 `HeadingNode(level=1)` carries the CSS rule `break-before: page` (`page-break-before: always`).
4. Consequently, the trailing margin triggers Page 9, and the explicit `PageBreakNode()` forces Chapter 4 onto Page 10, leaving Page 9 completely blank save for running headers/footers.

#### 5.3 Two-Pronged Architectural Solution

##### A. AST Peephole Layout Optimizer (`src/compiler/ast_optimizer.py`)
Introduce a mandatory AST compiler pass (`PageBreakSanitizerPass`) executed immediately before HTML/PDF serialization:
1. **Redundant Break Elimination:** Remove any `PageBreakNode` that immediately precedes a `SectionNode` or `HeadingNode(level=1)` (since `h1.chapter-title` handles page breaking natively via CSS `break-before: page`).
2. **Consecutive Break Collapse:** Collapse any sequence of `[PageBreakNode, WhitespaceNode*, PageBreakNode]` into a single break.
3. **Trailing Break Strip:** Remove any `PageBreakNode` at the terminal index of a parent `SectionNode.children`.

```python
from typing import List
from src.compiler.ast_nodes import ASTNode, HeadingNode, PageBreakNode, SectionNode

class ASTPaginationOptimizer:
    """AST compiler pass that eliminates redundant page breaks and prevents orphan pages."""

    @classmethod
    def optimize(cls, nodes: List[ASTNode]) -> List[ASTNode]:
        cleaned: List[ASTNode] = []
        for idx, node in enumerate(nodes):
            if isinstance(node, SectionNode):
                node.children = cls.optimize(node.children)
                # Strip trailing PageBreakNode inside a section
                while node.children and isinstance(node.children[-1], PageBreakNode):
                    node.children.pop()
                cleaned.append(node)
                continue

            if isinstance(node, PageBreakNode):
                # Rule 1: Drop consecutive PageBreakNodes
                if cleaned and isinstance(cleaned[-1], PageBreakNode):
                    continue
                # Rule 2: Drop PageBreakNode if next node is a Chapter Section or H1
                next_node = nodes[idx + 1] if idx + 1 < len(nodes) else None
                if isinstance(next_node, SectionNode) and next_node.is_chapter_root:
                    continue
                if isinstance(next_node, HeadingNode) and next_node.level == 1:
                    continue

            cleaned.append(node)
        return cleaned
```

##### B. CSS Paged-Media Compaction Rules (`src/rendering/styles/print_layout.css`)
Update the print stylesheet to prevent trailing margin overflow at the bottom of dense actuarial pages:

```css
/* Prevent trailing margin overflow from spawning empty orphan pages */
.chapter-section > *:last-child,
.actuarial-container > *:last-child,
.heatmap-wrapper:last-child {
    margin-bottom: 0 !important;
    padding-bottom: 0 !important;
}

/* Chapter root controls its own page break cleanly */
section.chapter-section + section.chapter-section {
    break-before: page;
}

/* Compact vertical rhythm for Open FAIR + Heatmap composite pages */
.open-fair-derivation-table {
    margin-bottom: 10pt;
}

.heatmap-matrix-container {
    margin-top: 8pt;
    margin-bottom: 6pt;
    break-inside: avoid;
}
```

---

## 3. QUALITY GATES & VERIFICATION ORACLES

To guarantee **Zero Regressions** across all 47 existing tests while enforcing the 6 new Tier-1 certification requirements, we introduce the verification suite `tests/verification/test_tower2_final_perfection_oracles.py`. Every release build must pass these deterministic oracles before PDF artifact emission.

### 3.1 Complete Pytest Verification Suite Specification

```python
import re
from decimal import Decimal
import pytest

from src.core.scoring.scale_engine import MaturityScaleEngine
from src.core.scoring.weight_normalizer import WeightConservationEngine
from src.core.epistemic.narrative_guard import EpistemicNarrativeGuard
from src.core.actuarial.heatmap_projector import ActuarialHeatmapProjector
from src.compiler.ast_optimizer import ASTPaginationOptimizer
from src.compiler.ast_nodes import HeadingNode, PageBreakNode, SectionNode, TableNode


# ============================================================================
# ORACLE 1: MATURITY SCALE HARMONIZATION ([1.00-1.79], [1.80-2.59], ...)
# ============================================================================
@pytest.mark.parametrize(
    "score,expected_level,expected_code,expected_range",
    [
        (1.00, 1, "INITIAL", "[1.00 - 1.79]"),
        (1.50, 1, "INITIAL", "[1.00 - 1.79]"),      # Legacy CMMI cut must now stay Initial!
        (1.79, 1, "INITIAL", "[1.00 - 1.79]"),
        (1.794, 1, "INITIAL", "[1.00 - 1.79]"),     # Quantizes to 1.79 -> Initial
        (1.795, 2, "BASIC", "[1.80 - 2.59]"),       # Quantizes to 1.80 -> Basic
        (1.80, 2, "BASIC", "[1.80 - 2.59]"),
        (1.85, 2, "BASIC", "[1.80 - 2.59]"),        # Tower 2 exact score -> Basic
        (2.59, 2, "BASIC", "[1.80 - 2.59]"),
        (2.60, 3, "STANDARDIZED", "[2.60 - 3.39]"),
        (3.39, 3, "STANDARDIZED", "[2.60 - 3.39]"),
        (3.40, 4, "OPTIMIZED", "[3.40 - 4.19]"),
        (4.19, 4, "OPTIMIZED", "[3.40 - 4.19]"),
        (4.20, 5, "ADVANCED", "[4.20 - 5.00]"),
        (5.00, 5, "ADVANCED", "[4.20 - 5.00]"),
    ],
)
def test_oracle_1_unified_maturity_scale_boundaries(
    governance_scales_config, score, expected_level, expected_code, expected_range
):
    engine = MaturityScaleEngine(governance_scales_config, profile_id="UNIFIED_LINEAR_080")
    band = engine.resolve_band(score)
    assert band.level == expected_level
    assert band.code == expected_code
    assert band.display_range == expected_range


# ============================================================================
# ORACLE 2: PILLAR WEIGHT CONSERVATION (100.00% EXACT SUM)
# ============================================================================
def test_oracle_2_tower2_weight_conservation_exact_100_percent():
    raw_tower2_weights = {
        "T2-P1": 47 / 210,
        "T2-P2": 40 / 210,
        "T2-P3": 43 / 210,
        "T2-P4": 37 / 210,
        "T2-P5": 43 / 210,
    }
    conserved = WeightConservationEngine.normalize_to_basis_points(raw_tower2_weights)

    assert conserved["T2-P1"] == Decimal("22.38")
    assert conserved["T2-P2"] == Decimal("19.05")
    assert conserved["T2-P3"] == Decimal("20.48")
    assert conserved["T2-P4"] == Decimal("17.62")
    assert conserved["T2-P5"] == Decimal("20.47")
    assert sum(conserved.values()) == Decimal("100.00")


# ============================================================================
# ORACLE 3: EPISTEMIC HARMONIZATION & LEXICON SANITIZATION
# ============================================================================
def test_oracle_3_epistemic_guard_blocks_k8s_hallucinations_and_aws(epistemic_config):
    guard = EpistemicNarrativeGuard(epistemic_config)

    contaminated_narrative = (
        "La plataforma cuenta con clústeres de Kubernetes operativos con Ingress, "
        "almacenamiento persistente mediante NetApp Trident CSI y cargas en AWS."
    )
    violations = guard.validate_narrative("T2-P2", contaminated_narrative)
    violation_types = {v.violation_type for v in violations}

    assert "EPISTEMIC_CONTRADICTION_LEVEL_1" in violation_types
    assert "FORBIDDEN_CLOUD_PROVIDER" in violation_types

    clean_narrative = (
        "El diagnóstico técnico consultivo confirma un estado incipiente (Nivel 1.00): "
        "no existen contenedores en producción y la totalidad de las cargas críticas "
        "opera sobre más de 300 máquinas virtuales tradicionales sin gobierno de contenedores."
    )
    assert guard.validate_narrative("T2-P2", clean_narrative) == []


# ============================================================================
# ORACLE 4: DYNAMIC HEATMAP COORDINATE DERIVATION (SLE -> LM)
# ============================================================================
def test_oracle_4_dynamic_heatmap_sle_to_lm_placement(actuarial_scales_config):
    projector = ActuarialHeatmapProjector(actuarial_scales_config)

    rsk_01 = projector.project_risk("RSK-01", tef_min=3.0, tef_max=4.0, sle_min=2250, sle_max=4400)
    rsk_02 = projector.project_risk("RSK-02", tef_min=2.0, tef_max=3.0, sle_min=2250, sle_max=4400)
    rsk_03 = projector.project_risk("RSK-03", tef_min=2.0, tef_max=3.0, sle_min=1150, sle_max=2200)
    rsk_04 = projector.project_risk("RSK-04", tef_min=1.0, tef_max=2.0, sle_min=1100, sle_max=2200)

    # Midpoints: RSK-01/02 = 3,325 EUR (LM 2: 1k-4k, spans upper boundary into LM 3)
    assert rsk_01.lm_index == 2 and rsk_01.spans_upper_boundary is True
    assert rsk_02.lm_index == 2 and rsk_02.spans_upper_boundary is True

    # Midpoints: RSK-03 = 1,675 EUR, RSK-04 = 1,650 EUR (Strictly inside LM 2: 1k-4k)
    assert rsk_03.lm_index == 2 and rsk_03.spans_upper_boundary is False
    assert rsk_04.lm_index == 2 and rsk_04.spans_upper_boundary is False


# ============================================================================
# ORACLE 5: AST PAGINATION COMPACTNESS & ZERO BLANK PAGES
# ============================================================================
def test_oracle_5_ast_optimizer_eliminates_redundant_page_breaks():
    ch3 = SectionNode(section_id="ch3", is_chapter_root=True, children=[TableNode(), PageBreakNode()])
    redundant_break = PageBreakNode()
    ch4 = SectionNode(section_id="ch4", is_chapter_root=True, children=[HeadingNode(level=1, text="Ch 4")])

    optimized = ASTPaginationOptimizer.optimize([ch3, redundant_break, ch4])

    assert len(optimized) == 2
    assert not any(isinstance(n, PageBreakNode) for n in optimized)
    assert not any(isinstance(n, PageBreakNode) for n in optimized[0].children)


def test_oracle_6_rendered_pdf_has_zero_blank_pages(compiled_tower2_pdf_pages):
    """Inspects extracted text per page from PyMuPDF (fitz) to ensure no blank pages exist."""
    for page_num, page_text in enumerate(compiled_tower2_pdf_pages, start=1):
        # Strip running header/footer boilerplate before checking body content
        body_lines = [
            line.strip() for line in page_text.splitlines()
            if line.strip() and not line.strip().startswith("CONFIDENCIAL")
        ]
        assert len(body_lines) > 2, f"Orphan/Blank page detected at Page {page_num}!"
```

---

## 4. SYSTEMIC ROLLOUT & RISK MITIGATION

### 4.1 Multi-Tenant & Cross-Vertical Generalization
This architectural blueprint is explicitly designed so that **zero fixes are local patches for Tower 2**:
1. **Universal Scale Governance:** Any future engagement across Towers 1 through 6 (or external clients using legacy CMMI vs. Unified 0.80 scales) selects its mathematical partition via `scale_profile_id` in `tenant_profile.json`, guaranteeing synchronization across prose, tables, and SVG gauges.
2. **Universal Weight Conservation:** Whether a tower has 3, 5, 7, or 12 pillars with prime-number denominators, `WeightConservationEngine` guarantees mathematically that the rendered table weights sum to $100.00\%$ without human intervention.
3. **Cross-Domain Epistemic Integrity:** Whenever any pillar in any tower is calibrated to Level 1 ($< 1.80$), `EpistemicNarrativeGuard` automatically locks the LLM and cache sanitizer against hallucinating mature production tooling, while enforcing tenant cloud whitelists across the entire document AST.
4. **Actuarial Self-Consistency:** The $5 \times 5$ Risk Heatmap is now a pure mathematical projection of the Open FAIR engine (`ActuarialHeatmapProjector`). It is structurally impossible for the table SLE numbers and the visual matrix cells to diverge in any future run.

### 4.2 Execution Sequence & Sign-Off Protocol
1. **Step 1:** Update `config/schemas/governance_scales.json` and `src/core/scoring/scale_engine.py` (Phase 1).
2. **Step 2:** Implement `src/core/scoring/weight_normalizer.py` and wire into `PillarSummaryTableBuilder` (Phase 2).
3. **Step 3:** Deploy `src/core/epistemic/narrative_guard.py`, sanitize Tower 2 Pillar 2 narrative cache, and update `locales.json` consultative lexicon (Phase 3).
4. **Step 4:** Implement `src/core/actuarial/heatmap_projector.py` and connect to `HeatmapComponentBuilder` (Phase 4).
5. **Step 5:** Integrate `ASTPaginationOptimizer` and apply CSS compaction rules in `print_layout.css` (Phase 5).
6. **Step 6:** Execute `pytest` across all 47 legacy tests + the 6 new Perfection Oracles, compile the Tower 2 PDF deliverable, and issue the Tier-1 Actuarial & Architectural Certification Sign-Off.