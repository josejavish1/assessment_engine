"""Implements shared utilities for pipeline steps that are executed as Python modules."""

import asyncio
import importlib
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

from infrastructure.runtime_env import ensure_google_cloud_env_defaults
from infrastructure.runtime_paths import ROOT, resolve_client_dir

logger = logging.getLogger(__name__)

AI_STEP_TIMEOUT_ENV = "ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"


def resolve_python_bin() -> str:
    """Return the path to the Python executable, preferring the local `.venv` directory."""
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def build_runtime_env(
    base_env: dict[str, str] | None = None,
    *,
    include_pythonpath: bool = True,
) -> dict[str, str]:
    """Constructs a dictionary of environment variables for a subprocess.

    Initializes an environment dictionary by creating a shallow copy of the
    provided `base_env` or, if `base_env` is None, a copy of the current
    process's environment (`os.environ`). This dictionary is then populated
    with default Google Cloud settings. If `include_pythonpath` is True, the
    `PYTHONPATH` is set to the project's source directory. Finally,
    `PYTHONUNBUFFERED` is set to '1' to disable I/O buffering, facilitating
    real-time log streaming from the subprocess.

    Args:
        base_env: An optional base environment dictionary. If not provided, a
            copy of `os.environ` is used.
        include_pythonpath: If True, sets the `PYTHONPATH` environment
            variable to the project's source directory.

    Returns:
        A dictionary of environment variables suitable for a subprocess.
    """
    env = os.environ.copy() if base_env is None else dict(base_env)
    ensure_google_cloud_env_defaults(env)
    if include_pythonpath:
        env["PYTHONPATH"] = str(ROOT / "src")

    # Sets the Python interpreter to unbuffered mode. This ensures stdout and stderr are written directly to their respective streams, facilitating real-time log streaming from subprocesses.
    env["PYTHONUNBUFFERED"] = "1"
    return env


def prepare_case_runtime(
    env: dict[str, str],
    *,
    client_id: str,
    tower_id: str,
) -> Path:
    """Prepares the runtime environment and directory for a specific assessment case.

    Ensures a dedicated directory for a given client and tower assessment exists,
    creating it if necessary. The directory path is formed by appending `tower_id`
    to a base path derived from `client_id`.

    This function mutates the provided `env` dictionary in-place, injecting the
    following keys: `ASSESSMENT_CLIENT_ID`, `ASSESSMENT_TOWER_ID`, and
    `ASSESSMENT_CASE_DIR`.

    Args:
        env: A dictionary of environment variables to be updated in-place.
        client_id: The unique identifier for the client.
        tower_id: The unique identifier for the tower, scoped to the client.

    Returns:
        A `pathlib.Path` object for the assessment case directory.

    Raises:
        PermissionError: If directory creation fails due to insufficient file
            system permissions.
        OSError: If a system-level error other than a permission issue occurs
            during directory creation.
    """
    case_dir = resolve_client_dir(client_id) / tower_id
    case_dir.mkdir(parents=True, exist_ok=True)
    env["ASSESSMENT_CLIENT_ID"] = client_id
    env["ASSESSMENT_TOWER_ID"] = tower_id
    env["ASSESSMENT_CASE_DIR"] = str(case_dir)
    return case_dir


def validate_runtime_environment(env: dict[str, str]) -> None:
    """Validate the runtime environment configuration for Vertex AI.

    Verifies that the `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`
    environment variables are present and contain non-whitespace characters.

    Args:
        env: A dictionary representing the environment variables, such as `os.environ`.

    Raises:
        RuntimeError: If either `GOOGLE_CLOUD_PROJECT` or `GOOGLE_CLOUD_LOCATION`
            is not found in `env`, or if its value is empty or consists
            solely of whitespace.
    """
    missing_vars = [
        name
        for name in ("GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION")
        if not env.get(name, "").strip()
    ]
    if missing_vars:
        raise RuntimeError("Falta configuración de entorno para Vertex AI.")


