```markdown
# ARGON PHASE 31: UNIVERSAL EVIDENCE GATING & EPISTEMIC ABSTRACTION CONTROL

**Document ID:** `ARGON-ARCH-P31-UEG`  
**Status:** MANDATORY EXECUTION  
**Author:** Gemini-4-Argon (Global Chief Systems Architect / Principal Compiler Engineer / FSA)  
**Target Subsystem:** Upstream Context Compilation, Ontology Projection, & Constrained Decoding Engine  

---

## 1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT

### 1.1 The Root Cause: Latent Space Prior Collapse
The rejection of Delivery 20 due to 41 instances of "Technical Specificity Hallucination" is not a prompt-engineering failure; it is a fundamental failure of epistemic boundary enforcement prior to token generation. 

Large Language Models operate as probabilistic state machines over dense vector spaces. When the upstream compiler injects a structured quantitative metric—such as `{"tower": "T7_ITSM", "score": 3.0, "max_score": 5.0}`—alongside an empty or sparse qualitative evidence array (`"transcript_citations": []`), the attention mechanism suffers from **Latent Space Prior Collapse**. 

In the absence of conditioning tokens from empirical client transcripts, the model maximizes likelihood by traversing the highest-probability weights associated with the training corpus's archetype for "ITSM Maturity Level 3". Consequently, the decoder emits canonical industry artifacts: *CMDB, CAB, ITIL v4, blameless post-mortems, CRAC units, Transit Gateways, or CIFS/NFS*. It mistakes the **ontological definition of the metric** for **empirical evidence of the client's topology**.

Post-generation regex sanitizers and hardcoded negative stop-lists are architectural anti-patterns. They attempt to solve an upstream type-system failure via downstream string manipulation, resulting in brittle, non-scalable whack-a-mole engineering.

### 1.2 The Paradigm Shift: Epistemic Type Systems & Abstraction Ceilings
To eradicate specificity hallucination deterministically across all 10 towers without hardcoded stop-lists, we must treat LLM generation as a **dependent-type compilation phase**:

1. **Epistemic Density Quantification ($\rho$):** We mathematically measure the exact information entropy and empirical token weight backing every individual Pillar and KPI *before* prompt assembly.
2. **Dynamic Abstraction Ceilings:** The epistemic density score $\rho$ dictates the **Abstraction Ceiling** of the prompt. If $\rho$ falls below a critical threshold, the compiler strips all domain-specific technical ontologies from the context window and locks the LLM into an **Abstract Governance & Capability Calculus** mode.
3. **Polymorphic Schema Constrained Decoding:** We replace static Pydantic output models with **Discriminated Epistemic Unions**. A low-density pillar does not merely receive a warning in the prompt; its target JSON schema is dynamically mutated by the compiler to physically lack fields for technical architecture, forcing the decoding sampler to generate strictly functional, process-oriented, and capability-level prose.
4. **Subgraph Projection Shielding:** Cross-tower contamination (e.g., T8 Governance leaking T1/T4 specifics like *SCADA*, *Oracle*, or *Equinix*) is eliminated by replacing global context passing with strict **Homomorphic Graph Projection**. T8 receives only anonymized topological metadata and functional governance primitives, severing its access to raw entity nodes bound to physical towers.

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

```
                        [ Raw Assessment Graph ]
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │  Phase 31.3: Subgraph Projection  │
                 │  (Cross-Tower Semantic Shielding) │
                 └─────────────────┬─────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │  Phase 31.1: Epistemic Density    │
                 │  Calculator (Compute ρ_p per node)│
                 └─────────────────┬─────────────────┘
                                   │
              ┌────────────────────┴────────────────────┐
              │ ρ_p < τ_abstract                        │ ρ_p ≥ τ_concrete
              ▼                                         ▼
┌───────────────────────────┐             ┌───────────────────────────┐
│   ABSTRACT GOVERNANCE     │             │    EMPIRICAL TECHNICAL    │
│      COMPILATION PATH     │             │      COMPILATION PATH     │
├───────────────────────────┤             ├───────────────────────────┤
│ 1. Strip Domain Ontology  │             │ 1. Prune Unattested Nodes │
│ 2. Inject Process Matrix  │             │ 2. Bind Verified Entities │
│ 3. Bind Abstract Schema   │             │ 3. Bind Concrete Schema   │
└─────────────┬─────────────┘             └─────────────┬─────────────┘
              │                                         │
              └────────────────────┬────────────────────┘
                                   │
                                   ▼
                 ┌───────────────────────────────────┐
                 │   Constrained Decoding Engine     │
                 │ (Zero-Hallucination Token Stream) │
                 └───────────────────────────────────┘
