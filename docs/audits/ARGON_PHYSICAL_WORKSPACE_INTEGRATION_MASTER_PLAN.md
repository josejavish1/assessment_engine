# MASTER IMPLEMENTATION PLAN: UNIVERSAL SELF-SERVICE WEB COCKPIT & CORE ENGINE CONVERGENCE

**Author:** `gemini-4-argon` (Supreme Cognitive Arbiter & Chief Enterprise Architect)  
**Architectural Mandate:** Zero-Defect Convergence of CLI Batch Pipeline and Real-Time Multi-Tenant Web Cockpit  
**Language & Compliance Standard:** 100% Technical English Codebase | Zero Hardcoding | Physical Workspace Supremacy

---

## 1. PHYSICAL WORKSPACE INTEGRATION ARCHITECTURE

The foundational law of this architecture is **Stateless Compute, Stateful Physical Workspace**. The web server (`server.py`) acts strictly as an asynchronous orchestrator and I/O gateway over the canonical file system hierarchy. Volatile in-memory dictionaries are forbidden as primary state stores.

### 1.1 Directory Topology
Every tenant session maps deterministically to a sanitized `client_slug` (e.g., `cementos-molins`, `starling-bank`, `rede-dor`).

```text
working/
├── [client_slug]/
│   ├── .lock                           # OS-level advisory lock file (fcntl / msvcrt)
│   ├── raw_ingested/                   # Original uploaded Artefact 1 & Artefact 2 files
│   │   ├── context_transcript.docx
│   │   └── assessment_matrix.xlsx
│   ├── client_intelligence.json        # Canonical ClientDossierV3 (Artefact 1 + OSINT)
│   ├── evidence_vault.json             # Extracted forensic chunks & citations
│   ├── digital_twin_state.json         # Real-time maturity ratings & forensic answers (Artefact 2)
│   ├── raptor_tree.json                # Hierarchical summary tree for LLM context injection
│   ├── fair_simulation_results.json    # 10,000 Monte Carlo run actuarial distribution
│   └── pipeline_status.json            # Real-time compilation telemetry & job state
└── out/
    └── [client_slug]/
        ├── Tome_1_AS_IS_Diagnostic_and_Roadmap.docx
        ├── Annex_01_IAM_and_Zero_Trust.docx
        ├── Annex_02_OT_Industrial_Security.docx
        └── ... (Up to 10 Specialized Technical Annexes)
```

### 1.2 Canonical Schema Contracts (Pydantic V2 Strict Mode)

All schemas reside in `src/core/schemas/workspace_contracts.py` and enforce `extra="forbid"` to prevent schema drift.

#### A. `client_intelligence.json` (`ClientDossierV3`)
```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class PerimeterScopeType(str, Enum):
    GLOBAL_HOLDING = "GLOBAL_HOLDING"
    REGIONAL_DIVISION = "REGIONAL_DIVISION"
    SUBSIDIARY_ENTITY = "SUBSIDIARY_ENTITY"
    INDUSTRIAL_FACILITY = "INDUSTRIAL_FACILITY"

class RegulatoryFrameworkSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    framework_id: str = Field(..., description="e.g., NIS2, DORA, LGPD, IEC_62443, FCA_SYSC")
    jurisdiction_iso: str = Field(..., description="ISO 3166-1 alpha-2, e.g., ES, GB, BR, FR")
    enforcement_tier: str = Field(..., description="e.g., Essential Entity, Tier-1 Systemic")
    applicability_rationale: str

class FinancialParameters(BaseModel):
    model_config = ConfigDict(extra="forbid")
    base_currency_iso: str = Field(..., pattern=r"^[A-Z]{3}$", description="e.g., EUR, GBP, BRL, USD")
    annual_revenue_amount: float = Field(..., gt=0)
    ebitda_margin_pct: float = Field(..., ge=-100.0, le=100.0)
    insurable_cyber_limit: float = Field(default=0.0, ge=0.0)

class PerimeterDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope_type: PerimeterScopeType
    target_entity_name: str
    parent_group_name: Optional[str] = None
    employee_headcount: int = Field(..., gt=0)
    operating_countries_iso: List[str]
    critical_assets_summary: List[str]

class ClientDossierV3(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(default="3.0.0", Literal="3.0.0")
    client_slug: str = Field(..., pattern=r"^[a-z0-9\-]+$")
    legal_entity_name: str
    industry_vertical_code: str = Field(..., description="NAICS/GICS mapped taxonomy code")
    primary_hq_country_iso: str = Field(..., pattern=r"^[A-Z]{2}$")
    output_locale: str = Field(..., description="Target deliverable language, e.g., es-ES, en-GB, pt-BR")
    last_updated_utc: datetime
    perimeter: PerimeterDefinition
    financials: FinancialParameters
    regulatory_landscape: List[RegulatoryFrameworkSpec]
    executive_context_synthesis: str = Field(..., description="Consolidated strategic context from Artefact 1")
    strategic_pain_points: List[str]
```

