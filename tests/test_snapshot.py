from oram_sim.block import Block, DummyBlock
from oram_sim.path_oram import PathORAM
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot


def test_state_snapshot_captures_padded_tree() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = oram.state_snapshot()

    assert isinstance(snapshot, ORAMStateSnapshot)
    assert snapshot.height == 2
    assert snapshot.bucket_capacity == 2
    assert snapshot.num_buckets == 7
    assert snapshot.num_leaves == 4

    assert set(snapshot.tree.keys()) == set(range(1, 8))
    assert all(len(bucket) == 2 for bucket in snapshot.tree.values())

    for bucket in snapshot.tree.values():
        assert all(isinstance(block, (Block, DummyBlock)) for block in bucket)


def test_state_snapshot_captures_position_map_and_stash() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = oram.state_snapshot()

    assert snapshot.position_map == oram.position_entries()
    assert snapshot.stash == tuple(oram.stash_blocks())


def test_state_snapshot_captures_highlighted_buckets() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = oram.state_snapshot(highlighted_buckets=[1, 3, 7])

    assert snapshot.highlighted_buckets == frozenset({1, 3, 7})


def test_read_snapshots_yield_access_snapshots() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshots = list(oram.read_snapshots(2))

    assert all(isinstance(snapshot, AccessSnapshot) for snapshot in snapshots)

    assert [snapshot.phase for snapshot in snapshots] == [
        "before_access",
        "after_path_read",
        "after_remap",
        "after_eviction",
    ]


def test_read_snapshots_include_metadata() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    old_leaf = oram.position_map.get_leaf(2)
    expected_path = tuple(oram.server.path_bucket_indices(old_leaf))

    snapshots = list(oram.read_snapshots(2))

    for snapshot in snapshots:
        assert snapshot.logical_id == 2
        assert snapshot.old_leaf == old_leaf
        assert snapshot.path == expected_path
        assert snapshot.state.highlighted_buckets == frozenset(expected_path)

    assert snapshots[-1].read_value == "c"


def test_read_snapshots_preserve_final_invariant() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshots = list(oram.read_snapshots(2))

    assert snapshots[0].state.invariant_holds
    assert snapshots[-1].state.invariant_holds
    assert oram.check_invariant()


def test_intermediate_snapshot_may_break_invariant() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshots = list(oram.read_snapshots(2))

    after_path_read = snapshots[1]

    # This is expected. At this debugging phase, path blocks have been copied
    # into the stash but the path has not yet been rewritten.
    assert not after_path_read.state.invariant_holds


def test_write_snapshots_update_value_after_completion() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshots = list(oram.write_snapshots(1, "new-b"))

    assert snapshots[-1].state.invariant_holds
    assert oram.read(1) == "new-b"


def test_snapshot_is_stable_after_later_access() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshots = list(oram.read_snapshots(2))
    captured_trace = snapshots[-1].state.physical_trace
    captured_position_map = dict(snapshots[-1].state.position_map)

    oram.read(1)

    assert snapshots[-1].state.physical_trace == captured_trace
    assert snapshots[-1].state.position_map == captured_position_map
    