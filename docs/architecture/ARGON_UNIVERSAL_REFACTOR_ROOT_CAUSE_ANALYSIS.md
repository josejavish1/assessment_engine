`docs/architecture/ARGON_UNIVERSAL_REFACTOR_ROOT_CAUSE_ANALYSIS.md`

```markdown
# ARGON UNIVERSAL REFACTOR: ROOT CAUSE ANALYSIS & DETERMINISTIC ARCHITECTURE PROPOSAL

**Author:** Gemini-4-Argon, Chief Systems Architect & Global Managing Partner  
**Status:** MANDATORY ARCHITECTURAL DIRECTIVE  
**Target System:** Enterprise Due Diligence Generation Engine (10-Tower Portfolio)  
**Current Audit Rating:** 6.0 / 10.0  
**Target Audit Rating:** 9.8+ / 10.0 (Deterministic, Auditable, Fail-Closed)

---

## 1. ROOT CAUSE IDENTIFICATION IN CURRENT ARCHITECTURE

The overarching failure of the current system stems from an inverted epistemological paradigm: **the system treats the Large Language Model (LLM) as an analytical reasoning engine and source of truth, rather than a constrained natural language rendering engine.** The current pipeline (`[Raw Data -> Unstructured Summary -> LLM Expansion -> Document]`) forces the stochastic model to perform deterministic calculations, resolve evidentiary conflicts, and interpolate missing architectural facts. 

Below is the granular root cause analysis across the nine identified failure domains.

### 1.1. Scoring, Weights, and Maturity Bands
*   **Root Cause:** Non-deterministic mathematical delegation and split-brain configuration.
*   **Architectural Failure:** Sub-pillar weights, tower weights, and maturity band thresholds are currently injected as text into prompt templates or scattered across disparate JSON/YAML files without a unified schema validator. The LLM is tasked with computing weighted averages and mapping numerical scores to qualitative maturity bands (e.g., "Initial", "Managed"). Because LLMs process tokens probabilistically rather than executing floating-point arithmetic, the system exhibits rounding drift, weight hallucination (weights not summing to $1.0$), and inconsistent maturity band assignments between the Executive Summary and individual Tower chapters.

### 1.2. Fact vs. Inference / Hallucination
*   **Root Cause:** Absence of epistemological typing and ontology enforcement in the intermediate data representation.
*   **Architectural Failure:** The ingestion pipeline flattens verified client telemetry, interview transcripts, and preliminary analyst notes into a single, undifferentiated text block. When the LLM is prompted to write an assessment, it cannot distinguish between an immutable *Fact* (e.g., "CrowdStrike Falcon v6.42 is deployed on 82% of endpoints"), an analytical *Inference* (e.g., "The 18% deployment gap exposes legacy servers to ransomware"), and a speculative *Assumption*. Consequently, the LLM elevates unverified inferences into stated architectural facts, violating factual parsimony.

### 1.3. Evidence Retrieval and Attribution
*   **Root Cause:** Context-window stuffing and post-hoc, unverified citation generation.
*   **Architectural Failure:** The current architecture passes massive, coarse-grained markdown summaries into the prompt context without atomic document chunking or immutable `Evidence_ID` hashing. The LLM is instructed to "cite sources," which it accomplishes by hallucinating plausible-sounding document names or attributing claims to an entire 200-page PDF without line, table, or page-level provenance. There is no programmatic verification that a generated claim actually maps to a valid, retrieved evidence node.

### 1.4. Contradictions and Epistemic Conflict Resolution
*   **Root Cause:** Implicit, stochastic conflict resolution inside the LLM attention mechanism.
*   **Architectural Failure:** In enterprise due diligence, data sources frequently conflict (e.g., the CISO states MFA is 100% enforced in an interview, while an Active Directory configuration export shows 34% of service accounts bypass MFA). Currently, both conflicting statements are fed into the context window. The LLM resolves this contradiction silently and arbitrarily—usually favoring whichever statement appears later in the prompt (recency bias) or whichever sounds more comprehensive—rather than flagging an explicit epistemic conflict and applying a deterministic hierarchy of evidentiary trust.

### 1.5. Missing Data and Imputation
*   **Root Cause:** Violation of the "Fail-Closed" principle via generative smoothing.
*   **Architectural Failure:** LLMs are trained via Reinforcement Learning from Human Feedback (RLHF) to be helpful, complete, and fluent. When an ingestion payload lacks data for a specific sub-pillar (e.g., zero documentation provided for Disaster Recovery RTO/RPO testing), the LLM bridges the void by generating generic industry boilerplate or assuming standard configurations exist ("The organization likely utilizes standard cloud backups..."). The system lacks a deterministic pre-check that locks out narrative generation when evidentiary thresholds are not met.

### 1.6. Cross-Tower Contamination (MECE Violations)
*   **Root Cause:** Global context bleeding and lack of domain-scoped data routing.
*   **Architectural Failure:** Every tower synthesizer receives a nearly identical, monolithic global case payload. Without strict Mutually Exclusive, Collectively Exhaustive (MECE) boundaries enforced at the data layer, the LLM repeats high-salience findings across multiple towers. For example, a single critical finding regarding an unpatched ERP database is simultaneously analyzed as an Infrastructure failure (Tower 2), an Application Architecture defect (Tower 3), a Data Governance risk (Tower 4), and a Cyber Security vulnerability (Tower 5), distorting the global risk posture and double-counting maturity penalties.

### 1.7. FAIR (Factor Analysis of Information Risk) Quantification
*   **Root Cause:** Stochastic fabrication of actuarial and probabilistic risk metrics.
*   **Architectural Failure:** The current system prompts the LLM to generate Threat Event Frequency (TEF), Vulnerability (Vuln), Primary Loss Magnitude (PLM), and Secondary Loss Magnitude (SLM) figures directly in markdown tables. The LLM fabricates point estimates or ranges that violate fundamental FAIR mathematical invariants (e.g., stating $LEF > TEF$, or calculating an Annualized Loss Expectancy [ALE] that does not equal the Monte Carlo integration of Frequency $\times$ Magnitude). No actual programmatic simulation (e.g., PERT/Beta distribution sampling) is executed.

### 1.8. Language Consistency and Validation State
*   **Root Cause:** Unchecked generative post-processing and lack of AST-level schema/linguistic gates.
*   **Architectural Failure:** System prompts mix languages (e.g., Spanish structural keys in `blueprint_pilar_architect_prompt.yaml` alongside English instructions), causing the LLM to leak non-English tokens, calques, or inconsistent terminology into the final output. Furthermore, the pipeline lacks a post-generation Abstract Syntax Tree (AST) validator. Markdown tables with broken column counts, invalid maturity strings, and unaccredited claims pass directly to the document compiler without raising fatal exceptions.

### 1.9. Widespread "Expand" Prompting
*   **Root Cause:** Optimization for token volume rather than information density (Anti-Parsimony).
*   **Architectural Failure:** Prompts across the repository explicitly instruct the LLM to *"expand extensively," "write a comprehensive, multi-paragraph deep dive,"* and *"elaborate on the architectural implications."* When paired with sparse input data, these directives act as a direct command to hallucinate. The model pads the document with consultant-speak, speculative technologies, and unverified architectural patterns to satisfy length constraints.

---

## 2. MODULES CAUSING THE BEHAVIOR

The following specific modules, prompts, and configuration files within the current repository are directly responsible for the architectural failures detailed above:

| Module / File Path | Defective Logic & Architectural Violation |
| :--- | :--- |
| `src/ingestion/build_case_input.py` | **Context Flattening & Contamination:** Ingests raw dataroom files and concatenates them into a monolithic, untyped JSON/Markdown blob (`case_summary.md`). Strips granular metadata (page numbers, row IDs, document timestamps) and fails to route evidence by MECE tower tags. |
| `src/pipeline/payload_to_ast.py` | **Permissive Parsing & Silent Imputation:** Converts intermediate JSON payloads into document AST nodes using `.get(key, "Standard configuration assumed")` patterns. Instead of raising a `MissingEvidenceError`, it injects default fallback strings that mask missing data and feed downstream hallucinations. |
| `src/synthesis/chapter4_synthesizer.py` | **Stochastic Aggregation & FAIR Fabrication:** Orchestrates cross-tower synthesis and financial risk quantification by feeding all 10 tower narratives back into an LLM context window. Prompts the LLM to calculate aggregate portfolio scores and generate FAIR risk tables via text generation rather than invoking a mathematical solver. |
| `prompts/blueprint_pilar_architect_prompt.yaml` | **"Expand" Directives & Linguistic Bleed:** Contains mixed-language structural keys (`pilar`, `subpilar`, `ponderacion`) and explicit instructions such as: *"Expand upon the provided summary to create an exhaustive enterprise-grade analysis. Infer standard architectural components where explicit details are sparse."* |
| `prompts/tower_deep_dive_synthesizer.yaml` | **Epistemic Conflation & Unbound Attribution:** Instructs the model to weave facts, gaps, and recommendations into continuous prose paragraphs without structured claim-evidence binding. Allows the LLM to determine sub-pillar scores on the fly based on "overall sentiment of the evidence." |
| `config/scoring_matrix.json` & `src/scoring/score_calculator.py` | **Split-Brain Scoring Logic:** `score_calculator.py` allows the LLM's JSON output to override pre-calculated deterministic scores if the LLM provides a "qualitative justification." `scoring_matrix.json` lacks a strict JSON Schema, allowing sub-pillar weights within a tower to sum to $\neq 1.000$. |
| `src/compiler/markdown_to_docx.py` | **Blind Compilation (Zero Pre-Document Validation):** Directly compiles LLM-generated Markdown into the final deliverable without running pre-flight validators for citation integrity, numerical consistency, forbidden speculative phrasing, or 100% Technical English compliance. |

---

## 3. PROPOSED NEW ARCHITECTURAL FLOW

To achieve a 9.8+/10 audit rating, the architecture must undergo a total paradigm shift. **The LLM is demoted from "Analyst and Author" to "Constrained Verbalizer of Accredited Claims."** 

All math, scoring, contradiction resolution, missing data detection, and FAIR Monte Carlo simulations must be executed deterministically in Python *before* any LLM invocation occurs.

### 3.1. High-Level Deterministic Pipeline Topology

```
[Original Sources (PDF, XLSX, JSON, Transcripts)]
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & ATOMIC EVIDENCE LEDGER (`EvidenceRegistry`)           │
│    • Deterministic chunking, SHA-256 hashing, metadata extraction.   │
│    • Assigns immutable `EV-XXXX` IDs and Epistemic Trust Tiers.      │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 2. EPISTEMIC RESOLUTION & FACT EXTRACTION                            │
│    • `SharedFactRegistry`: Canonical global facts (Tech stack, HC).  │
│    • `ContradictionEngine`: Detects conflicts, applies Trust Tiers.  │
│    • `MissingDataGate`: Enforces FAIL-CLOSED on unverified metrics.  │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 3. DETERMINISTIC ANALYTICAL ENGINES (ZERO LLM INVOLVEMENT)           │
│    • `MasterFrameworkMatrix`: Single Source of Truth for weights.    │
│    • `ScoringEngine`: Exact float math, rubric-based band mapping.   │
│    • `FAIREngine`: Scipy/Numpy Monte Carlo (10,000 iterations).      │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 4. MECE ROUTING & CLAIM LEDGER CONSTRUCTION (`TowerContextBuilder`)  │
│    • Scopes payload strictly to Tower $N$ + `SharedFactRegistry`.    │
│    • Builds `ClaimLedger`: Binds `[Fact | Gap | Implication | Rec]`  │
│      directly to `EV-XXXX` IDs and deterministic scores.             │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 5. CONSTRAINED LLM VERBALIZATION (FACTUAL PARSIMONY)                 │
│    • Prompted strictly to render the `ClaimLedger` into prose.       │
│    • Zero inference, zero expansion, zero math permitted.            │
└──────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────────────────┐
│ 6. PRE-DOCUMENT AST VALIDATORS (FAIL-CLOSED GATES)                   │
│    • `validate_framework()`, `validate_citations()`,                 │
│    • `validate_numbers()`, `LanguagePolicyEngine`.                   │
└──────────────────────────────────────────────────────────────────────┘
       │ (Pass 100% of Assertions)
       ▼
