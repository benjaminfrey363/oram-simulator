from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from oram_sim.experiments import (
    StashSizeWorkloadResult,
    final_stash_sizes_by_query,
)


@dataclass(frozen=True)
class StashSizeSeries:
    """
    A named stash-size time series.

    query_indices:
        One-based query indices.

    stash_sizes:
        Stash size after each completed ORAM access.
    """

    name: str
    query_indices: list[int]
    stash_sizes: list[int]

    def __post_init__(self) -> None:
        if len(self.query_indices) != len(self.stash_sizes):
            raise ValueError("query_indices and stash_sizes must have the same length")


def stash_size_series_from_result(
    name: str,
    result: StashSizeWorkloadResult,
) -> StashSizeSeries:
    """
    Extract stash size after each completed query.
    """
    stash_sizes = final_stash_sizes_by_query(result)
    query_indices = list(range(1, len(stash_sizes) + 1))

    return StashSizeSeries(
        name=name,
        query_indices=query_indices,
        stash_sizes=stash_sizes,
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
    series = stash_size_series_from_result("stash size", result)

    return save_stash_size_comparison_plot(
        series_list=[series],
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
            'python3 -m pip install matplotlib'
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
    ax.set_xlabel("Query index")
    ax.set_ylabel("Stash size after eviction")
    ax.set_ylim(bottom=0)
    ax.grid(True, alpha=0.3)

    if len(series_list) > 1:
        ax.legend()

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path
