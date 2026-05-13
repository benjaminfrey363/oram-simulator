from oram_sim.access_patterns import (
    hotspot_pattern,
    repeated_pattern,
    sequential_pattern,
)
from oram_sim.analysis import format_summary, summarize_access_trace
from oram_sim.storage import NaiveStorage


def run_pattern(name: str, pattern: list[int]) -> None:
    storage = NaiveStorage([f"block-{i}" for i in range(10)])

    for logical_id in pattern:
        storage.read(logical_id)

    summary = summarize_access_trace(storage.trace)

    print(f"{name}:")
    print(f"  logical pattern:  {pattern}")
    print(f"  physical trace:   {storage.trace.physical_addresses()}")
    print()
    print(format_summary(summary))
    print()


def main() -> None:
    run_pattern(
        "sequential",
        sequential_pattern(n_blocks=10, length=15),
    )

    run_pattern(
        "repeated",
        repeated_pattern(block_id=3, length=15),
    )

    run_pattern(
        "hotspot",
        hotspot_pattern(
            n_blocks=10,
            hot_blocks=[1, 2],
            length=15,
            hot_probability=0.8,
            seed=0,
        ),
    )


if __name__ == "__main__":
    main()