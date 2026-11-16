# ARGON PHASE 27: DETERMINISTIC EVIDENCE GATING & EPISTEMIC CONTROL BLUEPRINT

**Document ID:** `ARGON-ARCH-P27-001`  
**File Path:** `docs/architecture/ARGON_PHASE27_EVIDENCE_GATING_BLUEPRINT.md`  
**Author:** Gemini-4-Argon (Global Chief Systems Architect / Principal Compiler Engineer / FSA)  
**Target Release:** Phase 27 (Post-Delivery 17 Remediation)  
**Status:** MANDATORY EXECUTION SPECIFICATION  

---

## 1. EXECUTIVE SUMMARY & EPISTEMIC PARADIGM SHIFT

### 1.1 Post-Mortem of Delivery 17 Defects
While Phases 24 through 26 successfully achieved deterministic closure over our actuarial calculation engine—stabilizing Factor Analysis of Information Risk (FAIR) Threat Event Frequency (TEF) derivations, Single Loss Expectancy (SLE) distributions, and Annualized Loss Expectancy (ALE) Monte Carlo bounds—the Tier-1 audit of Delivery 17 exposed a critical vulnerability in the **Epistemic Control Plane**. 

The generative layer continues to treat quantitative maturity scores and localized architectural entities as an open license for abductive reasoning. Because Large Language Models (LLMs) operate as probabilistic token predictors trained on generalized enterprise architectures, providing an unconstrained context payload alongside a numerical score induces **Plausible Architectural Hallucination**. The engine substitutes empirical truth with industry-standard archetypes.

Specifically, the audit isolated five systemic failure modes:
1. **KPI-to-Claim Alignment Error:** Abductive leaping from abstract process scores (e.g., *Third-Party Vendor Management = 1.0*) to concrete, unverified physical security defects (e.g., *CCTV blind spots, NVR retention <30 days*).
2. **Technical Specificity Hallucination:** The injection of unverified network protocols, storage mechanics, and hardware interfaces (e.g., *BGP, BFD, NetApp CSI, WORM, SFP+*) that have zero lexical presence in the underlying discovery transcripts.
3. **Capability vs. Implementation Conflation:** Translating high capability maturity scores (e.g., *PAM = 4.50*) into specific commercial product mechanisms (e.g., *CyberArk vaulting, automated credential rotation, keystroke logging*) rather than restricting claims to governance maturity.
4. **Tower Context Contamination:** Allowing cross-pollination of raw physical infrastructure entities (e.g., *SimpliVity, ESXi, NetApp*) into non-infrastructure domains such as Tower 8 (Governance, Risk, Compliance & FinOps), causing the generator to re-litigate hardware topologies instead of focusing on financial and governance artifacts.
5. **FAIR Provenance Obfuscation:** Emitting strategic risk cards with mathematically sound ALE figures that lack cryptographic or structural lineage linking the underlying TEF, Vulnerability ($V$), and SLE inputs back to their exact empirical sources.

### 1.2 The Epistemic Paradigm Shift: Zero-Prompt-Reliance
Prompt engineering ("Do not hallucinate", "Only use provided facts") is fundamentally bankrupt as an architectural control. It relies on the probabilistic compliance of an inherently stochastic attention mechanism. 

Phase 27 marks a permanent transition to **Zero-Prompt-Reliance**. We are re-architecting the generation pipeline into a strict **Compiler Frontend and Static Analysis Backplane**:
* **Information-Theoretic Context Starvation (Pre-Generation):** The LLM cannot hallucinate cross-tower hardware contamination if the hardware tokens are stripped from its input context at the AST assembly layer (`TowerContextBuilder`).
* **Semantic Capability Bounding (Pre-Generation):** Survey KPIs are stripped of raw numerical ambiguity and replaced with strictly typed **Epistemic Claim Envelopes** that define the exact ontological boundaries of permissible assertions.
* **Lexical Witness Gating (Post-Generation AST Validation):** The LLM's output is parsed into a strongly typed Abstract Syntax Tree (AST). Every technical proper noun, acronym, protocol, and product mechanism is extracted and cross-examined against a deterministic **Transcript Lexicon Index (TLI)**. Any token lacking an empirical witness in the source audio transcripts triggers an immediate AST Compiler Panic, stripping or rewriting the offending node prior to serialization.

```
[Raw Transcripts] ──> [Lexical Indexer (TLI)] ──────────────────────────────┐
                                                                            ▼
[Survey KPIs] ──> [Semantic Bounder] ──> [TowerContextBuilder] ──> [LLM] ──> [AST Verifier] ──> [Verified Artifact]
                                                ▲                           │
[Tower Ontology] ───────────────────────────────┘                           └──> [Compiler Panic / Redaction]
```

---

## 2. DETAILED PHASED IMPLEMENTATION STRATEGY

### Phase 27.1: KPI Semantic Bounding & Capability-Implementation Decoupling
*Addresses Failure Modes 1 (KPI-to-Claim Alignment) and 3 (Capability vs. Implementation Conflation).*

#### 2.1.1 Architectural Mechanism
Survey responses measure **Process Capability and Governance Maturity** (aligned with CMMI/COBIT frameworks), *never* specific physical implementations or commercial software features, unless accompanied by an explicit transcript citation. 

