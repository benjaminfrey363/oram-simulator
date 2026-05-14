from pathlib import Path

from oram_sim.experiments import run_path_oram_mixed_workload
from oram_sim.plotting import (
    save_stash_size_comparison_plot,
    stash_size_series_from_mixed_result,
)
from oram_sim.workload import Read, Write


def main() -> None:
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    initial_values = [f"value-{i}" for i in range(16)]

    mostly_reads = [
        Read(3),
        Read(3),
        Read(7),
        Read(3),
        Read(1),
        Read(7),
        Read(3),
        Read(12),
        Read(3),
        Read(7),
    ]

    alternating_reads_writes = [
        Read(3),
        Write(3, "updated-3-a"),
        Read(3),
        Write(7, "updated-7-a"),
        Read(7),
        Write(3, "updated-3-b"),
        Read(3),
        Write(1, "updated-1-a"),
        Read(1),
        Read(3),
    ]

    write_heavy = [
        Write(0, "w0"),
        Write(1, "w1"),
        Write(2, "w2"),
        Write(3, "w3"),
        Write(4, "w4"),
        Read(0),
        Read(1),
        Read(2),
        Read(3),
        Read(4),
    ]

    workloads = {
        "mostly reads": mostly_reads,
        "alternating reads/writes": alternating_reads_writes,
        "write heavy": write_heavy,
    }

    series_list = []

    for name, operations in workloads.items():
        result = run_path_oram_mixed_workload(
            initial_values=initial_values,
            operations=operations,
            bucket_capacity=2,
            height=4,
            seed=0,
        )

        print(f"{name}:")
        print(f"  read results:      {result.read_results}")
        print(f"  observed leaves:   {result.observed_leaves}")
        print(f"  max stash size:    {result.max_stash_size}")
        print(f"  final stash size:  {result.final_stash_size}")
        print(f"  invariant holds:   {result.invariant_holds}")
        print()

        series_list.append(
            stash_size_series_from_mixed_result(name, result)
        )

    output_path = save_stash_size_comparison_plot(
        series_list=series_list,
        output_path=output_dir / "mixed-stash-size-comparison.png",
        title="Path ORAM stash size for mixed read/write workloads",
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()