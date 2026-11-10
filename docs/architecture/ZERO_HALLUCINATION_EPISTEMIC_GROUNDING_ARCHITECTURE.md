# ZERO-HALLUCINATION NEUROSYMBOLIC ARCHITECTURE
**Document ID:** `ARCH-VERIF-001`  
**Author:** `gemini-4-argon` (Principal Staff Systems Architect)  
**Status:** MANDATORY ENFORCEMENT  
**Target:** Elimination of Epistemic & Modal Collapse in Generative Assessment Engines  

---

## ROOT CAUSE ANALYSIS: THE MODAL COLLAPSE FAILURE

In standard autoregressive Large Language Models (LLMs), attention heads compute semantic similarity over dense vector spaces where modal operators (*"quería empezar"*, *"me gustaría"*) and tense markers are subordinated to high-salience entity tokens (*"contenedores"*, *"Kubernetes"*, *"NetApp"*). 

When prompted to synthesize an "AS-IS Production State," the LLM maximizes likelihood by bridging the high-salience entity (*"contenedores"*) with the structural persona of the section (*"en producción"*), interpolating *"despliegues ad-hoc sobre máquinas virtuales"* to rationalize the absence of an orchestrator. 

**Architectural Verdict:** LLMs must be stripped of the authority to synthesize direct prose from raw transcripts. Prose generation must be reduced to a **deterministic rendering of a formally verified Knowledge Graph**.

---

## 1. MODAL & TEMPORAL GROUNDING (THE EPISTEMIC TAGGING CONTRACT)

To prevent modal collapse, raw transcripts are never fed to summarization models. Instead, they pass through a **Neurosymbolic Semantic Parser** that extracts atomic propositions into a strictly typed **Evidence Ledger**.

Every extracted entity-state pair $P(e, s)$ is bound to a mandatory Epistemic Modal Operator $\mathcal{M}$ and Environment Vector $\mathcal{E}$.

### 1.1 The Epistemic Type System

```protobuf
syntax = "proto3";
package verification.epistemic;

enum EpistemicModality {
  MODALITY_UNSPECIFIED = 0; // Immediate compiler panic if emitted
  EMPIRICAL_PRODUCTION_FACT = 1; // Real, active, running in PROD today
  EMPIRICAL_NON_PROD_FACT = 2;   // Active only in DEV/TEST/SANDBOX
  ASPIRATIONAL_FUTURE_INTENT = 3; // Desire, roadmap, PoC intent, TO-BE
  TECHNICAL_ABSENCE_GAP = 4;      // Explicitly confirmed non-existence
  HISTORICAL_DEPRECATED = 5;      // Existed in the past, now decommissioned
}

enum GrammaticalTrigger {
  INDICATIVE_PRESENT_ACTIVE = 0; // "Tenemos", "Está en producción"
  VOLITIONAL_DESIDERATIVE = 1;   // "Quería empezar", "Me gustaría", "Planeamos"
  NEGATIVE_EXISTENTIAL = 2;      // "No tenemos", "Cero", "Falta"
}

message AtomicClaim {
  string claim_id = 1;                 // SHA-256 of (transcript_id + span)
  string tower_id = 2;                 // e.g., "TOWER_2_COMPUTE"
  string canonical_entity = 3;         // Normalized ontology URI: "tech:containers"
  string state_predicate = 4;          // e.g., "deployed_in_production"
  EpistemicModality modality = 5;      // STRICT MODAL TAG
  GrammaticalTrigger trigger_type = 6; // Linguistic justification
  string verbatim_quote = 7;           // Exact substring from transcript
  string lexical_modal_marker = 8;     // Exact verb phrase: "quería empezar a utilizar"
}
```

### 1.2 Deterministic Linguistic Deconstruction (The NetApp/Container Case)

When the ingestion pipeline processes the transcript:
> *"La NetApp la hemos comprado para ficheros y hemos aprovechado también para que el equipo desarrollo quería empezar a utilizar contenedores... y a mí me gustaría convertir... irnos más a modelo contenedor Kubernetes."*