To prevent the generator from inferring physical implementations from survey scores, we introduce the `KpiEpistemicEnvelope`. Prior to prompt serialization, the `SurveyNormalizationEngine` will transform every raw KPI metric into a bounded epistemic structure containing an explicit `OntologicalScope`, an `AllowedClaimVector`, and a `ForbiddenInferenceClass`.

#### 2.1.2 Capability vs. Implementation Stratification
When a KPI score is evaluated without a directly linked transcript quote (`has_empirical_witness == False`), the compiler enforces **Capability-Only Assertion Mode**:
* **Low Score ($\le 2.0$):** The generator may assert *process ad-hocness, lack of standardized policy, absence of formal governance, or undocumented operational procedures* strictly within the semantic boundary of the KPI definition. It is structurally blocked from asserting specific technical misconfigurations, missing hardware components, or failing software mechanisms.
* **High Score ($\ge 4.0$):** The generator may assert *defined governance, repeatable operational processes, executive oversight, and standardized lifecycle management*. It is structurally blocked from naming commercial vendors, specific cryptographic protocols, or automated technical enforcement mechanisms (e.g., "automatic rotation", "session recording").

#### 2.1.3 Ontological Alignment Matrix
Every KPI in the global catalog is mapped to a deterministic `SemanticDomainSet`. During the AST Verification pass, all nouns and noun phrases within a generated claim citing `KPI_ID` are projected into a high-dimensional embedding space (using a local, frozen, deterministic model such as `bge-large-en-v1.5` running at `temperature=0.0` with fixed seed) and evaluated against the KPI's definition vector. If the Cosine Similarity falls below $\tau_{align} = 0.68$, or if the claim triggers a token belonging to a disjoint domain taxonomy (e.g., Physical Security tokens appearing inside a Vendor Management KPI claim), the AST node is rejected.

---

### Phase 27.2: Transcript Evidence Hard-Lock (Lexical Witness Gate)
*Addresses Failure Mode 2 (Technical Specificity Hallucination).*

#### 2.2.1 Architectural Mechanism
No technical protocol, hardware interface, storage mechanism, or vendor feature may exist in the final delivery artifact unless it is backed by an **Empirical Lexical Witness** in the verified ingestion corpus (audio transcripts or uploaded configuration files).

We implement a two-stage compiler gate:
1. **Stage 1: The Transcript Lexicon Indexer (TLI):** During ingestion, all transcripts are tokenized, lemmatized, and scanned using an enterprise technical Named Entity Recognition (NER) pipeline and deterministic Regular Expression finite state machines. This builds an immutable `EmpiricalLexiconSet` per engagement.
2. **Stage 2: The Post-Generation AST Technical Gate (`TechnicalSpecificityVerifier`):** Before any generated text is accepted into the final document model, it is scanned for **High-Specificity Technical Tokens (HSTTs)**.

#### 2.2.2 High-Specificity Technical Token (HSTT) Detection
An HSTT is defined deterministically without hardcoding domain lists via three lexical heuristics:
1. **Acronym/Initialism Pattern:** Any token matching `\b[A-Z]{2,6}(?:-[A-Z0-9]+)?\b` (e.g., `BGP`, `BFD`, `WORM`, `CSI`, `NVR`, `CCTV`, `SFP+`, `PAM`, `VLAN`), excluding a minimal, universal standard English stop-list (e.g., `IT`, `CEO`, `SLA`, `KPI`, `ROI`, `USD`).
2. **CamelCase / Mixed-Case Vendor Signatures:** Any token matching `\b[A-Za-z]+[A-Z][A-Za-z0-9]*\b` (e.g., `NetApp`, `SimpliVity`, `CyberArk`, `ESXi`, `vSphere`, `ActiveDirectory`).
3. **Compound Technical Mechanisms:** Noun phrases containing numerical specifications or protocol quantifiers (e.g., `<30 days`, `10GbE`, `Layer-3`, ` deduplication`, `keystroke logging`, `password rotation`). These are identified via dependency parsing (`spacy` `en_core_web_trf`) looking for `compound`, `amod`, and `nummod` arcs attached to technical head nouns.

#### 2.2.3 The Zero-Tolerance Verification Rule
For every HSTT extracted from a generated AST node $N$:
$$\forall t \in \text{HSTT}(N), \quad \text{Verify}(t) = \mathbb{I}\left( \text{Lemma}(t) \in \mathcal{L}_{\text{transcript}} \lor \text{Lemma}(t) \in \mathcal{L}_{\text{kpi\_def}}(N.\text{source\_kpi}) \right)$$
If $\text{Verify}(t) == 0$, the AST Verifier throws an `UnverifiedTechnicalSpecificityError`. 

Instead of asking the LLM to "try again" via a conversational prompt, the compiler executes a **Deterministic Surgical Redaction & Generalization Pass**, replacing the offending clause with its bounded capability equivalent derived from the `KpiEpistemicEnvelope`, or pruning the sentence entirely if it carries no residual epistemic value.

---

### Phase 27.3: Tower Context Filtration (Strict Payload Isolation)
*Addresses Failure Mode 4 (Tower Context Contamination).*

