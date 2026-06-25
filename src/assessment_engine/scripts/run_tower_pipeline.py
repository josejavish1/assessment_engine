"""Defines the primary orchestration logic for the Assessment Engine pipeline.

This module implements a Directed Acyclic Graph (DAG) based asynchronous orchestrator
that executes pipeline stages in isolated subprocesses to mitigate global state
corruption and race conditions.
"""

import argparse
import asyncio
import os
import unicodedata
from pathlib import Path

from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
    prepare_case_runtime,
    resolve_ai_step_timeout_seconds,
    resolve_python_bin,
    validate_runtime_environment,
)
from assessment_engine.scripts.lib.runtime_env import (
    run_vertex_ai_preflight,
)
from assessment_engine.scripts.lib.runtime_paths import (
    resolve_blueprint_payload_path,
    resolve_tower_annex_template_path,
)

SKIP_MODE = False
START_FROM = None


def slugify(value: str) -> str:
    """Generate a sanitized, ASCII-based slug from a string.

    Converts the input string into a URL-friendly slug. The transformation
    involves NFKD Unicode normalization, ASCII-encoding with lossy character
    conversion, replacement of non-alphanumeric characters with underscores,
    conversion to lowercase, and collapsing of consecutive underscores.

    Args:
        value (str): The string to convert into a slug.

    Returns:
        str: The resulting slug. If the transformation results in an empty
            string, the default value 'client' is returned instead.
    """
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in ascii_value)
    return "_".join(part for part in cleaned.lower().split("_") if part) or "client"


async def run_step_async(
    cmd_args: list[str], env: dict[str, str], step_name: str
) -> None:
    """Execute a pipeline step in an isolated, asynchronous subprocess.

    Ensures process-level state isolation (e.g., `sys.argv`, `os.environ`) to
    facilitate safe, concurrent execution of pipeline stages. The function
    manages the full lifecycle of the subprocess, including its creation,
    environment variable injection, real-time streaming of stdout and stderr, and
    timeout enforcement.

    The execution of a step can be conditionally skipped. This behavior is
    controlled by the global module-level variables `SKIP_MODE` and `START_FROM`,
    which enables pipelines to be resumed from a specified step.

    Args:
        cmd_args: A list of strings representing the command and its arguments
            to execute.
        env: A dictionary of environment variables to set for the subprocess.
            These variables augment the parent process's environment.
        step_name: The human-readable name of the pipeline step, used for
            logging and error reporting.

    Returns:
        None

    Raises:
        RuntimeError: If the subprocess exits with a non-zero status code,
            exceeds its configured execution timeout, or if a critical error
            occurs during subprocess instantiation.
    """
    global SKIP_MODE
    if SKIP_MODE:
        if START_FROM and step_name == START_FROM:
            SKIP_MODE = False
            print(f"\n▶️  Reanudando en: {step_name}")
        else:
            print(f"⏭️  Saltando: {step_name}")
            return

    print(f"\n=== {step_name} (Iniciado) ===")

    # Injects custom environment variables into the subprocess environment to configure its execution context and behavior.
    process_env = os.environ.copy()
    process_env.update(env)
    timeout_seconds = resolve_ai_step_timeout_seconds(process_env, step_name)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if timeout_seconds is not None:
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError as exc:
                process.kill()
                stdout, stderr = await process.communicate()
                raise RuntimeError(
                    f"Timeout en {step_name} tras {timeout_seconds:.0f}s."
                ) from exc
        else:
            stdout, stderr = await process.communicate()

        # Asynchronously streams the subprocess's stdout and stderr to the main process's logger to ensure real-time visibility into its execution status and to capture diagnostic information.
        if stdout:
            print(stdout.decode("utf-8").strip())

        if process.returncode != 0:
            err_msg = stderr.decode("utf-8").strip()
            raise RuntimeError(
                f"Fallo nativo en {step_name} (Exit {process.returncode}):\n{err_msg}"
            )

        print(f"✅ {step_name} (Completado)")

    except Exception as e:
        raise RuntimeError(f"Error crítico lanzando {step_name}: {e}")


