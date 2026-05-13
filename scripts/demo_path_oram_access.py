from oram_sim.analysis import format_summary, summarize_physical_trace
from oram_sim.block import Block, DummyBlock
from oram_sim.path_oram import PathORAM


def format_visible_block(block: Block[str] | DummyBlock) -> str:
    """
    Format a block for demos.

    In a real ORAM, the server would not be able to distinguish real blocks
    from dummy blocks. Here we print them explicitly because this is a simulator.
    """
    if isinstance(block, DummyBlock):
        return f"dummy-{block.dummy_id}"

    return f"real-{block.logical_id}(leaf={block.leaf}, value={block.value})"


def print_position_map(oram: PathORAM[str]) -> None:
    for logical_id, leaf in oram.position_entries().items():
        print(f"  block {logical_id} -> leaf {leaf}")


def print_real_server_snapshot(oram: PathORAM[str]) -> None:
    snapshot = oram.server_snapshot()

    if not snapshot:
        print("  empty")
        return

    for bucket_index, blocks in snapshot.items():
        pretty_blocks = [
            f"block {block.logical_id} (leaf={block.leaf}, value={block.value})"
            for block in blocks
        ]
        print(f"  bucket {bucket_index}: {pretty_blocks}")


def print_padded_path_view(oram: PathORAM[str], leaf: int) -> None:
    path_indices = oram.server.path_bucket_indices(leaf)
    visible_path = oram.visible_path(leaf)

    for bucket_index, visible_bucket in zip(path_indices, visible_path):
        pretty = [format_visible_block(block) for block in visible_bucket]
        print(f"  bucket {bucket_index}: {pretty}")


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
    print(f"Server-visible path indices: {old_path}")
    print()

    print("Server-visible padded path before access:")
    print_padded_path_view(oram, old_leaf)
    print()

    value = oram.read(logical_id)

    print(f"Read result: {value}")
    print()

    new_leaf = oram.position_map.get_leaf(logical_id)

    print("Updated private position map:")
    print_position_map(oram)
    print()

    print(f"Logical block {logical_id} was remapped:")
    print(f"  old leaf: {old_leaf}")
    print(f"  new leaf: {new_leaf}")
    print()

    print("Real server snapshot after access:")
    print("  This is simulator-internal state, not what a real server should learn.")
    print_real_server_snapshot(oram)
    print()

    print("Server-visible padded path after access:")
    print("  Same path was rewritten with fixed-size padded buckets.")
    print_padded_path_view(oram, old_leaf)
    print()

    print("Private stash after access:")
    print_stash(oram)
    print()

    print("Server-visible physical bucket-index trace:")
    print(oram.physical_trace())
    print()
    print(format_summary(summarize_physical_trace(oram.physical_trace())))
    print()

    print(f"Invariant holds? {oram.check_invariant()}")


if __name__ == "__main__":
    main()
    