#### 2.3.1 Architectural Mechanism
The root cause of Tower 8 (Governance, FinOps, IT Strategy) hallucinating or re-interpreting hardware vulnerabilities from Tower 1 (Compute/Storage) or Tower 3 (Network) is **Context Over-Provisioning**. Passing a unified global fact sheet or shared entity graph to every tower generator violates the Principle of Least Privilege.

We re-architect the `TowerContextBuilder` to enforce **Information-Theoretic Payload Isolation**. A Tower Generator is physically prevented from observing entities, transcripts, or KPIs that fall outside its strict ontological jurisdiction.

#### 2.3.2 Entity Classification & Projection Algebra
Every extracted fact or transcript chunk in the ingestion store is tagged with an `EntityOntologicalClass` enum:
* `PHYSICAL_INFRASTRUCTURE` (Compute nodes, hypervisors, storage arrays, cabling, facilities).
* `NETWORK_TOPOLOGY` (Routing protocols, switches, firewalls, link state mechanisms).
* `APPLICATION_RUNTIME` (Databases, middleware, APIs, code repositories).
* `SECURITY_OPERATIONS` (IAM, PAM, SIEM, endpoint protection).
* `GOVERNANCE_AND_FINOPS` (Contracts, licensing renewals, CapEx/OpEx ledgers, organizational structure, vendor SLAs, portfolio roadmaps).

When building the context payload for Tower $T_k$, the `TowerContextBuilder` applies a strict projection operator $\Pi_{T_k}$:
$$\text{Payload}(T_k) = \{ e \in \text{GlobalFactStore} \mid e.\text{ontology\_class} \in \text{AllowedClasses}(T_k) \}$$

#### 2.3.3 The Governance/FinOps Projection Transformation
For Tower 8 (`GOVERNANCE_AND_FINOPS`), $\text{AllowedClasses}(T_8) = \{\text{GOVERNANCE\_AND\_FINOPS}\}$. 
If a raw transcript statement contains a hybrid fact—such as *"Our NetApp and SimpliVity clusters are out of warranty and costing $400k in extended support"*—passing the raw string to Tower 8 will contaminate its context with `NetApp` and `SimpliVity`, causing the LLM to generate storage architecture recommendations inside the FinOps chapter.

To solve this deterministically, the `TowerContextBuilder` executes an **Entity Abstraction Transform ($\mathcal{T}_{\text{abstract}}$)** on hybrid facts before injecting them into Tower 8:
* All tokens tagged as `PHYSICAL_INFRASTRUCTURE` or `NETWORK_TOPOLOGY` proper nouns are masked and replaced with their abstract asset class descriptors based on the ingestion NER tagger.
* *Raw Fact:* `"Our NetApp and SimpliVity clusters are out of warranty and costing $400k in extended support."`
* *Projected T8 Fact:* `"[Enterprise Storage Asset] and [Hyperconverged Compute Asset] instances are out of warranty and costing $400k in extended support."`

Tower 8 receives the exact financial and lifecycle governance signal required for FinOps analysis while remaining 100% blind to the underlying hardware nomenclature.

---

### Phase 27.4: FAIR Provenance Schema & Cryptographic Lineage
*Addresses Failure Mode 5 (FAIR Provenance Obfuscation).*

#### 2.4.1 Architectural Mechanism
Actuarial outputs without verifiable audit trails fail Tier-1 regulatory scrutiny. Every strategic and technical risk card must expose the exact empirical lineage of its three primary FAIR drivers:
1. **Threat Event Frequency (`tef_source`):** Why is this threat occurring at this frequency?
2. **Vulnerability / Susceptibility (`vuln_source`):** What specific control deficit allows the threat event to become a loss event?
3. **Single Loss Expectancy (`sle_source`):** What empirical financial, operational, or volumetric baseline dictates the magnitude of the loss?

#### 2.4.2 Strict Provenance Data Structures
We deprecate free-text risk justifications. The `FairRiskCard` Pydantic schema is upgraded to require strongly typed `ParameterProvenance` objects for `tef`, `vuln`, and `sle`. Every `ParameterProvenance` instance must resolve to an immutable `EvidencePointer` in the engagement database, complete with a SHA-256 content hash of the underlying evidence artifact (transcript utterance ID, survey KPI response ID, or financial baseline table row).

If any of the three provenance pointers is null, fails foreign-key resolution against the `VerifiedEvidenceStore`, or cites an evidence artifact that was rejected by the Phase 27.2 Lexical Witness Gate, the risk card fails schema instantiation and cannot be rendered.

---

## 3. ARCHITECTURAL CONTRACTS & COMPILER SCHEMAS

All code specifications below are production-ready Python 3.11+ utilizing `pydantic>=2.6` and standard library static analysis modules.

### 3.1 Epistemic Envelopes & FAIR Provenance Schemas (`src/argon/epistemic/schemas.py`)

