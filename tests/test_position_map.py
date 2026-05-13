import pytest

from oram_sim.position_map import PositionMap


def test_position_map_has_one_leaf_per_block() -> None:
    position_map = PositionMap(n_blocks=5, n_leaves=8, seed=0)

    entries = position_map.entries()

    assert set(entries.keys()) == {0, 1, 2, 3, 4}
    assert all(0 <= leaf < 8 for leaf in entries.values())


def test_position_map_is_reproducible_with_seed() -> None:
    first = PositionMap(n_blocks=10, n_leaves=16, seed=123)
    second = PositionMap(n_blocks=10, n_leaves=16, seed=123)

    assert first.entries() == second.entries()


def test_get_leaf_returns_current_leaf() -> None:
    position_map = PositionMap(n_blocks=5, n_leaves=8, seed=0)

    position_map.set_leaf(logical_id=2, leaf=7)

    assert position_map.get_leaf(2) == 7


def test_remap_updates_leaf() -> None:
    position_map = PositionMap(n_blocks=5, n_leaves=8, seed=0)

    new_leaf = position_map.remap(2)

    assert 0 <= new_leaf < 8
    assert position_map.get_leaf(2) == new_leaf


def test_set_leaf_rejects_out_of_range_leaf() -> None:
    position_map = PositionMap(n_blocks=5, n_leaves=8, seed=0)

    with pytest.raises(ValueError):
        position_map.set_leaf(logical_id=2, leaf=8)


def test_get_leaf_rejects_out_of_range_logical_id() -> None:
    position_map = PositionMap(n_blocks=5, n_leaves=8, seed=0)

    with pytest.raises(ValueError):
        position_map.get_leaf(5)


def test_position_map_rejects_invalid_sizes() -> None:
    with pytest.raises(ValueError):
        PositionMap(n_blocks=0, n_leaves=8)

    with pytest.raises(ValueError):
        PositionMap(n_blocks=5, n_leaves=0)
        