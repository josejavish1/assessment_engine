# MASTER ARCHITECTURAL BLUEPRINT: UNIVERSAL RISK & ASSESSMENT ENGINE (V4-ARGON)

**Document ID:** ARCH-2026-ARGON-001  
**Classification:** Engineering Mandate / Architectural Invariant  
**Author:** `gemini-4-argon` (Principal Staff Systems Architect, Lead Actuary, CRO)  
**Target State:** 100% Deterministic Routing, Zero Cross-Tower Bleed, Zero Hardcoding, 100% English Core, Universal Vertical Agnosticism.

---

## 0. FOUNDATIONAL INVARIANTS (NON-NEGOTIABLE)

Before executing Phase 1, the codebase must conform to three structural laws. Any violation will fail the build at the AST (Abstract Syntax Tree) analysis level.

1. **The Linguistic Isolation Law:** Every identifier, variable, comment, internal prompt, log message, database column, and exception string MUST be in canonical Technical English. Localization is strictly an Edge View-Layer concern resolved via `i18n` JSON resource bundles injected at the final serialization boundary.
2. **The Zero-Hardcoding Law:** No industry vertical, vendor name, regulatory framework, or scoring threshold may exist in imperative code (`.ts`, `.py`, `.go`). All domain knowledge must be externalized into declarative, version-controlled Ontological Schemas (YAML/JSON-LD) or dynamically resolved via Vector/Graph embeddings.
3. **The Scale-Invariance Law:** The engine calculates risk and maturity using normalized, non-parametric statistical distributions (e.g., percentiles, Z-scores, and log-normal exposure curves) rather than static dollar amounts or headcount tiers, enabling seamless scaling from a €20M regional logistics firm to a $50B global investment bank.

---

## PHASE 1: EPISTEMIC ROUTER & EVIDENCE PURITY
**Objective:** Eradicate the `0.055` static broadcast threshold bleed. Replace naive cosine-similarity broadcasting with an information-theoretic, Winner-Takes-Primary (WTP) routing engine that guarantees evidence purity across assessment towers.

### 1.1 The Problem with Static Thresholds (`0.055`)
A static similarity threshold (`0.055`) fails because embedding space density varies wildly across domains. In high-density clusters (e.g., general IT compliance), `0.055` broadcasts a single piece of evidence to 8+ towers, causing severe cross-tower contamination and hallucinated syntheses.

### 1.2 Architectural Solution: Dynamic Z-Score Routing & Shannon Entropy Gating
We replace the static threshold with a two-stage Epistemic Router:

1. **Stage 1: Dense-Sparse Hybrid Retrieval (Reciprocal Rank Fusion)**
   Combine dense vector embeddings (semantic intent) with sparse BM25/SPLADE tokens (exact technical nomenclature/acronyms) using Reciprocal Rank Fusion (RRF):
   $$\text{RRF\_Score}(d \in D, t \in T) = \frac{1}{\eta + \text{rank}_{\text{dense}}(d, t)} + \frac{1}{\eta + \text{rank}_{\text{sparse}}(d, t)}$$
   *(Where $d$ is the evidence chunk, $t$ is the target Tower, and $\eta = 60$ is the smoothing constant).*

2. **Stage 2: Winner-Takes-Primary (WTP) with Z-Score Secondary Bounding**
   For a given evidence chunk $d$, calculate the distribution of $\text{RRF\_Score}$ across all candidate towers $T$:
   * **Primary Assignment ($T_{\text{primary}}$):** Strictly assigned to $\arg\max_{t \in T} \text{RRF\_Score}(d, t)$, provided the score exceeds the global noise floor (dynamically calibrated via Out-Of-Distribution detection).
   * **Secondary Assignment ($T_{\text{secondary}}$):** A tower $t_i$ receives the evidence as *contextual-only* (read-only, cannot drive primary scoring) if and only if its Z-score satisfies:
     $$Z(t_i) = \frac{\text{Score}(t_i) - \mu_T}{\sigma_T} \ge 2.326 \quad (\text{Top } 1\% \text{ tail})$$
   * **Entropy Rejection (GIGO Shield):** Calculate the normalized Shannon Entropy $H_{\text{norm}}(d)$ of the routing probability distribution. If $H_{\text{norm}}(d) > 0.85$, the evidence is too ambiguous/generic (e.g., marketing fluff). It is routed to the `Epistemic_Quarantine_Sink` and excluded from all towers.

### 1.3 Data Contract: Evidence Envelope
```typescript
export interface EvidenceEnvelope {
  readonly id: string;
  readonly rawContentHash: string;
  readonly epistemicMetadata: {
    readonly shannonEntropy: number;
    readonly signalToNoiseRatio: number;
    readonly isQuarantined: boolean;
  };
  readonly routing: {
    readonly primaryTowerId: string; // Mutually exclusive. Drives actuarial scoring.
    readonly contextualTowerIds: readonly string[]; // Read-only reference. Cannot alter tower base score.
    readonly zScoreDistribution: Record<string, number>;
  };
}
```