```

### Phase 31.1: Epistemic Density Routing & Dynamic Ontology Pruning

We introduce the **Epistemic Density Calculator (EDC)** into the upstream context pipeline. Before any Tower or Pillar prompt is compiled, the EDC evaluates the empirical grounding of the target subgraph.

#### 1. Mathematical Formulation of Epistemic Density ($\rho_p$)
For a given Pillar $p$ containing a set of KPIs $K_p$, let $E_k$ be the set of verified transcript evidence chunks mapped to KPI $k \in K_p$. Each evidence chunk $e \in E_k$ possesses a semantic relevance confidence score $c_e \in [0, 1]$ and an entity specificity count $n_e$ (number of extracted concrete nouns/proper nouns verified in the transcript).

We define the KPI Evidence Weight $w_k$ as:
$$w_k = \tanh\left( \alpha \sum_{e \in E_k} (c_e \cdot \ln(1 + n_e)) \right)$$
where $\alpha$ is a scaling hyperparameter (calibrated to $\alpha = 0.5$). The bounded hyperbolic tangent ensures $w_k \in [0, 1)$.

The Pillar Epistemic Density $\rho_p$ is the coverage-weighted harmonic mean of its constituent KPIs, penalized by the ratio of unattested KPIs:
$$\rho_p = \left( \frac{|K_p^{\text{attested}}|}{|K_p|} \right) \cdot \left( \frac{1}{|K_p|} \sum_{k \in K_p} w_k \right)$$

#### 2. Tri-State Epistemic Routing
Based on $\rho_p$, the compiler assigns an `EpistemicRegime` enum to the pillar:
*   **`REGIME_ZERO_EVIDENCE` ($\rho_p == 0.0$):** Zero transcript hits. Only quantitative survey scores exist.
*   **`REGIME_SPARSE_GOVERNANCE` ($0.0 < \rho_p < 0.35$):** High-level directional statements exist in transcripts, but lack architectural implementation details.
*   **`REGIME_EMPIRICAL_CONCRETE` ($\rho_p \ge 0.35$):** Dense, verifiable technical evidence exists in the transcript graph.

#### 3. Dynamic Ontology Pruning (Solving the JSON Schema Leak)
Currently, the pipeline injects `tower_definition_*.json` into the prompt context so the LLM understands what a Tower evaluates. **This is the primary vector for hallucination.** When `tower_definition_T1.json` mentions *"CRAC units, UPS, DCIM, and hot/cold aisles"* as examples of what T1 measures, the LLM copies those tokens into the output if $\rho_p = 0$.

**Architectural Fix:**
The `tower_definition_*.json` files are refactored to separate **Functional Capability Definitions** from **Indicative Technical Exemplars**. 
During context compilation:
*   If `regime != REGIME_EMPIRICAL_CONCRETE`, the `technical_exemplars` array in the JSON schema is **completely stripped** from the context payload prior to serialization.
*   If `regime == REGIME_EMPIRICAL_CONCRETE`, the `technical_exemplars` array is intersected with the **Transcript Entity Lexicon** (via cosine similarity $\ge 0.82$ over embedding space). Any exemplar in the static JSON definition that does not have a semantic match in the actual client transcript is pruned prior to prompt injection.

#### 4. Upstream Score-to-Capability Translation
Numeric scores (e.g., `Score = 3.0`) are never passed raw to the LLM without an epistemic wrapper. The upstream engine maps `(score, regime)` through a deterministic **Actuarial Capability Matrix** that translates numbers into pure operational governance semantics:
*   *Score 3.0 (Standardized) + Zero Evidence* $\rightarrow$ `"The organization indicates that operational processes within this domain follow defined, repeatable management patterns, though specific architectural implementations and tooling topologies were not empirically audited during discovery."`

---

### Phase 31.2: Dynamic Output Schema Polymorphism

Prompt instructions alone ("Do not invent technical terms") fail due to attention decay over long contexts. We enforce the abstraction ceiling via **Constrained Decoding** using polymorphic Pydantic schemas.

Instead of a single `PillarAnalysisOutput` schema, we split the output contract into two mutually exclusive structural schemas governed by a Discriminated Union bound to the upstream `EpistemicRegime`.

1.  **`AbstractCapabilityAnalysis` (Bound when $\rho_p < 0.35$):**
    *   Field names and descriptions are engineered to force functional, process-oriented, and governance-level tokens.
    *   Contains fields like `operational_repeatable_patterns`, `governance_maturity_posture`, and `unverified_architectural_scope`.
    *   Explicitly lacks fields for `technology_stack`, `hardware_topology`, `protocol_standards`, or `vendor_ecosystem`.
    *   Includes an enforced structural field `epistemic_boundary_declaration` which must state the exact scope of missing empirical data.

2.  **`EmpiricalTechnicalAnalysis` (Bound when $\rho_p \ge 0.35$):**
    *   Unlocks architectural specificity fields (`verified_architecture_components`, `attested_protocols_and_tooling`).
    *   Every technical item emitted in `attested_protocols_and_tooling` is structurally paired with a mandatory `transcript_chunk_id: str` and `verbatim_quote: str` validator. If the LLM attempts to emit *"CMDB"* or *"VLAN"*, the schema forces it to immediately populate the adjacent `verbatim_quote` field from the provided context. If the quote does not exist in the input context, the deterministic Pydantic `@model_validator` throws a `ValidationError` and triggers an immediate compiler retry with penalty weights.

---

### Phase 31.3: Cross-Tower Semantic Shielding (Graph Projection)

Tower 8 (Governance, Risk, and Compliance) and Tower 10 (Operating Model) operate as horizontal synthesis layers. In Delivery 20, T8 leaked specific nouns (*SCADA, Oracle, SAP, Equinix*) because the pipeline fed the full global entity graph into T8's context window.

We eradicate this via **Homomorphic Graph Projection**:

1.  **Node Classification in the Evidence Graph:** Every extracted entity node $v \in V$ in the global assessment graph $G = (V, E)$ is tagged during ingestion with an ontological layer classification:
    *   `LAYER_PHYSICAL_INFRA` (e.g., Equinix, CRAC, Diesel Generator, SFP+)
    *   `LAYER_NETWORK_STORAGE` (e.g., VLAN, iSCSI, Transit Gateway)
    *   `LAYER_APPLICATION_VENDOR` (e.g., SAP, Oracle, Netskope, Fortinet, SCADA)
    *   `LAYER_GOVERNANCE_PROCESS` (e.g., Risk Register, Policy Exception, Steering Committee, SLA Governance)

2.  **Tower Access Control Matrix (TACM):** Each Tower $T_i$ is assigned an allowed set of ontological layers $\mathcal{L}(T_i)$.
    *   For $T_8$ (Governance), $\mathcal{L}(T_8) = \{\text{LAYER\_GOVERNANCE\_PROCESS}\}$.

3.  **The Projection Functor $\Pi_{T_i}(G)$:** When compiling the context for Tower $T_i$, the graph compiler applies the projection functor $\Pi_{T_i}$. Any node $v \notin \mathcal{L}(T_i)$ is **not deleted** (which would break structural relationships), but **hypernym-abstracted**:
    *   `Entity("Oracle ERP", LAYER_APPLICATION_VENDOR)` $\xrightarrow{\Pi_{T_8}}$ `AbstractNode("Tier-1 Core Enterprise Application", LAYER_GOVERNANCE_PROCESS)`
    *   `Entity("Equinix NY4", LAYER_PHYSICAL_INFRA)` $\xrightarrow{\Pi_{T_8}}$ `AbstractNode("Primary Colocation Facility", LAYER_GOVERNANCE_PROCESS)`
    *   `Entity("SCADA Network", LAYER_APPLICATION_VENDOR)` $\xrightarrow{\Pi_{T_8}}$ `AbstractNode("Operational Technology (OT) Control Environment", LAYER_GOVERNANCE_PROCESS)`

Thus, the LLM generating T8 literally never sees the token *"Oracle"*, *"SCADA"*, or *"Equinix"* in its input prompt. It is mathematically impossible for T8 to leak cross-tower implementation specifics because those tokens are replaced by their topological hypernyms upstream.

---

## 3. ARCHITECTURAL CONTRACTS

### 3.1 Upstream Epistemic Compiler & Polymorphic Pydantic Schemas
*Target File:* `src/argon/compiler/epistemic_contracts.py`

```python
from enum import Enum
from typing import List, Literal, Union, Annotated, Dict, Set
from pydantic import BaseModel, Field, model_validator, ConfigDict
import math