#### B. `evidence_vault.json` (`EvidenceVaultContract`)
```python
class EvidenceSourceType(str, Enum):
    INTERVIEW_TRANSCRIPT = "INTERVIEW_TRANSCRIPT"
    EXECUTIVE_NOTES = "EXECUTIVE_NOTES"
    QUESTIONNAIRE_MATRIX = "QUESTIONNAIRE_MATRIX"
    OSINT_HARVESTER = "OSINT_HARVESTER"

class EvidenceFragment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(..., description="Deterministic SHA-256 prefix, e.g., EV-8F9A2B")
    source_type: EvidenceSourceType
    source_filename: str
    ingestion_timestamp_utc: datetime
    raw_verbatim_text: str
    normalized_claim: str
    mapped_domain_ids: List[str] = Field(..., description="Links to canonical security towers")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    speaker_role: Optional[str] = None

class EvidenceVaultContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_slug: str
    total_fragments: int
    integrity_hash: str
    fragments: List[EvidenceFragment]
```

#### C. `digital_twin_state.json` (`DigitalTwinStateContract`)
```python
class QuestionResponseItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: str
    prompt_key: str = Field(..., description="i18n lookup key in engine_config/locales_ui.json")
    response_text: str
    maturity_indicator: float = Field(..., ge=1.0, le=5.0)
    supporting_evidence_ids: List[str] = Field(default_factory=list)

class SecurityTowerState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tower_id: str = Field(..., description="e.g., DOM_01_GOV, DOM_02_IAM, DOM_03_OT")
    calibrated_maturity_score: float = Field(..., ge=1.0, le=5.0)
    target_to_be_score: float = Field(..., ge=1.0, le=5.0)
    assessor_forensic_notes: str = Field(default="")
    is_applicable: bool = Field(default=True)
    question_responses: List[QuestionResponseItem]

class DigitalTwinStateContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    client_slug: str
    last_synchronized_utc: datetime
    overall_maturity_index: float = Field(..., ge=1.0, le=5.0)
    completion_percentage: float = Field(..., ge=0.0, le=100.0)
    towers: Dict[str, SecurityTowerState]
```

### 1.3 Atomic, Crash-Safe File Persistence (`WorkspacePersistenceManager`)
To guarantee zero corruption under concurrent async FastAPI worker requests and background compilation processes, all disk writes are mediated by `src/core/storage/workspace_manager.py`.

1. **Cross-Platform Advisory Locking:** Uses `portalocker` (wrapping `fcntl.flock` on POSIX and `msvcrt.locking` on Windows) on `working/[client_slug]/.lock` with a 10-second timeout.
2. **Write-Ahead Temp + POSIX Atomic Rename:**
   - Serialize Pydantic model to JSON string (`model.model_dump_json(indent=2)`).
   - Write payload to `working/[client_slug]/.tmp_[filename]_[uuid4].json`.
   - Flush OS buffers (`os.fsync(fd)`).
   - Execute `os.replace(temp_path, target_path)`—guaranteed atomic at the filesystem VFS level.

---

## 2. DUAL-MODE CAPTURE OF THE 2 CORE ARTEFACTS

The platform eliminates the divide between offline consultant workflows and self-service web workflows by converging both into identical workspace mutations.

