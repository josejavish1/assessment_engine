"""Provides the core orchestration logic for the Assessment Engine pipeline.

The module defines a Directed Acyclic Graph (DAG) of stages, where each stage is executed
in an isolated subprocess to prevent state interference and resource contention between steps.
"""
from __future__ import annotations


import argparse
import asyncio
import logging
import os
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

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

        # Launch the native, deadlock-free communicate method in an asynchronous task
        communicate_task = asyncio.create_task(proc.communicate())

        while not communicate_task.done():
            # Calculate remaining timeout if any
            current_timeout = 30.0
            if timeout_sec is not None:
                elapsed = time.time() - start_time
                remaining = timeout_sec - elapsed
                if remaining <= 0:
                    proc.kill()
                    communicate_task.cancel()
                    raise asyncio.TimeoutError()
                current_timeout = min(30.0, remaining)

            try:
                # Wait for completion or for the heartbeat timeout (30 seconds)
                await asyncio.wait_for(
                    asyncio.shield(communicate_task), timeout=current_timeout
                )
            except asyncio.TimeoutError:
                # If global timeout has been exceeded during the wait, kill and fail
                if timeout_sec is not None and (time.time() - start_time) > timeout_sec:
                    proc.kill()
                    communicate_task.cancel()
                    raise asyncio.TimeoutError()

                # Print progress heartbeat and keep waiting
                print(
                    "⏳ [Heartbeat] El motor sigue trabajando en segundo plano...",
                    flush=True,
                )

        stdout, stderr = await communicate_task
        return stdout, stderr

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
                out_msg = stdout.decode("utf-8").strip() if stdout else ""
                err_msg = stderr.decode("utf-8").strip() if stderr else ""
                if out_msg:
                    print(f"\n📢 [STDOUT antes del Timeout en {step_name}]:\n{out_msg}")
                if err_msg:
                    print(f"\n📢 [STDERR antes del Timeout en {step_name}]:\n{err_msg}")
                raise RuntimeError(
                    f"Timeout en {step_name} tras {timeout_seconds:.0f}s."
                ) from exc
        else:
            stdout, stderr = await _communicate_with_heartbeat(process)

        if stdout:
            print(stdout.decode("utf-8").strip())

        if process.returncode != 0:
            out_msg = stdout.decode("utf-8").strip() if stdout else ""
            err_msg = stderr.decode("utf-8").strip() if stderr else ""
            if out_msg and not stdout:
                print(f"\n📢 [STDOUT antes del Error en {step_name}]:\n{out_msg}")
            raise RuntimeError(
                f"Fallo nativo en {step_name} (Exit {process.returncode}):\n{err_msg}"
            )

        print(f"✅ {step_name} (Completado)")

    except Exception as e:
        raise RuntimeError(f"Critical error executing {step_name}: {e}")


