import pytest

from oram_sim.path_oram import PathORAM
from oram_sim.block import Block, DummyBlock


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


def test_read_returns_correct_value() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    assert oram.read(2) == "c"


def test_read_preserves_invariant() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    oram.read(2)

    assert oram.check_invariant()


def test_repeated_reads_return_correct_value() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    assert oram.read(2) == "c"
    assert oram.read(2) == "c"
    assert oram.read(2) == "c"

    assert oram.check_invariant()


def test_write_updates_value() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    oram.write(1, "new-b")

    assert oram.read(1) == "new-b"
    assert oram.check_invariant()


def test_multiple_writes_and_reads() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    oram.write(0, "new-a")
    oram.write(3, "new-d")

    assert oram.read(0) == "new-a"
    assert oram.read(1) == "b"
    assert oram.read(2) == "c"
    assert oram.read(3) == "new-d"

    assert oram.check_invariant()


def test_access_records_read_and_write_path() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    old_leaf = oram.position_map.get_leaf(2)
    expected_path = oram.server.path_bucket_indices(old_leaf)

    oram.read(2)

    assert oram.physical_trace() == expected_path + expected_path


def test_clear_physical_trace_after_access() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    oram.read(2)
    oram.clear_physical_trace()

    assert oram.physical_trace() == []


def test_access_works_when_target_starts_in_stash() -> None:
    oram = PathORAM(
        ["a", "b"],
        bucket_capacity=1,
        height=0,
        seed=0,
    )

    assert len(oram.stash_blocks()) == 1

    assert oram.read(1) == "b"
    assert oram.check_invariant()

def test_server_bucket_view_is_padded_to_bucket_capacity() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=3, seed=0)

    for bucket_index in range(1, oram.num_buckets + 1):
        visible_bucket = oram.server_bucket_view(bucket_index)

        assert len(visible_bucket) == 3
        assert all(isinstance(block, (Block, DummyBlock)) for block in visible_bucket)


def test_server_snapshot_padded_includes_all_buckets() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    padded_snapshot = oram.server_snapshot_padded()

    assert set(padded_snapshot.keys()) == set(range(1, oram.num_buckets + 1))
    assert all(len(bucket) == 2 for bucket in padded_snapshot.values())


def test_server_snapshot_padded_contains_dummy_blocks_for_empty_space() -> None:
    oram = PathORAM(["a"], bucket_capacity=3, height=1, seed=0)

    padded_snapshot = oram.server_snapshot_padded()

    all_visible_blocks = [
        block
        for bucket in padded_snapshot.values()
        for block in bucket
    ]

    assert any(isinstance(block, DummyBlock) for block in all_visible_blocks)


def test_visible_path_returns_padded_buckets() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    visible_path = oram.visible_path(leaf=3)

    # Height 2 means a path has root, internal node, leaf: 3 buckets.
    assert len(visible_path) == 3

    # Each bucket is padded to capacity 2.
    assert all(len(bucket) == 2 for bucket in visible_path)

def test_read_steps_yields_expected_phases() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    steps = list(oram.read_steps(2))

    assert [step.phase for step in steps] == [
        "before_access",
        "after_path_read",
        "after_remap",
        "after_eviction",
    ]


def test_read_steps_returns_read_value_in_steps() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    steps = list(oram.read_steps(2))

    assert steps[-1].read_value == "c"


def test_read_steps_preserves_invariant_after_completion() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    list(oram.read_steps(2))

    assert oram.check_invariant()


def test_read_steps_records_read_and_write_path_after_completion() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    old_leaf = oram.position_map.get_leaf(2)
    expected_path = oram.server.path_bucket_indices(old_leaf)

    steps = list(oram.read_steps(2))

    assert steps[-1].physical_trace == expected_path + expected_path
    assert oram.physical_trace() == expected_path + expected_path


def test_write_steps_updates_value_after_completion() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    list(oram.write_steps(1, "new-b"))

    assert oram.read(1) == "new-b"
    assert oram.check_invariant()


def test_after_path_read_step_has_path_read_trace_only() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    old_leaf = oram.position_map.get_leaf(2)
    expected_path = oram.server.path_bucket_indices(old_leaf)

    steps = list(oram.read_steps(2))

    after_path_read = steps[1]

    assert after_path_read.phase == "after_path_read"
    assert after_path_read.physical_trace == expected_path
