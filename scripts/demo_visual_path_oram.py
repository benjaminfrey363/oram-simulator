from oram_sim.access_patterns import repeated_pattern
from oram_sim.path_oram import PathORAM
from oram_sim.visualization import format_full_state


def print_separator() -> None:
    print()
    print("=" * 100)
    print()


def main() -> None:
    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    workload = repeated_pattern(block_id=3, length=4)

    print("Initial ORAM state")
    print_separator()
    print(format_full_state(oram, show_values=False))

    for step, logical_id in enumerate(workload, start=1):
        old_leaf = oram.position_map.get_leaf(logical_id)

        print_separator()
        print(f"Step {step}: read logical block {logical_id}")
        print()
        print("Before access:")
        print()
        print(format_full_state(
            oram,
            highlighted_leaf=old_leaf,
            show_values=False,
        ))

        value = oram.read(logical_id)
        new_leaf = oram.position_map.get_leaf(logical_id)

        print()
        print(f"Read result: {value}")
        print(f"Block {logical_id} remapped from leaf {old_leaf} to leaf {new_leaf}")

        print()
        print("After access:")
        print()
        print(format_full_state(
            oram,
            highlighted_leaf=old_leaf,
            show_values=False,
        ))

        print()
        print("Server-visible bucket-index trace so far:")
        print(oram.physical_trace())


if __name__ == "__main__":
    main()
    