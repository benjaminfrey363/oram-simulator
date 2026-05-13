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