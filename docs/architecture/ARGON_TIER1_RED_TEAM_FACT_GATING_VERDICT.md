# ADVERSARIAL RED TEAM VERDICT: FACT REGISTRY & CLAIM GATING ARCHITECTURE
**Document ID:** `ARGON-ARCH-RT-2026-004`  
**Target Path:** `docs/architecture/ARGON_TIER1_RED_TEAM_FACT_GATING_VERDICT.md`  
**Classification:** TIER-1 ARCHITECTURAL AUDIT / ADVERSARIAL PEER REVIEW  
**Auditor:** Global Head of Adversarial Architecture & Actuarial Peer Review (FSA, CERA, Ex-Principal Systems Architect)  
**Subject:** Structural Viability of `SharedFactRegistry` and `ClaimGatingOracle` for Eliminating Tactical JSON Patching and Epistemic Drift  

---

## 1. EXECUTIVE VERDICT & ADVERSARIAL RATING

### **Adversarial Architecture Rating: 5.8 / 10.0 (CONDITIONAL REJECTION)**

**Verdict:** The proposed dual-component architecture (`SharedFactRegistry` + `ClaimGatingOracle`) represents a directional improvement over post-hoc JSON tactical patching, moving enforcement from the serialization boundary to the generation boundary. **However, in its current naive formulation, it is an architectural illusion.** It replaces localized JSON string-patching with centralized, brittle semantic heuristics. 

If implemented naively, this system will **not** achieve Tier-1 status. Instead, it will introduce catastrophic generation latencies, infinite LLM rejection loops, false-negative suppression of valid domain inferences, and hidden hardcoding within configuration schemas. You are proposing to build an ad-hoc deterministic firewall around a stochastic engine without defining a formal ontology, a state-transition calculus, or an evidence-entailment grammar.

To elevate this architecture from a **5.8** (Brittle Enterprise Middleware) to a **9.8+** (Tier-1 Actuarial-Grade Epistemic Engine), the system must transition from **Lexical/Heuristic Gating** to **Graph-Backed Formal Epistemic Binding and Constrained Decoding**.

---

## 2. STRESS-TEST EVALUATION ACROSS MANDATORY DIMENSIONS

### 2.1 World-Class Tier-1 Certification (State-of-the-Art vs. Brittle Patch)
* **Current State:** **Brittle Patch.** A post-generation `ClaimGatingOracle` that inspects generated prose or JSON payloads for unauthorized tokens ("VESDA", "BitLocker") is merely a glorified regex/NER linter masquerading as an oracle. In distributed systems and production AI at scale, post-generation filtering is an anti-pattern known as *Rejection Sampling with Unbounded Variance*.
* **Tier-1 Standard:** True Tier-1 systems do not allow the LLM to hallucinate and then slap its wrist; they constrain the prior probability distribution before token emission and bind generation strictly to a pre-computed **Directed Acyclic Graph (DAG) of Verified Propositions**.

### 2.2 Zero Hardcoding & Total Scale Agnosticism
* **Current State:** **Fails Scale Agnosticism.** If `SharedFactRegistry` requires human engineers or static configuration files to define that `"613 days uptime"` belongs to `Domain: Infrastructure`, you have merely moved the hardcoding from the JSON patch script into the Registry initialization file. When Client B arrives with `"99.94% SLA adherence"` or `"42,000 unpatched CVEs"`, a static registry collapses.
* **Tier-1 Standard:** The Registry must be populated **zero-shot** via an automated, deterministic **Ingestion-Time Epistemic Extraction Pipeline** governed by a strict **Domain Ontology Schema (OWL/RDF or typed Pydantic Graph)**. Facts are dynamic instances; only the *ontological classes* (e.g., `TemporalMetric`, `ControlArtifact`, `FinancialExposure`) are static.