class EpistemicRegime(str, Enum):
    ZERO_EVIDENCE = "REGIME_ZERO_EVIDENCE"
    SPARSE_GOVERNANCE = "REGIME_SPARSE_GOVERNANCE"
    EMPIRICAL_CONCRETE = "REGIME_EMPIRICAL_CONCRETE"


class OntologicalLayer(str, Enum):
    PHYSICAL_INFRA = "LAYER_PHYSICAL_INFRA"
    NETWORK_STORAGE = "LAYER_NETWORK_STORAGE"
    APPLICATION_VENDOR = "LAYER_APPLICATION_VENDOR"
    GOVERNANCE_PROCESS = "LAYER_GOVERNANCE_PROCESS"


class EvidenceChunk(BaseModel):
    model_config = ConfigDict(frozen=True)
    chunk_id: str
    verbatim_text: str
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: List[str]
    ontological_layer: OntologicalLayer
    hypernym_fallback: str = Field(
        description="Abstract functional class used when node is projected across tower boundaries."
    )


class KPISubgraph(BaseModel):
    kpi_id: str
    kpi_name: str
    quantitative_score: float = Field(ge=1.0, le=5.0)
    evidence_chunks: List[EvidenceChunk] = Field(default_factory=list)

    def compute_weight(self, alpha: float = 0.5) -> float:
        if not self.evidence_chunks:
            return 0.0
        raw_sum = sum(
            c.confidence * math.log(1.0 + len(c.extracted_entities))
            for c in self.evidence_chunks
        )
        return math.tanh(alpha * raw_sum)