```
                   +-----------------------------------------+
                   |        ARTEFACT 1: CONTEXT DOSSIER      |
                   +--------------------+--------------------+
                                        |
            +---------------------------+---------------------------+
            | Path A: Interactive UI                                | Path B: Document Drop
            v                                                       v
+-----------------------+                               +-----------------------+
| OSINT Pre-Harvester   |                               | Multi-Format Parser   |
| + Perimeter Selector  |                               | (.docx, .pdf, .txt)   |
| + Live Context Editor |                               | + Chunking Engine     |
+-----------+-----------+                               +-----------+-----------+
            |                                                       |
            +---------------------------+---------------------------+
                                        |
                                        v
                   +-----------------------------------------+
                   |   working/[slug]/client_intelligence    |
                   |   working/[slug]/evidence_vault         |
                   +-----------------------------------------+
```

### 2.1 Artefact 1: Context Dossier (`client_intelligence.json` & `evidence_vault.json`)

#### Path A: Interactive Real-Time Capture
1. **OSINT Pre-Harvesting (`POST /api/workspace/{client_slug}/initialize`):**
   - User inputs Entity Name, HQ Country, Industry Vertical, and Output Locale.
   - Backend invokes `run_intelligence_harvesting.py` in discovery mode, resolving regulatory frameworks dynamically via `engine_config/regulatory_matrix.json` (e.g., mapping `GB` + `FINTECH` $\rightarrow$ `FCA_SYSC`, `PRA_SS2_21`, `DORA`; mapping `BR` + `HEALTHCARE` $\rightarrow$ `LGPD`, `ANVISA`, `CFM`; mapping `ES` + `MANUFACTURING` $\rightarrow$ `NIS2`, `CER`, `IEC_62443`).
2. **Perimeter Selection (`PATCH /api/workspace/{client_slug}/perimeter`):**
   - User toggles `PerimeterScopeType` (`GLOBAL_HOLDING` vs. `SUBSIDIARY_ENTITY` / `INDUSTRIAL_FACILITY`) and adjusts financial baseline parameters (`base_currency_iso`, `annual_revenue_amount`).
3. **Executive Context Recording (`PUT /api/workspace/{client_slug}/context-notes`):**
   - Real-time rich-text notes entered in the cockpit are chunked, assigned deterministic `EV-*` IDs with `source_type="EXECUTIVE_NOTES"`, appended to `evidence_vault.json`, and synthesized into `ClientDossierV3.executive_context_synthesis`.

#### Path B: Document Ingestion (`POST /api/workspace/{client_slug}/ingest/context-document`)
1. **Streaming Multipart Upload:** Accepts `.docx`, `.pdf`, or `.txt` files (e.g., `260721 Transcripción sesion de contexto...docx`).
2. **Raw Preservation:** Saved immediately to `working/[client_slug]/raw_ingested/`.
3. **Forensic Extraction Pipeline:**
   - Invokes `src/core/ingestion/transcript_extractor.py`.
   - Extracts verbatim paragraphs, identifies speaker turns, maps statements to security towers, populates `evidence_vault.json`, and updates `client_intelligence.json` and `raptor_tree.json` identically to the CLI batch pipeline.

### 2.2 Artefact 2: Domain Assessment Responses (`digital_twin_state.json`)

#### Path A: Interactive Cockpit (`PATCH /api/workspace/{client_slug}/digital-twin/tower/{tower_id}`)
1. **Live Calibration:** When the user adjusts a domain slider (1.0 to 5.0) or types answers into the forensic question inputs, the frontend sends a debounced (400ms) PATCH payload.
2. **State Mutation:** `WorkspacePersistenceManager` locks the workspace, updates the specific `SecurityTowerState` inside `digital_twin_state.json`, recalculates `overall_maturity_index` and `completion_percentage`, and returns the updated state vector.

#### Path B: Spreadsheet / Matrix Upload (`POST /api/workspace/{client_slug}/ingest/assessment-matrix`)
1. **Universal Matrix Parser (`src/core/ingestion/matrix_parser.py`):**
   - Accepts `.xlsx` (via `openpyxl`) or structured `.txt`/`.csv` files (e.g., `Preguntas Fast Assessment contestadas.xlsx`).
   - Uses header-agnostic semantic column detection (configured via `engine_config/matrix_column_mappings.json`) to extract Question IDs, Domain mappings, Quantitative Ratings (1–5), and Qualitative Comments.
