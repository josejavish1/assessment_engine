# ARGON PHASE 22: MASTER IMPLEMENTATION BLUEPRINT
**Document ID:** `docs/architecture/ARGON_PHASE22_MASTER_IMPLEMENTATION_BLUEPRINT.md`  
**Author:** Gemini-4-Argon (Global Chief Systems Architect, Principal Compiler Engineer, FSA)  
**Status:** APPROVED FOR IMMEDIATE EXECUTION  
**Target Architecture:** Tier-1 Autonomous Actuarial & Epistemic Synthesis Engine  

---

## 1. EXECUTIVE SUMMARY & PARADIGM SHIFT

Following the successful closure of the first seven architectural gates—most notably the implementation of the dynamic Epistemic Context Router and the Missing Data Circuit Breaker—the engine’s deterministic routing and foundational fault tolerance are operating within acceptable parameters. However, the external adversarial audit has identified three residual systemic vulnerabilities that invalidate our claim to a Tier-1 (8+/10) architectural certification. 

These vulnerabilities represent a fundamental failure in epistemic boundary enforcement and actuarial modeling:

1. **The "Implementation Hallucination" Syllogism (Epistemic Overreach):** The synthesis engine currently conflates quantitative maturity scores with qualitative technological specificity. When presented with a high self-assessed maturity score (e.g., 4.0 or 5.0) in the absence of corroborating interview transcripts, the Large Language Model (LLM) utilizes its parametric prior probabilities to hallucinate market-leading vendor implementations (e.g., inferring "Microsoft Entra ID" or "CrowdStrike Falcon"). This violates the closed-world assumption required for forensic auditability.
2. **The "Actuarial Bipolarity" in FAIR Vulnerability (Mathematical Degeneracy):** In `chapter4_synthesizer.py`, the Factor Analysis of Information Risk (FAIR) Monte Carlo simulation relies on a degenerate, step-function heuristic (`vuln_ratio = 0.80 if is_tier1 else 0.95`). By collapsing continuous control maturity manifolds into a binary constant across all ten risk towers, the engine destroys variance, invalidates the Loss Exceedance Curves (LEC), and renders the actuarial simulation mathematically indefensible.
3. **"False Certainty" in Contradiction Scoring (Ontological Collapse):** When the `ContradictionEngine` detects a divergence between high quantitative self-assessments and negative qualitative interview evidence, it currently executes a punitive override, collapsing the calibrated score to a static floor of `1.00 / 5.00`. This replaces an unverified optimistic claim with an unverified pessimistic certainty, corrupting downstream weighted averages and misrepresenting epistemic uncertainty as verified technological failure.

### The Paradigm Shift
Phase 22 transitions the Argon Engine from **Heuristic Approximation** to **Strict Epistemic and Actuarial Determinism**. 

```
+-----------------------------------------------------------------------------------+
|                        LEGACY HEURISTIC ARCHITECTURE                              |
+-----------------------------------------------------------------------------------+
| 1. High Score + Zero Transcripts  ---> LLM Parametric Prior ---> Vendor Hallucination|
| 2. Risk Tower Vulnerability       ---> Binary Switch        ---> 0.80 or 0.95     |
| 3. Qualitative Contradiction      ---> Punitive Override    ---> Forced 1.00/5.00 |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                     PHASE 22 DETERMINISTIC ARCHITECTURE                           |
+-----------------------------------------------------------------------------------+
| 1. High Score + Zero Transcripts  ---> Lexical AST Sanitizer ---> Agnostic Profile|
| 2. Risk Tower Vulnerability       ---> Continuous Non-Linear ---> Beta(α, β) Dist |
| 3. Qualitative Contradiction      ---> Epistemic State Tuple ---> 4.25* [PROVISIONAL]|
+-----------------------------------------------------------------------------------+
```