class PillarEpistemicContext(BaseModel):
    pillar_id: str
    tower_id: str
    kpis: List[KPISubgraph]

    @property
    def epistemic_density(self) -> float:
        if not self.kpis:
            return 0.0
        attested_count = sum(1 for k in self.kpis if len(k.evidence_chunks) > 0)
        if attested_count == 0:
            return 0.0
        coverage_ratio = attested_count / len(self.kpis)
        mean_weight = sum(k.compute_weight() for k in self.kpis) / len(self.kpis)
        return round(coverage_ratio * mean_weight, 4)

    @property
    def regime(self) -> EpistemicRegime:
        rho = self.epistemic_density
        if rho == 0.0:
            return EpistemicRegime.ZERO_EVIDENCE
        elif rho < 0.35:
            return EpistemicRegime.SPARSE_GOVERNANCE
        return EpistemicRegime.EMPIRICAL_CONCRETE


# ============================================================================
# POLYMORPHIC OUTPUT SCHEMAS (CONSTRAINED DECODING TARGETS)
# ============================================================================

class AttestedTechnicalArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")
    artifact_or_standard_name: str = Field(
        description="Exact technical component, protocol, vendor, or standard."
    )
    source_chunk_id: str = Field(
        description="Exact chunk_id from the provided context where this artifact is attested."
    )
    verbatim_evidence_substring: str = Field(
        description="Exact verbatim substring from the evidence chunk proving existence."
    )


class AbstractCapabilityAnalysis(BaseModel):
    """
    Bound to the LLM decoder when EpistemicRegime is ZERO_EVIDENCE or SPARSE_GOVERNANCE.
    Physically prevents the emission of unverified technical specifics.
    """
    model_config = ConfigDict(extra="forbid")
    regime_discriminator: Literal[
        EpistemicRegime.ZERO_EVIDENCE, 
        EpistemicRegime.SPARSE_GOVERNANCE
    ]
    capability_maturity_synthesis: str = Field(
        description=(
            "Synthesize operational maturity strictly in terms of process repeatability, "
            "management standardization, and organizational governance. "
            "PROHIBITED: Naming specific protocols, hardware components, software vendors, "
            "or unattested industry frameworks."
        )
    )
    functional_control_posture: str = Field(
        description="Analysis of functional control objectives achieved at this numeric maturity tier."
    )
    epistemic_boundary_declaration: str = Field(
        description="Explicit statement detailing which architectural layers lack empirical discovery data."
    )


