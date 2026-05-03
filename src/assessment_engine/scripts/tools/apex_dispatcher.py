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

from assessment_engine.scripts.lib.ai_client import call_agent
from assessment_engine.scripts.lib.apex_models import ApexDebateResponse
from assessment_engine.scripts.lib.apex_sentinel import ApexSentinel

# Configuración
console = Console()
logging.basicConfig(level=logging.INFO, filename="working/apex/error.log")
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
    "completed_count": 0,
    "last_event": "Inicializando..."
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
        Layout(name="active_mission", size=6),
        Layout(name="brain_stream", ratio=1),
        Layout(name="terminal_mirror", size=8),
        Layout(name="registry", size=10),
        Layout(name="footer", size=3),
    )
    return layout

def update_ui_components(layout: Layout):
    try:
        # Header
        elapsed = time.time() - UI_STATE["start_time"]
        m, s = divmod(int(elapsed), 60); h, m = divmod(m, 60)
        total = len(UI_STATE["all_tasks"]); done = UI_STATE["completed_count"]
        pct = (done / total * 100) if total > 0 else 0
        header_text = Text.assemble(
            (" APEX SENTINEL ", "bold white on blue"),
            f" | BURN: ${UI_STATE['total_cost']:.3f} | ",
            (f"PROGRESS: {pct:.1f}% ({done}/{total}) ", "bold yellow"),
            f"| UPTIME: {h:02d}:{m:02d}:{s:02d}"
        )
        layout["header"].update(Panel(header_text, style="blue"))

        # Mission
        if UI_STATE["active_task"]:
            t = UI_STATE["active_task"]
            status_color = "green" if "Running" in t['status'] else "yellow"
            mission_text = f"[bold cyan]ID:[/] {t['id']}  [bold {status_color}]STATUS:[/] {t['status']}\n[bold white]MISIÓN:[/] {t['title'][:80]}"
            layout["active_mission"].update(Panel(mission_text, title="[bold red]CURRENT MISSION[/]", border_style="red"))
        else:
            layout["active_mission"].update(Panel("Esperando tareas...", title="MISSION"))

        # Brain
        text = Text()
        for role, msg in UI_STATE["debate_transcript"][-6:]:
            color = "yellow" if "DOCTOR" in role else "magenta"
            if "SENTINEL" in role: color = "blue"
            text.append(f"[{role}]: ", style=f"bold {color}")
            text.append(f"{str(msg)[:200]}\n", style="italic")
        layout["brain_stream"].update(Panel(text, title="[bold]BRAIN STREAM[/]", border_style="yellow"))

        # Logs
        logs = "\n".join(UI_STATE["active_logs"][-6:])
        layout["terminal_mirror"].update(Panel(logs, title="[bold]TERMINAL MIRROR[/]", border_style="dim"))

        # Registry
        table = Table(expand=True, box=None, show_header=True)
        table.add_column("ID", width=8); table.add_column("Status", width=15); table.add_column("Task Title", ratio=1)
        start = max(0, UI_STATE["completed_count"] - 1)
        for t in UI_STATE["all_tasks"][start:start+7]:
            color = "green" if "Success" in t["status"] else "white"
            table.add_row(t["id"], f"[{color}]{t['status']}[/]", t["title"][:50])
        layout["registry"].update(Panel(table, title="[bold]BACKLOG[/]", border_style="blue"))
        layout["footer"].update(Panel(f"LOG: {UI_STATE['last_event']}", style="dim"))
    except Exception as e:
        layout["footer"].update(Panel(f"UI Error: {e}", style="red"))

async def run_po_orchestrator(task_prompt: str) -> tuple[bool, str]:
    clean_prompt = task_prompt.replace("\n", " ").replace('"', '\\"')
    cmd = [str(REPO_ROOT / "bin/po-run"), clean_prompt]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=REPO_ROOT)
    full_log = []
    while True:
        line = await process.stdout.readline()
        if not line: break
        decoded = line.decode().strip()
        if decoded: UI_STATE["active_logs"].append(decoded); full_log.append(decoded)
    _, stderr = await process.communicate()
    if stderr: full_log.append(stderr.decode()); UI_STATE["active_logs"].append(stderr.decode())
    return process.returncode == 0, "\n".join(full_log)

async def perform_apex_debate(error_logs: str, previous_failures: str) -> ApexDebateResponse:
    UI_STATE["debate_transcript"].append(("SENTINEL", "Iniciando debate..."))
    doctor_config = load_apex_prompt("apex_doctor.yaml")
    architect_config = load_apex_prompt("apex_architect.yaml")
    doctor_prompt = doctor_config["prompt_details"]["template"].format(error_logs=error_logs[:1500], previous_failures=previous_failures)
    architect_prompt = architect_config["prompt_details"]["template"].format(repository_invariants=(REPO_ROOT / "GEMINI.md").read_text(), proposed_strategy=doctor_prompt)
    data = await call_agent(model_name="gemini-2.5-pro", prompt=architect_prompt, output_schema=ApexDebateResponse, instruction="Resuelve el bloqueo.")
    response = ApexDebateResponse(**data)
    UI_STATE["debate_transcript"].append(("ARCHITECT", response.decision))
    SENTINEL.log_transaction(UI_STATE["active_task"]["id"] if UI_STATE["active_task"] else "N/A", "debate_completed", {"decision": response.decision, "reasoning": response.reasoning}, cost=0.15)
    return response

