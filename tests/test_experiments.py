import pytest

from oram_sim.experiments import (
    chunk_trace,
    observed_leaves_from_grouped_trace,
    run_naive_read_workload,
    run_path_oram_read_workload,
    final_stash_sizes_by_query,
    format_stash_size_report,
    run_path_oram_stash_size_workload,
    samples_for_phase,
    final_mixed_stash_sizes_by_query,
    format_mixed_workload_report,
    run_path_oram_mixed_workload,
    format_seed_sweep_report,
    run_path_oram_mixed_seed_sweep,
    run_path_oram_stash_size_seed_sweep,
)

from oram_sim.workload import Read, Write

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


def test_run_path_oram_stash_size_workload_records_all_phases() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    assert len(result.samples) == 12

    assert [sample.phase for sample in result.samples[:4]] == [
        "before_access",
        "after_path_read",
        "after_remap",
        "after_eviction",
    ]

    assert result.invariant_holds


def test_stash_size_samples_include_query_metadata() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    first = result.samples[0]

    assert first.query_index == 1
    assert first.logical_id == 2
    assert first.phase == "before_access"
    assert first.new_leaf is None


def test_after_path_read_stash_size_is_at_least_before_access() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    before_access = result.samples[0]
    after_path_read = result.samples[1]

    assert before_access.phase == "before_access"
    assert after_path_read.phase == "after_path_read"
    assert after_path_read.stash_size >= before_access.stash_size


def test_samples_for_phase() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 3],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    after_eviction = samples_for_phase(result, "after_eviction")

    assert len(after_eviction) == 2
    assert all(sample.phase == "after_eviction" for sample in after_eviction)


def test_final_stash_sizes_by_query() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 3],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    sizes = final_stash_sizes_by_query(result)

    assert len(sizes) == 2
    assert sizes == [
        sample.stash_size
        for sample in samples_for_phase(result, "after_eviction")
    ]


def test_format_stash_size_report() -> None:
    result = run_path_oram_stash_size_workload(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2],
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    report = format_stash_size_report(result)

    assert "logical workload:" in report
    assert "max stash size:" in report
    assert "after_path_read" in report
    assert "after_eviction" in report

def test_run_path_oram_mixed_workload_records_all_phases() -> None:
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

    assert len(result.samples) == 12

    assert [sample.phase for sample in result.samples[:4]] == [
        "before_access",
        "after_path_read",
        "after_remap",
        "after_eviction",
    ]

    assert result.invariant_holds


def test_run_path_oram_mixed_workload_returns_read_results() -> None:
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

    assert result.read_results == ["c", "new-b"]


def test_run_path_oram_mixed_workload_records_operations() -> None:
    result = run_path_oram_mixed_workload(
        initial_values=["a", "b"],
        operations=[
            Read(0),
            Write(1, "new-b"),
        ],
        bucket_capacity=2,
        height=1,
        seed=0,
    )

    assert result.operations == [
        "read(0)",
        "write(1, 'new-b')",
    ]


def test_run_path_oram_mixed_workload_records_observed_leaves() -> None:
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

    assert len(result.observed_leaves) == 3
    assert all(0 <= leaf < 4 for leaf in result.observed_leaves)


def test_final_mixed_stash_sizes_by_query() -> None:
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

    sizes = final_mixed_stash_sizes_by_query(result)

    assert len(sizes) == 3
    assert sizes == [
        sample.stash_size
        for sample in result.samples
        if sample.phase == "after_eviction"
    ]


def test_format_mixed_workload_report() -> None:
    result = run_path_oram_mixed_workload(
        initial_values=["a", "b"],
        operations=[
            Read(0),
            Write(1, "new-b"),
            Read(1),
        ],
        bucket_capacity=2,
        height=1,
        seed=0,
    )

    report = format_mixed_workload_report(result)

    assert "operations:" in report
    assert "read results:" in report
    assert "observed leaves:" in report
    assert "write(1, 'new-b')" in report
    assert "new-b" in report

def test_run_path_oram_stash_size_seed_sweep() -> None:
    result = run_path_oram_stash_size_seed_sweep(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        seeds=[0, 1, 2],
        workload_name="test read-only",
        bucket_capacity=2,
        height=2,
    )

    assert result.workload_name == "test read-only"
    assert result.seeds == [0, 1, 2]
    assert len(result.trials) == 3
    assert all(trial.operation_count == 3 for trial in result.trials)
    assert result.all_invariants_hold


def test_run_path_oram_stash_size_seed_sweep_rejects_empty_seeds() -> None:
    with pytest.raises(ValueError):
        run_path_oram_stash_size_seed_sweep(
            initial_values=["a", "b", "c", "d"],
            logical_pattern=[2, 2, 3],
            seeds=[],
            bucket_capacity=2,
            height=2,
        )


def test_run_path_oram_mixed_seed_sweep() -> None:
    result = run_path_oram_mixed_seed_sweep(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        seeds=[0, 1, 2],
        workload_name="test mixed",
        bucket_capacity=2,
        height=2,
    )

    assert result.workload_name == "test mixed"
    assert result.seeds == [0, 1, 2]
    assert len(result.trials) == 3
    assert all(trial.operation_count == 3 for trial in result.trials)
    assert result.all_invariants_hold


def test_format_seed_sweep_report() -> None:
    result = run_path_oram_stash_size_seed_sweep(
        initial_values=["a", "b", "c", "d"],
        logical_pattern=[2, 2, 3],
        seeds=[0, 1],
        workload_name="test report",
        bucket_capacity=2,
        height=2,
    )

    report = format_seed_sweep_report(result)

    assert "workload:" in report
    assert "number of seeds:" in report
    assert "largest observed stash size:" in report
    assert "test report" in report