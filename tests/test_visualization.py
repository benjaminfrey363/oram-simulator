from oram_sim.block import Block, DummyBlock
from oram_sim.path_oram import PathORAM
from oram_sim.visualization import (
    format_bucket,
    format_full_state,
    format_position_map,
    format_stash,
    format_tree,
    format_tree_with_highlighted_path,
    format_visible_block,
    format_access_step
)


def test_format_visible_real_block() -> None:
    block = Block(logical_id=2, value="hello", leaf=3)

    assert format_visible_block(block) == "B2@L3"


def test_format_visible_real_block_with_value() -> None:
    block = Block(logical_id=2, value="hello", leaf=3)

    assert format_visible_block(block, show_values=True) == "B2@L3=hello"


def test_format_visible_dummy_block() -> None:
    dummy = DummyBlock(dummy_id=10)

    assert format_visible_block(dummy) == "D"


def test_format_bucket_contains_bucket_index() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    text = format_bucket(oram, bucket_index=1)

    assert text.startswith("[1:")
    assert text.endswith("]")


def test_format_bucket_highlighted() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    text = format_bucket(oram, bucket_index=1, highlighted=True)

    assert text.startswith("*[1:")
    assert text.endswith("]*")


def test_format_tree_contains_depths() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    text = format_tree(oram)

    assert "depth 0:" in text
    assert "depth 1:" in text
    assert "depth 2:" in text


def test_format_tree_with_highlighted_path_marks_path_buckets() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    text = format_tree_with_highlighted_path(oram, leaf=3)

    # For height 2, leaf 3 has path [1, 3, 7].
    assert "highlighted leaf: 3" in text
    assert "highlighted path: [1, 3, 7]" in text
    assert "*[1:" in text
    assert "*[3:" in text
    assert "*[7:" in text


def test_format_position_map() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    text = format_position_map(oram)

    assert "private position map:" in text
    assert "block 0 -> leaf" in text
    assert "block 1 -> leaf" in text


def test_format_stash_empty() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    text = format_stash(oram)

    assert "private stash:" in text
    assert "empty" in text


def test_format_stash_with_values() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=1, height=0, seed=0)

    text = format_stash(oram, show_values=True)

    assert "private stash:" in text
    assert "value=" in text


def test_format_full_state() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    text = format_full_state(oram, highlighted_leaf=2)

    assert "highlighted leaf: 2" in text
    assert "private position map:" in text
    assert "private stash:" in text


def test_format_access_step() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, seed=0)

    step = next(oram.read_steps(2))

    text = format_access_step(step)

    assert "Before access" in text
    assert "logical block: 2" in text
    assert "old leaf:" in text
    assert "touched path:" in text
    