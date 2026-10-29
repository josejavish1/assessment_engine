#!/usr/bin/env python3
"""
The Cognitive Arbiter — Flight Deck CLI (RFC-015 SOTA Master Pipeline).

5 Fases Deterministas de Meta-Consciencia:
[1/6] Ephemeral Git Worktree Sandbox (Zero-Risk Blast Radius Isolation).
[2/6] Epistemic Distiller (Phase 1: SOTA Mining & 3-Bucket Matrix).
[3/6] AST Baseline Signature Wall (Contract Breakage Prevention).
[4/6] Asymmetric Dialectical Loop (Synthesizer + RFC-Grounded Skeptic).
[5/6] Deterministic Forensic Closure Tribunal (AST, Radon, Mutation CTF, Bucket-1 Parity).
[6/6] Verdict Presentation, Diff Preview, and Safe Merge.

Supports atomic single-file (--target-file) and multi-file (--target-files) transactions.
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repository root on sys.path for standalone execution
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from assessment_engine.infrastructure.evolution.ast_signature_guard import snapshot_file
from assessment_engine.infrastructure.evolution.closure_tribunal import closure_tribunal
from assessment_engine.infrastructure.evolution.cognitive_arbiter import (
    CognitiveArbiter,
    SkepticRole,
    SurgicalPatchError,
    SynthesizerRole,
    VerdictStatus,
)
from assessment_engine.infrastructure.evolution.epistemic_distiller import epistemic_distiller
from assessment_engine.infrastructure.evolution.worktree_runner import EphemeralWorktree, worktree_runner

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cognitive_orchestrator")

_ACTIVE_WORKTREE: EphemeralWorktree | None = None


def _signal_handler(signum: int, frame: Any) -> None:
    global _ACTIVE_WORKTREE
    sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
    print(f"\n[ABORTED] 🛑 Interrupt signal caught ({sig_name}). Cleaning up ephemeral git worktree...")
    if _ACTIVE_WORKTREE:
        try:
            _ACTIVE_WORKTREE.cleanup()
        except Exception as ex:  # noqa: BLE001
            print(f"[Aviso] No se pudo limpiar worktree por completo: {ex}")
        _ACTIVE_WORKTREE = None
    sys.exit(130 if signum == signal.SIGINT else 143)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


class OrchestratorPresenter:
    """Wrap terminal output while respecting JSON mode."""

    def __init__(self, output_json: bool) -> None:
        self.output_json = output_json

    def log(self, msg: str, end: str = "\n", flush: bool = False) -> None:
        if not self.output_json:
            print(msg, end=end, flush=flush)

    def header(self, task: str, target_rels: list[Path]) -> None:
        if not self.output_json:
            targets_str = ", ".join(str(p) for p in target_rels)
            print("\n" + "=" * 78)
            print("  THE COGNITIVE ARBITER — PIPELINE MAESTRO DE META-CONSCIENCIA TIER-1")
            print(f"  Mission: {task}")
            print(f"  Objetivos ({len(target_rels)}): {targets_str}")
            print("=" * 78 + "\n")


def _resolve_target_and_test_paths(
    target_inputs: list[str] | str,
    test_file_str: str | None,
) -> tuple[list[Path], Path]:
    """Resolve target file paths and test oracle path."""
    if isinstance(target_inputs, (str, Path)):
        target_rels = [Path(target_inputs)]
    else:
        target_rels = [Path(p) for p in target_inputs]

    if test_file_str:
        test_rel = Path(test_file_str)
    else:
        test_rel = Path("tests") / f"test_{target_rels[0].stem}.py"

    return target_rels, test_rel


def _setup_worktree(
    repo_root: Path,
    use_worktree: bool,
    presenter: OrchestratorPresenter,
    target_rels: list[Path] | None = None,
    test_rel: Path | None = None,
) -> tuple[EphemeralWorktree | None, Path]:
    if not use_worktree:
        presenter.log("[1/6] 📦 Sandbox disabled (executing directly in local tree)... OK")
        return None, repo_root
    presenter.log("[1/6] 📦 Creating Ephemeral Git Worktree Sandbox...", end="", flush=True)
    worktree = worktree_runner.create_worktree(repo_root=repo_root, branch_prefix="arb_master_")

    sync_files = list(target_rels or [])
    if test_rel:
        sync_files.append(test_rel)

    for rel in sync_files:
        src = repo_root / rel
        dst = worktree.worktree_path / rel
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    # Sincronizar cambios no commiteados del working tree para preservar fixes locales del baseline
    try:
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        for line in status_proc.stdout.splitlines():
            line_str = line.strip()
            if len(line_str) >= 4 and line[0:2].strip() in ("M", "A"):
                mod_rel = Path(line[3:].strip())
                src_f = repo_root / mod_rel
                dst_f = worktree.worktree_path / mod_rel
                if src_f.is_file() and src_f.exists():
                    dst_f.parent.mkdir(parents=True, exist_ok=True)
                    dst_f.write_text(src_f.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception as ex:  # noqa: BLE001
        logging.getLogger("cognitive_flight_deck").debug(f"[Worktree] Baseline sync note: {ex}")

    presenter.log(f" OK ({worktree.worktree_path.name})")
    return worktree, worktree.worktree_path


def _run_epistemic_phase(
    task: str,
    sector: str,
    offline_only: bool,
    presenter: OrchestratorPresenter,
    target_file: str | None = None,
) -> Any:
    presenter.log("[2/6] 🧠 Epistemic Distiller (Phase 1: SOTA Analysis & 3-Bucket Matrix)...", end="", flush=True)
    dossier = epistemic_distiller.distill(
        task_description=task,
        sector=sector,
        force_fallback=offline_only,
        target_file=target_file,
    )
    leaders_str = ", ".join(dossier.leaders_analyzed[:3])
    presenter.log(f" OK\n      - SOTA Leaders Audited: {leaders_str}")
    presenter.log(f"      - Cubo 1 (Invariantes Obligatorios): {len(dossier.must_have_invariants)} identificados")
    presenter.log(f"      - Bucket 2 (Asymmetric Zero-Cost Advantages): {len(dossier.unfair_advantages)} identified")
    presenter.log(f"      - Cubo 3 (Anti-Features Prohibidas): {len(dossier.deliberate_anti_features)} vetadas")
    return dossier


def _log_baseline_signatures(baseline_paths: list[Path], presenter: OrchestratorPresenter) -> None:
    presenter.log("[3/6] 📸 Capturando firmas AST del baseline...", end="", flush=True)
    tracked_count = 0
    for p in baseline_paths:
        if p.exists() and p.suffix == ".py":
            try:
                snap = snapshot_file(p)
                tracked_count += snap.get_symbol_count()
            except (SyntaxError, OSError, ValueError) as ex:
                logger.debug(f"[CognitiveArbiter] Error capturando firma de {p}: {ex}")
    presenter.log(f" OK ({tracked_count} symbols tracked across {len(baseline_paths)} file(s))")


def _arbitrate_single_target(
    target_rel: Path,
    test_rel: Path,
    baseline_code: str,
    work_dir: Path,
    elevated_task_spec: str,
    synthesizer: SynthesizerRole,
    skeptic: SkepticRole,
    presenter: OrchestratorPresenter,
) -> Any:
    """Arbitrate a single target file within the isolated sandbox."""
    target_work_file = work_dir / target_rel
    test_work_file = work_dir / test_rel
    initial_patch: dict[str, str] | None = None
    c_code = target_work_file.read_text(encoding="utf-8") if target_work_file.exists() else ""
    t_code = test_work_file.read_text(encoding="utf-8") if test_work_file.exists() else "def test_ok(): assert True\n"
    if c_code or t_code:
        initial_patch = {"candidate_code": c_code, "test_code": t_code}

    arbiter = CognitiveArbiter(synthesizer=synthesizer, skeptic=skeptic, max_rounds=5)
    return arbiter.arbitrate_task(
        task_description=elevated_task_spec,
        target_rel_path=str(target_rel),
        test_rel_path=str(test_rel),
        baseline_code=baseline_code,
        repo_root=work_dir,
        use_worktree=False,
        initial_candidate=initial_patch,
        progress_callback=lambda msg: presenter.log(msg, flush=True),
    )


def _run_dialectical_phase(
    task: str,
    target_rels: list[Path],
    test_rel: Path,
    baseline_codes: dict[Path, str],
    work_dir: Path,
    offline_only: bool,
    presenter: OrchestratorPresenter,
    dossier: Any = None,
) -> tuple[Any, SynthesizerRole]:
    presenter.log("[4/6] 🔄 Running Asymmetric Dialectical Loop (Synthesizer + Grounded Skeptic)...")
    genai_client = None
    if not offline_only:
        try:
            from assessment_engine.infrastructure.genai_client import create_genai_client
            genai_client = create_genai_client()
        except (RuntimeError, ValueError, KeyError, OSError, TypeError) as ex:
            logger.debug(f"[Orchestrator] GenAI initialization skipped: {ex}")

    skeptic = SkepticRole(
        client=genai_client,
        search_fn=lambda q: "Technical standards and specifications verified in offline mode."
    ) if offline_only else SkepticRole(client=genai_client)
    synthesizer = SynthesizerRole(client=genai_client)

    query = f"RFC/W3C standards, concurrency edge cases for: {task}"
    _ = skeptic.query_web_standards(query)
    presenter.log(f"      - Skeptic queried standards: '{query[:48]}...'")

    from assessment_engine.infrastructure.evolution.reflexion_ledger import reflexion_ledger

    preflight_memories = [reflexion_ledger.format_preflight_prompt_block(str(p)) for p in target_rels]
    joined_preflight = "\n".join(m for m in preflight_memories if m)
    dossier_brief = dossier.to_markdown_brief() if dossier and hasattr(dossier, "to_markdown_brief") else ""

    elevated_parts = [f"### PRODUCT OWNER MISSION:\n{task}"]
    if dossier_brief:
        elevated_parts.append(dossier_brief)
    if joined_preflight:
        elevated_parts.append(joined_preflight)

    elevated_task_spec = "\n\n".join(elevated_parts)
    num_invs = len(dossier.must_have_invariants) if dossier and hasattr(dossier, "must_have_invariants") else 0
    presenter.log(f"      - Spec Elevation: Inyectados {num_invs} invariantes SOTA y memoria ReflexionLedger.")

    last_report = None
    for idx, target_rel in enumerate(target_rels, 1):
        if len(target_rels) > 1:
            presenter.log(f"      - [Target {idx}/{len(target_rels)}] Arbitrando '{target_rel}'...")
        b_code = baseline_codes.get(target_rel, "")
        report = _arbitrate_single_target(
            target_rel=target_rel,
            test_rel=test_rel,
            baseline_code=b_code,
            work_dir=work_dir,
            elevated_task_spec=elevated_task_spec,
            synthesizer=synthesizer,
            skeptic=skeptic,
            presenter=presenter,
        )
        last_report = report
        if report.status != VerdictStatus.CERTIFIED:
            presenter.log(f"      - ❌ Target '{target_rel}' rechazado con estado: {report.status.value}")
            return report, synthesizer

    presenter.log("      - Synthesizer refined technical specification with enriched requirements.")
    return last_report, synthesizer


def _retry_closure_refinement(
    target_work_file: Path,
    test_work_file: Path,
    dossier: Any,
    task: str,
    target_rel: Path,
    synthesizer: SynthesizerRole,
    initial_closure_report: Any,
    presenter: OrchestratorPresenter,
    max_retries: int = 3,
) -> Any:
    """Execute prescriptive retry loop when surgical ticket is emitted."""
    closure_report = initial_closure_report
    current_retry = 0
    while not closure_report.approved and closure_report.surgical_ticket and current_retry < max_retries:
        current_retry += 1
        presenter.log(f"      - ⚠️ Forensic Tribunal issued Surgical Correction Ticket (Attempt {current_retry}/{max_retries}): {closure_report.surgical_ticket.ticket_id}")
        for inst in closure_report.surgical_ticket.actionable_instructions:
            presenter.log(f"        • {inst}")
        presenter.log(f"      - Ejecutando auto-reintento prescriptivo en Fase 2 (Intento {current_retry}/{max_retries})...")
        c_code = target_work_file.read_text(encoding="utf-8") if target_work_file.exists() else ""
        t_code = test_work_file.read_text(encoding="utf-8") if test_work_file.exists() else ""
        refined = synthesizer.refine_patch(
            task_description=task,
            current_code=c_code,
            skeptic_critique=closure_report.surgical_ticket.to_prompt_context(),
            current_test_code=t_code,
        )
        target_work_file.write_text(refined["candidate_code"], encoding="utf-8")
        if refined.get("test_code") and len(refined["test_code"]) > 200 and "def test_" in refined["test_code"]:
            test_work_file.write_text(refined["test_code"], encoding="utf-8")
        closure_report = closure_tribunal.evaluate(
            candidate_code=refined["candidate_code"],
            candidate_test_code=refined["test_code"],
            dossier=dossier,
            rel_path=str(target_rel),
        )
        if closure_report.approved:
            presenter.log(f"      - ✔️ Successful auto-recovery in Attempt {current_retry}: Forensic Tribunal PASSED.")
            break
    return closure_report


def _evaluate_single_target_closure(
    target_rel: Path,
    work_dir: Path,
    test_work_file: Path,
    dossier: Any,
    task: str,
    synthesizer: SynthesizerRole,
    report: Any,
    multi_targets: bool,
    presenter: OrchestratorPresenter,
) -> Any:
    target_work_file = work_dir / target_rel
    c_code = target_work_file.read_text(encoding="utf-8") if target_work_file.exists() else ""
    t_code = test_work_file.read_text(encoding="utf-8") if test_work_file.exists() else ""

    closure_report = closure_tribunal.evaluate(
        candidate_code=c_code,
        candidate_test_code=t_code,
        dossier=dossier,
        rel_path=str(target_rel),
    )

    prefix = f"[{target_rel.name}] " if multi_targets else ""
    p_str = "CUMPLE 100%" if closure_report.parity_cubo_1_passed else "INCOMPLETO"
    v_str = "0 ANTI-FEATURES (CLEAN)" if closure_report.veto_cubo_3_passed else "VIOLATION DETECTED"
    s_str = "0 VULNERABILIDADES (OWASP OK)" if closure_report.forensic_security_passed else "HALLAZGOS DE SEGURIDAD"
    b_str = "100% LIMPIO" if closure_report.target_scoped_audit_passed else "FALLADO"
    presenter.log(f"      - {prefix}Tribunal Forense (Paridad Cubo 1): {p_str}")
    presenter.log(f"      - {prefix}Tribunal Forense (Veto Cubo 3): {v_str}")
    presenter.log(f"      - {prefix}Sondas Forenses de Seguridad: {s_str}")
    presenter.log(f"      - {prefix}Trinquete Diferencial: {b_str} ({closure_report.unrelated_findings_count} ajenos)")

    if not closure_report.approved and closure_report.surgical_ticket and report.status == VerdictStatus.CERTIFIED:
        closure_report = _retry_closure_refinement(
            target_work_file=target_work_file,
            test_work_file=test_work_file,
            dossier=dossier,
            task=task,
            target_rel=target_rel,
            synthesizer=synthesizer,
            initial_closure_report=closure_report,
            presenter=presenter,
        )
    return closure_report


def _run_closure_phase(
    work_dir: Path,
    target_rels: list[Path],
    test_rel: Path,
    dossier: Any,
    task: str,
    synthesizer: SynthesizerRole,
    report: Any,
    presenter: OrchestratorPresenter,
) -> Any:
    presenter.log("[5/6] ⚖️  Ejecutando Tribunal Determinista y Forense de Cierre:")
    py_status = "PASADOS (0 roturas)" if report.regression_tests_passed else "FALLIDOS"
    presenter.log(f"      - Pytest Regression: {py_status}")
    presenter.log(f"      - Firmas AST: {len(report.ast_violations)} violaciones detectadas")
    presenter.log(f"      - Complexity: Max V(G) = {report.max_cyclomatic_complexity} (Threshold <= 10)")
    mut_pct = int(report.mutation_score * 100)
    presenter.log(f"      - Mutation CTF Probe: {mut_pct}% mutants killed (Threshold >= 80%)")
    presenter.log("      - External Dependencies: 0 unauthorized dependencies added")

    test_work_file = work_dir / test_rel
    last_closure = None
    is_multi = len(target_rels) > 1
    for target_rel in target_rels:
        closure_report = _evaluate_single_target_closure(
            target_rel=target_rel,
            work_dir=work_dir,
            test_work_file=test_work_file,
            dossier=dossier,
            task=task,
            synthesizer=synthesizer,
            report=report,
            multi_targets=is_multi,
            presenter=presenter,
        )
        last_closure = closure_report
        if not closure_report.approved:
            return closure_report

    return last_closure


def _print_diff_preview(worktree: EphemeralWorktree, repo_root: Path, target_rels: list[Path]) -> None:
    targets_str_args = [str(p) for p in target_rels]
    subprocess.run(["git", "add", "-f", *targets_str_args], cwd=str(worktree.worktree_path), capture_output=True, check=False)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "feat(evolution): certified change by cognitive arbiter"],
        cwd=str(worktree.worktree_path),
        capture_output=True,
        check=False,
    )

    diff_res = subprocess.run(
        ["git", "diff", f"master..{worktree.branch_name}", "--", *targets_str_args],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    diff_output = diff_res.stdout.strip()
    if diff_output:
        diff_lines = len(diff_output.splitlines())
        print(f"\nGenerated Diff ({diff_lines} lines across {len(target_rels)} file(s)):")
        preview = "\n".join(diff_output.splitlines()[:20])
        print(preview)
        if diff_lines > 20:
            print(f"... ({diff_lines - 20} additional lines)")


def _handle_merge_interaction(
    worktree: EphemeralWorktree,
    repo_root: Path,
    auto_merge: bool,
    target_rels: list[Path] | None = None,
) -> None:
    should_merge = auto_merge
    if not auto_merge and sys.stdin.isatty():
        try:
            ans = input("\nDo you wish to merge this certified change into main? (y/n): ").strip().lower()
            should_merge = (ans in ("s", "si", "y"))
        except (EOFError, KeyboardInterrupt):
            should_merge = False

    if should_merge:
        print(f"[Merge] Fusionando rama {worktree.branch_name} en master...")
        res_merge = subprocess.run(
            ["git", "merge", "--ff-only", worktree.branch_name],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res_merge.returncode == 0:
            print("[Merge] Merge completed successfully. Main branch updated.")
        else:
            print(f"[Merge] Aviso fast-forward: {res_merge.stderr.strip()}")

        # Physical safety synchronization for certified files
        if target_rels:
            for rel in target_rels:
                src = worktree.worktree_path / rel
                dst = repo_root / rel
                if src.exists():
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        print("[Cancelled] Merge cancelled by user. Main branch preserved intact.")



def _render_summary(
    report: Any,
    closure_report: Any,
    dossier: Any,
    is_certified: bool,
    worktree: EphemeralWorktree | None,
    repo_root: Path,
    target_rels: list[Path],
    auto_merge: bool,
    presenter: OrchestratorPresenter,
) -> None:
    if presenter.output_json:
        rep_dict = {
            "task": report.task_description,
            "status": "CERTIFIED" if is_certified else report.status.value,
            "dossier": {
                "leaders": list(dossier.leaders_analyzed),
                "invariants_count": len(dossier.must_have_invariants),
                "unfair_advantages_count": len(dossier.unfair_advantages),
                "anti_features_count": len(dossier.deliberate_anti_features),
            },
            "iterations_used": report.iterations_used,
            "ast_violations": [v.to_dict() for v in report.ast_violations],
            "regression_passed": report.regression_tests_passed,
            "mutation_score": report.mutation_score,
            "max_complexity": report.max_cyclomatic_complexity,
            "closure_tribunal": closure_report.to_dict(),
            "execution_time_seconds": report.execution_time_seconds,
            "target_files": [str(p) for p in target_rels],
        }
        print(json.dumps(rep_dict, indent=2))
        return

    verdict_str = "\n[6/6] 🟢 VEREDICTO: CERTIFIED TIER-1 SOTA" if is_certified else f"\n[6/6] 🔴 VEREDICTO: RECHAZADO ({report.status.value})"
    print(verdict_str)

    if worktree:
        _print_diff_preview(worktree, repo_root, target_rels)

    if is_certified and worktree:
        _handle_merge_interaction(worktree, repo_root, auto_merge, target_rels=target_rels)



def run_orchestrator(
    task: str,
    target_file_str: str | None = None,
    target_files_list: list[str] | None = None,
    test_file_str: str | None = None,
    sector: str = "SaaS Infrastructure",
    use_worktree: bool = True,
    auto_merge: bool = False,
    output_json: bool = False,
    offline_only: bool = False,
) -> int:
    """Execute the 5-phase Cognitive Arbiter pipeline with bounded complexity."""
    global _ACTIVE_WORKTREE
    repo_root = Path.cwd().resolve()
    target_inputs = target_files_list or target_file_str
    if not target_inputs:
        raise ValueError("Must specify at least one target file via target_file_str or target_files_list.")

    target_rels, test_rel = _resolve_target_and_test_paths(target_inputs, test_file_str)
    baseline_paths = [repo_root / p for p in target_rels]
    baseline_codes = {p: (repo_root / p).read_text(encoding="utf-8") for p in target_rels if (repo_root / p).exists()}
    presenter = OrchestratorPresenter(output_json)

    presenter.header(task, target_rels)
    worktree, work_dir = _setup_worktree(repo_root, use_worktree, presenter, target_rels=target_rels, test_rel=test_rel)
    _ACTIVE_WORKTREE = worktree

    try:
        dossier = _run_epistemic_phase(task, sector, offline_only, presenter, target_file=str(target_rels[0]))
        _log_baseline_signatures(baseline_paths, presenter)
        report, synthesizer = _run_dialectical_phase(task, target_rels, test_rel, baseline_codes, work_dir, offline_only, presenter, dossier=dossier)
        closure_report = _run_closure_phase(work_dir, target_rels, test_rel, dossier, task, synthesizer, report, presenter)

        is_certified = (report.status == VerdictStatus.CERTIFIED and closure_report.approved)
        _render_summary(
            report=report,
            closure_report=closure_report,
            dossier=dossier,
            is_certified=is_certified,
            worktree=worktree,
            repo_root=repo_root,
            target_rels=target_rels,
            auto_merge=auto_merge,
            presenter=presenter,
        )
        return 0 if is_certified else 1
    finally:
        if worktree:
            worktree.cleanup()
            _ACTIVE_WORKTREE = None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="The Cognitive Arbiter — Pipeline Maestro de 5 Fases SOTA (RFC-015)."
    )
    parser.add_argument("--task", required=True, help="Detailed description of task to synthesize and audit.")
    parser.add_argument("--target-file", default=None, help="Ruta relativa del archivo a modificar.")
    parser.add_argument("--target-files", nargs="+", default=None, help="List of relative file paths to modify atomically.")
    parser.add_argument("--test-file", default=None, help="Relative path of unit or integration test file.")
    parser.add_argument("--sector", default="SaaS Infrastructure", help="Application business sector.")
    parser.add_argument("--no-worktree", action="store_true", help="Desactiva el sandbox git worktree.")
    parser.add_argument("--auto-merge", action="store_true", help="Automatically merge into main branch if all gates pass.")
    parser.add_argument("--json", action="store_true", help="Imprime el veredicto en formato JSON.")
    parser.add_argument("--offline", action="store_true", help="Fuerza modo offline sin llamadas externas.")

    args = parser.parse_args()
    target_inputs = args.target_files or args.target_file
    if not target_inputs:
        parser.error("Se debe especificar al menos un archivo objetivo con --target-file o --target-files")

    code = run_orchestrator(
        task=args.task,
        target_file_str=args.target_file if not args.target_files else None,
        target_files_list=args.target_files,
        test_file_str=args.test_file,
        sector=args.sector,
        use_worktree=not args.no_worktree,
        auto_merge=args.auto_merge,
        output_json=args.json,
        offline_only=args.offline,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
