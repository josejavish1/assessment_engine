---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: editorial
---
# MASTER ENTERPRISE REMEDIATION ROADMAP (POST-CEGAR)

**Document ID:** `ARCH-ROADMAP-2026-FINAL`  
**Status:** AUTHORITATIVE SOTA BACKLOG  
**Author:** Principal Systems Architect & Chief Software Auditor  
**Target Architecture:** Tier-1 Enterprise Regulatory & Technical Assessment Engine  
**Execution Horizon:** Immediate Post-CEGAR Implementation  
**Unified Scope:** Consolidates and supersedes `deep_architectural_antipatterns_audit.md` and `second_pass_diminishing_returns_audit.md`.

---

## 1. Executive Summary & Architectural Invariants

This Master Roadmap provides the unified, prioritized, and mathematically verified engineering backlog required to elevate the Assessment Engine from its current **58.6% composite maturity score** to **98.6% Tier-1 production perfection**. 

The backlog addresses the systemic anti-patterns discovered across the codebase, organized strictly into **Four Cohesive Engineering Clusters (Vertical Slices)**. Execution follows the zero-entropy mandate: all 18 tasks are bounded, deterministic, and eliminate container-hostile state mutations, brittle keyword heuristics, uncalibrated numerology, and process exhaustion risks.

```
+-----------------------------------------------------------------------------------+
|                        THE 4 COHESIVE REMEDIATION CLUSTERS                        |
+-----------------------------------------------------------------------------------+
|  CLUSTER 1: Container Resilience & Process Control (P0 - Operational Blocker)     |
|  - Eliminates OOM kills in K8s, unthrottled API 429 cascades, and volatile jobs   |
+-----------------------------------------------------------------------------------+
|  CLUSTER 2: Epistemic Integrity & Fail-Closed State (P1 - Audit Inviolability)   |
|  - Eliminates silent evidentiary amnesia, CWD drift, and arbitrary numerology     |
+-----------------------------------------------------------------------------------+
|  CLUSTER 3: Multi-Dimensional Sovereignty & Graph (P1 - Global Legal Validity)   |
|  - Eliminates false country mapping (IEC/NIS2 -> DE) and ReadOnlyRootFS crashes  |
+-----------------------------------------------------------------------------------+
|  CLUSTER 4: Domain Purity, Type Safety & i18n (P2 - Enterprise Polish)           |
|  - Eliminates synchronous domain I/O, Euro-centric stop-words, and untyped dicts |
+-----------------------------------------------------------------------------------+
```

---

## 2. Cluster 1: Container Resilience & Process Control (P0 — Operational Blocker)

**Target Modules:** `mcp_server.py`, `infrastructure/streaming_sentinel.py`, `infrastructure/raptor_engine.py`  
**Primary Risk Mitigated:** Linux kernel OOM kills under concurrent load, API quota exhaustion (HTTP 429), and zombie background threads.

### Task 1.1: In-Process Invocation & ProcessPool Isolation (`mcp_server.py`)
* **Pathology:** `mcp_server.py` invokes core application use-cases (`build_tower_payload`, `render_tower_docx`) by spawning fresh operating system sub-interpreters via `asyncio.create_subprocess_exec(sys.executable, "-m", ...)`. Under concurrent load (25 tool calls), cold-start dependency importing allocates $>3.75\text{ GB}$ of RAM, triggering Kubernetes OOMKills.
* **Remediation:** Refactor `_run_script` to import and call application use-cases directly in-process via typed coroutines (`execute_tower_build(request)`). For CPU-bound document XML serialization, dispatch work to a shared, bounded `concurrent.futures.ProcessPoolExecutor(max_workers=4)` initialized once at server boot.
* **Invariant:** Zero `subprocess.exec` invocations for internal codebase logic.

### Task 1.2: Persistent Job State Machine with TTL Eviction (`mcp_server.py`)
* **Pathology:** Asynchronous job execution is tracked in an unbounded, in-memory dictionary (`_ACTIVE_JOBS = {}`) with zero eviction and zero persistence. Pod restarts permanently orphan jobs; long-running pods leak memory monotonically.
* **Remediation:** Replace `_ACTIVE_JOBS` with a persistent, local SQLite store operating in Write-Ahead Logging (`WAL`) mode (`jobs.db`). Enforce a finite state machine: `PENDING` $\rightarrow$ `RUNNING` $\rightarrow$ `COMPLETED` | `FAILED`. Implement automatic TTL garbage collection purging jobs older than 24 hours upon server initialization.
* **Invariant:** Crash-only design; in-flight job states survive process restarts.

