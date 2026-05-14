from pathlib import Path

from oram_sim.access_patterns import repeated_pattern
from oram_sim.graphviz_renderer import (
    access_snapshot_to_dot,
    render_access_snapshot,
    write_dot_file,
)
from oram_sim.path_oram import PathORAM


def phase_filename(phase: str) -> str:
    return phase.replace("_", "-")


def main() -> None:
    output_dir = Path("snapshots")
    output_dir.mkdir(exist_ok=True)

    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    workload = repeated_pattern(block_id=3, length=3)

    for query_index, logical_id in enumerate(workload, start=1):
        for snapshot in oram.read_snapshots(logical_id):
            stem = f"query-{query_index:03d}-{phase_filename(snapshot.phase)}"

            dot_path = output_dir / f"{stem}.dot"
            svg_path = output_dir / f"{stem}.svg"

            dot = access_snapshot_to_dot(
                snapshot,
                show_values=False,
                show_dummy_ids=False,
            )

            write_dot_file(dot, dot_path)

            try:
                rendered = render_access_snapshot(
                    snapshot,
                    svg_path,
                    show_values=False,
                    show_dummy_ids=False,
                )
                print(f"Wrote {dot_path} and {rendered}")
            except RuntimeError as exc:
                print(f"Wrote {dot_path}")
                print(f"Could not render SVG: {exc}")

    print()
    print(f"Done. Output directory: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
    