```python
from __future__ import annotations
import hashlib
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator


class EntityOntologicalClass(str, Enum):
    PHYSICAL_INFRASTRUCTURE = "PHYSICAL_INFRASTRUCTURE"
    NETWORK_TOPOLOGY = "NETWORK_TOPOLOGY"
    APPLICATION_RUNTIME = "APPLICATION_RUNTIME"
    SECURITY_OPERATIONS = "SECURITY_OPERATIONS"
    GOVERNANCE_AND_FINOPS = "GOVERNANCE_AND_FINOPS"


class EvidenceOriginType(str, Enum):
    TRANSCRIPT_UTTERANCE = "TRANSCRIPT_UTTERANCE"
    SURVEY_KPI_SCORE = "SURVEY_KPI_SCORE"
    FINANCIAL_BASELINE_TABLE = "FINANCIAL_BASELINE_TABLE"
    ACTUARIAL_INDUSTRY_PRIOR = "ACTUARIAL_INDUSTRY_PRIOR"


class EpistemicAssertionMode(str, Enum):
    CAPABILITY_GOVERNANCE_ONLY = "CAPABILITY_GOVERNANCE_ONLY"
    EMPIRICAL_IMPLEMENTATION_VERIFIED = "EMPIRICAL_IMPLEMENTATION_VERIFIED"


class EvidencePointer(BaseModel):
    """Immutable cryptographic pointer to an empirical source artifact."""
    artifact_id: str = Field(..., min_length=4, description="UUID or canonical key of the source record.")
    origin_type: EvidenceOriginType
    verbatim_excerpt: str = Field(..., min_length=1, description="Exact string from transcript or KPI definition.")
    sha256_witness: str = Field(..., min_length=64, max_length=64)

    @model_validator(mode="after")
    def verify_cryptographic_witness(self) -> EvidencePointer:
        expected_hash = hashlib.sha256(
            f"{self.artifact_id}:{self.origin_type.value}:{self.verbatim_excerpt}".encode("utf-8")
        ).hexdigest()
        if self.sha256_witness != expected_hash:
            raise ValueError(
                f"Epistemic Integrity Violation: SHA-256 witness mismatch for artifact '{self.artifact_id}'."
            )
        return self


class KpiEpistemicEnvelope(BaseModel):
    """Bounds the generative claim scope of a specific Survey KPI."""
    kpi_id: str
    kpi_domain: EntityOntologicalClass
    canonical_name: str
    canonical_definition: str
    raw_score: float = Field(..., ge=0.0, le=5.0)
    assertion_mode: EpistemicAssertionMode
    corroborating_transcript_pointers: List[EvidencePointer] = Field(default_factory=list)
    allowed_capability_descriptors: List[str]
    forbidden_implementation_inferences: List[str]

    @model_validator(mode="after")
    def enforce_assertion_mode_invariants(self) -> KpiEpistemicEnvelope:
        has_transcript_evidence = any(
            p.origin_type == EvidenceOriginType.TRANSCRIPT_UTTERANCE
            for p in self.corroborating_transcript_pointers
        )
        if not has_transcript_evidence and self.assertion_mode != EpistemicAssertionMode.CAPABILITY_GOVERNANCE_ONLY:
            raise ValueError(
                f"KPI '{self.kpi_id}' lacks transcript witnesses; must operate in CAPABILITY_GOVERNANCE_ONLY mode."
            )
        return self


class FairParameterProvenance(BaseModel):
    """Enforces explicit traceability for individual FAIR model parameters."""
    parameter_name: str = Field(..., pattern=r"^(TEF|VULN|SLE)$")
    quantitative_value_summary: str
    primary_evidence: EvidencePointer
    corroborating_evidence: List[EvidencePointer] = Field(default_factory=list)
    derivation_rationale: str = Field(
        ...,
        description="Deterministic explanation of how the primary evidence maps to the quantitative parameter.",
    )


class FairProvenanceBlock(BaseModel):
    """Mandatory provenance container attached to every strategic and technical Risk Card."""
    tef_source: FairParameterProvenance
    vuln_source: FairParameterProvenance
    sle_source: FairParameterProvenance

    @model_validator(mode="after")
    def validate_parameter_alignment(self) -> FairProvenanceBlock:
        if self.tef_source.parameter_name != "TEF":
            raise ValueError("tef_source must have parameter_name == 'TEF'")
        if self.vuln_source.parameter_name != "VULN":
            raise ValueError("vuln_source must have parameter_name == 'VULN'")
        if self.sle_source.parameter_name != "SLE":
            raise ValueError("sle_source must have parameter_name == 'SLE'")
        
        # Vulnerability must NEVER be derived purely from an industry prior; it requires client-specific evidence.
        if self.vuln_source.primary_evidence.origin_type == EvidenceOriginType.ACTUARIAL_INDUSTRY_PRIOR:
            raise ValueError(
                "Epistemic Gate Violation: Vulnerability (vuln_source) cannot rely on ACTUARIAL_INDUSTRY_PRIOR. "
                "It must reference a specific SURVEY_KPI_SCORE or TRANSCRIPT_UTTERANCE."
            )
        return self
```

---

### 3.2 Tower Context Builder & Payload Isolation (`src/argon/compiler/context_builder.py`)

