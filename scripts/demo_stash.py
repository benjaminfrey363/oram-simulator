from oram_sim.block import Block
from oram_sim.stash import Stash


def print_stash(stash: Stash[str]) -> None:
    if len(stash) == 0:
        print("  empty")
        return

    for block in stash.blocks():
        print(
            f"  block {block.logical_id}: "
            f"value={block.value}, assigned_leaf={block.leaf}"
        )


def main() -> None:
    stash = Stash[str]()

    print("Initial stash:")
    print_stash(stash)
    print()

    path_blocks = [
        Block(logical_id=0, value="block-0", leaf=3),
        Block(logical_id=2, value="block-2", leaf=7),
        Block(logical_id=4, value="block-4", leaf=1),
    ]

    print("After reading a path, we move its blocks into the stash:")
    stash.add_many(path_blocks)
    print_stash(stash)
    print()

    print("Now suppose we access logical block 2.")
    block = stash.require(2)

    updated_block = block.with_value("updated-block-2").with_leaf(5)
    stash.put(updated_block)

    print("After updating its value and remapping its assigned leaf:")
    print_stash(stash)


if __name__ == "__main__":
    main()
    