2. **Bi-Directional Synchronization:**
   - Populates `digital_twin_state.json` with computed tower scores and question responses.
   - Extracts qualitative comments as `EvidenceFragment` entries (`source_type="QUESTIONNAIRE_MATRIX"`) into `evidence_vault.json`.
   - Returns the hydrated `DigitalTwinStateContract` to the frontend, immediately snapping all UI sliders and textboxes to the imported values.

---

## 3. EXECUTION PIPELINE & REAL-TIME SYNTHESIS TRIGGER

When the user clicks **"Synthesize & Generate Deliverables"** in the Web Cockpit, the system transitions from interactive state capture to heavy actuarial and AST document compilation.

### 3.1 Asynchronous Subprocess Orchestration
Because RAPTOR tree construction, 10,000-iteration Monte Carlo FAIR simulations, and LLM-driven AST `.docx` compilation are CPU- and I/O-intensive, they must **never** block the FastAPI asyncio event loop.

1. **Trigger Endpoint (`POST /api/workspace/{client_slug}/compile`):**
   - Validates that `client_intelligence.json`, `evidence_vault.json`, and `digital_twin_state.json` exist and pass Pydantic schema validation.
   - Initializes `working/[client_slug]/pipeline_status.json` with state `QUEUED`.
   - Spawns an isolated background process via `asyncio.create_subprocess_exec`:
     ```python
     proc = await asyncio.create_subprocess_exec(
         sys.executable, "-m", "src.cli.build_client_delivery_suite",
         "--client-slug", client_slug,
         "--workspace-dir", str(workspace_path),
         "--output-dir", str(output_path),
         stdout=asyncio.subprocess.PIPE,
         stderr=asyncio.subprocess.PIPE
     )
     ```
2. **Pipeline Stages Executed by `build_client_delivery_suite.py`:**
   - **Stage 1 (Weight 15%):** Evidence Consolidation & Recursive RAPTOR Tree Indexing (`raptor_tree.json`).
   - **Stage 2 (Weight 20%):** Actuarial FAIR Monte Carlo Engine (10,000 runs parameterized by `ClientDossierV3.financials` and `DigitalTwinStateContract.towers` $\rightarrow$ `fair_simulation_results.json`).
   - **Stage 3 (Weight 35%):** Tome 1 Compilation (`tomo_asis_ast_compiler.py` $\rightarrow$ `Tome_1_AS_IS_Diagnostic_and_Roadmap.docx`).
   - **Stage 4 (Weight 25%):** Specialized Technical Annexes Compilation (Up to 10 domain annexes in `working/out/[client_slug]/`).
   - **Stage 5 (Weight 5%):** Forensic QA Gate (Zero-placeholder regex verification, XML schema validation of generated `.docx` archives).

### 3.2 Real-Time Telemetry via Server-Sent Events (SSE)
- **Endpoint:** `GET /api/workspace/{client_slug}/compile/stream`
- **Mechanism:** Reads `working/[client_slug]/pipeline_status.json` (updated atomically by the subprocess at each sub-step) and streams standardized SSE frames (`text/event-stream`) to the browser:
  ```json
  {
    "job_id": "job-94a1c0",
    "status": "RUNNING",
    "current_stage": "STAGE_3_TOME_1_AST",
    "progress_pct": 58.5,
    "message_key": "pipeline.stage.compiling_tome_1",
    "completed_files": []
  }
  ```

### 3.3 Binary Deliverable Streaming
- **Endpoint:** `GET /api/workspace/{client_slug}/deliverables/{filename}`
- **Security & Streaming:**
  - Sanitizes `filename` via `Path(filename).name` to prevent path traversal (`../`) attacks.
  - Verifies file existence inside `working/out/[client_slug]/`.
  - Streams binary payload via FastAPI `FileResponse` with strict headers:
    - `Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document`
    - `Content-Disposition: attachment; filename="{filename}"`

---

## 4. PHASED IMPLEMENTATION ROADMAP & TEST ORACLES

