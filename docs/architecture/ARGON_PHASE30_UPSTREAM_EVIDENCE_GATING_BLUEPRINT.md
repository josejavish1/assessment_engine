Here is the exhaustive, publication-grade Master Implementation Blueprint for `docs/architecture/ARGON_PHASE30_UPSTREAM_EVIDENCE_GATING_BLUEPRINT.md`.

```markdown
# ARGON PHASE 30: UPSTREAM EPISTEMIC EVIDENCE GATING BLUEPRINT

**Document ID:** `ARGON-ARCH-P30-UEG`  
**Status:** MANDATORY EXECUTION DIRECTIVE  
**Target Architecture:** Deterministic Pre-Prompt Compiler & Polymorphic Schema Engine  
**Language Invariant:** 100% Technical English (Zero Localized String Manipulation)  

---

## 1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT

### 1.1 Post-Mortem of the Post-Generation Sanitization Failure (Phases 27–29)
In Phases 27 through 29, the architecture attempted to enforce epistemic discipline via post-generation lexical mutation (`LexicalEpistemicSanitizer` and `TechnicalSpecificityGuard`). This approach relied on regular expressions and token-replacement matrices to scrub hallucinated vendor names, protocols, and unverified architectural states from the LLM’s output stream.

From a compiler design and formal linguistics perspective, post-generation regex replacement over natural language is a **Chomsky Hierarchy Type-3 (Regular Grammar) tool attempting to mutate a Type-0 (Unrestricted/Context-Sensitive) generative output**. This structural mismatch guarantees catastrophic failure modes:
1. **Syntactic Corruption & Noun Duplication:** Natural languages (especially inflected Romance languages like Spanish) encode grammatical gender, number, and prepositional governance across entire clauses. Replacing a specific noun phrase (e.g., a proprietary storage array) with a generic macro-term without parsing the full Abstract Syntax Tree (AST) of the sentence yields degenerate syntax, dangling modifiers, and redundant appositions.
2. **Persistence of the Underlying Hallucinated Proposition:** Scrubbing the token `"SAML 2.0"` to `"authentication protocol"` does not erase the surrounding hallucinated claim that the federated identity provider suffers from cryptographic token-replay vulnerabilities. The morphological wrapper changes, but the fabricated forensic premise survives intact.
3. **Semantic Drift (KPI-to-Claim Decoupling):** Post-processing cannot detect when a low maturity score in an administrative domain (e.g., Third-Party Vendor Risk Management) has been hallucinated by the LLM into a kinetic physical security failure (e.g., CCTV blind spots).

### 1.2 The Tier-1 Standard: Upstream Epistemic Compilation
In safety-critical systems and actuarial reporting, **you do not sanitize a corrupted output stream; you restrict the input state space and constrain the target compilation schema.** 

Phase 30 establishes a purely deterministic, 100% code-driven **Upstream Epistemic Evidence Gating** architecture. The core axiom of Phase 30 is:

$$\forall c \in \text{Claims}, \quad \text{Evidence}(c) = \emptyset \implies c \notin \text{PromptContext} \land \text{Schema}(c) \equiv \text{GovernanceOnly}$$

1. **Pre-Prompt Context Pruning:** If a factual dimension is `UNKNOWN` or belongs to an orthogonal operational domain, it is physically stripped from the memory space before the prompt string is allocated.
2. **Ontology-Bound Claim Compilation (OBCC):** Every quantitative Key Performance Indicator (KPI) is bound to an immutable domain ontology. The LLM is structurally prohibited from crossing ontological boundaries when synthesizing findings.
3. **Polymorphic Schema Enforcement (Discriminated Unions):** We leverage Constrained Decoding at the LLM inference layer via Pydantic Discriminated Unions. If a low-scoring KPI lacks verified empirical transcript citations, the compiler swaps the target output schema for that finding to a restricted `ProcessGovernanceFinding` class, which physically lacks the JSON keys required to express technical asset configurations, protocols, or architectural topologies.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

```
====================================================================================================
                          PHASE 30 UPSTREAM EPISTEMIC COMPILATION PIPELINE
====================================================================================================

 [ Raw Assessment Data ]     [ Empirical Transcripts ]     [ Shared Fact Registry ]
           |                             |                            |
           v                             v                            v
+----------------------------------------------------------------------------------+
| 1. SHARED FACT 3VL PRE-EMPTOR (Phase 30.4)                                       |
|    - Evaluates Kleene 3-Valued Logic (TRUE, FALSE, UNKNOWN).                     |
|    - Drops UNKNOWN states from actionable risk arrays.                           |
|    - Emits Negative Epistemic Constraints (Prohibition Directives).              |
+----------------------------------------------------------------------------------+
                                         |
                                         v
+----------------------------------------------------------------------------------+
| 2. STRICT PAYLOAD ISOLATOR (Phase 30.2)                                          |
|    - Applies Tower Scope Matrix (Contextual Firewall).                           |
|    - Strips T1-T7 physical/logical asset inventories from T8 (Governance).       |
+----------------------------------------------------------------------------------+
                                         |
                                         v