def parse_backlog() -> list[dict[str, str]]:
    if not BACKLOG_PATH.exists(): return []
    content = BACKLOG_PATH.read_text()
    pattern = r"\|\s*(\*?\*?P[123]\*?\*?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    matches = re.findall(pattern, content)
    tasks = []
    for match in matches:
        p, area, title, desc = [m.strip().replace("*", "") for m in match]
        if "Área" in area or "Prioridad" in p: continue
        tasks.append({"id": f"T{len(tasks)+1}", "priority": p, "title": title, "description": desc, "status": "Pending"})
    return tasks

async def process_task(task: dict, queue: list, idx: int):
    attempts = 0; max_rescue_rounds = 3; previous_failures = []
    UI_STATE["active_task"] = task; task["status"] = "Running"
    while attempts <= max_rescue_rounds:
        SENTINEL.log_transaction(task["id"], f"attempt_{attempts}", task)
        success, logs = await run_po_orchestrator(task.get("instruction") or f"Implementa: {task['title']}")
        if success:
            task["status"] = "Success"; SENTINEL.log_transaction(task["id"], "success", {}, cost=0.05); UI_STATE["completed_count"] += 1
            return True
        SENTINEL.log_transaction(task["id"], "attempt_failed", {"error_snippet": logs[-300:]})
        attempts += 1; task["status"] = "Rescuing"
        debate = await perform_apex_debate(logs, "\n".join(previous_failures))
        previous_failures.append(f"Fallo {attempts}: {debate.reasoning}")
        if debate.decision == "INJECT_PREREQUISITE":
            # Safeguard against infinite rescue loops: limit EMG injections for a single root task.
            if len([t for t in queue if t.get("id", "").startswith("EMG-")]) > 5:
                 UI_STATE["debate_transcript"].append(("SENTINEL", "Max emergency tasks reached. Hard blocking."))
                 task["status"] = "HARD_BLOCK"
                 SENTINEL.log_transaction(task["id"], "hard_block", {"reason": "Infinite rescue loop detected."})
                 UI_STATE["completed_count"] += 1
                 return False

            for p_task in reversed(debate.prerequisite_tasks):
                new_task = {**p_task, "priority": "EMG", "id": f"EMG-{int(time.time()) % 1000}", "status": "Pending"}
                queue.insert(idx, new_task); UI_STATE["all_tasks"].insert(idx, new_task)
            task["status"] = "Waiting EMG"; return False 
        elif debate.decision == "REJECTED" or debate.is_terminal_failure:
            task["status"] = "HARD_BLOCK"; SENTINEL.log_transaction(task["id"], "hard_block", {"reason": debate.reasoning}); UI_STATE["completed_count"] += 1; return False
        task["instruction"] = debate.revised_instruction
    return False

async def monitor_mode(layout: Layout):
    UI_STATE["all_tasks"] = parse_backlog()
    while True:
        if SENTINEL.ledger_path.exists():
            with SENTINEL.ledger_path.open("r") as f:
                UI_STATE["total_cost"] = 0
                for line in f:
                    try:
                        tx = json.loads(line)
                        UI_STATE["total_cost"] += tx.get("cost_usd", 0.0)
                        for t in UI_STATE["all_tasks"]:
                            if t["id"] == tx["task_id"]:
                                if tx["event"] == "success": t["status"] = "Success"
                                elif tx["event"] == "hard_block": t["status"] = "HARD_BLOCK"
                                elif "attempt" in tx["event"]: t["status"] = "Running"; UI_STATE["active_task"] = t
                        if tx["event"] == "debate_completed":
                            UI_STATE["debate_transcript"].append(("ARCHITECT", tx["details"]["decision"]))
                    except: continue
        update_ui_components(layout); await asyncio.sleep(1)

async def main():
    mode = "monitor" if "--monitor" in sys.argv else "worker"
    layout = make_layout()
    if mode == "monitor":
        with Live(layout, refresh_per_second=2, screen=True):
            await monitor_mode(layout)
        return
    UI_STATE["all_tasks"] = parse_backlog()
    with Live(layout, refresh_per_second=2, screen=not "--headless" in sys.argv):
        i = 0
        while i < len(UI_STATE["all_tasks"]):
            task = UI_STATE["all_tasks"][i]
            if SENTINEL.get_task_status(task["id"]) in ["success", "hard_block"]: i += 1; continue
            if not "--headless" in sys.argv: update_ui_components(layout)
            await process_task(task, UI_STATE["all_tasks"], i)
            UI_STATE["total_cost"] = SENTINEL.total_cost
            if not "--headless" in sys.argv: update_ui_components(layout)
            i += 1

if __name__ == "__main__":
    asyncio.run(main())
