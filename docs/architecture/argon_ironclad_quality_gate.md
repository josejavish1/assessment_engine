# ARGON IRONCLAD QUALITY GATE ARCHITECTURE

**Document ID:** `ARCH-GATE-2026-IRONCLAD`  
**Status:** CANONICAL PRODUCTION ARCHITECTURE  
**Auditor & Model:** `gemini-4-argon` (`ModelTier.REASONING`)  
**Standard:** Google Tier-1 / Anthropic Infrastructure  
**Core Invariant:** Fail-Closed Deterministic & Cryptographic State Gate. Zero tasks progress without explicit, mathematically verified Argon approval.

---

## 1. Forensic Justification: Why Manual tmux Review Is Flawed

In interactive multi-agent sessions, manual review loops suffer from four structural vulnerabilities:

1. **Context Contamination (Shared State Bias):** When an agent summarizes its own code before asking for a review, the reviewer inherits the author's blind spots. The reviewer accepts the author's framing rather than evaluating the cold AST.
2. **RLHF Sycophancy Bias:** Models conditioned via RLHF have a strong conversational prior toward agreeableness and conflict resolution. Without adversarial inversion, the reviewer acts as a polite rubber-stamp.
3. **Unstructured Output Hallucination:** Parsing natural language text (e.g., checking if `"approved"` is in the prose) creates false-positive passes when a model says: *"The architecture looks good, except for a critical vulnerability on line 42."*
4. **Human Fatigue & Diff Truncation:** A human operator in tmux cannot guarantee full AST line inspection across 18 PRs, often letting truncated diffs pass at 3:00 AM.

---

## 2. Zero-Bypass Cryptographic Gate Architecture

To guarantee that the orchestrator **mechanically cannot** advance to the next block without a 100% compliant, formally verified approval, we implement a **Fail-Closed Deterministic State Machine**:

```
+-----------------------------------------------------------------------------------+
|                        ZERO-BYPASS IRONCLAD QUALITY GATE                          |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
                    +----------------------------------------+
                    |   1. Git Working Tree Diff Extraction  |
                    |      (Compute SHA-256 of Raw Diff)     |
                    +----------------------------------------+
                                         |
                                         v
                    +----------------------------------------+
                    |   2. Deterministic Pre-Flight Sieve    |
                    |   - Zero Spanish Lexicon Scanner       |
                    |   - AST Hardcoded Literal Detector     |
                    +----------------------------------------+
                                  /              \
                         [FAIL]  /                \  [PASS]
                                /                  \
                               v                    v
        +------------------------------+    +---------------------------------------+
        | Short-Circuit Rejection      |    | 3. Adversarial Argon Audit            |
        | (Zero LLM Tokens Wasted)     |    | - Model: gemini-4-argon (REASONING)   |
        +------------------------------+    | - Temp: 0.0 (Deterministic)           |
                       |                    | - Isolated Context (Raw Diff Only)    |
                       |                    | - Structured Pydantic Schema Output   |
                       |                    +---------------------------------------+
                       |                                 /              \
                       |                        [REJECT]/                \[APPROVE]
                       v                               v                  v
        +------------------------------------------------+    +---------------------+
        | 4. Self-Healing Remediation Loop               |    | 5. Cryptographic    |
        | - Inject Exact Line/File Violations to Coder   |    |    Clearance Token  |
        | - Increment Attempt Counter (Max = N)          |    | - Bind Diff SHA-256 |
        | - If Attempt > N: git reset --hard & HALT      |    | - Advance DAG Node  |
        +------------------------------------------------+    +---------------------+
```

### Architectural Guarantees
1. **Isolated Context Execution:** `gemini-4-argon` never sees the Coder's prompt, history, or justifications. It receives **only** the raw unified `git diff`, line-numbered complete source files, and the adversarial system prompt.
2. **Strict Pydantic Schema Output:** Output is forced via `response_schema=ArgonAuditReport`. Every single sub-criterion (`zero_spanish_verified`, `zero_hardcoding_verified`, `universal_tier1_enterprise_ready`, `zero_bugs_or_antipatterns`) is an explicit boolean field.
3. **Mathematical Conjunction Invariant:** The Python gate overrides any verdict to `FAIL` if `len(findings) > 0` or if **any** boolean invariant is `False`, regardless of the LLM's prose summary.
4. **Cryptographic Clearance Token:** The task runner cannot transition state to `COMPLETED` without a `CryptographicClearanceToken` signed via `HMAC-SHA256` over the exact `git diff` hash. If a single byte mutates post-audit, the token is invalidated (TOCTOU protection).
5. **Deterministic Pre-Flight Sieve:** Local AST and regex scanners catch Spanish tokens (`á, é, í, ó, ú, ñ`, `configuracion`, etc.) and bare `except:` clauses in $<5\text{ ms}$, rejecting invalid code before calling the LLM API.

---

## 3. Comparison: Manual tmux Review vs. Automated Ironclad Gate

| Evaluation Dimension | Manual `tmux` Human-in-the-Loop | `ArgonIroncladQualityGate` Automated Harness |
| :--- | :--- | :--- |
| **Context Isolation** | **Vulnerable:** Shared thread context causes reviewer sycophancy and agreement bias. | **Immune:** 100% cold, stateless API call with `temperature=0.0`. Sees only raw diff and source code. |
| **Visibility Scope** | **Vulnerable:** Interactive CLIs truncate diffs and large file reads to save tokens. | **Exhaustive:** Line-numbered complete source files injected alongside unified diff for 100% AST visibility. |
| **Lexical & AST Sieve** | **Probabilistic:** Relies on model attention to spot a Spanish word in a 1,500-line file. | **Deterministic:** Python `ast.walk` and regex catch Spanish characters and syntax stubs instantaneously. |
| **Verdict Enforcement** | **Conversational:** Human operator may accept "mostly working" code during late-night fatigue. | **Mathematical:** Strict boolean conjunction in Python code: `findings == 0` AND all 4 booleans == `True`. |
| **Rollback Safety** | **Fragile:** Failed manual fixes leave dirty working trees and broken intermediate files. | **Transactional:** Bounded retries (max 5); failure triggers atomic `git reset --hard HEAD && git clean -fd`. |

---

## 4. Production Python Implementation (`ArgonIroncladQualityGate`)

The complete production implementation is integrated into `src/assessment_engine/infrastructure/quality/argon_gate.py` and provides the drop-in class `ArgonIroncladQualityGate` consuming `ModelTier.REASONING` (`gemini-4-argon`).
