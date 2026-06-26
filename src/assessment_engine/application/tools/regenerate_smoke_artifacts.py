"""Orchestrates the reproducible regeneration of smoke test artifacts within the `working/` directory."""

from __future__ import annotations

import argparse
import logging
import shlex
import subprocess

from assessment_engine.application.tools.generate_smoke_data import (
    DEFAULT_SCENARIO,
    SCENARIOS,
    generate_smoke_inputs,
    normalize_towers,
)
from assessment_engine.infrastructure.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
)
from assessment_engine.infrastructure.runtime_env import (
    run_vertex_ai_preflight,
)
from assessment_engine.infrastructure.runtime_paths import ROOT

logger = logging.getLogger(__name__)

BLUEPRINT_RESUME_STEP = "Engine: Tower Strategic Blueprint"


def run_step(
    cmd_args: list[str],
    step_name: str,
    env: dict[str, str],
    dry_run: bool,
) -> None:
    """Executes a shell command as a discrete step in a larger process.

    Logs a descriptive step name and the shell-quoted command for inspection.
    If `dry_run` is True, the command is not executed. Otherwise, the command
    is run as a subprocess from the project's root directory with the specified
    environment variables.

    Args:
        cmd_args: A sequence of strings representing the command and its
            arguments.
        step_name: A human-readable name for the step, used for logging.
        env: A dictionary of environment variables to set for the child process.
        dry_run: If True, logs the command without execution.

    Raises:
        SystemExit: If the subprocess returns a non-zero exit code, indicating
            failure.
    """
    printable = " ".join(shlex.quote(arg) for arg in cmd_args)
    logger.info(f"\n=== {step_name} ===")
    logger.info(printable)
    if dry_run:
        return

    completed = subprocess.run(
        cmd_args,
        cwd=ROOT,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def build_local_steps(
    python_bin: str,
    client_id: str,
    tower_id: str,
    context_path: str,
    responses_path: str,
) -> list[tuple[list[str], str]]:
    r"""{'docstring': "Construct a sequence of local command-line steps for a smoke test.\n\nAssembles a multi-step command pipeline to generate various test artifacts,\nsuch as case inputs and evidence ledgers, for a given client and tower. The\ncommands are designed for sequential execution, as the output of one step\nserves as the input for a subsequent step.\n\nArgs:\n    python_bin: The path to the Python executable for running modules.\n    client_id: The identifier for the client under test.\n    tower_id: The identifier for the specific tower configuration.\n    context_path: The file path to the context input data.\n    responses_path: The file path to the responses input data.\n\nReturns:\n    A list of command steps to be executed. Each item is a tuple\n    containing a command (as a list of strings for a subprocess) and a\n    human-readable description of the command's purpose."}."""
    tower_dir = ROOT / "working" / client_id / tower_id
    case_input_path = tower_dir / "case_input.json"
    evidence_ledger_path = tower_dir / "evidence_ledger.json"
    scoring_output_path = tower_dir / "scoring_output.json"
    label_suffix = f" ({tower_id})"

    return [
        (
            [
                python_bin,
                "-m",
                "assessment_engine.application.build_case_input",
                "--client",
                client_id,
                "--tower",
                tower_id,
                "--context-file",
                context_path,
                "--responses-file",
                responses_path,
            ],
            f"Build case_input{label_suffix}",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.application.build_evidence_ledger",
                "--case-input",
                str(case_input_path),
                "--context-file",
                context_path,
                "--responses-file",
                responses_path,
            ],
            f"Build evidence_ledger{label_suffix}",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_scoring",
                "--case-input",
                str(case_input_path),
            ],
            f"Run scoring{label_suffix}",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_evidence_analyst",
                "--case-input",
                str(case_input_path),
                "--evidence-ledger",
                str(evidence_ledger_path),
                "--scoring-output",
                str(scoring_output_path),
            ],
            f"Run evidence analyst{label_suffix}",
        ),
    ]


