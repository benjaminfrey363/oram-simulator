from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from oram_sim.path_oram import PathORAM
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot
from oram_sim.workload import Read, WorkloadOperation, Write, format_operation


T = TypeVar("T")


ViewerFrameKind = Literal["profile", "state", "access"]

ViewerCommand = Literal[
    "next",
    "previous",
    "quit",
    "toggle_values",
    "help",
    "stay",
]


@dataclass(frozen=True)
class ViewerFrame(Generic[T]):
    """
    One frame in an interactive ORAM viewer.

    Exactly one of profile_text, state_snapshot, or access_snapshot should be
    populated, depending on kind.
    """

    kind: ViewerFrameKind
    title: str
    profile_text: str | None = None
    state_snapshot: ORAMStateSnapshot[T] | None = None
    access_snapshot: AccessSnapshot[T] | None = None
    note: str | None = None


def build_viewer_frames(
    oram: PathORAM[T],
    operations: Sequence[WorkloadOperation],
    profile_text: str,
) -> list[ViewerFrame[T]]:
    """
    Execute a workload and collect immutable-ish frames for navigation.

    This lets the interactive viewer move forward and backward without trying
    to undo mutations to the live ORAM object.
    """
    frames: list[ViewerFrame[T]] = []

    frames.append(
        ViewerFrame(
            kind="profile",
            title="Path ORAM interactive viewer",
            profile_text=profile_text,
        )
    )

    frames.append(
        ViewerFrame(
            kind="state",
            title="Initial Path ORAM state",
            state_snapshot=oram.state_snapshot(),
        )
    )

    operation_count = len(operations)

    for query_index, operation in enumerate(operations, start=1):
        operation_label = format_operation(operation)

        if isinstance(operation, Read):
            snapshots = oram.read_snapshots(operation.logical_id)
        elif isinstance(operation, Write):
            snapshots = oram.write_snapshots(operation.logical_id, operation.value)
        else:
            raise TypeError(f"Unsupported operation: {operation!r}")

        for snapshot in snapshots:
            frames.append(
                ViewerFrame(
                    kind="access",
                    title=f"Query {query_index}/{operation_count}: {operation_label}",
                    access_snapshot=snapshot,
                    note=_note_for_phase(snapshot.phase),
                )
            )

    frames.append(
        ViewerFrame(
            kind="state",
            title="Final Path ORAM state",
            state_snapshot=oram.state_snapshot(),
        )
    )

    return frames


def parse_viewer_command(text: str) -> ViewerCommand:
    """
    Parse a viewer command.

    Empty input advances to the next frame.
    """
    command = text.strip().lower()

    if command in {"", "n", "next"}:
        return "next"

    if command in {"b", "p", "back", "prev", "previous"}:
        return "previous"

    if command in {"q", "quit", "exit"}:
        return "quit"

    if command in {"v", "values", "toggle"}:
        return "toggle_values"

    if command in {"h", "help", "?"}:
        return "help"

    return "stay"


def viewer_help_text() -> str:
    return "\n".join(
        [
            "Controls:",
            "  Enter / n    next frame",
            "  b / p        previous frame",
            "  v            toggle values",
            "  h / ?        show this help",
            "  q            quit",
        ]
    )


def _note_for_phase(phase: str) -> str | None:
    if phase == "after_path_read":
        return (
            "Debug note: path blocks have been copied into the stash, but the "
            "server path has not yet been rewritten. The placement invariant "
            "can be temporarily false."
        )

    if phase == "after_remap":
        return (
            "Debug note: the target block now has its new leaf assignment in "
            "the stash. Eviction has not happened yet."
        )

    return None