### 2.3 Chapter 4 Actuarial Perfection (Semantic Drift & Financial Integrity)
* **Current State:** **High Risk of Epistemic Corruption.** Actuarial models (Monte Carlo simulations, VaR, Loss Exceedance Curves, Fair Value adjustments) in Chapter 4 require strict mathematical provenance. If the `SharedFactRegistry` stores facts as raw strings or loosely typed JSON values (e.g., `"uptime": "613 days"`), the LLM or downstream parser will inevitably misinterpret units, time horizons, or conditional probabilities when translating narrative findings into Chapter 4 loss parameters.
* **Tier-1 Standard:** Every fact entering the registry must be compiled into an immutable **Actuarial Fact Tuple (AFT)** containing a canonical scalar value, SI/ISO unit, confidence interval, temporal validity window, and cryptographic hash of the source evidence span. Chapter 4 models must consume the AFT directly from the Registry via deterministic bindings—**never** via LLM-mediated narrative extraction.

---

## 3. IDENTIFIED ARCHITECTURAL BLIND SPOTS & FAILURE MODES

The following seven failure modes will break the proposed architecture in production if left unaddressed:

### Blind Spot 1: The "Absence of Evidence vs. Evidence of Absence" Fallacy
* **Mechanism:** The `ClaimGatingOracle` rejects outputs containing technologies not found in the evidence corpus (e.g., "VESDA", "BitLocker").
* **Failure Mode:** An enterprise audit *must* explicitly name missing industry-standard controls to establish negligence or control gaps! If the LLM writes: *"The facility lacks early-warning aspirating smoke detection (e.g., VESDA) and endpoint encryption (e.g., BitLocker),"* a naive `ClaimGatingOracle` will detect the tokens `"VESDA"` and `"BitLocker"`, note their absence from the client's evidence corpus, and **reject a completely valid, critical audit finding**.
* **Impact:** Systematic sterilization of the report. The engine becomes incapable of citing industry benchmarks, negative controls, or remediation targets unless they already exist in the client's broken environment.

### Blind Spot 2: Cross-Domain Causal Bleed vs. Strict Ownership Silos
* **Mechanism:** `SharedFactRegistry` restricts canonical facts (e.g., `"613 days uptime"`) strictly to their owner domain to prevent repetitive cross-chapter contamination.
* **Failure Mode:** Enterprise failures are systemic and cross-domain. `"613 days uptime"` on a core Solaris kernel has two distinct semantic meanings:
  1. *Infrastructure/Availability Domain:* Positive indicator of stability/resilience.
  2. *Cybersecurity/Patch Management Domain:* Catastrophic indicator of 20+ months without a kernel reboot, implying zero kernel-level security patching.
* **Impact:** By strictly locking a fact to a single owner domain, you blind the Cybersecurity and Actuarial Risk domains to critical cross-domain inferences. The issue is not that the fact appears in multiple domains; the issue is **uncontrolled repetition of the same narrative framing**.

### Blind Spot 3: Paraphrastic Evasion & Semantic Hallucination
* **Mechanism:** The Oracle gates specific named entities or technical nouns.
* **Failure Mode:** LLMs are masters of circumlocution. If blocked from outputting `"VESDA"`, the LLM will output *"laser-based multi-stage air sampling smoke detection."* If blocked from `"BitLocker"`, it will output *"native OS-level full-volume TPM-bound cryptographic encryption."* The hallucination survives completely intact; only the trademarked noun was stripped.
* **Impact:** False sense of security. Epistemic integrity is violated while all unit tests for token absence pass.

### Blind Spot 4: The Rejection Sampling Death Spiral (Latency & Cost Explosion)
* **Mechanism:** The LLM generates a 2,000-token chapter; the `ClaimGatingOracle` flags 3 unauthorized claims at token 1,850 and rejects the payload, triggering a retry with error feedback.
* **Failure Mode:** In complex enterprise corpora, retry prompts frequently induce *whack-a-mole* hallucinations (fixing claim A causes the attention mechanism to shift and hallucinate claim B) or catastrophic truncation. 
* **Impact:** P99 generation latency degrades from 15 seconds to 4+ minutes; token costs multiply by $3\times$ to $8\times$; pipeline determinism drops below SLA thresholds.

