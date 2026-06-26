"""Defines the primary orchestration logic and core utilities for the Assessment Engine pipeline."""

import sys

from assessment_engine.infrastructure.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
    run_module_step,
)
from assessment_engine.infrastructure.runtime_env import run_vertex_ai_preflight
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_dir,
    resolve_global_report_payload_path,
    resolve_global_report_template_path,
)


def main(argv: list[str] | None = None) -> None:
    """Run the end-to-end global strategic assessment pipeline for a client.

    Serves as the main command-line entry point, orchestrating a sequence of
    modules as isolated subprocesses to generate a consolidated executive
    report and an interactive digital twin interface.

    The pipeline execution consists of the following stages:
      1. Generation of a data payload from the Sovereign Graph Engine.
      2. Export of the current graph state as a Data Transfer Object (DTO).
      3. AI-driven refinement of the payload for executive-level analysis.
      4. Generation of data visualizations (e.g., radar chart, roadmap).
      5. Rendering of the final DOCX report from a template.
      6. Rendering of the interactive Lineage Matrix Explorer portal.

    The pipeline requires a single command-line argument specifying the
    `client_name`, which is used to resolve input data paths and name the
    final output artifacts.

    Args:
        argv: A list of command-line arguments. If None, `sys.argv` is used.
            The first argument after the script name must be the `client_name`.

    Raises:
        FileNotFoundError: If the client directory or required template files
            cannot be located based on the provided `client_name`.
        subprocess.CalledProcessError: If any of the external module
            subprocesses return a non-zero exit code.
        RuntimeError: If the Vertex AI preflight check fails due to issues such
            as authentication or API configuration.
    """
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

    # Step 1: Generate the initial data payload via the Sovereign Graph Engine.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.build_global_report_payload",
            str(client_dir),
            client_name,
            str(payload_path),
        ],
        "Build Global Payload (Graph-Based Roadmap)",
        env,
    )

    # Step 1.5: Export the current state object as a Data Transfer Object (DTO) for the Digital Twin.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.export_graph_state",
            client_name,
        ],
        "Export Digital Twin State Object",
        env,
    )

    # Step 2: Apply strategic refinement using an AI model configured for CIO-level analysis.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.run_executive_refiner",
            "--findings-path",
            str(payload_path),
            "--client",
            client_name,
        ],
        "Strategic Executive Refinement",
        env,
    )

    # Step 3: Generate all required data visualizations and graphics.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.generate_global_radar_chart",
            str(payload_path),
        ],
        "Generate Global Radar Chart",
        env,
    )
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.generate_executive_roadmap_image",
            str(payload_path),
        ],
        "Generate Executive Roadmap Visual",
        env,
    )

    # Step 4: Render the final assessment report in DOCX format.
    run_module_step(
        [
            python_bin,
            "-m",
            "adapters.render_global_report_from_template",
            str(payload_path),
            str(template_path),
            str(output_path),
        ],
        "Render Global DOCX (CIO-Ready)",
        env,
    )

    # Step 5: Render the interactive Lineage Matrix Explorer Portal, which serves as the digital twin interface.
    run_module_step(
        [
            python_bin,
            "-m",
            "adapters.render_lineage_portal",
            client_name,
        ],
        "Render Lineage Matrix Explorer Portal",
        env,
    )

    print(f"\nInforme Global Estratégico finalizado: {output_path}")


if __name__ == "__main__":
    main()