We will eradicate these antipatterns by enforcing three foundational axioms:
* **Axiom of Closed-World Specificity:** A proper noun (vendor, product, or proprietary protocol) may only be emitted in the synthesis layer if and only if its token representation is bijectively mapped to an explicit `evidence_id` within the ingested lexical graph.
* **Axiom of Continuous Actuarial Susceptibility:** Vulnerability ($V$) is a continuous, non-linear, monotonically decreasing function of the multi-dimensional control maturity vector ($\vec{M}$) and structural control effectiveness ($\vec{E}$), modeled stochastically via a Beta distribution to preserve variance in Monte Carlo simulations.
* **Axiom of Epistemic Stratification:** A numerical score and its epistemic certainty are orthogonal dimensions. Contradictions must mutate the *epistemic state* (flagging the metric as `PROVISIONAL` and widening its actuarial confidence interval) without arbitrarily mutating the *empirical magnitude* prior to field verification.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

### PHASE 22.1: Eradicating the "Implementation Hallucination" Syllogism

#### Architectural Objective
Decouple maturity band descriptions from vendor-specific telemetry. Enforce an Abstract Syntax Tree (AST) and Named Entity Recognition (NER) compilation pass over all LLM outputs to guarantee that unverified vendor assertions are structurally impossible to emit.

#### Target Modules
* `src/engine/epistemic/entity_registry.py` *(New Module)*
* `src/engine/prompts/agnostic_profiles.py` *(New Module)*
* `src/engine/synthesizers/narrative_compiler.py` *(Refactor)*

#### Step-by-Step Implementation Logic

1. **Construct the Ground-Truth Entity Registry:**
   During the initial ingestion phase of raw interview transcripts and documentary evidence, execute a deterministic NER pass combined with a curated lexicon of enterprise technology proper nouns. Every extracted technology or vendor token is hashed and stored in an immutable `VerifiedEntityRegistry`, mapped strictly to the source `evidence_id` and character offsets.

2. **Inject Agnostic Operational Profiles into System Prompts:**
   Modify the prompt construction pipeline in `narrative_compiler.py`. When a KPI possesses a quantitative score $S \in [1.0, 5.0]$ but the `VerifiedEntityRegistry` returns an empty set for that KPI’s domain, the prompt router must inject a strict **Agnostic Operational Profile** constraint. The LLM is instructed to describe the *mechanistic, architectural, and procedural characteristics* of that maturity band (e.g., "automated cryptographic key rotation and centralized identity federation") while strictly forbidding the emission of proper nouns.

3. **Implement the Post-Generation Lexical Sanitizer (Compiler Pass):**
   Treat LLM output not as final text, but as an intermediate representation (IR) subject to static analysis. Before any narrative block is committed to the document state:
   * Parse the generated text to extract all proper nouns, vendor signatures, and product monikers.
   * Cross-reference each extracted token against the `VerifiedEntityRegistry` scoped to the active KPI's mapped `evidence_id` list.
   * If an unlinked entity is detected, trigger an **Epistemic Violation Exception**. The compiler automatically strips the offending proper noun, replaces it with its canonical functional archetype (resolved via a deterministic taxonomy map), or triggers a constrained regeneration pass with negative logit bias applied to the offending token IDs.

---

### PHASE 22.2: Eradicating "Actuarial Bipolarity" in FAIR Vulnerability

#### Architectural Objective
Replace the hardcoded binary vulnerability assignment (`0.80` vs. `0.95`) in `chapter4_synthesizer.py` with a continuous, topology-aware actuarial derivation engine that computes susceptibility directly from mapped KPI control scores and feeds a parameterized Beta distribution into the Monte Carlo engine.

#### Target Modules
* `src/engine/actuarial/fair_vulnerability.py` *(New Module)*
* `src/engine/synthesizers/chapter4_synthesizer.py` *(Refactor)*
* `src/engine/models/risk_topology.py` *(Refactor)*

#### Step-by-Step Implementation Logic

1. **Establish the Risk-to-Control Topology Matrix:**
   In `risk_topology.py`, define a bipartite graph mapping each of the 10 Risk Towers ($R_j$) to its specific set of defending KPIs ($K_i$). Each edge in this graph is assigned a structural weight $w_{i,j} \in (0, 1]$ (where $\sum_i w_{i,j} = 1.0$) representing the architectural relevance of KPI $i$ to Risk Tower $j$, alongside a theoretical maximum **Control Effectiveness Factor** ($\eta_i \in (0, 1)$). The factor $\eta_i$ accounts for the reality that even a Maturity 5.0 control cannot achieve 100% risk elimination due to zero-day exploits or human circumvention (typically bounded at $\eta_{\max} = 0.92$).

