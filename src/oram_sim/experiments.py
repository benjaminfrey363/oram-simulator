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

    return PathORAMWorkloadResult(
        logical_pattern=list(logical_pattern),
        physical_trace=physical_trace,
        grouped_trace=chunk_trace(
            physical_trace,
            chunk_size=physical_accesses_per_logical_access,
        ),
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
