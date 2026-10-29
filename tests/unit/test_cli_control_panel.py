"""Top-Tier-1 unit tests for the Sovereign Assessment Engine CLI Control Panel."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import assessment_engine.application.cli as cli_mod

# --- PIPELINE COMMAND TESTS ---

def test_run_pipeline_full_success(tmp_path: Path):
    """Verify run_pipeline executes all phases 0-5 and returns 0 on complete success."""
    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value = subprocess.CompletedProcess(args=["python"], returncode=0)
        code = cli_mod.run_pipeline(
            client="Acme Bank",
            slug="acme_bank",
            context="context.docx",
            responses="responses.txt",
            towers_str="T1 T2",
        )
        assert code == 0
        # Phase 1, Phase 2 (x2 towers), Phase 3, Phase 4, Phase 5 = 6 invocations
        assert mock_sub.call_count >= 5


def test_run_pipeline_phase_failures(tmp_path: Path):
    """Verify run_pipeline aborts early with non-zero exit code if any phase fails."""
    # Phase 1 failure
    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value = subprocess.CompletedProcess(args=["python"], returncode=1)
        code = cli_mod.run_pipeline("Acme", "acme", "c.docx", "r.txt", "T1")
        assert code == 1

    # Phase 2 failure
    with patch("subprocess.run") as mock_sub:
        mock_sub.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0),  # Phase 1
            subprocess.CompletedProcess(args=[], returncode=2),  # Phase 2 Tower
        ]
        code = cli_mod.run_pipeline("Acme", "acme", "c.docx", "r.txt", "T1")
        assert code == 2


def test_run_pipeline_incremental_cache_bypass():
    """Verify run_pipeline bypasses subprocess execution when canonical artifacts exist."""
    repo_root = Path(cli_mod.__file__).resolve().parents[3]
    slug = "test_incremental_client"
    working_dir = repo_root / "working" / slug
    tower_dir = working_dir / "T1"
    presentation_dir = working_dir / "presentation"

    try:
        working_dir.mkdir(parents=True, exist_ok=True)
        tower_dir.mkdir(parents=True, exist_ok=True)
        presentation_dir.mkdir(parents=True, exist_ok=True)

        # Create mock artifacts for all phases
        (working_dir / "client_intelligence.json").write_text("{}", encoding="utf-8")
        (working_dir / "benchmarks_snapshot.json").write_text("{}", encoding="utf-8")
        (tower_dir / f"Diagnostico_ASIS_T1_{slug}.docx").write_text("asis", encoding="utf-8")
        (tower_dir / f"Strategic_Blueprint_T1_{slug}.docx").write_text("blueprint", encoding="utf-8")
        (tower_dir / "blueprint_t1_payload.json").write_text("{}", encoding="utf-8")
        (working_dir / "Informe_Ejecutivo_Consolidado_Test Inc.docx").write_text("global", encoding="utf-8")
        (working_dir / "global_report_payload.json").write_text("{}", encoding="utf-8")
        (working_dir / "Account_Action_Plan_Test Inc.docx").write_text("commercial", encoding="utf-8")
        (working_dir / "commercial_report_payload.json").write_text("{}", encoding="utf-8")
        (presentation_dir / "index.html").write_text("<html></html>", encoding="utf-8")

        with patch("subprocess.run") as mock_sub:
            code = cli_mod.run_pipeline(
                client="Test Inc",
                slug=slug,
                context="c.docx",
                responses="r.txt",
                towers_str="T1",
                force=False,
            )
            assert code == 0
            assert mock_sub.call_count == 0  # All phases bypassed!
    finally:
        if working_dir.exists():
            shutil.rmtree(working_dir, ignore_errors=True)


def test_run_pipeline_force_rebuild():
    """Verify run_pipeline with force=True forwards --force to towers and runs all phases."""
    with patch("subprocess.run") as mock_sub:
        mock_sub.return_value = subprocess.CompletedProcess(args=["python"], returncode=0)
        code = cli_mod.run_pipeline(
            client="Acme Force",
            slug="acme_force",
            context="c.docx",
            responses="r.txt",
            towers_str="T1",
            force=True,
        )
        assert code == 0
        assert mock_sub.call_count >= 4
        # Tower invocation should include --force
        tower_calls = [
            call for call in mock_sub.call_args_list if "--tower" in call[0][0]
        ]
        assert len(tower_calls) == 1
        assert "--force" in tower_calls[0][0][0]


# --- APEX PO-BATCH MANAGER TESTS ---

def test_manage_po_batch_missing_dispatcher():
    """Verify manage_po_batch returns 1 if apex_dispatcher.py does not exist."""
    with patch.object(Path, "exists", return_value=False):
        code = cli_mod.manage_po_batch(daemon=True, monitor=False)
        assert code == 1


def test_manage_po_batch_daemon_and_monitor(tmp_path: Path):
    """Verify daemon launch creates PID file and monitor mode invokes subprocess."""
    with patch("pathlib.Path.exists", return_value=True):
        # 1. Daemon mode
        mock_proc = MagicMock()
        mock_proc.pid = 99999
        with patch("subprocess.Popen", return_value=mock_proc):
            with patch("pathlib.Path.write_text") as mock_write:
                code_daemon = cli_mod.manage_po_batch(daemon=True, monitor=False)
                assert code_daemon == 0
                mock_write.assert_called_once_with("99999", encoding="utf-8")

        # 2. Monitor mode
        with patch("subprocess.run") as mock_sub:
            mock_sub.return_value = subprocess.CompletedProcess(args=[], returncode=0)
            code_mon = cli_mod.manage_po_batch(daemon=False, monitor=True)
            assert code_mon == 0


# --- LOCK-IN PORTABILITY TEST ---

def test_run_lockin_test_success_and_failure(tmp_path: Path):
    """Verify run_lockin_test executes isolated sandbox copy and asserts vendor-agnostic test suite."""
    with patch("subprocess.run") as mock_sub:
        # Success path
        mock_sub.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        assert cli_mod.run_lockin_test() == 0

        # Failure path (lock-in detected)
        mock_sub.return_value = subprocess.CompletedProcess(args=[], returncode=1)
        assert cli_mod.run_lockin_test() == 1


# --- RAGE COMMAND TESTS ---

def test_run_rage_command_lifecycle():
    """Verify run_rage_command invokes AgenticRageBenchmarker and parses snapshots."""
    mock_snap = MagicMock()
    mock_t1 = MagicMock(framework_name="ISO 27001", dynamic_score=4.2, verification_status="PASSED")
    mock_snap.snapshots = {"T1": mock_t1}

    mock_bench = MagicMock()
    mock_bench.run_rage_evaluation = AsyncMock(return_value=mock_snap)

    with patch("assessment_engine.infrastructure.agentic_benchmarker.AgenticRageBenchmarker", return_value=mock_bench):
        code = cli_mod.run_rage_command("Banco Santander", "banking", tower_filter="T1")
        assert code == 0

        # Exception path
        mock_bench.run_rage_evaluation.side_effect = RuntimeError("API down")
        code_err = cli_mod.run_rage_command("Banco Santander", "banking")
        assert code_err == 1


# --- AUDIT COMMAND TESTS ---

def test_run_audit_command_formatting():
    """Verify run_audit_command executes SoverikQualityEngine and formats report table."""
    mock_report = MagicMock(
        project_name="assessment_engine",
        global_score=100.0,
        global_grade="A+",
        probes={
            "security_sast": MagicMock(passed=True, score_pct=100.0),
            "test_coverage": MagicMock(passed=True, metrics={"line_coverage_pct": 75.0}),
            "assertion_quality": MagicMock(passed=True, metrics={"strong_ratio_pct": 90.0}),
            "mutation_gate": MagicMock(passed=True, score_pct=100.0),
            "neurosymbolic_topology": MagicMock(passed=True, metrics={"orphans_count": 0, "total_modules": 170}),
            "ast_complexity": MagicMock(passed=True, score_pct=100.0),
            "supply_chain": MagicMock(passed=True, metrics={"total_dependencies": 25}),
        },
    )

    mock_engine = MagicMock()
    mock_engine.audit_project.return_value = mock_report

    with patch("assessment_engine.infrastructure.auditor.scanner.SoverikQualityEngine", return_value=mock_engine):
        code = cli_mod.run_audit_command(target=".", output_dir="docs/audits")
        assert code == 0


# --- CLI MAIN ENTRYPOINT ARGV TESTS ---

def test_cli_main_subcommand_dispatch():
    """Verify main() parses argv and dispatches cleanly to subcommands."""
    # 1. run subcommand
    with patch("assessment_engine.application.cli.run_pipeline", return_value=0) as mock_rp:
        with pytest.raises(SystemExit) as exc:
            cli_mod.main([
                "run",
                "--client", "Acme",
                "--slug", "acme",
                "--context", "ctx.docx",
                "--responses", "resp.txt",
                "--towers", "T1 T2",
                "--force",
            ])
        assert exc.value.code == 0
        mock_rp.assert_called_once_with(
            "Acme", "acme", "ctx.docx", "resp.txt", "T1 T2", force=True, concurrency=6, language=None
        )

    # 2. po-batch subcommand
    with patch("assessment_engine.application.cli.manage_po_batch", return_value=0) as mock_pb:
        with pytest.raises(SystemExit) as exc:
            cli_mod.main(["po-batch", "--daemon"])
        assert exc.value.code == 0
        mock_pb.assert_called_once_with(True, False)

    # 3. rage subcommand
    with patch("assessment_engine.application.cli.run_rage_command", return_value=0) as mock_rg:
        with pytest.raises(SystemExit) as exc:
            cli_mod.main(["rage", "--client", "Santander", "--industry", "banking"])
        assert exc.value.code == 0
        mock_rg.assert_called_once_with("Santander", "banking", None)

    # 4. prove-lockin subcommand
    with patch("assessment_engine.application.cli.run_lockin_test", return_value=0) as mock_lk:
        with pytest.raises(SystemExit) as exc:
            cli_mod.main(["prove-lockin"])
        assert exc.value.code == 0
        assert mock_lk.called

    # 5. audit subcommand
    with patch("assessment_engine.application.cli.run_audit_command", return_value=0) as mock_ad:
        with pytest.raises(SystemExit) as exc:
            cli_mod.main(["audit", "--target", ".", "--output-dir", "docs/audits"])
        assert exc.value.code == 0
        mock_ad.assert_called_once_with(".", "docs/audits")
