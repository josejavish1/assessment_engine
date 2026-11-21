---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/runtime_paths.py
- src/assessment_engine/infrastructure/ai_client.py
- src/assessment_engine/mcp_server.py
- src/assessment_engine/infrastructure/epistemic_graph.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: code
notes: Canonical technical specification of the sovereign isolation, tenant vaults, and security boundaries.
---
# Sovereign Isolation & Access Control Boundaries

Canonical specification defining the security boundaries, tenant isolation models, filesystem sandboxing, and LLM data protection invariants of `assessment-engine`.

---

## 1. Architectural Philosophy: Sovereign by Design

`assessment-engine` rejects shared multi-tenant database pools to eliminate cross-tenant data leakage risks. The system enforces a **Local-First Sovereign Tenant Vault** architectural pattern (`src/assessment_engine/infrastructure/runtime_paths.py`):

```
+---------------------------------------------------------------------------------------+
| SOVEREIGN WORKSPACE ROOT: workspaces/<client_slug>/                                   |
|                                                                                       |
|  [ evidence/ ]      --> Read-only immutable vault for customer inputs (.docx, .txt)   |
|  [ scratchpad/ ]    --> Ephemeral intermediate JSON payloads & calculation state     |
|  [ deliverables/ ]  --> Compiled final Word .docx deliverables                        |
+---------------------------------------------------------------------------------------+
                                          |
                                          v (Bounded Prompts Wrapped in <untrusted_context>)
+---------------------------------------------------------------------------------------+
| ENTERPRISE VERTEX AI (ai_client.py)                                                   |
| - Zero Data Retention (ZDR) Enterprise Agreement                                      |
| - Service Account Authentication & SSL/TLS Pinning                                   |
| - Prompt Injection Containment Delimiters                                             |
+---------------------------------------------------------------------------------------+
```

---

## 2. Tenant Filesystem Sandboxing (`TenantWorkspace`)

All runtime paths derive strictly through `TenantWorkspace` records defined in `runtime_paths.py`:

```python
@dataclass(frozen=True)
class TenantWorkspace:
    client_slug: str
    root: Path         # workspaces/<client_slug>
    evidence: Path     # workspaces/<client_slug>/evidence
    scratchpad: Path   # workspaces/<client_slug>/scratchpad
    deliverables: Path # workspaces/<client_slug>/deliverables
```

### 2.1 Directory Traversal Guardrails
Path resolution is validated against boundary violations:
- **`WorkspaceConfig.validate_storage_path()`:** Canonicalizes real paths using `Path.resolve()`. Any path escaping the tenant root triggers a `PathTraversalError` and halts pipeline execution.
- **Symlink Disallowance:** Symlink creation pointing outside `workspaces/<client_slug>/` is blocked by runtime file handlers.

---

## 3. Subprocess Confinement & Execution Boundaries

In both CLI and Model Context Protocol (MCP) server modes:

1. **Subprocess Grouping:** Stages invoke via `python -m assessment_engine.application.run_tower_pipeline` (or specific stage modules) under distinct Process Group IDs (PGIDs), preventing lingering background tasks from polluting system memory.
2. **Environment Sanitization:** Child processes receive an explicit dictionary of validated runtime variables (`pipeline_runtime.py`). Hardcoded paths and shell substitutions are disallowed.
3. **Safety Action Gates:** In MCP mode (`mcp_server.py`), high-impact or destructive operations pause execution until an operator explicitly approves the action via `authorize_action_gate`.

---

## 4. LLM Data Privacy & Prompt Injection Defenses

### 4.1 Enterprise Zero Data Retention (ZDR)
Outbound LLM inference communicates exclusively through `src/assessment_engine/infrastructure/ai_client.py` targeting Google Cloud Vertex AI:
- Authenticated via Workload Identity or pinned service account keys.
- Operates under Google Cloud Enterprise Zero Data Retention agreements (customer telemetry is never retained or used to train public foundation models).

### 4.2 Indirect Prompt Injection Containment
To neutralize adversarial payloads embedded inside parsed customer documents (e.g., hidden prompt instructions in imported `.docx` or `.txt` files), all raw evidence text is sanitized and enclosed in explicit boundary envelopes:
```xml
<untrusted_context>
[Raw extracted evidence text from customer documents]
</untrusted_context>
```
System prompts instruct models to evaluate content inside `<untrusted_context>` strictly as passive data, stripping execution privileges and blocking semantic hijacking.

---

## 5. Architectural Invariants for AI Agents

1. **Strict Vault Isolation:** All disk reads and writes must operate within `TenantWorkspace` boundaries. Absolute paths outside the repo root or sibling tenant folders are strictly prohibited.
2. **No Data Leakage in Logging:** Raw credentials, API keys, and sensitive customer identifiers must never appear in log streams or diagnostic snapshots.
3. **Stateless Memory Teardown:** Temporary files in `scratchpad/` must be purgeable via standard workspace cleanup tasks without corrupting compiled deliverables in `deliverables/`.