from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Holds parsed pipeline configuration, runtime environment, and resolved file paths."""

    args: argparse.Namespace
    tower_id: str
    client_slug: str
    python_bin: str
    env: dict[str, str]
    case_dir: Path
    context_path: str
    responses_path: str
    payload_path: Path
    output_docx: Path
    output_asis_docx: Path
    blueprint_payload_path: Path
    output_blueprint_docx: Path
    force: bool


def _parse_and_prepare_pipeline(argv: list[str] | None = None) -> PipelineConfig:
    """Parse CLI arguments and initialize runtime environment and output paths."""
    global SKIP_MODE, START_FROM
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    parser.add_argument("--start-from", required=False, help="Step name to start from")
    parser.add_argument(
        "--force", action="store_true", help="Force rebuild everything and purge cache"
    )
    args = parser.parse_args(argv)

    if args.start_from:
        SKIP_MODE = True
        START_FROM = args.start_from

    tower_id = args.tower.upper().strip()
    client_slug = slugify(args.client)
    python_bin = resolve_python_bin()

    env = build_runtime_env()
    env["ASSESSMENT_CLIENT_ID"] = client_slug
    case_dir = prepare_case_runtime(env, client_id=client_slug, tower_id=tower_id)

    if args.force:
        print(f"🔄 [Cognitive Reset] Purgando razonamiento previo para {tower_id}...")
        if case_dir.exists():
            for f in [
                "findings.json",
                "evidence_ledger.json",
                f"blueprint_{tower_id.lower()}_payload.json",
                "blueprint_t2_payload.json",
                "case_input.json",
                "scoring_output.json",
                "benchmarks_snapshot.json",
                "custom_risk_profile.json",
                "loss_exceedance_curve.png",
                f"approved_annex_{tower_id.lower()}.template_payload.json",
            ]:
                path_to_del = case_dir / f
                if path_to_del.exists():
                    path_to_del.unlink()
    else:
        print(
            f"📈 [Incremental Mode] Preserving existing local cache in {case_dir}. Use --force to rebuild from scratch."
        )

    import time

    env["AI_EXECUTION_SEED"] = str(time.time())
    validate_runtime_environment(env)

    context_path = str(Path(args.context_file).resolve())
    responses_path = str(Path(args.responses_file).resolve())

    from assessment_engine.infrastructure.text_utils import (
        get_canonical_tower_filenames,
    )

    annex_stem = f"approved_annex_{tower_id.lower()}"
    payload_path = case_dir / f"{annex_stem}.template_payload.json"
    resolve_tower_annex_template_path()
    doc_lang = str(
        env.get("ASSESSMENT_DOC_LANG")
        or getattr(args, "language", None)
        or "en"
    ).lower()

    canonical_asis_name, canonical_tobe_name = get_canonical_tower_filenames(
        tower_id, client_name=args.client, locale=doc_lang
    )
    output_docx = case_dir / f"annex_{tower_id.lower()}_{client_slug}_final.docx"
    output_asis_docx = case_dir / canonical_asis_name
    blueprint_payload_path = resolve_blueprint_payload_path(client_slug, tower_id)
    output_blueprint_docx = case_dir / canonical_tobe_name

    return PipelineConfig(
        args=args,
        tower_id=tower_id,
        client_slug=client_slug,
        python_bin=python_bin,
        env=env,
        case_dir=case_dir,
        context_path=context_path,
        responses_path=responses_path,
        payload_path=payload_path,
        output_docx=output_docx,
        output_asis_docx=output_asis_docx,
        blueprint_payload_path=blueprint_payload_path,
        output_blueprint_docx=output_blueprint_docx,
        force=args.force,
    )


async def _stage_case_input_and_short_circuit(cfg: PipelineConfig) -> bool:
    """Construct case_input.json and short-circuit early if tower contains no survey answers."""
    case_input_file = cfg.case_dir / "case_input.json"
    if cfg.force or not case_input_file.exists() or case_input_file.stat().st_size == 0:
        try:
            from assessment_engine.application.build_case_input import (
                main as case_input_main,
            )

            case_input_main(
                [
                    "--client",
                    cfg.args.client,
                    "--tower",
                    cfg.tower_id,
                    "--context-file",
                    str(cfg.context_path),
                    "--responses-file",
                    str(cfg.responses_path),
                ]
            )
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-process case input failed: {e}. Usando fallback subprocess..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.build_case_input",
                    "--client",
                    cfg.args.client,
                    "--tower",
                    cfg.tower_id,
                    "--context-file",
                    cfg.context_path,
                    "--responses-file",
                    cfg.responses_path,
                ],
                cfg.env,
                "Build case_input",
            )
    else:
        print("⏭️  [Cache Bypass] Build case_input already generated. Skipping.")

    if case_input_file.exists():
        try:
            import json

            with open(case_input_file, "r", encoding="utf-8-sig") as f:
                case_input_data = json.load(f)
            answers_count = len(case_input_data.get("answers", []))
            if answers_count == 0:
                print(
                    f"\n⏭️  [Short-Circuit] No answers or scores detected for tower '{cfg.tower_id}' in {cfg.responses_path}.\n"
                    f"   This tower is out of assessment scope and will be skipped cleanly.\n"
                    f"   Exiting pipeline execution cleanly (Exit 0)..."
                )
                return True
        except Exception as e:
            print(f"⚠️ Warning analyzing case_input for scope validation: {e}")

    return False


async def _stage_evidence_and_benchmarks(cfg: PipelineConfig) -> None:
    """Assemble evidence ledger, freeze RAGE benchmarks, and calibrate financial scale."""
    evidence_ledger_file = cfg.case_dir / "evidence_ledger.json"
    if (
        cfg.force
        or not evidence_ledger_file.exists()
        or evidence_ledger_file.stat().st_size == 0
    ):
        await run_step_async(
            [
                cfg.python_bin,
                "-m",
                "assessment_engine.application.build_evidence_ledger",
                "--case-input",
                str(cfg.case_dir / "case_input.json"),
                "--context-file",
                cfg.context_path,
                "--responses-file",
                cfg.responses_path,
            ],
            cfg.env,
            "Build evidence_ledger",
        )
    else:
        print("⏭️  [Cache Bypass] Build evidence_ledger already generated. Skipping.")

    client_dir = Path("working") / cfg.client_slug
    client_intel_path = client_dir / "client_intelligence.json"
    industry_key = "default"
    if client_intel_path.exists():
        try:
            import json

            with open(client_intel_path, "r", encoding="utf-8-sig") as f:
                intel_data = json.load(f)
            profile_sec = intel_data.get("profile", {})
            industry_name = ""
            if isinstance(profile_sec, dict):
                industry_name = profile_sec.get("industry", "")
            if not industry_name:
                industry_name = intel_data.get("industry", "default")

            from assessment_engine.infrastructure.config_loader import (
                map_industry_to_profile,
            )

            industry_key = map_industry_to_profile(industry_name)
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Handled exception: {ex}")

    snapshot_file = cfg.case_dir.parent / "benchmarks_snapshot.json"
    tower_has_benchmark = False
    if snapshot_file.exists() and snapshot_file.stat().st_size > 0:
        try:
            with open(snapshot_file, "r", encoding="utf-8-sig") as sf:
                snap_data = json.load(sf)
            snapshots = snap_data.get("snapshots", {})
            t_snap = snapshots.get(cfg.tower_id, {})
            tower_has_benchmark = (
                isinstance(t_snap, dict)
                and t_snap.get("verification_status") == "verified"
            )
        except (OSError, ValueError, KeyError, AttributeError) as ex:
            logger.debug(f"[Fallback] Handled exception: {ex}")

    if cfg.force or not tower_has_benchmark:
        await run_step_async(
            [
                cfg.python_bin,
                "-m",
                "assessment_engine.application.cli",
                "rage",
                "--client",
                cfg.args.client,
                "--industry",
                industry_key,
                "--tower",
                cfg.tower_id,
            ],
            cfg.env,
            "Run RAGE Evaluation",
        )
    else:
        print(
            f"⏭️  [Cache Bypass] RAGE Benchmark for tower {cfg.tower_id} verified in snapshot. Skipping."
        )

    custom_profile_path = cfg.case_dir / "custom_risk_profile.json"
    if (
        cfg.force
        or not custom_profile_path.exists()
        or custom_profile_path.stat().st_size == 0
    ):
        print(
            "\n🌐 [System] Initializing Dynamic Financial Scale Calibrator (FAIR-MAM)..."
        )
        try:
            from assessment_engine.application.tools.financial_scale_calibrator import (
                FinancialScaleCalibrator,
            )

            calibrator = FinancialScaleCalibrator(env=cfg.env)
            await calibrator.calibrate_client_scale(
                cfg.args.client, cfg.tower_id, industry_key
            )
        except Exception as e:
            print(f"⚠️ [Financial Calibrator] Financial scale calibration failed: {e}")
    else:
        print(
            "⏭️  [Cache Bypass] Engine: Financial Scale Calibrator already generated. Skipping."
        )


async def _stage_scoring_and_qualitative_chain(cfg: PipelineConfig) -> None:
    """Execute quantitative scoring followed by qualitative research and executive refinement chain."""
    scoring_file = cfg.case_dir / "scoring_output.json"
    if cfg.force or not scoring_file.exists() or scoring_file.stat().st_size == 0:
        try:
            import json

            from assessment_engine.application.run_scoring import (
                build_scoring,
                load_json,
            )
            from assessment_engine.infrastructure.config_loader import (
                load_tower_definition,
            )

            case_in = load_json(cfg.case_dir / "case_input.json")
            t_def = load_tower_definition(cfg.tower_id)
            sc_out = build_scoring(case_in, t_def)
            scoring_file.write_text(
                json.dumps(sc_out, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-process scoring failed: {e}. Usando fallback subprocess..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_scoring",
                    "--case-input",
                    str(cfg.case_dir / "case_input.json"),
                ],
                cfg.env,
                "Run scoring",
            )
    else:
        print("⏭️  [Cache Bypass] Run scoring already generated. Skipping.")

    findings_file = cfg.case_dir / "findings.json"
    if cfg.force or not findings_file.exists() or findings_file.stat().st_size == 0:
        try:
            from assessment_engine.application.run_evidence_analyst import (
                main as analyst_main,
            )

            await analyst_main(
                [
                    "--case-input",
                    str(cfg.case_dir / "case_input.json"),
                    "--evidence-ledger",
                    str(cfg.case_dir / "evidence_ledger.json"),
                    "--scoring-output",
                    str(cfg.case_dir / "scoring_output.json"),
                ]
            )
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-process evidence analyst failed: {e}. Usando fallback subprocess..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_evidence_analyst",
                    "--case-input",
                    str(cfg.case_dir / "case_input.json"),
                    "--evidence-ledger",
                    str(cfg.case_dir / "evidence_ledger.json"),
                    "--scoring-output",
                    str(cfg.case_dir / "scoring_output.json"),
                ],
                cfg.env,
                "Run evidence analyst",
            )

        try:
            from assessment_engine.application.run_sota_researcher import (
                main as sota_main,
            )

            await sota_main(
                [
                    "--findings-path",
                    str(cfg.case_dir / "findings.json"),
                    "--client",
                    cfg.args.client,
                ]
            )
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-process SOTA researcher failed: {e}. Usando fallback subprocess..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_sota_researcher",
                    "--findings-path",
                    str(cfg.case_dir / "findings.json"),
                    "--client",
                    cfg.args.client,
                ],
                cfg.env,
                "Run technical researcher",
            )

        try:
            from assessment_engine.application.run_executive_refiner import (
                main as refiner_main,
            )

            await refiner_main(
                [
                    "--findings-path",
                    str(cfg.case_dir / "findings.json"),
                    "--client",
                    cfg.args.client,
                ]
            )
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-process executive refiner failed: {e}. Usando fallback subprocess..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_executive_refiner",
                    "--findings-path",
                    str(cfg.case_dir / "findings.json"),
                    "--client",
                    cfg.args.client,
                ],
                cfg.env,
                "Run executive refiner",
            )

        findings_target = cfg.case_dir / "findings.json"
        import json

        for _ in range(10):
            if findings_target.exists() and findings_target.stat().st_size > 0:
                try:
                    with open(findings_target, "r", encoding="utf-8-sig") as vf:
                        json.load(vf)
                    break
                except (OSError, json.JSONDecodeError, ValueError) as ex:
                    logger.debug(
                        f"[Pipeline] Polling de findings_target en curso: {ex}"
                    )
            await asyncio.sleep(0.5)
    else:
        print(
            "[System] [Cache Bypass] Findings and technical research already generated. Skipping Analyst Chain."
        )


async def _stage_blueprint_and_annex(cfg: PipelineConfig) -> None:
    """Synthesize the Tower Strategic Blueprint payload and Executive Annex payload."""
    print("\n[System] Initializing Top-Down Flow: Strategic Blueprint...")
    if (
        cfg.force
        or not cfg.blueprint_payload_path.exists()
        or cfg.blueprint_payload_path.stat().st_size == 0
    ):
        if cfg.env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
            print("🔎 Ejecutando preflight de Vertex AI...")
            preflight = run_vertex_ai_preflight(env=cfg.env)
            print(
                f"✅ Vertex AI listo (project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
            )

        try:
            from assessment_engine.application.run_tower_blueprint_engine import (
                run_tower_blueprint,
            )

            await run_tower_blueprint(cfg.args.client, cfg.tower_id)
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-memory Blueprint invocation failed: {e}. Using subprocess fallback..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_tower_blueprint_engine",
                    cfg.args.client,
                    cfg.tower_id,
                ],
                cfg.env,
                "Engine: Tower Strategic Blueprint",
            )
    else:
        print(
            "⏭️  [Cache Bypass] Engine: Tower Strategic Blueprint already generated. Skipping API call."
        )

    print("\n🚀 Starting Executive Synthesis...")
    if (
        cfg.force
        or not cfg.payload_path.exists()
        or cfg.payload_path.stat().st_size == 0
    ):
        try:
            from assessment_engine.application.run_executive_annex_synthesizer import (
                synthesize_annex,
            )

            await synthesize_annex(cfg.args.client, cfg.tower_id)
        except Exception as e:
            logger.warning(
                f"[Pipeline] In-memory Annex invocation failed: {e}. Using subprocess fallback..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.run_executive_annex_synthesizer",
                    cfg.args.client,
                    cfg.tower_id,
                ],
                cfg.env,
                "Engine: Executive Annex Synthesizer",
            )
    else:
        print(
            "⏭️  [Cache Bypass] Engine: Executive Annex Synthesizer already generated. Skipping API call."
        )


async def _stage_render_deliverables(cfg: PipelineConfig) -> None:
    """Concurrently compile final AS-IS diagnostic report, radar charts, and Blueprint Word DOCX documents."""

    async def render_standard_report() -> None:
        await run_step_async(
            [
                cfg.python_bin,
                "-m",
                "assessment_engine.adapters.generate_asis_markdown_modules",
                str(cfg.blueprint_payload_path),
            ],
            cfg.env,
            "Generate AS-IS Markdown Modules",
        )

        await run_step_async(
            [
                cfg.python_bin,
                "-m",
                "assessment_engine.application.generate_tower_radar_chart",
                str(cfg.payload_path),
                str(cfg.payload_path.with_name("pillar_radar_chart.generated.png")),
            ],
            cfg.env,
            "Generate short radar",
        )

        try:
            from assessment_engine.adapters.compile_asis_docx_from_modules import (
                compile_docx,
            )

            compile_docx(str(cfg.case_dir), str(cfg.output_asis_docx))
        except Exception as ex:
            logger.warning(
                f"[Pipeline] In-memory compilation of AS-IS failed: {ex}. Using subprocess fallback..."
            )
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.adapters.compile_asis_docx_from_modules",
                    str(cfg.case_dir),
                    str(cfg.output_asis_docx),
                ],
                cfg.env,
                "Compile AS-IS DOCX from Modules",
            )
        import shutil

        shutil.copyfile(
            cfg.output_asis_docx,
            cfg.case_dir / f"AS-IS_Anexo_Tecnico_{cfg.tower_id}.docx",
        )
        shutil.copyfile(
            cfg.output_asis_docx,
            cfg.case_dir / f"Diagnostico_ASIS_{cfg.tower_id}_{cfg.client_slug}.docx",
        )

        if cfg.env.get("ASSESSMENT_ENABLE_SHADOW_COMPILER", "").strip() == "1":
            await run_step_async(
                [
                    cfg.python_bin,
                    "-m",
                    "assessment_engine.application.tools.run_shadow_compilation",
                    "--blueprint-payload",
                    str(cfg.blueprint_payload_path),
                    "--approved-annex",
                    str(cfg.payload_path),
                    "--output",
                    str(cfg.case_dir / f"AS-IS_Anexo_Tecnico_{cfg.tower_id}.shadow.docx"),
                ],
                cfg.env,
                "V4 AST Shadow Compilation (Canary)",
            )
        else:
            print(
                f"⏭️  [Production Mode] AS-IS deliverable certified. Skipping internal shadow AST canary for {cfg.tower_id}."
            )

    async def run_blueprint_flow() -> None:
        if cfg.blueprint_payload_path.exists():
            try:
                import json

                from assessment_engine.adapters.render_tower_blueprint import (
                    render_blueprint,
                )
                from assessment_engine.domain.schemas.blueprint import (
                    BlueprintPayload,
                )

                bp_data = json.loads(
                    cfg.blueprint_payload_path.read_text(encoding="utf-8")
                )
                bp_payload = BlueprintPayload.model_validate(bp_data)
                render_blueprint(
                    payload=bp_payload,
                    output_path=cfg.output_blueprint_docx,
                    client_dir=cfg.case_dir.parent,
                )
            except Exception as ex:
                logger.warning(
                    f"[Pipeline] In-memory rendering of Blueprint failed: {ex}. Using subprocess fallback..."
                )
                await run_step_async(
                    [
                        cfg.python_bin,
                        "-m",
                        "assessment_engine.adapters.render_tower_blueprint",
                        str(cfg.blueprint_payload_path),
                        str(cfg.output_blueprint_docx),
                    ],
                    cfg.env,
                    "Render: Tower Strategic Blueprint DOCX",
                )

        if cfg.output_blueprint_docx.exists():
            import shutil

            shutil.copyfile(
                cfg.output_blueprint_docx,
                cfg.case_dir / f"Blueprint_Transformacion_{cfg.tower_id}_{cfg.client_slug}.docx",
            )

    print("\n🚀 Finalizing: Standard Rendering + Blueprint in parallel...")
    await asyncio.gather(render_standard_report(), run_blueprint_flow())

    print(f"\n✅ Pipeline {cfg.tower_id} completed successfully (Canonical Dual Model):")
    print(f"  📄 Deliverable 1 (AS-IS Diagnostic): {cfg.output_asis_docx}")
    print(f"  🚀 Entregable 2 (Blueprint TO-BE):   {cfg.output_blueprint_docx}")
    print(
        f"  📊 Expediente Actuarial (SR 11-7):   {cfg.case_dir / f'Expediente_Auditoria_Riesgos_{cfg.tower_id}.md'}"
    )


async def run_pipeline(argv: list[str] | None = None) -> None:
    """Orchestrates the end-to-end execution of the assessment pipeline."""
    cfg = _parse_and_prepare_pipeline(argv)
    should_stop = await _stage_case_input_and_short_circuit(cfg)
    if should_stop:
        return

    await _stage_evidence_and_benchmarks(cfg)
    await _stage_scoring_and_qualitative_chain(cfg)
    await _stage_blueprint_and_annex(cfg)
    await _stage_render_deliverables(cfg)


if __name__ == "__main__":
    asyncio.run(run_pipeline())