+----------------------------------------------------------------------------------+
| 3. ONTOLOGY-BOUND CLAIM COMPILER (Phase 30.3)                                    |
|    - Evaluates Citation Registry for each anomalous KPI.                         |
|    - Binds KPI to Strict Domain Ontology (prevents Vendor -> CCTV drift).        |
|    - Assigns Epistemic Mode:                                                     |
|        * Citations > 0  --> Mode: EMPIRICAL_TECHNICAL                            |
|        * Citations == 0 --> Mode: CAPABILITY_GOVERNANCE_ONLY                     |
+----------------------------------------------------------------------------------+
                                         |
                                         v
+----------------------------------------------------------------------------------+
| 4. POLYMORPHIC SCHEMA GENERATOR (Constrained Decoding)                           |
|    - Compiles dynamic Pydantic Discriminated Union response model.               |
|    - Physically omits technical JSON fields for CAPABILITY_GOVERNANCE_ONLY mode. |
+----------------------------------------------------------------------------------+
                                         |
                                         v
                           [ LLM Structured Inference ]
```

---

### Phase 30.1: Dismantling the Post-Generation Sanitizers

**Objective:** Permanently eradicate all regex-based text mutation, lexical scrubbing, and post-generation string replacement pipelines to restore 100% grammatical fidelity in the target output language.

#### Architectural Execution Steps:
1. **Decommission & Purge Modules:**
   - Delete `src/sanitizers/lexical_epistemic_sanitizer.py` (`LexicalEpistemicSanitizer`).
   - Delete `src/guards/technical_specificity_guard.py` (`TechnicalSpecificityGuard`).
   - Purge all localized replacement dictionaries, regex pattern registries, and fallback synonym tables from the configuration tree.
2. **Unbind Pipeline Hooks:**
   - Remove all post-inference middleware hooks in the orchestration engine that intercept LLM response payloads prior to DOCX rendering.
3. **Repurpose Detection Logic as Read-Only Verification Oracles:**
   - The entity-recognition patterns previously used to *replace* text must be refactored into pure, side-effect-free boolean evaluators within the test suite (`tests/oracles/epistemic_leak_detector.py`).
   - In production, if an epistemic violation occurs, the system must raise a hard `EpistemicBoundaryViolationError` and trigger a deterministic schema-constrained retry, **never** a silent string replacement.

---

### Phase 30.2: Upstream Context Filtration & Strict Payload Isolation

**Objective:** Eliminate Tower Context Contamination (specifically preventing Tower 8 Governance from receiving and regurgitating hardware/software inventories such as HCI nodes, storage arrays, or industrial control systems).

#### Architectural Execution Steps:
1. **The Tower Epistemic Scope Matrix (`TowerScopeMatrix`):**
   - Implement a deterministic access-control matrix that governs the exact slices of the global `AssessmentState` each Tower is permitted to read during prompt compilation.
   - Classify all ingested facts into strict taxonomic strata:
     - `STRATUM_PHYSICAL_INFRA` (Facilities, cabling, power, cooling, physical security).
     - `STRATUM_LOGICAL_COMPUTE_STORAGE` (Hypervisors, storage arrays, SAN/NAS, container orchestration).
     - `STRATUM_NETWORK_TOPOLOGY` (Routing, switching, firewalls, protocols).
     - `STRATUM_IDENTITY_ACCESS` (Directory services, authentication protocols, privilege vaults).
     - `STRATUM_INDUSTRIAL_OT` (SCADA, PLCs, RTUs, Purdue Model zones).
     - `STRATUM_ENTERPRISE_GOVERNANCE` (Policies, organizational charts, risk registers, compliance frameworks, SLA/OLA metrics, financial budgets).
2. **Hard Context Slicing (`UpstreamContextIsolator`):**
   - Before instantiating the prompt builder for any Tower $T_i$, the `UpstreamContextIsolator` executes a relational projection over the global context graph:
     $$\text{Context}(T_i) = \pi_{\text{AllowedStrata}(T_i)}(\text{GlobalAssessmentState})$$
   - For Tower 8 (Governance, Risk, and Compliance), $\text{AllowedStrata}(T_8) = \{\text{STRATUM\_ENTERPRISE\_GOVERNANCE}\}$.
   - Any data structure referencing hardware models, storage protocols, hypervisor clusters, or OT telemetry is physically dropped from memory when constructing the $T_8$ payload. The LLM cannot hallucinate or regurgitate hardware inventory in a Governance chapter if the inventory tokens do not exist in the context window.

---

### Phase 30.3: The Ontology-Bound Claim Compiler (OBCC) & Polymorphic Schema Enforcement

**Objective:** Eradicate KPI-to-Claim misalignment (e.g., vendor management scores generating physical CCTV findings) and Technical Specificity Hallucinations (e.g., inventing WORM storage, PAM session recording, SAML 2.0, RODC, or dual fiber paths from generic survey scores).

#### Architectural Execution Steps:
1. **Deterministic KPI Domain Ontology Binding:**
   - Every survey question / KPI in the global catalog is statically mapped in configuration (`config/ontology/kpi_domain_bindings.json`) to:
     - `primary_domain`: The exact operational taxonomy (e.g., `THIRD_PARTY_RISK_GOVERNANCE`).
     - `allowed_claim_subjects`: Exhaustive list of valid conceptual subjects the finding may address (e.g., `["SLA enforcement", "vendor risk assessments", "contractual right-to-audit", "supply chain visibility"]`).
     - `prohibited_adjacent_domains`: Explicit negative boundaries (e.g., `["PHYSICAL_PERIMETER_SECURITY", "SURVEILLANCE_SYSTEMS", "ACCESS_CONTROL_HARDWARE"]`).
2. **Epistemic Accreditation Evaluation:**
   - For every KPI flagged as a gap (score below threshold), the `OntologyBoundClaimCompiler` queries the `EmpiricalEvidenceRegistry` (populated exclusively from verified interview transcripts and ingested configuration files).
   - The compiler calculates the **Epistemic Accreditation State**:
     - If $\text{Card}(\text{VerifiedCitations}(\text{KPI}_k)) > 0$: State is `EPISTEMIC_MODE_EMPIRICAL_TECHNICAL`.
     - If $\text{Card}(\text{VerifiedCitations}(\text{KPI}_k)) = 0$: State is `EPISTEMIC_MODE_GOVERNANCE_CAPABILITY_ONLY`.
3. **Polymorphic Schema Enforcement via Discriminated Unions:**
   - Instead of asking the LLM to "be careful not to invent technical details" via system prompt prose (which LLMs routinely violate due to probabilistic attention drift), we change the **compiled output JSON schema** passed to the LLM’s structured output engine.
   - When `EPISTEMIC_MODE_GOVERNANCE_CAPABILITY_ONLY` is active for a finding:
     - The schema branch `CapabilityGovernanceFinding` is enforced.
     - Fields for `affected_technical_assets`, `protocols_and_mechanisms`, `architectural_topology_flaw`, and `empirical_citation_ids` are **physically absent** from the JSON schema definition for that slot.
     - The schema forces the LLM to populate `process_maturity_gap`, `missing_governance_standard`, and `organizational_impact`.
     - Furthermore, the schema injects the KPI's `primary_domain` as a literal constraint (`Literal[...]`), making it mathematically impossible for the token sampler to drift from Vendor Management to CCTV systems.

---

### Phase 30.4: Shared Fact Three-Valued Logic (3VL) Pre-emption

**Objective:** Prevent the LLM from inferring or hallucinating an actionable risk for an `UNKNOWN` shared fact by correlating it with adjacent metrics (e.g., claiming "severe vCPU oversubscription" when vCPU oversubscription is `UNKNOWN`, merely because host memory utilization is high).

#### Architectural Execution Steps:
1. **Kleene Three-Valued Logic ($K_3$) State Enforcement:**
   - Every metric in the `SharedFactRegistry` is strictly typed with a Kleene truth/epistemic state: `VERIFIED_PRESENT` ($\mathbf{T}$), `VERIFIED_ABSENT` ($\mathbf{F}$), or `EPISTEMICALLY_UNKNOWN` ($\mathbf{U}$).
2. **Correlation Severance & Cross-Inference Blocking:**
   - In standard Kleene logic, conjunction with an unknown yields unknown unless falsified: $\mathbf{T} \land \mathbf{U} = \mathbf{U}$.
   - Therefore, High Memory Pressure ($\mathbf{T}$) combined with vCPU Oversubscription ($\mathbf{U}$) **cannot** evaluate to a Composite Compute Exhaustion Risk ($\mathbf{T}$).
   - The `SharedFactPreEmptor` runs prior to prompt assembly and partitions all tower-relevant facts into two disjoint sets:
     - `ActionableVerifiedFacts`: Facts where state $\in \{\mathbf{T}, \mathbf{F}\}$.
     - `EpistemicBlindSpots`: Facts where state $= \mathbf{U}$.
3. **Structural Removal & Negative Epistemic Constraint Injection:**
   - Facts in `EpistemicBlindSpots` are **completely excluded** from the `ConfirmedAnomalies` payload array.
   - Instead, they are compiled into a dedicated, immutable `NegativeEpistemicConstraints` block in the prompt compilation envelope.
   - For each $\mathbf{U}$ fact, the compiler generates a deterministic **Inference Prohibition Directive**:
     - *Example:* `"FACT_ID: compute.vcpu_oversubscription_ratio | STATE: UNKNOWN | DIRECTIVE: Zero empirical telemetry exists for vCPU allocation ratios. You are strictly prohibited from inferring, estimating, or asserting CPU contention or vCPU oversubscription from memory utilization, storage latency, or host count."`

---

## 3. ARCHITECTURAL CONTRACTS

The following production-grade Python 3.11+ / Pydantic v2 architectural contracts define the exact data structures, compilers, and polymorphic schemas required to execute Phase 30.

```python
"""
FILE: src/architecture/epistemic_compiler.py
DESCRIPTION: Deterministic Upstream Epistemic Evidence Gating & Polymorphic Schema Engine.
INVARIANT: 100% Technical English. Zero post-generation regex mutation.
"""