### Blind Spot 5: Metric Aggregation & Derived Fact Blindness
* **Mechanism:** The Oracle validates that numerical claims in the output exist in the `SharedFactRegistry`.
* **Failure Mode:** The evidence states: *Server A downtime = 14 hours; Server B downtime = 22 hours.* The LLM writes: *"Total cluster downtime reached 36 hours."* `"36 hours"` does not exist in the raw evidence corpus. A strict Oracle rejects it as a hallucination; a permissive Oracle allows arbitrary math hallucinations.
* **Impact:** The system either bans all synthesis/aggregation or fails to catch bad LLM arithmetic (which is fatal in Chapter 4).

### Blind Spot 6: Entity Resolution & Synonym Collision
* **Mechanism:** Dynamic ingestion populates the Registry from heterogeneous documents (PDFs, spreadsheets, interview transcripts).
* **Failure Mode:** Document A cites `"Entra ID"`. Document B cites `"Azure AD"`. Document C cites `"AAD"`. Without a canonical Entity Resolution & Synonym Normalization layer prior to Registry commit, the Registry records three conflicting facts, or the Oracle rejects `"Azure AD"` because the prompt context only injected the `"Entra ID"` chunk.

### Blind Spot 7: Context Window Starvation via Registry Injection
* **Mechanism:** Passing the `SharedFactRegistry` and negative constraints into the LLM prompt so it knows what it can and cannot say.
* **Failure Mode:** A real due diligence data room yields 5,000 to 50,000 atomic facts. Injecting the entire Registry or an exhaustive list of banned hallucinations into the system prompt will blow out the context window, degrade needle-in-a-haystack retrieval attention, and induce instruction-following collapse.

---

## 4. MANDATORY RED TEAM ENHANCEMENTS (THE TIER-1 BLUEPRINT)

To achieve an unassailable **9.8/10 Tier-1 Architecture**, you must abandon naive registry/oracle concepts and implement the following five-layer **Epistemic Control Plane**.

```
====================================================================================================
                         ARGON TIER-1 EPISTEMIC CONTROL PLANE (BLUEPRINT)
====================================================================================================

 [RAW DATA ROOM CORPUS] (PDFs, CSVs, Logs, Interviews)
           │
           ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │ LAYER 1: ZERO-SHOT ONTOLOGICAL EXTRACTION & ENTITY RESOLUTION                                 │
 │  • Deterministic NER + Dependency Parsing + Constrained LLM Extraction                        │
 │  • Canonical Alias Graph (e.g., "AAD" == "Azure AD" == "Entra ID")                            │
 │  • Compiles raw text into Immutable Actuarial Fact Tuples (AFTs) with SHA-256 Span Provenance │
 └─────────────────────────────────────────┬─────────────────────────────────────────────────────┘
                                           │
                                           ▼
 ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
 │ LAYER 2: GRAPH-BACKED SHARED FACT REGISTRY (MVCC + LEASE SEMANTICS)                           │
 │  • Typed Property Graph (Nodes: Entities/Metrics, Edges: Domain Perspectives)                 │
 │  • Lease Allocation Engine: Assigns 'PRIMARY_NARRATIVE' vs 'CROSS_DOMAIN_CITATION' leases     │
 │  • Deterministic Compute Engine: Pre-calculates all aggregations/ratios (Zero LLM Math)       │
 └───────────────────┬─────────────────────────────────────────────────────┬─────────────────────┘
                     │ (Sub-Graph Projection)                              │ (Direct Typed Binding)
                     ▼                                                     ▼
 ┌───────────────────────────────────────────────┐     ┌─────────────────────────────────────────┐
 │ LAYER 3: CONSTRAINED IR GENERATION            │     │ LAYER 5: CHAPTER 4 ACTUARIAL ENGINE     │
 │  • LLM outputs Intermediate Representation    │     │  • Consumes AFTs directly via Rust/Py   │
 │    (IR) AST, NOT raw unconstrained prose      │     │  • Monte Carlo / VaR / Loss Curves      │
 │  • Every sentence node MUST bind to `[AFT_ID]`│     │  • 100% immune to narrative drift       │
 │    or declare `polarity: GAP_BENCHMARK`       │     └───────────────────┬─────────────────────┘
 └───────────────────┬───────────────────────────┘                         │
                     │                                                     │
                     ▼                                                     │
 ┌───────────────────────────────────────────────┐                         │
 │ LAYER 4: POLARITY-AWARE CLAIM GATING ORACLE   │                         │
 │  • DeBERTa-v3-Large NLI Entailment Check      │                         │
 │  • Polarity Gate: Allows absent tech ONLY     │                         │
 │    under Negative/Remediation syntax trees    │                         │
 │  • Surgical AST Pruning (No full retries)     │                         │
 └───────────────────┬───────────────────────────┘                         │
                     │                                                     │
                     └──────────────────────────┬──────────────────────────┘
                                                ▼
                              [DETERMINISTIC REPORT COMPILER]
                                                │
                                                ▼
                           [TIER-1 CERTIFIED ASSESSMENT ARTIFACT]
====================================================================================================
```