### Phase 1: Linguistic Purge & Canonical Workspace Contracts
- **Engineering Tasks:**
  1. Audit all `.py`, `.ts`, and `.tsx` files; extract any remaining Spanish string literals into `engine_config/locales_ui.json` and rename all non-English variables/functions/classes to Technical English.
  2. Implement `src/core/schemas/workspace_contracts.py` (`ClientDossierV3`, `EvidenceVaultContract`, `DigitalTwinStateContract`).
  3. Implement `src/core/storage/workspace_manager.py` with `portalocker` and atomic `os.replace` writes.
- **Test Oracle:**
  - Static AST linter (`tests/audit/test_english_purity.py`) scanning all Python/TS AST identifiers and docstrings against Spanish dictionary tokens (Must return `0` violations).
  - Concurrency torture test (`tests/unit/test_workspace_concurrency.py`): 50 parallel async coroutines mutating `digital_twin_state.json` simultaneously with zero JSON decode errors or lost updates.

### Phase 2: Dual-Mode Ingestion Engines (Artefact 1 & Artefact 2)
- **Engineering Tasks:**
  1. Refactor `run_intelligence_harvesting.py` and `transcript_extractor.py` into callable service classes supporting both CLI invocation and FastAPI multipart upload endpoints.
  2. Build `matrix_parser.py` for `.xlsx`/`.txt` questionnaire ingestion into `digital_twin_state.json`.
  3. Remove all hardcoded client references (`molins`, etc.) from backend routers; wire all `/api/workspace/{client_slug}/*` endpoints to `WorkspacePersistenceManager`.
- **Test Oracle:**
  - Integration test ingesting `260721 Transcripción sesion de contexto...docx` and `Preguntas Fast Assessment contestadas.xlsx` via HTTP `POST` and asserting structural equivalence with CLI-generated `client_intelligence.json`, `evidence_vault.json`, and `digital_twin_state.json`.

### Phase 3: Subprocess Synthesis Bridge & Deliverable Streaming
- **Engineering Tasks:**
  1. Implement async subprocess runner in `server.py` invoking `build_client_delivery_suite.py`.
  2. Implement `pipeline_status.json` emitter inside the compiler pipeline and the SSE endpoint `/api/workspace/{client_slug}/compile/stream`.
  3. Wire `/api/workspace/{client_slug}/deliverables/{filename}` to serve real `.docx` artifacts from `working/out/[client_slug]/`.
- **Test Oracle:**
  - Forensic `.docx` inspection test (`tests/integration/test_docx_integrity.py`): Unzips generated `word/document.xml`, parses via `lxml`, asserts zero `{{placeholder}}`, `TODO`, or `None` strings, verifies native Word table structures, and validates currency/regulatory accuracy.

### Phase 4: Multi-Tenant E2E Playwright Verification Suite
- **Engineering Tasks:**
  1. Connect React/TypeScript frontend tabs (Context Setup, Digital Twin Cockpit, Synthesis & Executive Deliverables) to the `/api/workspace/{client_slug}/*` endpoints.
  2. Build automated Playwright E2E test suite (`tests/e2e/multi_tenant_journey.spec.ts`) executing three full end-to-end journeys:
     - **Tenant A (Spain Heavy Manufacturing):** `cementos-molins` | Scope: `GLOBAL_HOLDING` | Currency: `EUR` | Frameworks: `NIS2`, `CER`, `IEC_62443` | Locale: `es-ES`.
     - **Tenant B (UK Digital FinTech):** `starling-bank` | Scope: `GLOBAL_HOLDING` | Currency: `GBP` | Frameworks: `FCA_SYSC`, `PRA_SS2_21`, `DORA` | Locale: `en-GB`.
     - **Tenant C (Brazil Healthcare Network):** `rede-dor` | Scope: `SUBSIDIARY_ENTITY` | Currency: `BRL` | Frameworks: `LGPD`, `ANVISA`, `CFM` | Locale: `pt-BR`.
- **Test Oracle:**
  - All 3 Playwright E2E scenarios complete from workspace creation through real-time compilation to `.docx` binary download with HTTP 200 status, verified physical files in `working/[client_slug]/`, and 100% schema & forensic validation pass rate.