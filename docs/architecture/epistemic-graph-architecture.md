---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/epistemic_graph.py
- src/assessment_engine/infrastructure/epistemic_graph_service.py
- engine_config/policies/epistemic_dependencies.json
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
notes: Technical specification of the Epistemic Graph Event Store and Loopy Causal Belief Network service.
---
# Epistemic Knowledge Graph Architecture

Canonical specification defining the dual-tier graph architecture of `assessment-engine`: the SQLite event-sourced assertion store and the Loopy Causal Belief Network (LCBN) risk propagation engine.

---

## 1. Dual-Tier Architectural Model

The Epistemic Graph decouples deterministic state persistence from causal graph inference:

```
+---------------------------------------------------------------------------------------+
| INFERENCE & PROPAGATION LAYER: EpistemicGraphService (epistemic_graph_service.py)     |
| - Loopy Causal Belief Network (NetworkX)                                              |
| - Banach Fixed-Point Risk Propagation                                                 |
| - Eigenvector Risk Centrality (ERC / Katz-PageRank)                                   |
| - Counterfactual Simulation (do-calculus) & Analytical Backpropagation                |
+---------------------------------------------------------------------------------------+
                                          ^
                                          | (Reads Topology & Dependencies)
                                          v
+---------------------------------------------------------------------------------------+
| DECLARATIVE DEPENDENCY PROFILES: engine_config/policies/epistemic_dependencies.json   |
+---------------------------------------------------------------------------------------+
                                          ^
                                          | (Materializes Events & Assertions)
                                          v
+---------------------------------------------------------------------------------------+
| EVENT-SOURCED STORAGE LAYER: EpistemicGraph (epistemic_graph.py)                      |
| - Append-only SQLite Event Ledger (epistemic_graph.db)                                |
| - Subject-Predicate-Object Triplet Registry                                           |
| - CQRS State Projections & Path-Traversal Guardrails                                  |
+---------------------------------------------------------------------------------------+
```

---

## 2. Loopy Causal Belief Network (LCBN) Engine

Unlike acyclic DAGs, enterprise technology architectures contain bidirectional feedback loops (e.g., Network T3 secures SOC T5, while SOC T5 monitors Network T3). `EpistemicGraphService` manages cyclic dependencies through mathematical contraction:

### 2.1 Banach Fixed-Point Risk Convergence
Risk propagation across cyclic topologies is solved iteratively:

$$R^{(t+1)} = \sigma\left(W \cdot R^{(t)} + R^{(0)}\right)$$

Where $W$ is the weighted adjacency matrix loaded from `epistemic_dependencies.json`, $R^{(0)}$ represents baseline intrinsic risk, and $\sigma$ is a bounded sigmoid scaling function. Iteration executes until convergence:

$$\|R^{(t+1)} - R^{(t)}\| < \text{tol} \quad (\text{default: } 10^{-6}, \text{max\_iter: } 100)$$

### 2.2 Eigenvector Risk Centrality (ERC / Katz-PageRank)
Combines empirical Monte Carlo variance with graph centrality to isolate the enterprise Single Point of Failure (SPOF):

$$\vec{c} = d \cdot W^T \vec{c} + (1 - d) \cdot \vec{\sigma}_{\text{MonteCarlo}}$$

- **Damping Factor ($d$):** Fixed at $0.85$ to prevent nilpotent matrix collapse.
- **$\vec{\sigma}_{\text{MonteCarlo}}$:** Empirical standard deviation vector from single-tower risk fuzzer runs.
- **SPOF Identification:** The node with $\max(c_i)$ designates the highest-priority architectural bottleneck.

### 2.3 Counterfactual Interventions (Pearl do-calculus)
Simulates hypothetical remediation scenarios:
```python
# Evaluates impact of artificial maturity uplift on dependent towers
delta: Dict[str, Any] = service.simulate_counterfactual_intervention(
    intrinsic_maturities=current_scores,
    interventions={"T3": 4.5, "T5": 4.0}
)
```

### 2.4 Causal Backpropagation & Online Learning
The engine adjusts graph weights dynamically based on empirical audit discrepancies:
1. Calculates Mean Squared Error (MSE) between a priori model estimates and a posteriori audit scores.
2. Updates edge weights $W_{ij} \leftarrow W_{ij} - \eta \cdot \frac{\partial \text{MSE}}{\partial W_{ij}}$ with learning rate $\eta = 0.05$.
3. Persists optimized weights atomically using `os.replace` to `epistemic_dependencies.json`.

---

## 3. SQLite Event Store Architecture (`epistemic_graph.py`)

`EpistemicGraph` enforces transactional persistence and auditability:

### 3.1 Event Ledger Schema
- **`events` Table:**
  - `event_id: TEXT PRIMARY KEY` (UUIDv4)
  - `event_type: TEXT` (`ASSERTION_RECORDED`, `INITIATIVE_PROMOTED`, `DEPENDENCY_LINKED`)
  - `entity_id: TEXT` (Canonical identifier)
  - `payload: TEXT` (JSON-serialized event data)
  - `timestamp: REAL` (Epoch seconds)

### 3.2 Security & Integrity Controls
- **Path-Traversal Guard:** `WorkspaceConfig.validate_storage_path()` blocks directory traversal attacks (`PathTraversalError`).
- **Ledger Corruption Detection:** Replay policies verify database hash sequences, raising `LedgerCorruptionError` upon malformed entries.

---

## 4. Architectural Invariants for AI Agents

1. **Deterministic Convergence:** Graph propagation algorithms must guarantee finite execution through strict convergence thresholds ($\text{tol} = 10^{-6}$).
2. **Atomic Weight Mutability:** Updates to `epistemic_dependencies.json` must execute via atomic file replacement to prevent corrupt configuration states during concurrent reads.
3. **Event Replayability:** All projection states in the epistemic graph must be deterministically reconstructible from the SQLite event log.