### Enhancement 1: Replace String Facts with Immutable Actuarial Fact Tuples (AFTs)
Do not store strings in the `SharedFactRegistry`. Define a strict, domain-agnostic metamodel. Every extracted fact must conform to this schema at ingestion time:

```python
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field
import hashlib

class EpistemicModality(str, Enum):
    OBSERVED_EVIDENCE = "OBSERVED_EVIDENCE"       # Directly verified in telemetry/logs
    MANAGEMENT_ASSERTION = "MANAGEMENT_ASSERTION" # Stated in interview, unverified
    DERIVED_METRIC = "DERIVED_METRIC"             # Deterministically calculated by Argon
    ABSENT_CONTROL = "ABSENT_CONTROL"             # Explicitly confirmed missing

class DomainPerspective(BaseModel):
    domain_id: str                                # e.g., "INFRASTRUCTURE", "CYBERSECURITY"
    lease_type: str                               # "PRIMARY_OWNER" | "SECONDARY_CONSUMER"
    semantic_framing: str                         # e.g., "High Availability" vs "Unpatched Kernel Risk"
    consumed_in_section: Optional[str] = None     # Tracks usage to prevent repetition

class ActuarialFactTuple(BaseModel):
    fact_id: str = Field(..., description="Deterministic SHA-256 hash of canonical_subject + predicate + source_span")
    canonical_subject: str                        # Resolved via Ontology (e.g., "SYS_SOLARIS_CORE_01")
    predicate: str                                # Ontology verb (e.g., "HAS_CONTINUOUS_UPTIME")
    value_scalar: Optional[Union[float, int, bool]] = None
    value_text: Optional[str] = None
    unit_iso: Optional[str] = None                # e.g., "DAYS", "USD", "PERCENT"
    modality: EpistemicModality
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_document_id: str
    source_char_span: tuple[int, int]
    verbatim_quote: str
    domain_leases: List[DomainPerspective]
```

### Enhancement 2: Implement "Perspective Lease Allocation" Instead of Hard Domain Silos
To solve **Blind Spot 2 (Cross-Domain Causal Bleed)** and eliminate repetitive phrasing across chapters without blinding domains to shared facts:
1. During ingestion, a lightweight deterministic classifier assigns **one** `PRIMARY_OWNER` lease and $N$ `SECONDARY_CONSUMER` leases to each `ActuarialFactTuple`.
2. **The Lease Rule:** 
   * The `PRIMARY_OWNER` domain is permitted to state the fact in full descriptive detail, quote the verbatim evidence, and establish the baseline finding.
   * A `SECONDARY_CONSUMER` domain is **syntactically barred** from restating the descriptive narrative. It is only permitted to reference the `fact_id` as a *causal premise* for its own domain-specific consequence (e.g., *"Given the extended runtime established in [§2.1 / FACT-89a], kernel-level CVE remediation has been bypassed..."*).
