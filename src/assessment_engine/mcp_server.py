"""
Servidor MCP (Model Context Protocol) para el Assessment Engine.

Este módulo expone las herramientas core de renderizado y análisis
para que puedan ser consumidas por un Supervisor Agent (LangGraph/CrewAI)
o clientes MCP compatibles (Cursor, Claude Desktop, etc).
"""

import asyncio
import json
import os
import subprocess
import sys
import uuid
from json import JSONDecodeError
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.schemas.blueprint import BlueprintPayload

# Inicializar FastMCP
mcp = FastMCP("Assessment Engine Core")

# Rutas base
ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable
LOAD_ERRORS = (JSONDecodeError, OSError, UnicodeDecodeError)


def _read_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _summarize_validation_error(error: ValidationError) -> list[str]:
    summary: list[str] = []
    for item in error.errors():
        location = " -> ".join(str(part) for part in item["loc"])
        summary.append(f"{location}: {item['msg']}")
    return summary


def _inspect_payload_artifact(path: Path, schema, artifact_name: str) -> dict:
    artifact_state: dict[str, Any] = {
        "path": str(path),
        "status": "missing",
    }
    if not path.exists():
        return artifact_state

    artifact_state["status"] = "present"
    try:
        data = _read_json_file(path)
    except LOAD_ERRORS as error:
        artifact_state["status"] = "error"
        artifact_state["message"] = f"{artifact_name} could not be loaded: {error}"
        return artifact_state

    try:
        payload = schema.model_validate(data)
    except ValidationError as error:
        artifact_state["status"] = "invalid"
        artifact_state["validation_errors"] = _summarize_validation_error(error)
        return artifact_state

    artifact_state["status"] = "valid"
    artifact_state["generation_metadata"] = data.get("_generation_metadata")
    if artifact_name == "Blueprint":
        artifact_state["tower_code"] = payload.document_meta.tower_code
        artifact_state["tower_name"] = payload.document_meta.tower_name
    else:
        artifact_state["tower_code"] = payload.document_meta.get("tower_code")
        artifact_state["tower_name"] = payload.document_meta.get("tower_name")
    return artifact_state


def _inspect_docx_artifact(pattern: str, case_dir: Path) -> dict:
    matches = sorted(case_dir.glob(pattern))
    if not matches:
        return {"status": "missing"}
    return {
        "status": "present",
        "path": str(matches[0]),
    }


def _canonical_overall_status(canonical_state: dict) -> str:
    payload_statuses = (
        canonical_state["blueprint_payload"]["status"],
        canonical_state["annex_payload"]["status"],
    )
    if all(status == "valid" for status in payload_statuses):
        return "complete"
    if any(status in {"invalid", "error"} for status in payload_statuses):
        return "invalid"
    if any(status in {"valid", "present"} for status in payload_statuses):
        return "partial"
    return "missing"


def _inspect_canonical_state(case_dir: Path) -> dict:
    blueprint_candidates = sorted(case_dir.glob("blueprint_*_payload.json"))
    annex_candidates = sorted(case_dir.glob("approved_annex_*.template_payload.json"))

    blueprint_path = (
        blueprint_candidates[0]
        if blueprint_candidates
        else case_dir / "blueprint_payload.json"
    )
    annex_path = (
        annex_candidates[0]
        if annex_candidates
        else case_dir / "approved_annex.template_payload.json"
    )

    canonical_state = {
        "mode": "blueprint-first",
        "blueprint_payload": _inspect_payload_artifact(
            blueprint_path,
            BlueprintPayload,
            "Blueprint",
        ),
        "annex_payload": _inspect_payload_artifact(
            annex_path,
            AnnexPayload,
            "Annex",
        ),
        "deliverables": {
            "blueprint_docx": _inspect_docx_artifact(
                "Blueprint_Transformacion_*.docx", case_dir
            ),
            "annex_docx": _inspect_docx_artifact("annex_*_final.docx", case_dir),
        },
    }
    canonical_state["overall_status"] = _canonical_overall_status(canonical_state)
    return canonical_state


def _inspect_legacy_state(case_dir: Path) -> dict:
    legacy_state = {}
    for section in ["asis", "risks", "gap", "tobe", "todo", "conclusion"]:
        file = case_dir / f"approved_{section}.generated.json"
        if not file.exists():
            legacy_state[section] = {"status": "missing"}
            continue

        try:
            data = _read_json_file(file)
        except LOAD_ERRORS as error:
            legacy_state[section] = {
                "status": "error",
                "message": str(error),
            }
            continue

        legacy_state[section] = {
            "status": data.get("status", "unknown"),
            "metadata": data.get("_approval_metadata", {}),
            "path": str(file),
        }
    return legacy_state


def _run_script(module_name: str, args: list[str]) -> str:
    """Ejecuta un script del motor de forma aislada y segura."""
    cmd = [PYTHON_BIN, "-m", module_name] + args
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"Error ejecutando {module_name}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        )
    # Combine stdout and stderr since logs often go to stderr
    combined_output = f"{result.stdout}\n{result.stderr}".strip()
    return combined_output