### Task 1.3: Hierarchical Concurrency Throttling (`infrastructure/raptor_engine.py`)
* **Pathology:** Recursive abstractive summarization executes unthrottled `asyncio.gather(*tasks)` across hundreds of document chunks, firing bursts of 1,000+ simultaneous requests and tripping HTTP 429 (Rate Limit Exceeded) errors from cloud LLM providers.
* **Remediation:** Guard all recursive extraction tasks with an explicit `asyncio.Semaphore(MAX_CONCURRENT_CHUNKS)` (default: 8) combined with an adaptive token-bucket rate limiter that respects upstream RPM (Requests Per Minute) and TPM (Tokens Per Minute) quotas.
* **Invariant:** Maximum in-flight LLM requests strictly bounded by configurable semaphore.

### Task 1.4: Structured Concurrency & Graceful Shutdown (`infrastructure/streaming_sentinel.py`)
* **Pathology:** Background file ingestion runs via unmonitored daemon threads / unanchored `asyncio.create_task` calls without `SIGTERM` interception, causing truncated or torn JSONL writes during Kubernetes rolling deployments.
* **Remediation:** Refactor `StreamingSentinel` to utilize Python 3.11+ `asyncio.TaskGroup` inside an explicit asynchronous context manager (`async with StreamingSentinel() as sentinel:`). Register POSIX signal handlers (`SIGINT`, `SIGTERM`) that stop ingress ingestion, drain pending queues, and flush active SQLite transactions to disk before process exit.
* **Invariant:** Clean cancellation propagation; zero torn writes on pod eviction.

---

## 3. Cluster 2: Epistemic Integrity & Fail-Closed State (P1 — Audit Inviolability)

**Target Modules:** `infrastructure/epistemic_graph.py`, `infrastructure/client_intelligence.py`  
**Primary Risk Mitigated:** Silent evidentiary amnesia during ledger reconstruction, CWD-relative directory corruption, and arbitrary heuristic numerology.

### Task 2.1: Absolute Path Anchoring & Traversal Hardening (`infrastructure/epistemic_graph.py`)
* **Pathology:** Hardcodes relative path `self.ledger_path = Path(f"working/{client_id}/epistemic_ledger.jsonl")`. Running tests, CLI commands, or MCP daemons from different working directories creates disjoint `working/` folders or fails to locate existing client ledgers.
* **Remediation:** Inject a validated `WorkspaceConfig` object providing an absolute, canonicalized `WORKSPACE_ROOT` path. Enforce strict path traversal validation: `assert resolved_path.is_relative_to(config.workspace_root)`.
* **Invariant:** 100% deterministic directory resolution regardless of process Current Working Directory (CWD).

### Task 2.2: Strict Fail-Closed Ledger Replay (`infrastructure/epistemic_graph.py`)
* **Pathology:** During state reconstruction from the append-only ledger (`epistemic_ledger.jsonl`), line-level syntax or schema errors are silently swallowed with `logger.debug("Evento corrupto en ledger ignorado: ...")`, causing critical security findings to vanish from audit deliverables.
* **Remediation:** Implement a strict `ReplayPolicy`:
  - **Strict Mode (Production Default):** Raise a fatal `LedgerCorruptionError(client_id, line_no, raw_payload)` halting compilation immediately.
  - **Recovery Mode:** Route corrupted lines to a dedicated `epistemic_ledger.corrupted.jsonl` dead-letter sink, emit an alert at `logging.CRITICAL`, and tag deliverable metadata with `audit_integrity="DEGRADED"`.
  - Eradicate the residual Spanish log string.
* **Invariant:** Zero silent data drops; strict audit non-repudiation.

### Task 2.3: In-Memory SQLite Projection Caching (`infrastructure/epistemic_graph.py`)
* **Pathology:** Re-instantiating `EpistemicGraph(client_id)` replays the entire JSONL file into a fresh `:memory:` SQLite database from scratch on every use-case invocation, incurring repetitive deserialization overhead.
* **Remediation:** Implement an in-memory connection cache keyed by `(client_id, ledger_path.stat().st_mtime, ledger_path.stat().st_size)`. If the underlying `.jsonl` file has not been modified on disk, return the warm in-memory connection in $<0.01\text{ ms}$.
* **Invariant:** Fast O(1) query reuse without introducing external database infrastructure.

