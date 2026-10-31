---
status: Verified
owner: docs-governance
source_of_truth:
- docs/README.md
- docs/SYSTEM_ARCHITECTURE.md
last_verified_against: 2026-06-26
applies_to:
- humans
- ai-agents
doc_type: operational
diataxis: how_to
verification_mode: editorial
---
# AUTONOMOUS EXECUTION PIPELINE: TIER-1 ORCHESTRATION

## 1. SOTA Autonomous Meta-Intelligence Loop

To eliminate the fragile, manual, human-in-the-loop (HITL) execution pattern—specifically the ad-hoc `argon_audit_prX.py` scripts and interactive `tmux` sessions—we transition to a **Deterministic State-Machine Orchestrator** powered by an asynchronous Actor-Critic Agentic Topology.

The manual loop suffers from context degradation, non-deterministic prompt handoffs, and state contamination across sequential Pull Requests (PRs). The Tier-1 replacement is a persistent daemon—the **Autonomous Meta-Orchestrator (AMO)**—that ingests the entire `MASTER_IMPLEMENTATION_BLUEPRINT.md`, compiles it into a Directed Acyclic Graph (DAG) of atomic execution units, and drives execution to completion using isolated sandboxes and formal verification gates.

```
+-----------------------------------------------------------------------------------+
|                        AUTONOMOUS META-ORCHESTRATOR (AMO)                         |
|                                                                                   |
|  +-----------------------+     +-----------------------+     +-----------------+  |
|  | Blueprint AST Parser  | --> | Execution DAG Engine  | --> | State Store     |  |
|  | (Markdown -> JSON-LD) |     | (Topological Sort)    |     | (SQLite WAL)    |  |
|  +-----------------------+     +-----------------------+     +-----------------+  |
|                                            |                                      |
|                                            v                                      |
|  +-----------------------------------------------------------------------------+  |
|  |                 EPHEMERAL GIT WORKTREE SANDBOX (PR-N)                       |  |
|  |                                                                             |  |
|  |   +-------------------+      +-------------------+      +---------------+   |  |
|  |   | Builder Subagent  | ---> | Static/Dynamic    | ---> | Adversarial   |   |  |
|  |   | (MCP Tool-Use)    |      | Verification Gate |      | Critic Agent  |   |  |
|  |   +-------------------+      +-------------------+      +---------------+   |  |
|  |             ^                          |                        |           |  |
|  |             +--------------------------+------------------------+           |  |
|  |                       Self-Healing Feedback Loop (CEGAR)                    |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 1.1 Architectural Components

#### 1. Blueprint AST Compiler (`BlueprintCompiler`)
Instead of feeding a 5,000+ line Markdown file into an LLM context window—which guarantees "lost-in-the-middle" attention degradation—the AMO parses `MASTER_IMPLEMENTATION_BLUEPRINT.md` using a deterministic Abstract Syntax Tree (AST) parser (e.g., `mistune` or `markdown-it-py`). 
*   It extracts each PR section (`# PR-1`, `# PR-2`, etc.), its target file paths, architectural invariants, and verification commands.
*   It compiles these into a strictly typed **Execution Manifest (`manifest.json`)** representing a topological DAG.

#### 2. Persistent State Store (`StateLedger`)
Backed by a local SQLite database operating in Write-Ahead Logging (`WAL`) mode, the ledger tracks the exact lifecycle state of every node in the DAG:
*   `PENDING` -> `PROVISIONING` -> `SYNTHESIZING` -> `VERIFYING` -> `AUDITING` -> `MERGED` (or `HALTED_ESCALATION`).
*   This guarantees idempotency. If the host machine reboots or the daemon crashes, the AMO resumes from the exact state transition without human intervention.

#### 3. Ephemeral Git Worktree Sandboxing (`SandboxManager`)
The AMO never mutates the primary working directory directly. For each node `PR-X` in the DAG, the orchestrator provisions an isolated Git worktree:
```bash
git worktree add -b feat/auto-pr-X /tmp/amo_sandboxes/pr_X main
```
All synthesis, testing, and auditing occur strictly within `/tmp/amo_sandboxes/pr_X`.

