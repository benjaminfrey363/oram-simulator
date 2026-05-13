import pytest

from oram_sim.block import Block, DummyBlock


def test_block_stores_fields() -> None:
    block = Block(logical_id=3, value="hello", leaf=5)

    assert block.logical_id == 3
    assert block.value == "hello"
    assert block.leaf == 5


def test_block_with_value_returns_updated_copy() -> None:
    block = Block(logical_id=3, value="old", leaf=5)

    updated = block.with_value("new")

    assert updated.logical_id == 3
    assert updated.value == "new"
    assert updated.leaf == 5

    assert block.value == "old"


def test_block_with_leaf_returns_updated_copy() -> None:
    block = Block(logical_id=3, value="hello", leaf=5)

    updated = block.with_leaf(1)

    assert updated.logical_id == 3
    assert updated.value == "hello"
    assert updated.leaf == 1

    assert block.leaf == 5


def test_block_rejects_negative_logical_id() -> None:
    with pytest.raises(ValueError):
        Block(logical_id=-1, value="bad", leaf=0)


def test_block_rejects_negative_leaf() -> None:
    with pytest.raises(ValueError):
        Block(logical_id=0, value="bad", leaf=-1)

def test_dummy_block_stores_id() -> None:
    dummy = DummyBlock(dummy_id=5)

    assert dummy.dummy_id == 5


def test_dummy_block_rejects_negative_id() -> None:
    with pytest.raises(ValueError):
        DummyBlock(dummy_id=-1)
        