@mcp.tool()
def build_tower_payload(
    approved_annex_json: str, output_json: str, client_name: str, profile: str = "short"
) -> str:
    """
    Construye un payload intermedio legacy para renderizar el Anexo de Torre.
    Convierte un annex refined heredado en un payload estructurado para DOCX.
    """
    out = _run_script(
        "assessment_engine.scripts._legacy.build_tower_annex_template_payload",
        [approved_annex_json, output_json, client_name, profile],
    )
    return f"✅ Payload construido con éxito.\n{out}"


@mcp.tool()
def render_tower_docx(payload_json: str, template_docx: str, output_docx: str) -> str:
    """
    Renderiza el documento final DOCX del Anexo de Torre usando una plantilla corporativa.
    Requiere el payload_json generado previamente por build_tower_payload.
    """
    out = _run_script(
        "assessment_engine.scripts.render_tower_annex_from_template",
        [payload_json, template_docx, output_docx],
    )
    return f"✅ Documento de Torre renderizado con éxito.\n{out}"


@mcp.tool()
def generate_radar_chart(global_payload_json: str) -> str:
    """
    Genera el gráfico de radar global en formato PNG a partir del payload global.
    """
    out = _run_script(
        "assessment_engine.scripts.generate_global_radar_chart", [global_payload_json]
    )
    return f"✅ Gráfico generado con éxito.\n{out}"


@mcp.tool()
def render_commercial_docx(
    commercial_payload_json: str, template_docx: str, output_docx: str
) -> str:
    """
    Renderiza el documento final DOCX del Account Action Plan Comercial.
    """
    out = _run_script(
        "assessment_engine.scripts.render_commercial_report",
        [commercial_payload_json, template_docx, output_docx],
    )
    return f"✅ Reporte comercial renderizado.\n{out}"


@mcp.tool()
def get_tower_state(case_dir: str) -> str:
    """
    Inspecciona un directorio de caso y devuelve un resumen JSON del estado
    de los artefactos de la torre. Prioriza el flujo canónico blueprint->annex
    y mantiene el detalle legacy por compatibilidad y diagnóstico.
    """
    path = Path(case_dir)
    if not path.exists() or not path.is_dir():
        return f"Error: Directorio {case_dir} no encontrado."

    state = {
        "canonical": _inspect_canonical_state(path),
        "legacy": _inspect_legacy_state(path),
    }
    state.update(state["legacy"])
    return json.dumps(state, indent=2, ensure_ascii=False)


# Memoria en RAM para la cola de trabajos (Job Queue)
job_status: dict[str, str] = {}
job_results: dict[str, str] = {}


async def _background_run_plan(job_id: str, request_text: str):
    loop = asyncio.get_event_loop()

    def run_sync():
        return _run_script(
            "assessment_engine.scripts.tools.run_product_owner_orchestrator",
            ["plan", "--request", request_text],
        )

    try:
        out = await loop.run_in_executor(None, run_sync)
        found_plan = False
        for line in out.splitlines():
            try:
                log_data = json.loads(line)
                msg = log_data.get("message", "")
                if "Plan generado en " in msg:
                    request_dir = msg.split("Plan generado en ")[1].strip()
                    plan_path = Path(request_dir) / "plan.json"
                    if plan_path.exists():
                        plan_data = plan_path.read_text(encoding="utf-8")
                        job_results[job_id] = (
                            f"✅ Plan generado con éxito.\nREQUEST_DIR={request_dir}\n{plan_data}"
                        )
                        found_plan = True
                        break
            except Exception:
                continue
        if not found_plan:
            job_results[job_id] = (
                f"❌ Error: Plan generated but path not found in logs.\nLogs: {out}"
            )
        job_status[job_id] = "completed"
    except Exception as e:
        job_status[job_id] = "error"
        job_results[job_id] = f"❌ Error ejecutando orquestador: {e}"


