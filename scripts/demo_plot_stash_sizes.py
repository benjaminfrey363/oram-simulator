from pathlib import Path

from oram_sim.access_patterns import (
    hotspot_pattern,
    random_pattern,
    repeated_pattern,
    sequential_pattern,
)
from oram_sim.experiments import run_path_oram_stash_size_workload
from oram_sim.plotting import (
    save_stash_size_comparison_plot,
    stash_size_series_from_result,
)


def run_workload(name: str, logical_pattern: list[int]):
    initial_values = [f"value-{i}" for i in range(32)]

    return run_path_oram_stash_size_workload(
        initial_values=initial_values,
        logical_pattern=logical_pattern,
        bucket_capacity=2,
        height=5,
        seed=0,
    )


def main() -> None:
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    workloads = {
        "repeated": repeated_pattern(block_id=3, length=40),
        "sequential": sequential_pattern(n_blocks=32, length=40),
        "random": random_pattern(n_blocks=32, length=40, seed=1),
        "hotspot": hotspot_pattern(
            n_blocks=32,
            hot_blocks=[1, 2, 3, 4],
            length=40,
            hot_probability=0.8,
            seed=2,
        ),
    }

    series_list = []

    for name, logical_pattern in workloads.items():
        result = run_workload(name, logical_pattern)

        print(f"{name}:")
        print(f"  max stash size:   {result.max_stash_size}")
        print(f"  final stash size: {result.final_stash_size}")
        print(f"  invariant holds:  {result.invariant_holds}")
        print()

        series_list.append(stash_size_series_from_result(name, result))

    output_path = save_stash_size_comparison_plot(
        series_list=series_list,
        output_path=output_dir / "stash-size-comparison.png",
        title="Path ORAM stash size after each access",
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
    