def resolve_ai_step_timeout_seconds(
    env: dict[str, str],
    step_name: str,
) -> float | None:
    """Resolve the execution timeout in seconds for a designated AI pipeline step.

    Scans the `step_name` for specific keywords ("Engine:", "Refinement",
    "Run ") to identify it as an AI-related step. If the step is identified
    as such, the timeout is sourced from the `AI_STEP_TIMEOUT_ENV` environment
    variable within the provided `env` dictionary. If this variable is not set
    or is an empty string, a default value of 120.0 seconds is returned.

    Args:
        env: A dictionary representing the execution environment variables.
        step_name: The name of the pipeline step to evaluate.

    Returns:
        The configured timeout in seconds as a float for AI-related steps,
        or `None` if the step is not identified as an AI step.

    Raises:
        RuntimeError: If the `AI_STEP_TIMEOUT_ENV` environment variable is
            present but contains a non-numeric or non-positive value.
    """
    # Enforce a timeout on AI-related subprocesses to mitigate the risk of indefinite execution stalls.
    if (
        "Engine:" not in step_name
        and "Refinement" not in step_name
        and "Run " not in step_name
    ):
        return None

    raw_value = str(env.get(AI_STEP_TIMEOUT_ENV, "")).strip()
    if not raw_value:
        return 120.0  # A default timeout is set for Google Cloud API calls to prevent indefinite hangs on unresponsive network requests.

    try:
        timeout_seconds = float(raw_value)
    except ValueError as exc:
        raise RuntimeError(
            f"{AI_STEP_TIMEOUT_ENV} debe ser un número positivo."
        ) from exc

    if timeout_seconds <= 0:
        raise RuntimeError(f"{AI_STEP_TIMEOUT_ENV} debe ser mayor que 0.")

    return timeout_seconds


def run_module_step(cmd_args: list[str], step_name: str, env: dict[str, str]) -> None:
    r"""{'docstring': 'Execute a Python module in-process, simulating a command-line invocation.\n\n    Simulates a `python -m <module_name> ...` call by dynamically importing\n    and reloading the specified module. Execution is isolated from the caller\n    by temporarily patching `sys.argv` and `os.environ`. The original state of\n    these global objects is restored after execution, regardless of outcome.\n\n    The target module must define a `main` function. If `main` is a coroutine\n    function, it is executed within a new asyncio event loop.\n\n    Args:\n        cmd_args: A list of strings representing the command-line arguments.\n            Must follow the format `[\'<executable_placeholder>\', \'-m\',\n            \'<module_name>\', ...]`. The first element is ignored.\n        step_name: A descriptive name for the pipeline step, used for logging and\n            error reporting.\n        env: A dictionary of environment variables to establish for the module\'s\n            execution context. This environment temporarily replaces the parent\n            process\'s environment for the duration of the call.\n\n    Returns:\n        None.\n\n    Raises:\n        ValueError: If `cmd_args` has fewer than three elements or its second\n            element is not `"-m"`.\n        ImportError: If the module specified in `cmd_args` cannot be imported.\n        RuntimeError: If the target module does not define a `main` function, the\n            `main` function raises an unhandled exception, or the module\n            terminates via `sys.exit` with a non-zero status code.'}."""
    logger.info(f"=== {step_name} ===")

    if len(cmd_args) < 3 or cmd_args[1] != "-m":
        raise ValueError(f"Comando no soportado por run_module_step: {cmd_args}")

    module_name = cmd_args[2]
    script_args = cmd_args[3:]
    process_env = build_runtime_env(env)
    original_env = os.environ.copy()
    mock_argv = [module_name] + script_args

    try:
        os.environ.clear()
        os.environ.update(process_env)
        with patch.object(sys, "argv", mock_argv):
            mod = importlib.import_module(module_name)
            importlib.reload(mod)
            if not hasattr(mod, "main"):
                raise RuntimeError(f"El módulo {module_name} no tiene función main()")

            result = mod.main()
            if asyncio.iscoroutine(result):
                asyncio.run(result)
    except SystemExit as exc:
        if exc.code not in (0, None):
            raise RuntimeError(
                f"Fallo nativo (SystemExit) en {step_name} con código: {exc.code}"
            ) from exc
        logger.info(f"[{step_name}] Finalizado con exit(0)")
    except Exception as exc:
        logger.exception(f"Fallo nativo en {step_name} con error: {exc}")
        raise RuntimeError(f"Fallo nativo en {step_name} con error: {exc}") from exc
    finally:
        os.environ.clear()
        os.environ.update(original_env)
