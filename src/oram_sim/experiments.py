from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from oram_sim.analysis import TraceSummary, summarize_physical_trace
from oram_sim.path_oram import PathORAM
from oram_sim.storage import NaiveStorage
from oram_sim.snapshot import AccessPhase

from oram_sim.workload import Read, WorkloadOperation, Write, format_operation

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

@dataclass(frozen=True)
class StashSizeSample:
    """
    One stash-size measurement during a Path ORAM workload.

    query_index:
        One-based index of the logical query in the workload.

    phase:
        The access phase at which the measurement was taken.

    stash_size:
        Number of real blocks in the private stash at this phase.
    """

    query_index: int
    logical_id: int
    phase: AccessPhase
    stash_size: int
    invariant_holds: bool
    physical_trace_length: int
    old_leaf: int
    new_leaf: int | None


@dataclass(frozen=True)
class StashSizeWorkloadResult:
    """
    Stash-size measurements for a read-only Path ORAM workload.
    """

    logical_pattern: list[int]
    samples: list[StashSizeSample]
    max_stash_size: int
    final_stash_size: int
    invariant_holds: bool


def run_path_oram_stash_size_workload(
    initial_values: Sequence[T],
    logical_pattern: Sequence[int],
    bucket_capacity: int = 4,
    height: int | None = None,
    seed: int | None = None,
) -> StashSizeWorkloadResult:
    """
    Run a read-only workload and record stash size after every access phase.
    """
    oram = PathORAM(
        initial_values=initial_values,
        bucket_capacity=bucket_capacity,
        height=height,
        seed=seed,
    )

    samples: list[StashSizeSample] = []

    for query_index, logical_id in enumerate(logical_pattern, start=1):
        for snapshot in oram.read_snapshots(logical_id):
            samples.append(
                StashSizeSample(
                    query_index=query_index,
                    logical_id=logical_id,
                    phase=snapshot.phase,
                    stash_size=snapshot.stash_size,
                    invariant_holds=snapshot.state.invariant_holds,
                    physical_trace_length=len(snapshot.physical_trace),
                    old_leaf=snapshot.old_leaf,
                    new_leaf=snapshot.new_leaf,
                )
            )

    max_stash_size = max(
        (sample.stash_size for sample in samples),
        default=0,
    )

    return StashSizeWorkloadResult(
        logical_pattern=list(logical_pattern),
        samples=samples,
        max_stash_size=max_stash_size,
        final_stash_size=len(oram.stash_blocks()),
        invariant_holds=oram.check_invariant(),
    )


def samples_for_phase(
    result: StashSizeWorkloadResult,
    phase: AccessPhase,
) -> list[StashSizeSample]:
    """
    Return the stash-size samples from one phase.
    """
    return [
        sample
        for sample in result.samples
        if sample.phase == phase
    ]


def final_stash_sizes_by_query(
    result: StashSizeWorkloadResult,
) -> list[int]:
    """
    Return stash sizes after each completed access.

    This uses the after_eviction phase, since that is the final phase of a
    Path ORAM access.
    """
    return [
        sample.stash_size
        for sample in samples_for_phase(result, "after_eviction")
    ]


def format_stash_size_report(result: StashSizeWorkloadResult) -> str:
    """
    Format stash-size measurements as a readable text report.
    """
    lines = [
        f"logical workload:      {result.logical_pattern}",
        f"max stash size:       {result.max_stash_size}",
        f"final stash size:     {result.final_stash_size}",
        f"final invariant:      {result.invariant_holds}",
        "",
        (
            "query  logical  phase                 stash  invariant  "
            "trace_len  old_leaf  new_leaf"
        ),
        "-" * 84,
    ]

    for sample in result.samples:
        new_leaf = "-" if sample.new_leaf is None else str(sample.new_leaf)

        lines.append(
            f"{sample.query_index:>5}  "
            f"{sample.logical_id:>7}  "
            f"{sample.phase:<20}  "
            f"{sample.stash_size:>5}  "
            f"{str(sample.invariant_holds):>9}  "
            f"{sample.physical_trace_length:>9}  "
            f"{sample.old_leaf:>8}  "
            f"{new_leaf:>8}"
        )

    return "\n".join(lines)

@dataclass(frozen=True)
class MixedWorkloadSample(Generic[T]):
    """
    One phase sample from a mixed read/write Path ORAM workload.
    """

    query_index: int
    operation: str
    logical_id: int
    phase: AccessPhase
    stash_size: int
    invariant_holds: bool
    physical_trace_length: int
    old_leaf: int
    new_leaf: int | None
    read_value: T | None


