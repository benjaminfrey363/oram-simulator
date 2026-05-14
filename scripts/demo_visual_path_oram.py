from oram_sim.access_patterns import repeated_pattern
from oram_sim.path_oram import PathORAM
from oram_sim.visualization import (
    format_access_step,
    format_full_state,
)


def print_separator() -> None:
    print()
    print("=" * 100)
    print()


def print_phase_header(title: str) -> None:
    print()
    print("-" * 100)
    print(title)
    print("-" * 100)
    print()


def main() -> None:
    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    workload = repeated_pattern(block_id=3, length=3)

    print("Initial ORAM state")
    print_separator()
    print(format_full_state(oram, show_values=False))

    for query_index, logical_id in enumerate(workload, start=1):
        print_separator()
        print(f"Query {query_index}: read logical block {logical_id}")

        last_step = None

        for step in oram.read_steps(logical_id):
            last_step = step

            print_phase_header(format_access_step(step))

            print(
                format_full_state(
                    oram,
                    highlighted_leaf=step.old_leaf,
                    show_values=False,
                )
            )

            if step.phase == "after_path_read":
                print()
                print(
                    "Note: this is an intermediate debugging state. "
                    "The old path has been copied into the private stash, "
                    "but the server path has not yet been rewritten."
                )

            if step.phase == "after_remap":
                print()
                print(
                    "Note: the target block in the stash now has its new assigned leaf. "
                    "The write-back phase has not happened yet."
                )

        print()
        print(f"Query {query_index} complete.")
        if last_step is not None:
            print(f"Read value: {last_step.read_value}")


if __name__ == "__main__":
    main()