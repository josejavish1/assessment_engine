---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/epistemic_graph.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: editorial
notes: ADR 0002 accepting local SQLite in WAL mode for epistemic event graph persistence.
---
# ADR 0002: Local SQLite with Write-Ahead Logging (WAL) for Epistemic Graph Persistence

- **Status:** Accepted
- **Date:** 2026-10-20
- **Deciders:** Principal Architect / Sovereign Engineering Board

---

## 1. Context & Problem Statement

The platform requires an event-sourced assertion store (`EpistemicGraph`) to track evidence fragments, technical gap observations, and cross-tower dependency DAGs. Traditional enterprise patterns suggest hosting a centralized relational database (e.g., PostgreSQL / RDS) or a dedicated graph database (Neo4j).

However, `assessment-engine` is designed as a **sovereign, local-first engine** capable of executing in air-gapped environments, localized laptops, and isolated CI workers without external database credentials or network latency.

---

## 2. Decision Drivers

- **Zero External Infrastructure Dependency:** Enable full pipeline execution and pytest runs without provisioning external database daemons or Docker compose services.
- **Tenant Vault Isolation:** Customer data must isolate physically on disk (`workspaces/<client_slug>/epistemic_graph.db`). Deleting or archiving the workspace directory must completely delete the client's data footprint.
- **High Concurrency & Crash Resilience:** Support concurrent reads from multiple CLI processes and FastAPI workers without database locking errors.

---

## 3. Considered Options

| Option | Operational Overhead | Portability & Air-Gap | Tenant Isolation | Verdict |
|---|:---:|:---:|:---:|:---:|
| **Option 1: Centralized PostgreSQL** | High (RDS/Docker daemon required) | Low (Network-bound) | Soft (Row-Level Security) | Rejected |
| **Option 2: Embedded Graph DB (Neo4j)** | High (JVM dependency) | Medium | Medium | Rejected |
| **Option 3: Local SQLite with WAL** | Zero (Python stdlib) | High (100% portable) | Hard (Physical file vault) | **Accepted** |

---

## 4. Decision Outcome

**Chosen Option: Option 3 (Local SQLite with Write-Ahead Logging).**

Each tenant workspace persists an embedded SQLite event store (`epistemic_graph.db`) configured with `PRAGMA journal_mode=WAL;` and `PRAGMA synchronous=NORMAL;`.

### Positive Consequences:
- **Portability:** Zero infrastructure setup; executing `pytest` or `run_tower_pipeline.py` requires only Python standard library `sqlite3`.
- **Absolute Tenant Privacy:** Client data is physically bounded within `workspaces/<client_slug>/`; cross-tenant leakage is physically impossible.
- **Concurrent Throughput:** WAL mode allows concurrent readers to operate without blocking sequential event appends.

### Negative Consequences & Trade-offs:
- Graph queries require NetworkX projection in Python memory rather than server-side Cypher graph traversal.
- Distributed write clustering is unsupported; execution scaling is process-based per tenant.