@dataclass(frozen=True)
class MixedWorkloadResult(Generic[T]):
    """
    Result of running a mixed read/write Path ORAM workload.
    """

    operations: list[str]
    read_results: list[T]
    samples: list[MixedWorkloadSample[T]]
    physical_trace: list[int]
    observed_leaves: list[int]
    max_stash_size: int
    final_stash_size: int
    invariant_holds: bool


def run_path_oram_mixed_workload(
    initial_values: Sequence[T],
    operations: Sequence[WorkloadOperation],
    bucket_capacity: int = 4,
    height: int | None = None,
    seed: int | None = None,
) -> MixedWorkloadResult[T]:
    """
    Run a mixed read/write workload against PathORAM.

    Read operations contribute to read_results.
    Write operations update the ORAM but do not contribute to read_results.

    Both reads and writes produce the same server-visible ORAM access pattern:
    one path read followed by one path write.
    """
    oram = PathORAM(
        initial_values=initial_values,
        bucket_capacity=bucket_capacity,
        height=height,
        seed=seed,
    )

    samples: list[MixedWorkloadSample[T]] = []
    read_results: list[T] = []
    observed_leaves: list[int] = []

    for query_index, operation in enumerate(operations, start=1):
        operation_label = format_operation(operation)

        if isinstance(operation, Read):
            snapshot_iterator = oram.read_snapshots(operation.logical_id)
        elif isinstance(operation, Write):
            snapshot_iterator = oram.write_snapshots(
                operation.logical_id,
                operation.value,
            )
        else:
            raise TypeError(f"unsupported workload operation: {operation!r}")

        snapshots = list(snapshot_iterator)

        if len(snapshots) == 0:
            raise RuntimeError("access produced no snapshots")

        final_snapshot = snapshots[-1]
        observed_leaves.append(final_snapshot.old_leaf)

        if isinstance(operation, Read):
            if final_snapshot.read_value is None:
                raise RuntimeError("read operation produced no read value")
            read_results.append(final_snapshot.read_value)

        for snapshot in snapshots:
            samples.append(
                MixedWorkloadSample(
                    query_index=query_index,
                    operation=operation_label,
                    logical_id=operation.logical_id,
                    phase=snapshot.phase,
                    stash_size=snapshot.stash_size,
                    invariant_holds=snapshot.state.invariant_holds,
                    physical_trace_length=len(snapshot.physical_trace),
                    old_leaf=snapshot.old_leaf,
                    new_leaf=snapshot.new_leaf,
                    read_value=snapshot.read_value,
                )
            )

    max_stash_size = max(
        (sample.stash_size for sample in samples),
        default=0,
    )

    return MixedWorkloadResult(
        operations=[format_operation(operation) for operation in operations],
        read_results=read_results,
        samples=samples,
        physical_trace=oram.physical_trace(),
        observed_leaves=observed_leaves,
        max_stash_size=max_stash_size,
        final_stash_size=len(oram.stash_blocks()),
        invariant_holds=oram.check_invariant(),
    )


def final_mixed_stash_sizes_by_query(
    result: MixedWorkloadResult[T],
) -> list[int]:
    """
    Return stash sizes after each completed mixed-workload operation.
    """
    return [
        sample.stash_size
        for sample in result.samples
        if sample.phase == "after_eviction"
    ]


def format_mixed_workload_report(result: MixedWorkloadResult[T]) -> str:
    """
    Format a mixed workload result as a readable report.
    """
    lines = [
        f"operations:           {result.operations}",
        f"read results:         {result.read_results}",
        f"observed leaves:      {result.observed_leaves}",
        f"max stash size:       {result.max_stash_size}",
        f"final stash size:     {result.final_stash_size}",
        f"final invariant:      {result.invariant_holds}",
        "",
        (
            "query  operation                 phase                 stash  "
            "invariant  trace_len  old_leaf  new_leaf  read_value"
        ),
        "-" * 112,
    ]

    for sample in result.samples:
        new_leaf = "-" if sample.new_leaf is None else str(sample.new_leaf)
        read_value = "-" if sample.read_value is None else repr(sample.read_value)

        lines.append(
            f"{sample.query_index:>5}  "
            f"{sample.operation:<24}  "
            f"{sample.phase:<20}  "
            f"{sample.stash_size:>5}  "
            f"{str(sample.invariant_holds):>9}  "
            f"{sample.physical_trace_length:>9}  "
            f"{sample.old_leaf:>8}  "
            f"{new_leaf:>8}  "
            f"{read_value}"
        )

    return "\n".join(lines)

