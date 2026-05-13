from oram_sim.analysis import format_summary, summarize_physical_trace
from oram_sim.path_oram import PathORAM


def print_position_map(oram: PathORAM[str]) -> None:
    for logical_id, leaf in oram.position_entries().items():
        print(f"  block {logical_id} -> leaf {leaf}")


def print_server_snapshot(oram: PathORAM[str]) -> None:
    snapshot = oram.server_snapshot()

    if not snapshot:
        print("  empty")
        return

    for bucket_index, blocks in snapshot.items():
        pretty_blocks = [
            f"block {block.logical_id} (leaf {block.leaf}, value={block.value})"
            for block in blocks
        ]
        print(f"  bucket {bucket_index}: {pretty_blocks}")


def print_stash(oram: PathORAM[str]) -> None:
    blocks = oram.stash_blocks()

    if not blocks:
        print("  empty")
        return

    for block in blocks:
        print(
            f"  block {block.logical_id}: "
            f"leaf={block.leaf}, value={block.value}"
        )


def main() -> None:
    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    logical_id = 2

    print("Initial private position map:")
    print_position_map(oram)
    print()

    old_leaf = oram.position_map.get_leaf(logical_id)
    old_path = oram.server.path_bucket_indices(old_leaf)

    print(f"About to read logical block {logical_id}.")
    print(f"Private old leaf: {old_leaf}")
    print(f"Server-visible path to old leaf: {old_path}")
    print()

    value = oram.read(logical_id)

    print(f"Read result: {value}")
    print()

    print("Updated private position map:")
    print_position_map(oram)
    print()

    print("Server snapshot after access:")
    print_server_snapshot(oram)
    print()

    print("Private stash after access:")
    print_stash(oram)
    print()

    print("Server-visible physical trace:")
    print(oram.physical_trace())
    print()
    print(format_summary(summarize_physical_trace(oram.physical_trace())))
    print()

    print(f"Invariant holds? {oram.check_invariant()}")


if __name__ == "__main__":
    main()
    