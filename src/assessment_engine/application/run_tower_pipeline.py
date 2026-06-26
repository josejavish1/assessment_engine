"""Provides the core orchestration logic for the Assessment Engine pipeline. The module defines a Directed Acyclic Graph (DAG) of stages, where each stage is executed in an isolated subprocess to prevent state interference and resource contention between steps."""

import argparse
import asyncio
import os
import unicodedata
from pathlib import Path

from assessment_engine.infrastructure.pipeline_runtime import (
    build_runtime_env,
    prepare_case_runtime,
    resolve_ai_step_timeout_seconds,
    resolve_python_bin,
    validate_runtime_environment,
)
from assessment_engine.infrastructure.runtime_env import (
    run_vertex_ai_preflight,
)
from assessment_engine.infrastructure.runtime_paths import (
    resolve_blueprint_payload_path,
    resolve_tower_annex_template_path,
)

SKIP_MODE = False
START_FROM = None


def slugify(value: str) -> str:
    """Convert a string into a URL-compatible slug."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in ascii_value)
    return "_".join(part for part in cleaned.lower().split("_") if part) or "client"


async def run_step_async(
    cmd_args: list[str], env: dict[str, str], step_name: str
) -> None:
    """Asynchronously executes a command in an isolated subprocess for a pipeline step.

    This function launches the specified command in a new process, ensuring that
    any environment variable modifications do not affect the parent process or
    other concurrent steps. It asynchronously captures and streams the
    subprocess's stdout and stderr. For long-running operations, a periodic
    heartbeat message is printed to the console to indicate that the process
    is still active.

    The execution of the step is conditional, governed by the module-level
    `SKIP_MODE` and `START_FROM` variables, allowing for pipeline steps to be
    skipped or resumed from a specific point. A configurable timeout is
    enforced, and the subprocess will be terminated if it exceeds this limit.

    Args:
        cmd_args: A list containing the command to execute as the first
            element and its subsequent arguments.
        env: A dictionary of environment variables to set for the subprocess.
            These are merged with, and take precedence over, the parent
            process's environment variables.
        step_name: A descriptive name for the pipeline step, used for
            logging, error messages, and conditional execution logic.

    Raises:
        RuntimeError: If the subprocess returns a non-zero exit code, if the
            execution time exceeds the configured timeout, or if a critical
            error occurs during subprocess creation or management.
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

    process_env = os.environ.copy()
    process_env.update(env)
    timeout_seconds = resolve_ai_step_timeout_seconds(process_env, step_name)

    async def _communicate_with_heartbeat(proc, timeout_sec=None):
        import time

        start_time = time.time()
        stdout_chunks = []
        stderr_chunks = []

        async def read_stream(stream, chunks):
            """Asynchronously reads all lines from a stream and appends them to a list.

            This coroutine consumes the provided stream until an End-Of-File (EOF) is
            detected. The function mutates the `chunks` list argument in-place.

            Args:
                stream (Optional[asyncio.StreamReader]): The asynchronous stream to read
                    from, such as a process's stdout or stderr. If `None`, the function
                    returns immediately.
                chunks (List[bytes]): A list to which the lines read from the stream,
                    as bytes, are appended.
            """
            if stream is None:
                return
            while True:
                line = await stream.readline()
                if not line:
                    break
                chunks.append(line)

        out_task = asyncio.create_task(read_stream(proc.stdout, stdout_chunks))
        err_task = asyncio.create_task(read_stream(proc.stderr, stderr_chunks))

        last_heartbeat = time.time()
        while not out_task.done() or not err_task.done() or proc.returncode is None:
            if timeout_sec is not None and (time.time() - start_time) > timeout_sec:
                proc.kill()
                raise asyncio.TimeoutError()
            if time.time() - last_heartbeat > 30:
                print(
                    "⏳ [Heartbeat] El motor sigue trabajando en segundo plano...",
                    flush=True,
                )
                last_heartbeat = time.time()
            try:
                await asyncio.wait_for(asyncio.shield(proc.wait()), timeout=1.0)
            except asyncio.TimeoutError:
                pass

        await out_task
        await err_task
        return b"".join(stdout_chunks), b"".join(stderr_chunks)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if timeout_seconds is not None:
            try:
                stdout, stderr = await _communicate_with_heartbeat(
                    process, timeout_sec=timeout_seconds
                )
            except asyncio.TimeoutError as exc:
                process.kill()
                stdout, stderr = await process.communicate()
                raise RuntimeError(
                    f"Timeout en {step_name} tras {timeout_seconds:.0f}s."
                ) from exc
        else:
            stdout, stderr = await _communicate_with_heartbeat(process)

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
    r"""{'docstring': "Orchestrates the end-to-end execution of the assessment pipeline.\n\n    This asynchronous function serves as the primary entry point for the\n    assessment process. It parses command-line arguments and executes a\n    sequence of idempotent, cache-gated stages as isolated subprocesses.\n\n    Each stage generates a deterministic, intermediate artifact (e.g.,\n    `case_input.json`, `findings.json`). If an artifact for a stage already\n    exists in the case-specific output directory and the cache has not been\n    invalidated, the stage is skipped. This mechanism allows for resumable\n    and incremental pipeline executions.\n\n    The pipeline consists of the following stages:\n    1.  Case Input Construction: Builds the initial `case_input.json`.\n    2.  Evidence Ledger Assembly: Consolidates data into `evidence_ledger.json`.\n    3.  Quantitative Scoring: Produces `scoring_output.json`.\n    4.  Qualitative Analysis: Runs language models to generate `findings.json`.\n    5.  Blueprint Payload Generation: Synthesizes the strategic blueprint payload.\n    6.  Annex Payload Synthesis: Creates the executive annex payload.\n    7.  DOCX Rendering: Renders final Microsoft Word (.docx) reports in parallel.\n\n    Command-line Args:\n        --tower (str): The specific assessment tower ID (e.g., 'DATA_AI').\n        --client (str): The name of the client being assessed.\n        --context-file (str): Path to the JSON file with assessment context.\n        --responses-file (str): Path to the JSON file with client responses.\n        --start-from (str, optional): The stage name to start from, skipping\n            all preceding stages. Defaults to starting from the beginning.\n        --force (bool, optional): If present, invalidates the cache by deleting\n            existing intermediate artifacts, forcing re-computation.\n\n    Returns:\n        None. The function's primary side effect is writing artifacts to a\n        case-specific output directory on the file system.\n\n    Raises:\n        FileNotFoundError: If paths from `--context-file` or `--responses-file`\n            are invalid.\n        subprocess.CalledProcessError: If any pipeline stage subprocess exits\n            with a non-zero status code.\n        Exception: Propagates exceptions from runtime environment validation."}."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    parser.add_argument("--start-from", required=False, help="Step name to start from")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild everything and purge cache"
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
    case_dir = prepare_case_runtime(env, client_id=client_slug, tower_id=tower_id)

    # Defines the sequence of pipeline stages. Each stage is cache-gated and designed to be idempotent, producing a deterministic output artifact that allows subsequent runs to skip re-computation.
    # Cache invalidation is triggered by the `--force` command-line argument.
    if args.force:
        print(f"🔄 [Cognitive Reset] Purgando razonamiento previo para {tower_id}...")
        if case_dir.exists():
            for f in [
                "findings.json",
                "evidence_ledger.json",
                "blueprint_t2_payload.json",
                "case_input.json",
                "scoring_output.json",
                f"approved_annex_{tower_id.lower()}.template_payload.json",
            ]:
                path_to_del = case_dir / f
                if path_to_del.exists():
                    path_to_del.unlink()
    else:
        print(
            f"📈 [Incremental Mode] Respetando caché local existente en {case_dir}. Use --force para reconstruir de cero."
        )

    import time

    env["AI_EXECUTION_SEED"] = str(time.time())

    validate_runtime_environment(env)

    context_path = str(Path(args.context_file).resolve())
    responses_path = str(Path(args.responses_file).resolve())

    annex_stem = f"approved_annex_{tower_id.lower()}"
    payload_path = case_dir / f"{annex_stem}.template_payload.json"
    resolve_tower_annex_template_path()
    output_docx = case_dir / f"annex_{tower_id.lower()}_{client_slug}_final.docx"
    blueprint_payload_path = resolve_blueprint_payload_path(client_slug, tower_id)
    output_blueprint_docx = (
        case_dir / f"Blueprint_Transformacion_{tower_id}_{client_slug}.docx"
    )

    #
    # Stage 1: Construct the `case_input` data structure. This stage is cache-gated.
    #
    case_input_file = case_dir / "case_input.json"
    if (
        args.force
        or not case_input_file.exists()
        or case_input_file.stat().st_size == 0
    ):
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.build_case_input",
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
    else:
        print("⏭️  [Cache Bypass] Build case_input already generated. Skipping.")

    #
    # Stage 2: Assemble the `evidence_ledger` containing all data required for scoring. This stage is cache-gated.
    #
    evidence_ledger_file = case_dir / "evidence_ledger.json"
    if (
        args.force
        or not evidence_ledger_file.exists()
        or evidence_ledger_file.stat().st_size == 0
    ):
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.build_evidence_ledger",
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
    else:
        print("⏭️  [Cache Bypass] Build evidence_ledger already generated. Skipping.")

    #
    # Stage 3: Execute quantitative scoring models using the `evidence_ledger`. This stage is cache-gated.
    #
    scoring_file = case_dir / "scoring_output.json"
    if args.force or not scoring_file.exists() or scoring_file.stat().st_size == 0:
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_scoring",
                "--case-input",
                str(case_dir / "case_input.json"),
            ],
            env,
            "Run scoring",
        )
    else:
        print("⏭️  [Cache Bypass] Run scoring already generated. Skipping.")

    #
    # Stage 4: Execute the qualitative analysis chain, a sequence of language models (e.g., analyst, refiner). This stage is cache-gated.
    #
    findings_file = case_dir / "findings.json"
    if args.force or not findings_file.exists() or findings_file.stat().st_size == 0:
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_evidence_analyst",
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

        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_sota_researcher",
                "--findings-path",
                str(case_dir / "findings.json"),
                "--client",
                args.client,
            ],
            env,
            "Run SOTA researcher",
        )

        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_executive_refiner",
                "--findings-path",
                str(case_dir / "findings.json"),
                "--client",
                args.client,
            ],
            env,
            "Run executive refiner",
        )
        print(
            "⏳ [Sovereign QA] Esperando asentamiento físico del archivo findings.json en disco..."
        )
        await asyncio.sleep(2.0)
    else:
        print(
            "⏭️  [Cache Bypass] Findings and SOTA research already generated. Skipping Analyst Chain."
        )

    #
    # Stage 5: Generate the Tower Strategic Blueprint payload. This stage is cache-gated.
    #
    print("\n🚀 Iniciando Flujo Top-Down: Blueprint Estratégico...")
    if (
        args.force
        or not blueprint_payload_path.exists()
        or blueprint_payload_path.stat().st_size == 0
    ):
        if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
            print("🔎 Ejecutando preflight de Vertex AI...")
            preflight = run_vertex_ai_preflight(env=env)
            print(
                f"✅ Vertex AI listo (project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
            )

        try:
            await run_step_async(
                [
                    python_bin,
                    "-m",
                    "assessment_engine.application.run_tower_blueprint_engine",
                    args.client,
                    tower_id,
                ],
                env,
                "Engine: Tower Strategic Blueprint",
            )
        except Exception as e:
            print(f"⚠️ Fallo crítico en Blueprint: {e}")
            return
    else:
        print(
            "⏭️  [Cache Bypass] Engine: Tower Strategic Blueprint already generated. Skipping API call."
        )

    #
    # Stage 6: Synthesize the Executive Annex payload. This stage is cache-gated.
    #
    print("\n🚀 Iniciando Síntesis Ejecutiva...")
    if args.force or not payload_path.exists() or payload_path.stat().st_size == 0:
        try:
            await run_step_async(
                [
                    python_bin,
                    "-m",
                    "assessment_engine.application.run_executive_annex_synthesizer",
                    args.client,
                    tower_id,
                ],
                env,
                "Engine: Executive Annex Synthesizer",
            )
        except Exception as e:
            print(f"⚠️ Fallo en síntesis del anexo: {e}")
    else:
        print(
            "⏭️  [Cache Bypass] Engine: Executive Annex Synthesizer already generated. Skipping API call."
        )

    #
    # Stage 7: Render the final DOCX artifacts. This stage is not cached, as the rendering execution time is negligible, making cache overhead non-beneficial.
    #
    async def render_standard_report():
        """Orchestrates the multi-stage rendering of the final report and associated artifacts.

        This asynchronous function executes a sequence of subprocesses to construct the
        final report deliverables. The rendering pipeline consists of the following
        stages:

        1.  **Intermediate Artifact Generation**: Generates Markdown and CSV modules
            from the main blueprint payload.
        2.  **Data Visualization**: Creates a PNG radar chart from quantitative
            summary data.
        3.  **Final Document Compilation**: Compiles the intermediate artifacts into
            the primary Microsoft Word (DOCX) document.
        4.  **Canary Build**: Performs a parallel Abstract Syntax Tree (AST) 'shadow
            compilation' to produce a canary version of the report for validation.

        The function's execution is not cached, as the rendering time is negligible,
        rendering caching overhead counterproductive.

        Raises:
            Exception: If any underlying rendering subprocess encounters an error.
        """
        # Phase 1: Generate intermediate Markdown and CSV artifacts from the `blueprint_payload_path` to enable offline review before final compilation.
        await run_step_async(
            [
                python_bin,
                "-m",
                "adapters.generate_asis_markdown_modules",
                str(blueprint_payload_path),
            ],
            env,
            "Generate AS-IS Markdown Modules",
        )

        # Generate radar chart visualization for quantitative summary.
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.generate_tower_radar_chart",
                str(payload_path),
                str(payload_path.with_name("pillar_radar_chart.generated.png")),
            ],
            env,
            "Generate short radar",
        )

        # Phase 2: Compile the final DOCX report from the intermediate module artifacts.
        await run_step_async(
            [
                python_bin,
                "-m",
                "adapters.compile_asis_docx_from_modules",
                str(case_dir),
                str(case_dir / f"AS-IS_Anexo_Tecnico_{tower_id}.docx"),
            ],
            env,
            "Compile AS-IS DOCX from Modules",
        )

        # Perform an Abstract Syntax Tree (AST) shadow compilation. This generates a canary artifact for non-production analysis of alternative logic paths.
        await run_step_async(
            [
                python_bin,
                "-m",
                "assessment_engine.application.tools.run_shadow_compilation",
                "--blueprint-payload",
                str(blueprint_payload_path),
                "--approved-annex",
                str(payload_path),
                "--output",
                str(case_dir / f"AS-IS_Anexo_Tecnico_{tower_id}.shadow.docx"),
            ],
            env,
            "V4 AST Shadow Compilation (Canary)",
        )

    async def run_blueprint_flow():
        """Asynchronously executes the blueprint DOCX rendering subprocess.

        This coroutine conditionally invokes a subprocess to render the Tower Strategic
        Blueprint DOCX document. The operation is contingent upon the existence of the
        payload file specified by the module-level `blueprint_payload_path` variable.

        The rendering logic is encapsulated within the `adapters.render_tower_blueprint`
        module, which is executed using the interpreter at `python_bin`. The input
        payload path and the `output_blueprint_docx` path are passed as command-line
        arguments. The subprocess executes within the environment defined by `env`.

        Returns:
            None.

        Raises:
            Exception: Propagates an exception from the underlying `run_step_async`
                call if the rendering subprocess fails (e.g., returns a non-zero
                exit code).
        """
        if blueprint_payload_path.exists():
            await run_step_async(
                [
                    python_bin,
                    "-m",
                    "adapters.render_tower_blueprint",
                    str(blueprint_payload_path),
                    str(output_blueprint_docx),
                ],
                env,
                "Render: Tower Strategic Blueprint DOCX",
            )

    print("\n🚀 Finalizando: Renderizado Estándar + Blueprint en paralelo...")
    await asyncio.gather(render_standard_report(), run_blueprint_flow())

    print(f"\n✅ Pipeline {tower_id} completado con éxito.")
    print(f"📄 DOCX Resumen Ejecutivo: {output_docx}")
    print(f"🚀 DOCX Blueprint Estratégico: {output_blueprint_docx}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
