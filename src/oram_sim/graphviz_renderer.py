from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from oram_sim.block import Block, DummyBlock
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot


T = TypeVar("T")


def snapshot_to_dot(
    snapshot: ORAMStateSnapshot[T],
    title: str | None = None,
    show_values: bool = False,
    show_dummy_ids: bool = False,
) -> str:
    """
    Convert an ORAM state snapshot to Graphviz DOT.

    This function does not require the graphviz Python package. It just returns
    DOT text. Use render_dot() or render_snapshot() to create SVG/PNG files.
    """
    lines: list[str] = [
        "digraph ORAMTree {",
        "  graph [rankdir=TB, splines=line, nodesep=0.45, ranksep=0.75];",
        '  node [shape=box, style="rounded,filled", fontname="Menlo", fontsize=10];',
        '  edge [color="#555555"];',
    ]

    if title is not None:
        lines.append(f'  labelloc="t";')
        lines.append(f'  label="{_dot_escape(title)}";')
        lines.append("")

    for bucket_index in range(1, snapshot.num_buckets + 1):
        highlighted = bucket_index in snapshot.highlighted_buckets
        label = _bucket_label(
            snapshot,
            bucket_index,
            show_values=show_values,
            show_dummy_ids=show_dummy_ids,
        )

        attrs = {
            "label": label,
            "fillcolor": "#ffe599" if highlighted else "#f3f4f6",
            "color": "#cc0000" if highlighted else "#555555",
            "penwidth": "3" if highlighted else "1",
        }

        lines.append(f"  b{bucket_index} {_format_attrs(attrs)};")

    lines.append("")

    for bucket_index in range(1, 2**snapshot.height):
        left = 2 * bucket_index
        right = 2 * bucket_index + 1

        if left <= snapshot.num_buckets:
            lines.append(f"  b{bucket_index} -> b{left};")

        if right <= snapshot.num_buckets:
            lines.append(f"  b{bucket_index} -> b{right};")

    lines.append("")

    for depth in range(snapshot.height + 1):
        start = 2**depth
        end = 2 ** (depth + 1)
        nodes = " ".join(f"b{bucket_index};" for bucket_index in range(start, end))
        lines.append(f"  {{ rank=same; {nodes} }}")

    lines.append("}")

    return "\n".join(lines)


def access_snapshot_to_dot(
    snapshot: AccessSnapshot[T],
    show_values: bool = False,
    show_dummy_ids: bool = False,
) -> str:
    """
    Convert an access-phase snapshot to DOT, including a descriptive title.
    """
    title = _access_snapshot_title(snapshot)

    return snapshot_to_dot(
        snapshot.state,
        title=title,
        show_values=show_values,
        show_dummy_ids=show_dummy_ids,
    )


def write_dot_file(
    dot: str,
    output_path: str | Path,
) -> Path:
    """
    Write DOT text to a file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dot, encoding="utf-8")
    return path


def render_dot(
    dot: str,
    output_path: str | Path,
    fmt: str | None = None,
) -> Path:
    """
    Render DOT text to an output file using the graphviz package.

    output_path can include a suffix, for example:

        snapshots/tree.svg
        snapshots/tree.png

    If fmt is omitted, it is inferred from the suffix. If there is no suffix,
    SVG is used.
    """
    try:
        from graphviz import Source
    except ImportError as exc:
        raise RuntimeError(
            "Rendering requires the graphviz Python package. "
            "Install it with: python3 -m pip install graphviz"
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if fmt is None:
        fmt = output_path.suffix.removeprefix(".") or "svg"

    if output_path.suffix:
        render_base = output_path.with_suffix("")
    else:
        render_base = output_path

    source = Source(dot)
    rendered_path = source.render(
        filename=str(render_base),
        format=fmt,
        cleanup=True,
    )

    return Path(rendered_path)


def render_snapshot(
    snapshot: ORAMStateSnapshot[T],
    output_path: str | Path,
    title: str | None = None,
    show_values: bool = False,
    show_dummy_ids: bool = False,
    fmt: str | None = None,
) -> Path:
    """
    Render an ORAM state snapshot to SVG/PNG/PDF/etc.
    """
    dot = snapshot_to_dot(
        snapshot,
        title=title,
        show_values=show_values,
        show_dummy_ids=show_dummy_ids,
    )

    return render_dot(dot, output_path=output_path, fmt=fmt)


def render_access_snapshot(
    snapshot: AccessSnapshot[T],
    output_path: str | Path,
    show_values: bool = False,
    show_dummy_ids: bool = False,
    fmt: str | None = None,
) -> Path:
    """
    Render an access-phase snapshot to SVG/PNG/PDF/etc.
    """
    dot = access_snapshot_to_dot(
        snapshot,
        show_values=show_values,
        show_dummy_ids=show_dummy_ids,
    )

    return render_dot(dot, output_path=output_path, fmt=fmt)


def _bucket_label(
    snapshot: ORAMStateSnapshot[T],
    bucket_index: int,
    show_values: bool,
    show_dummy_ids: bool,
) -> str:
    blocks = snapshot.bucket(bucket_index)

    slots = [
        _visible_block_label(
            block,
            show_values=show_values,
            show_dummy_ids=show_dummy_ids,
        )
        for block in blocks
    ]

    return f"bucket {bucket_index}\\n" + " | ".join(slots)


def _visible_block_label(
    block: Block[T] | DummyBlock,
    show_values: bool,
    show_dummy_ids: bool,
) -> str:
    if isinstance(block, DummyBlock):
        if show_dummy_ids:
            return f"D{block.dummy_id}"
        return "D"

    if show_values:
        return f"B{block.logical_id}@L{block.leaf}={block.value}"

    return f"B{block.logical_id}@L{block.leaf}"


def _access_snapshot_title(snapshot: AccessSnapshot[T]) -> str:
    phase_titles = {
        "before_access": "Before access",
        "after_path_read": "After path read into stash",
        "after_remap": "After remapping target block",
        "after_eviction": "After eviction/write-back",
    }

    pieces = [
        phase_titles[snapshot.phase],
        f"logical block {snapshot.logical_id}",
        f"old leaf {snapshot.old_leaf}",
    ]

    if snapshot.new_leaf is not None:
        pieces.append(f"new leaf {snapshot.new_leaf}")

    pieces.append(f"path {list(snapshot.path)}")
    pieces.append(f"stash size {snapshot.stash_size}")

    return " | ".join(pieces)


def _format_attrs(attrs: dict[str, str]) -> str:
    return "[" + ", ".join(
        f'{key}="{_dot_escape(value)}"'
        for key, value in attrs.items()
    ) + "]"


def _dot_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