from __future__ import annotations
from enum import Enum
from typing import Annotated, Dict, List, Literal, Optional, Set, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# 1. TAXONOMIC & EPISTEMIC ENUMERATIONS
# ============================================================================

class EpistemicState(str, Enum):
    """Kleene Three-Valued Logic (K3) Epistemic States for Shared Facts."""
    VERIFIED_PRESENT = "VERIFIED_PRESENT"      # Truth value: TRUE (Empirical evidence confirms existence/issue)
    VERIFIED_ABSENT = "VERIFIED_ABSENT"        # Truth value: FALSE (Empirical evidence confirms healthy/absent)
    EPISTEMICALLY_UNKNOWN = "UNKNOWN"          # Truth value: UNKNOWN (No empirical telemetry captured)


class EpistemicStratum(str, Enum):
    """Strict taxonomic strata for Upstream Context Isolation (Phase 30.2)."""
    PHYSICAL_INFRA = "STRATUM_PHYSICAL_INFRA"
    LOGICAL_COMPUTE_STORAGE = "STRATUM_LOGICAL_COMPUTE_STORAGE"
    NETWORK_TOPOLOGY = "STRATUM_NETWORK_TOPOLOGY"
    IDENTITY_ACCESS = "STRATUM_IDENTITY_ACCESS"
    INDUSTRIAL_OT = "STRATUM_INDUSTRIAL_OT"
    ENTERPRISE_GOVERNANCE = "STRATUM_ENTERPRISE_GOVERNANCE"