---

## PHASE 2: AUTONOMOUS ONTOLOGICAL EXPANSION
**Objective:** Enable the engine to assess unknown, niche, or ultra-specialized verticals (e.g., Submarine Cable Laying, Nuclear Enrichment, High-Frequency Algorithmic Trading) with zero code changes and zero hardcoded taxonomies.

### 2.1 Architectural Solution: Meta-Ontology & Dynamic Graph Hydration
Instead of hardcoding industry taxonomies, the engine will utilize a **3-Tier Meta-Ontology Framework** backed by a Neo4j/ TypeDB Knowledge Graph and a declarative JSON-Schema registry.

1. **Tier 0: The Universal Actuarial Core (Immutable)**
   Defines abstract, physics-level risk primitives that apply to all human enterprises: *Single Point of Failure (SPOF), Mean Time To Recovery (MTTR), Regulatory Revocation Exposure, Counterparty Default, Key-Person Dependency, Capital Liquidity Ratio.*
2. **Tier 1: Sector Archetypes (Declarative Graph)**
   Maps Tier 0 primitives to broad operational topologies (e.g., *Continuous Process Manufacturing, Regulated Financial Custodianship, Distributed Physical Logistics*).
3. **Tier 2: Autonomous Just-In-Time (JIT) Taxonomy Synthesis**
   When an organization's NAICS/ISIC code or ingestion corpus falls outside high-confidence graph coverage, the **Ontological Expansion Agent** executes before the assessment begins:
   * Extracts domain-specific entities, standards (e.g., DO-178C for Aerospace, NERC CIP for Utilities), and failure modes from the ingested corpus and authoritative external registries.
   * Synthesizes a transient, strictly typed **Domain Overlay Graph (DOG)** that maps niche controls directly to Tier 0 Actuarial Primitives.
   * Persists the validated overlay into the Vector/Graph store for future reuse (Self-Learning Flywheel).

### 2.2 Scale Normalization Engine (Mid-Market vs. Fortune 500)
To evaluate a €20M company and a $50B enterprise using the exact same engine, all inputs are passed through a **Parametric Complexity Scaler** before scoring:

$$\text{Expected\_Control\_Maturity}(T_i) = \Phi\left( \alpha \cdot \ln(\text{Revenue}) + \beta \cdot \text{Regulatory\_Density} + \gamma \cdot \text{Topological\_Complexity} \right)$$

* A €20M regional trucking company is not penalized for lacking a 24/7 internal SOC with custom SIEM rules if they have a contractually bound MDR vendor; a $50B bank is catastrophically penalized for the same setup. The scoring engine evaluates **Residual Risk Relative to Operational Complexity**, not absolute checklist matching.

---

## PHASE 3: DELIVERABLE SYNTHESIS & SEMANTIC FIREWALLS
**Objective:** Achieve 100% deliverable quality. Eliminate cross-tower contamination, hallucinated metrics, and linguistic bleed before any output is persisted to the database or rendered to the user.

### 3.1 The Semantic Firewall Architecture
No LLM generation step is allowed to write directly to the database or presentation layer. Every synthesis node is wrapped in a deterministic **Semantic Firewall** operating as a synchronous middleware pipeline:

```
[Tower Evidence (Primary Only)] 
       │
       ▼
[Constrained Synthesis Engine (100% English System Prompts)]
       │
       ▼
[Gate 1: Structural & Schema Validator (Zod / Pydantic)]
       │
       ▼
[Gate 2: Cross-Tower Contamination Firewall (Orthogonal Vector Check)]
       │
       ▼
[Gate 3: Epistemic Grounding Verifier (NLI Entailment Check)]
       │
       ▼
[Gate 4: Edge Localization Transformer (Target Locale JSON Injection)]
       │
       ▼
[Immutable Deliverable Persistence]
```

### 3.2 Firewall Gate Specifications
* **Gate 1: Zero-Trust Schema Enforcement:** Output must strictly conform to pre-compiled AST schemas. Every claim must contain an array of `evidenceChunkIds[]`. Claims with empty arrays are rejected immediately.
* **Gate 2: Cross-Tower Contamination Check:** Every generated paragraph in Tower $A$ is embedded in real-time and compared against the centroids of all other Towers $B \dots Z$.
  * *Invariant:* If $\text{CosineSim}(\text{Paragraph}_{A}, \text{Centroid}_{B}) > \text{CosineSim}(\text{Paragraph}_{A}, \text{Centroid}_{A})$, the firewall throws a `CrossTowerContaminationException`, strips the offending paragraph, and triggers a targeted regeneration with a negative constraint penalty against Tower $B$'s vocabulary.
