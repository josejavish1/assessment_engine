"""
Módulo regenerate_smoke_artifacts.py.
Orquesta la regeneración reproducible de artefactos smoke en working/.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys

from assessment_engine.scripts.lib.runtime_env import (
    ensure_google_cloud_env_defaults,
    run_vertex_ai_preflight,
)
from assessment_engine.scripts.lib.runtime_paths import ROOT
from assessment_engine.scripts.tools.generate_smoke_data import generate_smoke_inputs


BLUEPRINT_RESUME_STEP = "Engine: Tower Strategic Blueprint"


def resolve_python_bin() -> str:
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def run_step(
    cmd_args: list[str],
    step_name: str,
    env: dict[str, str],
    dry_run: bool,
) -> None:
    printable = " ".join(shlex.quote(arg) for arg in cmd_args)
    print(f"\n=== {step_name} ===")
    print(printable)
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


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="smoke_ivirma")
    parser.add_argument("--tower", default="T5")
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
    tower_id = args.tower.upper().strip()
    python_bin = resolve_python_bin()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    ensure_google_cloud_env_defaults(env)
    if args.writer_model:
        env["ASSESSMENT_MODEL_OVERRIDE_WRITER_FAST"] = args.writer_model
    if args.vertex_query_timeout_seconds is not None:
        env["ASSESSMENT_VERTEX_QUERY_TIMEOUT_SECONDS"] = str(
            args.vertex_query_timeout_seconds
        )
    if args.ai_step_timeout_seconds is not None:
        env["ASSESSMENT_AI_STEP_TIMEOUT_SECONDS"] = str(
            args.ai_step_timeout_seconds
        )

    context_path, responses_path = generate_smoke_inputs(
        client=client_id,
        towers=[tower_id],
        seed=args.seed,
        write_files=not args.dry_run,
    )
    print("\n=== Smoke inputs ===")
    print(str(context_path))
    print(str(responses_path))

    client_dir = ROOT / "working" / client_id
    tower_dir = client_dir / tower_id
    case_input_path = tower_dir / "case_input.json"
    evidence_ledger_path = tower_dir / "evidence_ledger.json"
    scoring_output_path = tower_dir / "scoring_output.json"

    local_steps = [
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
                str(context_path),
                "--responses-file",
                str(responses_path),
            ],
            "Build case_input",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.build_evidence_ledger",
                "--case-input",
                str(case_input_path),
                "--context-file",
                str(context_path),
                "--responses-file",
                str(responses_path),
            ],
            "Build evidence_ledger",
        ),
        (
            [
                python_bin,
                "-m",
                "assessment_engine.scripts.run_scoring",
                "--case-input",
                str(case_input_path),
            ],
            "Run scoring",
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
            "Run evidence analyst",
        ),
    ]

    for cmd_args, step_name in local_steps:
        run_step(cmd_args, step_name, env, args.dry_run)

    if args.local_only:
        print("\n✅ Regeneración local completada hasta findings.json.")
        return

    if args.skip_vertex_preflight:
        print("\n=== Vertex AI preflight ===")
        print("Skipped by flag: --skip-vertex-preflight")
    elif args.dry_run:
        print("\n=== Vertex AI preflight ===")
        print("Would run Vertex AI preflight before the first AI-backed step.")
    else:
        print("\n=== Vertex AI preflight ===")
        result = run_vertex_ai_preflight(
            env=env,
            model_name=args.vertex_model,
            timeout_seconds=args.vertex_preflight_timeout_seconds,
        )
        print("✅ Vertex AI preflight passed.")
        print(f"   - project: {result['project']}")
        print(f"   - location: {result['location']}")
        print(f"   - model: {result['model']}")
        if args.writer_model:
            print(f"   - writer_model_override: {args.writer_model}")

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
        "Resume tower pipeline from strategic blueprint",
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

    print("\n✅ Regeneración smoke finalizada.")


if __name__ == "__main__":
    main()
