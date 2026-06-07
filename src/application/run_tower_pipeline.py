"""
Módulo run_tower_pipeline.py.
Contiene la lógica y utilidades principales para el pipeline de Assessment Engine.
Implementa un orquestador asíncrono basado en un DAG (Directed Acyclic Graph)
utilizando Subprocesos Asíncronos aislados para evitar Race Conditions de memoria global.
"""

import argparse
import asyncio
import os
import unicodedata
from pathlib import Path

from infrastructure.pipeline_runtime import (
    build_runtime_env,
    prepare_case_runtime,
    resolve_ai_step_timeout_seconds,
    resolve_python_bin,
    validate_runtime_environment,
)
from infrastructure.runtime_env import (
    run_vertex_ai_preflight,
)
from infrastructure.runtime_paths import (
    resolve_blueprint_payload_path,
    resolve_tower_annex_template_path,
)

SKIP_MODE = False
START_FROM = None


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in ascii_value)
    return "_".join(part for part in cleaned.lower().split("_") if part) or "client"


async def run_step_async(
    cmd_args: list[str], env: dict[str, str], step_name: str
) -> None:
    """
    Ejecuta un paso de forma asíncrona mediante subprocesos.
    Garantiza aislamiento de estado (sys.argv, os.environ) para ejecución paralela segura.
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    parser.add_argument("--start-from", required=False, help="Step name to start from")
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

    # --- COGNITIVE RESET ---
    print(f"🔄 [Cognitive Reset] Purgando razonamiento previo para {tower_id}...")
    if case_dir.exists():
        for f in ["findings.json", "evidence_ledger.json", "blueprint_t2_payload.json"]:
            path_to_del = case_dir / f
            if path_to_del.exists():
                path_to_del.unlink()

    import time

    env["AI_EXECUTION_SEED"] = str(time.time())

    validate_runtime_environment(env)

    context_path = str(Path(args.context_file).resolve())
    responses_path = str(Path(args.responses_file).resolve())

    annex_stem = f"approved_annex_{tower_id.lower()}"
    payload_path = case_dir / f"{annex_stem}.template_payload.json"
    template_annex_path = resolve_tower_annex_template_path()
    output_docx = case_dir / f"annex_{tower_id.lower()}_{client_slug}_final.docx"

    await run_step_async(
        [
            python_bin,
            "-m",
            "application.build_case_input",
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
            "application.build_evidence_ledger",
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
            "application.run_scoring",
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
            "application.run_evidence_analyst",
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

    # --- ETAPA DE REFINADO EJECUTIVO (Tier 1 Standards) ---
    # --- ETAPA DE INVESTIGACIÓN SOTA (State of the Art 2026) ---
    await run_step_async(
        [
            python_bin,
            "-m",
            "application.run_sota_researcher",
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
            "application.run_executive_refiner",
            "--findings-path",
            str(case_dir / "findings.json"),
            "--client",
            args.client,
        ],
        env,
        "Run executive refiner",
    )

    print("\n🚀 Iniciando Flujo Top-Down: Blueprint Estratégico...")
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        print("🔎 Ejecutando preflight de Vertex AI...")
        preflight = run_vertex_ai_preflight(env=env)
        print(
            f"✅ Vertex AI listo (project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
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
                "application.run_tower_blueprint_engine",
                args.client,
                tower_id,
            ],
            env,
            "Engine: Tower Strategic Blueprint",
        )
    except Exception as e:
        print(f"⚠️ Fallo crítico en Blueprint: {e}")
        return

    print("\n🚀 Iniciando Síntesis Ejecutiva...")
    try:
        await run_step_async(
            [
                python_bin,
                "-m",
                "application.run_executive_annex_synthesizer",
                args.client,
                tower_id,
            ],
            env,
            "Engine: Executive Annex Synthesizer",
        )
    except Exception as e:
        print(f"⚠️ Fallo en síntesis del anexo: {e}")

    async def render_standard_report():
        await run_step_async(
            [
                python_bin,
                "-m",
                "application.generate_tower_radar_chart",
                str(payload_path),
                str(payload_path.with_name("pillar_radar_chart.generated.png")),
            ],
            env,
            "Generate short radar",
        )
        await run_step_async(
            [
                python_bin,
                "-m",
                "adapters.render_tower_annex_from_template",
                str(payload_path),
                str(template_annex_path),
                str(output_docx),
                "--semantic-styles",
            ],
            env,
            "Render short DOCX",
        )

    async def run_blueprint_flow():
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
