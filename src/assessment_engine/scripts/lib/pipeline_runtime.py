"""Provides shared utility functions for Python module-based pipeline entrypoints."""

import asyncio
import importlib
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults
from assessment_engine.scripts.lib.runtime_paths import ROOT, resolve_client_dir

logger = logging.getLogger(__name__)

AI_STEP_TIMEOUT_ENV = "ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"


def resolve_python_bin() -> str:
    """Resolve the path to the Python executable, preferring a local venv."""
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def build_runtime_env(
    base_env: dict[str, str] | None = None,
    *,
    include_pythonpath: bool = True,
) -> dict[str, str]:
    """Build a runtime environment dictionary for a subprocess.

    Constructs a dictionary of environment variables for executing child processes.
    The environment is initialized with a copy of the `base_env` dictionary, or
    with a copy of `os.environ` if `base_env` is None. This dictionary is then
    updated with standard Google Cloud environment variables and can optionally
    include a `PYTHONPATH` pointing to the project's source root.

    Args:
        base_env: An optional base dictionary of environment variables. If None,
            a copy of `os.environ` is used as the base.
        include_pythonpath: If True, sets the `PYTHONPATH` environment variable
            to the project's 'src' directory.

    Returns:
        A dictionary of string key-value pairs representing the configured
        runtime environment.
    """
    env = os.environ.copy() if base_env is None else dict(base_env)
    ensure_google_cloud_env_defaults(env)
    if include_pythonpath:
        env["PYTHONPATH"] = str(ROOT / "src")
    return env


def prepare_case_runtime(
    env: dict[str, str],
    *,
    client_id: str,
    tower_id: str,
) -> Path:
    r"""{'docstring': "Ensures a case-specific directory exists and injects runtime variables.\n\n    This function establishes the runtime context for an individual assessment case.\n    It constructs a path from the client and tower IDs, then creates the\n    corresponding directory on the filesystem if it does not already exist.\n\n    The provided `env` dictionary is populated in-place with the following keys:\n    - `ASSESSMENT_CLIENT_ID`: The client's unique identifier.\n    - `ASSESSMENT_TOWER_ID`: The tower's unique identifier.\n    - `ASSESSMENT_CASE_DIR`: The string representation of the created directory path.\n\n    Args:\n        env: A dictionary representing the runtime environment. This dictionary\n            is modified in-place with case-specific variables.\n        client_id: The unique identifier for the client.\n        tower_id: The unique identifier for the tower within the client's scope.\n\n    Returns:\n        A `pathlib.Path` object representing the path to the case directory.\n\n    Raises:\n        OSError: If the directory cannot be created due to filesystem errors,\n            such as insufficient permissions."}."""
    case_dir = resolve_client_dir(client_id) / tower_id
    case_dir.mkdir(parents=True, exist_ok=True)
    env["ASSESSMENT_CLIENT_ID"] = client_id
    env["ASSESSMENT_TOWER_ID"] = tower_id
    env["ASSESSMENT_CASE_DIR"] = str(case_dir)
    return case_dir


def validate_runtime_environment(env: dict[str, str]) -> None:
    """Validates required environment variables for the Vertex AI runtime.

    Ensures that both `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` are
    present as keys in the provided environment dictionary and that their
    corresponding values are non-empty strings after stripping whitespace.

    Args:
        env: A dictionary representing the environment variables to validate.

    Raises:
        RuntimeError: If either `GOOGLE_CLOUD_PROJECT` or
            `GOOGLE_CLOUD_LOCATION` is missing, or if its value is an empty
            or whitespace-only string.
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
    """Resolve the timeout in seconds for a designated AI pipeline step.

    Identifies a step as an AI component if its name contains "Engine:" or
    "Refinement". If so, this function retrieves the timeout value from the
    environment variable specified by the `AI_STEP_TIMEOUT_ENV` constant.

    Args:
        env: The dictionary of environment variables to search for the timeout
            configuration.
        step_name: The name of the pipeline step to evaluate.

    Returns:
        The timeout in seconds as a float if the step is an AI step and a
        valid, positive timeout is configured. Returns None if the step is not
        an AI step or if no timeout is specified.

    Raises:
        RuntimeError: If the configured timeout value is present but is not a
            positive floating-point number.
    """
    if "Engine:" not in step_name and "Refinement" not in step_name:
        return None

    raw_value = str(env.get(AI_STEP_TIMEOUT_ENV, "")).strip()
    if not raw_value:
        return None

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
    """Executes a Python module as a pipeline step in a controlled environment.

    This function simulates a command-line invocation (e.g.,
    `python -m my_module.main --arg1 val1`) for a Python module. It operates
    by dynamically importing the target module, patching `sys.argv` with the
    provided arguments, and setting a specific execution environment via `os.environ`.

    Execution is isolated: a temporary environment is constructed from a base
    configuration and updated with the provided `env` dictionary. The calling
    process's environment is saved and fully restored upon completion or failure
    of the step, preventing side effects.

    The target module must contain a `main()` function. If `main` is a
    coroutine, it is executed via `asyncio.run()`.

    Args:
        cmd_args: A list of strings representing the command-line invocation.
            The list must follow the format `['<executable>', '-m',
            '<module_name>', ...args]`. The first element is ignored but is
            conventionally required.
        step_name: The name of the pipeline step, used for contextual logging
            and error reporting.
        env: A dictionary of environment variables to set for the duration of
            the module's execution. These override any base environment variables.

    Raises:
        ValueError: If `cmd_args` has fewer than three elements or its second
            element is not `'-m'`.
        ImportError: If the module specified in `cmd_args` cannot be found or
            imported.
        RuntimeError: If the target module does not have a `main` function, if
            module execution raises an unhandled exception, or if it terminates
            via `SystemExit` with a non-zero exit code.
    """
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
