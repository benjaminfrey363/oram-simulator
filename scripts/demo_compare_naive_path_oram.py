from oram_sim.access_patterns import hotspot_pattern, repeated_pattern
from oram_sim.analysis import format_summary
from oram_sim.experiments import (
    PathORAMWorkloadResult,
    run_naive_read_workload,
    run_path_oram_read_workload,
)


def print_path_oram_grouped_trace(result: PathORAMWorkloadResult) -> None:
    half = result.physical_accesses_per_logical_access // 2

    for index, logical_id in enumerate(result.logical_pattern):
        group = result.grouped_trace[index]
        read_path = group[:half]
        write_path = group[half:]

        print(f"  logical access {index}: read block {logical_id}")
        print(f"    server sees read path:  {read_path}")
        print(f"    server sees write path: {write_path}")


def compare_workload(name: str, logical_pattern: list[int]) -> None:
    initial_values = [f"value-{i}" for i in range(8)]

    naive = run_naive_read_workload(
        initial_values=initial_values,
        logical_pattern=logical_pattern,
    )

    path_oram = run_path_oram_read_workload(
        initial_values=initial_values,
        logical_pattern=logical_pattern,
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    print("=" * 72)
    print(name)
    print("=" * 72)
    print()

    print("Logical workload:")
    print(logical_pattern)
    print()

    print("NaiveStorage server-visible trace:")
    print(naive.physical_trace)
    print()
    print(format_summary(naive.summary))
    print()

    print("PathORAM server-visible trace, grouped by logical access:")
    print_path_oram_grouped_trace(path_oram)
    print()
    print(format_summary(path_oram.summary))
    print()

    print(f"Path ORAM invariant holds? {path_oram.invariant_holds}")
    print()


def main() -> None:
    compare_workload(
        name="Repeated access workload",
        logical_pattern=repeated_pattern(block_id=3, length=8),
    )

    compare_workload(
        name="Hotspot workload",
        logical_pattern=hotspot_pattern(
            n_blocks=8,
            hot_blocks=[1, 2],
            length=12,
            hot_probability=0.8,
            seed=1,
        ),
    )


if __name__ == "__main__":
    main()
    