from oram_sim.position_map import PositionMap


def print_position_map(position_map: PositionMap) -> None:
    for logical_id, leaf in position_map.entries().items():
        print(f"  block {logical_id} -> leaf {leaf}")


def main() -> None:
    position_map = PositionMap(
        n_blocks=5,
        n_leaves=8,
        seed=0,
    )

    print("Initial private position map:")
    print_position_map(position_map)
    print()

    logical_id = 2
    old_leaf = position_map.get_leaf(logical_id)
    new_leaf = position_map.remap(logical_id)

    print(f"Accessing logical block {logical_id}:")
    print(f"  old assigned leaf: {old_leaf}")
    print(f"  new assigned leaf: {new_leaf}")
    print()

    print("Updated private position map:")
    print_position_map(position_map)


if __name__ == "__main__":
    main()
    