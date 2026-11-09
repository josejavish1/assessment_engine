---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
last_verified_against: 2026-11-08
applies_to:
- gemini
- audits
doc_type: operational
diataxis: reference
verification_mode: editorial
---

# EXECUTION PLAN: SECTION 3.1 ARCHITECTURAL TRANSFORMATION (TIER-1 SYNTHESIS ENGINE)

**Author:** `gemini-4-argon` (Principal Staff Enterprise Architect & AI Engineering Lead)  
**Target State:** Certified 10.0/10.0 McKinsey/Gartner Executive Output  
**Scope:** 10 IT Assessment Towers – Section 3.1 (Macroscopic Executive Synthesis & Transversal Patterns)  
**Governance:** Strict adherence to Language Decoupling, Universal Tenant Scalability, Algorithmic Integrity, and Domain Isolation.

---

## EXECUTIVE SUMMARY

The current 4.70/10 audit score in Section 3.1 is a symptom of a coupling anti-pattern: business logic, domain ontologies, and localized prose are intermingled within the Python compilation layer, leading to cross-tower contamination (e.g., Compute abstractions bleeding into FinOps and Storage) and generic boilerplate. 

To achieve a certified 10.0/10.0 standard without violating the **Zero Hardcoding** and **Language Decoupling** laws, we must shift from a *template-filling script* to a **Data-Driven Ontological Synthesis Engine**. The Python layer will act strictly as an agnostic Abstract Syntax Tree (AST) compiler, while domain intelligence, vertical-specific business impacts, and linguistic rendering are fully externalized into declarative JSON catalogs and resolved dynamically against the tenant's payload at runtime.

---

## PHASE 1: DATA ARCHITECTURE & CATALOGS
**Objective:** Decouple linguistic representation and domain ontology from the execution engine while maintaining zero client-specific hardcoding.

### 1.1. Schema Refactoring in `engine_config/locales.json`
We will eliminate monolithic boilerplate strings and introduce a parameterized, multi-dimensional localization schema under the `section_3_1` namespace.

*   **Macroscopic Synthesis Templates:** Indexed by `tower_id` and `maturity_tier` (`CRITICAL`, `STABILIZING`, `OPTIMIZED`). Uses strict Named Entity Placeholders (e.g., `{vertical_impact_metric}`, `{primary_tech_debt_vector}`, `{capex_opex_exposure}`) rather than hardcoded client strings.
*   **Transversal Pattern Catalogs:** Each of the 10 towers will have a dedicated sub-dictionary of structural patterns (e.g., `STORAGE_SILO_FRAGMENTATION`, `FINOPS_UNALLOCATED_SPEND`, `NETWORK_SPOF_TOPOLOGY`). This guarantees **100% domain isolation** and permanently prevents Compute text from bleeding into Storage or FinOps.
*   **Vertical Impact Lexicon:** A matrix mapping standard industry verticals (`MANUFACTURING`, `FINANCIAL_SERVICES`, `HEALTHCARE`, `RETAIL`, `GENERIC_ENTERPRISE`) to operational business impacts (e.g., mapping `MANUFACTURING` + `LATENCY_RISK` $\rightarrow$ *"physical logistics bottlenecks and plant floor disruption"* without ever mentioning a specific client name or localized plant).

### 1.2. Domain Ontology Configuration (`engine_config/domain_ontology.json`)
Create a new language-agnostic structural definition file that maps raw payload telemetry signals to abstract architectural patterns:
*   Defines the exact boundary between **Section 3.1 (Macroscopic/Transversal)** and **Section 3.2 (Granular Pillars)**.
*   Section 3.1 ontology rules will strictly aggregate cross-pillar metrics (e.g., systemic governance, architectural topology, lifecycle debt, financial efficiency) while explicitly excluding single-pillar point findings.

---

## PHASE 2: COMPILER ENGINE REFACTORING
**Objective:** Refactor the compilation pipeline (`payload_to_ast.py` and `in_memory_asis_compiler.py`) to operate in 100% Technical English with zero hardcoded literals, ensuring deterministic algorithmic integrity.

### 2.1. Purging and Refactoring `payload_to_ast.py`
*   **Lexical Sanitization:** Audit and strip all Spanish identifiers, comments, docstrings, regex patterns, and fallback literals. Enforce strict PEP-8 Technical English naming conventions (e.g., refactor legacy variables to `macro_synthesis_node`, `transversal_pattern_vectors`, `tenant_vertical_context`).
*   **Typed AST Node Construction:** Introduce immutable data structures (` dataclasses` or `Pydantic` models) for Section 3.1:
    *   `Section31MacroNode`: Holds normalized telemetry scores, dynamically extracted entity references (vendor-agnostic tags pulled from the payload), and the resolved vertical impact key.
    *   `TransversalPatternNode`: Represents a single structural pattern containing `pattern_id`, `severity_weight`, `evidence_metrics`, and `business_impact_vector`.
*   **Defensive Telemetry Parsing:** Implement safe navigation operators and mathematical guards (`safe_divide(numerator, denominator, default=0.0)`) when computing cross-pillar ratios to guarantee zero `ZeroDivisionError`, `KeyError`, or `IndexError` exceptions on sparse tenant payloads.