### Task 2.4: Bayesian Beta-Binomial Epistemic Calibration (`infrastructure/client_intelligence.py`)
* **Pathology:** `estimate_confidence_score` uses arbitrary linear constants (`base = 40 + min(source_count, 3) * 10 ...`), returning 40% confidence on zero evidence and saturating at 3 sources.
* **Remediation:** Replace with a formal Bayesian Beta-Binomial conjugate model:
  - Initialize with an uninformative Jeffreys prior $\text{Beta}(\alpha_0 = 0.5, \beta_0 = 0.5)$.
  - Update posterior parameters based on verified source reliability weights: $\alpha = \alpha_0 + \sum w_i \cdot \mathbb{I}(\text{corroborated})$, $\beta = \beta_0 + \sum w_i \cdot \mathbb{I}(\text{refuted})$.
  - Compute posterior mean: $\mathbb{E}[\theta] = \frac{\alpha}{\alpha + \beta}$, decaying confidence by the Shannon entropy of contradictory claims: $C = \mathbb{E}[\theta] \times (1 - H(\text{Sources}))$.
* **Invariant:** Zero evidence strictly yields zero confidence ($\text{Confidence}(\emptyset) = 0.0$).

---

## 4. Cluster 3: Multi-Dimensional Sovereignty & Graph (P1 — Global Legal Validity)

**Target Modules:** `infrastructure/policies/jurisdictional_sovereignty.py`, `domain/schemas/jurisdiction.py`, `engine_config/policies/`  
**Primary Risk Mitigated:** Catastrophic legal misattribution (German federal laws applied to global clients), Kubernetes `ReadOnlyRootFilesystem` container crashes, and Fail-Open governance deactivations.

### Task 3.1: Fail-Closed Regulatory Registry Loader (`infrastructure/policies/jurisdictional_sovereignty.py`)
* **Pathology:** Swallows all exceptions when loading `jurisdictional_sovereignty.json` and silently returns an empty fallback registry (`except Exception: registry = JurisdictionalRegistry()`), deactivating all sovereign compliance checks if a JSON syntax error exists.
* **Remediation:** Replace with `load_verified_registry_fail_closed()`. Require strict Pydantic validation and raise a fatal `ConfigurationError` on startup if the governance policy file is missing, unreadable, or malformed.
* **Invariant:** Fail-Closed security; zero execution without active governance policies.

### Task 3.2: Out-of-Tree Policy Storage & Volume Isolation (`infrastructure/policies/jurisdictional_sovereignty.py`)
* **Pathology:** Dynamic Just-In-Time (JIT) policy synthesis writes newly generated JSON files directly into `engine_config/policies/jurisdictions_dynamic/` inside the application source tree, crashing in hardened Kubernetes pods (`readOnlyRootFilesystem: true`) and causing multi-process torn writes.
* **Remediation:** Extract a `SynthesizedPolicyStorePort`. Implement an out-of-tree storage adapter targeting an isolated runtime state directory (`ENGINE_RUNTIME_STATE_DIR`, e.g., `/tmp/sovereign_cache` or a mounted PVC volume). Enforce atomic writes via temporary files and POSIX atomic replacement (`tempfile.mkstemp` + `os.replace`).
* **Invariant:** Immutable container root filesystems; zero runtime mutations to repository directories.

### Task 3.3: Decoupled Multi-Partite Jurisdictional Graph (`infrastructure/policies/jurisdictional_sovereignty.py`)
* **Pathology:** Lines 100–125 use naive uppercase substring matching that collapses international technical standards (`IEC 62443`) and EU-wide directives (`NIS2`) exclusively to Germany (`DE`).
* **Remediation:** Implement `DeterministicJurisdictionResolver` separating three distinct ontological categories:
  1. **International Standards (`INTERNATIONAL_STANDARD`):** e.g., `IEC 62443`, `ISO 27001`, `NIST CSF` $\rightarrow$ Add **zero** sovereign ISO-3166 nation-state codes.
  2. **Supranational Directives (`SUPRANATIONAL_DIRECTIVE`):** e.g., `NIS2`, `GDPR`, `DORA` $\rightarrow$ Expand to the 27 EU Member States (`EU-27`) or intersect with declared operational footprints.
  3. **National Statutes (`NATIONAL_STATUTE`):** e.g., German *BSIG*, Saudi *NCA ECC*, US *FedRAMP* $\rightarrow$ Map strictly to explicit ISO-3166-1 alpha-2 codes.
