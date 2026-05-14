from pathlib import Path

from oram_sim.experiments import run_path_oram_mixed_workload
from oram_sim.plotting import save_mixed_stash_phase_plot
from oram_sim.workload import Read, Write


def main() -> None:
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    initial_values = [f"value-{i}" for i in range(16)]

    workload = [
        Read(3),
        Read(3),
        Write(3, "updated-3-a"),
        Read(3),
        Write(7, "updated-7-a"),
        Read(7),
        Write(3, "updated-3-b"),
        Read(3),
        Write(1, "updated-1-a"),
        Read(1),
    ]

    result = run_path_oram_mixed_workload(
        initial_values=initial_values,
        operations=workload,
        bucket_capacity=2,
        height=4,
        seed=0,
    )

    print("Max stash size across all phases:")
    print(result.max_stash_size)
    print()

    print("Final stash size after completed workload:")
    print(result.final_stash_size)
    print()

    output_path = save_mixed_stash_phase_plot(
        result=result,
        output_path=output_dir / "mixed-stash-size-by-phase.png",
        title="Path ORAM stash size by access phase",
    )

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()