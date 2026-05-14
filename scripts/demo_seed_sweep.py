from pathlib import Path

from oram_sim.access_patterns import (
    hotspot_pattern,
    random_pattern,
    repeated_pattern,
    sequential_pattern,
)
from oram_sim.experiments import (
    format_seed_sweep_report,
    run_path_oram_stash_size_seed_sweep,
)
from oram_sim.plotting import (
    max_stash_size_series_from_seed_sweep,
    save_max_stash_size_boxplot,
)


def main() -> None:
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    initial_values = [f"value-{i}" for i in range(32)]
    seeds = list(range(50))

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
        result = run_path_oram_stash_size_seed_sweep(
            initial_values=initial_values,
            logical_pattern=logical_pattern,
            seeds=seeds,
            workload_name=name,
            bucket_capacity=2,
            height=5,
        )

        print("=" * 80)
        print(format_seed_sweep_report(result))
        print()

        series_list.append(max_stash_size_series_from_seed_sweep(result))

    output_path = save_max_stash_size_boxplot(
        series_list=series_list,
        output_path=output_dir / "max-stash-size-seed-sweep.png",
        title="Max stash size over 50 random seeds",
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
    