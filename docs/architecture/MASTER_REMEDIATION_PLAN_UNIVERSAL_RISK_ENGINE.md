# Master Remediation Plan: Universal Epistemic & Institutional Risk Engine (SR 11-7 / Open FAIR / IFRS)

## Executive Summary
This document formalizes the root-cause remediation plan designed to eradicate all manual patching, silent capability dropping, and mathematical/scale distortions across the assessment engine. It addresses the findings of the Red Team Adversarial Audit (`docs/audits/RED_TEAM_ROOT_CAUSE_REMEDIATION_AUDIT.md`) and enforces a universal, scale-invariant architecture valid for 100% of enterprises globally (Fintech, Process Manufacturing, Healthcare, Utilities, Public Cloud SaaS).

---

## 1. Root Cause Taxonomy & Systemic Defects

### Defect 1: The 19 Missing Pillars & Broken Index Bijection
* **Mechanism:** Naive filtering in `in_memory_asis_compiler.py` dropped findings classified as `SURVEY_INFERRED_BOILERPLATE` using `continue`.
* **Consequence:** 19 of 61 assessed pillars disappeared from the deliverable. In Tower 10, cards skipped from `RVS04` to `RVS06`, leaving the client questioning the validity of `RVS07`. Critical physical domains (Tower 1 Power and HVAC; Tower 7 Service Desk and SRE) vanished completely.
* **Remediation:** Strict Contiguous Index Bijection (`RVS01` $\to$ `RVS0N`). No capability is ever dropped. Survey-only maturity gaps are rendered **in-place** as compact, non-stochastic Governance Stubs (`ALE = 0 €`, `RTO = 0.0h`).

### Defect 2: The 8-Hour Outage Fallacy on Minor Operational Friction
* **Mechanism:** Lack of duration physical modeling caused the engine to default to macro-tower outage hours (e.g., 8.0h or 14.0h) for localized chores (unrotated `/var/log` partitions, missing 802.1X NAC, unensayed DRP documentation).
* **Consequence:** Local disk chores were modeled as catastrophic 62,688 € enterprise blackouts. Control gaps (NAC, DRP documents) were falsely modeled as primary loss events with intrinsic downtime.
* **Remediation:** 5-Tier Loss Physics with strict Pre-Flight Circuit Breakers:
  1. **Non-Production Zero-Outage Rule:** Lab/test/dev environments mandate $t_{\text{RTO}} = 0.0\text{h}$ and $\alpha_{\text{prod}} = 0.0$.
  2. **Tier-A Operational Friction Cap:** Local maintenance/disk tasks capped at $t_{\text{RTO}} \le 0.5\text{h}$ and $\text{ALE} \le 5,000\text{ €}$.
  3. **Vulnerability Separation:** Security and governance controls (NAC, PAM, DRP documents) carry $t_{\text{RTO}} = 0.0\text{h}$ as primary loss; their impact is strictly modeled as event frequency multipliers or regulatory liability.

### Defect 3: Conflation of Stochastic Risk (Ledger A) and Deterministic OpEx (Ledger B)
* **Mechanism:** The engine forced guaranteed recurring OpEx waste (NOS 450k € contract, 55k € USB imaging) through probabilistic Poisson distributions and Euler diversification credits.
* **Consequence:** USB imaging was assigned frequency = 1.0/year ($20\text{ €/year}$) because fleet volume ($N=350$) was lost. The NOS contract was slashed by Euler diversification to $9,940\text{ €/year}$.
* **Remediation:** Strict Dual-Ledger Architecture:
  * **Ledger A (Stochastic ALE):** Unplanned disruptions ($P < 1.0$), aggregated via Monte Carlo, bounded Euler diversification credit $\le 25.0\%$.
  * **Ledger B (Deterministic OpEx / Toil):** Guaranteed recurring drain ($P = 1.0$), evaluated algebraically as $V_{\text{annual}} \times t_{\text{hours}} \times W_{\text{wage}} + \text{Cash\_Bleed}$, **strictly 0.0% Euler discount**.

---

