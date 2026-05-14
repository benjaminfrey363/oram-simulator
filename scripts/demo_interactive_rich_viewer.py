from __future__ import annotations

from rich.console import Console

from oram_sim.path_oram import PathORAM
from oram_sim.rich_renderer import rich_access_snapshot, rich_state_snapshot
from oram_sim.workload import Read, Write, WorkloadOperation, format_operation


def wait_for_enter(console: Console, message: str = "Press Enter to continue...") -> None:
    console.print()
    console.input(f"[bold bright_black]{message}[/bold bright_black]")


def render_screen(console: Console, title: str, renderable) -> None:
    console.clear()
    console.rule(f"[bold]{title}[/bold]")
    console.print()
    console.print(renderable)


def main() -> None:
    console = Console()

    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    workload: list[WorkloadOperation] = [
        Read(3),
        Read(3),
        Write(3, "updated-3"),
        Read(3),
        Write(1, "updated-1"),
        Read(1),
    ]

    render_screen(
        console,
        title="Initial Path ORAM state",
        renderable=rich_state_snapshot(oram.state_snapshot(), show_values=False),
    )
    wait_for_enter(console)

    for query_index, operation in enumerate(workload, start=1):
        operation_label = format_operation(operation)

        if isinstance(operation, Read):
            snapshots = oram.read_snapshots(operation.logical_id)
        elif isinstance(operation, Write):
            snapshots = oram.write_snapshots(operation.logical_id, operation.value)
        else:
            raise TypeError(f"Unsupported operation: {operation!r}")

        for snapshot in snapshots:
            render_screen(
                console,
                title=f"Query {query_index}: {operation_label}",
                renderable=rich_access_snapshot(snapshot, show_values=False),
            )

            if snapshot.phase == "after_path_read":
                console.print()
                console.print(
                    "[yellow]Debug note:[/yellow] path blocks have been copied "
                    "into the stash, but the server path has not yet been "
                    "rewritten. The placement invariant can be temporarily false."
                )

            if snapshot.phase == "after_remap":
                console.print()
                console.print(
                    "[magenta]Debug note:[/magenta] the target block now has its "
                    "new leaf assignment in the stash. Eviction has not happened yet."
                )

            wait_for_enter(console)

    render_screen(
        console,
        title="Final Path ORAM state",
        renderable=rich_state_snapshot(oram.state_snapshot(), show_values=False),
    )

    console.print()
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    main()
    