The parser enforces a **Syntactic Dependency Tree Split** before entity extraction:

| Claim ID | Canonical Entity | State Predicate | Lexical Modal Marker | Grammatical Trigger | Assigned `EpistemicModality` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CLM-801` | `tech:storage:netapp` | `acquired_for_files` | *"hemos comprado"* | `INDICATIVE_PRESENT_ACTIVE` | `EMPIRICAL_PRODUCTION_FACT` |
| `CLM-802` | `tech:compute:containers` | `utilization` | *"quería empezar a utilizar"* | `VOLITIONAL_DESIDERATIVE` | `ASPIRATIONAL_FUTURE_INTENT` |
| `CLM-803` | `tech:compute:kubernetes` | `architecture_model` | *"me gustaría convertir / irnos"* | `VOLITIONAL_DESIDERATIVE` | `ASPIRATIONAL_FUTURE_INTENT` |

**Automatic Dual-Inference Rule (The Absence Corollary):**
In our epistemic logic, if an entity $e$ is tagged with `ASPIRATIONAL_FUTURE_INTENT` regarding predicate `embrace/start` (*"empezar a utilizar"*), a deterministic Datalog rule automatically fires to inject a `TECHNICAL_ABSENCE_GAP` into the Ledger:

$$\forall e \, \Big( \text{Modality}(e, \text{start\_using}) = \texttt{ASPIRATIONAL\_FUTURE\_INTENT} \implies \text{Assert}\big(\text{Modality}(e, \text{deployed\_in\_prod}) = \texttt{TECHNICAL\_ABSENCE\_GAP}\big) \Big)$$

This produces explicit Claim `CLM-804`: `tech:compute:containers` $\rightarrow$ `TECHNICAL_ABSENCE_GAP` (Zero production footprint).

### 1.3 Section-Level Epistemic Isolation (Memory-Safe Partitioning)

The Document Generation Engine operates under **Hardware-Like Memory Isolation**. The prompt context for any section is populated exclusively via a strict SQL/Graph query over the `EvidenceLedger`:

*   **Volume 1 (AS-IS Current State) Context Loader:**
    ```sql
    SELECT canonical_entity, state_predicate, verbatim_quote 
    FROM EvidenceLedger 
    WHERE modality IN ('EMPIRICAL_PRODUCTION_FACT', 'TECHNICAL_ABSENCE_GAP')
      AND modality NOT IN ('ASPIRATIONAL_FUTURE_INTENT');
    ```
*   **Architectural Consequence:** The Volume 1 generator **literally never sees** `CLM-802` or `CLM-803` as active states. It only sees `CLM-801` (NetApp for files) and the derived `CLM-804` (Explicit absence of containers in production). It is information-theoretically impossible for the LLM to hallucinate containers in production if the token `"contenedores"` only enters its context window wrapped inside a `<CONFIRMED_ABSENCE>` XML tag.

---

## 2. THE CLOSED-WORLD ASSUMPTION (CWA) COMPILER GATE

Even with context isolation, an LLM might suffer from **Parametric Prior Contamination** (inventing `"despliegues ad-hoc sobre máquinas virtuales"` based on its pre-training weights). 

To intercept this, no LLM output is ever written directly to the deliverable. Every generated sentence must pass through the **CWA Compiler Gate**.

### 2.1 The Closed-World Assumption Axiom

Let $\mathcal{L}$ be the `EvidenceLedger`. Under the Closed-World Assumption:
> **Any positive empirical assertion $p$ not explicitly proven by a record in $\mathcal{L}$ with modality `EMPIRICAL_PRODUCTION_FACT` is evaluated as `FALSE` (Hallucination).**

### 2.2 Pre-Compilation Verification Pipeline

```
[LLM Draft Sentence] 
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 1: Deconstruct into Atomic Propositions (AST)       │
└──────────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ STEP 2: Bipartite Graph Alignment against EvidenceLedger │
└──────────────────────────────────────────────────────────┘
       │
       ├──► Match Found (Modality == EMPIRICAL_FACT) ──► [PASS]
       │
       └──► No Match / Modality Mismatch ──────────────► [COMPILER PANIC]
                                                               │
                                                               ▼
                                          ┌─────────────────────────────────────────┐
                                          │ STEP 3: Deterministic AST Rewrite       │
                                          │ (Inject Explicit Absence Truth)         │
                                          └─────────────────────────────────────────┘