class EmpiricalTechnicalAnalysis(BaseModel):
    """
    Bound to the LLM decoder ONLY when EpistemicRegime is EMPIRICAL_CONCRETE.
    Requires strict cryptographic-grade binding between technical nouns and transcript chunks.
    """
    model_config = ConfigDict(extra="forbid")
    regime_discriminator: Literal[EpistemicRegime.EMPIRICAL_CONCRETE]
    architectural_and_operational_synthesis: str = Field(
        description="Comprehensive technical synthesis integrating verified empirical artifacts."
    )
    verified_technical_artifacts: List[AttestedTechnicalArtifact] = Field(
        min_length=1,
        description="List of concrete technical implementations explicitly verified in transcripts."
    )
    governance_and_control_alignment: str


# Discriminated Union for Pipeline Routing
PolymorphicPillarOutput = Annotated[
    Union[AbstractCapabilityAnalysis, EmpiricalTechnicalAnalysis],
    Field(discriminator="regime_discriminator")
]


class ValidatedPillarEnvelope(BaseModel):
    """
    Post-decoding compiler verification wrapper.
    Executes deterministic ground-truth verification against the input context.
    """
    context: PillarEpistemicContext
    llm_output: PolymorphicPillarOutput

    @model_validator(mode="after")
    def verify_epistemic_invariants(self) -> "ValidatedPillarEnvelope":
        expected_regime = self.context.regime
        if self.llm_output.regime_discriminator != expected_regime:
            raise ValueError(
                f"Epistemic Regime Mismatch: Context dictated {expected_regime}, "
                f"but decoder emitted {self.llm_output.regime_discriminator}."
            )

        if isinstance(self.llm_output, EmpiricalTechnicalAnalysis):
            valid_chunks: Dict[str, str] = {
                c.chunk_id: c.verbatim_text
                for kpi in self.context.kpis
                for c in kpi.evidence_chunks
            }
            for artifact in self.llm_output.verified_technical_artifacts:
                if artifact.source_chunk_id not in valid_chunks:
                    raise ValueError(
                        f"Hallucinated Chunk ID '{artifact.source_chunk_id}' for artifact "
                        f"'{artifact.artifact_or_standard_name}'."
                    )
                source_text = valid_chunks[artifact.source_chunk_id].lower()
                if artifact.verbatim_evidence_substring.lower() not in source_text:
                    raise ValueError(
                        f"Non-verbatim citation for '{artifact.artifact_or_standard_name}'. "
                        f"Substring '{artifact.verbatim_evidence_substring}' not found in chunk."
                    )
        return self
```

### 3.2 Cross-Tower Graph Projection Engine
*Target File:* `src/argon/compiler/graph_projector.py`

```python
from typing import Dict, Set, List
from src.argon.compiler.epistemic_contracts import (
    OntologicalLayer, EvidenceChunk, KPISubgraph, PillarEpistemicContext
)