def main(argv: list[str] | None = None) -> None:
    """Orchestrates the end-to-end regeneration of smoke test artifacts.

    This function serves as the main entry point for a command-line utility
    that regenerates all artifacts for a smoke test client. It parses command-
    line arguments to configure and execute a multi-stage pipeline.

    The process begins by generating synthetic user inputs (context and responses).
    It then proceeds with a series of local-only pipeline steps. If not
    restricted to local execution, it continues with AI-backed steps that
    require Vertex AI access, optionally performing a preflight check to
    validate credentials and model availability. The pipeline can conclude by
    running optional global, commercial, and web-rendering stages.

    Execution can be customized via flags for partial regeneration (e.g.,
    `--local-only`) or for a dry run, which prints the commands that would be
    executed without running them.

    Args:
        argv: A list of command-line arguments to parse. If None, defaults to
            `sys.argv[1:]`.

    Raises:
        subprocess.CalledProcessError: If any of the orchestrated pipeline steps
            fail by returning a non-zero exit code and the `--dry-run` flag
            is not set.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="smoke_ivirma")
    parser.add_argument("--tower", default="T5")
    parser.add_argument("--towers", nargs="+", default=None)
    parser.add_argument(
        "--scenario", choices=sorted(SCENARIOS), default=DEFAULT_SCENARIO
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--with-global", action="store_true")
    parser.add_argument("--with-commercial", action="store_true")
    parser.add_argument("--with-web", action="store_true")
    parser.add_argument("--skip-vertex-preflight", action="store_true")
    parser.add_argument("--vertex-model", default=None)
    parser.add_argument("--writer-model", default=None)
    parser.add_argument("--vertex-preflight-timeout-seconds", type=float, default=None)
    parser.add_argument("--vertex-query-timeout-seconds", type=float, default=None)
    parser.add_argument("--ai-step-timeout-seconds", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    client_id = args.client.strip() or "smoke_ivirma"
    tower_ids = normalize_towers(args.towers or [args.tower])
    python_bin = resolve_python_bin()

    env = build_runtime_env()
    if args.skip_vertex_preflight:
        env["ASSESSMENT_SKIP_VERTEX_PREFLIGHT"] = "1"
    if args.writer_model:
        env["ASSESSMENT_MODEL_OVERRIDE_WRITER_FAST"] = args.writer_model
    if args.vertex_query_timeout_seconds is not None:
        env["ASSESSMENT_VERTEX_QUERY_TIMEOUT_SECONDS"] = str(
            args.vertex_query_timeout_seconds
        )
    if args.ai_step_timeout_seconds is not None:
        env["ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"] = str(args.ai_step_timeout_seconds)

    context_path, responses_path = generate_smoke_inputs(
        client=client_id,
        towers=tower_ids,
        seed=args.seed,
        scenario=args.scenario,
        write_files=not args.dry_run,
    )
    logger.info("\n=== Smoke inputs ===")
    logger.info(str(context_path))
    logger.info(str(responses_path))
    logger.info(f"Towers: {', '.join(tower_ids)}")

    for tower_id in tower_ids:
        for cmd_args, step_name in build_local_steps(
            python_bin,
            client_id,
            tower_id,
            str(context_path),
            str(responses_path),
        ):
            run_step(cmd_args, step_name, env, args.dry_run)

    if args.local_only:
        logger.info("\n✅ Regeneración local completada hasta findings.json.")
        return

    if args.skip_vertex_preflight:
        logger.info("\n=== Vertex AI preflight ===")
        logger.info("Skipped by flag: --skip-vertex-preflight")
    elif args.dry_run:
        logger.info("\n=== Vertex AI preflight ===")
        logger.info("Would run Vertex AI preflight before the first AI-backed step.")
    else:
        logger.info("\n=== Vertex AI preflight ===")
        result = run_vertex_ai_preflight(
            env=env,
            model_name=args.vertex_model,
            timeout_seconds=args.vertex_preflight_timeout_seconds,
        )
        logger.info("✅ Vertex AI preflight passed.")
        logger.info(f"   - project: {result['project']}")
        logger.info(f"   - location: {result['location']}")
        logger.info(f"   - model: {result['model']}")
        if args.writer_model:
            logger.info(f"   - writer_model_override: {args.writer_model}")

    for tower_id in tower_ids:
        tower_pipeline_cmd = [
            python_bin,
            "-m",
            "assessment_engine.application.run_tower_pipeline",
            "--tower",
            tower_id,
            "--client",
            client_id,
            "--context-file",
            str(context_path),
            "--responses-file",
            str(responses_path),
            "--start-from",
            BLUEPRINT_RESUME_STEP,
        ]
        run_step(
            tower_pipeline_cmd,
            f"Resume tower pipeline from strategic blueprint ({tower_id})",
            env,
            args.dry_run,
        )

    if args.with_global:
        run_step(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_global_pipeline",
                client_id,
            ],
            "Run global pipeline",
            env,
            args.dry_run,
        )

    if args.with_commercial:
        run_step(
            [
                python_bin,
                "-m",
                "assessment_engine.application.run_commercial_pipeline",
                client_id,
            ],
            "Run commercial pipeline",
            env,
            args.dry_run,
        )

    if args.with_web:
        run_step(
            [
                python_bin,
                "-m",
                "adapters.render_web_presentation",
                client_id,
            ],
            "Render web dashboard",
            env,
            args.dry_run,
        )

    logger.info("\n✅ Regeneración smoke finalizada.")


if __name__ == "__main__":
    main()