async def run_pipeline():
    """Orchestrates an asynchronous, multi-stage pipeline for technology tower assessments.

    This function serves as the primary entry point for executing a complete assessment.
    It consumes command-line arguments to configure the pipeline's inputs and
    behavior. The pipeline can be resumed from a specific step if a previous run
    was interrupted.

    The pipeline proceeds through several distinct phases:
    1.  **Initialization**: Parses arguments, builds a runtime environment, and
        creates a unique case directory for all generated artifacts.
    2.  **Foundational Analysis**: Sequentially executes scripts to generate core
        data, including the case input, evidence ledger, scoring data, and
        evidence analysis.
    3.  **Strategic Synthesis**: Executes a top-down synthesis flow, including an
        optional Vertex AI preflight check, followed by the core strategic
        blueprint and executive annex synthesizer engines.
    4.  **Parallel Rendering**: Concurrently renders the final output documents
        using `asyncio.gather`, producing a comprehensive Strategic Blueprint
        DOCX and a standardized executive summary annex DOCX.

    Command-line arguments are used for configuration instead of function parameters:
        --tower: The technology tower identifier (e.g., "SECURITY").
        --client: The name of the client being assessed.
        --context-file: Path to the input context JSON file.
        --responses-file: Path to the input responses JSON file.
        --start-from (optional): The name of the step to resume execution from.

    Returns:
        None. The function's side effects include the creation of a case
        directory populated with intermediate analysis files and final report
        documents.

    Raises:
        Exception: Propagated from failures in underlying asynchronous subprocess
            calls, which may indicate script execution errors or file I/O issues.
            Critical failures during the strategic synthesis phase will terminate
            execution.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    parser.add_argument(
        "--start-from", required=False, help="Nombre del step desde el que reanudar"
    )
    args = parser.parse_args()

    global SKIP_MODE, START_FROM
    if args.start_from:
        SKIP_MODE = True
        START_FROM = args.start_from

    tower_id = args.tower.upper().strip()
    client_slug = slugify(args.client)
    python_bin = resolve_python_bin()

    env = build_runtime_env()
    case_dir = prepare_case_runtime(
        env,
        client_id=client_slug,
        tower_id=tower_id,
    )

    validate_runtime_environment(env)

    context_path = str(Path(args.context_file).resolve())
    responses_path = str(Path(args.responses_file).resolve())

    annex_stem = f"approved_annex_{tower_id.lower()}"
    payload_path = case_dir / f"{annex_stem}.template_payload.json"
    template_annex_path = resolve_tower_annex_template_path()
    output_docx = case_dir / f"annex_{tower_id.lower()}_{client_slug}_final.docx"

    # Phase 1: Sequential, deterministic preparation of foundational data and environment.
    await run_step_async(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.build_case_input",
            "--client",
            args.client,
            "--tower",
            tower_id,
            "--context-file",
            context_path,
            "--responses-file",
            responses_path,
        ],
        env,
        "Build case_input",
    )

    await run_step_async(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.build_evidence_ledger",
            "--case-input",
            str(case_dir / "case_input.json"),
            "--context-file",
            context_path,
            "--responses-file",
            responses_path,
        ],
        env,
        "Build evidence_ledger",
    )
    await run_step_async(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.run_scoring",
            "--case-input",
            str(case_dir / "case_input.json"),
        ],
        env,
        "Run scoring",
    )
    await run_step_async(
        [
            python_bin,
            "-m",
            "assessment_engine.scripts.run_evidence_analyst",
            "--case-input",
            str(case_dir / "case_input.json"),
            "--evidence-ledger",
            str(case_dir / "evidence_ledger.json"),
            "--scoring-output",
            str(case_dir / "scoring_output.json"),
        ],
        env,
        "Run evidence analyst",
    )

    # Implements the top-down phase of the Strangler Fig pattern, migrating from the legacy Blueprint model to the new Annex architecture.
    print(
        "\n🚀 Iniciando Flujo Top-Down: Blueprint Estratégico (Single Source of Truth)..."
    )
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        print("🔎 Ejecutando preflight de Vertex AI...")
        preflight = run_vertex_ai_preflight(env=env)
        print(
            "✅ Vertex AI listo "
            f"(project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
        )
    blueprint_payload_path = resolve_blueprint_payload_path(client_slug, tower_id)
    output_blueprint_docx = (
        case_dir / f"Blueprint_Transformacion_{tower_id}_{client_slug}.docx"
    )

    try:
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.run_tower_blueprint_engine",
                args.client,
                tower_id,
            ],
            env,
            "Engine: Tower Strategic Blueprint",
        )
    except Exception as e:
        print(f"⚠️ Fallo crítico en Blueprint: {e}")
        return

    print("\n🚀 Iniciando Síntesis Ejecutiva (El Nuevo Anexo Top-Down)...")
    try:
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.run_executive_annex_synthesizer",
                args.client,
                tower_id,
            ],
            env,
            "Engine: Executive Annex Synthesizer",
        )
    except Exception as e:
        print(f"⚠️ Fallo en síntesis del anexo: {e}")

    # Legacy code block decommissioned during a phased migration. This code is preserved but commented out to prevent a split-brain scenario where both old and new logic could execute concurrently.
    # Phase 2: Parallel execution of agentic generation tasks (Branch A).
    #
    #
    #
    #
    # The OSINT (Open-Source Intelligence) gathering step is not executed on a per-tower basis in the current architecture. This node is maintained as a placeholder for potential future activation or re-implementation.
    #
    #
    # Phase 3: Parallel execution of strategic analysis tasks (Branch B).
    #
    #
    #
    #
    #
    #
    # Phase 4: Sequential aggregation and finalization of report components (Branch C).
    #
    #
    #
    # Phase 5: Final document assembly and rendering.
    #
    #
    #
    #
    #

    # Defines the final rendering pipeline stage, which has been refactored to consume the standardized payload format produced by the Synthesizer service.
    async def render_standard_report():
        """Asynchronously renders a DOCX report from a standardized payload.

        Invokes an external Python script (`render_tower_annex_from_template`) to
        perform the final rendering stage of the report generation pipeline. This
        function consumes a standardized payload file produced by an upstream
        'Synthesizer' service.

        Note:
            This function does not accept arguments directly. It relies on the
            following variables being present in its execution context:
            - `python_bin` (str): Path to the Python interpreter.
            - `payload_path` (str): Path to the input JSON payload file.
            - `template_annex_path` (str): Path to the DOCX template file.
            - `output_docx` (str): Path for the generated DOCX report.
            - `env` (dict): Environment variables for the subprocess.

        Returns:
            None. The function's primary side effect is writing a DOCX file to
            the path specified by the `output_docx` context variable.

        Raises:
            Exception: If the underlying `run_step_async` call fails, which can
                be caused by a non-zero exit code from the rendering script or by
                missing input files (e.g., payload, template).
        """
        # The assembly and refinement stages are deprecated. The upstream Synthesizer service is now responsible for generating the final `payload_path`, which is directly consumable by the rendering stage.
        #
        #
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.render_tower_annex_from_template",
                str(payload_path),
                str(template_annex_path),
                str(output_docx),
                "--semantic-styles",
            ],
            env,
            "Render short DOCX",
        )

    async def run_blueprint_flow():
        """Asynchronously executes the Tower Strategic Blueprint rendering process.

        This coroutine checks for the existence of an input payload file specified by the global `blueprint_payload_path` variable. If the file is present, it spawns an asynchronous subprocess to execute the `render_tower_blueprint` script. The subprocess is invoked using the interpreter path from the global `python_bin` and the environment from the global `env`.

        All exceptions encountered during the subprocess execution are caught and suppressed. A warning message is printed to standard output, ensuring that failures in this step do not interrupt the parent execution flow.

        Returns:
            None
        """
        try:
            if blueprint_payload_path.exists():
                await run_step_async(
                    [
                        python_bin,
                        "-m",
                        "assessment_engine.scripts.render_tower_blueprint",
                        str(blueprint_payload_path),
                        str(output_blueprint_docx),
                    ],
                    env,
                    "Render: Tower Strategic Blueprint DOCX",
                )
        except Exception as e:
            print(f"⚠️ Fallo no bloqueante en Blueprint Render: {e}")

    print("\n🚀 Finalizando: Renderizado Estándar + Blueprint en paralelo...")
    await asyncio.gather(render_standard_report(), run_blueprint_flow())

    print(f"\n✅ Pipeline {tower_id} completado con éxito.")
    print(f"📄 DOCX Resumen Ejecutivo: {output_docx}")
    print(f"🚀 DOCX Blueprint Estratégico (Definitivo): {output_blueprint_docx}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