* **Gate 3: Natural Language Inference (NLI) Grounding:** A lightweight, high-speed DeBERTa-v3 NLI cross-encoder evaluates every synthesized assertion against its cited `evidenceChunkIds[]`. Each pair is scored for `Entailment`, `Neutral`, or `Contradiction`. Any assertion scoring $< 0.88$ `Entailment` is rejected as a hallucination.
* **Gate 4: Edge Localization & Linguistic Purity:** The synthesis engine thinks, reasons, and generates the canonical deliverable AST in 100% Technical English. Only after Gates 1–3 pass does the **Edge Localization Transformer** translate the AST values into the client's target language (e.g., Spanish, German, Japanese) using a deterministic, domain-locked glossary lookup table combined with an isolated translation pass.

---

## PHASE 4: CI/CD QUALITY GATES & ARCHITECTURAL INVARIANTS
**Objective:** Mathematically prove the 10/10 standard on every commit. Prevent regressions, linguistic bleed, and routing degradation from ever merging into `main`.

### 4.1 Pipeline Gate 1: Static AST Linguistic & Hardcoding Linter (`< 15 seconds`)
Every PR triggers a custom Tree-sitter / ESLint / Ruff AST scanner:
1. **Natural Language Detector (Zero-Spanish Rule):** Scans all string literals, comments, variable names, and prompt templates using a fast trigram language model + dictionary filter. If a single Spanish token (or non-English word) is detected outside of `/locales/*.json`, the build fails immediately.
2. **Hardcoding Detector:** Bans magic numbers (e.g., `0.055`, `0.75`) and bans string literals inside routing/scoring directories. Enforces that all constants must be imported from validated configuration schemas.

### 4.2 Pipeline Gate 2: Property-Based & Metamorphic Testing (`< 2 minutes`)
Using Hypothesis (Python) or fast-check (TypeScript), run 10,000 randomized synthetic company profiles through the scoring and routing engine on every build:
* **Monotonicity Invariant:** Adding positive evidence to Tower $A$ must *never* decrease the score of Tower $A$ and must *never* alter the primary score of Tower $B$ ($\frac{\partial \text{Score}(B)}{\partial \text{Evidence}(A)} = 0$).
* **Scale Continuity Invariant:** Smoothly scaling company revenue from $10M to $100B while holding control evidence constant must produce a continuous, non-oscillating risk curve without step-function cliffs.

### 4.3 Pipeline Gate 3: The Golden Corpus Confusion Matrix (`< 5 minutes`)
Maintain an immutable, multi-vertical Golden Corpus containing 500 labeled, adversarial evidence chunks (including deliberate multi-domain traps, e.g., *"An SAP ERP invoice for a physical firewall installation at a nuclear plant"*):
* **Routing Precision/Recall Invariant:** The Epistemic Router must achieve a Macro-F1 score of $\ge 0.985$ on Primary Tower assignment and $0.000$ false-positive bleed into unrelated towers.
* **GIGO Rejection Invariant:** 100% of synthetic noise/marketing fluff documents injected into the test suite must be routed to `Epistemic_Quarantine_Sink`.

---

## EXECUTION ROADMAP & CUTOVER STRATEGY

| Sprint / Milestone | Architectural Deliverables | Exit Criteria (Mathematical Proof) |
| :--- | :--- | :--- |
| **Milestone 1: Linguistic & Config Purge** | Extract all strings to `/locales/`. Extract all domain arrays and magic numbers (`0.055`) to declarative schemas. Deploy AST CI/CD Linter. | `0` non-English tokens in codebase. `0` magic numbers in routing/scoring modules. Build passes Gate 1. |
| **Milestone 2: Epistemic Router v4** | Implement Hybrid RRF + Z-Score WTP Router + Shannon Entropy Quarantine. Deprecate legacy broadcast router. | Cross-tower evidence bleed reduced to `0.0%` on Golden Corpus. Ambiguous inputs quarantined at `100%` rate. |
| **Milestone 3: Autonomous Ontology Engine** | Deploy Tier 0/1/2 Meta-Ontology Graph and JIT Domain Overlay synthesis. Implement Parametric Complexity Scaler. | Engine successfully generates complete, hallucination-free risk models for 3 unseen verticals (e.g., Biotech, Maritime, Space) with zero code edits. |
| **Milestone 4: Semantic Firewalls & Cutover** | Wrap all synthesis nodes in Gates 1–4 (Schema, Orthogonal Vector Check, NLI Entailment, Edge Localization). | `100%` of generated claims mathematically entailed by primary evidence ($P(\text{Entailment}) \ge 0.88$). `0.0%` cross-tower vocabulary bleed. |