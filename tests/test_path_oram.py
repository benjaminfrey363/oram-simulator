import pytest

from oram_sim.path_oram import PathORAM


def test_path_oram_initializes_basic_parameters() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    assert oram.n_blocks == 4
    assert oram.height == 2
    assert oram.num_leaves == 4
    assert oram.num_buckets == 7
    assert oram.bucket_capacity == 2


def test_path_oram_default_height_rounds_up() -> None:
    oram = PathORAM(["a", "b", "c", "d", "e"], bucket_capacity=2, seed=0)

    assert oram.height == 3
    assert oram.num_leaves == 8


def test_position_map_has_one_entry_per_block() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    entries = oram.position_entries()

    assert set(entries.keys()) == {0, 1, 2, 3}
    assert all(0 <= leaf < oram.num_leaves for leaf in entries.values())


def test_initialization_creates_all_blocks_once() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    blocks = oram.all_blocks()

    assert sorted(block.logical_id for block in blocks) == [0, 1, 2, 3]
    assert sorted(block.value for block in blocks) == ["a", "b", "c", "d"]


def test_blocks_on_server_are_on_their_assigned_paths() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    for bucket_index, blocks in oram.server_snapshot().items():
        for block in blocks:
            path = oram.server.path_bucket_indices(block.leaf)
            assert bucket_index in path


def test_block_leaves_match_position_map() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    for block in oram.all_blocks():
        assert oram.position_map.get_leaf(block.logical_id) == block.leaf


def test_check_invariant_after_initialization() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    assert oram.check_invariant()


def test_initialization_is_reproducible_with_seed() -> None:
    first = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=123)
    second = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=123)

    assert first.position_entries() == second.position_entries()


def test_overflow_blocks_go_to_stash() -> None:
    oram = PathORAM(
        ["a", "b"],
        bucket_capacity=1,
        height=0,
        seed=0,
    )

    assert len(oram.server_snapshot()[1]) == 1
    assert len(oram.stash_blocks()) == 1
    assert oram.check_invariant()


def test_rejects_empty_initial_values() -> None:
    with pytest.raises(ValueError):
        PathORAM([], bucket_capacity=2)


def test_rejects_invalid_bucket_capacity() -> None:
    with pytest.raises(ValueError):
        PathORAM(["a"], bucket_capacity=0)


def test_rejects_invalid_height() -> None:
    with pytest.raises(ValueError):
        PathORAM(["a"], bucket_capacity=1, height=-1)
        