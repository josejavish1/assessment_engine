import time

#
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


def make_layout() -> Layout:
    """Construct the main application TUI layout with header, footer, backlog, and details panels."""
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
    """Constructs a `rich.table.Table` from an iterable of task records.

    The function initializes a table with predefined columns ("Task ID", "Status",
    "Progress") and populates it by iterating through the input tasks. The
    progress value is formatted as a percentage string for display.

    Args:
        tasks: An iterable of task records. Each record must be a sequence
            (e.g., tuple or list) containing exactly three elements: the
            task ID (str), the status (str), and the progress (int or float).

    Returns:
        A `rich.table.Table` instance populated with the provided task data.

    Raises:
        ValueError: If a record within the `tasks` iterable does not contain
            exactly three elements, preventing successful unpacking.
        TypeError: If a record within the `tasks` iterable is not itself an
            iterable object.
    """
    table = Table(title="Backlog Status")
    table.add_column("Task ID")
    table.add_column("Status")
    table.add_column("Progress")
    for task_id, status, prog in tasks:
        table.add_row(task_id, status, f"{prog}%")
    return table


def main():
    """Initializes and runs a terminal-based user interface for task monitoring.

    This function constructs and displays a terminal dashboard using the rich library.
    The TUI is built on a `Layout` object, which is partitioned into a header, a
    task backlog table, a details panel, and a footer. The entire layout is
    rendered within a `Live` context to enable real-time updates.

    A simulation loop executes to demonstrate progress by periodically
    incrementing a sample task's completion percentage and refreshing the
    backlog table. The application runs until this simulation completes or is
    terminated by the user (Ctrl+C).

    Args:
        None.

    Returns:
        None.
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