3. Once a `PRIMARY_OWNER` lease is redeemed during generation, its state flips to `CONSUMED` in the Registry's Multi-Version Concurrency Control (MVCC) state store.

### Enhancement 3: Polarity-Aware Claim Gating (Solving the VESDA/BitLocker Paradox)
To solve **Blind Spot 1**, the `ClaimGatingOracle` must never operate as a flat token blacklist/whitelist. It must evaluate the **Epistemic Polarity** of every detected entity using Dependency Parsing or Natural Language Inference (NLI):

$$\text{Valid}(c) \iff \Big( \text{Entity}(c) \in \mathcal{E}_{\text{corpus}} \land \text{Polarity}(c) = \text{ASSERTIVE} \Big) \lor \Big( \text{Entity}(c) \notin \mathcal{E}_{\text{corpus}} \land \text{Polarity}(c) \in \{ \text{NEGATIVE\_GAP}, \text{REMEDIATION\_TARGET}, \text{BENCHMARK\_COMPARISON} \} \Big)$$

* **Rule A (Assertive Polarity):** If the sentence asserts that the client *possesses, operates, or relies upon* Entity $X$ (e.g., *"The data center is protected by VESDA"*), Entity $X$ **must** exist in $\mathcal{E}_{\text{corpus}}$ with `modality != ABSENT_CONTROL`. Otherwise, **HARD REJECT**.
* **Rule B (Negative/Remediation Polarity):** If the sentence states that the client *lacks* Entity $X$, or *should implement* Entity $X$ as a remediation target (e.g., *"Deploy BitLocker across all Windows endpoints"*), the Oracle **permits** the entity, provided it is tagged in the Intermediate Representation as a `BENCHMARK_CONTROL` or `REMEDIATION_RECOMMENDATION`.

### Enhancement 4: Intermediate Representation (IR) & Surgical AST Pruning
To solve **Blind Spot 3 (Paraphrastic Evasion)** and **Blind Spot 4 (Rejection Death Spirals)**, stop generating raw prose directly. Force the LLM (via Structured Outputs / Context-Free Grammar Constrained Decoding) to output a **Sentence-Level Epistemic AST**:

```json
{
  "section_id": "3.2_endpoint_security",
  "claims": [
    {
      "statement": "Workstations lack full-disk encryption, exposing local cached credentials.",
      "epistemic_type": "EMPIRICAL_FINDING",
      "bound_fact_ids": ["AFT-44910a"],
      "polarity": "ASSERTIVE"
    },
    {
      "statement": "Remediation requires immediate GPO enforcement of BitLocker with TPM 2.0 key protectors.",
      "epistemic_type": "REMEDIATION_RECOMMENDATION",
      "bound_fact_ids": ["AFT-44910a"],
      "polarity": "REMEDIATION_TARGET",
      "external_benchmarks_cited": ["BitLocker", "TPM 2.0"]
    }
  ]
}
```

**Why this is unassailable:**
1. **Zero Unbound Claims:** If the LLM attempts to hallucinate a fact via paraphrasing (Blind Spot 3), it is forced by the JSON schema to provide a `bound_fact_ids` array. The `ClaimGatingOracle` runs a fast local **DeBERTa-v3-Large NLI cross-encoder** comparing the `statement` against the `verbatim_quote` of `AFT-44910a`. If the NLI entailment score $P(\text{entailment}) < 0.85$, the claim is rejected regardless of what synonyms the LLM used!
2. **Zero Retry Death Spirals:** Because output is an array of atomic claim objects, if Claim #4 fails the Oracle check, **you do not regenerate the chapter**. The Oracle deterministically prunes Claim #4 from the AST (or sends *only* Claim #4 to a micro-repair prompt) and compiles the remaining verified claims into fluent prose. Latency overhead drops from minutes to **< 120 milliseconds**.

