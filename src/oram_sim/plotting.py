from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence, TypeVar

from oram_sim.experiments import (
    MixedWorkloadResult,
    StashSizeWorkloadResult,
    SeedSweepResult,
    final_mixed_stash_sizes_by_query,
    final_stash_sizes_by_query,
)
from oram_sim.snapshot import AccessPhase



T = TypeVar("T")


_PHASE_ORDER: tuple[AccessPhase, ...] = (
    "before_access",
    "after_path_read",
    "after_remap",
    "after_eviction",
)


class _HasPhaseAndStashSize(Protocol):
    @property
    def phase(self) -> AccessPhase:
        return self.phase
    @property
    def stash_size(self) -> int:
        return self.stash_size


@dataclass(frozen=True)
class StashSizeSeries:
    """
    A named stash-size time series.

    query_indices:
        One-based query/operation indices.

    stash_sizes:
        Stash size measurements.
    """

    name: str
    query_indices: list[int]
    stash_sizes: list[int]

    def __post_init__(self) -> None:
        if len(self.query_indices) != len(self.stash_sizes):
            raise ValueError("query_indices and stash_sizes must have the same length")


@dataclass(frozen=True)
class MaxStashSizeSeries:
    """
    Max-stash-size measurements over many random seeds.
    """

    name: str
    seeds: list[int]
    max_stash_sizes: list[int]

    def __post_init__(self) -> None:
        if len(self.seeds) != len(self.max_stash_sizes):
            raise ValueError("seeds and max_stash_sizes must have the same length")


def max_stash_size_series_from_seed_sweep(
    result: SeedSweepResult,
) -> MaxStashSizeSeries:
    """
    Extract max stash size by seed from a seed-sweep experiment.
    """
    return MaxStashSizeSeries(
        name=result.workload_name,
        seeds=result.seeds,
        max_stash_sizes=result.max_stash_sizes,
    )


def stash_size_series_from_result(
    name: str,
    result: StashSizeWorkloadResult,
) -> StashSizeSeries:
    """
    Extract stash size after each completed read-only query.

    This uses the after_eviction phase.
    """
    stash_sizes = final_stash_sizes_by_query(result)
    query_indices = list(range(1, len(stash_sizes) + 1))

    return StashSizeSeries(
        name=name,
        query_indices=query_indices,
        stash_sizes=stash_sizes,
    )


def stash_size_series_from_mixed_result(
    name: str,
    result: MixedWorkloadResult[T],
) -> StashSizeSeries:
    """
    Extract stash size after each completed mixed read/write operation.

    This uses the after_eviction phase.
    """
    stash_sizes = final_mixed_stash_sizes_by_query(result)
    query_indices = list(range(1, len(stash_sizes) + 1))

    return StashSizeSeries(
        name=name,
        query_indices=query_indices,
        stash_sizes=stash_sizes,
    )


def stash_size_phase_series_from_result(
    name: str,
    result: StashSizeWorkloadResult,
) -> list[StashSizeSeries]:
    """
    Extract one stash-size series per access phase from a read-only workload.
    """
    return _stash_size_phase_series_from_samples(
        name=name,
        samples=result.samples,
    )


def stash_size_phase_series_from_mixed_result(
    name: str,
    result: MixedWorkloadResult[T],
) -> list[StashSizeSeries]:
    """
    Extract one stash-size series per access phase from a mixed workload.
    """
    return _stash_size_phase_series_from_samples(
        name=name,
        samples=result.samples,
    )


def save_stash_size_plot(
    result: StashSizeWorkloadResult,
    output_path: str | Path,
    title: str = "Path ORAM stash size over time",
) -> Path:
    """
    Save a single stash-size plot.

    This plots the stash size after each completed ORAM access.
    """
    series = stash_size_series_from_result("after eviction", result)

    return save_stash_size_comparison_plot(
        series_list=[series],
        output_path=output_path,
        title=title,
    )


def save_stash_phase_plot(
    result: StashSizeWorkloadResult,
    output_path: str | Path,
    title: str = "Path ORAM stash size by access phase",
) -> Path:
    """
    Save a plot with one line per phase for a read-only workload.
    """
    return save_stash_size_comparison_plot(
        series_list=stash_size_phase_series_from_result("read-only", result),
        output_path=output_path,
        title=title,
    )


def save_mixed_stash_phase_plot(
    result: MixedWorkloadResult[T],
    output_path: str | Path,
    title: str = "Path ORAM stash size by access phase",
) -> Path:
    """
    Save a plot with one line per phase for a mixed read/write workload.
    """
    return save_stash_size_comparison_plot(
        series_list=stash_size_phase_series_from_mixed_result("mixed", result),
        output_path=output_path,
        title=title,
    )


def save_stash_size_comparison_plot(
    series_list: Sequence[StashSizeSeries],
    output_path: str | Path,
    title: str = "Path ORAM stash size comparison",
) -> Path:
    """
    Save a comparison plot for several stash-size time series.
    """
    if len(series_list) == 0:
        raise ValueError("series_list must be nonempty")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Plotting requires matplotlib. Install it with: "
            "python3 -m pip install matplotlib"
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9, 5))

    for series in series_list:
        ax.plot(
            series.query_indices,
            series.stash_sizes,
            marker="o",
            label=series.name,
        )

    ax.set_title(title)
    ax.set_xlabel("Operation index")
    ax.set_ylabel("Stash size")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)

    if len(series_list) > 1:
        ax.legend()

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path


def _stash_size_phase_series_from_samples(
    name: str,
    samples: Sequence[_HasPhaseAndStashSize],
) -> list[StashSizeSeries]:
    """
    Build one stash-size series per access phase.
    """
    series_list: list[StashSizeSeries] = []

    for phase in _PHASE_ORDER:
        stash_sizes = [
            sample.stash_size
            for sample in samples
            if sample.phase == phase
        ]

        query_indices = list(range(1, len(stash_sizes) + 1))

        series_list.append(
            StashSizeSeries(
                name=f"{name}: {phase}",
                query_indices=query_indices,
                stash_sizes=stash_sizes,
            )
        )

    return series_list


def save_max_stash_size_boxplot(
    series_list: Sequence[MaxStashSizeSeries],
    output_path: str | Path,
    title: str = "Max stash size over random seeds",
) -> Path:
    """
    Save a boxplot comparing max stash size distributions across workloads.
    """
    if len(series_list) == 0:
        raise ValueError("series_list must be nonempty")

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError(
            "Plotting requires matplotlib. Install it with: "
            "python3 -m pip install matplotlib"
        ) from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = [series.max_stash_sizes for series in series_list]
    labels = [series.name for series in series_list]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.boxplot(data, labels=labels)
    ax.set_title(title)
    ax.set_xlabel("Workload")
    ax.set_ylabel("Max stash size during run")
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path