### 2.2. Refactoring `in_memory_asis_compiler.py`
*   **Removal of Cross-Tower Fallbacks:** Delete the legacy fallback logic that defaults to Compute strings when a tower lacks specific configuration. Replace it with a strict `TowerOntologyResolver` that binds exclusively to the active `tower_id`.
*   **Late-Stage Locale Binding:** The compiler will traverse the `Section31MacroNode` and `TransversalPatternNode` objects, resolving text exclusively via key lookups against `locales.json` using the tenant's target locale code (e.g., `es_ES`, `en_US`).
*   **Dynamic Token Interpolation:** Implement a safe string interpolation engine (`SafeLocaleFormatter(string.Formatter)`) that injects payload-derived facts (e.g., detected hypervisors, monitoring tools, or storage arrays present in the tenant's JSON payload) into the localized templates without hardcoding vendor names in `.py` files.

---

## PHASE 3: DYNAMIC CONTEXT EXTRACTION & PATTERN SYNTHESIS
**Objective:** Dynamically derive the macroscopic synthesis and exactly three (3) bespoke transversal patterns per tower from the tenant's payload without cannibalizing Section 3.2.

### 3.1. The 3-Pattern Deterministic Selection Algorithm
To guarantee **exactly 3 transversal patterns** per tower regardless of payload density:
1.  **Signal Aggregation (Cross-Pillar):** The engine evaluates the tenant's payload across all 5 pillars of a given tower, extracting normalized deficit vectors:
    *   *Vector A: Architectural & Topological Debt* (Sprawl, fragmentation, legacy protocols).
    *   *Vector B: Operational & Observability Blindness* (Reactive management, lack of automation/telemetry).
    *   *Vector C: Financial & Lifecycle Exposure* (CapEx/OpEx inefficiency, EoL/EoS hardware/software risk, compliance exposure).
2.  **Scoring & Ranking:** Candidate patterns defined in `domain_ontology.json` for that specific tower are scored using a weighted affinity formula based on the tenant's payload metrics and findings.
3.  **Deterministic Padding (Sparse Payload Guard):** If a tenant payload is sparse and yields fewer than 3 high-severity dynamic patterns, the algorithm deterministically pads the selection to exactly 3 using the tower's baseline structural patterns calibrated to the tenant's overall maturity score. This guarantees `len(patterns) == 3` as an absolute invariant.

### 3.2. Dynamic Business Impact Mapping (Tenant-Agnostic)
Instead of hardcoding operational narratives (like truck queues or specific ERP failures), the engine executes a two-step resolution:
1.  **Entity & Metric Extraction:** Extracts the tenant's declared `industry_vertical`, `revenue_band`, and `critical_workloads` directly from the payload metadata, alongside tower-specific KPIs (e.g., RPO/RTO gaps in Data Protection, orphan volume percentages in Storage, unallocated cloud tags in FinOps).
2.  **Ontological Synthesis:** Cross-references the tower's active pattern with the `Vertical Impact Lexicon` in `locales.json` to synthesize how that technical deficit translates into executive risk (CapEx bloat, EBITDA erosion, SLA penalties, or operational throughput degradation).

### 3.3. Anti-Cannibalization Firewall (Section 3.1 vs. Section 3.2)
*   **Section 3.1 (The "Why" and "Macro-How"):** Restricted to systemic, cross-cutting root causes (e.g., *"Decoupling between capacity planning and financial governance driving structural over-provisioning"*).
*   **Section 3.2 (The "What" and "Where"):** Retains granular, pillar-specific telemetry and component-level audits. The AST builder will flag and strip any granular metric key used in detail in 3.2 from being repeated verbatim in 3.1, utilizing rolled-up composite indices instead.

---

## PHASE 4: QUALITY ASSURANCE & ARCHITECTURAL INVARIANTS
**Objective:** Enforce non-negotiable laws via automated CI/CD gates and property-based testing.

### 4.1. Static Analysis & Lexical Gates (`tests/test_architectural_laws.py`)
1.  **Zero-Spanish AST/Regex Gate:** A pytest suite that parses all `.py` files using Python's `ast` and `tokenize` modules, scanning identifiers, docstrings, comments, and string literals against a Spanish dictionary and diacritic regex (`/[áéíóúñü¿¡]/i`). Any match triggers an immediate build failure.
2.  **Zero-Hardcoding Gate (Forbidden Token Scanner):** Scans the entire codebase and `locales.json` schema keys/templates for forbidden tenant or vendor literals (e.g., specific client names, hardcoded hardware models, or legacy assessment artifacts).

### 4.2. Functional & Ontological Invariant Tests (`tests/test_section_3_1_compiler.py`)
1.  **Cross-Tower Contamination Test:** Compiles Section 3.1 across all 10 towers using a synthetic payload and runs Cosine Similarity / Jaccard Index checks across the generated outputs. Asserts that domain-specific lexicon leakage between towers (e.g., Compute terminology in FinOps or Storage) is `0.0%`.
2.  **Cardinality Invariant Test:** Asserts that for all 10 towers, across 100+ randomized payload permutations, the compiled AST for Section 3.1 contains **exactly 1** Macroscopic Synthesis block and **exactly 3** Transversal Structural Patterns (`assert len(node.transversal_patterns) == 3`).
3.  **Chaos & Boundary Testing (Algorithmic Integrity):** Feeds malformed, empty (`{}`), zero-valued, and extreme-scale ($20M SME vs. $500B Global Bank) payloads into `payload_to_ast.py` and `in_memory_asis_compiler.py`. Asserts zero unhandled exceptions and 100% schema-compliant output generation.
4.  **Locale Parity Test:** Validates that every key path accessed by the compiler exists symmetrically across all supported target languages in `engine_config/locales.json` with identical `{placeholder}` signatures.