@mcp.tool()
async def start_plan_generation(request_text: str) -> str:
    """
    Inicia la generación de un plan de forma asíncrona.
    Devuelve un job_id inmediatamente para no bloquear al cliente HTTP.
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"

    # Lanzar la tarea en segundo plano sin bloquear (Fire and forget)
    asyncio.create_task(_background_run_plan(job_id, request_text))

    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_plan_status(job_id: str) -> str:
    """
    Comprueba el estado de un plan en generación.
    """
    status = job_status.get(job_id, "not_found")
    if status == "completed" or status == "error":
        result = job_results.get(job_id, "")
        return json.dumps({"status": status, "result": result})
    return json.dumps({"status": status})


@mcp.tool()
async def start_plan_execution(request_dir: str, alt_index: int = 0) -> str:
    """
    Inicia la ejecución (Fase 2) de un plan previamente generado y aprobado.
    Devuelve un job_id inmediatamente.
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = "running"
    job_results[job_id] = ""

    async def _background_run_execution():
        import asyncio.subprocess

        cmd = [
            PYTHON_BIN,
            "-m",
            "assessment_engine.scripts.tools.run_product_owner_orchestrator",
            "execute",
            "--request-dir",
            request_dir,
            "--alt-index",
            str(alt_index),
            "--allow-dirty",
            "--executor-command",
            ".github/scripts/orchestrator-gemini-executor.sh {repo_root} {task_prompt_file} {attempt}",
        ]

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                job_results[job_id] += line.decode("utf-8")

            await process.wait()

            if process.returncode != 0:
                job_status[job_id] = "error"
                job_results[job_id] += (
                    f"\n❌ El proceso terminó con código de error {process.returncode}"
                )
            else:
                job_status[job_id] = "completed"
                job_results[job_id] += "\n✅ Ejecución completada."

        except Exception as e:
            job_status[job_id] = "error"
            job_results[job_id] += f"\n❌ Error en ejecución: {e}"

    asyncio.create_task(_background_run_execution())
    return json.dumps({"job_id": job_id, "status": "started"})


@mcp.tool()
def check_execution_status(job_id: str) -> str:
    """
    Comprueba el estado de una ejecución en proceso, devolviendo el log parcial si está corriendo.
    """
    status = job_status.get(job_id, "not_found")
    result = job_results.get(job_id, "")
    return json.dumps({"status": status, "result": result})


@mcp.tool()
def check_action_gate(request_dir: str) -> str:
    """
    Comprueba si existe un bloqueo de Gobernanza Inmunitaria (Action Gate).
    """
    import os

    summary_path = os.path.join(request_dir, "reconciliation_summary.json")
    if os.path.exists(summary_path):
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps({"action_gate_active": True, "data": data})
        except Exception as e:
            return json.dumps({"action_gate_active": False, "error": str(e)})
    return json.dumps({"action_gate_active": False})


@mcp.tool()
def authorize_action_gate(request_dir: str, alt_index: int = 0) -> str:
    """
    Autoriza un Action Gate actualizando el plan y eliminando el bloqueo.
    """
    import os

    summary_path = os.path.join(request_dir, "reconciliation_summary.json")
    plan_path = os.path.join(request_dir, "plan.json")

    if not os.path.exists(summary_path):
        return json.dumps({"success": False, "message": "No hay Action Gate activo."})

    try:
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        if os.path.exists(plan_path):
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)

            active_plan = plan
            if "tasks" not in plan and "alternatives" in plan:
                active_plan = plan["alternatives"][alt_index]

            blast_radius = summary.get("diagnosis", {}).get("blast_radius", [])
            if "in_scope" not in active_plan:
                active_plan["in_scope"] = []
            for file in blast_radius:
                if file not in active_plan["in_scope"]:
                    active_plan["in_scope"].append(file)

            invariant_breach = summary.get("diagnosis", {}).get(
                "required_invariant_breach"
            )
            if invariant_breach and "invariants" in active_plan:
                active_plan["invariants"] = [
                    inv for inv in active_plan["invariants"] if inv != invariant_breach
                ]
                active_plan["invariants"].append(
                    f"EXCEPTION AUTHORIZED BY HUMAN: Se permite romper el invariante previo respecto a: {invariant_breach}"
                )

            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            # Guardar el feedback para el Worker
            feedback_path = os.path.join(request_dir, "authorized_feedback.json")
            with open(feedback_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "task_id": summary.get("task_id"),
                        "feedback": f"SÍNTOMA ANTERIOR:\n{summary.get('raw_error')}\n\nCURA AUTORIZADA POR EL PRODUCT OWNER:\n{summary.get('diagnosis', {}).get('proposed_cure')}",
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

        os.remove(summary_path)
        return json.dumps({"success": True, "message": "Action Gate autorizado."})
    except Exception as e:
        return json.dumps({"success": False, "message": f"Error autorizando: {e}"})


@mcp.tool()
def abort_and_revert() -> str:
    """
    El 'Botón Rojo' de emergencia. Aborta la ejecución actual (mata los procesos si se puede)
    y ejecuta un `git reset --hard` para devolver el repositorio al estado original.
    """
    try:
        # En un sistema en producción más avanzado mataríamos el proceso Popen por PID
        subprocess.run(
            ["git", "reset", "--hard"], cwd=str(ROOT), check=True, capture_output=True
        )
        subprocess.run(
            ["git", "clean", "-fd"], cwd=str(ROOT), check=True, capture_output=True
        )
        return json.dumps(
            {
                "success": True,
                "message": "✅ Abortado y código revertido a su estado original (git reset --hard).",
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "message": f"❌ Error al revertir: {e}"})


if __name__ == "__main__":
    import argparse
    import logging

    from assessment_engine.lib.logger_config import setup_structured_logging

    setup_structured_logging(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run()
