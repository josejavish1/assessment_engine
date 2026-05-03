import time
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.console import Console

console = Console()

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="backlog", ratio=1),
        Layout(name="details", ratio=2),
    )
    return layout

def generate_table(tasks):
    table = Table(title="Backlog Status")
    table.add_column("Task ID")
    table.add_column("Status")
    table.add_column("Progress")
    for task_id, status, prog in tasks:
        table.add_row(task_id, status, f"{prog}%")
    return table

def main():
    layout = make_layout()
    tasks = [
        ["T1", "Success", 100],
        ["T2", "Running", 45],
        ["T3", "Pending", 0],
    ]
    
    with Live(layout, refresh_per_second=4, screen=True):
        layout["header"].update(Panel("APEX COMMAND CENTER | Cost: $1.24", style="bold blue"))
        layout["backlog"].update(generate_table(tasks))
        layout["details"].update(Panel("CURRENT PHASE: [bold yellow]DEBATE[/]\nREASONING: Architect is auditing Doctor's rescue plan to ensure Zero-Workaround compliance.", title="Phase Details"))
        layout["footer"].update(Panel("Press Ctrl+C to abort batch process safely.", style="dim"))
        
        for i in range(45, 101, 5):
            tasks[1][2] = i
            layout["backlog"].update(generate_table(tasks))
            time.sleep(0.5)

if __name__ == "__main__":
    main()