class OperationalDomain(str, Enum):
    """Canonical Operational Domains for Ontology-Bound Claim Compilation (Phase 30.3)."""
    THIRD_PARTY_VENDOR_GOVERNANCE = "THIRD_PARTY_VENDOR_GOVERNANCE"
    PHYSICAL_PERIMETER_SURVEILLANCE = "PHYSICAL_PERIMETER_SURVEILLANCE"
    STORAGE_RESILIENCE_BACKUP = "STORAGE_RESILIENCE_BACKUP"
    PRIVILEGED_ACCESS_GOVERNANCE = "PRIVILEGED_ACCESS_GOVERNANCE"
    DIRECTORY_FEDERATION_ARCHITECTURE = "DIRECTORY_FEDERATION_ARCHITECTURE"
    TELECOM_PATHWAY_REDUNDANCY = "TELECOM_PATHWAY_REDUNDANCY"
    COMPUTE_CAPACITY_MANAGEMENT = "COMPUTE_CAPACITY_MANAGEMENT"
    ENTERPRISE_RISK_MANAGEMENT = "ENTERPRISE_RISK_MANAGEMENT"


class FindingEpistemicMode(str, Enum):
    """Discriminator values for Polymorphic Finding Schemas."""
    EMPIRICAL_TECHNICAL = "EMPIRICAL_TECHNICAL"
    CAPABILITY_GOVERNANCE_ONLY = "CAPABILITY_GOVERNANCE_ONLY"


# ============================================================================
# 2. UPSTREAM INPUT CONTRACTS (ONTOLOGY, CITATIONS, SHARED FACTS)
# ============================================================================

class EmpiricalCitation(BaseModel):
    """Immutable record of an empirical fact extracted from transcripts or configs."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    citation_id: str = Field(..., pattern=r"^CIT-[A-Z0-9]{6,12}$")
    source_artifact: str = Field(..., description="Exact transcript or config filename.")
    verbatim_excerpt: str = Field(..., min_length=10)
    verified_technical_entities: List[str] = Field(
        default_factory=list,
        description="Explicit technical protocols/products verified in this excerpt (e.g., 'SAML 2.0', 'NetApp')."
    )


class KPIOntologyBinding(BaseModel):
    """Static ontological boundary definition for a single assessment KPI."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    kpi_id: str
    kpi_title: str
    stratum: EpistemicStratum
    primary_domain: OperationalDomain
    allowed_claim_subjects: List[str] = Field(..., min_length=1)
    prohibited_adjacent_domains: List[OperationalDomain] = Field(default_factory=list)


class SharedFactRecord(BaseModel):
    """Single authoritative metric in the cross-tower Shared Fact Registry."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_id: str
    stratum: EpistemicStratum
    domain: OperationalDomain
    metric_name: str
    epistemic_state: EpistemicState
    verified_value: Optional[Union[float, int, str, bool]] = None
    citation_ids: List[str] = Field(default_factory=list)
    prohibited_proxy_metrics: List[str] = Field(
        default_factory=list,
        description="Metrics that MUST NOT be used to infer this fact when state is UNKNOWN."
    )

    @model_validator(mode="after")
    def enforce_3vl_consistency(self) -> SharedFactRecord:
        if self.epistemic_state == EpistemicState.EPISTEMICALLY_UNKNOWN:
            if self.verified_value is not None or len(self.citation_ids) > 0:
                raise ValueError(f"Fact '{self.fact_id}' is UNKNOWN but contains value or citations.")
        else:
            if self.verified_value is None:
                raise ValueError(f"Fact '{self.fact_id}' is VERIFIED but lacks a verified_value.")
        return self


class EvaluatedKPIAnomaly(BaseModel):
    """Represents a low-scoring KPI entering the compilation pipeline."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    kpi_id: str
    quantitative_score: float = Field(..., ge=0.0, le=5.0)
    ontology: KPIOntologyBinding
    linked_citations: List[EmpiricalCitation] = Field(default_factory=list)


