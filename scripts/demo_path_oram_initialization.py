from oram_sim.path_oram import PathORAM


def main() -> None:
    oram = PathORAM(
        initial_values=[f"block-{i}" for i in range(8)],
        bucket_capacity=2,
        height=3,
        seed=0,
    )

    print("Path ORAM parameters:")
    print(f"  logical blocks:   {oram.n_blocks}")
    print(f"  tree height:      {oram.height}")
    print(f"  leaves:           {oram.num_leaves}")
    print(f"  buckets:          {oram.num_buckets}")
    print(f"  bucket capacity:  {oram.bucket_capacity}")
    print()

    print("Private position map:")
    for logical_id, leaf in oram.position_entries().items():
        print(f"  block {logical_id} -> leaf {leaf}")
    print()

    print("Server snapshot:")
    for bucket_index, blocks in oram.server_snapshot().items():
        pretty_blocks = [
            f"block {block.logical_id} (leaf {block.leaf})"
            for block in blocks
        ]
        print(f"  bucket {bucket_index}: {pretty_blocks}")
    print()

    print("Private stash:")
    if len(oram.stash_blocks()) == 0:
        print("  empty")
    else:
        for block in oram.stash_blocks():
            print(f"  block {block.logical_id} (leaf {block.leaf})")
    print()

    print(f"Invariant holds? {oram.check_invariant()}")


if __name__ == "__main__":
    main()
    