2. **Implement the Continuous Vulnerability Derivation Formula:**
   For a given Risk Tower $j$, compute the aggregate Control Mitigation Capacity ($C_j$) as the weighted harmonic or arithmetic mean of the normalized maturity scores ($M_i \in [1.0, 5.0]$) of its mapped KPIs, scaled by their respective effectiveness factors:
   
   $$C_j = \sum_{i \in \text{KPI}(R_j)} w_{i,j} \cdot \left( \frac{M_i}{5.0} \right)^\gamma \cdot \eta_i$$

   Where $\gamma$ is the **Non-Linear Maturity Exponent** (calibrated to $\gamma = 1.35$). This exponent reflects the actuarial reality that low-maturity controls (Scores 1–2, ad-hoc/repeatable) offer disproportionately low mitigation against sophisticated threat actors compared to systemic, automated controls (Scores 4–5).
   
   The point-estimate Vulnerability ($\mu_{V,j}$) is then derived as:

   $$\mu_{V,j} = \text{clip}\left(1.0 - C_j, \, V_{\min}, \, V_{\max}\right)$$

   Where $V_{\min} = 0.05$ (residual systemic vulnerability floor) and $V_{\max} = 0.99$ (near-certain susceptibility ceiling).

3. **Parameterize the Monte Carlo Beta Distribution:**
   To prevent deterministic point-estimate collapse inside the Monte Carlo engine, convert $\mu_{V,j}$ into a stochastic Beta distribution $\text{Beta}(\alpha_j, \beta_j)$ for sampling across the $N = 100,000$ iterations. 
   Introduce an **Epistemic Precision Scalar** ($\kappa_j$) derived from the verification state of the underlying KPIs (e.g., $\kappa = 50$ for fully verified controls; $\kappa = 10$ for provisional/contradicted controls, inducing higher variance):

   $$\alpha_j = \mu_{V,j} \cdot \kappa_j, \quad \beta_j = (1.0 - \mu_{V,j}) \cdot \kappa_j$$

4. **Refactor `chapter4_synthesizer.py`:**
   Excise the `vuln_ratio = 0.80 if is_tier1 else 0.95` logic entirely. Instantiate the `FairVulnerabilityEngine`, pass the active `KPIAssessmentState` vector, and inject the resulting $\text{Beta}(\alpha_j, \beta_j)$ distributions directly into the FAIR Loss Event Frequency ($LEF = TEF \times V$) simulation loop.

---

### PHASE 22.3: Eradicating "False Certainty" in Contradiction Scoring

#### Architectural Objective
Eliminate the punitive `1.00 / 5.00` score override inside the `ContradictionEngine`. Implement a multi-dimensional metric representation that preserves the empirical self-assessed value while elevating the epistemic status to `PROVISIONAL`, propagating uncertainty flags to the UI/report layer and widening actuarial variance in downstream calculations.

#### Target Modules
* `src/engine/epistemic/contradiction_engine.py` *(Refactor)*
* `src/engine/models/metric_state.py` *(New Module)*
* `src/engine/renderers/markdown_formatter.py` *(Refactor)*

#### Step-by-Step Implementation Logic

1. **Introduce the `EpistemicState` Enum and `CalibratedMetric` Tuple:**
   Replace raw floating-point score primitives across the engine with a strongly-typed `CalibratedMetric` object. This object encapsulates the `raw_self_assessment`, the `calibrated_value`, the `epistemic_state` (`VERIFIED`, `UNCORROBORATED`, `PROVISIONAL_CONTRADICTED`, `MISSING_DATA`), a `display_token` (e.g., `"4.25*"`), and an `uncertainty_penalty_factor`.

