from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "bin" / "po-run"
ORCHESTRATOR = (
    REPO_ROOT / "src/assessment_engine/scripts/tools/run_product_owner_orchestrator.py"
)
DEFAULT_EXECUTOR = (
    f"{REPO_ROOT / '.github/scripts/orchestrator-gemini-executor.sh'} "
    "{repo_root} {task_prompt_file} {attempt}"
)


def _ensure_wrapper_is_executable() -> None:
    WRAPPER.chmod(0o755)


def _write_fake_python(tmp_path: Path) -> tuple[Path, Path]:
    capture_path = tmp_path / "captured_args.bin"
    fake_python = tmp_path / "fake-python"
    fake_python.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        ': "${PO_RUN_CAPTURE_FILE:?}"\n'
        'printf \'%s\\0\' "$@" > "$PO_RUN_CAPTURE_FILE"\n',
        encoding="utf-8",
    )
    fake_python.chmod(0o755)
    return fake_python, capture_path


def _read_captured_args(path: Path) -> list[str]:
    return [item for item in path.read_text(encoding="utf-8").split("\0") if item]


def test_po_run_wrapper_builds_run_command_with_default_executor(
    tmp_path: Path,
) -> None:
    _ensure_wrapper_is_executable()
    fake_python, capture_path = _write_fake_python(tmp_path)
    env = os.environ.copy()
    env["ASSESSMENT_ENGINE_PYTHON_BIN"] = str(fake_python)
    env["PO_RUN_CAPTURE_FILE"] = str(capture_path)
    env.pop("ASSESSMENT_ORCHESTRATOR_EXECUTOR_CMD", None)

    result = subprocess.run(
        [str(WRAPPER), "Quiero mejorar la UX del orquestador"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert _read_captured_args(capture_path) == [
        str(ORCHESTRATOR),
        "run",
        "--request",
        "Quiero mejorar la UX del orquestador",
        "--executor-command",
        DEFAULT_EXECUTOR,
    ]


def test_po_run_wrapper_builds_plan_command_without_executor(tmp_path: Path) -> None:
    _ensure_wrapper_is_executable()
    fake_python, capture_path = _write_fake_python(tmp_path)
    env = os.environ.copy()
    env["ASSESSMENT_ENGINE_PYTHON_BIN"] = str(fake_python)
    env["PO_RUN_CAPTURE_FILE"] = str(capture_path)

    result = subprocess.run(
        [str(WRAPPER), "--plan", "Quiero revisar la spec minima"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert _read_captured_args(capture_path) == [
        str(ORCHESTRATOR),
        "plan",
        "--request",
        "Quiero revisar la spec minima",
    ]


def test_po_run_wrapper_rejects_missing_request_noninteractive(tmp_path: Path) -> None:
    _ensure_wrapper_is_executable()
    fake_python, capture_path = _write_fake_python(tmp_path)
    env = os.environ.copy()
    env["ASSESSMENT_ENGINE_PYTHON_BIN"] = str(fake_python)
    env["PO_RUN_CAPTURE_FILE"] = str(capture_path)

    result = subprocess.run(
        [str(WRAPPER), "--plan"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Debes indicar una peticion" in result.stderr
    assert not capture_path.exists()