```python
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple
from src.argon.epistemic.schemas import (
    EntityOntologicalClass,
    EvidencePointer,
    KpiEpistemicEnvelope,
)


@dataclass(frozen=True)
class TaggedTranscriptNode:
    utterance_id: str
    raw_text: str
    ontological_classes: FrozenSet[EntityOntologicalClass]
    extracted_entities: Dict[str, EntityOntologicalClass]  # e.g., {"NetApp": PHYSICAL_INFRASTRUCTURE}
    evidence_pointer: EvidencePointer


class TowerContextIsolationError(Exception):
    """Raised when an unauthorized ontological entity breaches a tower payload."""


class TowerContextBuilder:
    """
    Deterministic context compiler that enforces Information-Theoretic Payload Isolation
    across enterprise towers. Zero prompt reliance.
    """

    TOWER_ONTOLOGY_MATRIX: Dict[str, Set[EntityOntologicalClass]] = {
        "T1_COMPUTE_STORAGE": {EntityOntologicalClass.PHYSICAL_INFRASTRUCTURE},
        "T2_VIRTUALIZATION_CLOUD": {
            EntityOntologicalClass.PHYSICAL_INFRASTRUCTURE,
            EntityOntologicalClass.APPLICATION_RUNTIME,
        },
        "T3_NETWORK_CONNECTIVITY": {EntityOntologicalClass.NETWORK_TOPOLOGY},
        "T4_SECURITY_COMPLIANCE": {EntityOntologicalClass.SECURITY_OPERATIONS},
        "T8_GOVERNANCE_FINOPS": {EntityOntologicalClass.GOVERNANCE_AND_FINOPS},
    }

    ABSTRACT_CLASS_LABELS: Dict[EntityOntologicalClass, str] = {
        EntityOntologicalClass.PHYSICAL_INFRASTRUCTURE: "[Physical Infrastructure Asset]",
        EntityOntologicalClass.NETWORK_TOPOLOGY: "[Network Topology Component]",
        EntityOntologicalClass.APPLICATION_RUNTIME: "[Application Runtime Platform]",
        EntityOntologicalClass.SECURITY_OPERATIONS: "[Security Control Mechanism]",
    }

    def __init__(
        self,
        transcript_nodes: List[TaggedTranscriptNode],
        kpi_envelopes: List[KpiEpistemicEnvelope],
    ) -> None:
        self._transcript_nodes = transcript_nodes
        self._kpi_envelopes = kpi_envelopes

    def build_isolated_payload(
        self, tower_id: str
    ) -> Tuple[List[str], List[KpiEpistemicEnvelope], Set[str]]:
        """
        Returns:
            1. Sanitized transcript statements permissible for this tower.
            2. Filtered KPI envelopes belonging strictly to this tower's ontology.
            3. Tower-specific allowed lexical witness set (for downstream AST verification).
        """
        if tower_id not in self.TOWER_ONTOLOGY_MATRIX:
            raise ValueError(f"Unknown tower identifier: {tower_id}")

        allowed_classes = self.TOWER_ONTOLOGY_MATRIX[tower_id]
        sanitized_statements: List[str] = []
        allowed_lexicon: Set[str] = set()

        # 1. Filter and Transform Transcript Nodes
        for node in self._transcript_nodes:
            if not (node.ontological_classes & allowed_classes):
                continue  # Complete exclusion if node has no relevance to this tower's ontology

            processed_text = node.raw_text
            for entity_token, entity_class in node.extracted_entities.items():
                if entity_class not in allowed_classes:
                    # Apply Entity Abstraction Transform for cross-domain hybrid facts (e.g., T8 FinOps)
                    replacement = self.ABSTRACT_CLASS_LABELS.get(
                        entity_class, "[Redacted Technical Entity]"
                    )
                    pattern = re.compile(r"\b" + re.escape(entity_token) + r"\b", re.IGNORECASE)
                    processed_text = pattern.sub(replacement, processed_text)
                else:
                    allowed_lexicon.add(entity_token.lower())

            sanitized_statements.append(processed_text)
            # Add non-entity tokens from the sanitized text to the allowed lexicon
            for word in re.findall(r"\b[a-zA-Z0-9_\-\+]+\b", processed_text.lower()):
                allowed_lexicon.add(word)

        # 2. Filter KPI Envelopes strictly by Ontological Domain
        filtered_kpis = [
            kpi for kpi in self._kpi_envelopes if kpi.kpi_domain in allowed_classes
        ]
        for kpi in filtered_kpis:
            for word in re.findall(r"\b[a-zA-Z0-9_\-\+]+\b", kpi.canonical_definition.lower()):
                allowed_lexicon.add(word)

        self._verify_payload_isolation(tower_id, sanitized_statements, allowed_classes)
        return sanitized_statements, filtered_kpis, allowed_lexicon

    def _verify_payload_isolation(
        self,
        tower_id: str,
        statements: List[str],
        allowed_classes: Set[EntityOntologicalClass],
    ) -> None:
        """Self-check invariant: ensures zero forbidden entities leaked through regex boundaries."""
        forbidden_entities: Set[str] = set()
        for node in self._transcript_nodes:
            for entity_token, entity_class in node.extracted_entities.items():
                if entity_class not in allowed_classes:
                    forbidden_entities.add(entity_token.lower())

        for stmt in statements:
            stmt_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-\+]+\b", stmt.lower()))
            leaked = stmt_tokens & forbidden_entities
            if leaked:
                raise TowerContextIsolationError(
                    f"CRITICAL COMPILER PANIC: Tower '{tower_id}' payload contaminated with "
                    f"unauthorized ontological entities: {leaked}"
                )
```

