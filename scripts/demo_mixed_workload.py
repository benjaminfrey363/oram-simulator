from oram_sim.experiments import (
    final_mixed_stash_sizes_by_query,
    format_mixed_workload_report,
    run_path_oram_mixed_workload,
)
from oram_sim.workload import Read, Write, format_workload


def main() -> None:
    initial_values = [f"value-{i}" for i in range(8)]

    workload = [
        Read(3),
        Read(3),
        Write(3, "updated-3"),
        Read(3),
        Write(1, "updated-1"),
        Read(1),
        Read(3),
    ]

    result = run_path_oram_mixed_workload(
        initial_values=initial_values,
        operations=workload,
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    print("Mixed read/write workload:")
    print(format_workload(workload))
    print()

    print(format_mixed_workload_report(result))
    print()

    print("Final stash size after each completed operation:")
    print(final_mixed_stash_sizes_by_query(result))
    print()

    print("Read results:")
    print(result.read_results)
    print()

    print("Observed leaves:")
    print(result.observed_leaves)


if __name__ == "__main__":
    main()