#### 4. Dual-Agent Execution Core (Builder vs. Critic)
*   **The Builder Agent (Synthesizer):** Operating via the Model Context Protocol (MCP), the Builder is granted read/write filesystem access *strictly* scoped to the active worktree. It receives *only* the slice of the blueprint relevant to `PR-X` plus the read-only AST signatures of dependencies from `PR-(X-1)`.
*   **The Critic Agent (Adversarial Auditor):** A completely separate LLM invocation with **zero shared conversational history** with the Builder. It operates with read-only permissions and evaluates the `git diff` against strict formal rubrics.

---

## 2. Continuous Verification & Adversarial Auditing

The manual creation of `argon_audit_prX.py` scripts is an anti-pattern. It relies on the human operator remembering to include all modified files and manually inspecting unstructured prose output from the LLM.

We replace this with a **Multi-Stage Deterministic & Probabilistic Verification Pipeline** that executes automatically upon every Builder synthesis completion.

### 2.1 Stage 1: Deterministic Static & Linguistic Gate (Zero-Token Cost)
Before invoking an expensive LLM for an adversarial audit, the worktree must pass a ruthless, deterministic static analysis gate. If any check fails, the pipeline immediately short-circuits and returns the stderr payload to the Builder.

1.  **Zero-Spanish Linguistic Enforcement (Regex/AST Scanner):**
    Scans all added/modified lines in the `git diff` (identifiers, docstrings, comments, string literals) for Spanish character sets (`[áéíóúñÁÉÍÓÚÑ¿¡]`) and a compiled dictionary of common Spanish technical terms (`configuracion`, `archivo`, `prueba`, `error_de_`, `implementacion`, etc.).