2. **Refactor `ContradictionEngine` Resolution Logic:**
   When the NLI (Natural Language Inference) or heuristic contradiction detector identifies a severe conflict between a quantitative survey response (e.g., $M_i = 4.25$) and qualitative interview evidence (e.g., transcript `ev_882` states *"We have no automated ingress policies on our clusters"*):
   * **DO NOT** mutate `calibrated_value` to `1.00`. Retain `calibrated_value = 4.25`.
   * Mutate `epistemic_state` to `EpistemicState.PROVISIONAL_CONTRADICTED`.
   * Populate the `contradiction_metadata` payload with the exact conflicting `evidence_id`, the calculated semantic divergence score, and the mandatory field-audit remediation action.
   * Set the `display_token` to append the epistemic caveat glyph: `f"{calibrated_value:.2f}*"`.

3. **Propagate Epistemic Uncertainty to Aggregations and Actuarial Models:**
   * **Reporting Layer:** When rolling up KPI scores into Domain or Tower averages, compute two distinct metrics: the **Nominal Maturity Average** (utilizing the `4.25` value, marked as provisional if any constituent KPI is provisional) and the **Risk-Adjusted Conservative Baseline** (which applies a configurable discount factor ONLY for internal stress-testing, explicitly separated from the primary score).
   * **Actuarial Layer Integration:** Link Phase 22.3 directly to Phase 22.2. When `FairVulnerabilityEngine` encounters a KPI in the `PROVISIONAL_CONTRADICTED` state, it reduces the Epistemic Precision Scalar ($\kappa_j$) by 75% and shifts the effective control maturity input for the Monte Carlo simulation toward a wider uniform prior, accurately reflecting that the control cannot be relied upon without falsifying the client's stated score in the executive tables.

---

## 3. ARCHITECTURAL CONTRACTS & SCHEMAS

The following production-grade Python 3.11+ implementations define the exact data contracts, Pydantic V2 schemas, and algorithmic engines required to execute Phase 22.

### 3.1 Epistemic State & Metric Contracts (`src/engine/models/metric_state.py`)

```python
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, computed_field, model_validator


class EpistemicState(str, Enum):
    """Defines the verification ontology of an assessed metric."""
    VERIFIED = "VERIFIED"                                 # Corroborated by explicit documentary/transcript evidence
    UNCORROBORATED = "UNCORROBORATED"                     # Self-assessed without contradicting or supporting evidence
    PROVISIONAL_CONTRADICTED = "PROVISIONAL_CONTRADICTED" # Self-assessment conflicts with qualitative evidence
    MISSING_DATA = "MISSING_DATA"                         # Circuit breaker state; no data provided


class ContradictionRecord(BaseModel):
    """Immutable audit record of an epistemic divergence."""
    contradicting_evidence_id: str = Field(..., description="Unique identifier of the conflicting transcript/document chunk.")
    verbatim_quote: str = Field(..., description="Exact lexical substring demonstrating the contradiction.")
    semantic_divergence_score: float = Field(..., ge=0.0, le=1.0, description="Cosine/NLI contradiction confidence.")
    audit_remediation_directive: str = Field(..., description="Required field validation action to resolve provisional status.")


class CalibratedMetric(BaseModel):
    """
    Replaces primitive float scores across the Argon Engine.
    Decouples empirical magnitude from epistemic certainty.
    """
    kpi_id: str = Field(..., pattern=r"^KPI-[A-Z0-9_]+$")
    raw_self_assessment: Optional[float] = Field(None, ge=1.0, le=5.0)
    calibrated_value: Optional[float] = Field(None, ge=1.0, le=5.0)
    epistemic_state: EpistemicState = Field(default=EpistemicState.UNCORROBORATED)
    corroborating_evidence_ids: List[str] = Field(default_factory=list)
    contradiction_records: List[ContradictionRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def enforce_epistemic_invariants(self) -> "CalibratedMetric":
        if self.epistemic_state == EpistemicState.PROVISIONAL_CONTRADICTED:
            if not self.contradiction_records:
                raise ValueError("PROVISIONAL_CONTRADICTED state requires at least one ContradictionRecord.")
            # INVARIANT: Never collapse calibrated_value to 1.00 on contradiction. Retain self-assessment.
            if self.raw_self_assessment is not None and self.calibrated_value != self.raw_self_assessment:
                self.calibrated_value = self.raw_self_assessment
        return self

    @computed_field
    @property
    def formatted_display(self) -> str:
        """Generates the publication-grade representation of the metric."""
        if self.epistemic_state == EpistemicState.MISSING_DATA or self.calibrated_value is None:
            return "N/A [DATA OMITTED]"
        if self.epistemic_state == EpistemicState.PROVISIONAL_CONTRADICTED:
            return f"{self.calibrated_value:.2f}* [PROVISIONAL]"
        return f"{self.calibrated_value:.2f}"

    @computed_field
    @property
    def actuarial_precision_weight(self) -> float:
        """
        Scalar [0.1, 1.0] governing the variance of the Beta distribution in FAIR simulations.
        Lower values induce wider confidence intervals (higher epistemic uncertainty).
        """
        mapping = {
            EpistemicState.VERIFIED: 1.00,
            EpistemicState.UNCORROBORATED: 0.65,
            EpistemicState.PROVISIONAL_CONTRADICTED: 0.20,
            EpistemicState.MISSING_DATA: 0.10,
        }
        return mapping[self.epistemic_state]
```