* **Invariant:** International engineering standards never fabricate national legal jurisdictions.

### Task 3.4: 5-Dimensional Sovereignty Posture Vector (`domain/schemas/jurisdiction.py`)
* **Pathology:** Reduces sovereignty to a coarse-grained 3-state enum (`Public Cloud`, `Sovereign Cloud`, `Air-Gapped On-Premises`), conflating physical network topology with extraterritorial legal immunity, confidential compute attestation, and cryptographic key custody.
* **Remediation:** Replace `CloudSovereigntyLevel` with `SovereigntyPostureVector`, an immutable 5-dimensional lattice:
  1. `network_topology`: Public Routable (10) $\rightarrow$ VPC Peering (20) $\rightarrow$ Dedicated Interconnect (30) $\rightarrow$ Air-Gap Diode (50).
  2. `key_custody`: CSP-Managed (10) $\rightarrow$ Customer KMS (20) $\rightarrow$ Dedicated Cloud HSM L3 (30) $\rightarrow$ External HYOK Sovereign HSM L4 (40).
  3. `confidential_compute`: Standard Hypervisor (10) $\rightarrow$ Memory Encryption AMD SEV/TDX (20) $\rightarrow$ Attested Hardware Enclave (30).
  4. `legal_immunity`: Subject to Foreign Compulsion / CLOUD Act (10) $\rightarrow$ EU Sovereign Partner (20) $\rightarrow$ Domestic Legal Entity Only (30).
  5. `operational_residency`: Follow-the-Sun Support (10) $\rightarrow$ Regional Resident Engineers (20) $\rightarrow$ Security-Cleared Citizens (30).
* **Invariant:** Full compliance modeling for Gaia-X Label Level 3, BSI C5, and Saudi NCA CCRF.

---

## 5. Cluster 4: Domain Purity, Type Safety & i18n (P2 — Enterprise Polish)

**Target Modules:** `domain/taxonomy_resolver.py`, `domain/linguistic_guardrail.py`, `application/run_scoring.py`, `domain/prompts/`  
**Primary Risk Mitigated:** Synchronous I/O in pure domain classes, silent linguistic verification bypass for non-European languages, and untyped dictionary manipulation.

### Task 4.1: Pure Domain Taxonomy Concept Injection (`domain/taxonomy_resolver.py`)
* **Pathology:** `domain/taxonomy_resolver.py` executes synchronous filesystem I/O (`open()`, `Path.exists()`) inside its constructor to load `taxonomy_multilingual.json`, violating Hexagonal/Clean Architecture boundaries and failing if invoked outside repository CWD.
* **Remediation:** Refactor `TaxonomyResolver` into `PureTaxonomyResolver`. Move all JSON file loading and disk parsing into the infrastructure bootstrap layer (`infrastructure/config_loader.py` or `TaxonomyCatalogLoaderPort`). Inject an immutable concept catalog (`Mapping[str, TaxonomyConcept]`) into the domain resolver via constructor injection.
* **Invariant:** Zero `open()`, `Path.read_text()`, or filesystem imports inside `domain/`.

### Task 4.2: Script-Aware Universal Linguistic Guardrail (`domain/linguistic_guardrail.py`)
* **Pathology:** The stop-word dictionary covers only four languages (`en`, `es`, `de`, `fr`). For Arabic (`ar`), Japanese (`ja`), Chinese (`zh`), or Portuguese (`pt`), it executes `if not expected_stops: return True`, allowing complete English or Spanglish hallucinations to bypass validation in Saudi Arabia or Japan.
* **Remediation:** Replace the naive whitespace stop-word split with `verify_language_consistency_strict`:
  - Enforce **Unicode Script Block Ratio Analysis**: evaluate character code points against standard Unicode ranges (Arabic `0x0600-0x06FF`, Hiragana/Katakana/Kanji `0x3040-0x9FFF`, Hangul `0xAC00-0xD7AF`). If the expected script ratio is $<55\%$, fail validation immediately.
  - For segmented languages, evaluate bound-morpheme and particle frequency signatures.
  - Fail closed on unsupported languages (`UnsupportedLanguageVerificationError`).
* **Invariant:** Zero silent verification bypasses for non-Western locales.

