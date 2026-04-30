"""
Helpers comunes para entrypoints de pipeline basados en módulos Python.
"""

from __future__ import annotations

import asyncio
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

from assessment_engine.scripts.lib.runtime_env import ensure_google_cloud_env_defaults
from assessment_engine.scripts.lib.runtime_paths import ROOT


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