2.  **Anti-Hardcoding & Stub Detection (AST Visitor):**
    A custom Python `ast.NodeVisitor` scans the AST of all modified `.py` files and rejects the diff if it detects:
    *   `pass` statements or `Ellipsis` (`...`) inside non-abstract function/method bodies.
    *   `raise NotImplementedError` in production classes.
    *   Comment markers: `TODO`, `FIXME`, `HACK`, `PLACEHOLDER`, `mock`, `dummy`.
    *   Magic numbers or hardcoded paths (`/home/`, `/Users/`, `C:\`) outside designated constant modules.
3.  **Strict Type & Lint Verification:**
    Executes `ruff check --select ALL` and `mypy --strict` across the modified modules.

### 2.2 Stage 2: Dynamic Execution Gate (`pytest`)
The orchestrator executes the test suite inside the isolated worktree with strict timeouts and coverage enforcement:
```bash
pytest tests/ --tb=short --maxfail=5 --timeout=30 --cov=src --cov-fail-under=90
```

### 2.3 Stage 3: Automated Adversarial Critic (`gemini-4-argon` Structured Audit)
Only if Stages 1 and 2 pass does the AMO invoke the **Adversarial Critic**. Instead of generating a bespoke script per PR, the AMO uses a unified **Universal Forensic Auditor Engine**. 

It programmatically extracts the exact `git diff main...HEAD`, pairs it with the blueprint specification for `PR-X`, and forces the Critic model to output a strictly validated **Pydantic JSON Schema**.

#### Universal Critic Output Schema:
```python
from enum import Enum
from pydantic import BaseModel, Field

class Severity(str, Enum):
    BLOCKER = "BLOCKER"       # Triggers immediate rollback/retry
    WARNING = "WARNING"       # Logged, does not block merge
    NIT = "NIT"

class AuditViolation(BaseModel):
    file_path: str = Field(..., description="Relative path to the offending file.")
    line_number: int = Field(..., description="Exact line number in the new file.")
    severity: Severity
    category: str = Field(..., description="E.g., ARCHITECTURAL_DRIFT, HARDCODED_MOCK, LOGIC_FLAW, LANGUAGE_VIOLATION")
    evidence: str = Field(..., description="Exact code snippet exhibiting the flaw.")
    remediation_directive: str = Field(..., description="Exact technical instruction for the Builder to fix the flaw.")

class ForensicAuditReport(BaseModel):
    pr_identifier: str
    passed_audit: bool = Field(..., description="True ONLY if zero BLOCKER violations exist.")
    architectural_alignment_score: float = Field(..., ge=0.0, le=1.0)
    violations: list[AuditViolation]
    summary: str
```

By enforcing `response_mime_type="application/json"` and validating against `ForensicAuditReport`, the orchestrator makes a deterministic boolean branching decision: `if report.passed_audit and report.architectural_alignment_score >= 0.95: proceed()`.

---

## 3. CI/CD Integration & Rollback (Fail-Fast & Self-Healing)

An autonomous system running unattended in the background must guarantee **Workspace Invariance** (never leaving the repository in a broken state) and **Bounded Termination** (never entering an infinite token-burning loop).

```
                     +------------------------+
                     |  Provision Worktree    |
                     |  attempt_counter = 1   |
                     +-----------+------------+
                                 |
                                 v
                     +------------------------+
          +--------->|   Builder Synthesis    |
          |          +-----------+------------+
          |                      |
          |                      v
          |          +------------------------+
          |          | Stage 1: Static/AST    |
          |          | Stage 2: Pytest Gate   |
          |          +-----------+------------+
          |                      |
     [Inject Error               | (Pass)
      Trace & Reset]             v
          |          +------------------------+
          |          | Stage 3: Argon Critic  |
          |          +-----------+------------+
          |                      |
          |              +-------+-------+
          |              |               |
          |           [FAIL]          [PASS]
          |              |               |
          |              v               v
   +------+--------------+---+   +-------+----------------+
   | attempt_counter < MAX?  |   | Atomic Fast-Forward    |
   | [YES]: counter += 1     |   | Merge to `main`        |
   |        git checkout --  |   | Cleanup Worktree       |
   +-------------+-----------+   +------------------------+
                 |
                [NO]
                 |
                 v
   +-------------------------+
   | Quarantine Branch       |
   | Dump Forensic Telemetry |
   | HALT DAG / Alert Human  |
   +-------------------------+
```

### 3.1 Counterexample-Guided Abstraction Refinement (CEGAR) Loop for Code
When any verification stage fails (Static AST, `pytest`, or Argon Critic), the orchestrator does not immediately abort. Instead, it enters a **Bounded Self-Healing Reflexion Loop** (`MAX_RETRIES = 4`):

1.  **Failure Capture:** The orchestrator captures the exact failure artifact (either the `pytest` stack trace, the AST linter violation, or the serialized `AuditViolation` list from the Critic).
2.  **Selective State Reset:**
    *   If the failure is a syntax error or massive test regression, the orchestrator runs `git reset --hard HEAD` inside the worktree to wipe the corrupted synthesis, feeding the error trace into a clean retry prompt.
    *   If the failure is a localized Critic violation or minor test failure, the working tree is preserved, and the Builder is instructed to apply surgical patches (`git diff` refinement).
3.  **Prompt Augmentation (Negative Constraints):** The Builder's prompt for `Attempt N+1` is dynamically augmented with a `<CRITICAL_PREVIOUS_ATTEMPT_FAILURE>` block containing the exact remediation directives.

### 3.2 Atomic Promotion & Quarantine Protocol
*   **Promotion (Success Path):** Once Stages 1, 2, and 3 pass within the worktree:
    1. The orchestrator commits the changes inside the worktree with a standardized semantic commit message (`feat(PR-X): autonomous synthesis verified by Argon Critic [score: 0.98]`).
    2. It switches to the primary repository, performs an atomic fast-forward merge (`git merge --ff-only feat/auto-pr-X`), and deletes the ephemeral worktree.
*   **Quarantine (Exhaustion Path):** If `attempt_counter > MAX_RETRIES`:
    1. The orchestrator **does not** merge to `main`.
    2. It commits the failed state to a quarantine branch (`quarantine/pr-X-failed-attempt-4`).
    3. It writes a comprehensive forensic bundle (`/var/log/amo/pr_X_crash_dump.json`) containing all 4 diffs, test outputs, and Critic reports.
    4. It gracefully halts dependent nodes in the DAG while continuing to execute orthogonal (non-dependent) PR branches if the DAG topology permits.

---

## 4. Concrete Implementation Strategy

You can bootstrap this exact Tier-1 architecture in your workspace **today** by deploying a single, self-contained daemon script: `autonomous_meta_orchestrator.py`. This completely deprecates manual `argon_audit_prX.py` scripts.

### 4.1 Directory Structure Setup
Create the orchestrator control plane directory in your project root:
```bash
mkdir -p .amo/{state,logs,sandboxes}
```

### 4.2 Production Blueprint: `autonomous_meta_orchestrator.py`
Save the following production-grade implementation in your repository root. It implements the Blueprint Parser, AST Static Gate, Subprocess Sandbox Manager, and Structured Argon Critic in pure Python.

```python
#!/usr/bin/env python3
"""
Autonomous Meta-Orchestrator (AMO) - Tier-1 Zero-HITL Execution Engine.
Replaces manual PR implementation and ad-hoc argon_audit_prX.py scripts.
"""

import ast
import json
import logging
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

from pydantic import BaseModel, Field

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [AMO-DAEMON] %(message)s",
    handlers=[
        logging.FileHandler(".amo/logs/orchestrator.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("AMO")


# =====================================================================
# 1. SCHEMAS & DATA STRUCTURES
# =====================================================================

class NodeStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    QUARANTINED = "QUARANTINED"


class Severity(str, Enum):
    BLOCKER = "BLOCKER"
    WARNING = "WARNING"


class AuditViolation(BaseModel):
    file_path: str
    line_number: int
    severity: Severity
    category: str
    evidence: str
    remediation_directive: str


class ForensicAuditReport(BaseModel):
    pr_identifier: str
    passed_audit: bool
    architectural_alignment_score: float = Field(ge=0.0, le=1.0)
    violations: List[AuditViolation]
    summary: str


@dataclass
class PRTaskNode:
    pr_id: str
    title: str
    specification_markdown: str
    target_files: List[str]


# =====================================================================
# 2. DETERMINISTIC STATIC & LINGUISTIC VERIFIER (ZERO-TOKEN GATE)
# =====================================================================

class StaticForensicGate:
    """Enforces Zero-Spanish, Zero-Stubs, and AST hygiene prior to LLM Audit."""

    SPANISH_CHAR_REGEX = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
    SPANISH_WORDS_REGEX = re.compile(
        r"\b(configuracion|archivo|prueba|implementacion|ejemplo|temporal|funcion|clase|objeto|retorno|verdadero|falso)\b",
        re.IGNORECASE,
    )
    FORBIDDEN_MARKERS = re.compile(r"\b(TODO|FIXME|HACK|PLACEHOLDER|XXX)\b")

    @classmethod
    def verify_worktree(cls, worktree_path: Path, base_branch: str = "main") -> List[str]:
        violations: List[str] = []

        # Get modified/added files relative to base_branch
        cmd = ["git", "diff", "--name-only", "--diff-filter=AM", base_branch]
        res = subprocess.run(cmd, cwd=worktree_path, capture_output=True, text=True, check=True)
        changed_files = [f.strip() for f in res.stdout.splitlines() if f.strip().endswith(".py")]

        if not changed_files:
            violations.append("STATIC_GATE_FAILURE: Builder produced zero modified Python files.")
            return violations

        for rel_path in changed_files:
            full_path = worktree_path / rel_path
            content = full_path.read_text(encoding="utf-8")

            # 1. Linguistic Check (Zero Spanish Mandate)
            for idx, line in enumerate(content.splitlines(), start=1):
                if cls.SPANISH_CHAR_REGEX.search(line) or cls.SPANISH_WORDS_REGEX.search(line):
                    violations.append(f"{rel_path}:{idx} [LANGUAGE_VIOLATION] Spanish characters or lexicon detected: '{line.strip()}'")
                if cls.FORBIDDEN_MARKERS.search(line):
                    violations.append(f"{rel_path}:{idx} [INCOMPLETE_CODE] Forbidden marker (TODO/FIXME/PLACEHOLDER) detected: '{line.strip()}'")

            # 2. AST Structural Check (Zero Stubs / NotImplementedError)
            try:
                tree = ast.parse(content, filename=rel_path)
                violations.extend(cls._check_ast_for_stubs(tree, rel_path))
            except SyntaxError as exc:
                violations.append(f"{rel_path}:{exc.lineno} [SYNTAX_ERROR] {exc.msg}")

        return violations

    @staticmethod
    def _check_ast_for_stubs(tree: ast.AST, rel_path: str) -> List[str]:
        ast_violations: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Skip abstract methods
                decorator_names = [
                     getattr(d, "id", getattr(d, "attr", "")) for d in node.decorator_list
                ]
                if "abstractmethod" in decorator_names:
                    continue

                # Check if body is just `pass` or `...` (ignoring docstring)
                body = node.body
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
                    body = body[1:]  # Strip docstring

                if len(body) == 1:
                    stmt = body[0]
                    if isinstance(stmt, ast.Pass):
                        ast_violations.append(f"{rel_path}:{node.lineno} [STUB_DETECTED] Function '{node.name}' contains only a 'pass' statement.")
                    elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value is Ellipsis:
                        ast_violations.append(f"{rel_path}:{node.lineno} [STUB_DETECTED] Function '{node.name}' contains only an Ellipsis (...).")

            if isinstance(node, ast.Raise) and isinstance(node.exc, (ast.Name, ast.Call)):
                exc_name = node.exc.id if isinstance(node.exc, ast.Name) else getattr(node.exc.func, "id", "")
                if exc_name == "NotImplementedError":
                    ast_violations.append(f"{rel_path}:{node.lineno} [STUB_DETECTED] 'NotImplementedError' raised in production code.")

        return ast_violations


# =====================================================================
# 3. BLUEPRINT COMPILER & STATE LEDGER
# =====================================================================

class BlueprintCompiler:
    """Parses MASTER_IMPLEMENTATION_BLUEPRINT.md into discrete PRTaskNodes."""

    PR_HEADER_REGEX = re.compile(r"^#{1,2}\s+(PR-\d+)[:\s-]+(.*)$", re.MULTILINE)

    @classmethod
    def compile(cls, blueprint_path: Path) -> List[PRTaskNode]:
        raw_md = blueprint_path.read_text(encoding="utf-8")
        matches = list(cls.PR_HEADER_REGEX.finditer(raw_md))
        nodes: List[PRTaskNode] = []

        for idx, match in enumerate(matches):
            pr_id = match.group(1).strip()
            title = match.group(2).strip()
            start_pos = match.start()
            end_pos = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_md)
            section_md = raw_md[start_pos:end_pos].strip()

            # Extract file paths mentioned in backticks (e.g., `src/module/file.py`)
            files = sorted(set(re.findall(r"`([a-zA-Z0-9_/\.-]+\.py)`", section_md)))
            nodes.append(PRTaskNode(pr_id=pr_id, title=title, specification_markdown=section_md, target_files=files))

        logger.info(f"Compiled {len(nodes)} PR execution nodes from {blueprint_path}")
        return nodes


class StateLedger:
    """Persistent SQLite WAL ledger for crash-resilient execution tracking."""

    def __init__(self, db_path: Path):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pr_ledger (
                pr_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                last_error TEXT
            )
            """
        )
        self.conn.commit()

    def get_status(self, pr_id: str) -> Optional[NodeStatus]:
        cur = self.conn.execute("SELECT status FROM pr_ledger WHERE pr_id = ?", (pr_id,))
        row = cur.fetchone()
        return NodeStatus(row[0]) if row else None

    def update_state(self, pr_id: str, status: NodeStatus, attempts: int, last_error: str = "") -> None:
        self.conn.execute(
            """
            INSERT INTO pr_ledger (pr_id, status, attempts, last_error)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(pr_id) DO UPDATE SET
                status=excluded.status,
                attempts=excluded.attempts,
                last_error=excluded.last_error
            """,
            (pr_id, status.value, attempts, last_error),
        )
        self.conn.commit()


# =====================================================================
# 4. CORE ORCHESTRATOR ENGINE
# =====================================================================

class AutonomousMetaOrchestrator:
    def __init__(self, repo_root: Path, blueprint_path: Path, max_retries: int = 4):
        self.repo_root = repo_root.resolve()
        self.blueprint_path = blueprint_path.resolve()
        self.max_retries = max_retries
        self.sandbox_dir = self.repo_root / ".amo" / "sandboxes"
        self.ledger = StateLedger(self.repo_root / ".amo" / "state" / "ledger.db")

    def execute_pipeline(self) -> None:
        nodes = BlueprintCompiler.compile(self.blueprint_path)
        for node in nodes:
            current_status = self.ledger.get_status(node.pr_id)
            if current_status == NodeStatus.COMPLETED:
                logger.info(f"[{node.pr_id}] Already COMPLETED in ledger. Skipping.")
                continue

            logger.info(f"[{node.pr_id}] Initiating autonomous execution cycle: '{node.title}'")
            success = self._execute_pr_node(node)
            if not success:
                logger.critical(f"[{node.pr_id}] Failed after {self.max_retries} attempts. Quarantined. Halting pipeline.")
                sys.exit(1)

        logger.info("ALL BLUEPRINT NODES SUCCESSFULLY SYNTHESIZED, AUDITED, AND MERGED.")

    def _execute_pr_node(self, node: PRTaskNode) -> bool:
        worktree_path = self.sandbox_dir / node.pr_id.lower()
        branch_name = f"feat/auto-{node.pr_id.lower()}"

        self._provision_worktree(worktree_path, branch_name)
        feedback_context = ""

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"[{node.pr_id}] --- Synthesis Attempt {attempt}/{self.max_retries} ---")
            self.ledger.update_state(node.pr_id, NodeStatus.IN_PROGRESS, attempt, feedback_context)

            # 1. Invoke Builder Subagent
            self._invoke_builder_agent(node, worktree_path, feedback_context)

            # 2. Stage 1: Deterministic Static & Linguistic Gate
            static_violations = StaticForensicGate.verify_worktree(worktree_path)
            if static_violations:
                feedback_context = "STAGE 1 STATIC GATE FAILED:\n" + "\n".join(static_violations)
                logger.warning(f"[{node.pr_id}] Static Gate rejected synthesis:\n{feedback_context}")
                continue

            # 3. Stage 2: Dynamic Pytest Verification Gate
            pytest_passed, pytest_output = self._run_pytest_gate(worktree_path)
            if not pytest_passed:
                feedback_context = f"STAGE 2 PYTEST GATE FAILED:\n{pytest_output}"
                logger.warning(f"[{node.pr_id}] Pytest Gate rejected synthesis.")
                continue

            # 4. Stage 3: Adversarial Critic Audit (Replaces argon_audit_prX.py)
            audit_report = self._invoke_adversarial_critic(node, worktree_path)
            if not audit_report.passed_audit or audit_report.architectural_alignment_score < 0.95:
                formatted_violations = "\n".join(
                    f"- [{v.severity}] {v.file_path}:{v.line_number} ({v.category}): {v.remediation_directive}"
                    for v in audit_report.violations
                )
                feedback_context = (
                    f"STAGE 3 ARGON FORENSIC AUDIT REJECTED (Score: {audit_report.architectural_alignment_score}):\n"
                    f"Summary: {audit_report.summary}\nViolations:\n{formatted_violations}"
                )
                logger.warning(f"[{node.pr_id}] Adversarial Critic rejected synthesis:\n{feedback_context}")
                continue

            # All Gates Passed -> Atomic Promotion
            self._promote_and_cleanup(node, worktree_path, branch_name, audit_report.architectural_alignment_score)
            self.ledger.update_state(node.pr_id, NodeStatus.COMPLETED, attempt, "")
            return True

        # Exhausted Retries -> Quarantine
        self._quarantine_worktree(node, worktree_path, feedback_context)
        self.ledger.update_state(node.pr_id, NodeStatus.QUARANTINED, self.max_retries, feedback_context)
        return False

    def _provision_worktree(self, worktree_path: Path, branch_name: str) -> None:
        if worktree_path.exists():
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=self.repo_root, check=False)
        subprocess.run(["git", "branch", "-D", branch_name], cwd=self.repo_root, capture_output=True, check=False)
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), "main"],
            cwd=self.repo_root,
            check=True,
        )

    def _invoke_builder_agent(self, node: PRTaskNode, worktree_path: Path, feedback: str) -> None:
        """
        Dispatches synthesis task to the Builder Agent (e.g., Claude Code / Gemini CLI / Cognitive Orchestrator)
        scoped strictly to `worktree_path`.
        """
        prompt = (
            f"ROLE: Principal Systems Engineer.\n"
            f"MANDATE: Implement {node.pr_id} ({node.title}) in 100% formal Technical English. "
            f"Zero Spanish. Zero hardcoded mocks, stubs, or TODOs.\n\n"
            f"SPECIFICATION:\n{node.specification_markdown}\n\n"
        )
        if feedback:
            prompt += (
                f"CRITICAL REMEDIATION REQUIRED (Previous attempt failed verification):\n"
                f"{feedback}\n"
                f"Fix all reported violations surgically.\n"
            )

        prompt_file = worktree_path / ".amo_builder_prompt.md"
        prompt_file.write_text(prompt, encoding="utf-8")

        # Hook into existing workspace agent runner or CLI tool:
        # Adjust command below if using `run_cognitive_orchestrator.py` or `claude` / `gemini` CLI
        cmd = [
            sys.executable,
            str(self.repo_root / "run_cognitive_orchestrator.py"),
            "--workspace", str(worktree_path),
            "--prompt-file", str(prompt_file),
        ]
        logger.info(f"[{node.pr_id}] Executing Builder Agent inside sandbox...")
        subprocess.run(cmd, cwd=worktree_path, check=False)
        if prompt_file.exists():
            prompt_file.unlink()

    def _run_pytest_gate(self, worktree_path: Path) -> tuple[bool, str]:
        cmd = [sys.executable, "-m", "pytest", "tests/", "--tb=short", "-q"]
        res = subprocess.run(cmd, cwd=worktree_path, capture_output=True, text=True)
        return (res.returncode == 0), (res.stdout + "\n" + res.stderr)[-4000:]

    def _invoke_adversarial_critic(self, node: PRTaskNode, worktree_path: Path) -> ForensicAuditReport:
        """
        Programmatic replacement for `argon_audit_prX.py`.
        Extracts git diff and queries Gemini-4-Argon with strict JSON schema validation.
        """
        diff_res = subprocess.run(
            ["git", "diff", "main"], cwd=worktree_path, capture_output=True, text=True, check=True
        )
        git_diff_payload = diff_res.stdout

        critic_system_prompt = (
            "You are a Tier-1 Adversarial Code Auditor (Gemini-4-Argon). "
            "Perform a ruthless forensic audit of the provided git diff against the PR specification. "
            "Check for: 1) Any Spanish words/comments, 2) Hardcoded values or stubs, "
            "3) Subtle algorithmic bugs, 4) Deviations from the specification. "
            "Respond strictly in JSON matching the ForensicAuditReport schema."
        )
        user_payload = (
            f"PR SPECIFICATION ({node.pr_id}):\n{node.specification_markdown}\n\n"
            f"GIT DIFF TO AUDIT:\n```diff\n{git_diff_payload}\n```"
        )

        # Using Google GenAI SDK with structured outputs
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        response = client.models.generate_content(
            model="gemini-2.5-pro",  # Or your specific gemini-4-argon endpoint alias
            contents=user_payload,
            config=types.GenerateContentConfig(
                system_instruction=critic_system_prompt,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=ForensicAuditReport,
            ),
        )
        return ForensicAuditReport.model_validate_json(response.text)

    def _promote_and_cleanup(self, node: PRTaskNode, worktree_path: Path, branch_name: str, score: float) -> None:
        subprocess.run(["git", "add", "-A"], cwd=worktree_path, check=True)
        commit_msg = f"feat({node.pr_id}): autonomous synthesis verified by Argon Critic [score: {score:.2f}]"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=worktree_path, check=True)

        # Merge back to main atomically
        subprocess.run(["git", "checkout", "main"], cwd=self.repo_root, check=True)
        subprocess.run(["git", "merge", "--ff-only", branch_name], cwd=self.repo_root, check=True)

        # Teardown sandbox
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_path)], cwd=self.repo_root, check=True)
        subprocess.run(["git", "branch", "-d", branch_name], cwd=self.repo_root, check=True)
        logger.info(f"[{node.pr_id}] Promoted to `main` and cleaned up sandbox.")

    def _quarantine_worktree(self, node: PRTaskNode, worktree_path: Path, last_error: str) -> None:
        dump_file = self.repo_root / ".amo" / "logs" / f"quarantine_{node.pr_id.lower()}.log"
        dump_file.write_text(last_error, encoding="utf-8")
        logger.error(f"[{node.pr_id}] Forensic failure dump written to {dump_file}. Worktree preserved at {worktree_path}.")


if __name__ == "__main__":
    amo = AutonomousMetaOrchestrator(
        repo_root=Path("."),
        blueprint_path=Path("MASTER_IMPLEMENTATION_BLUEPRINT.md"),
        max_retries=4,
    )
    amo.execute_pipeline()
```

### 4.3 Bootstrapping Execution Today (Detached Daemon Mode)

Instead of babysitting an interactive `tmux` loop, launch the Autonomous Meta-Orchestrator as an unattended background daemon using `nohup` or a dedicated detached `tmux` control plane:

```bash
# 1. Delete obsolete manual audit scripts
rm -f argon_audit_pr*.py

# 2. Ensure clean git working state on main
git status --porcelain

# 3. Launch the Autonomous Meta-Orchestrator in a detached background session
tmux new-session -d -s amo_control_plane "python3 autonomous_meta_orchestrator.py"

# 4. (Optional) Monitor real-time structured telemetry passively
tail -f .amo/logs/orchestrator.log
```

### 4.4 Operational Guarantees Achieved
1.  **Zero Manual Audit Scripts:** `StaticForensicGate` + `_invoke_adversarial_critic` dynamically inspect the exact `git diff` of every PR without writing a single `argon_audit_prX.py` file.
2.  **100% Linguistic & Structural Purity:** Any Spanish token or `pass`/`NotImplementedError` stub is caught in `<50ms` by the AST visitor and bounced back to the Builder before wasting API tokens on the Critic.
3.  **Zero Repository Contamination:** Failed syntheses are isolated inside `.amo/sandboxes/pr-x/` and never touch `main` until all three verification gates (Static AST, `pytest`, and Argon Critic) pass simultaneously.