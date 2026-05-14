from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, Literal, TypeVar, cast

from oram_sim.path_oram import PathORAM
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot
from oram_sim.storage import NaiveStorage
from oram_sim.workload import Read, WorkloadOperation, Write, format_operation


T = TypeVar("T")


ComparisonFrameKind = Literal["profile", "initial", "operation", "final"]


@dataclass(frozen=True)
class NaiveObservation(Generic[T]):
    operation: str
    observed_address: int
    physical_trace: tuple[int, ...]
    read_value: T | None = None


@dataclass(frozen=True)
class PathORAMObservation(Generic[T]):
    operation: str
    observed_leaf: int
    observed_path: tuple[int, ...]
    observed_leaves_so_far: tuple[int, ...]
    physical_trace: tuple[int, ...]
    final_snapshot: AccessSnapshot[T]
    read_value: T | None = None


@dataclass(frozen=True)
class ComparisonFrame(Generic[T]):
    """
    One frame in the NaiveStorage vs PathORAM comparison viewer.
    """

    kind: ComparisonFrameKind
    title: str

    profile_text: str | None = None
    path_oram_state: ORAMStateSnapshot[T] | None = None

    operation_index: int | None = None
    operation_count: int | None = None
    operation: str | None = None

    naive_observation: NaiveObservation[T] | None = None
    path_oram_observation: PathORAMObservation[T] | None = None

    read_values_match: bool | None = None


def build_comparison_frames(
    initial_values: Sequence[T],
    operations: Sequence[WorkloadOperation],
    profile_text: str,
    bucket_capacity: int = 4,
    height: int | None = None,
    seed: int | None = None,
) -> list[ComparisonFrame[T]]:
    """
    Run the same logical workload against NaiveStorage and PathORAM.

    The returned frames are snapshots suitable for interactive navigation.
    """
    naive = NaiveStorage(list(initial_values))

    oram = PathORAM(
        initial_values=initial_values,
        bucket_capacity=bucket_capacity,
        height=height,
        seed=seed,
    )

    frames: list[ComparisonFrame[T]] = []

    frames.append(
        ComparisonFrame(
            kind="profile",
            title="NaiveStorage vs PathORAM comparison",
            profile_text=profile_text,
        )
    )

    frames.append(
        ComparisonFrame(
            kind="initial",
            title="Initial Path ORAM state",
            path_oram_state=oram.state_snapshot(),
        )
    )

    observed_leaves: list[int] = []
    operation_count = len(operations)

    for operation_index, operation in enumerate(operations, start=1):
        operation_label = format_operation(operation)

        if isinstance(operation, Read):
            naive_read_value = naive.read(operation.logical_id)
            snapshots = list(oram.read_snapshots(operation.logical_id))

            if not snapshots:
                raise RuntimeError("Path ORAM read produced no snapshots")

            final_snapshot = snapshots[-1]
            path_read_value = final_snapshot.read_value

            read_values_match = naive_read_value == path_read_value

        elif isinstance(operation, Write):
            naive.write(operation.logical_id, cast(T, operation.value))
            snapshots = list(
                oram.write_snapshots(
                    operation.logical_id,
                    cast(T, operation.value),
                )
            )

            if not snapshots:
                raise RuntimeError("Path ORAM write produced no snapshots")

            final_snapshot = snapshots[-1]
            naive_read_value = None
            path_read_value = None
            read_values_match = None

        else:
            raise TypeError(f"Unsupported operation: {operation!r}")

        observed_leaves.append(final_snapshot.old_leaf)

        naive_observation = NaiveObservation(
            operation=operation_label,
            observed_address=operation.logical_id,
            physical_trace=tuple(naive.trace.physical_addresses()),
            read_value=naive_read_value,
        )

        path_observation = PathORAMObservation(
            operation=operation_label,
            observed_leaf=final_snapshot.old_leaf,
            observed_path=final_snapshot.path,
            observed_leaves_so_far=tuple(observed_leaves),
            physical_trace=final_snapshot.physical_trace,
            final_snapshot=final_snapshot,
            read_value=path_read_value,
        )

        frames.append(
            ComparisonFrame(
                kind="operation",
                title=f"Operation {operation_index}/{operation_count}: {operation_label}",
                operation_index=operation_index,
                operation_count=operation_count,
                operation=operation_label,
                naive_observation=naive_observation,
                path_oram_observation=path_observation,
                read_values_match=read_values_match,
            )
        )

    frames.append(
        ComparisonFrame(
            kind="final",
            title="Final Path ORAM state",
            path_oram_state=oram.state_snapshot(),
        )
    )

    return frames