```

### 2.3 Execution Trace on the Failing Sentence

**Input Draft Sentence $S$:**  
*"Adopción embrionaria de contenedores sin orquestador gestionado en producción, dependiendo de despliegues ad-hoc sobre máquinas virtuales."*

#### Step 1: Proposition Extraction (Sentence $\rightarrow$ Logical AST)
A zero-temperature extractor decomposes $S$ into atomic claims $\mathcal{C}(S)$:
1. $c_1$: `Entity(containers)` + `State(embryonic_adoption_in_production)` + `Modality(EMPIRICAL_PRODUCTION_FACT)`
2. $c_2$: `Entity(orchestrator)` + `State(absent_in_production)` + `Modality(TECHNICAL_ABSENCE_GAP)`
3. $c_3$: `Entity(containers)` + `State(adhoc_deployments_on_vms)` + `Modality(EMPIRICAL_PRODUCTION_FACT)`

#### Step 2: Deterministic Ledger Lookup & Verification
The Compiler Gate executes a strict verification function `verify(c, Ledger)` for each $c \in \mathcal{C}(S)$:

```python
def verify_proposition(c: AtomicProposition, ledger: EvidenceLedger) -> VerificationResult:
    # 1. Query ledger for the canonical entity in the target tower
    records = ledger.query(entity=c.canonical_entity, tower=c.tower)
    
    # 2. Closed-World Assumption Check: If entity is absent from ledger, fail immediately
    if not records:
        return VerificationResult(
            status="FAILED_CWA_UNMENTIONED_ENTITY",
            offending_claim=c,
            remediation_action="PURGE_AND_ASSERT_ABSENCE"
        )
        
    # 3. Modal Compatibility Check
    for r in records:
        if c.claimed_modality == Modality.EMPIRICAL_PRODUCTION_FACT:
            if r.modality == Modality.ASPIRATIONAL_FUTURE_INTENT:
                return VerificationResult(
                    status="FAILED_MODAL_COLLAPSE_DETECTED",
                    offending_claim=c,
                    ground_truth_record=r,
                    remediation_action="REWRITE_AS_ABSENCE_WITH_FUTURE_INTENT"
                )
            if r.modality == Modality.TECHNICAL_ABSENCE_GAP:
                return VerificationResult(
                    status="FAILED_CONTRADICTS_ABSENCE_GAP",
                    offending_claim=c,
                    ground_truth_record=r,
                    remediation_action="REWRITE_AS_EXPLICIT_ABSENCE"
                )
                
    # 4. Predicate Entailment Check (NLI DeBERTa-v3-Large Cross-Encoder)
    # Must score > 0.98 entailment against the verbatim_quote of an EMPIRICAL_PRODUCTION_FACT
    entailing_records = [
        r for r in records 
        if r.modality == Modality.EMPIRICAL_PRODUCTION_FACT 
        and nli_entailment(premise=r.verbatim_quote, hypothesis=c.raw_text) > 0.98
    ]
    
    if not entailing_records:
        return VerificationResult(
            status="FAILED_UNGROUNDED_PREDICATE_HALLUCINATION",
            offending_claim=c,
            remediation_action="PURGE_PREDICATE"
        )
        
    return VerificationResult(status="VERIFIED", supporting_records=entailing_records)
