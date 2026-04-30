"""
Módulo run_commercial_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import os
import sys
import importlib
import asyncio
from unittest.mock import patch
from pathlib import Path
from assessment_engine.scripts.lib.runtime_env import (
    ensure_google_cloud_env_defaults,
    run_vertex_ai_preflight,
)

ROOT = Path(__file__).resolve().parents[3]


def run_step(cmd_args: list[str], step_name: str) -> None:
    print(f"\n=== {step_name} ===")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    for k, v in env.items():
        os.environ[k] = v

    if len(cmd_args) >= 3 and cmd_args[1] == "-m":
        module_name = cmd_args[2]
        script_args = cmd_args[3:]
    else:
        raise ValueError(f"Comando no soportado por run_native_step: {cmd_args}")

    mock_argv = [module_name] + script_args
    try:
        with patch.object(sys, 'argv', mock_argv):
            mod = importlib.import_module(module_name)
            importlib.reload(mod)
            if hasattr(mod, 'main'):
                result = mod.main()
                if asyncio.iscoroutine(result):
                    asyncio.run(result)
            else:
                raise RuntimeError(f"El módulo {module_name} no tiene función main()")
    except SystemExit as e:
        if e.code != 0 and e.code is not None:
            raise RuntimeError(f"Fallo nativo (SystemExit) en {step_name} con código: {e.code}")
        else:
            print(f"[{step_name}] Finalizado con exit(0)")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"Fallo nativo en {step_name} con error: {e}")


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python -m scripts.run_commercial_pipeline <client_name>")
        sys.exit(1)

    client_name = (argv if argv is not None else sys.argv)[1]
    client_dir = ROOT / "working" / client_name
    env = os.environ.copy()
    ensure_google_cloud_env_defaults(env)
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        preflight = run_vertex_ai_preflight(env=env)
        print(
            "✅ Vertex AI listo "
            f"(project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
        )

    global_payload_path = client_dir / "global_report_payload.json"
    commercial_payload_path = client_dir / "commercial_report_payload.json"
    template_path = (
        ROOT
        / "source_docs"
        / "templates"
        / "11. Template Documento General Alpha v.05.docx"
    )
    output_path = client_dir / f"Account_Action_Plan_{client_name}.docx"

    python_bin = str(ROOT / ".venv" / "bin" / "python")
    if not Path(python_bin).exists():
        python_bin = sys.executable

    # 1. Ejecutar Refinador Comercial Multi-Agente
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.run_commercial_refiner",
            str(global_payload_path),
        ],
        "Multi-Agent Commercial Refinement",
    )

    # 2. Renderizar Documento Word Confidencial
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.render_commercial_report",
            str(commercial_payload_path),
            str(template_path),
            str(output_path),
        ],
        "Render Account Action Plan",
    )

    print(
        f"\n¡Pipeline Comercial finalizado con éxito! Documento generado: {output_path}"
    )


if __name__ == "__main__":
    main()