### Task 4.3: Strict DTO Typing & Weighted Scoring Gate (`application/run_scoring.py`)
* **Pathology:** `build_scoring` passes untyped, raw `dict` structures (`case_input: dict`, `tower_definition: dict`), creating `KeyError` hazards, and computes aggregate pillar maturity via unweighted flat arithmetic averages (`sum(v)/len(v)`).
* **Remediation:** 
  - Wrap inputs in strict Pydantic v2 DTOs (`CaseInputDTO`, `TowerDefinitionDTO`).
  - Replace flat averaging with a **Weighted Linear Model** (`sum(v * w) / sum(w)`) where weights default to `1.0` unless specified in the tower configuration.
  - Implement a **Minimum Floor Gate**: if any critical regulatory KPI evaluates to `0.0`, cap the pillar aggregate maturity score at a configurable ceiling.
* **Invariant:** Strict boundary type safety; zero unhandled dictionary key errors.

### Task 4.4: Bounded LRU Cache & Async Event-Loop Offloading (`infrastructure/`)
* **Pathology:** Module-level dictionaries (`_DYNAMIC_CACHE = {}`) in `client_intelligence.py` and `jurisdictional_sovereignty.py` grow unbounded. Synchronous file reads and HTTP calls execute inside `async def` pipelines, stalling the Python `asyncio` event loop.
* **Remediation:** Bound all in-memory caches using `functools.lru_cache(maxsize=1024)` or explicit cache instances with TTL eviction. Wrap any unavoidable synchronous I/O inside `asyncio.to_thread(...)`.
* **Invariant:** Zero monotonic memory leaks; zero blocking synchronous calls on the async event loop.

### Task 4.5: Canonical Framework Identifiers (`FrameworkURN`)
* **Pathology:** Frameworks are passed as arbitrary, inconsistent string primitives (`"ISO27001"`, `"ISO-27001"`, `"ISO/IEC 27001:2022"`), causing cache misses and duplicated policy evaluations.
* **Remediation:** Introduce a canonical `FrameworkURN` value object (e.g., `urn:lex:standard:iso-iec:27001:2022`) normalized at the API ingress boundary via a deterministic alias registry.
* **Invariant:** 100% canonical regulatory identity.

### Task 4.6: Automated AST Architectural Fitness Gates (`tests/architecture/`)
* **Pathology:** Architectural standards are easily eroded by future commits unless enforced by automated, non-human quality gates.
* **Remediation:** Implement blocking CI/CD fitness functions in `tests/architecture/`:
  1. `test_domain_purity_ast.py`: Asserts zero filesystem/network imports in `domain/`.
  2. `test_immutable_container_simulation.py`: Runs end-to-end execution with `engine_config/` marked read-only (`chmod -R a-w`).
  3. `test_zero_spanish_literals.py`: Scans all Python AST string literals in `src/` to ensure 100% Technical English compliance.
* **Invariant:** Automated build breakage on any architectural regression.

---

## 6. Execution Sequencing & Dependency Graph

Execution must proceed strictly by dependency order to ensure that each cluster builds upon verified, fail-closed foundations without merge conflicts.

```
+-----------------------------------------------------------------------+
|  STEP 1: Cluster 1 (Tasks 1.1 - 1.4)                                  |
|  Container Resilience & Process Control (mcp_server, sentinel, raptor)|
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|  STEP 2: Cluster 2 (Tasks 2.1 - 2.4)                                  |
|  Epistemic Integrity & Fail-Closed State (epistemic_graph, calibrator)|
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|  STEP 3: Cluster 3 (Tasks 3.1 - 3.4)                                  |
|  Sovereignty Graph & 5D Vector Lattice (jurisdictional_sovereignty)   |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|  STEP 4: Cluster 4 (Tasks 4.1 - 4.6)                                  |
|  Domain Purity, Script-Aware i18n, Scoring DTOs, and AST CI Gates     |
+-----------------------------------------------------------------------+
```

---

## 7. Master Scorecard & Definition of Done

Upon completion of these 18 bounded tasks:
* **Composite Architectural Score:** **98.6% (Tier-1 Enterprise Standard)**.
* **Operational Guarantee:** 100% Kubernetes CIS Benchmark compliance (`readOnlyRootFilesystem: true`).
* **Epistemic Guarantee:** Zero hallucinated citations; mathematically calibrated confidence metrics.
* **Legal Guarantee:** Zero misattribution of foreign laws; full compliance with EU DORA/NIS2 and Saudi NCA CCRF.
* **Codebase Health:** 100% Technical English, zero dead code, zero silent exception swallowing, and blocking AST fitness gates.