### 3.2 Non-Punitive Contradiction Engine (`src/engine/epistemic/contradiction_engine.py`)

```python
from typing import List
from src.engine.models.metric_state import CalibratedMetric, ContradictionRecord, EpistemicState


class ContradictionResolutionEngine:
    """
    Evaluates quantitative self-assessments against qualitative evidence graphs.
    Enforces the Axiom of Epistemic Stratification (Zero False Certainty).
    """
    CONTRADICTION_THRESHOLD: float = 0.75

    @classmethod
    def evaluate_metric(
        cls,
        kpi_id: str,
        self_assessed_score: float,
        corroborating_ids: List[str],
        detected_conflicts: List[ContradictionRecord]
    ) -> CalibratedMetric:
        """
        Determines the epistemic state of a metric without executing punitive score overrides.
        """
        severe_conflicts = [
            c for c in detected_conflicts 
            if c.semantic_divergence_score >= cls.CONTRADICTION_THRESHOLD
        ]

        if severe_conflicts:
            # ANTIPATTERN ERADICATED: We do NOT force calibrated_value = 1.00.
            # We preserve the self-assessed value and transition the state to PROVISIONAL_CONTRADICTED.
            return CalibratedMetric(
                kpi_id=kpi_id,
                raw_self_assessment=self_assessed_score,
                calibrated_value=self_assessed_score,
                epistemic_state=EpistemicState.PROVISIONAL_CONTRADICTED,
                corroborating_evidence_ids=corroborating_ids,
                contradiction_records=severe_conflicts
            )

        state = EpistemicState.VERIFIED if corroborating_ids else EpistemicState.UNCORROBORATED
        
        return CalibratedMetric(
            kpi_id=kpi_id,
            raw_self_assessment=self_assessed_score,
            calibrated_value=self_assessed_score,
            epistemic_state=state,
            corroborating_evidence_ids=corroborating_ids,
            contradiction_records=[]
        )
```

### 3.3 Lexical Specificity Compiler & Hallucination Guard (`src/engine/epistemic/entity_registry.py`)