@dataclass(frozen=True)
class SeedTrialResult:
    """
    Result from one random seed in a stash-size experiment.
    """

    seed: int
    operation_count: int
    max_stash_size: int
    final_stash_size: int
    invariant_holds: bool


@dataclass(frozen=True)
class SeedSweepResult:
    """
    Result from running the same workload over many random seeds.
    """

    workload_name: str
    trials: list[SeedTrialResult]

    @property
    def seeds(self) -> list[int]:
        return [trial.seed for trial in self.trials]

    @property
    def max_stash_sizes(self) -> list[int]:
        return [trial.max_stash_size for trial in self.trials]

    @property
    def final_stash_sizes(self) -> list[int]:
        return [trial.final_stash_size for trial in self.trials]

    @property
    def all_invariants_hold(self) -> bool:
        return all(trial.invariant_holds for trial in self.trials)

    @property
    def largest_observed_stash_size(self) -> int:
        return max(self.max_stash_sizes, default=0)


def run_path_oram_stash_size_seed_sweep(
    initial_values: Sequence[T],
    logical_pattern: Sequence[int],
    seeds: Sequence[int],
    workload_name: str = "read-only",
    bucket_capacity: int = 4,
    height: int | None = None,
) -> SeedSweepResult:
    """
    Run the same read-only stash-size workload over many random seeds.
    """
    if len(seeds) == 0:
        raise ValueError("seeds must be nonempty")

    trials: list[SeedTrialResult] = []

    for seed in seeds:
        result = run_path_oram_stash_size_workload(
            initial_values=initial_values,
            logical_pattern=logical_pattern,
            bucket_capacity=bucket_capacity,
            height=height,
            seed=seed,
        )

        trials.append(
            SeedTrialResult(
                seed=seed,
                operation_count=len(logical_pattern),
                max_stash_size=result.max_stash_size,
                final_stash_size=result.final_stash_size,
                invariant_holds=result.invariant_holds,
            )
        )

    return SeedSweepResult(
        workload_name=workload_name,
        trials=trials,
    )


def run_path_oram_mixed_seed_sweep(
    initial_values: Sequence[T],
    operations: Sequence[WorkloadOperation],
    seeds: Sequence[int],
    workload_name: str = "mixed",
    bucket_capacity: int = 4,
    height: int | None = None,
) -> SeedSweepResult:
    """
    Run the same mixed read/write workload over many random seeds.
    """
    if len(seeds) == 0:
        raise ValueError("seeds must be nonempty")

    trials: list[SeedTrialResult] = []

    for seed in seeds:
        result = run_path_oram_mixed_workload(
            initial_values=initial_values,
            operations=operations,
            bucket_capacity=bucket_capacity,
            height=height,
            seed=seed,
        )

        trials.append(
            SeedTrialResult(
                seed=seed,
                operation_count=len(operations),
                max_stash_size=result.max_stash_size,
                final_stash_size=result.final_stash_size,
                invariant_holds=result.invariant_holds,
            )
        )

    return SeedSweepResult(
        workload_name=workload_name,
        trials=trials,
    )


def format_seed_sweep_report(result: SeedSweepResult) -> str:
    """
    Format a seed-sweep result as a readable text report.
    """
    max_sizes = result.max_stash_sizes

    average_max = (
        sum(max_sizes) / len(max_sizes)
        if max_sizes
        else 0.0
    )

    lines = [
        f"workload:                    {result.workload_name}",
        f"number of seeds:             {len(result.trials)}",
        f"all invariants hold:          {result.all_invariants_hold}",
        f"largest observed stash size:  {result.largest_observed_stash_size}",
        f"average max stash size:       {average_max:.2f}",
        "",
        "seed  operations  max_stash  final_stash  invariant",
        "-" * 56,
    ]

    for trial in result.trials:
        lines.append(
            f"{trial.seed:>4}  "
            f"{trial.operation_count:>10}  "
            f"{trial.max_stash_size:>9}  "
            f"{trial.final_stash_size:>11}  "
            f"{str(trial.invariant_holds):>9}"
        )

    return "\n".join(lines)

