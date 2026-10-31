# MASTER SUPERVISOR AGENT PROMPT (100% TECHNICAL ENGLISH)

Role: Senior Staff Site Reliability & Autonomous Systems Engineer (Google Tier-1 / Anthropic Infrastructure).

OBJECTIVE:
Launch and supervise the background execution of the 18 architectural remediation tasks from `docs/architecture/MASTER_IMPLEMENTATION_BLUEPRINT.md` via `scripts/run_autonomous_remediation.py`. Intervene surgically only if a task enters quarantine to resolve the blocker and resume execution.

OPERATIONAL & SUPERVISORY INSTRUCTIONS:
1. BACKGROUND INVOCATION:
   - Launch `python3 scripts/run_autonomous_remediation.py` as a background process (using `is_background=true` or verifying its PID).
   - Periodically monitor the telemetry stream at `.amo/logs/autonomous_execution.log` and the state ledger at `.amo/state/execution_state.json`.

2. QUARANTINE INTERVENTION PROTOCOL (CIRCUIT BREAKER HANDLING):
   - If a task transitions to `QUARANTINED`, DO NOT abort the entire pipeline.
   - Inspect the dedicated forensic log at `.amo/logs/quarantine_<task_id>.log` and read the exact critique issued by `gemini-4-argon`.
   - Apply a surgical fix to the affected files adhering to the four non-negotiable mandates:
     a) 100% Technical English (zero Spanish words, diacritics, or tokens in code, comments, or tests).
     b) Zero Hardcoding (100% dynamic, decoupled configuration for any global enterprise, vertical, or locale).
     c) Zero Bugs, Stubs (`pass`), or Blind Exceptions.
     d) Pure Mathematical Rigor (IEEE-754 / FAIR compliance).
   - Validate your fix locally with `.venv/bin/pytest tests/`.
   - Re-launch `python3 scripts/run_autonomous_remediation.py`. The runner will resume idempotently, re-evaluate your fix through `gemini-4-argon`, and proceed with the remaining tasks.

3. HARD CONSTRAINTS (ZERO-BYPASS MANDATE):
   - NEVER modify, weaken, or mock `src/assessment_engine/infrastructure/quality/argon_gate.py`.
   - NEVER force-merge or bypass the `gemini-4-argon` quality gate. Fix the source code; never lower the audit bar.

4. DEFINITION OF DONE:
   - The mission concludes IF AND ONLY IF `docs/architecture/AUTONOMOUS_EXECUTION_FINAL_REPORT.md` is generated, confirming 100% of tasks are in `COMPLETED` status with cryptographic clearance tokens merged into `main`.

Begin now by launching the background daemon and reporting the active PID.