```python
import re
from typing import Dict, Set, List, Tuple
from pydantic import BaseModel, Field


class VerifiedEntityRegistry(BaseModel):
    """
    Immutable symbol table mapping canonical technology/vendor tokens 
    to their exact source transcript evidence_ids.
    """
    # Map of lowercase vendor/product token -> Set of evidence_ids where it explicitly appears
    entity_to_evidence_map: Dict[str, Set[str]] = Field(default_factory=dict)
    
    # Global lexicon of known enterprise technology proper nouns to monitor
    monitored_proper_nouns: Dict[str, str] = Field(
        default_factory=lambda: {
            "bitlocker": "full-disk encryption mechanism",
            "entra id": "centralized identity provider",
            "active directory": "directory services infrastructure",
            "crowdstrike": "endpoint detection and response (EDR) platform",
            "splunk": "security information and event management (SIEM) system",
            "kubernetes": "container orchestration platform",
            "okta": "identity and access management (IAM) solution",
            "palo alto": "next-generation firewall (NGFW) appliance",
            "prisma": "cloud native application protection platform (CNAPP)",
            "cyberark": "privileged access management (PAM) vault",
            "aws": "cloud infrastructure provider",
            "azure": "cloud computing platform",
            "gcp": "cloud infrastructure environment",
            "servicenow": "IT service management (ITSM) workflow engine",
            "tenable": "vulnerability management scanner",
            "qualys": "vulnerability assessment platform",
        },
        description="Maps specific proper nouns to their vendor-agnostic functional archetypes."
    )

    def register_verified_mention(self, entity_token: str, evidence_id: str) -> None:
        normalized = entity_token.strip().lower()
        if normalized not in self.entity_to_evidence_map:
            self.entity_to_evidence_map[normalized] = set()
        self.entity_to_evidence_map[normalized].add(evidence_id)

    def is_entity_authorized(self, entity_token: str, active_evidence_ids: List[str]) -> bool:
        """
        Returns True if and only if the entity was explicitly mentioned in the 
        evidence chunks scoped to the current synthesis block.
        """
        normalized = entity_token.strip().lower()
        if normalized not in self.entity_to_evidence_map:
            return False
        authorized_sources = self.entity_to_evidence_map[normalized]
        return bool(authorized_sources.intersection(set(active_evidence_ids)))


class EpistemicNarrativeSanitizer:
    """
    Compiler pass that enforces Evidence-Based Specificity on LLM narrative outputs.
    Strips unverified vendor hallucinations and substitutes agnostic operational archetypes.
    """
    def __init__(self, registry: VerifiedEntityRegistry):
        self.registry = registry

    def compile_and_sanitize(
        self, 
        raw_narrative: str, 
        scoped_evidence_ids: List[str]
    ) -> Tuple[str, List[str]]:
        """
        Scans generated text for monitored proper nouns. If a noun is not backed by 
        scoped_evidence_ids, replaces it with its agnostic operational profile.
        
        Returns: (sanitized_narrative, list_of_intercepted_hallucinations)
        """
        sanitized_text = raw_narrative
        intercepted_hallucinations: List[str] = []

        # Sort keys by length descending to match multi-word entities (e.g., "entra id") first
        sorted_entities = sorted(
            self.registry.monitored_proper_nouns.keys(), 
            key=len, 
            reverse=True
        )

        for entity in sorted_entities:
            # Case-insensitive word-boundary regex
            pattern = re.compile(rf"\b{re.escape(entity)}\b", re.IGNORECASE)
            if pattern.search(sanitized_text):
                if not self.registry.is_entity_authorized(entity, scoped_evidence_ids):
                    archetype = self.registry.monitored_proper_nouns[entity]
                    sanitized_text = pattern.sub(archetype, sanitized_text)
                    intercepted_hallucinations.append(entity)

        return sanitized_text, intercepted_hallucinations
```

### 3.4 Dynamic FAIR Vulnerability Engine (`src/engine/actuarial/fair_vulnerability.py`)

