"""
Módulo run_global_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
"""
import argparse
import sys

from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
    run_module_step,
)
from assessment_engine.scripts.lib.runtime_env import run_vertex_ai_preflight
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_client_dir,
    resolve_global_report_payload_path,
    resolve_global_report_template_path,
)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("client_name")
    parser.add_argument(
        "--blueprint-only",
        action="store_true",
        help="Construye el payload global solo desde blueprints y desactiva el fallback legacy.",
    )
    args = parser.parse_args((argv if argv is not None else sys.argv)[1:])

    client_name = args.client_name
    client_dir = resolve_client_dir(client_name)
    env = build_runtime_env()
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        preflight = run_vertex_ai_preflight(env=env)
        print(
            "✅ Vertex AI listo "
            f"(project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
        )

    payload_path = resolve_global_report_payload_path(client_name)
    template_path = resolve_global_report_template_path()
    output_path = client_dir / f"Informe_Ejecutivo_Consolidado_{client_name}.docx"

    python_bin = resolve_python_bin()

    # 1. Generar Payload Inicial
    run_module_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.build_global_report_payload",
            str(client_dir),
            client_name,
            str(payload_path),
            *(["--blueprint-only"] if args.blueprint_only else []),
        ],
        "Build Global Payload",
        env,
    )

    # 2. Refinado Estratégico con IA (CIO Level)
    run_module_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.run_executive_refiner",
            str(payload_path),
        ],
        "Strategic Executive Refinement",
        env,
    )

    # 3. Generar Visuales
    run_module_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.generate_global_radar_chart",
            str(payload_path),
        ],
        "Generate Global Radar Chart",
        env,
    )
    run_module_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.generate_executive_roadmap_image",
            str(payload_path),
        ],
        "Generate Executive Roadmap Visual",
        env,
    )

    # 4. Renderizar DOCX
    run_module_step(
        [
            python_bin,
            "-m", "assessment_engine.scripts.render_global_report_from_template",
            str(payload_path),
            str(template_path),
            str(output_path),
        ],
        "Render Global DOCX (CIO-Ready)",
        env,
    )

    print(f"\nInforme Global Estratégico finalizado: {output_path}")


if __name__ == "__main__":
    main()
