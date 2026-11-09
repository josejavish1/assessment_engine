---
status: Approved
owner: architecture-council
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- architecture
doc_type: strategic
diataxis: reference
verification_mode: editorial
---

# RFC-0042: Architectural Remediation of Assessment Synthesis & Mathematical Invariants

* **Author:** `gemini-4-argon` (Principal Enterprise Systems Architect & Forensic Auditor)
* **Status:** APPROVED FOR EXECUTION
* **Compliance Mandate:** 100% Universal Agnosticism | Zero Hardcoding | 100% Technical English Codebase | Strict SSOT Enforcement

---

## 1. Executive Summary & Forensic Audit Posture

A forensic audit of the assessment generation pipeline revealed five systemic vulnerabilities that compromise the mathematical integrity, empirical truth, and technical credibility of the platform's outputs. The pipeline currently permits subjective user input to override empirical telemetry, exhibits split-brain definitions of maturity boundaries, violates Open FAIR (Factor Analysis of Information Risk) cost-accounting taxonomy, and lacks sufficient ontological guardrails to prevent storage-protocol hallucinations in container orchestration contexts.

This RFC establishes a four-phase surgical execution plan. It enforces a strict separation of concerns, establishes canonical Single Sources of Truth (SSOT), and guarantees that the engine remains universally applicable across any industry vertical, enterprise scale, currency, or target localization without relying on brittle, client-specific heuristics.

---

## 2. Phased Strategic Execution Plan

### PHASE 1: Canonical Scale Unification & Taxonomic Invariants
**Objective:** Eliminate split-brain maturity definitions (Defect 4) to ensure that downstream arbitration and AST rendering operate on a single, immutable mathematical foundation.

*   **Target Files:**
    *   `maturity_band.py` (Canonical SSOT)
    *   `payload_to_ast.py` (Consumer)
*   **Architectural Invariant to Enforce:**
    *   **The Single Scale Invariant:** No presentation or AST-transformation module may define, calculate, or hardcode numerical boundary intervals. All maturity interval definitions must be dynamically queried from `maturity_band.py`.
*   **Surgical Remediation Strategy:**
    1.  **Audit `maturity_band.py`:** Expose a public, immutable data structure or accessor method (e.g., `get_canonical_scale_intervals()`) that returns the exact boundary tuples (`1.00–1.59`, `1.60–2.59`, `2.60–3.59`, `3.60–4.59`, `4.60–5.00`) along with their canonical Technical English designation keys.
    2.  **Refactor `payload_to_ast.py`:** Locate the Section 2 rendering logic where the legacy equidistant intervals (`1.0–1.8`, `1.8–2.6`, etc.) are hardcoded. Rip out the static interval declarations and replace them with a dynamic iteration over the canonical data structure imported from `maturity_band.py`.
    3.  **Verification:** Section 2 (Methodology/Scale Overview) and Section 3 (Domain Scoring) will become mathematically incapable of drifting out of sync.

---

### PHASE 2: Forensic SSOT Score Arbitration & Narrative Alignment
**Objective:** Eradicate subjective survey hallucinations (Defect 1) and the resulting narrative contradictions in the Executive Summary (Defect 2) by transitioning from "Survey Overwrite" to "Forensic Evidence Arbitration."

*   **Target Files:**
    *   `score_reconciler.py` (Arbitration Engine)
    *   `payload_to_ast.py` (AST & Narrative Resolver)
    *   Localization Dictionaries / i18n String Templates (specifically targeting `p4_modernization_mandate`)
*   **Architectural Invariants to Enforce:**
    *   **The Empirical Supremacy Invariant:** Self-assessed survey telemetry (`S_survey`) is treated as *unverified assertion*. Synthesized LLM telemetry derived from architectural discovery (`S_empirical`) is treated as *verified evidence*. When `S_survey > S_empirical` beyond a configurable variance threshold ($\Delta > 1.0$), the engine must reject the survey inflation, lock the canonical score to `S_empirical`, and emit a `PerceptionGapWarning` metadata flag.
    *   **The Narrative Floor Invariant:** A capability cannot be designated or praised as an organizational "strength" in the AST unless its reconciled canonical score meets or exceeds the canonical threshold for "Defined/Competent" maturity (i.e., $\ge 2.60$ per `maturity_band.py`).
*   **Surgical Remediation Strategy:**
    1.  **Refactor `score_reconciler.py`:**
        *   Remove the blind assignment logic that overwrites LLM pillar scores with raw survey scores.
        *   Implement an **Asymmetric Forensic Arbitration Algorithm**:
            *   If `S_empirical` exists and is grounded by negative evidence (e.g., absence of technology, score $\le 1.59$), `S_canonical = S_empirical`.
            *   Calculate `perception_delta = S_survey - S_empirical`. Attach this metric to the pillar payload to explicitly report on "Executive Blindspots / Dunning-Kruger Risk" in the output, turning a pipeline defect into a high-value consulting insight.
    2.  **Harden `payload_to_ast.py`:**
        *   In the resolver for `p4_modernization_mandate`, decouple the logic from a naive `max(pillar_scores)` lookup.
        *   Implement a conditional gate: Query the highest-scoring canonical pillar. If `max_pillar.score >= 2.60`, resolve the template using the standard "capability strength" phrasing. If `max_pillar.score < 2.60` (meaning *all* capabilities are immature), dynamically switch to a fallback i18n template key (e.g., `p4_modernization_mandate_foundational`) that frames the highest score merely as the "least critical vulnerability" or "initial baseline," preventing false praise of non-existent infrastructure.

---

### PHASE 3: Open FAIR Mathematical Sanitization
**Objective:** Eliminate the double-counting of capital recovery and hardware replacement costs in the probabilistic risk quantification engine (Defect 3).

