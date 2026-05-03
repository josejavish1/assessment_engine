import asyncio
import json
import logging
import subprocess
import re
import time
import sys
from pathlib import Path
from typing import Any, Optional

from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.apex_models import ApexDebateResponse
from assessment_engine.scripts.lib.apex_sentinel import ApexSentinel

# Configuración
console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APEX-Dispatcher")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
BACKLOG_PATH = REPO_ROOT / "docs/audits/IMPROVEMENT_BACKLOG.md"
WORKING_DIR = REPO_ROOT / "working/apex"
SENTINEL = ApexSentinel(WORKING_DIR, budget_limit=25.0)

UI_STATE = {
    "all_tasks": [],
    "active_task": None,
    "active_logs": [],
    "debate_transcript": [],
    "total_cost": 0.0,
    "start_time": time.time(),
    "completed_count": 0
}

def load_apex_prompt(filename: str) -> dict:
    import yaml
    filepath = Path(__file__).resolve().parent.parent.parent / "prompts" / "registry" / filename
    with filepath.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="active_mission", size=7),
        Layout(name="brain_stream", ratio=1),
        Layout(name="terminal_mirror", size=8),
        Layout(name="registry", size=12),
        Layout(name="footer", size=3),
    )
    return layout

def generate_header() -> Panel:
    elapsed = time.time() - UI_STATE["start_time"]
    m, s = divmod(int(elapsed), 60)
    h, m = divmod(m, 60)
    timer = f"{h:02d}:{m:02d}:{s:02d}"
    
    total = len(UI_STATE["all_tasks"])
    done = UI_STATE["completed_count"]
    pct = (done / total * 100) if total > 0 else 0
    
    content = Text.assemble(
        (" APEX SENTINEL ", "bold white on blue"),
        f" | BURN: ${UI_STATE['total_cost']:.3f} | ",
        (f"PROGRESS: {pct:.1f}% ({done}/{total}) ", "bold yellow"),
        f"| UPTIME: {timer}"
    )
    return Panel(content, style="blue")

def generate_forge_mission() -> Panel:
    if not UI_STATE["active_task"]:
        return Panel("Esperando tareas...", title="MISSION")
    t = UI_STATE["active_task"]
    return Panel(
        f"[bold cyan]ID:[/] {t['id']}  [bold cyan]PRIO:[/] {t['priority']}  [bold cyan]STATUS:[/] {t['status']}\n[bold white]MISIÓN:[/] {t['title']}",
        title="[bold red]CURRENT MISSION[/]", border_style="red"
    )

def generate_brain_stream() -> Panel:
    text = Text()
    for role, msg in UI_STATE["debate_transcript"][-8:]:
        color = "yellow" if "DOCTOR" in role else "magenta"
        if "SENTINEL" in role: color = "blue"
        text.append(f"[{role}]: ", style=f"bold {color}")
        text.append(f"{msg}\n", style="italic")
    return Panel(text, title="[bold]BRAIN STREAM (AI Reasoning)[/]", border_style="yellow")

def generate_terminal_mirror() -> Panel:
    logs = "\n".join(UI_STATE["active_logs"][-6:])
    return Panel(logs, title="[bold]TERMINAL MIRROR[/]", border_style="dim")

def generate_registry() -> Panel:
    table = Table(expand=True, box=None, show_header=True)
    table.add_column("ID", style="dim", width=8)
    table.add_column("Status", width=15)
    table.add_column("Task Title", ratio=1)
    
    # Mostrar ventana inteligente del backlog
    current_idx = 0
    for i, t in enumerate(UI_STATE["all_tasks"]):
        if UI_STATE["active_task"] and t["id"] == UI_STATE["active_task"]["id"]:
            current_idx = i
            break
    
    start = max(0, current_idx - 2)
    end = start + 8
    visible = UI_STATE["all_tasks"][start:end]
    
    for t in visible:
        s = t["status"]
        color = "white"
        if "Success" in s: color = "green"
        elif "Running" in s: color = "yellow"
        elif "HARD_BLOCK" in s: color = "red"
        table.add_row(t["id"], f"[{color}]{s}[/]", t["title"])
        
    return Panel(table, title=f"[bold]REGISTRY (Total: {len(UI_STATE['all_tasks'])})[/]", border_style="blue")

async def run_po_orchestrator(task_prompt: str) -> tuple[bool, str]:
    # Sanitizar el prompt de saltos de línea para la CLI
    clean_prompt = task_prompt.replace("\n", " ").replace('"', '\\"')
    
    # Extraer flags especiales del prompt si el Tribunal las incluyó
    flags = []
    if "--allow-dirty" in task_prompt:
        flags.append("--allow-dirty")
        clean_prompt = clean_prompt.replace("--allow-dirty", "").strip()

    cmd = [str(REPO_ROOT / "bin/po-run")] + flags + [clean_prompt]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=REPO_ROOT
    )
    
    full_log = []
    while True:
        line = await process.stdout.readline()
        if not line: break
        decoded = line.decode().strip()
        if decoded:
            UI_STATE["active_logs"].append(decoded)
            full_log.append(decoded)
    
    _, stderr = await process.communicate()
    if stderr:
        UI_STATE["active_logs"].append(stderr.decode())
        full_log.append(stderr.decode())
        
    return process.returncode == 0, "\n".join(full_log)

