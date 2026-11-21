---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/policy_engine.py
- engine_config/policies
- tests/integration/test_policy_engine.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
notes: Technical specification of the Sovereign Policy Engine interceptor and the 8 registered compiler policies.
---
# Sovereign Policy Engine Architecture

Canonical specification defining the architecture, compilation lifecycle, deterministic invariant checks, and registered policy passes of `SovereignPolicyEngine` (`src/assessment_engine/infrastructure/policy_engine.py`).

---

## 1. Interception Pattern: Single-Pass Deterministic Policy Compiler

`SovereignPolicyEngine` operates as a deterministic post-synthesis interceptor within the single-tower evaluation pipeline (`run_tower_blueprint_engine.py`). It ingests raw LLM-synthesized blueprint JSON, executes a sequential chain of 8 registered policy passes, and produces a sanitized, compliant blueprint payload prior to OpenXML AST compilation:

```
[ Raw LLM Blueprint Payload ]
             |
             v
+---------------------------------------------------------------------------------------+
| SOVEREIGN POLICY ENGINE COMPILER (policy_engine.py)                                   |
| Intercepts payload and executes the 8 registered policy passes in sequential order:   |
|                                                                                       |
| 1. ClientSanitizationPolicy       --> Deep unescape & confidential scrubbing          |
| 2. FairRiskPolicy                 --> Dual TCO + FAIR Monte Carlo Bayesian modeling   |
| 3. DeduplicationPolicy            --> Consolidates cross-pillar project redundancy     |
| 4. SequencingPolicy               --> Enforces chronological dependency waves (H1-H3) |
| 5. OTPerimeterPolicy              --> Mandates hardware data diodes for SCADA/OT       |
| 6. ArchiMateDeliverablesPolicy    --> Validates ArchiMate structural taxonomy         |
| 7. BusinessCaseGroundingPolicy    --> Bounds financial sizing to corporate tiers      |
| 8. ReverseTraceabilityPolicy      --> Enforces mandatory L0 evidence fragment lineage |
+---------------------------------------------------------------------------------------+
             |
             v
[ Sanitized Blueprint SSOT: blueprint_<tower>_payload.json ]
             |
             v
[ OpenXML AST Compilers: payload_to_ast.py + docx_compiler.py ]
```

---

## 2. Registered Policy Specifications (`POLICY_REGISTRY`)

The compiler executes eight immutable policy passes:

| Pass | Policy Class | Invariant Enforcement & Failure Remediation |
|---|---|---|
| **1** | `ClientSanitizationPolicy` | Recursively cleans Unicode escapes (`deep_unescape`) and strips inadvertent cross-tenant data leaks. |
| **2** | `FairRiskPolicy` | Evaluates loss distributions using a dual TCO + FAIR actuarial model (10,000 Monte Carlo iterations) with SHA-256 stable seeds. Conjugates Gamma-Poisson (TEF) and Beta-Binomial (VULN) against `evidence_ledger.json`. |
| **3** | `DeduplicationPolicy` | Detects semantically redundant initiatives scattered across distinct pillars (e.g., duplicate cloud migration tasks in Compute vs Networks) and merges them into a single master project under the primary governance pillar. |
| **4** | `SequencingPolicy` | Fixes chronological hallucination in LLM planning. Mandates foundational governance in Horizon 1 ($M_{1}-M_{6}$) before permitting large-scale production deployments in Horizon 2 ($M_{6}-M_{12}$). |
| **5** | `OTPerimeterPolicy` | Inspects initiative scopes for industrial SCADA, ICS, or OT keywords. Unconditionally injects physical hardware data diodes to guarantee unidirectional boundary isolation under NIS2 and Spanish PIC directives. |
| **6** | `ArchiMateDeliverablesPolicy` | Validates that all initiative deliverables conform to standardized ArchiMate enterprise architecture taxonomy. |
| **7** | `BusinessCaseGroundingPolicy` | Constrains capital expenditure and operational cost sizing against the client's financial tier declared in `client_intelligence.json`. |
| **8** | `ReverseTraceabilityPolicy` | Verifies that every proposed remediation project directly links to at least one verified `Finding` in `findings.json`. Unanchored initiatives are pruned. |

---

## 3. Actuarial Modeling & Bayesian Risk Integration

The `FairRiskPolicy` integrates quantitative actuarial modeling directly into the policy compiler:

### 3.1 Dual-Model Monte Carlo Simulation
- **Iteration Bound:** Executes 10,000 Monte Carlo runs per technology pillar.
- **Reproducibility:** Seeded via SHA-256 hash digests of client and tower identifiers to guarantee thread-safe, cryptographically stable outputs across runs.
- **Conjugate Bayesian Updating:**
  - Threat Event Frequency ($\text{TEF} \sim \text{Poisson}(\lambda)$): Prior $\Gamma(\alpha_0, \beta_0)$ updated to posterior $\Gamma(\alpha_0 + k, \beta_0 + 1)$.
  - Vulnerability ($\text{VULN} \sim \text{Binomial}(n, p)$): Prior $\text{Beta}(\alpha_0, \beta_0)$ updated to posterior $\text{Beta}(\alpha_0 + x, \beta_0 + n - x)$.

### 3.2 Dynamic Risk Threshold Escalation
When calculated Annualized Loss Expectancy (ALE) exceeds client risk tolerances defined in `engine_config/policies/fair_risk_profiles.json`, the policy compiler automatically escalates initiative severity and overrides prompt suggestions.

---

## 4. Architectural Invariants for AI Agents

1. **Deterministic Compilation:** Policies must execute as pure transformations on the input payload dictionary without network I/O or stochastic variance.
2. **Reverse Traceability Enforcement:** An initiative lacking verified evidence citations must never pass `ReverseTraceabilityPolicy`.
3. **Hard Perimeters for OT:** Any industrial system flagged under OT or SCADA requires physical unidirectional data diodes; logical or software firewalls alone are strictly rejected.
