"""Main entry point for orchestrating the end-to-end Assessment Engine pipeline."""

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
    r"""{'docstring': 'Orchestrates the end-to-end pipeline to generate a consolidated executive report.\n\n    This function serves as the main entry point for the global report generation\n    script. It executes a multi-stage pipeline by invoking a series of\n    subordinate modules as separate processes. The pipeline stages include:\n\n    1.  Payload Generation: Constructs a core JSON data payload from various\n        client-specific input sources.\n    2.  AI Refinement: Processes the JSON payload through an AI model to\n        synthesize high-level strategic insights.\n    3.  Visuals Generation: Creates data visualizations, including a radar\n        chart and an executive roadmap image, from the refined payload.\n    4.  DOCX Rendering: Assembles the structured content and generated visuals\n        into a final DOCX report using a predefined template.\n\n    An optional preflight check is performed to validate the Vertex AI\n    environment configuration. This check can be disabled by setting the\n    `ASSESSMENT_SKIP_VERTEX_PREFLIGHT` environment variable to "1".\n\n    Args:\n        argv: Command-line arguments, where the first element after the script\n            name is the client name. If `None`, `sys.argv` is used.\n\n    Returns:\n        None. This function produces a DOCX file as a side effect and prints its\n        path to standard output upon successful completion.\n\n    Raises:\n        SystemExit: If the client name is not provided as a command-line\n            argument.\n        FileNotFoundError: If the directory for the specified client or a\n            required template file cannot be found.\n        Exception: Propagates exceptions from the preflight check or any of the\n            pipeline subprocesses, indicating a failure in a specific stage.'}."""
    if len(argv if argv is not None else sys.argv) < 2:
        print("Uso: python -m scripts.run_global_pipeline <client_name>")
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

    payload_path = resolve_global_report_payload_path(client_name)
    template_path = resolve_global_report_template_path()
    output_path = client_dir / f"Informe_Ejecutivo_Consolidado_{client_name}.docx"

    python_bin = resolve_python_bin()

    # Stage 1: Initial Payload Generation. Constructs the core data payload from various input sources, forming the basis for subsequent analysis.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.build_global_report_payload",
            str(client_dir),
            client_name,
            str(payload_path),
        ],
        "Build Global Payload",
        env,
    )

    # Stage 2: AI-driven Strategic Refinement. The initial payload is processed by AI models to synthesize high-level strategic insights and narrative themes.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.run_executive_refiner",
            str(payload_path),
        ],
        "Strategic Executive Refinement",
        env,
    )

    # Stage 3: Visuals Generation. Generates data visualizations, such as charts and diagrams, based on the refined payload data.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.generate_global_radar_chart",
            str(payload_path),
        ],
        "Generate Global Radar Chart",
        env,
    )
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.generate_executive_roadmap_image",
            str(payload_path),
        ],
        "Generate Executive Roadmap Visual",
        env,
    )

    # Stage 4: DOCX Document Rendering. Assembles the structured content and generated visuals into a final, formatted DOCX report.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.render_global_report_from_template",
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
