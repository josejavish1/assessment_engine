import asyncio
import json
import logging
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
    Tree,
)
from textual.screen import ModalScreen

logging.basicConfig(level=logging.INFO, filename="working/apex/monitor_ui.log")
logger = logging.getLogger("APEX-XRay")

if "APEX_WORKSPACE_DIR" in os.environ:
    REPO_ROOT = Path(os.environ["APEX_WORKSPACE_DIR"]).resolve()
else:
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

WORKING_DIR = REPO_ROOT / "working" / "apex"
BACKLOG_PATH = REPO_ROOT / "docs" / "audits" / "IMPROVEMENT_BACKLOG.md"
LEDGER_PATH = WORKING_DIR / "apex_ledger.jsonl"
PID_PATH = WORKING_DIR / "apex.pid"

def get_latest_request_dir() -> Path | None:
    # Find the most recently created session directory in working/
    working_base = REPO_ROOT / "working"
    if not working_base.exists():
        return None
    session_dirs = [d for d in working_base.iterdir() if d.is_dir() and d.name.startswith("session_")]
    if not session_dirs:
        # Fallback to TOWER_ID based if possible, or just search for authorized_feedback.json
        client_dirs = [d for d in working_base.iterdir() if d.is_dir() and not d.name.startswith("apex")]
        latest = None
        latest_mtime = 0
        for client_dir in client_dirs:
             for tower_dir in client_dir.iterdir():
                 if tower_dir.is_dir():
                     mtime = tower_dir.stat().st_mtime
                     if mtime > latest_mtime:
                         latest_mtime = mtime
                         latest = tower_dir
        return latest
    session_dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return session_dirs[0]

def parse_backlog() -> list[dict[str, str]]:
    if not BACKLOG_PATH.exists(): return []
    content = BACKLOG_PATH.read_text(encoding="utf-8")
    pattern = r"\|\s*(\*?\*?P[123]\*?\*?)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
    matches = re.findall(pattern, content)
    tasks = []
    for match in matches:
        p, area, title, desc = [m.strip().replace("*", "") for m in match]
        if "Área" in area or "Prioridad" in p: continue
        tasks.append({"id": f"T{len(tasks)+1}", "priority": p, "title": title, "description": desc, "status": "Pending"})
    return tasks

class HintModal(ModalScreen):
    """Screen for submitting a hint to the orchestrator."""
    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Enter Feedback/Hint for the Agent (Injected as Prerequisite):"),
            Input(placeholder="Type your hint here..."),
            Horizontal(
                Button("Submit", variant="success", id="submit_hint"),
                Button("Cancel", variant="error", id="cancel_hint"),
            ),
            id="hint_dialog"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_hint":
            input_widget = self.query_one(Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)

class ApexMonitorApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    #main_container {
        layout: horizontal;
        height: 1fr;
    }
    #left_panel {
        width: 35%;
        height: 1fr;
        layout: vertical;
        border_right: solid white;
    }
    #right_panel {
        width: 65%;
        height: 1fr;
        layout: vertical;
    }
    #backlog_table {
        height: 60%;
    }
    #brain_scanner {
        height: 40%;
        border_top: solid white;
    }
    #pipeline_train {
        height: 30%;
    }
    #shadow_tracker {
        height: 70%;
        border_top: solid white;
    }
    #hint_dialog {
        padding: 1 2;
        width: 60;
        height: 15;
        background: $surface;
        border: solid $accent;
        align: center middle;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("k", "kill_orchestrator", "Kill Agent", show=True),
        Binding("h", "hint", "Inject Hint", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.tasks = []
        self.active_task_id = None
        self.last_ledger_pos = 0
        self.active_branch = None
        self.is_orchestrator_alive = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="main_container"):
            with Vertical(id="left_panel"):
                yield Label("📋 MISSION BACKLOG", classes="panel_title")
                yield DataTable(id="backlog_table", cursor_type="row")
                yield Label("🧠 BRAIN SCANNER", classes="panel_title")
                yield RichLog(id="brain_scanner", wrap=True, highlight=True, markup=True)
            with Vertical(id="right_panel"):
                yield Label("🛤️ PIPELINE TRAIN (Plan & Progress)", classes="panel_title")
                yield Tree("Pipeline Execution", id="pipeline_train")
                yield Label("💻 SHADOW TRACKER (Live Code Diff)", classes="panel_title")
                yield RichLog(id="shadow_tracker", wrap=False, highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        self.title = "APEX X-Ray Command Center"
        
        # Init Backlog Table
        table = self.query_one(DataTable)
        table.add_columns("ID", "Status", "Title")
        self.tasks = parse_backlog()
        for i, t in enumerate(self.tasks):
            table.add_row(t["id"], t["status"], t["title"], key=t["id"])
            
        self.update_state_loop()
        self.poll_git_diff()

    @work(exclusive=True, thread=True)
    def update_state_loop(self):
        """Reads ledger and PID in a loop."""
        while True:
            self.call_from_thread(self._check_pid)
            self.call_from_thread(self._read_ledger)
            time.sleep(1)

    @work(exclusive=True, thread=True)
    def poll_git_diff(self):
        """Polls git diff safely."""
        while True:
            if self.active_branch:
                shadow_dir = Path("/tmp") / f"shadow_worktree_{self._slugify(self.active_branch)}"
                if shadow_dir.exists():
                    lock_file = shadow_dir / ".git" / "index.lock"
                    if not lock_file.exists():
                        try:
                            # Use git diff with color to feed RichLog
                            result = subprocess.run(
                                ["git", "diff", "--color=always"],
                                cwd=shadow_dir,
                                capture_output=True,
                                text=True
                            )
                            if result.returncode == 0:
                                self.call_from_thread(self._update_diff, result.stdout)
                        except Exception as e:
                            logger.error(f"Error polling diff: {e}")
            time.sleep(2)

    def _update_diff(self, diff_text: str):
        log = self.query_one("#shadow_tracker", RichLog)
        # Only clear and update if there's actual content to avoid flickering
        if diff_text.strip():
            log.clear()
            log.write(diff_text)

    def _slugify(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', '-', text)
        return text.strip('-')

    def _check_pid(self):
        alive = False
        if PID_PATH.exists():
            try:
                pid = int(PID_PATH.read_text().strip())
                os.kill(pid, 0)
                alive = True
            except (OSError, ValueError):
                pass
        
        self.is_orchestrator_alive = alive
        header = self.query_one(Header)
        if alive:
            self.title = f"APEX X-Ray Command Center | [green]ONLINE (PID: {pid})[/green]"
        else:
            self.title = f"APEX X-Ray Command Center | [bold red]SYSTEM HALTED[/bold red]"

    def _read_ledger(self):
        if not LEDGER_PATH.exists():
            return

        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            f.seek(self.last_ledger_pos)
            lines = f.readlines()
            self.last_ledger_pos = f.tell()

        table = self.query_one(DataTable)
        brain = self.query_one("#brain_scanner", RichLog)
        tree = self.query_one(Tree)

        for line in lines:
            try:
                tx = json.loads(line)
                event = tx.get("event")
                task_id = tx.get("task_id")
                details = tx.get("details", {})
                
                # Update task status
                if task_id and event in ["attempt_0", "success", "attempt_failed", "hard_block"]:
                    new_status = event
                    if event == "attempt_0":
                        new_status = "Running"
                        self.active_task_id = task_id
                        # Check if a plan exists and build tree
                        self._build_pipeline_tree(task_id, tree)
                    elif event == "success":
                        new_status = "Success"
                    elif event == "hard_block":
                        new_status = "HARD_BLOCK"
                    
                    try:
                         # Ensure the row exists before updating
                         table.update_cell(task_id, "Status", new_status)
                    except Exception:
                         pass

                # Scan for tool calls in logs to feed Brain Scanner
                if "tool_results" in str(details) or "Function call" in str(details) or event == "debate_completed":
                    if event == "debate_completed":
                        brain.write(f"[bold magenta][ARCHITECT][/] {details.get('decision')} - {details.get('reasoning')[:100]}...")
                    else:
                        # Attempt to extract some meaning
                        msg = details.get("message", "") or str(details)
                        if "list_source_files" in msg:
                            brain.write("[bold cyan][AGENT][/] Exploring repository files...")
                        elif "read_doc_file" in msg:
                            brain.write("[bold cyan][AGENT][/] Reading architecture documentation...")
                        elif "replace" in msg or "write_file" in msg:
                            brain.write("[bold green][AGENT][/] Applying code changes...")
                        
            except json.JSONDecodeError:
                continue
                
    def _build_pipeline_tree(self, task_id: str, tree: Tree):
        req_dir = get_latest_request_dir()
        if not req_dir: return
        plan_path = req_dir / "plan.json"
        if plan_path.exists():
            try:
                plan = json.loads(plan_path.read_text())
                if "branch_name" in plan:
                    self.active_branch = plan["branch_name"]
                
                tree.clear()
                tree.root.expand()
                tree.root.label = f"Task: {task_id}"
                tree.root.add_leaf("✓ Planning Completed")
                
                tasks_node = tree.root.add("Execution Plan", expand=True)
                for t in plan.get("tasks", []):
                    tasks_node.add_leaf(f"[{t['id']}] {t['title']}")
            except Exception:
                pass

    async def action_kill_orchestrator(self) -> None:
        if PID_PATH.exists():
            try:
                pid = int(PID_PATH.read_text().strip())
                os.kill(pid, 9)
                self.query_one("#brain_scanner", RichLog).write(f"[bold red]System terminated PID {pid}.[/bold red]")
            except Exception as e:
                self.query_one("#brain_scanner", RichLog).write(f"[bold red]Failed to kill: {e}[/bold red]")

    def action_hint(self) -> None:
        self.push_screen(HintModal(), self.handle_hint)
        
    def handle_hint(self, hint_text: str | None) -> None:
        if hint_text:
            req_dir = get_latest_request_dir()
            if req_dir:
                fb_path = req_dir / "authorized_feedback.json"
                try:
                    payload = {"task_id": self.active_task_id or "global", "feedback": hint_text}
                    fb_path.write_text(json.dumps(payload))
                    self.query_one("#brain_scanner", RichLog).write(f"[bold green]Hint injected for {self.active_task_id}![/bold green]")
                except Exception as e:
                    self.query_one("#brain_scanner", RichLog).write(f"[bold red]Failed to inject hint: {e}[/bold red]")

if __name__ == "__main__":
    app = ApexMonitorApp()
    app.run()
