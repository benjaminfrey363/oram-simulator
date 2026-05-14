from oram_sim.access_patterns import (
    hotspot_pattern,
    random_pattern,
    repeated_pattern,
    sequential_pattern,
)
from oram_sim.experiments import (
    final_stash_sizes_by_query,
    format_stash_size_report,
    run_path_oram_stash_size_workload,
)


def run_case(name: str, logical_pattern: list[int]) -> None:
    initial_values = [f"value-{i}" for i in range(16)]

    result = run_path_oram_stash_size_workload(
        initial_values=initial_values,
        logical_pattern=logical_pattern,
        bucket_capacity=2,
        height=4,
        seed=0,
    )

    print("=" * 100)
    print(name)
    print("=" * 100)
    print()
    print(format_stash_size_report(result))
    print()
    print("Final stash size after each completed query:")
    print(final_stash_sizes_by_query(result))
    print()


def main() -> None:
    run_case(
        name="Repeated workload",
        logical_pattern=repeated_pattern(block_id=3, length=12),
    )

    run_case(
        name="Sequential workload",
        logical_pattern=sequential_pattern(n_blocks=16, length=16),
    )

    run_case(
        name="Random workload",
        logical_pattern=random_pattern(n_blocks=16, length=16, seed=1),
    )

    run_case(
        name="Hotspot workload",
        logical_pattern=hotspot_pattern(
            n_blocks=16,
            hot_blocks=[1, 2, 3],
            length=16,
            hot_probability=0.8,
            seed=2,
        ),
    )


if __name__ == "__main__":
    main()