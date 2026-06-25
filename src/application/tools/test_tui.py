import time

#
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


def make_layout() -> Layout:
    r"""{'docstring': "Construct the main layout for the application's Text User Interface (TUI).\n\nThe layout is composed of a primary vertical column containing three panels:\n`header`, `main`, and `footer`. The `main` panel is subsequently subdivided\ninto a horizontal row containing `backlog` and `details` panels.\n\nReturns:\n    An initialized `Layout` object representing the complete TUI structure."}."""
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
    """Generates a `rich.table.Table` populated with task data.

    The table is configured with the title "Backlog Status" and three columns:
    "Task ID", "Status", and "Progress". Progress values from the input data are
    formatted into percentage strings (e.g., a value of 85 becomes "85%").

    Args:
        tasks (Iterable[Tuple[Any, Any, Any]]): An iterable of task records.
            Each record must be an iterable (e.g., a tuple) containing three
            elements in the order: task ID, status, and progress value.

    Returns:
        rich.table.Table: A `Table` object configured and populated with the
            provided task data, ready for rendering.

    Raises:
        ValueError: If any record within the `tasks` iterable cannot be unpacked
            into exactly three values.
    """
    table = Table(title="Backlog Status")
    table.add_column("Task ID")
    table.add_column("Status")
    table.add_column("Progress")
    for task_id, status, prog in tasks:
        table.add_row(task_id, status, f"{prog}%")
    return table


def main():
    """Run the main terminal user interface (TUI) application.

    Initializes and renders a dashboard layout within a `rich.live.Live` display
    context. The dashboard is composed of four panels: a header, a task backlog
    table, phase details, and a footer. The function then simulates the
    progress of a predefined task by periodically updating its completion
    percentage in the backlog table until the task is marked as complete.
    """
    layout = make_layout()
    tasks = [
        ["T1", "Success", 100],
        ["T2", "Running", 45],
        ["T3", "Pending", 0],
    ]

    with Live(layout, refresh_per_second=4, screen=True):
        layout["header"].update(
            Panel("APEX COMMAND CENTER | Cost: $1.24", style="bold blue")
        )
        layout["backlog"].update(generate_table(tasks))
        layout["details"].update(
            Panel(
                "CURRENT PHASE: [bold yellow]DEBATE[/]\nREASONING: Architect is auditing Doctor's rescue plan to ensure Zero-Workaround compliance.",
                title="Phase Details",
            )
        )
        layout["footer"].update(
            Panel("Press Ctrl+C to abort batch process safely.", style="dim")
        )

        for i in range(45, 101, 5):
            tasks[1][2] = i
            layout["backlog"].update(generate_table(tasks))
            time.sleep(0.5)


if __name__ == "__main__":
    main()
