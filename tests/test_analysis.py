import pytest

from oram_sim.analysis import summarize_access_trace, summarize_physical_trace
from oram_sim.storage import NaiveStorage

from oram_sim.analysis import (
    adjacent_repeat_flags,
    compare_adjacent_repeats,
    format_repeat_comparison,
)

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



def test_adjacent_repeat_flags() -> None:
    assert adjacent_repeat_flags([3, 3, 2, 2, 2, 1]) == [
        True,
        False,
        True,
        True,
        False,
    ]


def test_compare_adjacent_repeats_identical_naive_trace() -> None:
    comparison = compare_adjacent_repeats(
        logical_sequence=[3, 3, 3, 3],
        observed_sequence=[3, 3, 3, 3],
    )

    assert comparison.length == 4
    assert comparison.transition_count == 3

    assert comparison.logical_repeat_count == 3
    assert comparison.observed_repeat_count == 3

    assert comparison.agreement_count == 3
    assert comparison.agreement_rate == 1.0

    assert comparison.logical_repeats_visible_count == 3
    assert comparison.logical_repeats_visible_rate == 1.0


def test_compare_adjacent_repeats_oram_like_trace() -> None:
    comparison = compare_adjacent_repeats(
        logical_sequence=[3, 3, 3, 3],
        observed_sequence=[6, 1, 7, 4],
    )

    assert comparison.length == 4
    assert comparison.transition_count == 3

    assert comparison.logical_repeat_count == 3
    assert comparison.observed_repeat_count == 0

    assert comparison.agreement_count == 0
    assert comparison.agreement_rate == 0.0

    assert comparison.logical_repeats_visible_count == 0
    assert comparison.logical_repeats_visible_rate == 0.0


def test_compare_adjacent_repeats_mixed_case() -> None:
    comparison = compare_adjacent_repeats(
        logical_sequence=[1, 1, 2, 3, 3],
        observed_sequence=[5, 5, 5, 1, 2],
    )

    # logical repeat flags:
    #   [True, False, False, True]
    #
    # observed repeat flags:
    #   [True, True, False, False]

    assert comparison.transition_count == 4

    assert comparison.logical_repeat_count == 2
    assert comparison.observed_repeat_count == 2

    assert comparison.agreement_count == 2
    assert comparison.agreement_rate == 0.5

    assert comparison.logical_repeats_visible_count == 1
    assert comparison.logical_repeats_visible_rate == 0.5

    assert comparison.observed_repeats_without_logical_repeat_count == 1
    assert comparison.observed_repeats_without_logical_repeat_rate == 0.5


def test_compare_adjacent_repeats_rejects_length_mismatch() -> None:
    with pytest.raises(ValueError):
        compare_adjacent_repeats(
            logical_sequence=[1, 2, 3],
            observed_sequence=[1, 2],
        )


def test_format_repeat_comparison() -> None:
    comparison = compare_adjacent_repeats(
        logical_sequence=[3, 3, 3],
        observed_sequence=[5, 1, 2],
    )

    formatted = format_repeat_comparison(comparison)

    assert "logical adjacent repeats" in formatted
    assert "logical repeats still visible" in formatted