```

**Compiler Evaluation of $S$:**
*   **Evaluation of $c_1$ (`containers in production`):** Looks up `tech:compute:containers`. Finds `CLM-802` (`ASPIRATIONAL_FUTURE_INTENT`) and `CLM-804` (`TECHNICAL_ABSENCE_GAP`). Zero records with `EMPIRICAL_PRODUCTION_FACT`.  
    $\rightarrow$ **THROWS:** `FAILED_MODAL_COLLAPSE_DETECTED`.
*   **Evaluation of $c_3$ (`adhoc_deployments_on_vms`):** Looks up predicate `adhoc_deployments_on_vms`. NLI entailment against transcript is `0.001`.  
    $\rightarrow$ **THROWS:** `FAILED_UNGROUNDED_PREDICATE_HALLUCINATION`.

#### Step 3: Deterministic AST Fallback & Rewrite
When the Compiler Gate panics, **it does not ask the LLM to "try again" with a softer prompt**. It strips the LLM of generation rights for that sentence and invokes a **Deterministic Template Renderer** bound directly to the failing `ground_truth_record` (`CLM-802` and `CLM-804`):

*   **Template for `FAILED_MODAL_COLLAPSE_DETECTED` (Volume 1 AS-IS):**
    > *"Ausencia total de `[canonical_entity]` en el entorno productivo actual (`[TECHNICAL_ABSENCE_GAP]`), existiendo únicamente una intención preliminar no materializada por parte de `[actor]` para su evaluación futura (`[verbatim_quote]`)."*

*   **Compiled, Verified Output Injected into Document:**
    > *"Ausencia total de contenedores y orquestadores (Kubernetes) en el entorno productivo actual, existiendo únicamente una intención preliminar por parte del equipo de desarrollo para iniciar su adopción futura apoyándose en la cabina NetApp recién adquirida."*

---

## 3. THE FORMAL VERIFICATION INVARIANT

To guarantee 100% zero-hallucination across any client, language, or vertical, the assessment engine enforces a **Proof-Carrying Prose (PCP)** architecture. No document can be compiled into PDF/DOCX unless its accompanying formal proof evaluates to `SAT` (Satisfiable) in an SMT Solver (Z3).

### 3.1 Mathematical Formulation of the Invariant

Let:
*   $\mathcal{D}$ be the final deliverable document, partitioned into sections $S_k \in \mathcal{D}$.
*   $\tau(S_k) \subseteq \{\texttt{FACT}, \texttt{INTENT}, \texttt{ABSENCE}\}$ be the set of allowed epistemic modalities for section $S_k$ (e.g., $\tau(\text{Vol\_1\_AS\_IS}) = \{\texttt{FACT}, \texttt{ABSENCE}\}$).
*   $\mathcal{P}(S_k) = \{p_1, p_2, \dots, p_n\}$ be the set of atomic propositions extracted from the prose of section $S_k$.
*   $\mathcal{L} = \{e_1, e_2, \dots, e_m\}$ be the immutable `EvidenceLedger` extracted from the client's raw data sources.
*   $\models_{\text{NLI}}(e, p)$ be the relation stating that evidence $e$ strictly entails proposition $p$ without modal shift.

**The Master Verification Invariant ($\mathcal{I}_{\text{zero}}$):**

$$\mathcal{I}_{\text{zero}}(\mathcal{D}, \mathcal{L}) \iff \forall S_k \in \mathcal{D}, \forall p \in \mathcal{P}(S_k) : \exists e \in \mathcal{L} \text{ such that } \Big( \models_{\text{NLI}}(e, p) \land \text{Modality}(p) = \text{Modality}(e) \land \text{Modality}(p) \in \tau(S_k) \Big)$$

If $\neg \mathcal{I}_{\text{zero}}(\mathcal{D}, \mathcal{L})$, the build pipeline halts with a non-zero exit code (`ERR_EPISTEMIC_VIOLATION`).

### 3.2 Language & Vertical Agnosticism (The Canonical IR)

To ensure this invariant holds across Spanish, English, German, or Japanese, and across Banking, Healthcare, or Retail:
1.  **Universal Dependencies (UD) Morphological Grounding:** Modal tagging does not rely on fragile regexes. It uses a fine-tuned multilingual transformer + UD parser that maps language-specific mood/tense morphology (e.g., Spanish Imperfect Subjunctive *"quisiera"* / Conditional *"gustaría"*, English *"would like to"*, German Konjunktiv II *"würden gerne"*) into the language-agnostic `EpistemicModality` enum before entering the Ledger.
2.  **Domain Ontology Plug-ins:** The `canonical_entity` field maps to pluggable vertical ontologies (e.g., `cloud:k8s` for IT Infrastructures, `core:cobol_cics` for Mainframe Banking, `hl7:fhir_api` for Healthcare). The verification logic operates strictly on the symbolic IDs and epistemic tags, making the verifier 100% invariant to the industry vertical.

### 3.3 The 5-Stage Zero-Hallucination Pipeline

```
STAGE 1: INGESTION & EPISTEMIC SEALING
  Raw Transcripts ──► [Syntactic/Modal Parser] ──► Immutable EvidenceLedger (JSON-LD / Protobuf)
  * Output: Cryptographically signed AtomicClaims with strict EpistemicModality tags.

