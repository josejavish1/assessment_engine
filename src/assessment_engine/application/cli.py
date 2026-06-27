#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sovereign Assessment Engine CLI Control Panel.

This module unifies all execution pipelines, background daemon management (APEX),
autonomous AI-agent execution, and portability lock-in verification
into a single, unified, and cross-platform Python-native console CLI script.
"""

# golden-path: ignore
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run_pipeline(
    client: str, slug: str, context: str, responses: str, towers_str: str
) -> int:
    """Executes the complete end-to-end assessment pipeline for a client.

    Args:
        client: The formal name of the client holding/subsidiary.
        slug: The lowercase, safe filesystem slug representing the client.
        context: The path to the Word context document.
        responses: The path to the technical responses TXT file.
        towers_str: A space-separated list of tower codes to execute.

    Returns:
        The exit code (0 for success).
    """
    repo_root = Path(__file__).resolve().parents[3]
    working_dir = repo_root / "working" / slug

    print("========================================================")
    print(f" INICIANDO PIPELINE DE ASSESSMENT - CLIENTE: {client}")
    print("========================================================")

    print(f"🧹 Cleaning previous execution directory under: {working_dir}...")
    if working_dir.exists():
        shutil.rmtree(working_dir)
    working_dir.mkdir(parents=True, exist_ok=True)

    # Resolve interpreter
    python_bin = sys.executable

    # Credentials helper fallback
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        fallback_credentials = Path.home() / ".secrets" / "sa-key.json"
        if fallback_credentials.exists():
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(fallback_credentials)
        else:
            print(
                f"⚠️ Warning: No GCP credentials key found at default path {fallback_credentials}."
            )

    # --- Phase 0: Ingestion ---
    ingest_script = (
        repo_root / "src/assessment_engine/application/tools" / f"ingest_{slug}.py"
    )
    if ingest_script.exists():
        print("📥 FASE 0: Running Document Ingestion (Raptor & Evidence Engine)...")
        res = subprocess.run([python_bin, str(ingest_script)], cwd=repo_root)
        if res.returncode != 0:
            print("❌ Phase 0 Ingestion failed. Aborting pipeline.")
            return res.returncode
    else:
        # Check if RAG tree already exists
        rag_cache = repo_root / "working/redeia_v3/redeia/raptor_tree.json"
        if rag_cache.exists() and slug == "redeia":
            print("⏭️ FASE 0: Reutilizando RAG previo.")
        else:
            print(f"⚠️ FASE 0: Skipping ingestion (no specific ingest_{slug}.py found).")

    # --- Phase 1: Client Intelligence ---
    print("🔍 FASE 1: Harvesting Client & Market Strategic Intelligence...")
    intel_script = (
        repo_root / "src/assessment_engine/application/run_intelligence_harvesting.py"
    )
    res = subprocess.run(
        [python_bin, str(intel_script), client, context], cwd=repo_root
    )
    if res.returncode != 0:
        print("❌ Phase 1 Client Intelligence failed. Aborting pipeline.")
        return res.returncode

    # --- Phase 2: Technical Towers ---
    towers = [t.strip() for t in towers_str.split(" ") if t.strip()]
    tower_script = repo_root / "src/assessment_engine/application/run_tower_pipeline.py"
    for tower in towers:
        print(f"\n▶️ PROCESANDO TORRE {tower}")
        print("--------------------------------------------------------")
        res = subprocess.run(
            [
                python_bin,
                str(tower_script),
                "--tower",
                tower,
                "--client",
                client,
                "--context-file",
                context,
                "--responses-file",
                responses,
            ],
            cwd=repo_root,
        )
        if res.returncode != 0:
            print(f"❌ Phase 2 Tower {tower} pipeline failed. Aborting pipeline.")
            return res.returncode

    # --- Phase 3 & 4: Aggregation and Strategic/Commercial Synthesis ---
    print("\n🌐 PROCESANDO AGREGACIÓN GLOBAL Y REPORTES DE ENTREGABLES")
    print("--------------------------------------------------------")
    print("🎛️ FASE 3: Generating Global Consolidated Report...")
    global_script = (
        repo_root / "src/assessment_engine/application/run_global_pipeline.py"
    )
    res = subprocess.run([python_bin, str(global_script), client], cwd=repo_root)
    if res.returncode != 0:
        print("❌ Phase 3 Global aggregation failed. Aborting pipeline.")
        return res.returncode

    print("📊 FASE 4: Executing Internal Commercial Plan Refiner...")
    comm_script = (
        repo_root / "src/assessment_engine/application/run_commercial_pipeline.py"
    )
    res = subprocess.run([python_bin, str(comm_script), client], cwd=repo_root)
    if res.returncode != 0:
        print("❌ Phase 4 Commercial refining failed. Aborting pipeline.")
        return res.returncode

    # --- Phase 5: Web presentation ---
    print("🖥️ FASE 5: Composing Interactive Web Dashboard...")
    web_script = repo_root / "src/assessment_engine/adapters/render_web_presentation.py"
    res = subprocess.run([python_bin, str(web_script), slug], cwd=repo_root)
    if res.returncode != 0:
        print("❌ Phase 5 Web presentation rendering failed.")
        return res.returncode

    print("\n==========================================================")
    print(f"✅ EJECUCIÓN DEL PIPELINE COMPLETADA CON ÉXITO PARA {client}")
    print("==========================================================")
    return 0


def manage_po_batch(daemon: bool, monitor: bool) -> int:
    """Manages the background APEX Sentinel daemon or runs the connected monitor.

    Args:
        daemon: If True, launches the sentinel in headless background mode.
        monitor: If True, launches the interactive monitoring TUI.

    Returns:
        The exit code (0 for success).
    """
    repo_root = Path(__file__).resolve().parents[3]
    apex_dir = repo_root / "working/apex"
    apex_dir.mkdir(parents=True, exist_ok=True)

    log_file = apex_dir / "session.log"
    pid_file = apex_dir / "apex.pid"
    dispatcher_script = (
        repo_root / "src/assessment_engine/application/tools/apex_dispatcher.py"
    )

    if not dispatcher_script.exists():
        print(f"[-] Dispatcher script not found: {dispatcher_script}", file=sys.stderr)
        return 1

    if daemon:
        print("Lanzando Apex Sentinel en segundo plano...")
        print(f"Logs disponibles en: {log_file}")

        # Open log file to redirect stdout/stderr
        try:
            with open(log_file, "a", encoding="utf-8") as log:
                process = subprocess.Popen(
                    [sys.executable, str(dispatcher_script), "--headless"],
                    stdout=log,
                    stderr=log,
                    close_fds=True,
                    start_new_session=True,
                )
            pid_file.write_text(str(process.pid), encoding="utf-8")
            print(f"[+] Proceso lanzado con PID {process.pid}.")
            print(
                "Puedes desconectarte tranquilamente. Para monitorizar, usa: assessment-engine po-batch --monitor"
            )
            return 0
        except Exception as e:
            print(f"[-] Failed to launch daemon: {e}", file=sys.stderr)
            return 1

    if monitor or (not daemon and not monitor):
        print("[+] Connecting interactive monitor TUI to ledger...")
        res = subprocess.run([sys.executable, str(dispatcher_script)], cwd=repo_root)
        return res.returncode

    return 0


def run_lockin_test() -> int:
    """Executes the zero-lockin portability validation test.

    This copies the codebase to an isolated temporary sandbox, removes all
    adapter abstractions, forces the fake LLM provider, and runs the entire
    test suite.
    """
    print(
        "[Audit] Initializing Portability Sandbox Verification (Tear-down Validation)..."
    )
    repo_root = Path(__file__).resolve().parents[3]

    with tempfile.TemporaryDirectory() as chaos_dir:
        chaos_path = Path(chaos_dir)
        print(f"[+] Isolated sandbox created at: {chaos_path}")

        # Copy repository recursively excluding caches and environments
        shutil_ignore = shutil.ignore_patterns(
            ".git",
            ".venv",
            "working",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".artifacts",
        )

        # Copy tree
        for item in repo_root.iterdir():
            if item.name in (
                ".git",
                ".venv",
                "working",
                ".artifacts",
                ".pytest_cache",
                ".mypy_cache",
                ".ruff_cache",
            ):
                continue
            if item.is_dir():
                shutil.copytree(
                    item, chaos_path / item.name, symlinks=True, ignore=shutil_ignore
                )
            else:
                shutil.copy2(item, chaos_path / item.name)

        # Extirpate the adapter layers physically to simulate total vendor removal
        adapters_dir = chaos_path / "src/assessment_engine/adapters"
        if adapters_dir.exists():
            print(
                f"[Audit] Simulating provider removal by deleting adapter layers at: {adapters_dir}"
            )
            shutil.rmtree(adapters_dir)

        # Force the isolated environment variables
        custom_env = os.environ.copy()
        custom_env["SOVEREIGN_LLM_PROVIDER"] = "fake"

        # Run pytest inside the sandboxed path
        print("[+] Running unit tests inside the sandbox...")
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/"],
            cwd=chaos_path,
            env=custom_env,
        )

        if res.returncode == 0:
            print("✅ Zero Vendor Lock-in guaranteed. Codebase is vendor-agnostic!")
            return 0
        else:
            print("❌ Vendor Lock-in detected! Core layers depend on missing adapters.")
            return 1


def run_rage_command(client: str, industry: str) -> int:
    """Executes the dynamic RAGE (Runtime Agentic Grounding & Evaluation) pipeline.

    Loads the dynamic frameworks, runs the grounding search agent with Google search,
    secures and downloads local PDF snapshots to the vault, cross-examines evidence,
    and performs pure Python rubric evaluation.
    """
    import asyncio

    from assessment_engine.infrastructure.agentic_benchmarker import (
        AgenticRageBenchmarker,
    )
    from assessment_engine.infrastructure.text_utils import slugify

    print("========================================================")
    print(f" INICIANDO PIPELINE DE RAGE - CLIENTE: {client} | INDUSTRIA: {industry}")
    print("========================================================")

    repo_root = Path(__file__).resolve().parents[3]
    slug = slugify(client)
    working_dir = repo_root / "working" / slug
    working_dir.mkdir(parents=True, exist_ok=True)

    benchmarker = AgenticRageBenchmarker(client_id=slug, working_dir=working_dir)

    try:
        # Run asynchronous RAGE engine inside synchronous CLI flow
        snapshot = asyncio.run(benchmarker.run_rage_evaluation(industry))
        print("\n========================================================")
        print("✓ RAGE EXECUTION COMPLETED SUCCESSFULLY!")
        print("--------------------------------------------------------")
        print(f"Total Towers Evaluated: {len(snapshot.snapshots)}")
        for t_id, t_snap in sorted(snapshot.snapshots.items()):
            print(
                f"- Tower {t_id} ({t_snap.framework_name}): Score {t_snap.dynamic_score:,.1f} ({t_snap.verification_status.upper()})"
            )
        print("========================================================")
        return 0
    except Exception as e:
        print(f"[-] RAGE Execution failed: {e}", file=sys.stderr)
        return 1


def main() -> None:
    """Main CLI entrypoint parser."""
    parser = argparse.ArgumentParser(
        description="Sovereign Assessment Engine Unified CLI Control Panel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="subcommand", required=True, help="Subcommands"
    )

    # Pipeline Run
    run_parser = subparsers.add_parser(
        "run", help="Run the full end-to-end assessment pipeline."
    )
    run_parser.add_argument(
        "--client", required=True, help="Formal client name (e.g. 'REDEIA')"
    )
    run_parser.add_argument(
        "--slug", required=True, help="Lowercase client filesystem slug (e.g. 'redeia')"
    )
    run_parser.add_argument("--context", required=True, help="Path to context document")
    run_parser.add_argument(
        "--responses", required=True, help="Path to responses TXT file"
    )
    run_parser.add_argument(
        "--towers",
        required=True,
        help="Space-separated list of tower codes (e.g. 'T2 T5')",
    )

    # APEX Daemon Manager
    batch_parser = subparsers.add_parser(
        "po-batch", help="Manage the background APEX Sentinel daemon."
    )
    batch_group = batch_parser.add_mutually_exclusive_group()
    batch_group.add_argument(
        "--daemon", action="store_true", help="Launch Sentinel in headless daemon mode."
    )
    batch_group.add_argument(
        "--monitor", action="store_true", help="Connect TUI monitor to the ledger."
    )

    # RAGE Evaluation Command
    rage_parser = subparsers.add_parser(
        "rage",
        help="Execute the dynamic RAGE (Runtime Agentic Grounding & Evaluation) benchmarks evaluation.",
    )
    rage_parser.add_argument(
        "--client", required=True, help="Formal client name (e.g. 'REDEIA')"
    )
    rage_parser.add_argument(
        "--industry",
        required=True,
        help="Canonical industry profile key (e.g. 'critical_infrastructure')",
    )

    # Zero Lockin Portability Test
    subparsers.add_parser(
        "prove-lockin", help="Execute the zero vendor lock-in portability test."
    )

    args = parser.parse_args()

    if args.subcommand == "run":
        sys.exit(
            run_pipeline(
                args.client, args.slug, args.context, args.responses, args.towers
            )
        )
    elif args.subcommand == "po-batch":
        sys.exit(manage_po_batch(args.daemon, args.monitor))
    elif args.subcommand == "rage":
        sys.exit(run_rage_command(args.client, args.industry))
    elif args.subcommand == "prove-lockin":
        sys.exit(run_lockin_test())


if __name__ == "__main__":
    main()