```python
import numpy as np
from typing import Dict, List
from pydantic import BaseModel, Field
from src.engine.models.metric_state import CalibratedMetric, EpistemicState


class ControlMappingSpec(BaseModel):
    """Defines the structural relationship between a defending KPI and a Risk Tower."""
    kpi_id: str
    structural_weight: float = Field(..., gt=0.0, le=1.0, description="Relative weight w_{i,j} of this control.")
    effectiveness_ceiling: float = Field(..., gt=0.0, lt=1.0, description="Max theoretical mitigation \eta_i (e.g., 0.90).")


class RiskTowerVulnerabilityProfile(BaseModel):
    """Output contract containing the derived actuarial parameters for a specific Risk Tower."""
    risk_tower_id: str
    point_estimate_vulnerability: float = Field(..., ge=0.05, le=0.99)
    beta_alpha: float = Field(..., gt=0.0)
    beta_beta: float = Field(..., gt=0.0)
    effective_control_coverage: float = Field(..., ge=0.0, le=1.0)
    contains_provisional_controls: bool


class FairVulnerabilityEngine:
    """
    Actuarial derivation engine that computes continuous FAIR Vulnerability distributions
    from empirical KPI control maturities. Eradicates binary 0.80/0.95 hardcoding.
    """
    NON_LINEAR_MATURITY_EXPONENT: float = 1.35  # \gamma: Penalizes ad-hoc maturity (scores 1-2)
    VULN_FLOOR: float = 0.05                    # Minimum residual susceptibility (zero-day/insider baseline)
    VULN_CEILING: float = 0.99                  # Maximum susceptibility ceiling
    BASE_PRECISION_KAPPA: float = 45.0          # Base concentration parameter for Beta distribution

    @classmethod
    def derive_tower_vulnerability(
        cls,
        risk_tower_id: str,
        control_specs: List[ControlMappingSpec],
        assessed_metrics: Dict[str, CalibratedMetric]
    ) -> RiskTowerVulnerabilityProfile:
        """
        Computes Vuln = 1.0 - \sum (w_i * (Score_i / 5.0)^\gamma * \eta_i)
        and parameterizes a stochastic Beta(\alpha, \beta) distribution.
        """
        if not control_specs:
            raise ValueError(f"Risk Tower {risk_tower_id} has zero mapped control specifications.")

        total_weight = sum(spec.structural_weight for spec in control_specs)
        if not np.isclose(total_weight, 1.0, atol=1e-3):
            raise ValueError(f"Structural weights for {risk_tower_id} must sum to 1.0 (got {total_weight}).")

        aggregate_mitigation: float = 0.0
        weighted_precision: float = 0.0
        has_provisional: bool = False

        for spec in control_specs:
            metric = assessed_metrics.get(spec.kpi_id)
            
            # Handle Missing Data Circuit Breaker state conservatively
            if metric is None or metric.epistemic_state == EpistemicState.MISSING_DATA or metric.calibrated_value is None:
                normalized_maturity = 0.0  # Unverified/missing control provides zero assumed mitigation
                precision_weight = 0.10
                has_provisional = True
            else:
                if metric.epistemic_state == EpistemicState.PROVISIONAL_CONTRADICTED:
                    has_provisional = True
                
                # Normalize [1.0, 5.0] maturity scale to [0.0, 1.0] operational capability scale
                # Score of 1.0 (Initial/Ad-hoc) equates to 0.05 base capability, 5.0 equates to 1.0
                linear_capability = max(0.05, (metric.calibrated_value - 1.0) / 4.0)
                normalized_maturity = float(linear_capability ** cls.NON_LINEAR_MATURITY_EXPONENT)
                precision_weight = metric.actuarial_precision_weight

            control_mitigation = spec.structural_weight * normalized_maturity * spec.effectiveness_ceiling
            aggregate_mitigation += control_mitigation
            weighted_precision += spec.structural_weight * precision_weight

        # Point estimate derivation bounded by actuarial floor and ceiling
        raw_vulnerability = 1.0 - aggregate_mitigation
        point_vuln = float(np.clip(raw_vulnerability, cls.VULN_FLOOR, cls.VULN_CEILING))

        # Parameterize Beta distribution: \alpha = \mu * \kappa, \beta = (1 - \mu) * \kappa
        effective_kappa = max(4.0, cls.BASE_PRECISION_KAPPA * weighted_precision)
        alpha = point_vuln * effective_kappa
        beta = (1.0 - point_vuln) * effective_kappa

        return RiskTowerVulnerabilityProfile(
            risk_tower_id=risk_tower_id,
            point_estimate_vulnerability=round(point_vuln, 4),
            beta_alpha=round(alpha, 4),
            beta_beta=round(beta, 4),
            effective_control_coverage=round(aggregate_mitigation, 4),
            contains_provisional_controls=has_provisional
        )

    @staticmethod
    def sample_vulnerability_vector(
        profile: RiskTowerVulnerabilityProfile, 
        iterations: int = 100_000, 
        seed: int = 42
    ) -> np.ndarray:
        """Generates the stochastic vulnerability vector for FAIR Monte Carlo simulation."""
        rng = np.random.default_rng(seed)
        return rng.beta(a=profile.beta_alpha, b=profile.beta_beta, size=iterations)
```

