"""
Execute quality gate runner checks, decoupled from adk_lean_factory.py via the Strangler Fig pattern. Provide:
- _run_harness_verification: Run the scripts/verify.sh harness.
- _check_api_and_harness_guards: Verify AST invariants and harness traps.
- _check_closed_loop_web_evals: Run closed-loop red team evaluations (Web/UX/Console).
- execute_quality_gate_step: Run deterministic quality evaluation and manage LATS backtracking.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from google.adk.events import Event, EventActions
from google.genai import types

from assessment_engine.infrastructure.foundry.workspace import ProjectWorkspace

logger = logging.getLogger("assessment_engine.infrastructure.foundry.quality_gate_runner")

DEFAULT_MAX_CYCLES = int(os.environ.get("FACTORY_MAX_CYCLES", "5"))


def _run_harness_verification(workspace: ProjectWorkspace) -> tuple[bool, str, str]:
    """Run the workspace scripts/verify.sh verification harness."""
    verify_script = workspace.workspace_dir / "scripts" / "verify.sh"
    if not verify_script.exists():
        cmd = "MISSING_VERIFY_SCRIPT"
        verify_output = (
            "[EXIT CODE: 1]\n"
            "QUALITY GATE ERROR: Mandatory polyglot verification harness 'scripts/verify.sh' was not created.\n"
            "The Lead Architect must author 'scripts/verify.sh' (chmod 755) containing the project-specific linters, type checks, and tests."
        )
        logger.error(f"Quality gate error: {verify_output}")
        return False, cmd, verify_output

    cmd = "bash scripts/verify.sh"
    logger.info(f"Executing verification harness: {cmd}...")
    res = workspace.execute_bash(cmd)
    if isinstance(res, tuple):
        exit_code, verify_output = res
        is_success = exit_code == 0
    else:
        verify_output = str(res)
        is_success = verify_output.startswith("[EXIT CODE: 0]")
    logger.info(f"Harness output snippet: {verify_output[:400]}")
    return is_success, cmd, verify_output


def _check_api_and_harness_guards(
    workspace: ProjectWorkspace, curr_success: bool, curr_output: str
) -> tuple[bool, str]:
    """Verify that public signatures are not violated and harness traps remain intact."""
    api_violations = workspace.verify_public_api_invariants()
    is_lib = (workspace.workspace_dir / "pyproject.toml").exists() and not (workspace.workspace_dir / "src" / "main.py").exists()
    current_branch = workspace.get_current_branch()
    if api_violations and (is_lib or not current_branch.startswith("feature/")):
        curr_success = False
        violation_summary = "\n[PUBLIC API SIGNATURE VIOLATIONS DETECTED]:\n" + "\n".join(f"- {v}" for v in api_violations)
        curr_output += violation_summary
        logger.error(violation_summary)
    elif api_violations:
        logger.info("[AST SIGNATURE EVOLUTION OBSERVED]: Internal methods evolved consistently within feature branch.")

    harness_violations = workspace.verify_harness_integrity()
    if harness_violations:
        curr_success = False
        violation_summary = "\n[HARNESS WORKAROUND DETECTED]:\n" + "\n".join(f"- {v}" for v in harness_violations)
        curr_output += violation_summary
        logger.error(violation_summary)
    return curr_success, curr_output


def _check_closed_loop_web_evals(
    workspace: ProjectWorkspace, curr_success: bool, curr_output: str
) -> tuple[bool, str]:
    """Run closed-loop browser evaluations for web applications."""
    is_web = (workspace.workspace_dir / ".app_daemon.json").exists() or \
             (workspace.workspace_dir / "public" / "index.html").exists() or \
             (workspace.workspace_dir / "package.json").exists() or \
             (workspace.workspace_dir / "src" / "main.py").exists()

    if curr_success and is_web:
        closed_loop = workspace.run_closed_loop_evals()
        has_fatal_ui_errors = bool(closed_loop.get("network_errors")) or bool(closed_loop.get("page_errors"))
        if has_fatal_ui_errors or (closed_loop.get("status") == "REJECT" and closed_loop.get("ux_score", 10) <= 3):
            curr_success = False
            err_msg = (
                f"\n[CLOSED-LOOP RED TEAM REJECT]:\n"
                f"- Telemetry Network Errors: {closed_loop.get('network_errors', [])}\n"
                f"- Unhandled JS Page Errors: {closed_loop.get('page_errors', [])}\n"
                f"- UX Auditor Critique: {closed_loop.get('persona_verdict', '')}\n"
                f"- Actionable Fixes: {closed_loop.get('actionable_fixes', [])}"
            )
            curr_output += err_msg
            logger.error(f"Closed-loop red team reject: {err_msg}")
        else:
            score = closed_loop.get("ux_score", 10)
            verdict = closed_loop.get("persona_verdict", "Approved")
            logger.info(f"Closed-Loop Red Team Certified (Score: {score}/10): {verdict}")
            workspace.append_veritas_receipt("RED_TEAM_UX_CERTIFIED", {
                "ux_score": score,
                "verdict": verdict,
                "behavioral_delta": closed_loop.get("behavioral_delta", 0)
            }, "PASS")
    return curr_success, curr_output


def execute_quality_gate_step(workspace: ProjectWorkspace) -> Event:
    """Execute the deterministic quality gate step and manage LATS backtracking."""
    workspace.cycle_counter += 1
    logger.info(f"[DETERMINISTIC QUALITY GATE] Cycle {workspace.cycle_counter}/{DEFAULT_MAX_CYCLES} - Project: {workspace.slug}")

    is_success, cmd, verify_output = _run_harness_verification(workspace)
    is_success, verify_output = _check_api_and_harness_guards(workspace, is_success, verify_output)
    is_success, verify_output = _check_closed_loop_web_evals(workspace, is_success, verify_output)

    blast = workspace.get_blast_radius()

    if is_success:
        logger.info("[QUALITY GATE CERTIFIED] Linters, static typing, security, and test coverage (>=90%) fully satisfied.")
        workspace.append_veritas_receipt("QUALITY_GATE_PASS", {
            "command": cmd,
            "exit_code": 0,
            "cycle": workspace.cycle_counter,
            "blast_radius": blast
        }, "VERIFIED")
        workspace.purge_ephemeral_debris()
        workspace.execute_bash("git add . && git commit -m 'feat: verified clean implementation checkpoint'")
        workspace.last_verified_commit = workspace.get_head_sha()
        return Event(
            actions=EventActions(route="pass"),
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text="🛡️ Quality Gate CERTIFICADO: Linters, tipado estricto, seguridad SAST y suite de tests al 100% satisfechos.")]
            )
        )

    workspace.append_veritas_receipt("QUALITY_GATE_FAIL", {
        "command": cmd,
        "cycle": workspace.cycle_counter,
        "blast_radius": blast,
        "error": verify_output[:300]
    }, "REJECTED")

    if workspace.cycle_counter >= DEFAULT_MAX_CYCLES:
        logger.warning(f"[LATS BACKTRACKING] Maximum refinement cycles reached. Rolling back to verified commit {workspace.last_verified_commit}...")
        workspace.append_veritas_receipt("LATS_BACKTRACKING", {
            "cycle": workspace.cycle_counter,
            "rollback_commit": workspace.last_verified_commit,
            "blast_radius": blast
        }, "ROLLBACK")
        if "workspaces" in str(workspace.workspace_dir) and workspace.workspace_dir.name != "workspaces":
            workspace.execute_bash(f"git reset --hard {workspace.last_verified_commit}")
        return Event(actions=EventActions(route="escalate"))

    antibody_file = workspace.synthesize_antibody(verify_output)
    antibody_notice = f"- 🧬 AUTOPSY ANTIBODY SYNTHESIZED: '{antibody_file}' has been added to regression suite.\n" if antibody_file else ""

    workspace.purge_ephemeral_debris()
    workspace.execute_bash(f"git add . && git commit -m 'wip: iteration {workspace.cycle_counter} verification failed' || true")
    repo_map = workspace.get_repo_map("src")

    immediate_trace = verify_output[-2500:] if len(verify_output) > 2500 else verify_output

    feedback = (
        f"QUALITY GATE REJECTION (Cycle {workspace.cycle_counter}/{DEFAULT_MAX_CYCLES}):\n\n"
        f"ITERATION BLAST RADIUS (SCOPE & CHANGE IMPACT):\n"
        f"- Changed Files: {blast['changed_files']}\n"
        f"- Git Stat: {blast['shortstat']}\n\n"
        f"{antibody_notice}"
        f"SYMBOL MAP (REPO MAP):\n{repo_map}\n\n"
        f"IMMEDIATE FAILURE TRACE (CYCLE {workspace.cycle_counter} ONLY - NOISY HISTORY PRUNED):\n{immediate_trace}\n\n"
        "MANDATORY ROOT CAUSE ANALYSIS (RCA) PROTOCOL:\n"
        "1. Focus solely on resolving the immediate failure above without regressing passing components.\n"
        "2. Zero-Patch Invariant: Absolutely NO swallowing exceptions with 'except: pass', suppressing types with 'Any' or '# type: ignore', or deleting failing tests.\n"
        "3. Preserve Public API Invariants: Never delete or alter existing public function signatures in 'src/' without explicit architecture evolution.\n"
        "4. Apply a surgical structural fix in 'src/' using 'replace_in_file' until 'scripts/verify.sh' returns EXIT CODE 0."
    )
    return Event(actions=EventActions(route="retry"), content=types.Content(role="user", parts=[types.Part.from_text(text=feedback)]))
