"""
Módulo regenerate_smoke_artifacts.py.
Orquesta la regeneración reproducible de artefactos smoke en working/.
"""

from __future__ import annotations

import argparse
import logging
import shlex
import subprocess

from assessment_engine.scripts.lib.pipeline_runtime import (
    build_runtime_env,
    resolve_python_bin,
)
from assessment_engine.scripts.lib.runtime_env import (
    run_vertex_ai_preflight,
)
from assessment_engine.scripts.lib.runtime_paths import ROOT
from assessment_engine.scripts.tools.generate_smoke_data import (
    DEFAULT_SCENARIO,
    SCENARIOS,
    generate_smoke_inputs,
    normalize_towers,
)

logger = logging.getLogger(__name__)

BLUEPRINT_RESUME_STEP = "Engine: Tower Strategic Blueprint"


def run_step(
    cmd_args: list[str],
    step_name: str,
    env: dict[str, str],
    dry_run: bool,
) -> None:
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
                "assessment_engine.scripts.build_case_input",
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
                "assessment_engine.scripts.build_evidence_ledger",
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
                "assessment_engine.scripts.run_scoring",
                "--case-input",
                str(case_input_path),
            ],
            f"Run scoring{label_suffix}",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.run_evidence_analyst",
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
            "assessment_engine.scripts.run_tower_pipeline",
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
                "assessment_engine.scripts.run_global_pipeline",
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
                "assessment_engine.scripts.run_commercial_pipeline",
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
                "assessment_engine.scripts.render_web_presentation",
                client_id,
            ],
            "Render web dashboard",
            env,
            args.dry_run,
        )

    logger.info("\n✅ Regeneración smoke finalizada.")


if __name__ == "__main__":
    main()