---

## 4. QUALITY GATES & VERIFICATION ORACLES

To achieve Tier-1 (8+/10) certification and empirically prove the eradication of all three antipatterns, the CI/CD pipeline must enforce the following four deterministic Verification Oracles (`tests/oracles/test_phase22_invariants.py`). Pull requests failing any oracle will be blocked at the compiler gate.

### Oracle 1: The Zero-Hallucination Epistemic Gate
* **Test Vector:** Inject a synthetic assessment state where `KPI-IAM_01` has a self-assessed score of `5.0`, and `scoped_evidence_ids = []` (zero interview transcripts provided). Pass a simulated LLM narrative containing `"The organization utilizes Microsoft Entra ID and CyberArk to enforce zero-trust privileges."` into `EpistemicNarrativeSanitizer.compile_and_sanitize()`.
* **Pass Criteria:** 
  1. `intercepted_hallucinations` must equal `["entra id", "cyberark"]`.
  2. Output narrative must contain zero instances of `"Entra ID"` or `"CyberArk"`, substituting `"centralized identity provider"` and `"privileged access management (PAM) vault"`.
  3. Re-run with `"entra id"` registered to `ev_101` and `scoped_evidence_ids = ["ev_101"]`. Assert that `"Entra ID"` is preserved while `"CyberArk"` is still stripped.

### Oracle 2: The Actuarial Continuity & Variance Gate
* **Test Vector:** Instantiate 10 distinct Risk Towers with varying KPI maturity vectors ranging continuously from `1.0` to `5.0`. Execute `FairVulnerabilityEngine.derive_tower_vulnerability()` across all 10 towers.
* **Pass Criteria:**
  1. **Static AST Inspection:** Parse the AST of `src/engine/synthesizers/chapter4_synthesizer.py`. Assert that the float literals `0.8`, `0.80`, and `0.95` do not exist inside any conditional assignment node.
  2. **Monotonicity Invariant:** Assert that for any two control vectors $\vec{M}_A > \vec{M}_B$, the derived vulnerability strictly satisfies $\mu_{V,A} < \mu_{V,B}$.
  3. **Non-Degeneracy Invariant:** Assert that the cardinality of unique `point_estimate_vulnerability` values across the 10 diverse risk towers is `10` (100% unique differentiation), and that the sampled Monte Carlo vector exhibits a non-zero standard deviation ($\sigma > 0.015$).

### Oracle 3: The Non-Punitive Contradiction Gate
* **Test Vector:** Execute `ContradictionResolutionEngine.evaluate_metric()` with `kpi_id="KPI-K8S_04"`, `self_assessed_score=4.25`, and a `ContradictionRecord` with `semantic_divergence_score=0.91`.
* **Pass Criteria:**
  1. Assert `metric.calibrated_value == 4.25` (Strict inequality against `1.00`).
  2. Assert `metric.epistemic_state == EpistemicState.PROVISIONAL_CONTRADICTED`.
  3. Assert `metric.formatted_display == "4.25* [PROVISIONAL]"`.
  4. Pass this metric into `FairVulnerabilityEngine` and assert that the resulting Beta distribution variance ($\text{Var}(X) = \frac{\alpha\beta}{(\alpha+\beta)^2(\alpha+\beta+1)}$) is at least $3.0\times$ wider than an identical metric in the `VERIFIED` state.

### Oracle 4: The Lexical Purity & Zero-Hardcoding Gate
* **Test Vector:** Execute a repository-wide regex and AST scan across `src/` and `docs/`.
* **Pass Criteria:**
  1. Zero matches for Spanish lexical tokens (e.g., `\b(riesgo|amenaza|vulnerabilidad|puntaje|evidencia|madurez|capítulo|brecha)\b`).
  2. Zero matches for client-specific enterprise strings or hardcoded organizational identifiers outside of isolated test fixtures.