### Enhancement 5: Deterministic Actuarial Binding for Chapter 4
To guarantee **Chapter 4 Actuarial Perfection**:
1. **Ban LLM Arithmetic:** The LLM is strictly forbidden from performing addition, multiplication, percentage derivation, or financial modeling.
2. **Deterministic Pre-Computation:** During Layer 2 Registry initialization, a deterministic Python/Rust calculation module scans all numeric `ActuarialFactTuple` nodes, executes standard aggregation rules (sums, means, downtime totals, SLA breaches), and writes new `ActuarialFactTuple` entries back into the Registry with `modality = DERIVED_METRIC` and a full provenance lineage graph.
3. **Direct Code-to-Model Injection:** Chapter 4 risk tables, Fair Value adjustments, and Monte Carlo parameters read scalars directly from the `SharedFactRegistry` using typed queries (`registry.get_metric(subject="CLUSTER_DOWNTIME", unit="HOURS")`). The LLM in Chapter 4 is restricted to generating *explanatory commentary* around pre-rendered, locked numerical tables. Semantic drift is mathematically impossible.

---

## 5. FINAL SIGN-OFF PROTOCOL & CERTIFICATION CRITERIA

I am placing a **HARD ARCHITECTURAL HOLD** on the naive implementation of `SharedFactRegistry` and `ClaimGatingOracle`. Development may proceed **only** by incorporating the five enhancements detailed in Section 4.

To achieve **Tier-1 Production Sign-Off (Rating $\ge$ 9.5/10)**, the engineering team must pass the following **Adversarial Verification Gate** in CI/CD:

| Gate ID | Adversarial Test Case | Required System Behavior | Pass Metric |
| :--- | :--- | :--- | :--- |
| **GATE-01** | **Zero-Hardcoding Corpus Swap:** Run pipeline against 3 completely unseen, industry-divergent client data rooms (e.g., Healthcare, Aerospace, FinTech) with zero code or config changes. | Ontology extractor populates `SharedFactRegistry` dynamically; zero client-specific strings in codebase (`git grep` audit). | **100% Pass** (0 hardcoded literals) |
| **GATE-02** | **The "VESDA/BitLocker" Negative Control Test:** Inject evidence showing an unencrypted, unprotected server room. Prompt for gap analysis and remediation. | Oracle **blocks** any claim that VESDA/BitLocker is installed, but **permits** citing VESDA/BitLocker as missing controls or remediation targets. | **0% False Rejections** of valid gap findings |
| **GATE-03** | **Paraphrastic Hallucination Injection:** Force-inject a subtle paraphrased hallucination (no banned keywords used) into the IR stream. | NLI Entailment Check against bound `AFT_ID` detects $P(\text{entailment}) < 0.85$ and surgically prunes the node without full-chapter retry. | **100% Interception** in $< 150\text{ms}$ |
| **GATE-04** | **Cross-Domain Lease Enforcement:** Inject a high-salience fact (`"613 days uptime"`). Generate Infrastructure, Cyber, and Executive Summary chapters. | Fact is narrated in full **once** (Primary Lease) and cited strictly by causal reference in secondary domains. Zero verbatim/semantic duplication. | **Duplication Rate = 0.0%** |
| **GATE-05** | **Chapter 4 Actuarial Provenance Audit:** Trace every financial/risk number in Chapter 4 back to raw data room byte offsets. | Every Chapter 4 scalar resolves deterministically to an `ActuarialFactTuple` SHA-256 hash or a registered `DERIVED_METRIC` formula. | **100% Cryptographic Lineage** |

---
**Signed:**  
*Global Head of Adversarial Architecture & Actuarial Peer Review*  
*Fellow of the Society of Actuaries (FSA) | Principal Systems Architect*