# ============================================================================
# 3. POLYMORPHIC OUTPUT SCHEMAS (DISCRIMINATED UNIONS FOR CONSTRAINED DECODING)
# ============================================================================

class BaseFindingContract(BaseModel):
    """Base schema shared by all compiled findings."""
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(..., description="Deterministic finding identifier mapped 1:1 to source KPI.")
    source_kpi_id: str = Field(..., description="Must match the exact KPI ID being evaluated.")
    bound_operational_domain: OperationalDomain = Field(
        ...,
        description="Strictly locked to the source KPI's primary_domain. Cross-domain drift is prohibited."
    )
    executive_summary: str = Field(
        ...,
        min_length=30,
        max_length=500,
        description="High-level synthesis of the gap within the bound operational domain."
    )


class EmpiricalTechnicalFinding(BaseFindingContract):
    """
    UNLOCKED TECHNICAL SCHEMA:
    Permitted ONLY when the source KPI has >= 1 verified EmpiricalCitations.
    Allows the LLM to articulate specific protocols, topologies, and asset flaws.
    """
    epistemic_mode: Literal[FindingEpistemicMode.EMPIRICAL_TECHNICAL] = FindingEpistemicMode.EMPIRICAL_TECHNICAL
    
     backing_citation_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Mandatory reference to verified EmpiricalCitation IDs."
    )
    verified_technical_entities_referenced: List[str] = Field(
        ...,
        description="Must be a strict subset of the verified_technical_entities in the backing citations."
    )
    architectural_and_protocol_analysis: str = Field(
        ...,
        min_length=50,
        description="Detailed forensic analysis of the verified technical architecture, protocols, or configurations."
    )
    technical_remediation_blueprint: str = Field(
        ...,
        min_length=50,
        description="Engineering-grade remediation targeting the verified technical assets."
    )


class CapabilityGovernanceFinding(BaseFindingContract):
    """
    RESTRICTED GOVERNANCE/CAPABILITY SCHEMA:
    Enforced automatically when a KPI has ZERO empirical transcript citations (Survey-only gap).
    
    STRUCTURAL INVARIANT:
    Notice the complete physical absence of fields for technical entities, protocols,
    hardware models, or architectural topologies. The LLM is structurally forced into
    a Process/Governance/Capability maturity posture.
    """
    epistemic_mode: Literal[FindingEpistemicMode.CAPABILITY_GOVERNANCE_ONLY] = (
        FindingEpistemicMode.CAPABILITY_GOVERNANCE_ONLY
    )

    unverified_technical_speculation_prohibition_ack: Literal[True] = Field(
        ...,
        description="Must be set to True. Confirms zero unverified protocols, vendors, or topologies are asserted."
    )
    capability_maturity_deficiency: str = Field(
        ...,
        min_length=50,
        description=(
            "Analysis of the organizational capability, process control, or governance maturity gap "
            "indicated by the quantitative survey score, strictly restricted to the bound_operational_domain. "
            "PROHIBITED: Do not mention specific hardware vendors, protocols (e.g., SAML, WORM, RODC), "
            "or physical infrastructure layouts."
        )
    )
    governance_and_control_impact: str = Field(
        ...,
        min_length=40,
        description="Impact on policy enforcement, operational oversight, compliance accountability, or SLA adherence."
    )
    process_and_policy_remediation: str = Field(
        ...,
        min_length=40,
        description="Remediation focused on governance frameworks, standard operating procedures, and audit controls."
    )


# The Polymorphic Discriminated Union
PolymorphicFinding = Annotated[
    Union[EmpiricalTechnicalFinding, CapabilityGovernanceFinding],
    Field(discriminator="epistemic_mode")
]


class TowerGenerationOutputContract(BaseModel):
    """Top-level schema passed to the LLM Structured Outputs API."""
    model_config = ConfigDict(extra="forbid")

    tower_id: str
    compiled_findings: List[PolymorphicFinding]


# ============================================================================
# 4. UPSTREAM COMPILATION ENGINES (PHASES 30.2, 30.3, 30.4)
# ============================================================================

class NegativeEpistemicDirective(BaseModel):
    """Compiled prohibition directive for UNKNOWN Shared Facts (Phase 30.4)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    fact_id: str
    metric_name: str
    directive_text: str


class CompiledFindingSlot(BaseModel):
    """Pre-compiled instruction slot dictating the exact epistemic mode for a single KPI."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_index: int
    kpi_id: str
    required_epistemic_mode: FindingEpistemicMode
    locked_operational_domain: OperationalDomain
    allowed_claim_subjects: List[str]
    prohibited_domains: List[OperationalDomain]
    authorized_citations: List[EmpiricalCitation]
    authorized_technical_vocabulary: List[str]


