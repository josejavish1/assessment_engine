---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/mcp_server.py
- src/assessment_engine/application
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: explanation
verification_mode: mixed
notes: Canonical architecture specification of the FastMCP tool server and agentic execution protocol.
---
# Model Context Protocol (MCP) Server Architecture

Canonical specification defining the Model Context Protocol (MCP) server architecture, tool interfaces, subprocess isolation, and asynchronous job execution in `src/assessment_engine/mcp_server.py`.

---

## 1. Architectural Scope & Service Model

The MCP service mode exposes discrete capabilities of the `assessment-engine` platform as typed tool interfaces conforming to the Anthropic Model Context Protocol specification:

```
[ External AI Agent / Supervisor ]
                |
                v (JSON-RPC over stdio / SSE)
+---------------------------------------------------------------------------------------+
| FAST_MCP SERVER: src/assessment_engine/mcp_server.py                                  |
| - Tool Discovery & Signature Introspection                                            |
| - Subprocess Confinement & Execution Isolation                                         |
| - Persistent Job Store (sqlite3 / job queue)                                          |
| - Safety Action Gatekeeper                                                            |
+---------------------------------------------------------------------------------------+
                |
         +------+------+
         |             |
         v             v
[ Python Runtime ]  [ OpenXML AST Compilers ]
(application/*.py)  (payload_to_ast.py + docx_compiler.py)
```

- **Module Path:** `src/assessment_engine/mcp_server.py`.
- **Framework:** `fastmcp.FastMCP`.
- **Primary Objective:** Provide external LLM supervisors with deterministic execution primitives, structured state inspection, and on-demand AST compilation without running entire batch pipelines.

---

## 2. FastMCP Tool Catalog

The service exposes 13 typed tool interfaces across three functional categories:

### A. State Inspection & Telemetry
| Tool Identifier | Input Parameters | Return Schema | Operational Invariant |
|---|---|---|---|
| `get_tower_state` | `client_id: str`, `tower: str`, `working_dir: Optional[str]` | `Dict[str, Any]` | Validates physical JSON files against `BlueprintPayload` and `AnnexPayload` schemas, returning status (`valid`, `invalid`, `missing`, `error`). |

### B. Declarative AST Compilation & Delivery
| Tool Identifier | Input Parameters | Return Schema | Operational Invariant |
|---|---|---|---|
| `compile_tower_annex_ast` | `payload_json: str`, `output_docx: str`, `doc_lang: str = "en"` | `str` (Confirmation) | Compiles OpenXML DOCX directly via `payload_to_ast.py` and `docx_compiler.py`. |
| `render_tower_docx` | `annex_payload_json: str`, `template_docx: str`, `output_docx: str` | `str` (Confirmation) | Legacy Word template rendering adapter. |
| `build_tower_payload` | `client_id: str`, `tower: str` | `str` (JSON Path) | Backward-compatible builder for legacy intermediate payload structures. |
| `generate_radar_chart` | `global_payload_json: str`, `output_path: str` | `str` (PNG Path) | Renders multi-axis capability radar chart from global report payload. |
| `render_commercial_docx` | `commercial_payload_json: str`, `template_docx: str`, `output_docx: str` | `str` (Confirmation) | Compiles Account Action Plan deliverable binary. |

### C. Asynchronous Agentic Jobs & Human-in-the-Loop Gates
| Tool Identifier | Input Parameters | Return Schema | Operational Invariant |
|---|---|---|---|
| `start_plan_generation` | `client_id: str`, `tower: str`, `instructions: str` | `Dict[str, Any]` (`job_id`) | Enqueues background planning job in persistent job store. |
| `check_plan_status` | `job_id: str` | `Dict[str, Any]` | Polls asynchronous plan generation status (`running`, `completed`, `failed`). |
| `start_plan_execution` | `job_id: str` | `Dict[str, Any]` | Dispatches stage execution across child worker threads. |
| `check_execution_status`| `job_id: str` | `Dict[str, Any]` | Returns execution telemetry, task logs, and error traces. |
| `check_action_gate` | `job_id: str` | `Dict[str, Any]` | Interrogates active safety gates requiring explicit operator approval. |
| `authorize_action_gate`| `job_id: str`, `gate_id: str`, `action: str` | `Dict[str, Any]` | Authorizes or declines paused execution transitions. |
| `abort_and_revert` | `job_id: str` | `Dict[str, Any]` | Aborts execution and restores workspace to clean state. |

---

## 3. Subprocess Execution & Security Isolation

When invoking internal application modules, the MCP server enforces strict process boundaries:

1. **Subprocess Confinement:** Subprocesses invoke explicitly via `python -m assessment_engine.application.<module>`. Direct in-process execution is prohibited for heavy stages to prevent global state pollution.
2. **Environment Propagation:** Propagates `PYTHONPATH`, Google Cloud credentials, and locale parameters deterministically.
3. **Structured Failure Traps:** Captures both `stdout` and `stderr`. Non-zero exit codes raise structured JSON errors preventing opaque failures.
4. **Canonical Primacy:** State inspection in `get_tower_state` evaluates modern `blueprint_<tower>_payload.json` and `approved_annex_<tower>.template_payload.json` first, treating legacy section files as secondary diagnostic data.

---

## 4. Architectural Invariants for AI Agents

1. **Schema Validation on Read:** `get_tower_state` must execute Pydantic model validation against disk payloads before reporting a state as `valid`.
2. **Asynchronous Safety:** Destructive operations or multi-tower runs must require explicit approval through `check_action_gate` and `authorize_action_gate`.
3. **Format Monism:** All render tools compile strictly to Microsoft Word (`.docx`). PDF and HTML output tools are prohibited.
