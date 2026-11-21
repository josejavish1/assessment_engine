---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/application
- src/assessment_engine/infrastructure
- src/assessment_engine/adapters/compilers
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: End-to-end technical specification of the assessment factory execution flow.
---
# Assessment Factory Flow Specification

Canonical execution specification defining the end-to-end data pipeline of the `assessment-engine` platform, from multi-modal customer evidence ingestion to compiled OpenXML `.docx` deliverables.

---

## 1. End-to-End Pipeline DAG

The following flowchart captures the six sequential execution phases across deterministic Python compute and bounded LLM synthesis:

```mermaid
flowchart TD
    %% --- PHASE 0 ---
    subgraph PHASE_0 ["Phase 0: Multi-Modal Ingestion"]
        direction TB
        IN_DOCX([".docx Customer Context"])
        IN_TXT([".txt Questionnaire Responses"])
        IN_CONFIG(["engine_config/ (Ontologies & Scales)"])

        P0_1["0.1 EvidenceEngine (evidence_engine.py)"]
        P0_1_A["Block-level Parser (Headings H1-H3)"]
        P0_1_B["Content-Addressable SHA-256 Hashing"]
        VAULT[("evidence_vault.json<br/>(L0 Atomic Fragments)")]

        P0_2["0.2 RaptorEngine (raptor_engine.py)"]
        P0_2_A["Semantic Clustering"]
        P0_2_B["Recursive Abstractive Summarization"]
        TREE[("raptor_tree.json<br/>(Hierarchical Knowledge Tree)")]

        IN_DOCX --> P0_1 --> P0_1_A --> P0_1_B --> VAULT
        VAULT --> P0_2 --> P0_2_A --> P0_2_B --> TREE
    end

    %% --- PHASE 1 ---
    subgraph PHASE_1 ["Phase 1: Upstream Context Harvesting"]
        direction TB
        P1_1["1.1 run_intelligence_harvesting.py"]
        P1_1_A["Enterprise Profile Extractor"]
        P1_1_B["Executive Agenda Grounding"]
        INTEL[("client_intelligence.json<br/>(Client DNA Profile)")]

        TREE & VAULT & IN_CONFIG --> P1_1 --> P1_1_A & P1_1_B --> INTEL
    end

    %% --- PHASE 2 ---
    subgraph PHASE_2 ["Phase 2: Single-Tower Technical Analysis"]
        direction TB
        P2_1["2.1 build_case_input.py"]
        P2_2["2.2 run_scoring.py (CMMI Maturity)"]
        P2_3["2.3 run_evidence_analyst.py"]
        FINDINGS[("findings.json<br/>(Grounded Findings)")]

        P2_4["2.4 run_tower_blueprint_engine.py"]
        BLUEPRINT[("blueprint_Txx_payload.json<br/>(Tower Single Source of Truth)")]

        INTEL & IN_TXT & IN_CONFIG --> P2_1 --> P2_2 --> P2_3 --> FINDINGS
        FINDINGS & INTEL --> P2_4 --> BLUEPRINT
    end

    %% --- PHASE 3 ---
    subgraph PHASE_3 ["Phase 3: Actuarial Risk & Loss Modeling"]
        direction TB
        P3_1["3.1 Bayesian FAIR Copula Engine"]
        P3_1_A["Gamma-Poisson Threat Calibration"]
        P3_1_B["Beta-Binomial Vulnerability Conjugation"]
        P3_2["3.2 Euler Risk Allocator"]
        ACTUARIAL[("actuarial_profile.json<br/>(TCO & FAIR Monte Carlo Loss)")]

        BLUEPRINT & IN_CONFIG --> P3_1 --> P3_1_A & P3_1_B --> P3_2 --> ACTUARIAL
    end

    %% --- PHASE 4 ---
    subgraph PHASE_4 ["Phase 4: Epistemic Graph & Strategy Resolution"]
        direction TB
        P4_1["4.1 Epistemic Graph Sync (epistemic_graph.py)"]
        P4_1_A["Subject-Predicate-Object Triplet Extraction"]
        P4_2["4.2 Cross-Tower Nexus & Topological Sort"]
        P4_2_A["Wait-For Dependency Graph"]
        P4_2_B["Wave Allocation (H1, H2, H3)"]
        GRAPH[("epistemic_graph.db<br/>(SQLite Event Store)")]

        BLUEPRINT & ACTUARIAL --> P4_1 --> P4_1_A --> GRAPH
        GRAPH --> P4_2 --> P4_2_A & P4_2_B
    end

    %% --- PHASE 5 ---
    subgraph PHASE_5 ["Phase 5: AST Compilation & Deliverable Generation"]
        direction TB
        P5_1["5.1 payload_to_ast.py (AST Transformation)"]
        P5_2["5.2 docx_compiler.py (OpenXML Primitive Assembly)"]
        P5_3["5.3 TomoAsisAstCompiler (Global Consolidation)"]
        
        DOC_ANNEX([".docx Tower Annexes"])
        DOC_BLUEPRINT([".docx Tower Blueprints"])
        DOC_GLOBAL([".docx Tomo 1 Consolidado"])
        DOC_COMMERCIAL([".docx Account Action Plan"])

        BLUEPRINT & ACTUARIAL --> P5_1 --> P5_2 --> DOC_ANNEX & DOC_BLUEPRINT
        P5_3 --> DOC_GLOBAL & DOC_COMMERCIAL
    end

    style VAULT fill:#1e293b,stroke:#38bdf8,stroke-width:1px,color:#f8fafc
    style TREE fill:#1e293b,stroke:#38bdf8,stroke-width:1px,color:#f8fafc
    style INTEL fill:#1e293b,stroke:#a855f7,stroke-width:1px,color:#f8fafc
    style BLUEPRINT fill:#1e293b,stroke:#f97316,stroke-width:2px,color:#f8fafc
    style ACTUARIAL fill:#1e293b,stroke:#22c55e,stroke-width:1px,color:#f8fafc
    style GRAPH fill:#1e293b,stroke:#eab308,stroke-width:1px,color:#f8fafc
```