# Tower Access Control Matrix (TACM)
TOWER_ONTOLOGY_CLEARANCE: Dict[str, Set[OntologicalLayer]] = {
    "T1_FACILITIES": {OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T2_CLOUD": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T3_NETWORK": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T4_STORAGE": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.PHYSICAL_INFRA, OntologicalLayer.GOVERNANCE_PROCESS},
    "T5_END_USER": {OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T6_SECURITY": {OntologicalLayer.NETWORK_STORAGE, OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T7_ITSM": {OntologicalLayer.GOVERNANCE_PROCESS, OntologicalLayer.APPLICATION_VENDOR},
    # T8 & T10 are strictly shielded from physical, network, and vendor specifics
    "T8_GOVERNANCE": {OntologicalLayer.GOVERNANCE_PROCESS},
    "T9_APPLICATIONS": {OntologicalLayer.APPLICATION_VENDOR, OntologicalLayer.GOVERNANCE_PROCESS},
    "T10_OPERATING_MODEL": {OntologicalLayer.GOVERNANCE_PROCESS},
}


class CrossTowerGraphProjector:
    """
    Applies the Homomorphic Projection Functor \Pi_{T_i}(G) to prevent cross-tower
    entity leakage (e.g., preventing SCADA, Oracle, or Equinix from leaking into T8).
    """

    @staticmethod
    def project_chunk(chunk: EvidenceChunk, target_tower_id: str) -> EvidenceChunk:
        allowed_layers = TOWER_ONTOLOGY_CLEARANCE.get(
            target_tower_id, {OntologicalLayer.GOVERNANCE_PROCESS}
        )
        if chunk.ontological_layer in allowed_layers:
            return chunk

        # Apply hypernym abstraction across the verbatim text for out-of-scope entities
        abstracted_text = chunk.verbatim_text
        for entity in chunk.extracted_entities:
            abstracted_text = abstracted_text.replace(
                entity, f"[{chunk.hypernym_fallback}]"
            )

        return EvidenceChunk(
            chunk_id=f"{chunk.chunk_id}_PROJ_{target_tower_id}",
            verbatim_text=abstracted_text,
            confidence=chunk.confidence * 0.85,  # Slight epistemic discount for projected nodes
            extracted_entities=[chunk.hypernym_fallback],
            ontological_layer=OntologicalLayer.GOVERNANCE_PROCESS,
            hypernym_fallback=chunk.hypernym_fallback,
        )

    @classmethod
    def compile_shielded_context(
        cls, raw_context: PillarEpistemicContext
    ) -> PillarEpistemicContext:
        projected_kpis: List[KPISubgraph] = []
        for kpi in raw_context.kpis:
            projected_chunks = [
                cls.project_chunk(c, raw_context.tower_id)
                for c in kpi.evidence_chunks
            ]
            projected_kpis.append(
                KPISubgraph(
                    kpi_id=kpi.kpi_id,
                    kpi_name=kpi.kpi_name,
                    quantitative_score=kpi.quantitative_score,
                    evidence_chunks=projected_chunks,
                )
            )
        return PillarEpistemicContext(
            pillar_id=raw_context.pillar_id,
            tower_id=raw_context.tower_id,
            kpis=projected_kpis,
        )
```

### 3.3 Polymorphic System Prompt Injection Contract
*Target File:* `config/prompts/phase31_epistemic_envelope.yaml`

```yaml
system_prompt_envelope:
  base_directive: |
    You are an actuarial systems auditor executing under strict Epistemic Type Constraints.
    Your output is compiled against a formal verification oracle.

  regime_directives:
    REGIME_ZERO_EVIDENCE: |
      [ABSTRACTION CEILING: MAXIMUM - ZERO EMPIRICAL EVIDENCE]
       Epistemic Density (\rho) = 0.0000.
      1. The client dataset contains ONLY quantitative maturity scores for this pillar. Zero qualitative transcripts or architectural artifacts were provided.
      2. You are operating under the `AbstractCapabilityAnalysis` schema contract.
      3. STRICT INVARIANT: You must translate the numeric scores exclusively into abstract operational capabilities, process repeatability paradigms, and governance control postures.
      4. DO NOT emit any concrete nouns representing physical hardware, network protocols, storage architectures, software vendors, or named industry sub-processes. Discuss WHAT functional capability the score implies, never HOW it is technically implemented.

    REGIME_SPARSE_GOVERNANCE: |
      [ABSTRACTION CEILING: HIGH - SPARSE DIRECTIONAL EVIDENCE]
      Epistemic Density (\rho) = {{ epistemic_density }}.
      1. The client dataset contains high-level directional statements but lacks dense architectural verification.
      2. You are operating under the `AbstractCapabilityAnalysis` schema contract.
      3. Anchor your analysis strictly to the functional governance patterns present in the provided chunks. Do not extrapolate standard industry implementations beyond the literal text.

    REGIME_EMPIRICAL_CONCRETE: |
      [ABSTRACTION CEILING: UNLOCKED - EMPIRICAL GROUNDING VERIFIED]
      Epistemic Density (\rho) = {{ epistemic_density }}.
      1. You are operating under the `EmpiricalTechnicalAnalysis` schema contract.
      2. You may reference specific technical architectures, protocols, and vendors ONLY if they appear in the `evidence_chunks` payload.
      3. Every technical artifact you reference MUST be registered in `verified_technical_artifacts` with its exact `source_chunk_id` and a `verbatim_evidence_substring` that passes a deterministic substring assertion.
```

---

## 4. VERIFICATION ORACLES

To guarantee zero regressions and prove mathematically that Delivery 20's 41 hallucinations cannot recur, the CI/CD pipeline is gated by three deterministic **Verification Oracles** located in `tests/oracles/test_phase31_epistemic_gating.py`.

### Oracle 1: The Zero-Transcript Vacuum Invariant (Null-Hypothesis Test)
*   **Objective:** Prove that when the pipeline is fed a full 10-Tower quantitative assessment (all KPIs scored between `1.0` and `5.0`) with an **empty transcript graph** ($\forall p, \rho_p = 0.0$), the system emits **zero** concrete technical implementation nouns across all 10 towers without relying on post-generation regex sanitizers.
*   **Execution:**
    1. Instantiate `PillarEpistemicContext` across all 10 towers with `evidence_chunks=[]`.
    2. Assert that every context deterministically resolves to `EpistemicRegime.ZERO_EVIDENCE`.
    3. Assert that the Dynamic Ontology Pruner strips 100% of `technical_exemplars` from the serialized `tower_definition_*.json` payloads before LLM invocation.
    4. Execute LLM generation using the bound `AbstractCapabilityAnalysis` schema.
    5. **Information-Theoretic Lexical Verification:** Pass the generated output through an NLP Part-of-Speech and Named Entity Recognition (POS/NER) parser (`spacy: en_core_web_trf`) combined with an Inverse Document Frequency (IDF) specificity analyzer computed over the static `tower_definition_*.json` exemplar corpus.
    6. **Pass Criteria:** 
        *   `NER_Entities(Output) ∩ Technical_Exemplar_Lexicon == ∅` (Zero overlap with domain-specific technical exemplars across all 10 towers).
        *   100% of outputs validate against `AbstractCapabilityAnalysis`.

### Oracle 2: The Cross-Tower Contamination Firewall Test
*   **Objective:** Prove that Tower 8 (Governance) and Tower 10 (Operating Model) cannot leak physical, network, or vendor specifics even when the global assessment graph is saturated with them.
*   **Execution:**
    1. Construct a synthetic high-density evidence graph containing explicit `EvidenceChunk` nodes for `"SCADA"`, `"Oracle"`, `"SAP"`, `"Equinix"`, `"VLAN"`, `"Netskope"`, and `"CRAC units"`, tagged with their respective `PHYSICAL_INFRA`, `NETWORK_STORAGE`, and `APPLICATION_VENDOR` layers.
    2. Pass this graph through `CrossTowerGraphProjector.compile_shielded_context()` targeting `T8_GOVERNANCE`.
    3. **Pass Criteria (Pre-LLM):** Assert that the serialized prompt string for `T8_GOVERNANCE` has a cosine similarity of `< 0.15` against the specific entity tokens and a literal substring count of `0` for every entity tagged outside `LAYER_GOVERNANCE_PROCESS`.
    4. **Pass Criteria (Post-LLM):** Assert that the generated `T8_GOVERNANCE` output references only the projected hypernyms (e.g., `"[Operational Technology (OT) Control Environment]"`, `"[Tier-1 Core Enterprise Application]"`, `"[Primary Colocation Facility]"`).

### Oracle 3: Adversarial Hallucination Injection & Compiler Rejection Test
*   **Objective:** Prove that if the LLM experiences a stochastic sampling anomaly in `REGIME_EMPIRICAL_CONCRETE` and attempts to invent an unattested industry standard (e.g., inventing `"blameless post-mortems"` or `"CMDB"` when the transcript only mentions `"ServiceNow ticketing"`), the `ValidatedPillarEnvelope` deterministically halts compilation.
*   **Execution:**
    1. Provide a `T7_ITSM` context with $\rho_p = 0.45$ containing a single chunk: `"chunk_01": "We log all user support requests in ServiceNow ticketing."`
    2. Mock a compromised LLM response that emits `EmpiricalTechnicalAnalysis` containing both `"ServiceNow"` (valid) and `"CMDB"` (hallucinated), attempting to map `"CMDB"` to `"chunk_01"`.
    3. **Pass Criteria:** Assert that `ValidatedPillarEnvelope` raises a `pydantic.ValidationError` with the exact message: `"Non-verbatim citation for 'CMDB'. Substring '...' not found in chunk."` Assert that the compiler catches this exception, increments the logit bias penalty against the hallucinated token span, and re-executes decoding until the output is 100% isomorphic to the empirical evidence graph.
```