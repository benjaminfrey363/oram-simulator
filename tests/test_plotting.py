import pytest

from oram_sim.access_patterns import repeated_pattern
from oram_sim.experiments import run_path_oram_stash_size_workload
from oram_sim.plotting import (
    StashSizeSeries,
    save_stash_size_comparison_plot,
    stash_size_series_from_result,
)


def test_stash_size_series_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        StashSizeSeries(
            name="bad",
            query_indices=[1, 2],
            stash_sizes=[0],
        )


def test_stash_size_series_from_result() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series = stash_size_series_from_result("repeated", result)

    assert series.name == "repeated"
    assert series.query_indices == [1, 2, 3]
    assert len(series.stash_sizes) == 3


def test_save_stash_size_comparison_plot_rejects_empty_series(tmp_path) -> None:
    with pytest.raises(ValueError):
        save_stash_size_comparison_plot(
            series_list=[],
            output_path=tmp_path / "stash.png",
        )


def test_save_stash_size_comparison_plot_writes_file(tmp_path) -> None:
    pytest.importorskip("matplotlib")

    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=repeated_pattern(block_id=2, length=3),
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series = stash_size_series_from_result("repeated", result)

    output_path = save_stash_size_comparison_plot(
        series_list=[series],
        output_path=tmp_path / "stash.png",
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"
    