from __future__ import annotations

from pathlib import Path

from assessment_engine.scripts.tools import run_incremental_quality_gate as gate


def test_normalize_live_python_paths_filters_to_live_surface() -> None:
    paths = [
        "README.md",
        "_PROJECT_ARCHIVE_/tool.py",
        "src/assessment_engine/scripts/run_global_pipeline.py",
        "src/assessment_engine/scripts/run_global_pipeline.py",
        "tests/test_pipeline_runtime.py",
        "docs/example.py",
    ]

    assert gate.normalize_live_python_paths(paths) == [
        "src/assessment_engine/scripts/run_global_pipeline.py",
        "tests/test_pipeline_runtime.py",
    ]


def test_main_skips_when_no_live_python_files_changed(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    monkeypatch.setattr(
        gate, "git_changed_files", lambda *_args, **_kwargs: ["README.md"]
    )

    exit_code = gate.main(
        ["--repo-root", str(tmp_path), "--base-sha", "base", "--head-sha", "head"]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Incremental quality gate skipped" in captured.out


def test_main_runs_quality_commands_for_changed_live_files(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        gate,
        "git_changed_files",
        lambda *_args, **_kwargs: ["README.md", "tests/test_pipeline_runtime.py"],
    )

    recorded: dict[str, object] = {}

    def fake_run_quality_commands(repo_root: Path, target_files: list[str]) -> int:
        recorded["repo_root"] = repo_root
        recorded["target_files"] = target_files
        return 0

    monkeypatch.setattr(gate, "run_quality_commands", fake_run_quality_commands)

    exit_code = gate.main(
        ["--repo-root", str(tmp_path), "--base-sha", "base", "--head-sha", "head"]
    )

    assert exit_code == 0
    assert recorded == {
        "repo_root": tmp_path.resolve(),
        "target_files": ["tests/test_pipeline_runtime.py"],
    }


def test_main_returns_failure_from_quality_commands(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        gate,
        "git_changed_files",
        lambda *_args, **_kwargs: [
            "src/assessment_engine/scripts/run_global_pipeline.py"
        ],
    )
    monkeypatch.setattr(gate, "run_quality_commands", lambda *_args, **_kwargs: 1)

    exit_code = gate.main(
        ["--repo-root", str(tmp_path), "--base-sha", "base", "--head-sha", "head"]
    )

    assert exit_code == 1