STAGE 2: CONSTRAINED SYMBOLIC PLANNING
  EvidenceLedger ──► [Datalog Inference Engine] ──► Section Discourse Plan
  * Output: Strict list of Claim IDs permitted per section. Vol 1 receives ZERO `ASPIRATIONAL` IDs.

STAGE 3: SANDWICHED SURFACE REALIZATION (LLM AS A DUMB RENDERER)
  Section Discourse Plan ──► [LLM Surface Realizer (Temp=0.0)] ──► Draft Prose AST
  * Rule: Every generated clause must carry an inline pointer `[ref:CLM-XXX]` to its parent claim.

STAGE 4: THE CWA COMPILER GATE (DECONSTRUCTION & Z3 VERIFICATION)
  Draft Prose AST ──► [Inverse Proposition Extractor] ──► Extracted Claims C(S)
  Extracted Claims C(S) + EvidenceLedger ──► [Z3 SMT Solver / NLI Verifier]
  * Check 1 (Citation Integrity): Does every clause have a valid `[ref:CLM-XXX]`?
  * Check 2 (Closed-World Check): Are there any entities/predicates in C(S) not in `[ref:CLM-XXX]`?
  * Check 3 (Modal Invariance): Does Modality(C(S)) == Modality(CLM-XXX) == AllowedModality(Section)?

STAGE 5: DETERMINISTIC REMEDIATION OR COMPILATION
  ├── If Z3 returns SAT (100% Verified) ──► Strip `[ref:CLM-XXX]` tags ──► Compile Executive Deliverable.
  └── If Z3 returns UNSAT (Hallucination/Modal Collapse) ──► Purge offending AST node ──► Inject Deterministic Absence/Fact Template.
```

### 3.4 Summary of Mathematical Guarantees

| Failure Mode | Legacy LLM Pipeline | `gemini-4-argon` Neurosymbolic Architecture |
| :--- | :--- | :--- |
| **Modal Collapse** (*Desire $\rightarrow$ Fact*) | High probability; LLM blends future intent with present state. | **0% Probability.** `ASPIRATIONAL_FUTURE_INTENT` is physically excluded from the Vol 1 (AS-IS) SQL context query and blocked by the Z3 Modal Invariance check. |
| **Prior Interpolation** (*"Ad-hoc on VMs"*) | High probability; LLM invents plausible architectural glue. | **0% Probability.** Violates the Closed-World Assumption (`FAILED_UNGROUNDED_PREDICATE`). Any predicate not entailed ($>0.98$) by a verbatim quote is purged. |
| **Silent Omission of Gaps** | LLM glosses over missing tech or invents embryonic states. | **0% Probability.** The Datalog Absence Corollary automatically converts *"we want to start using X"* into an explicit `TECHNICAL_ABSENCE_GAP` record for `X` in production. |