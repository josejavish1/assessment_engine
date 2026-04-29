"""
Módulo run_global_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import os
import sys
import importlib
import asyncio
from unittest.mock import patch
from pathlib import Path

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
        print("Uso: python -m scripts.run_global_pipeline <client_name>")
        sys.exit(1)

    client_name = (argv if argv is not None else sys.argv)[1]
    client_dir = ROOT / "working" / client_name

    payload_path = client_dir / "global_report_payload.json"
    template_path = (
        ROOT
        / "source_docs"
        / "templates"
        / "11. Template Documento General Alpha v.05.docx"
    )
    output_path = client_dir / f"Informe_Ejecutivo_Consolidado_{client_name}.docx"

    python_bin = str(ROOT / ".venv" / "bin" / "python")
    if not Path(python_bin).exists():
        python_bin = sys.executable

    # 1. Generar Payload Inicial
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.build_global_report_payload",
            str(client_dir),
            client_name,
            str(payload_path),
        ],
        "Build Global Payload",
    )

    # 2. Refinado Estratégico con IA (CIO Level)
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.run_executive_refiner",
            str(payload_path),
        ],
        "Strategic Executive Refinement",
    )

    # 3. Generar Visuales
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.generate_global_radar_chart",
            str(payload_path),
        ],
        "Generate Global Radar Chart",
    )
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.generate_executive_roadmap_image",
            str(payload_path),
        ],
        "Generate Executive Roadmap Visual",
    )

    # 4. Renderizar DOCX
    run_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.render_global_report_from_template",
            str(payload_path),
            str(template_path),
            str(output_path),
        ],
        "Render Global DOCX (CIO-Ready)",
    )

    print(f"\nInforme Global Estratégico finalizado: {output_path}")


if __name__ == "__main__":
    main()
