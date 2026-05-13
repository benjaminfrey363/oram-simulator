from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from oram_sim.analysis import TraceSummary, summarize_physical_trace
from oram_sim.path_oram import PathORAM
from oram_sim.storage import NaiveStorage


T = TypeVar("T")


@dataclass(frozen=True)
class NaiveWorkloadResult:
    logical_pattern: list[int]
    physical_trace: list[int]
    summary: TraceSummary


@dataclass(frozen=True)
class PathORAMWorkloadResult:
    logical_pattern: list[int]
    physical_trace: list[int]
    grouped_trace: list[list[int]]
    observed_leaves: list[int]
    physical_accesses_per_logical_access: int
    invariant_holds: bool
    summary: TraceSummary


def run_naive_read_workload(
    initial_values: Sequence[T],
    logical_pattern: Sequence[int],
) -> NaiveWorkloadResult:
    """
    Run a read-only logical workload against NaiveStorage.
    """
    storage = NaiveStorage(list(initial_values))

    for logical_id in logical_pattern:
        storage.read(logical_id)

    physical_trace = storage.trace.physical_addresses()

    return NaiveWorkloadResult(
        logical_pattern=list(logical_pattern),
        physical_trace=physical_trace,
        summary=summarize_physical_trace(physical_trace),
    )


def run_path_oram_read_workload(
    initial_values: Sequence[T],
    logical_pattern: Sequence[int],
    bucket_capacity: int = 4,
    height: int | None = None,
    seed: int | None = None,
) -> PathORAMWorkloadResult:
    """
    Run a read-only logical workload against PathORAM.
    """
    oram = PathORAM(
        initial_values=initial_values,
        bucket_capacity=bucket_capacity,
        height=height,
        seed=seed,
    )

    physical_accesses_per_logical_access = 2 * (oram.height + 1)

    for logical_id in logical_pattern:
        oram.read(logical_id)

    physical_trace = oram.physical_trace()
    grouped_trace = chunk_trace(
        physical_trace,
        chunk_size=physical_accesses_per_logical_access,
    )
    observed_leaves = observed_leaves_from_grouped_trace(
        grouped_trace=grouped_trace,
        height=oram.height,
    )

    return PathORAMWorkloadResult(
        logical_pattern=list(logical_pattern),
        physical_trace=physical_trace,
        grouped_trace=grouped_trace,
        observed_leaves=observed_leaves,
        physical_accesses_per_logical_access=physical_accesses_per_logical_access,
        invariant_holds=oram.check_invariant(),
        summary=summarize_physical_trace(physical_trace),
    )


def chunk_trace(trace: Sequence[int], chunk_size: int) -> list[list[int]]:
    """
    Split a physical trace into chunks of a fixed size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if len(trace) % chunk_size != 0:
        raise ValueError(
            f"trace length {len(trace)} is not divisible by chunk size {chunk_size}"
        )

    return [
        list(trace[i : i + chunk_size])
        for i in range(0, len(trace), chunk_size)
    ]


def observed_leaves_from_grouped_trace(
    grouped_trace: Sequence[Sequence[int]],
    height: int,
) -> list[int]:
    """
    Convert grouped Path ORAM bucket traces into observed leaves.

    For a tree of height h, one Path ORAM access touches:

        read path of length h + 1
        write path of length h + 1

    Example for height 2:

        [1, 2, 5, 1, 2, 5]

    The read path is [1, 2, 5]. The final bucket 5 is a leaf bucket.
    Since the leaf buckets are 4, 5, 6, 7, this corresponds to leaf label 1.
    """
    if height < 0:
        raise ValueError("height must be nonnegative")

    path_length = height + 1
    group_size = 2 * path_length
    first_leaf_bucket = 2**height
    n_leaves = 2**height

    observed_leaves: list[int] = []

    for group in grouped_trace:
        if len(group) != group_size:
            raise ValueError(
                f"expected group of length {group_size}, got {len(group)}"
            )

        read_path = list(group[:path_length])
        write_path = list(group[path_length:])

        if read_path != write_path:
            raise ValueError(
                "expected read path and write path to be equal within one access"
            )

        leaf_bucket = read_path[-1]
        leaf = leaf_bucket - first_leaf_bucket

        if leaf < 0 or leaf >= n_leaves:
            raise ValueError(
                f"computed invalid leaf {leaf} from leaf bucket {leaf_bucket}"
            )

        observed_leaves.append(leaf)

    return observed_leaves
