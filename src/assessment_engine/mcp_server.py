"""
Servidor MCP (Model Context Protocol) para el Assessment Engine.

Este módulo expone las herramientas core de renderizado y análisis
para que puedan ser consumidas por un Supervisor Agent (LangGraph/CrewAI)
o clientes MCP compatibles (Cursor, Claude Desktop, etc).
"""
import os
import sys
import json
import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Inicializar FastMCP
mcp = FastMCP("Assessment Engine Core")

# Rutas base
ROOT = Path(__file__).resolve().parents[2]
PYTHON_BIN = sys.executable

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
    de los artefactos de la torre (asis, risks, gap, tobe, todo, conclusion).
    Útil para que un agente supervisor evalúe el progreso del assessment.
    """
    path = Path(case_dir)
    if not path.exists() or not path.is_dir():
        return f"Error: Directorio {case_dir} no encontrado."
    
    state = {}
    for section in ["asis", "risks", "gap", "tobe", "todo", "conclusion"]:
        file = path / f"approved_{section}.generated.json"
        if file.exists():
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                state[section] = {
                    "status": data.get("status", "unknown"), 
                    "metadata": data.get("_approval_metadata", {})
                }
            except Exception as e:
                state[section] = {"status": "error", "message": str(e)}
        else:
            state[section] = {"status": "missing"}
    
    return json.dumps(state, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # FastMCP maneja automáticamente el transporte (stdio, SSE) y el ciclo de vida.
    mcp.run()
