---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/streaming_sentinel.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: editorial
notes: Operational guide, architectural design, and FinOps token shields for Streaming Sentinel on-demand evidence ingestion.
---
# Streaming Sentinel Operations Guide

Canonical operational specification detailing the real-time evidence ingestion engine, dual-tier buffering, multi-worker concurrency mutexes, and FinOps token guardrails in `src/assessment_engine/infrastructure/streaming_sentinel.py`.

---

## 1. Dual-Tier Storage Architecture (Zero-Lockin)

`StreamingSentinel` decouples continuous evidence capture from expensive cloud LLM synthesis:

```
[ Inbound Evidence Streams: Regulatory Alerts, Meeting Transcripts, Log Feeds ]
                                        |
                                        v
+---------------------------------------------------------------------------------------+
| HOT STORAGE TIER: Local SQLite Buffer (streaming_queue.db)                            |
| - High-throughput Write-Ahead Logging (WAL) Mode                                      |
| - Zero API Token Cost (0.00 EUR) & Negligible Disk Overhead                           |
+---------------------------------------------------------------------------------------+
                                        |
                                        v (On-Demand / Dampened Scheduler Trigger)
+---------------------------------------------------------------------------------------+
| COLD STORAGE TIER: Canonical Knowledge Vault & RAG Trees                              |
| - EvidenceEngine (evidence_vault.json) & RaptorEngine (raptor_tree.json)              |
| - EpistemicGraphService Causal Risk Re-calculation                                    |
+---------------------------------------------------------------------------------------+
```

- **Hot Layer:** Ingests unparsed evidence payloads into an ephemeral SQLite database (`streaming_queue.db`) configured in Write-Ahead Logging (`WAL`) mode.
- **Cold Layer:** On-demand batch synchronization flushes pending items, deduplicates fragments, updates the RAPTOR hierarchical tree, and triggers Bayesian graph recalculations.

---

## 2. Four-Tier FinOps & Cybersecurity Shields

To protect against Out-Of-Memory (OOM) attacks, semantic flooding, and unbounded Vertex AI token consumption, the Sentinel executes four sequential filtering gates in local CPU memory before initiating any LLM invocation:

```text
[ Inbound Evidence Payload ]
             |
             v
[ SHIELD 1: Anti-OOM Payload Boundary ] ───(Exceeds 5MB)───► [ HTTP 422 Rejection ]
             |
             v
[ SHIELD 2: Syntactic SHA-256 Hashing ] ───(Exact Match)───► [ Discarded (0 API Tokens) ]
             |
             v
[ SHIELD 3: Semantic Jaccard Filter ]   ───(Overlap > 75%)─► [ Discarded (0 API Tokens) ]
             |
             v
[ SHIELD 4: Dampened Batching Scheduler ] ──(Wait Quiet)──► [ Trigger RAPTOR Rebuild ]
```

1. **Shield 1 (Anti-OOM Payload Guard):** Pydantic schema validation (`EvidencePayload`) strictly rejects payloads with `content` $> 5\text{MB}$ or `source_url` $> 2048$ characters.
2. **Shield 2 (Syntactic SHA-256 Hashing):** Computes a SHA-256 digest over normalized text. Exact duplicates are discarded immediately without downstream processing.
3. **Shield 3 (Semantic Jaccard Token Filter):** Compares token overlap against existing fragments. Payloads sharing $> 75\%$ Jaccard similarity are classified as redundant rewrites and dropped.
4. **Shield 4 (Dampened Batching Scheduler):** Dampens rapid evidence bursts, deferring RAPTOR tree re-indexing until 5 new items accumulate or after a 10-second quiet period.
5. **Defense-in-Depth (Path Traversal Guard):** Enforces strict `Path.is_relative_to()` assertions, blocking directory traversal attacks attempting to escape the tenant sandbox.

---

## 3. Concurrency & Hardware Resilience

`StreamingSentinel` enforces enterprise-grade resilience across multi-worker and distributed deployment topologies:

1. **Distributed OS Mutex (`.sentinel_lock`):** In multi-worker Uvicorn or Gunicorn deployments, a filesystem-level atomic directory lock (`.sentinel_lock`) prevents concurrent write collisions against `evidence_vault.json`.
2. **POSIX Atomic I/O:** All file updates serialize to temporary files (`.tmp`) and commit via atomic `os.replace()`, preventing database corruption upon power-loss or unexpected worker restarts.
3. **SQLite WAL Maintenance:** Automatic cursor management (`contextlib.closing`) and passive background checkpointing (`PRAGMA wal_checkpoint(PASSIVE)`) prevent unbounded `.db-wal` file growth.
4. **FastAPI Lifespan Integration:** Daemon polling threads bind cleanly to FastAPI's asynchronous lifespan context manager, terminating child workers gracefully on SIGTERM.

---

## 4. Operational Ingestion Recipes

### Enqueueing Evidence (Passive Ingestion - Zero Token Cost):
```python
from assessment_engine.infrastructure.streaming_sentinel import StreamingSentinel

sentinel = StreamingSentinel(client_id="acme_corp")
sentinel.enqueue_evidence(
    source_url="https://regulatory-gazette.eu/nis2-directive-update",
    content="Official directive specifying updated risk management deadlines for essential entities..."
)
```

### On-Demand Batch Synchronization:
When ready to incorporate queued evidence into the canonical RAG vault and update Bayesian copula weights:
```bash
python -m assessment_engine.application.tools.sync_sentinel --client acme_corp
```

### Dynamic Graph Auto-Calibration:
Updates edge weights in `epistemic_dependencies.json` via analytical gradient descent based on audited maturity feedback:
```python
from assessment_engine.infrastructure.epistemic_graph_service import EpistemicGraphService

service = EpistemicGraphService(industry_profile="critical_infrastructure")
report = service.backpropagate_audit_feedback(
    intrinsic_maturities=current_scores,
    audited_maturities=verified_audit_scores,
    lr=0.05
)
```
