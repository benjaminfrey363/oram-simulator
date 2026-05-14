import pytest

from oram_sim.access_patterns import repeated_pattern
from oram_sim.experiments import (
    run_path_oram_mixed_workload,
    run_path_oram_stash_size_seed_sweep,
    run_path_oram_stash_size_workload,
)
from oram_sim.plotting import (
    StashSizeSeries,
    save_stash_size_comparison_plot,
    stash_size_series_from_mixed_result,
    stash_size_series_from_result,
    save_mixed_stash_phase_plot,
    save_stash_phase_plot,
    stash_size_phase_series_from_mixed_result,
    stash_size_phase_series_from_result,
    MaxStashSizeSeries,
    max_stash_size_series_from_seed_sweep,
    save_max_stash_size_boxplot,
)
from oram_sim.workload import Read, Write


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


def test_stash_size_series_from_mixed_result() -> None:
    result = run_path_oram_mixed_workload(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series = stash_size_series_from_mixed_result("mixed", result)

    assert series.name == "mixed"
    assert series.query_indices == [1, 2, 3]
    assert len(series.stash_sizes) == 3


def test_save_stash_size_comparison_plot_accepts_mixed_series(tmp_path) -> None:
    pytest.importorskip("matplotlib")

    result = run_path_oram_mixed_workload(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series = stash_size_series_from_mixed_result("mixed", result)

    output_path = save_stash_size_comparison_plot(
        series_list=[series],
        output_path=tmp_path / "mixed-stash.png",
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"

def test_stash_size_phase_series_from_result() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 3],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series_list = stash_size_phase_series_from_result("read-only", result)

    assert len(series_list) == 4
    assert [series.name for series in series_list] == [
        "read-only: before_access",
        "read-only: after_path_read",
        "read-only: after_remap",
        "read-only: after_eviction",
    ]

    assert all(series.query_indices == [1, 2] for series in series_list)
    assert all(len(series.stash_sizes) == 2 for series in series_list)


def test_stash_size_phase_series_from_mixed_result() -> None:
    result = run_path_oram_mixed_workload(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series_list = stash_size_phase_series_from_mixed_result("mixed", result)

    assert len(series_list) == 4
    assert all(series.query_indices == [1, 2, 3] for series in series_list)
    assert all(len(series.stash_sizes) == 3 for series in series_list)


def test_after_path_read_series_can_show_nonzero_stash() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    series_list = stash_size_phase_series_from_result("read-only", result)

    after_path_read = next(
        series
        for series in series_list
        if series.name == "read-only: after_path_read"
    )

    assert len(after_path_read.stash_sizes) == 1
    assert after_path_read.stash_sizes[0] > 0


def test_save_stash_phase_plot_writes_file(tmp_path) -> None:
    pytest.importorskip("matplotlib")

    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=repeated_pattern(block_id=2, length=3),
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    output_path = save_stash_phase_plot(
        result=result,
        output_path=tmp_path / "phase-stash.png",
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_save_mixed_stash_phase_plot_writes_file(tmp_path) -> None:
    pytest.importorskip("matplotlib")

    result = run_path_oram_mixed_workload(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    output_path = save_mixed_stash_phase_plot(
        result=result,
        output_path=tmp_path / "mixed-phase-stash.png",
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_max_stash_size_series_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        MaxStashSizeSeries(
            name="bad",
            seeds=[0, 1],
            max_stash_sizes=[0],
        )


def test_max_stash_size_series_from_seed_sweep() -> None:
    result = run_path_oram_stash_size_seed_sweep(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        seeds=[0, 1, 2],
        workload_name="seed sweep",
        bucket_capacity=2,
        height=2,
    )

    series = max_stash_size_series_from_seed_sweep(result)

    assert series.name == "seed sweep"
    assert series.seeds == [0, 1, 2]
    assert len(series.max_stash_sizes) == 3


def test_save_max_stash_size_boxplot_rejects_empty_series(tmp_path) -> None:
    with pytest.raises(ValueError):
        save_max_stash_size_boxplot(
            series_list=[],
            output_path=tmp_path / "boxplot.png",
        )


def test_save_max_stash_size_boxplot_writes_file(tmp_path) -> None:
    pytest.importorskip("matplotlib")

    result = run_path_oram_stash_size_seed_sweep(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        seeds=[0, 1, 2],
        workload_name="seed sweep",
        bucket_capacity=2,
        height=2,
    )

    series = max_stash_size_series_from_seed_sweep(result)

    output_path = save_max_stash_size_boxplot(
        series_list=[series],
        output_path=tmp_path / "boxplot.png",
    )

    assert output_path.exists()
    assert output_path.suffix == ".png"
