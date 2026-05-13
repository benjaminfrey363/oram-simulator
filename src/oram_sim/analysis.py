from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

from oram_sim.trace import AccessTrace


@dataclass(frozen=True)
class TraceSummary:
    """
    Summary statistics for a server-visible physical access trace.
    """

    length: int
    unique_addresses: int
    most_frequent_address: int | None
    most_frequent_count: int
    repeat_count: int
    repeat_rate: float
    address_frequencies: dict[int, int]
    transition_frequencies: dict[tuple[int, int], int]


def summarize_physical_trace(physical_addresses: Sequence[int]) -> TraceSummary:
    """
    Compute simple leakage statistics for a physical access trace.

    The physical trace represents what the server sees.
    For naive storage, this is exactly the logical access pattern.
    For ORAM, this should ideally reveal much less.
    """
    length = len(physical_addresses)

    address_counter = Counter(physical_addresses)
    transition_counter = Counter(
        (physical_addresses[i], physical_addresses[i + 1])
        for i in range(length - 1)
    )

    if address_counter:
        most_frequent_address, most_frequent_count = address_counter.most_common(1)[0]
    else:
        most_frequent_address = None
        most_frequent_count = 0

    repeat_count = sum(
        1
        for i in range(length - 1)
        if physical_addresses[i] == physical_addresses[i + 1]
    )

    repeat_rate = repeat_count / (length - 1) if length >= 2 else 0.0

    return TraceSummary(
        length=length,
        unique_addresses=len(address_counter),
        most_frequent_address=most_frequent_address,
        most_frequent_count=most_frequent_count,
        repeat_count=repeat_count,
        repeat_rate=repeat_rate,
        address_frequencies=dict(address_counter),
        transition_frequencies=dict(transition_counter),
    )


def summarize_access_trace(trace: AccessTrace) -> TraceSummary:
    """
    Convenience wrapper for summarizing an AccessTrace object.
    """
    return summarize_physical_trace(trace.physical_addresses())


def format_summary(summary: TraceSummary) -> str:
    """
    Format a trace summary for demos.
    """
    if summary.length == 0:
        return "empty trace"

    most_frequent = (
        f"{summary.most_frequent_address} "
        f"({summary.most_frequent_count}/{summary.length} accesses)"
    )

    return "\n".join(
        [
            f"length:                  {summary.length}",
            f"unique addresses:        {summary.unique_addresses}",
            f"most frequent address:   {most_frequent}",
            f"consecutive repeats:     {summary.repeat_count}",
            f"repeat rate:             {summary.repeat_rate:.2%}",
        ]
    )

@dataclass(frozen=True)
class AdjacentRepeatComparison:
    """
    Compare adjacent-repeat structure between a logical pattern and an observed trace.

    We are not asking whether the numbers are equal.

    For Path ORAM, comparing logical block id 3 to observed leaf 3 is not
    meaningful. Instead, we ask whether repetitions are preserved:

        logical[i] == logical[i - 1]
        observed[i] == observed[i - 1]
    """

    length: int
    transition_count: int

    logical_repeat_count: int
    observed_repeat_count: int

    agreement_count: int
    agreement_rate: float

    logical_repeats_visible_count: int
    logical_repeats_visible_rate: float

    observed_repeats_without_logical_repeat_count: int
    observed_repeats_without_logical_repeat_rate: float


def adjacent_repeat_flags(sequence: Sequence[object]) -> list[bool]:
    """
    Return the adjacent-repeat pattern of a sequence.

    Example:
        [3, 3, 2, 2, 5]
    gives:
        [True, False, True, False]
    """
    return [
        sequence[i] == sequence[i - 1]
        for i in range(1, len(sequence))
    ]


def compare_adjacent_repeats(
    logical_sequence: Sequence[object],
    observed_sequence: Sequence[object],
) -> AdjacentRepeatComparison:
    """
    Compare whether adjacent repetitions in the logical workload remain visible
    in the observed trace.

    This is useful for comparing:

        logical workload vs naive physical addresses
        logical workload vs Path ORAM observed leaves

    The sequences must have the same length. For Path ORAM, use the observed
    leaf per logical access, not the full bucket trace.
    """
    if len(logical_sequence) != len(observed_sequence):
        raise ValueError(
            "logical_sequence and observed_sequence must have the same length"
        )

    length = len(logical_sequence)
    transition_count = max(0, length - 1)

    logical_flags = adjacent_repeat_flags(logical_sequence)
    observed_flags = adjacent_repeat_flags(observed_sequence)

    logical_repeat_count = sum(logical_flags)
    observed_repeat_count = sum(observed_flags)

    agreement_count = sum(
        logical_repeat == observed_repeat
        for logical_repeat, observed_repeat in zip(logical_flags, observed_flags)
    )

    agreement_rate = (
        agreement_count / transition_count
        if transition_count > 0
        else 0.0
    )

    logical_repeats_visible_count = sum(
        logical_repeat and observed_repeat
        for logical_repeat, observed_repeat in zip(logical_flags, observed_flags)
    )

    logical_repeats_visible_rate = (
        logical_repeats_visible_count / logical_repeat_count
        if logical_repeat_count > 0
        else 0.0
    )

    logical_change_count = transition_count - logical_repeat_count

    observed_repeats_without_logical_repeat_count = sum(
        (not logical_repeat) and observed_repeat
        for logical_repeat, observed_repeat in zip(logical_flags, observed_flags)
    )

    observed_repeats_without_logical_repeat_rate = (
        observed_repeats_without_logical_repeat_count / logical_change_count
        if logical_change_count > 0
        else 0.0
    )

    return AdjacentRepeatComparison(
        length=length,
        transition_count=transition_count,
        logical_repeat_count=logical_repeat_count,
        observed_repeat_count=observed_repeat_count,
        agreement_count=agreement_count,
        agreement_rate=agreement_rate,
        logical_repeats_visible_count=logical_repeats_visible_count,
        logical_repeats_visible_rate=logical_repeats_visible_rate,
        observed_repeats_without_logical_repeat_count=(
            observed_repeats_without_logical_repeat_count
        ),
        observed_repeats_without_logical_repeat_rate=(
            observed_repeats_without_logical_repeat_rate
        ),
    )


def format_repeat_comparison(comparison: AdjacentRepeatComparison) -> str:
    """
    Format adjacent-repeat comparison results for demos.
    """
    return "\n".join(
        [
            f"length:                                {comparison.length}",
            f"adjacent transitions:                  {comparison.transition_count}",
            f"logical adjacent repeats:              {comparison.logical_repeat_count}",
            f"observed adjacent repeats:             {comparison.observed_repeat_count}",
            (
                "repeat/change agreement:              "
                f"{comparison.agreement_count}/{comparison.transition_count} "
                f"({comparison.agreement_rate:.2%})"
            ),
            (
                "logical repeats still visible:         "
                f"{comparison.logical_repeats_visible_count}/"
                f"{comparison.logical_repeat_count} "
                f"({comparison.logical_repeats_visible_rate:.2%})"
            ),
            (
                "observed repeats without logical repeat: "
                f"{comparison.observed_repeats_without_logical_repeat_count} "
                f"({comparison.observed_repeats_without_logical_repeat_rate:.2%})"
            ),
        ]
    )
