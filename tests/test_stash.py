import pytest

from oram_sim.block import Block
from oram_sim.stash import DuplicateBlockError, MissingBlockError, Stash


def test_empty_stash_has_length_zero() -> None:
    stash = Stash[str]()

    assert len(stash) == 0
    assert stash.blocks() == []


def test_add_block_to_stash() -> None:
    stash = Stash[str]()
    block = Block(logical_id=2, value="hello", leaf=5)

    stash.add(block)

    assert len(stash) == 1
    assert stash.get(2) == block
    assert stash.contains(2)


def test_add_rejects_duplicate_logical_id() -> None:
    stash = Stash[str]()

    stash.add(Block(logical_id=2, value="first", leaf=5))

    with pytest.raises(DuplicateBlockError):
        stash.add(Block(logical_id=2, value="second", leaf=7))


def test_put_replaces_existing_block() -> None:
    stash = Stash[str]()

    old_block = Block(logical_id=2, value="old", leaf=5)
    new_block = Block(logical_id=2, value="new", leaf=7)

    stash.add(old_block)
    stash.put(new_block)

    assert len(stash) == 1
    assert stash.get(2) == new_block


def test_add_many() -> None:
    stash = Stash[str]()

    blocks = [
        Block(logical_id=0, value="a", leaf=1),
        Block(logical_id=1, value="b", leaf=2),
        Block(logical_id=2, value="c", leaf=3),
    ]

    stash.add_many(blocks)

    assert len(stash) == 3
    assert stash.blocks() == blocks


def test_require_returns_existing_block() -> None:
    stash = Stash[str]()
    block = Block(logical_id=2, value="hello", leaf=5)

    stash.add(block)

    assert stash.require(2) == block


def test_require_rejects_missing_block() -> None:
    stash = Stash[str]()

    with pytest.raises(MissingBlockError):
        stash.require(2)


def test_remove_returns_and_deletes_block() -> None:
    stash = Stash[str]()
    block = Block(logical_id=2, value="hello", leaf=5)

    stash.add(block)

    removed = stash.remove(2)

    assert removed == block
    assert len(stash) == 0
    assert not stash.contains(2)


def test_remove_rejects_missing_block() -> None:
    stash = Stash[str]()

    with pytest.raises(MissingBlockError):
        stash.remove(2)


def test_clear_removes_all_blocks() -> None:
    stash = Stash[str]()

    stash.add(Block(logical_id=0, value="a", leaf=1))
    stash.add(Block(logical_id=1, value="b", leaf=2))

    stash.clear()

    assert len(stash) == 0
    assert stash.blocks() == []


def test_rejects_negative_logical_id() -> None:
    stash = Stash[str]()

    with pytest.raises(ValueError):
        stash.get(-1)

    with pytest.raises(ValueError):
        stash.contains(-1)

    with pytest.raises(ValueError):
        stash.remove(-1)
        