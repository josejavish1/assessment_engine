"""
Servidor MCP (Model Context Protocol) para el Assessment Engine.

Este módulo expone las herramientas core de renderizado y análisis
para que puedan ser consumidas por un Supervisor Agent (LangGraph/CrewAI)
o clientes MCP compatibles (Cursor, Claude Desktop, etc).
"""
import json
import os
import subprocess
import sys
from json import JSONDecodeError
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from assessment_engine.schemas.annex_synthesis import AnnexPayload
from assessment_engine.schemas.blueprint import BlueprintPayload

# Inicializar FastMCP
mcp = FastMCP("Assessment Engine Core")

# Rutas base
ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable


def _read_json_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _summarize_validation_error(error: ValidationError) -> list[str]:
    summary: list[str] = []
    for item in error.errors():
        location = " -> ".join(str(part) for part in item["loc"])
        summary.append(f"{location}: {item['msg']}")
    return summary


def _inspect_payload_artifact(path: Path, schema, artifact_name: str) -> dict:
    artifact_state = {
        "path": str(path),
        "status": "missing",
    }
    if not path.exists():
        return artifact_state

    artifact_state["status"] = "present"
    try:
        data = _read_json_file(path)
    except (JSONDecodeError, OSError) as error:
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
    if any(status == "invalid" for status in payload_statuses):
        return "invalid"
    if any(status in {"valid", "present"} for status in payload_statuses):
        return "partial"
    return "missing"


def _inspect_canonical_state(case_dir: Path) -> dict:
    blueprint_candidates = sorted(case_dir.glob("blueprint_*_payload.json"))
    annex_candidates = sorted(case_dir.glob("approved_annex_*.template_payload.json"))

    blueprint_path = blueprint_candidates[0] if blueprint_candidates else case_dir / "blueprint_payload.json"
    annex_path = annex_candidates[0] if annex_candidates else case_dir / "approved_annex.template_payload.json"

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
            "blueprint_docx": _inspect_docx_artifact("Blueprint_Transformacion_*.docx", case_dir),
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
        except (JSONDecodeError, OSError) as error:
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
        raise RuntimeError(f"Error ejecutando {module_name}:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
    return result.stdout.strip()

@mcp.tool()
def build_tower_payload(approved_annex_json: str, output_json: str, client_name: str, profile: str = "short") -> str:
    """
    Construye el payload intermedio para renderizar el Anexo de Torre.
    Convierte el JSON crudo aprobado en un payload estructurado para docx.
    """
    out = _run_script(
        "assessment_engine.scripts.build_tower_annex_template_payload", 
        [approved_annex_json, output_json, client_name, profile]
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
        [payload_json, template_docx, output_docx]
    )
    return f"✅ Documento de Torre renderizado con éxito.\n{out}"

@mcp.tool()
def generate_radar_chart(global_payload_json: str) -> str:
    """
    Genera el gráfico de radar global en formato PNG a partir del payload global.
    """
    out = _run_script(
        "assessment_engine.scripts.generate_global_radar_chart", 
        [global_payload_json]
    )
    return f"✅ Gráfico generado con éxito.\n{out}"

@mcp.tool()
def render_commercial_docx(commercial_payload_json: str, template_docx: str, output_docx: str) -> str:
    """
    Renderiza el documento final DOCX del Account Action Plan Comercial.
    """
    out = _run_script(
        "assessment_engine.scripts.render_commercial_report", 
        [commercial_payload_json, template_docx, output_docx]
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

if __name__ == "__main__":
    # FastMCP maneja automáticamente el transporte (stdio, SSE) y el ciclo de vida.
    mcp.run()
