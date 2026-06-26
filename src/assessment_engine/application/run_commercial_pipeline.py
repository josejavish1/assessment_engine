"""Provides the primary entry point and orchestration logic for the commercial assessment pipeline."""

import sys

from assessment_engine.infrastructure.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
    run_module_step,
)
from assessment_engine.infrastructure.runtime_env import run_vertex_ai_preflight
from assessment_engine.infrastructure.runtime_paths import (
    resolve_client_dir,
    resolve_commercial_report_payload_path,
    resolve_global_report_payload_path,
    resolve_global_report_template_path,
)


def main(argv: list[str] | None = None) -> None:
    r"""{'docstring': 'Orchestrate the commercial data processing and report generation pipeline.\n\n    This function serves as the main entry point for processing a specific client\'s\n    data and generating a final "Account Action Plan" report. The pipeline is\n    driven by a single command-line argument: the client\'s name.\n\n    The pipeline consists of two primary phases executed as separate Python\n    modules:\n    1.  Data Refinement: Invokes `application.run_commercial_refiner` to\n        process and structure the client\'s raw data payload using a\n        multi-agent system.\n    2.  Report Rendering: Invokes `adapters.render_commercial_report` to render\n        the refined data into a Microsoft Word (.docx) document using a\n        predefined template.\n\n    Prior to execution, an optional preflight check verifies the Vertex AI\n    environment. This check can be disabled by setting the\n    `ASSESSMENT_SKIP_VERTEX_PREFLIGHT` environment variable to "1". All file\n    paths for input payloads, templates, and outputs are resolved dynamically\n    based on the provided client name.\n\n    Args:\n        argv: A list of command-line arguments. If None, `sys.argv` is used.\n            The script expects the second element (`argv[1]`) to be the\n            client\'s name.\n\n    Returns:\n        None.\n\n    Raises:\n        SystemExit: If the required client name argument is not provided.\n        FileNotFoundError: If the client directory, input payload files, or\n            report template cannot be located by the path resolution helpers.\n        subprocess.CalledProcessError: If the data refinement or report rendering\n            sub-modules fail during execution.'}."""
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

    # Phase 1: Refine and structure the commercial data inputs using the designated multi-agent system.
    run_module_step(
        [
            python_bin,
            "-m",
            "assessment_engine.application.run_commercial_refiner",
            str(global_payload_path),
        ],
        "Multi-Agent Commercial Refinement",
        env,
    )

    # Phase 2: Generate the final output artifact, a confidential Microsoft Word document, from the refined commercial data.
    run_module_step(
        [
            python_bin,
            "-m",
            "adapters.render_commercial_report",
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
