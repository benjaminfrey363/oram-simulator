from __future__ import annotations

from typing import TypeVar

from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from oram_sim.block import Block, DummyBlock
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot


T = TypeVar("T")


def rich_access_snapshot(
    snapshot: AccessSnapshot[T],
    show_values: bool = False,
):
    """
    Build a Rich renderable for one access-phase snapshot.
    """
    return Group(
        rich_access_metadata(snapshot),
        Columns(
            [
                Panel(
                    rich_tree_snapshot(snapshot.state, show_values=show_values),
                    title="Server-visible padded tree",
                    border_style="blue",
                ),
                Panel(
                    Group(
                        rich_position_map(snapshot.state),
                        Text(""),
                        rich_stash(snapshot.state, show_values=show_values),
                    ),
                    title="Private client state",
                    border_style="green",
                ),
            ],
            equal=False,
            expand=True,
        ),
        rich_trace_panel(snapshot.state),
    )


def rich_state_snapshot(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
):
    """
    Build a Rich renderable for a standalone ORAM state snapshot.
    """
    return Group(
        Columns(
            [
                Panel(
                    rich_tree_snapshot(snapshot, show_values=show_values),
                    title="Server-visible padded tree",
                    border_style="blue",
                ),
                Panel(
                    Group(
                        rich_position_map(snapshot),
                        Text(""),
                        rich_stash(snapshot, show_values=show_values),
                    ),
                    title="Private client state",
                    border_style="green",
                ),
            ],
            equal=False,
            expand=True,
        ),
        rich_trace_panel(snapshot),
    )


def rich_access_metadata(snapshot: AccessSnapshot[T]) -> Panel:
    phase_titles = {
        "before_access": "Before access",
        "after_path_read": "After path read into stash",
        "after_remap": "After remapping target block",
        "after_eviction": "After eviction/write-back",
    }

    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold")
    table.add_column()

    table.add_row("phase", phase_titles[snapshot.phase])
    table.add_row("logical block", str(snapshot.logical_id))
    table.add_row("old leaf", str(snapshot.old_leaf))
    table.add_row("touched path", str(list(snapshot.path)))

    if snapshot.new_leaf is not None:
        table.add_row("new leaf", str(snapshot.new_leaf))

    if snapshot.read_value is not None:
        table.add_row("read value", repr(snapshot.read_value))

    table.add_row("stash size", str(snapshot.stash_size))
    table.add_row("invariant holds", str(snapshot.state.invariant_holds))

    return Panel(
        table,
        title="Path ORAM access phase",
        border_style=_phase_border_style(snapshot.phase),
    )


def rich_tree_snapshot(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
) -> Tree:
    """
    Render the binary tree server as a Rich tree.

    Highlighted buckets are the path touched by the current access.
    """
    root = Tree(
        _bucket_markup(snapshot, 1, show_values=show_values),
        guide_style="bright_black",
    )

    _add_children(
        root,
        snapshot=snapshot,
        bucket_index=1,
        show_values=show_values,
    )

    return root


def rich_position_map(snapshot: ORAMStateSnapshot[T]) -> Table:
    table = Table(
        title="Position map",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold green",
    )

    table.add_column("Block", justify="right")
    table.add_column("Leaf", justify="right")

    for logical_id, leaf in sorted(snapshot.position_map.items()):
        table.add_row(str(logical_id), str(leaf))

    return table


def rich_stash(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
) -> Table:
    table = Table(
        title="Stash",
        box=box.SIMPLE,
        show_header=True,
        header_style="bold magenta",
    )

    table.add_column("Block", justify="right")
    table.add_column("Leaf", justify="right")

    if show_values:
        table.add_column("Value")

    if not snapshot.stash:
        if show_values:
            table.add_row("-", "-", "empty")
        else:
            table.add_row("-", "-")
        return table

    for block in sorted(snapshot.stash, key=lambda block: block.logical_id):
        if show_values:
            table.add_row(
                str(block.logical_id),
                str(block.leaf),
                repr(block.value),
            )
        else:
            table.add_row(str(block.logical_id), str(block.leaf))

    return table


def rich_trace_panel(snapshot: ORAMStateSnapshot[T]) -> Panel:
    trace_text = Text(str(list(snapshot.physical_trace)))

    return Panel(
        trace_text,
        title="Server-visible bucket-index trace so far",
        border_style="bright_black",
    )


def _add_children(
    tree: Tree,
    snapshot: ORAMStateSnapshot[T],
    bucket_index: int,
    show_values: bool,
) -> None:
    left = 2 * bucket_index
    right = 2 * bucket_index + 1

    if left <= snapshot.num_buckets:
        left_tree = tree.add(
            _bucket_markup(snapshot, left, show_values=show_values),
            guide_style="bright_black",
        )
        _add_children(
            left_tree,
            snapshot=snapshot,
            bucket_index=left,
            show_values=show_values,
        )

    if right <= snapshot.num_buckets:
        right_tree = tree.add(
            _bucket_markup(snapshot, right, show_values=show_values),
            guide_style="bright_black",
        )
        _add_children(
            right_tree,
            snapshot=snapshot,
            bucket_index=right,
            show_values=show_values,
        )


def _bucket_markup(
    snapshot: ORAMStateSnapshot[T],
    bucket_index: int,
    show_values: bool,
) -> str:
    highlighted = bucket_index in snapshot.highlighted_buckets

    blocks = snapshot.bucket(bucket_index)
    slots = " | ".join(
        _block_markup(block, show_values=show_values)
        for block in blocks
    )

    if highlighted:
        return (
            f"[bold black on yellow] bucket {bucket_index} [/bold black on yellow] "
            f"{slots}"
        )

    return f"[bold]bucket {bucket_index}[/bold] {slots}"


def _block_markup(
    block: Block[T] | DummyBlock,
    show_values: bool,
) -> str:
    if isinstance(block, DummyBlock):
        return "[dim]D[/dim]"

    if show_values:
        value = escape(repr(block.value))
        return (
            f"[bold cyan]B{block.logical_id}[/bold cyan]"
            f"@[green]L{block.leaf}[/green]"
            f"=[white]{value}[/white]"
        )

    return (
        f"[bold cyan]B{block.logical_id}[/bold cyan]"
        f"@[green]L{block.leaf}[/green]"
    )


def _phase_border_style(phase: str) -> str:
    if phase == "before_access":
        return "blue"

    if phase == "after_path_read":
        return "yellow"

    if phase == "after_remap":
        return "magenta"

    if phase == "after_eviction":
        return "green"

    return "white"