---

## 2. Core Execution Mechanisms

### 2.1 Multi-Modal Ingestion (`EvidenceEngine` & `RaptorEngine`)
- **Deterministic Chunking (`EvidenceEngine`):** Decomposes raw `.docx` and `.txt` files into content-addressable `EvidenceFragment` records indexed by deterministic SHA-256 hashes. Headings ($H1$ to $H3$) are tracked across paragraphs to preserve semantic context.
- **Hierarchical Clustering (`RaptorEngine`):** Constructs a recursive tree (`raptor_tree.json`). Leaf fragments are grouped by semantic proximity and summarized via bounded LLM invocations across levels ($L_1, L_2$) with rate-limiting backoff.

### 2.2 Grounded Single-Tower Synthesis (`run_tower_blueprint_engine.py`)
- **Pillar-Aligned Evaluation:** Maps customer questionnaire scores and evidence fragments against tower-specific pillars.
- **Contract-First Synthesis:** Synthesizes `blueprint_<tower>_payload.json` validating strictly against `src/assessment_engine/domain/schemas/blueprint.py`.
- **Definition of Done (DoD):** Blueprints require quantitative maturity scores (1.0 to 5.0), explicit gap analyses, and sized remediation initiatives ($S, M, L, XL$).

### 2.3 Actuarial Risk Modeling (`bayesian_fair_copula_engine.py`)
- **Dual Engine:** Couples Total Cost of Ownership (TCO) with Factor Analysis of Information Risk (FAIR).
- **Bayesian Updating:** Evaluates Loss Event Frequency (LEF) and Vulnerability (VULN) using Gamma-Poisson and Beta-Binomial conjugate distributions conditioned on empirical evidence in `evidence_ledger.json`.
- **Euler Capital Allocation:** Allocates portfolio-level Value at Risk (VaR) across technology towers based on marginal risk contributions.

### 2.4 Epistemic Graph Sync (`epistemic_graph.py`)
- **Semantic Triplets:** Ingests findings and initiatives into an SQLite event-sourcing graph as formal relational assertions:
  $$\langle \text{Project ID} \rangle \xrightarrow{\text{REQUIRES}} \langle \text{Dependency ID} \rangle$$
  $$\langle \text{Risk ID} \rangle \xrightarrow{\text{IMPACTS}} \langle \text{Pillar ID} \rangle$$
- **Topological Sorting:** Resolves the dependency DAG to assign transformation initiatives into non-conflicting delivery waves ($H_1, H_2, H_3$).

### 2.5 AST Presentation Compilation (`docx_compiler.py`)
- **Exclusive DOCX Monism:** Compiles structured JSON payloads into Microsoft Word (`.docx`) through intermediate Abstract Syntax Trees (AST).
- **Separation of Concerns:** Compilers (`payload_to_ast.py`, `docx_compiler.py`, `tomo_asis_ast_compiler.py`) only format and layout pre-calculated metrics. Recalculation or mutation of domain data in presentation logic is prohibited.
