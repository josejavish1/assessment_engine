---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/infrastructure/ai_client.py
- src/assessment_engine/application/tools/regenerate_smoke_artifacts.py
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: code
notes: Operational runbook and FMEA failure mode analysis for cloud API resilience and deterministic failovers.
---
# Resilience Playbook & Failure Mode Effects Analysis (FMEA)

Canonical operational specification detailing failure modes, automated retry circuits, graceful degradation policies, and offline fallback procedures across `assessment-engine`.

---

## 1. Failure Mode and Effects Analysis (FMEA)

| Failure Mode | System Impact | Severity | Automated Mitigation Circuit | Operational Triage Recipe |
|---|---|:---:|---|---|
| **HTTP 429 Quota Exhaustion** | Vertex AI API requests are throttled, halting synthesis. | High | Exponential backoff retry via `tenacity` (min 2s, max 30s, up to 5 attempts) coupled to `TokenBucketRateLimiter` in `ai_client.py`. | Reduce concurrency limit (`VERTEX_CONCURRENCY_LIMIT`) in shell environment or dispatch jobs during off-peak hours. |
| **API Connection Timeout** | Subprocess freezes indefinitely awaiting external LLM response. | Critical | Enforced async timeout (`asyncio.timeout(timeout_seconds)`) raising `VertexQueryTimeoutError`. | Rerun stage using `--local-only` flag or increase timeout threshold in `runtime_env.py`. |
| **Truncated JSON Response** | Incomplete LLM generation yields malformed JSON. | High | Automated syntactic repair via `parse_json_from_text` (re-balances trailing brackets and braces). | Inspect prompt input token volume; adjust max output tokens in model parameter configurations. |
| **Missing Customer Evidence** | Incomplete questionnaire responses leave technical pillars unanchored. | Medium | Fallback to baseline default scoring with explicit `Needs Review` status flag. | Ingest additional source documents via `EvidenceEngine.ingest_file()`. |

---

## 2. Graceful Degradation & Failover Policies

The platform maintains deterministic fallback policies ensuring continuous deliverable generation even during complete cloud provider outages:

### 2.1 Air-Gapped Local-Only Mode (`--local-only`)
When operating within air-gapped environments or during prolonged cloud provider outages, the pipeline compiles deliverables deterministically using cached baseline fixtures:

```bash
python src/assessment_engine/application/tools/regenerate_smoke_artifacts.py --local-only
```

- **Behavior:** Bypasses Vertex AI preflight checks and uses static pillar findings from `templates/` rather than making outbound network API calls.

### 2.2 Dry-Run Preflight Mode (`--dry-run`)
Validates end-to-end pipeline wiring, filesystem permissions, and OpenXML template compilation without incurring API token costs:

```bash
python src/assessment_engine/application/tools/regenerate_smoke_artifacts.py --dry-run
```

- **Behavior:** Generates structurally valid empty payloads to confirm that downstream AST compilers (`docx_compiler.py`, `tomo_asis_ast_compiler.py`) execute without exceptions.

### 2.3 Offline Evidence Snapshotting (Anti Link-Rot)
For regulatory benchmarking (RAGE), `EvidenceSnapshotter` caches physical PDF and HTML copies of external standards in `workspaces/<client_id>/evidence_cache/`. If live web retrieval fails, the engine falls back to locally snapshotted assets.

---

## 3. Production Incident Resolution Recipes

### Incident A: Google Cloud Authentication Exceptions (`GoogleDefaultCredentialsError`)
1. Verify active Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```
2. Verify pinned service account path:
   ```bash
   python -m assessment_engine.application.tools.check_vertex_ai_access
   ```
3. If internet access is completely blocked, switch execution to local mode (`--local-only`).

### Incident B: CI Schema Drift Gate Failures
1. Identify diverging Pydantic models reported by `validate_contracts_schemas.py`.
2. Execute automated schema contract reconciliation:
   ```bash
   python src/assessment_engine/application/tools/validate_contracts_schemas.py --repo-root . --documentation-map docs/documentation-map.yaml --autofix
   ```
3. Commit aligned Markdown contract tables and push to re-trigger CI.
