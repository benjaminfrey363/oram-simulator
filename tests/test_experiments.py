import pytest

from oram_sim.experiments import (
    chunk_trace,
    observed_leaves_from_grouped_trace,
    run_naive_read_workload,
    run_path_oram_read_workload,
)


def test_chunk_trace() -> None:
    assert chunk_trace([1, 2, 3, 4, 5, 6], chunk_size=2) == [
        [1, 2],
        [3, 4],
        [5, 6],
    ]


def test_chunk_trace_rejects_bad_chunk_size() -> None:
    with pytest.raises(ValueError):
        chunk_trace([1, 2, 3], chunk_size=0)


def test_chunk_trace_rejects_uneven_trace() -> None:
    with pytest.raises(ValueError):
        chunk_trace([1, 2, 3], chunk_size=2)


def test_observed_leaves_from_grouped_trace_height_two() -> None:
    grouped_trace = [
        [1, 2, 4, 1, 2, 4],
        [1, 2, 5, 1, 2, 5],
        [1, 3, 7, 1, 3, 7],
    ]

    assert observed_leaves_from_grouped_trace(
        grouped_trace=grouped_trace,
        height=2,
    ) == [0, 1, 3]


def test_observed_leaves_rejects_mismatched_read_write_path() -> None:
    grouped_trace = [
        [1, 2, 4, 1, 2, 5],
    ]

    with pytest.raises(ValueError):
        observed_leaves_from_grouped_trace(
            grouped_trace=grouped_trace,
            height=2,
        )


def test_observed_leaves_rejects_bad_group_size() -> None:
    grouped_trace = [
        [1, 2, 4],
    ]

    with pytest.raises(ValueError):
        observed_leaves_from_grouped_trace(
            grouped_trace=grouped_trace,
            height=2,
        )


def test_run_naive_read_workload() -> None:
    result = run_naive_read_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
    )

    assert result.logical_pattern == [2, 2, 3]
    assert result.physical_trace == [2, 2, 3]
    assert result.summary.length == 3
    assert result.summary.repeat_count == 1


def test_run_path_oram_read_workload() -> None:
    result = run_path_oram_read_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        bucket_capacity=2,
        seed=0,
    )

    # Four blocks gives default height 2.
    # One Path ORAM logical access reads a path of length 3
    # and writes a path of length 3.
    assert result.physical_accesses_per_logical_access == 6

    assert result.logical_pattern == [2, 2, 3]
    assert len(result.grouped_trace) == 3
    assert all(len(group) == 6 for group in result.grouped_trace)

    assert len(result.observed_leaves) == 3
    assert all(0 <= leaf < 4 for leaf in result.observed_leaves)

    assert result.summary.length == 18
    assert result.invariant_holds
    