async def perform_apex_debate(error_logs: str, previous_failures: str) -> ApexDebateResponse:
    UI_STATE["debate_transcript"].append(("SENTINEL", "Activando Tribunal Supremo..."))
    
    doctor_config = load_apex_prompt("apex_doctor.yaml")
    architect_config = load_apex_prompt("apex_architect.yaml")
    invariants = (REPO_ROOT / "GEMINI.md").read_text()

    doctor_prompt = doctor_config["prompt_details"]["template"].format(
        error_logs=error_logs[:1500], 
        previous_failures=previous_failures
    )
    
    architect_prompt = architect_config["prompt_details"]["template"].format(
        repository_invariants=invariants,
        proposed_strategy=doctor_prompt
    )

    data = await call_agent(
        model_name="gemini-2.5-pro",
        prompt=architect_prompt,
        output_schema=ApexDebateResponse,
        instruction="Eres el Tribunal APEX con Autonomía Total. Resuelve el bloqueo."
    )
    
    response = ApexDebateResponse(**data)
    UI_STATE["debate_transcript"].append(("ARCHITECT", f"Veredicto: {response.decision}"))
    SENTINEL.log_transaction(UI_STATE["active_task"]["id"] if UI_STATE["active_task"] else "N/A", "debate_completed", {
        "decision": response.decision,
        "reasoning": response.reasoning,
        "injected_tasks": [t.get("title") for t in response.prerequisite_tasks]
    }, cost=0.15)
    return response


def parse_backlog() -> list[dict[str, str]]:
    if not BACKLOG_PATH.exists(): return []
    content = BACKLOG_PATH.read_text()
    pattern = r"\|\s*(\*?\*?P[123]\*?\*?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    matches = re.findall(pattern, content)
    tasks = []
    for match in matches:
        priority, area, title, desc = [m.strip().replace("*", "") for m in match]
        if "Área" in area or "Prioridad" in priority: continue
        tasks.append({
            "id": f"T{len(tasks)+1}", "priority": priority, "title": title,
            "description": desc, "status": "Pending"
        })
    return tasks

async def main():
    headless = "--headless" in sys.argv
    layout = make_layout()
    UI_STATE["all_tasks"] = parse_backlog()
    
    for t in UI_STATE["all_tasks"]:
        prev = SENTINEL.get_task_status(t["id"])
        if prev in ["success", "hard_block"]:
            t["status"] = f"Done ({prev})"
            UI_STATE["completed_count"] += 1

    with Live(layout, refresh_per_second=4, screen=not headless):
        i = 0
        while i < len(UI_STATE["all_tasks"]):
            task = UI_STATE["all_tasks"][i]
            if "Done" in task["status"]: i += 1; continue
            
            UI_STATE["active_task"] = task
            task["status"] = "Running"
            UI_STATE["active_logs"] = [] # Clear logs for new task
            
            success, logs = await run_po_orchestrator(task.get("instruction") or f"Implementa: {task['title']}")

            if success:
                task["status"] = "Success"
                SENTINEL.log_transaction(task["id"], "success", {}, cost=0.05)
                UI_STATE["completed_count"] += 1
                i += 1
            else:
                SENTINEL.log_transaction(task["id"], "attempt_failed", {"error_snippet": logs[-500:]})
                task["status"] = "Rescuing"

                debate = await perform_apex_debate(logs, "Fallo inicial.")
                
                if debate.decision == "INJECT_PREREQUISITE":
                    # Lógica de recursividad corregida: inyectar DELANTE de la tarea actual
                    new_tasks = []
                    for p_task in debate.prerequisite_tasks:
                        nt = {**p_task, "priority": "EMG", "id": f"EMG-{int(time.time()) % 1000}", "status": "Pending"}
                        new_tasks.append(nt)
                    
                    # Insertar y NO incrementar i para que procese las nuevas
                    for nt in reversed(new_tasks):
                        UI_STATE["all_tasks"].insert(i, nt)
                    
                    task["status"] = "Waiting EMG"
                    # No incrementamos i, así que el bucle procesará la primera EMG inyectada
                elif debate.decision == "REJECTED" or debate.is_terminal_failure:
                    task["status"] = "HARD_BLOCK"
                    SENTINEL.log_transaction(task["id"], "hard_block", {"reason": debate.reasoning})
                    i += 1
                else:
                    # APPROVED: Reintento con instrucción revisada
                    task["instruction"] = debate.revised_instruction
                    # No incrementamos i para reintentar la misma tarea con la nueva instrucción
            
            UI_STATE["total_cost"] = SENTINEL.total_cost
            if not headless:
                layout["header"].update(generate_header())
                layout["active_mission"].update(generate_forge_mission())
                layout["brain_stream"].update(generate_brain_stream())
                layout["terminal_mirror"].update(generate_terminal_mirror())
                layout["registry"].update(generate_registry())
                layout["footer"].update(Panel(f"Control: Ctrl+C para suspender | Ledger: working/apex/apex_ledger.jsonl", style="dim"))

if __name__ == "__main__":
    asyncio.run(main())