---

### 3.3 Post-Generation AST Epistemic Verifier (`src/argon/compiler/ast_verifier.py`)

```python
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set
from src.argon.epistemic.schemas import (
    EpistemicAssertionMode,
    FairProvenanceBlock,
    KpiEpistemicEnvelope,
)


class EpistemicCompilationError(Exception):
    """Base exception for AST Epistemic Verification failures."""


class UnverifiedTechnicalSpecificityError(EpistemicCompilationError):
    """Raised when generated text contains HSTTs absent from the empirical lexicon."""


class KpiSemanticBoundaryViolationError(EpistemicCompilationError):
    """Raised when a claim citing a KPI drifts outside the KPI's semantic vector boundary."""


class CapabilityImplementationConflationError(EpistemicCompilationError):
    """Raised when a CAPABILITY_GOVERNANCE_ONLY KPI is used to claim a specific technical implementation."""


@dataclass
class GeneratedClaimNode:
    """AST Node representing a single atomic assertion in a generated report."""
    node_id: str
    tower_id: str
    claim_text: str
    cited_kpi_id: Optional[str]
    cited_utterance_ids: List[str]
    fair_provenance: Optional[FairProvenanceBlock] = None


class AstEpistemicVerifier:
    """
    Deterministic Post-Generation AST Compiler Gate.
    Validates every generated claim node against:
    1. The Transcript Lexicon Index (HSTT Hard-Lock).
    2. KPI Semantic Bounding (Cosine Similarity & Disjoint Taxonomy Check).
    3. Capability vs. Implementation Stratification Rules.
    """

    # Universal non-technical enterprise acronyms exempt from HSTT lexical locking
    UNIVERSAL_ACRONYM_ALLOWLIST: Set[str] = {
        "IT", "CEO", "CFO", "CIO", "CISO", "SLA", "KPI", "ROI", "TCO",
        "CAPEX", "OPEX", "USD", "EUR", "FAIR", "TEF", "SLE", "ALE", "GRC"
    }

    # Regex patterns for High-Specificity Technical Tokens (HSTTs)
    ACRONYM_PATTERN = re.compile(r"\b[A-Z]{2,6}(?:-[A-Z0-9]+)?\+?s?\b")
    CAMELCASE_VENDOR_PATTERN = re.compile(r"\b[A-Za-z]+[A-Z][A-Za-z0-9]*\b")
    QUANTIFIED_SPEC_PATTERN = re.compile(
        r"(?:<\s*\d+\s*(?:days|hours|ms|gb|tb)|>\s*\d+\s*(?:days|hours|ms|gb|tb)|\b\d+\s*(?:gbps|mbps|gbe|tb|gb|mhz|ghz)\b)",
        re.IGNORECASE,
    )

    # Structural indicators of concrete implementation mechanisms (forbidden in CAPABILITY_GOVERNANCE_ONLY mode)
    IMPLEMENTATION_MECHANISM_PATTERNS: List[re.Pattern] = [
        re.compile(r"\b(?:automatic|automated)\s+(?:password|credential|key)\s+rotation\b", re.I),
        re.compile(r"\bkeystroke\s+(?:logging|recording|monitoring)\b", re.I),
        re.compile(r"\bsession\s+(?:recording|vaulting|proxying)\b", re.I),
        re.compile(r"\bblind\s+spots?\b", re.I),
        re.compile(r"\bretention\s+(?:period|window)?\s*(?:of|<|>|less\s+than)\s*\d+\b", re.I),
        re.compile(r"\bdeduplication\b", re.I),
        re.compile(r"\bworm\s+(?:storage|locking|immutability)\b", re.I),
    ]

    def __init__(
        self,
        tower_allowed_lexicon: Set[str],
        kpi_registry: Dict[str, KpiEpistemicEnvelope],
        semantic_similarity_fn: Callable[[str, str], float],
        similarity_threshold: float = 0.68,
    ) -> None:
        self._lexicon = {w.lower() for w in tower_allowed_lexicon}
        self._kpi_registry = kpi_registry
        self._similarity_fn = semantic_similarity_fn
        self._threshold = similarity_threshold

    def verify_ast_node(self, node: GeneratedClaimNode) -> GeneratedClaimNode:
        """
        Executes all deterministic verification passes on an AST Claim Node.
        Raises an EpistemicCompilationError if any invariant is breached.
        """
        self._enforce_hstt_lexical_lock(node)
        if node.cited_kpi_id:
            self._enforce_kpi_semantic_bounds(node)
            self._enforce_capability_implementation_separation(node)
        return node

    def _extract_hstts(self, text: str) -> Set[str]:
        hstts: Set[str] = set()
        for match in self.ACRONYM_PATTERN.findall(text):
            clean = match.rstrip("s")
            if clean not in self.UNIVERSAL_ACRONYM_ALLOWLIST:
                hstts.add(match)

        for match in self.CAMELCASE_VENDOR_PATTERN.findall(text):
            hstts.add(match)

        for match in self.QUANTIFIED_SPEC_PATTERN.findall(text):
            hstts.add(match.strip())

        return hstts

    def _enforce_hstt_lexical_lock(self, node: GeneratedClaimNode) -> None:
        """Phase 27.2: Forbids technical acronyms, vendors, or specs absent from the tower lexicon."""
        extracted_hstts = self._extract_hstts(node.claim_text)
        unverified_tokens: List[str] = []

        for token in extracted_hstts:
            normalized = token.lower().rstrip("s")
            # Check if exact token or sub-tokens exist in verified tower lexicon
            sub_tokens = re.findall(r"[a-z0-9\+]+", normalized)
            if normalized not in self._lexicon and not all(st in self._lexicon for st in sub_tokens):
                unverified_tokens.append(token)

        if unverified_tokens:
            raise UnverifiedTechnicalSpecificityError(
                f"AST Node '{node.node_id}' in Tower '{node.tower_id}' injected unverified "
                f"High-Specificity Technical Tokens (HSTTs) absent from transcript evidence: {unverified_tokens}"
            )

    def _enforce_kpi_semantic_bounds(self, node: GeneratedClaimNode) -> None:
        """Phase 27.1: Ensures claim text remains within the semantic neighborhood of the cited KPI."""
        kpi_id = node.cited_kpi_id
        if not kpi_id or kpi_id not in self._kpi_registry:
            raise KpiSemanticBoundaryViolationError(
                f"AST Node '{node.node_id}' cites unknown or unauthorized KPI '{kpi_id}'."
            )

        envelope = self._kpi_registry[kpi_id]
        reference_corpus = f"{envelope.canonical_name}: {envelope.canonical_definition}"
        similarity = self._similarity_fn(node.claim_text, reference_corpus)

        if similarity < self._threshold:
            raise KpiSemanticBoundaryViolationError(
                f"AST Node '{node.node_id}' failed KPI Semantic Bounding. "
                f"Claim similarity ({similarity:.3f}) to KPI '{kpi_id}' ({envelope.canonical_name}) "
                f"is below mandatory threshold ({self._threshold})."
            )

        # Check explicit forbidden inferences configured on the KPI envelope
        claim_lower = node.claim_text.lower()
        for forbidden_term in envelope.forbidden_implementation_inferences:
            if forbidden_term.lower() in claim_lower:
                raise KpiSemanticBoundaryViolationError(
                    f"AST Node '{node.node_id}' triggered forbidden inference term '{forbidden_term}' "
                    f"while citing KPI '{kpi_id}'."
                )

    def _enforce_capability_implementation_separation(self, node: GeneratedClaimNode) -> None:
        """Phase 27.1 / Mode 3: Prevents translating survey scores into concrete mechanisms without transcripts."""
        envelope = self._kpi_registry[node.cited_kpi_id]  # type: ignore[index]

        # If the node cites no transcript utterances, or the KPI is locked to CAPABILITY_GOVERNANCE_ONLY
        if (
            envelope.assertion_mode == EpistemicAssertionMode.CAPABILITY_GOVERNANCE_ONLY
            or len(node.cited_utterance_ids) == 0
        ):
            for pattern in self.IMPLEMENTATION_MECHANISM_PATTERNS:
                match = pattern.search(node.claim_text)
                if match:
                    raise CapabilityImplementationConflationError(
                        f"AST Node '{node.node_id}' conflated capability score (KPI '{envelope.kpi_id}' = {envelope.raw_score}) "
                        f"with unverified implementation mechanism: '{match.group(0)}'. "
                        f"Empirical transcript utterance citation is mandatory for implementation claims."
                    )
```

