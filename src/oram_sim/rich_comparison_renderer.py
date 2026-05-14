from __future__ import annotations

from typing import TypeVar

from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from oram_sim.comparison import ComparisonFrame
from oram_sim.rich_renderer import rich_state_snapshot


T = TypeVar("T")


def rich_comparison_frame(
    frame: ComparisonFrame[T],
    show_values: bool = False,
):
    """
    Build a Rich renderable for a NaiveStorage vs PathORAM comparison frame.
    """
    if frame.kind == "profile":
        return Panel(
            frame.profile_text or "",
            title="Workload profile",
            border_style="cyan",
        )

    if frame.kind in {"initial", "final"}:
        if frame.path_oram_state is None:
            raise RuntimeError(f"{frame.kind} frame is missing path_oram_state")

        return rich_state_snapshot(
            frame.path_oram_state,
            show_values=show_values,
        )

    if frame.kind == "operation":
        return _rich_operation_comparison(frame, show_values=show_values)

    raise RuntimeError(f"unsupported comparison frame kind: {frame.kind}")


def _rich_operation_comparison(
    frame: ComparisonFrame[T],
    show_values: bool,
):
    if frame.naive_observation is None:
        raise RuntimeError("operation frame is missing naive_observation")

    if frame.path_oram_observation is None:
        raise RuntimeError("operation frame is missing path_oram_observation")

    path_state = frame.path_oram_observation.final_snapshot.state

    return Group(
        _rich_operation_header(frame),
        Columns(
            [
                Panel(
                    _rich_naive_observation(frame),
                    title="NaiveStorage",
                    border_style="red",
                ),
                Panel(
                    _rich_path_oram_observation(frame),
                    title="PathORAM",
                    border_style="green",
                ),
            ],
            expand=True,
            equal=True,
        ),
        Panel(
            rich_state_snapshot(path_state, show_values=show_values),
            title="PathORAM state after operation",
            border_style="blue",
        ),
    )


def _rich_operation_header(frame: ComparisonFrame[T]) -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("operation", frame.operation or "-")

    if frame.read_values_match is True:
        table.add_row("read values match", "[green]True[/green]")
    elif frame.read_values_match is False:
        table.add_row("read values match", "[red]False[/red]")
    else:
        table.add_row("read values match", "-")

    return Panel(
        table,
        title="Logical operation",
        border_style="cyan",
    )


def _rich_naive_observation(frame: ComparisonFrame[T]) -> Table:
    observation = frame.naive_observation

    if observation is None:
        raise RuntimeError("missing naive observation")

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("server sees address", str(observation.observed_address))
    table.add_row("physical trace", str(list(observation.physical_trace)))

    if observation.read_value is not None:
        table.add_row("read result", repr(observation.read_value))

    table.add_row(
        "leakage story",
        "logical id is directly visible",
    )

    return table


def _rich_path_oram_observation(frame: ComparisonFrame[T]) -> Table:
    observation = frame.path_oram_observation

    if observation is None:
        raise RuntimeError("missing Path ORAM observation")

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("server observes leaf", str(observation.observed_leaf))
    table.add_row("server observes path", str(list(observation.observed_path)))
    table.add_row(
        "observed leaves so far",
        str(list(observation.observed_leaves_so_far)),
    )
    table.add_row("bucket-index trace", str(list(observation.physical_trace)))

    if observation.read_value is not None:
        table.add_row("read result", repr(observation.read_value))

    table.add_row(
        "leakage story",
        "logical id is hidden behind remapped paths",
    )

    return table
