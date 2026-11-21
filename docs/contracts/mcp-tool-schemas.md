---
status: Verified
owner: docs-governance
source_of_truth:
- src/assessment_engine/mcp_server.py
- docs/architecture/mcp-mode.md
last_verified_against: 2026-11-21
applies_to:
- humans
- ai-agents
doc_type: canonical
diataxis: reference
verification_mode: schema
notes: Canonical JSON-RPC schema contracts and tool definitions for the FastMCP Model Context Protocol service.
---
# FastMCP Server Tool Schemas Contract

Canonical reference specification defining the input parameter schemas, return models, and JSON-RPC dispatch protocols for all 13 tools exposed by the **FastMCP Service** (`src/assessment_engine/mcp_server.py`).

---

## 1. Protocol Architecture & JSON-RPC Dispatch

External agent orchestrators (Cursor, Claude Desktop, autonomous sub-agents) invoke tools via JSON-RPC 2.0 messages transmitted over `stdio` or Server-Sent Events (SSE):

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get_tower_state",
    "arguments": {
      "client_id": "acme_corp",
      "tower": "T1"
    }
  },
  "id": "req-001"
}
```

---

## 2. Assessment & Pipeline Inspection Tools

### `get_tower_state`
Inspects workspace disk artifacts for a specific tower and validates them against Pydantic schemas.

```json
{
  "name": "get_tower_state",
  "description": "Inspects generated payloads and compilation readiness for a specific tower.",
  "parameters": {
    "type": "object",
    "properties": {
      "client_id": { "type": "string", "description": "Unique client slug identifier" },
      "tower": { "type": "string", "description": "Tower code (e.g., T1, T2, T3, T5)" },
      "working_dir": { "type": "string", "description": "Optional custom workspace path" }
    },
    "required": ["client_id", "tower"]
  }
}
```
- **Return Type:** `Dict[str, Any]` (`status: "valid" | "invalid" | "missing" | "error"`, `blueprint_path: str`, `annex_path: str`, `validation_errors: list[str]`).

---

## 3. Declarative AST Compilation Tools

### `compile_tower_annex_ast`
Compiles an executive tower annex directly via OpenXML AST compilers (`payload_to_ast.py` and `docx_compiler.py`).

```json
{
  "name": "compile_tower_annex_ast",
  "description": "Compiles a tower annex DOCX document directly via the Declarative AST Engine.",
  "parameters": {
    "type": "object",
    "properties": {
      "payload_json": { "type": "string", "description": "Filesystem path to the input blueprint payload JSON file" },
      "output_docx": { "type": "string", "description": "Destination path for the compiled DOCX binary" },
      "doc_lang": { "type": "string", "enum": ["en", "es"], "default": "en", "description": "Document language locale" }
    },
    "required": ["payload_json", "output_docx"]
  }
}
```
- **Return Type:** `str` (Confirmation message with byte size and absolute path).

### `generate_radar_chart`
Compiles the multi-axis capability radar chart vector visual from the global report payload.

```json
{
  "name": "generate_radar_chart",
  "description": "Renders the multi-axis radar chart PNG graphic from global_report_payload.json.",
  "parameters": {
    "type": "object",
    "properties": {
      "global_payload_json": { "type": "string", "description": "Path to global_report_payload.json" },
      "output_path": { "type": "string", "description": "Output destination path for the PNG image" }
    },
    "required": ["global_payload_json", "output_path"]
  }
}
```

### `render_commercial_docx`
Compiles the Account Action Plan commercial proposal deliverable.

```json
{
  "name": "render_commercial_docx",
  "description": "Compiles the commercial account action plan proposal deliverable into OpenXML DOCX.",
  "parameters": {
    "type": "object",
    "properties": {
      "commercial_payload_json": { "type": "string", "description": "Path to commercial_report_payload.json" },
      "template_docx": { "type": "string", "description": "Path to base OpenXML template style" },
      "output_docx": { "type": "string", "description": "Output path for the generated DOCX" }
    },
    "required": ["commercial_payload_json", "template_docx", "output_docx"]
  }
}
```

---

## 4. Asynchronous Agentic Job Management & Safety Gates

### `start_plan_generation` & `check_plan_status`
Enqueues and polls asynchronous planning jobs managed by the persistent job store.

```json
{
  "name": "start_plan_generation",
  "description": "Enqueues an asynchronous plan generation job.",
  "parameters": {
    "type": "object",
    "properties": {
      "client_id": { "type": "string" },
      "tower": { "type": "string" },
      "instructions": { "type": "string", "description": "Specific planning objectives and constraints" }
    },
    "required": ["client_id", "tower", "instructions"]
  }
}
```

### `check_action_gate` & `authorize_action_gate`
Inspects and resolves interactive safety gates requiring human-in-the-loop (HITL) approval prior to executing high-risk operations.

```json
{
  "name": "authorize_action_gate",
  "description": "Resolves a paused execution gate with operator authorization or rejection.",
  "parameters": {
    "type": "object",
    "properties": {
      "job_id": { "type": "string", "description": "Active job identifier" },
      "gate_id": { "type": "string", "description": "Unique identifier of the paused safety gate" },
      "action": { "type": "string", "enum": ["approve", "reject", "abort"] }
    },
    "required": ["job_id", "gate_id", "action"]
  }
}
```

### `abort_and_revert`
Emergency abort mechanism rolling back uncommitted scratchpad modifications.

```json
{
  "name": "abort_and_revert",
  "description": "Halts active job execution, terminates child worker threads, and restores workspace hygiene.",
  "parameters": {
    "type": "object",
    "properties": {
      "job_id": { "type": "string", "description": "Target job identifier" }
    },
    "required": ["job_id"]
  }
}
```

---

## 5. Architectural Invariants for AI Agents

1. **Strict Type Safety:** Parameter arguments must match declared JSON Schema types; unvalidated string casts are rejected by FastMCP.
2. **Process Confinement:** Tools invoking child scripts must execute within distinct process groups with timeout handling.
3. **Format Monism:** Render tools compile exclusively to Microsoft Word (`.docx`). Tools emitting PDF or HTML are disallowed.