---

## 4. VERIFICATION ORACLES & DETERMINISTIC INVARIANT SUITE

To guarantee zero regression across all global deployments, the CI/CD pipeline (`pytest` gate) must execute the following five deterministic verification oracles before any code or delivery artifact is promoted.

### 4.1 Oracle 1: KPI-to-Claim Semantic Drift Oracle (Failure Mode 1)
* **Test Vector:** Inject a KPI Envelope for `KPI-VM-01` (*Third-Party Vendor Management*, `raw_score=1.0`, `canonical_definition="Governance lifecycle for evaluating, onboarding, and auditing external service providers and supplier contracts."`).
* **Adversarial AST Input:** `GeneratedClaimNode` citing `KPI-VM-01` with `claim_text="Physical facility monitoring exhibits CCTV blind spots and NVR video retention under 30 days."`
* **Expected Deterministic Outcome:**
  1. `AstEpistemicVerifier._enforce_hstt_lexical_lock` raises `UnverifiedTechnicalSpecificityError` on `["CCTV", "NVR", "<30 days"]`.
  2. Even if acronyms are spelled out ("closed-circuit television"), `AstEpistemicVerifier._enforce_kpi_semantic_bounds` computes a Cosine Similarity $< 0.35$ against the Vendor Management definition (threshold $\ge 0.68$) and raises `KpiSemanticBoundaryViolationError`.

### 4.2 Oracle 2: Zero-Witness Technical Specificity Oracle (Failure Mode 2)
* **Test Vector:** Initialize `TowerContextBuilder` for `T3_NETWORK_CONNECTIVITY` with a transcript containing only: *"Our core data center switches experience occasional failover delays during peak load."*
* **Adversarial AST Input:** `GeneratedClaimNode` with `claim_text="Enabling BFD over BGP routing with SFP+ transceivers and NetApp CSI WORM deduplication will resolve the failover delay."`
* **Expected Deterministic Outcome:**
  1. `_extract_hstts` isolates `{"BFD", "BGP", "SFP+", "NetApp", "CSI", "WORM"}`.
  2. Cross-reference against `tower_allowed_lexicon` yields 0 hits.
  3. Compiler halts with `UnverifiedTechnicalSpecificityError`.

