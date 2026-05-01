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
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in ascii_value)
    return "_".join(part for part in cleaned.lower().split("_") if part) or "client"


async def run_step_async(cmd_args: list[str], env: dict[str, str], step_name: str) -> None:
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
    
    # Preparamos el entorno inyectando nuestras variables personalizadas
    process_env = os.environ.copy()
    process_env.update(env)
    timeout_seconds = resolve_ai_step_timeout_seconds(process_env, step_name)

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            env=process_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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
        
        # Volcamos la salida para mantener visibilidad de logs
        if stdout:
            print(stdout.decode('utf-8').strip())
            
        if process.returncode != 0:
            err_msg = stderr.decode('utf-8').strip()
            raise RuntimeError(f"Fallo nativo en {step_name} (Exit {process.returncode}):\n{err_msg}")
            
        print(f"✅ {step_name} (Completado)")

    except Exception as e:
        raise RuntimeError(f"Error crítico lanzando {step_name}: {e}")

async def run_pipeline():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tower", required=True)
    parser.add_argument("--client", required=True)
    parser.add_argument("--context-file", required=True)
    parser.add_argument("--responses-file", required=True)
    parser.add_argument("--start-from", required=False, help="Nombre del step desde el que reanudar")
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

    # --- FASE 1: PREPARACIÓN DETERMINISTA (SECUENCIAL) ---
    await run_step_async(
        [python_bin, "-m", "assessment_engine.scripts.build_case_input", "--client", args.client, "--tower", tower_id, "--context-file", context_path, "--responses-file", responses_path],
        env, "Build case_input"
    )
    
    await run_step_async(
        [python_bin, "-m", "assessment_engine.scripts.build_evidence_ledger", "--case-input", str(case_dir / "case_input.json"), "--context-file", context_path, "--responses-file", responses_path],
        env, "Build evidence_ledger"
    )
    await run_step_async(
        [python_bin, "-m", "assessment_engine.scripts.run_scoring", "--case-input", str(case_dir / "case_input.json")],
        env, "Run scoring"
    )
    await run_step_async(
        [python_bin, "-m", "assessment_engine.scripts.run_evidence_analyst", "--case-input", str(case_dir / "case_input.json"), "--evidence-ledger", str(case_dir / "evidence_ledger.json"), "--scoring-output", str(case_dir / "scoring_output.json")],
        env, "Run evidence analyst"
    )

    # --- NUEVA FASE TOP-DOWN (ESTRANGULADOR: BLUEPRINT -> ANEXO) ---
    print("\n🚀 Iniciando Flujo Top-Down: Blueprint Estratégico (Single Source of Truth)...")
    if env.get("ASSESSMENT_SKIP_VERTEX_PREFLIGHT", "").strip() != "1":
        print("🔎 Ejecutando preflight de Vertex AI...")
        preflight = run_vertex_ai_preflight(env=env)
        print(
            "✅ Vertex AI listo "
            f"(project={preflight['project']}, location={preflight['location']}, model={preflight['model']})"
        )
    blueprint_payload_path = resolve_blueprint_payload_path(client_slug, tower_id)
    output_blueprint_docx = case_dir / f"Blueprint_Transformacion_{tower_id}_{client_slug}.docx"
    
    try:
        await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_tower_blueprint_engine", args.client, tower_id], env, "Engine: Tower Strategic Blueprint")
    except Exception as e:
        print(f"⚠️ Fallo crítico en Blueprint: {e}")
        return

    print("\n🚀 Iniciando Síntesis Ejecutiva (El Nuevo Anexo Top-Down)...")
    try:
        await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_executive_annex_synthesizer", args.client, tower_id], env, "Engine: Executive Annex Synthesizer")
    except Exception as e:
        print(f"⚠️ Fallo en síntesis del anexo: {e}")

    # LEGACY CODE - COMENTADO PARA EVITAR SPLIT BRAIN
    # # --- FASE 2: GENERACIÓN AGÉNTICA (PARALELIZABLE) [RAMA A] ---
    # print("\n🚀 Iniciando Generación Paralela Rama A (AS-IS + RISKS + OSINT)...")
    # await asyncio.gather(
    #     run_step_async([python_bin, "-m", "assessment_engine.scripts.run_section_pipeline", "asis"], env, "Generate AS-IS"),
    #     run_step_async([python_bin, "-m", "assessment_engine.scripts.run_section_pipeline", "risks"], env, "Generate Risks"),
    #     # OSINT no se corre por torre, solo lo dejamos como placeholder si fuera necesario a futuro
    # )
    #
    # # --- FASE 3: ANÁLISIS ESTRATÉGICO (PARALELIZABLE) [RAMA B] ---
    # print("\n🚀 Iniciando Análisis Estratégico Paralelo Rama B (GAP + TO-BE)...")
    # await asyncio.gather(
    #     run_step_async([python_bin, "-m", "assessment_engine.scripts.run_tobe_pipeline"], env, "Generate TO-BE"),
    #     run_step_async([python_bin, "-m", "assessment_engine.scripts.run_gap_pipeline"], env, "Generate GAP")
    # )
    #
    # # --- FASE 4: CIERRE DEL REPORTE (SECUENCIAL) [RAMA C] ---
    # await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_todo_pipeline"], env, "Generate TO-DO")
    # await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_conclusion_pipeline"], env, "Generate Conclusion")
    #
    # # --- FASE 5: ENSAMBLADO Y RENDERIZADO ---
    # await run_step_async([python_bin, "-m", "assessment_engine.scripts.assemble_tower_annex"], env, "Assemble annex")
    # 
    # tower_name_mock = "TOWER_NAME"
    # await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_global_review_pipeline", str(case_dir), tower_id, tower_name_mock], env, "Global review")
    # await run_step_async([python_bin, "-m", "assessment_engine.scripts.run_global_refiner_pipeline", str(case_dir), tower_id, tower_name_mock], env, "Global refiner")

    # Pipeline final de renderizado (Re-acondicionado para usar el nuevo Payload del Sintetizador)
    async def render_standard_report():
        # Ya no ensamblamos ni refinamos. El Synthesizer escupe el payload_path directamente listo para render.
        # await run_step_async([python_bin, "-m", "assessment_engine.scripts.build_tower_annex_template_payload", str(refined_path if refined_path.exists() else assembled_path), str(payload_path), args.client, "short"], env, "Build short template payload")
        # await run_step_async([python_bin, "-m", "assessment_engine.scripts.generate_tower_radar_chart", str(payload_path), str(radar_path)], env, "Generate short radar")
        await run_step_async([python_bin, "-m", "assessment_engine.scripts.render_tower_annex_from_template", str(payload_path), str(template_annex_path), str(output_docx), "--semantic-styles"], env, "Render short DOCX")

    async def run_blueprint_flow():
        try:
            if blueprint_payload_path.exists():
                await run_step_async([python_bin, "-m", "assessment_engine.scripts.render_tower_blueprint", str(blueprint_payload_path), str(output_blueprint_docx)], env, "Render: Tower Strategic Blueprint DOCX")
        except Exception as e:
            print(f"⚠️ Fallo no bloqueante en Blueprint Render: {e}")

    print("\n🚀 Finalizando: Renderizado Estándar + Blueprint en paralelo...")
    await asyncio.gather(
        render_standard_report(),
        run_blueprint_flow()
    )

    print(f"\n✅ Pipeline {tower_id} completado con éxito.")
    print(f"📄 DOCX Resumen Ejecutivo: {output_docx}")
    print(f"🚀 DOCX Blueprint Estratégico (Definitivo): {output_blueprint_docx}")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