## 2. Technical Architecture & Data Contracts

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CANONICAL INDEX ENFORCER & IN-PLACE COMPACT STUBS                       │
│    Every tower enforces exact contiguous index: RVS01 to RVS0N              │
│    • Verified Field Evidence (Tier 1/2) ──> Full Open FAIR Risk Card        │
│    • Sector Exposure Prior (Tier 3)     ──> Badge: [SECTOR PRIOR UNVERIFIED]│
│    • Survey Maturity Gap (Tier 4)       ──> In-Place Compact Stub (ALE = 0) │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. PRE-FLIGHT PLAUSIBILITY CIRCUIT BREAKERS (input_resolver.py)             │
│    • Non-Prod Env (Lab/Dev/Test)        ──> RTO = 0.0h, Outage Loss = 0.0   │
│    • Internal Sysadmin Tasks            ──> Cost capped at Hours * Wage     │
│    • Tier-A Disk / Log Rotation         ──> RTO <= 0.5h, ALE <= 5,000       │
│    • Control Gaps (NAC / DRP Docs)      ──> RTO = 0.0h (Likelihood only)    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. DUAL-LEDGER FINANCIAL SPLIT (IFRS / GAAP / BASEL III)                    │
│    • Ledger A (Stochastic ALE): P < 1.0, Monte Carlo, Euler Cap <= 25%      │
│    • Ledger B (Deterministic OpEx): P = 1.0, V_fleet * h * Wage + Cash_Bleed │
│      Euler Discount = 0.0% (No diversification of guaranteed waste)         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. CROSS-TOWER CANONICAL CONTRACT DEDUPLICATION                             │
│    • Primary Owner Pillar carries the financial payload                     │
│    • Contributory Pillars reference primary with Incremental OpEx = 0.0     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phased Execution Roadmap

### Phase 1: Core Domain Physics & Circuit Breakers (`src/assessment_engine/domain/`)
1. Implement Pre-Flight Circuit Breakers in `input_resolver.py` (`Non-Prod Zero-Outage`, `Internal Task Cap`, `Tier-A Operational Friction Ceiling`).
2. Implement Fleet Volume Multiplier ($V_{\text{annual}}$) in `input_resolver.py` and `euler_allocator.py` for Ledger B toil.
3. Enforce Dual-Ledger data contracts in `AdditiveLossDecomposition`:
   - `stochastic_ale`: Ledger A
   - `deterministic_opex`: Ledger B
   - `is_deterministic`: Boolean flag enforcing 0% Euler discount.

### Phase 2: In-Place Compact Stubs & Contiguous Bijection (`src/assessment_engine/adapters/compilers/`)
1. Refactor `in_memory_asis_compiler.py` to eliminate `continue` skips on boilerplate findings.
2. Render Tier 4 findings as **In-Place Compact Stubs** (3 lines: Maturity score, Survey Gap description, `ALE = 0.00 €`, `RTO = 0.0h`).
3. Add Hard Compilation Assertion:
   ```python
   expected_ids = [f"RVS{i:02d}" for i in range(1, len(canonical_pillars) + 1)]
   actual_ids = [r["id"] for r in rendered_cards]
   assert actual_ids == expected_ids, f"Index Bijection Broken in Tower {tower_id}: {actual_ids} != {expected_ids}"
   ```

### Phase 3: Dual-Ledger Presentation in AST & Word Compiler (`payload_to_ast.py`)
1. Render Dual-Ledger Executive Matrix in Chapter 4 and Tomo 1:
   - Column 1: Stochastic Risk Exposure (Ledger A - Mean ALE)
   - Column 2: Extreme Tail Risk (Ledger A - VaR 99.9% / PML)
   - Column 3: Guaranteed Annual OpEx Leakage & Toil (Ledger B - EBITDA Drag)
2. Render individual Ledger B cards with dedicated OpEx styling (no fake downtime bars, zero Euler discount, clear Fleet Volume derivation).

### Phase 4: Full Empirical Re-Hydration & Verification
1. Re-hydrate the 19 unevidenced findings in Molins using authentic quotes from the 347 interview speech turns (CPD 2 battery UPS, NetApp 4h replication, weighbridge serial convertors, SAU disconnection).
2. Execute automated validation:
   - Zero broken sums.
   - Zero numbering gaps across all 10 towers.
   - Zero hardcoded numbers.
   - 100% Technical English in `src/`.
3. Submit final deliverable suite to Top-Tier Tribunal for definitive certification.
