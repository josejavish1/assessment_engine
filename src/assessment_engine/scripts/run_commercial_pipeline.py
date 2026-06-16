"""
Módulo run_commercial_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""

import sys

from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
    run_module_step,
)
from assessment_engine.scripts.lib.runtime_env import run_vertex_ai_preflight
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_client_dir,
    resolve_commercial_report_payload_path,
    resolve_global_report_payload_path,
    resolve_global_report_template_path,
)


def main(argv: list[str] | None = None) -> None:
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python -m scripts.run_commercial_pipeline <client_name>")
        sys.exit(1)

    client_name = (argv if argv is not None else sys.argv)[1]
    client_dir = resolve_client_dir(client_name)
    env = build_runtime_env()
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        preflight = run_vertex_ai_preflight(env=env)
        print(
            "✅ Vertex AI listo "
            f"(project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
        )

    global_payload_path = resolve_global_report_payload_path(client_name)
    commercial_payload_path = resolve_commercial_report_payload_path(client_name)
    template_path = resolve_global_report_template_path()
    output_path = client_dir / f"Account_Action_Plan_{client_name}.docx"

    python_bin = resolve_python_bin()

    # 1. Ejecutar Refinador Comercial Multi-Agente
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.run_commercial_refiner",
            str(global_payload_path),
        ],
        "Multi-Agent Commercial Refinement",
        env,
    )

    # 2. Renderizar Documento Word Confidencial
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.render_commercial_report",
            str(commercial_payload_path),
            str(template_path),
            str(output_path),
        ],
        "Render Account Action Plan",
        env,
    )

    print(
        f"\n¡Pipeline Comercial finalizado con éxito! Documento generado: {output_path}"
    )


if __name__ == "__main__":
    main()
