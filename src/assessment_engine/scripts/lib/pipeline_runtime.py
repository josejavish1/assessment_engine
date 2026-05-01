"""
Helpers comunes para entrypoints de pipeline basados en módulos Python.
"""

import asyncio
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults
from assessment_engine.scripts.lib.runtime_paths import ROOT, resolve_client_dir

AI_STEP_TIMEOUT_ENV = "ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"


def resolve_python_bin() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def build_runtime_env(
    base_env: dict[str, str] | None = None,
    *,
    include_pythonpath: bool = True,
) -> dict[str, str]:
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
    case_dir = resolve_client_dir(client_id) / tower_id
    case_dir.mkdir(parents=True, exist_ok=True)
    env["ASSESSMENT_CLIENT_ID"] = client_id
    env["ASSESSMENT_TOWER_ID"] = tower_id
    env["ASSESSMENT_CASE_DIR"] = str(case_dir)
    return case_dir


def validate_runtime_environment(env: dict[str, str]) -> None:
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
    print(f"\n=== {step_name} ===")

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
        print(f"[{step_name}] Finalizado con exit(0)")
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise RuntimeError(f"Fallo nativo en {step_name} con error: {exc}") from exc
    finally:
        os.environ.clear()
        os.environ.update(original_env)