[Final Audited Deliverable (DOCX / PDF / AST)]
```

---

### 3.2. Detailed Specification of Core Architectural Components

#### A. Single Source of Truth for the Framework (`MasterFrameworkMatrix`)
*   **Implementation:** `src/core/framework_matrix.py` backed by an immutable, schema-locked configuration `config/master_framework_v4.json`.
*   **Mechanics:** Defines all $N$ Towers, their constituent Sub-Pillars, exact decimal weights ($w_i \in (0, 1]$), evaluation rubrics, and MECE taxonomy tags.
*   **Invariant:** Upon system boot, `validate_framework()` executes. It asserts using `decimal.Decimal` (to prevent IEEE 754 floating-point drift) that $\sum w_{\text{subpillar}} == 1.0000$ for every tower, and $\sum w_{\text{tower}} == 1.0000$ for the portfolio. If violated, the pipeline halts immediately with a `FrameworkIntegrityError`.

#### B. 100% Deterministic `ScoringEngine` and `FAIREngine`
*   **Implementation:** `src/engines/scoring_engine.py` and `src/engines/fair_engine.py`.
*   **Scoring Mechanics:** The LLM **never** calculates or modifies a score. Each sub-pillar is evaluated against structured boolean/numerical rubric criteria derived from the `ClaimLedger`.
    *   Sub-pillar score $S_{t,s} \in [1.0, 5.0]$ is computed via deterministic rubric evaluation.
    *   Tower score $S_t = \sum_{s=1}^{k} (w_{t,s} \cdot S_{t,s})$.
    *   Maturity Bands are mapped strictly via deterministic interval lookup:
        *   $[1.00, 1.80) \rightarrow \text{Level 1: Initial / Ad-Hoc}$
        *   $[1.80, 2.60) \rightarrow \text{Level 2: Repeatable}$
        *   $[2.60, 3.40) \rightarrow \text{Level 3: Defined}$
        *   $[3.40, 4.20) \rightarrow \text{Level 4: Managed}$
        *   $[4.20, 5.00] \rightarrow \text{Level 5: Optimized}$
*   **FAIR Mechanics:** `FAIREngine` ingests structured threat parameters (Min, Most Likely, Max, Confidence) mapped from verified gaps. It executes a 10,000-iteration Monte Carlo simulation using Beta-PERT distributions via `numpy`/`scipy` (with a fixed random seed for 100% audit reproducibility). It outputs an immutable `FAIRResult` object containing 10th, 50th (Median), and 90th percentile Annualized Loss Exposure (ALE) values. The LLM receives these exact strings as read-only constants.

#### C. `EvidenceItem` and `Claim` Ledgers (Claim-Level Evidence Gating)
*   **Implementation:** `src/ledgers/evidence_ledger.py` and `src/ledgers/claim_ledger.py` (enforced via Pydantic v2 strict models).
*   **Mechanics:**
    *   `EvidenceItem`: Every ingested artifact chunk is assigned a deterministic hash ID (e.g., `EV-8F3A`), source file path, exact location pointer (page/row/cell/timestamp), extraction method, and an `EpistemicTrustTier` (`TIER_1_SYSTEM_TELEMETRY`, `TIER_2_CONFIG_EXPORT`, `TIER_3_DOCUMENTATION`, `TIER_4_VERBAL_INTERVIEW`).
    *   `Claim`: No sentence containing a technical assertion can be sent to the document compiler unless it is encapsulated in a `Claim` object. A `Claim` requires at least one valid `EV-XXXX` reference. If a claim lacks an `EV-XXXX` pointer, the `ClaimLedger` rejects its instantiation.

#### D. `ContradictionEngine` and Missing Data Rules (Fail-Closed Technical Facts)
*   **Implementation:** `src/engines/contradiction_engine.py` and `src/engines/missing_data_gate.py`.
*   **Contradiction Mechanics:** When two `EvidenceItem` nodes map to the same architectural attribute with conflicting values (e.g., `EV-0012` [Interview] states `encryption_at_rest = True` vs. `EV-0089` [AWS Config JSON] states `encryption_at_rest = False`), the `ContradictionEngine` intercepts both before LLM synthesis.
    1.  It resolves the canonical state using strict Epistemic Trust Tier precedence (`TIER_1 > TIER_2 > TIER_3 > TIER_4`).
    2.  It generates a mandatory `ContradictionRecord` that forces the downstream narrative to explicitly report the discrepancy (e.g., *"Management asserted X [EV-0012]; however, system telemetry confirms Y [EV-0089]. Assessment is anchored to telemetry."*).
*   **Missing Data (Fail-Closed) Mechanics:** If a sub-pillar or required technical attribute has zero mapped `EvidenceItem` objects, `MissingDataGate` sets the attribute state to `UNVERIFIED_DATA_GAP`.
    *   **Rule:** Missing data **never** defaults to "average" or "assumed present."
    *   It triggers an automatic rubric penalty in the `ScoringEngine` (capping the sub-pillar score at a maximum of `1.50` [Initial]) and outputs a deterministic boilerplate string: `"INSUFFICIENT EVIDENCE: Client did not provide verifiable artifacts for [Attribute]. Scored Fail-Closed."` The LLM is bypassed or strictly forbidden from elaborating on the missing domain.

#### E. `TowerContextBuilder` and `SharedFactRegistry` (MECE Isolation)
*   **Implementation:** `src/routing/tower_context_builder.py` and `src/registries/shared_fact_registry.py`.
*   **Mechanics:**
    *   `SharedFactRegistry`: Holds global, immutable baseline constants (e.g., Total IT Headcount, Annual IT OpEx/CapEx, Core ERP Vendor, Primary Cloud Providers). All towers read from this registry so baseline numbers never diverge across chapters.
    *   `TowerContextBuilder`: Enforces strict MECE isolation. When building the context payload for Tower $T$, it queries the `ClaimLedger` strictly for claims where `primary_tower_id == T`. If a finding in Tower $T$ has secondary implications for Tower $K$, the builder injects a lightweight `CrossReferencePointer` (`XREF-TK-01`) rather than duplicating the evidence. The LLM in Tower $K$ is instructed to render a one-line reference to Tower $T$ without re-analyzing or re-scoring the defect.

#### F. Explicit Epistemological Separation (Fact, Evidence, Gap, Implication, Recommendation)
*   **Implementation:** `src/models/epistemic_unit.py`.
*   **Mechanics:** The unstructured "deep-dive paragraph" is abolished. Every analytical block in the AST must be instantiated as an `EpistemicUnit` containing five strictly separated, schema-validated fields:
    1.  `Fact`: Objective current state statement (Strictly bound to `EV-XXXX`).
    2.  `Evidence`: Direct quote, metric, or configuration parameter extracted from `EV-XXXX` (with Trust Tier badge).
    3.  `Gap`: The deterministic delta between the `Fact` and the `MasterFrameworkMatrix` target rubric criterion.
    4.  `Implication`: The technical or operational risk resulting from the `Gap` (linked to `FAIREngine` output if quantifiable).
    5.  `Recommendation`: Concrete remediation action, tagged with deterministic effort/cost T-shirt sizing and target horizon (Day 1, 100-Day, Post-Merger).
*   **LLM Role:** The LLM is only permitted to polish the syntax of `Implication` and `Recommendation` while strictly preserving all entity names, metrics, and `EV-XXXX` tags.

#### G. `LanguagePolicyEngine` and Pre-Document Validators
*   **Implementation:** `src/validators/pre_document_validators.py` and `src/validators/language_policy_engine.py`.
*   **Mechanics:** Before `markdown_to_docx.py` is permitted to execute, the generated AST must pass a mandatory suite of deterministic assertion gates. Any failure raises a fatal exception, halting compilation:
    *   `validate_framework(ast, master_matrix)`: Verifies all towers, sub-pillars, weights, and rubric mappings match the Single Source of Truth.
    *   `validate_numbers(ast, scoring_engine, fair_engine, shared_facts)`: Extracts all numerical tokens/metrics from the AST via regex/NLP and asserts 100% exact equality against the deterministic outputs of the `ScoringEngine`, `FAIREngine`, and `SharedFactRegistry`.
    *   `validate_citations(ast, evidence_ledger)`: Extracts every `[EV-XXXX]` tag in the document. Asserts that every tag exists in the `EvidenceRegistry`, belongs to the correct MECE tower, and that zero factual sentences exist without an `[EV-XXXX]` tag.
    *   `LanguagePolicyEngine.validate(ast)`:
        1.  **100% Technical English Enforcement:** Scans all AST text nodes and structural headers against a linguistic classifier and forbidden-token dictionary to ensure zero Spanish/non-English leakage.
        2.  **Anti-Hallucination / Anti-Speculation Lexicon Gate:** Scans for and blocks hedge words that indicate unauthorized LLM inference (e.g., *"likely", "probably", "it can be assumed", "typically", "appear to have", "presumably"*). If detected, the node is rejected for violating Factual Parsimony.
```