*   **Target Files:**
    *   `payload_to_ast.py` (Financial Risk Aggregator / AST Builder)
    *   *(Optional)* Upstream Risk Calculation Module if rate composition occurs prior to AST ingestion.
*   **Architectural Invariant to Enforce:**
    *   **The Mutually Exclusive Loss Taxonomy Invariant:** In accordance with the Open FAIR standard, Primary Loss (Productivity/Revenue loss per hour, $L_{prod}$) and Secondary/Response Loss (One-time Recovery/Replacement capital expenditure, $C_{rec}$) must remain strictly orthogonal. Hourly outage rates must represent *exclusively* operational burn; fixed asset replacement costs must be applied exclusively as a discrete scalar addition ($L_{total} = (T_{downtime} \times R_{hourly\_op}) + C_{rec}$).
*   **Surgical Remediation Strategy:**
    1.  **Deconstruct Rate Composition in `payload_to_ast.py`:** Audit the exact lineage of the variables feeding `total_p90_val`.
    2.  **Enforce Variable Orthogonality:**
        *   If the upstream hourly rate variable is a composite rate (i.e., $R_{composite} = R_{op} + \frac{C_{rec}}{T_{expected}}$), strip the discrete addition of emergency hardware replacement cost from the `total_p90_val` aggregation formula.
        *   *Preferred Clean-Room Architecture:* Redefine the hourly rate variable strictly as `hourly_operational_loss_rate` (excluding all CapEx/replacement costs). Compute the P90 downtime operational loss ($T_{P90} \times \text{hourly\_operational\_loss\_rate}$), and add the discrete `one_time_recovery_capex` ($C_{rec}$) *once* at the final summation boundary.
    3.  **Currency & Scale Agnosticism:** Ensure all mathematical operations operate on raw, unformatted floating-point scalars, deferring currency symbol injection and locale-specific number formatting strictly to the final AST presentation layer.

---

### PHASE 4: Ontological Guardrails for Infrastructure Synthesis
**Objective:** Prevent the LLM synthesis engine from hallucinating object storage protocols (S3) as valid backing stores for stateful container block/file Persistent Volume Claims (Defect 5).

*   **Target Files:**
    *   `universal_tower_synthesizer.py` (specifically the `UniversalTowerSynthesizer` class and its associated system prompt/directive registries).
*   **Architectural Invariant to Enforce:**
    *   **The Protocol-Workload Compatibility Invariant:** The synthesis engine must enforce strict OSI/Storage layer compatibility. Object Storage (REST/HTTP API via S3) and Block/File Storage (POSIX/iSCSI/NFS/NVMe-oF via CSI) are non-interchangeable architectural domains. Kubernetes native `PersistentVolumeClaims` (PVCs) for stateful workloads (databases, queues, general POSIX mounts) strictly require a Container Storage Interface (CSI) orchestrator binding to block or file primitives.
*   **Surgical Remediation Strategy:**
    1.  **Augment Sector/Domain Directives in `universal_tower_synthesizer.py`:**
        *   Inject a deterministic, vendor-agnostic **Storage Protocol Constraint Block** into the system directives governing Infrastructure, Storage, and Container Orchestration towers.
    2.  **Enforce Universal Technical Guardrails (Zero Vendor Hardcoding):**
        *   Instruct the synthesizer via strict negative constraints: *"NEVER recommend Object Storage (S3/Swift) as a direct backing store for standard Kubernetes PersistentVolumeClaims (PVCs) or POSIX-dependent stateful workloads."*
        *   Instruct the synthesizer via positive architectural mapping: *"When evaluating or recommending persistent storage for container orchestration (Kubernetes/OpenShift), you MUST mandate a compliant Container Storage Interface (CSI) driver (e.g., NetApp Astra Trident, Ceph CSI, or equivalent enterprise storage orchestrator) provisioning native Block (iSCSI/NVMe-oF/FC) or File (NFS/SMB) protocols. Object storage (S3) may only be cited for cloud-native application-level API consumption, backup targets, or log archival."*
    3.  **Technical English Enforcement:** Ensure these directives are written in unambiguous, canonical Technical English within the prompt registry, relying on the downstream localization layer to translate the resulting architectural synthesis into the client's target language.

---

## 3. Summary of Architectural Guarantees

| Defect ID | Root Cause | Remediated File(s) | Enforced Invariant | Universal Agnosticism Guarantee |
| :--- | :--- | :--- | :--- | :--- |
| **Defect 1** | Blind survey overwrite | `score_reconciler.py` | Empirical Supremacy | Evaluates mathematical delta ($\Delta$) between evidence and assertion; zero client/domain hardcoding. |
| **Defect 2** | Naive `max()` narrative praise | `payload_to_ast.py`, i18n | Narrative Floor ($\ge 2.60$) | Uses canonical maturity thresholds to select appropriate semantic framing dynamically. |
| **Defect 3** | Overlapping FAIR loss vectors | `payload_to_ast.py` | Mutually Exclusive Loss Taxonomy | Pure mathematical separation of OpEx burn rates and CapEx recovery scalars; currency-agnostic. |
| **Defect 4** | Split-brain CMMI intervals | `maturity_band.py`, `payload_to_ast.py` | Single Scale SSOT | Centralizes scale boundaries in one module; all sections render from the same programmatic array. |
| **Defect 5** | Missing storage protocol rules | `universal_tower_synthesizer.py` | Protocol-Workload Compatibility | Enforces industry-standard CSI/POSIX vs. S3/Object architectural truths; adapts to any vendor stack. |

---
*Awaiting authorization to proceed to code implementation phase.*