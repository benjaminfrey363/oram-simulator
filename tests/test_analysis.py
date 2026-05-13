from oram_sim.analysis import summarize_access_trace, summarize_physical_trace
from oram_sim.storage import NaiveStorage


def test_empty_trace_summary() -> None:
    summary = summarize_physical_trace([])

    assert summary.length == 0
    assert summary.unique_addresses == 0
    assert summary.most_frequent_address is None
    assert summary.most_frequent_count == 0
    assert summary.repeat_count == 0
    assert summary.repeat_rate == 0.0
    assert summary.address_frequencies == {}
    assert summary.transition_frequencies == {}


def test_repeated_trace_summary() -> None:
    summary = summarize_physical_trace([3, 3, 3, 3])

    assert summary.length == 4
    assert summary.unique_addresses == 1
    assert summary.most_frequent_address == 3
    assert summary.most_frequent_count == 4
    assert summary.repeat_count == 3
    assert summary.repeat_rate == 1.0
    assert summary.address_frequencies == {3: 4}
    assert summary.transition_frequencies == {(3, 3): 3}


def test_mixed_trace_summary() -> None:
    summary = summarize_physical_trace([1, 2, 1, 1, 3])

    assert summary.length == 5
    assert summary.unique_addresses == 3
    assert summary.most_frequent_address == 1
    assert summary.most_frequent_count == 3
    assert summary.repeat_count == 1
    assert summary.repeat_rate == 0.25
    assert summary.address_frequencies == {
        1: 3,
        2: 1,
        3: 1,
    }
    assert summary.transition_frequencies == {
        (1, 2): 1,
        (2, 1): 1,
        (1, 1): 1,
        (1, 3): 1,
    }


def test_summarize_access_trace_from_naive_storage() -> None:
    storage = NaiveStorage(["a", "b", "c", "d"])

    storage.read(2)
    storage.read(2)
    storage.read(3)

    summary = summarize_access_trace(storage.trace)

    assert summary.length == 3
    assert summary.unique_addresses == 2
    assert summary.most_frequent_address == 2
    assert summary.most_frequent_count == 2
    assert summary.repeat_count == 1
    