### 4.3 Oracle 3: Capability vs. Implementation Conflation Oracle (Failure Mode 3)
* **Test Vector:** Inject `KPI-SEC-04` (*Privileged Access Management Governance*, `raw_score=4.50`, `corroborating_transcript_pointers=[]`). By schema invariant, `assertion_mode` automatically locks to `EpistemicAssertionMode.CAPABILITY_GOVERNANCE_ONLY`.
* **Adversarial AST Input:** `GeneratedClaimNode` citing `KPI-SEC-04` (`cited_utterance_ids=[]`) with `claim_text="The organization maintains mature PAM controls featuring a centralized CyberArk vault, automatic password rotation, and keystroke logging."`
* **Expected Deterministic Outcome:**
  1. `CyberArk` triggers `UnverifiedTechnicalSpecificityError`.
  2. `"automatic password rotation"` and `"keystroke logging"` match `IMPLEMENTATION_MECHANISM_PATTERNS` while `assertion_mode == CAPABILITY_GOVERNANCE_ONLY`, raising `CapabilityImplementationConflationError`.
  3. **Valid Passing Control Vector:** `"The organization demonstrates mature Privileged Access Management governance with well-defined administrative oversight and standardized lifecycle policies."` -> **PASSES**.

### 4.4 Oracle 4: Tower 8 Context Contamination Oracle (Failure Mode 4)
* **Test Vector:** Ingest a hybrid `TaggedTranscriptNode`:
  * `raw_text`: `"We need to renew the Enterprise Agreement for our ESXi hosts and SimpliVity clusters before Q4 to avoid a 20% penalty on our NetApp storage refresh."`
  * `ontological_classes`: `{PHYSICAL_INFRASTRUCTURE, GOVERNANCE_AND_FINOPS}`
  * `extracted_entities`: `{"ESXi": PHYSICAL_INFRASTRUCTURE, "SimpliVity": PHYSICAL_INFRASTRUCTURE, "NetApp": PHYSICAL_INFRASTRUCTURE}`
* **Execution:** Invoke `TowerContextBuilder.build_isolated_payload("T8_GOVERNANCE_FINOPS")`.
* **Expected Deterministic Outcome:**
  1. The statement returned to Tower 8 is strictly transformed to: `"We need to renew the Enterprise Agreement for our [Physical Infrastructure Asset] hosts and [Physical Infrastructure Asset] clusters before Q4 to avoid a 20% penalty on our [Physical Infrastructure Asset] storage refresh."`
  2. The `tower_allowed_lexicon` for Tower 8 contains **zero** occurrences of `esxi`, `simplivity`, or `netapp`.
  3. Any subsequent attempt by the Tower 8 LLM generator to emit those hardware strings triggers an immediate `UnverifiedTechnicalSpecificityError` in the AST Verifier.

### 4.5 Oracle 5: FAIR Provenance Cryptographic Lineage Oracle (Failure Mode 5)
* **Test Vector A (Missing Provenance):** Instantiate a strategic risk card where `sle_source` is omitted or `None`. -> **Pydantic `ValidationError`**.
* **Test Vector B (Tampered Excerpt):** Instantiate `EvidencePointer` where `verbatim_excerpt` is modified by a single character compared to the ingestion store's `sha256_witness`. -> **`ValueError: Epistemic Integrity Violation: SHA-256 witness mismatch`**.
* **Test Vector C (Unverified Vulnerability Prior):** Instantiate `FairProvenanceBlock` where `vuln_source.primary_evidence.origin_type == EvidenceOriginType.ACTUARIAL_INDUSTRY_PRIOR`. -> **`ValueError: Epistemic Gate Violation: Vulnerability (vuln_source) cannot rely on ACTUARIAL_INDUSTRY_PRIOR`**.

---

## 5. EXECUTION ROADMAP & COMPILER INTEGRATION PIPELINE

| Step | Component | Target File | Action |
| :--- | :--- | :--- | :--- |
| **1** | Epistemic Schemas | `src/argon/epistemic/schemas.py` | Deploy `EvidencePointer`, `KpiEpistemicEnvelope`, and `FairProvenanceBlock` models. |
| **2** | Ingestion Tagger | `src/argon/ingestion/lexicon_indexer.py` | Build `TaggedTranscriptNode` pipeline with SHA-256 witness generation and ontological entity tagging. |
| **3** | Context Isolation | `src/argon/compiler/context_builder.py` | Replace legacy context builder with `TowerContextBuilder` implementing $\Pi_{T_k}$ and $\mathcal{T}_{\text{abstract}}$. |
| **4** | AST Gate | `src/argon/compiler/ast_verifier.py` | Wire `AstEpistemicVerifier` into the post-generation deserialization hook of all Tower Generators. |
| **5** | CI/CD Gate | `tests/epistemic/test_phase27_oracles.py` | Implement the 5 Verification Oracles as mandatory blocking unit tests. |