class CompiledTowerPromptEnvelope(BaseModel):
    """
    The final, sanitized, deterministic input payload sent to the Prompt Renderer.
    Contains ZERO cross-tower contamination and ZERO actionable UNKNOWN facts.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    tower_id: str
    permitted_strata: List[EpistemicStratum]
    actionable_shared_facts: List[SharedFactRecord]
    negative_epistemic_directives: List[NegativeEpistemicDirective]
    finding_compilation_slots: List[CompiledFindingSlot]


class UpstreamEpistemicCompiler:
    """
    Deterministic Pre-Prompt Compiler enforcing:
    1. Tower Context Isolation (Phase 30.2)
    2. Ontology-Bound Claim Compilation & Polymorphic Mode Assignment (Phase 30.3)
    3. Shared Fact 3VL Pre-emption (Phase 30.4)
    """

    # Deterministic Tower Scope Matrix (Phase 30.2)
    TOWER_STRATA_MATRIX: Dict[str, Set[EpistemicStratum]] = {
        "T1_COMPUTE_VIRTUALIZATION": {EpistemicStratum.LOGICAL_COMPUTE_STORAGE},
        "T2_NETWORK_CORE": {EpistemicStratum.NETWORK_TOPOLOGY},
        "T3_FACILITIES_PHYSICAL": {EpistemicStratum.PHYSICAL_INFRA},
        "T4_STORAGE_BACKUP": {EpistemicStratum.LOGICAL_COMPUTE_STORAGE},
        "T5_INDUSTRIAL_OT": {EpistemicStratum.INDUSTRIAL_OT, EpistemicStratum.NETWORK_TOPOLOGY},
        "T6_CYBERSECURITY_OPERATIONS": {EpistemicStratum.IDENTITY_ACCESS, EpistemicStratum.NETWORK_TOPOLOGY},
        "T7_APPLICATIONS_DATA": {EpistemicStratum.LOGICAL_COMPUTE_STORAGE},
        # T8 (Governance) is strictly isolated from all physical/logical hardware & OT strata
        "T8_GOVERNANCE_RISK_COMPLIANCE": {EpistemicStratum.ENTERPRISE_GOVERNANCE},
        "T9_IDENTITY_DIRECTORY": {EpistemicStratum.IDENTITY_ACCESS},
    }

    @classmethod
    def compile_tower_envelope(
        cls,
        tower_id: str,
        global_shared_facts: List[SharedFactRecord],
        tower_kpi_anomalies: List[EvaluatedKPIAnomaly],
    ) -> CompiledTowerPromptEnvelope:
        if tower_id not in cls.TOWER_STRATA_MATRIX:
            raise KeyError(f"Unregistered Tower ID '{tower_id}' in Epistemic Scope Matrix.")

        allowed_strata = cls.TOWER_STRATA_MATRIX[tower_id]

        # --------------------------------------------------------------------
        # STEP 1: Upstream Context Filtration (Phase 30.2)
        # Strip any shared fact belonging to a stratum outside the tower's scope.
        # --------------------------------------------------------------------
        scoped_facts = [
            fact for fact in global_shared_facts
            if fact.stratum in allowed_strata
        ]

        # --------------------------------------------------------------------
        # STEP 2: Shared Fact Three-Valued Logic Pre-emption (Phase 30.4)
        # Partition into Actionable Facts vs. Epistemic Blind Spots (UNKNOWN).
        # --------------------------------------------------------------------
        actionable_facts: List[SharedFactRecord] = []
        negative_directives: List[NegativeEpistemicDirective] = []

        for fact in scoped_facts:
            if fact.epistemic_state == EpistemicState.EPISTEMICALLY_UNKNOWN:
                proxy_warning = (
                    f" Do NOT infer or extrapolate this metric from proxy metrics: {fact.prohibited_proxy_metrics}."
                    if fact.prohibited_proxy_metrics else ""
                )
                directive = NegativeEpistemicDirective(
                    fact_id=fact.fact_id,
                    metric_name=fact.metric_name,
                    directive_text=(
                        f"EPISTEMIC BLIND SPOT [{fact.fact_id}]: The metric '{fact.metric_name}' is "
                        f"EPISTEMICALLY_UNKNOWN. You are strictly prohibited from asserting any risk, "
                        f"degradation, or over-allocation regarding '{fact.metric_name}'.{proxy_warning}"
                    )
                )
                negative_directives.append(directive)
            else:
                actionable_facts.append(fact)

        # --------------------------------------------------------------------
        # STEP 3: Ontology-Bound Claim Compilation (Phase 30.3)
        # Assign Polymorphic Epistemic Mode per KPI Anomaly.
        # --------------------------------------------------------------------
        compilation_slots: List[CompiledFindingSlot] = []

        for idx, anomaly in enumerate(tower_kpi_anomalies):
            # Enforce Stratum Isolation on KPIs as well
            if anomaly.ontology.stratum not in allowed_strata:
                raise PermissionError(
                    f"Contamination Violation: KPI '{anomaly.kpi_id}' belongs to stratum "
                    f"'{anomaly.ontology.stratum}', which is prohibited in Tower '{tower_id}'."
                )

            has_empirical_evidence = len(anomaly.linked_citations) > 0
            mode = (
                FindingEpistemicMode.EMPIRICAL_TECHNICAL
                if has_empirical_evidence
                else FindingEpistemicMode.CAPABILITY_GOVERNANCE_ONLY
            )

            # Extract strictly verified technical vocabulary from citations
            authorized_vocab: Set[str] = set()
            for cit in anomaly.linked_citations:
                for entity in cit.verified_technical_entities:
                    authorized_vocab.add(entity)

            slot = CompiledFindingSlot(
                slot_index=idx,
                kpi_id=anomaly.kpi_id,
                required_epistemic_mode=mode,
                locked_operational_domain=anomaly.ontology.primary_domain,
                allowed_claim_subjects=anomaly.ontology.allowed_claim_subjects,
                prohibited_domains=anomaly.ontology.prohibited_adjacent_domains,
                authorized_citations=anomaly.linked_citations if has_empirical_evidence else [],
                authorized_technical_vocabulary=sorted(list(authorized_vocab)),
            )
            compilation_slots.append(slot)

        return CompiledTowerPromptEnvelope(
            tower_id=tower_id,
            permitted_strata=sorted(list(allowed_strata), key=lambda s: s.value),
            actionable_shared_facts=actionable_facts,
            negative_epistemic_directives=negative_directives,
            finding_compilation_slots=compilation_slots,
        )

    @staticmethod
    def validate_llm_output_against_envelope(
        envelope: CompiledTowerPromptEnvelope,
        llm_output: TowerGenerationOutputContract,
    ) -> None:
        """
        Deterministic Post-Inference Contract Verifier.
        Does NOT mutate strings. Validates structural alignment between the
        compiled upstream envelope and the Polymorphic Union output.
        Raises hard exceptions to trigger structured retry on violation.
        """
        if len(llm_output.compiled_findings) != len(envelope.finding_compilation_slots):
            raise ValueError(
                f"Slot cardinality mismatch: Expected {len(envelope.finding_compilation_slots)} "
                f"findings, received {len(llm_output.compiled_findings)}."
            )

        for slot, finding in zip(envelope.finding_compilation_slots, llm_output.compiled_findings):
            # 1. Verify KPI Alignment
            if finding.source_kpi_id != slot.kpi_id:
                raise ValueError(
                    f"KPI Alignment Violation: Slot expected KPI '{slot.kpi_id}', "
                    f"finding reported '{finding.source_kpi_id}'."
                )

            # 2. Verify Ontological Domain Lock (Prevents Vendor -> CCTV drift)
            if finding.bound_operational_domain != slot.locked_operational_domain:
                raise ValueError(
                    f"Ontological Drift Violation on KPI '{slot.kpi_id}': "
                    f"Expected domain '{slot.locked_operational_domain}', got '{finding.bound_operational_domain}'."
                )

            # 3. Verify Polymorphic Union Branch Selection
            if finding.epistemic_mode != slot.required_epistemic_mode:
                raise TypeError(
                    f"Epistemic Mode Violation on KPI '{slot.kpi_id}': "
                    f"Compiler mandated '{slot.required_epistemic_mode}', LLM output '{finding.epistemic_mode}'."
                )

            # 4. If Technical Mode, verify citations and technical entities are strictly subsets of authorized
            if isinstance(finding, EmpiricalTechnicalFinding):
                authorized_cit_ids = {c.citation_id for c in slot.authorized_citations}
                for cid in finding.backing_citation_ids:
                    if cid not in authorized_cit_ids:
                        raise ValueError(
                            f"Hallucinated Citation ID '{cid}' in finding '{finding.finding_id}'."
                        )
                authorized_vocab_set = set(slot.authorized_technical_vocabulary)
                for entity in finding.verified_technical_entities_referenced:
                    if entity not in authorized_vocab_set:
                        raise ValueError(
                            f"Unauthorized Technical Entity '{entity}' in finding '{finding.finding_id}'. "
                            f"Allowed entities from citations: {authorized_vocab_set}"
                        )
```

---

## 4. VERIFICATION ORACLES

To guarantee zero regressions and prove deterministic compliance prior to DOCX rendering, the CI/CD pipeline must execute the following five formal Verification Oracles (`tests/oracles/test_phase30_epistemic_gating.py`).

### Oracle 1: The Sanitizer Extinction & Grammatical Integrity Oracle
* **Target Failure Mode:** Grammatical corruption and noun duplication caused by post-generation regex scrubbers.
* **Test Formulation:**
  1. Perform static AST inspection across the entire `src/` directory. Assert that `LexicalEpistemicSanitizer` and `TechnicalSpecificityGuard` do not exist and that `re.sub` is never invoked on LLM response strings.
  2. Pass synthetic LLM output strings containing complex multi-clause technical prose through the post-inference pipeline to the DOCX builder.
* **Pass Invariant:**
  $$\text{SHA256}(\text{LLM\_Structured\_Text\_Field}) \equiv \text{SHA256}(\text{Rendered\_DOCX\_Paragraph\_Text})$$
  Zero byte-level mutation occurs between structured JSON validation and document serialization.

### Oracle 2: The Ontological Boundary Enforcement Oracle (KPI-to-Claim Alignment)
* **Target Failure Mode:** Low survey score in "Vendor Management" generating a finding about "CCTV blind spots".
* **Test Formulation:**
  1. Instantiate an `EvaluatedKPIAnomaly` with `kpi_id="KPI-GOV-04"`, `primary_domain=OperationalDomain.THIRD_PARTY_VENDOR_GOVERNANCE`, and `prohibited_adjacent_domains=[OperationalDomain.PHYSICAL_PERIMETER_SURVEILLANCE]`.
  2. Compile the envelope via `UpstreamEpistemicCompiler.compile_tower_envelope()`.
  3. Attempt to validate a mocked LLM output where `bound_operational_domain` is set to `PHYSICAL_PERIMETER_SURVEILLANCE`.
* **Pass Invariant:**
  `validate_llm_output_against_envelope()` deterministically raises `ValueError("Ontological Drift Violation...")` 100% of the time.

### Oracle 3: The Polymorphic Capability-Only Gate Oracle (Zero Uncited Technical Specificity)
* **Target Failure Mode:** T4 inventing NetApp CSI/WORM, T6 inventing PAM vaults/session recording, T9 inventing SAML 2.0/RODC, or T3 inventing dual fiber pathways from survey scores with zero transcript citations.
* **Test Formulation:**
  1. Instantiate `EvaluatedKPIAnomaly` objects for T3, T4, T6, and T9 with `linked_citations=[]` (empty list).
  2. Run `UpstreamEpistemicCompiler.compile_tower_envelope()`.
  3. Assert that every generated `CompiledFindingSlot` has `required_epistemic_mode == FindingEpistemicMode.CAPABILITY_GOVERNANCE_ONLY` and `authorized_technical_vocabulary == []`.
  4. Attempt to deserialize an `EmpiricalTechnicalFinding` (or inject technical fields like `architectural_and_protocol_analysis`) into that slot.
* **Pass Invariant:**
  Pydantic validation and `validate_llm_output_against_envelope()` reject the payload with a hard `TypeError` / `ValidationError`. Only `CapabilityGovernanceFinding` instances are accepted.

### Oracle 4: The Kleene 3VL Pre-emption Oracle (Shared Fact Authority)
* **Target Failure Mode:** vCPU oversubscription is `UNKNOWN`, yet the LLM asserts "severe vCPU oversubscription" by correlating high host memory pressure.
* **Test Formulation:**
  1. Populate `global_shared_facts` with two records in `STRATUM_LOGICAL_COMPUTE_STORAGE`:
     - `fact_id="compute.host_memory_utilization"`, `epistemic_state=VERIFIED_PRESENT`, `verified_value="94%"`.
     - `fact_id="compute.vcpu_oversubscription_ratio"`, `epistemic_state=EPISTEMICALLY_UNKNOWN`, `prohibited_proxy_metrics=["compute.host_memory_utilization"]`.
  2. Compile the envelope for `T1_COMPUTE_VIRTUALIZATION`.
* **Pass Invariant:**
  1. `"compute.vcpu_oversubscription_ratio"` is **absent** from `envelope.actionable_shared_facts`.
  2. `envelope.negative_epistemic_directives` contains an explicit `NegativeEpistemicDirective` locking `"compute.vcpu_oversubscription_ratio"` and explicitly naming `"compute.host_memory_utilization"` as a prohibited proxy metric.

### Oracle 5: The Tower 8 Contextual Firewall Oracle (Zero Cross-Contamination)
* **Target Failure Mode:** Tower 8 (Governance) receiving and regurgitating hardware/OT inventory (SimpliVity, NetApp, SCADA).
* **Test Formulation:**
  1. Construct a comprehensive `global_shared_facts` array containing facts across all strata: `LOGICAL_COMPUTE_STORAGE` (SimpliVity, NetApp), `INDUSTRIAL_OT` (SCADA), `NETWORK_TOPOLOGY` (Core Switches), and `ENTERPRISE_GOVERNANCE` (IT Risk Register).
  2. Execute `UpstreamEpistemicCompiler.compile_tower_envelope(tower_id="T8_GOVERNANCE_RISK_COMPLIANCE", ...)`.
  3. Serialize the resulting `CompiledTowerPromptEnvelope` to a JSON string.
* **Pass Invariant:**
  1. `envelope.permitted_strata == [EpistemicStratum.ENTERPRISE_GOVERNANCE]`.
  2. All facts belonging to Compute, Storage, Network, Physical, and OT strata are 100% absent from `envelope.actionable_shared_facts` and `envelope.negative_epistemic_directives`.
  3. Attempting to pass a hardware-stratum KPI into `T8_GOVERNANCE_RISK_COMPLIANCE` immediately raises `PermissionError("Contamination Violation...")` before the LLM API is ever invoked.
```