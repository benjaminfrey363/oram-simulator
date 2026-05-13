from oram_sim.block import Block, DummyBlock
from oram_sim.path_oram import PathORAM


def format_visible_block(block: Block[str] | DummyBlock) -> str:
    if isinstance(block, DummyBlock):
        return f"dummy-{block.dummy_id}"

    return f"real-{block.logical_id}(leaf={block.leaf}, value={block.value})"


def main() -> None:
    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(4)],
        bucket_capacity=3,
        height=2,
        seed=0,
    )

    print("Real server snapshot:")
    print("  This shows only real blocks currently stored in buckets.")
    print()

    for bucket_index, blocks in oram.server_snapshot().items():
        pretty = [
            f"real-{block.logical_id}(leaf={block.leaf}, value={block.value})"
            for block in blocks
        ]
        print(f"  bucket {bucket_index}: {pretty}")

    print()
    print("Padded server-visible snapshot:")
    print("  Every bucket now appears to have exactly bucket_capacity blocks.")
    print()

    for bucket_index, visible_blocks in oram.server_snapshot_padded().items():
        pretty = [format_visible_block(block) for block in visible_blocks]
        print(f"  bucket {bucket_index}: {pretty}")

    print()
    print("Example padded path view for leaf 3:")
    print()

    path_indices = oram.server.path_bucket_indices(3)
    visible_path = oram.visible_path(3)

    for bucket_index, visible_bucket in zip(path_indices, visible_path):
        pretty = [format_visible_block(block) for block in visible_bucket]
        print(f"  bucket {bucket_index}: {pretty}")


if __name__ == "__main__":
    main()
    