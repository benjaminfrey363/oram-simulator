from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from oram_sim.block import Block, DummyBlock
from oram_sim.path_oram import AccessStep, PathORAM
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot


T = TypeVar("T")


def format_visible_block(
    block: Block[T] | DummyBlock,
    show_values: bool = False,
) -> str:
    """
    Format one visible bucket slot.

    Real blocks are shown as B{id}@L{leaf}.
    Dummy blocks are shown as D.

    In a real ORAM, the server should not be able to distinguish these.
    We show the distinction explicitly because this is a simulator.
    """
    if isinstance(block, DummyBlock):
        return "D"

    if show_values:
        return f"B{block.logical_id}@L{block.leaf}={block.value}"

    return f"B{block.logical_id}@L{block.leaf}"


def format_bucket(
    oram: PathORAM[T],
    bucket_index: int,
    highlighted: bool = False,
    show_values: bool = False,
) -> str:
    """
    Format one bucket using the padded server-visible view.
    """
    visible_blocks = oram.server_bucket_view(bucket_index)
    contents = ",".join(
        format_visible_block(block, show_values=show_values)
        for block in visible_blocks
    )

    label = f"[{bucket_index}: {contents}]"

    if highlighted:
        return f"*{label}*"

    return label


def format_tree(
    oram: PathORAM[T],
    highlighted_buckets: Iterable[int] | None = None,
    show_values: bool = False,
) -> str:
    """
    Format the binary tree server as a terminal-friendly diagram.

    The tree is displayed by depth. Buckets are padded with dummy blocks, so
    this represents the server-visible fixed-size bucket view.

    highlighted_buckets can be used to mark a touched path.
    """
    highlighted = set(highlighted_buckets or [])

    labels_by_depth: list[list[str]] = []

    for depth in range(oram.height + 1):
        start = 2**depth
        end = 2 ** (depth + 1)

        labels = [
            format_bucket(
                oram,
                bucket_index,
                highlighted=bucket_index in highlighted,
                show_values=show_values,
            )
            for bucket_index in range(start, end)
        ]

        labels_by_depth.append(labels)

    max_label_width = max(
        len(label)
        for labels in labels_by_depth
        for label in labels
    )

    cell_width = max_label_width + 2
    lines: list[str] = []

    for depth, labels in enumerate(labels_by_depth):
        centered_labels = [
            label.center(cell_width)
            for label in labels
        ]

        # Simple spacing heuristic. This is intended for small pedagogical
        # trees, not huge production diagrams.
        indent_width = (2 ** (oram.height - depth) - 1) * (cell_width // 2)
        gap_width = max(2, (2 ** (oram.height - depth + 1) - 1) * (cell_width // 2))

        indent = " " * indent_width
        gap = " " * gap_width

        tree_line = indent + gap.join(centered_labels).rstrip()
        lines.append(f"depth {depth}: {tree_line}")

    return "\n".join(lines)


def format_tree_with_highlighted_path(
    oram: PathORAM[T],
    leaf: int,
    show_values: bool = False,
) -> str:
    """
    Format the tree with the root-to-leaf path highlighted.
    """
    path = oram.server.path_bucket_indices(leaf)

    header = [
        f"highlighted leaf: {leaf}",
        f"highlighted path: {path}",
        "",
    ]

    return "\n".join(header) + format_tree(
        oram,
        highlighted_buckets=path,
        show_values=show_values,
    )


def format_position_map(oram: PathORAM[T]) -> str:
    """
    Format the private client-side position map.
    """
    lines = ["private position map:"]

    for logical_id, leaf in sorted(oram.position_entries().items()):
        lines.append(f"  block {logical_id} -> leaf {leaf}")

    return "\n".join(lines)


def format_stash(
    oram: PathORAM[T],
    show_values: bool = False,
) -> str:
    """
    Format the private client-side stash.
    """
    blocks = sorted(
        oram.stash_blocks(),
        key=lambda block: block.logical_id,
    )

    lines = ["private stash:"]

    if not blocks:
        lines.append("  empty")
        return "\n".join(lines)

    for block in blocks:
        if show_values:
            lines.append(
                f"  block {block.logical_id}: "
                f"leaf={block.leaf}, value={block.value}"
            )
        else:
            lines.append(
                f"  block {block.logical_id}: leaf={block.leaf}"
            )

    return "\n".join(lines)


def format_full_state(
    oram: PathORAM[T],
    highlighted_leaf: int | None = None,
    show_values: bool = False,
) -> str:
    """
    Format the tree, position map, and stash together.
    """
    if highlighted_leaf is None:
        tree = format_tree(oram, show_values=show_values)
    else:
        tree = format_tree_with_highlighted_path(
            oram,
            leaf=highlighted_leaf,
            show_values=show_values,
        )

    return "\n\n".join(
        [
            tree,
            format_position_map(oram),
            format_stash(oram, show_values=show_values),
        ]
    )

def format_access_step(step: AccessStep[T]) -> str:
    """
    Format metadata for one stepped Path ORAM access phase.
    """
    phase_titles = {
        "before_access": "Before access",
        "after_path_read": "After path read into stash",
        "after_remap": "After remapping target block",
        "after_eviction": "After eviction/write-back",
    }

    lines = [
        phase_titles[step.phase],
        f"  logical block: {step.logical_id}",
        f"  old leaf:      {step.old_leaf}",
        f"  touched path:  {step.path}",
    ]

    if step.new_leaf is not None:
        lines.append(f"  new leaf:      {step.new_leaf}")

    if step.read_value is not None:
        lines.append(f"  read value:    {step.read_value}")

    lines.extend(
        [
            f"  stash size:    {step.stash_size}",
            f"  trace so far:  {step.physical_trace or []}",
        ]
    )

    return "\n".join(lines)

def format_tree_snapshot(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
) -> str:
    """
    Format a captured tree snapshot.

    This does not read from a live ORAM object. It only uses the captured
    snapshot state, which makes it suitable for future graphical renderers.
    """
    labels_by_depth: list[list[str]] = []

    for depth in range(snapshot.height + 1):
        start = 2**depth
        end = 2 ** (depth + 1)

        labels: list[str] = []

        for bucket_index in range(start, end):
            visible_blocks = snapshot.bucket(bucket_index)
            contents = ",".join(
                format_visible_block(block, show_values=show_values)
                for block in visible_blocks
            )

            label = f"[{bucket_index}: {contents}]"

            if bucket_index in snapshot.highlighted_buckets:
                label = f"*{label}*"

            labels.append(label)

        labels_by_depth.append(labels)

    max_label_width = max(
        len(label)
        for labels in labels_by_depth
        for label in labels
    )

    cell_width = max_label_width + 2
    lines: list[str] = []

    for depth, labels in enumerate(labels_by_depth):
        centered_labels = [
            label.center(cell_width)
            for label in labels
        ]

        indent_width = (2 ** (snapshot.height - depth) - 1) * (cell_width // 2)
        gap_width = max(
            2,
            (2 ** (snapshot.height - depth + 1) - 1) * (cell_width // 2),
        )

        indent = " " * indent_width
        gap = " " * gap_width

        tree_line = indent + gap.join(centered_labels).rstrip()
        lines.append(f"depth {depth}: {tree_line}")

    return "\n".join(lines)


def format_position_map_snapshot(snapshot: ORAMStateSnapshot[T]) -> str:
    lines = ["private position map:"]

    for logical_id, leaf in sorted(snapshot.position_map.items()):
        lines.append(f"  block {logical_id} -> leaf {leaf}")

    return "\n".join(lines)


def format_stash_snapshot(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
) -> str:
    blocks = sorted(
        snapshot.stash,
        key=lambda block: block.logical_id,
    )

    lines = ["private stash:"]

    if not blocks:
        lines.append("  empty")
        return "\n".join(lines)

    for block in blocks:
        if show_values:
            lines.append(
                f"  block {block.logical_id}: "
                f"leaf={block.leaf}, value={block.value}"
            )
        else:
            lines.append(f"  block {block.logical_id}: leaf={block.leaf}")

    return "\n".join(lines)


def format_state_snapshot(
    snapshot: ORAMStateSnapshot[T],
    show_values: bool = False,
) -> str:
    invariant_text = (
        "placement invariant holds: "
        f"{snapshot.invariant_holds}"
    )

    return "\n\n".join(
        [
            format_tree_snapshot(snapshot, show_values=show_values),
            format_position_map_snapshot(snapshot),
            format_stash_snapshot(snapshot, show_values=show_values),
            invariant_text,
        ]
    )


def format_access_snapshot(snapshot: AccessSnapshot[T]) -> str:
    """
    Format metadata for one captured Path ORAM access phase.
    """
    phase_titles = {
        "before_access": "Before access",
        "after_path_read": "After path read into stash",
        "after_remap": "After remapping target block",
        "after_eviction": "After eviction/write-back",
    }

    lines = [
        phase_titles[snapshot.phase],
        f"  logical block: {snapshot.logical_id}",
        f"  old leaf:      {snapshot.old_leaf}",
        f"  touched path:  {list(snapshot.path)}",
    ]

    if snapshot.new_leaf is not None:
        lines.append(f"  new leaf:      {snapshot.new_leaf}")

    if snapshot.read_value is not None:
        lines.append(f"  read value:    {snapshot.read_value}")

    lines.extend(
        [
            f"  stash size:    {snapshot.stash_size}",
            f"  trace so far:  {list(snapshot.physical_trace)}",
            f"  invariant:     {snapshot.state.invariant_holds}",
        ]
    )

    return "\n".join(lines)
