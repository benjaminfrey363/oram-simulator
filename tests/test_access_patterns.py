import pytest

from oram_sim.access_patterns import (
    hotspot_pattern,
    random_pattern,
    repeated_pattern,
    sequential_pattern,
)


def test_sequential_pattern_default_length() -> None:
    assert sequential_pattern(4) == [0, 1, 2, 3]


def test_sequential_pattern_custom_length() -> None:
    assert sequential_pattern(4, length=10) == [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]


def test_repeated_pattern() -> None:
    assert repeated_pattern(3, length=5) == [3, 3, 3, 3, 3]


def test_random_pattern_is_reproducible_with_seed() -> None:
    first = random_pattern(n_blocks=10, length=20, seed=123)
    second = random_pattern(n_blocks=10, length=20, seed=123)

    assert first == second


def test_random_pattern_stays_in_range() -> None:
    pattern = random_pattern(n_blocks=10, length=100, seed=0)

    assert all(0 <= block_id < 10 for block_id in pattern)


def test_hotspot_pattern_is_reproducible_with_seed() -> None:
    first = hotspot_pattern(
        n_blocks=10,
        hot_blocks=[1, 2],
        length=20,
        hot_probability=0.8,
        seed=123,
    )
    second = hotspot_pattern(
        n_blocks=10,
        hot_blocks=[1, 2],
        length=20,
        hot_probability=0.8,
        seed=123,
    )

    assert first == second


def test_hotspot_pattern_stays_in_range() -> None:
    pattern = hotspot_pattern(
        n_blocks=10,
        hot_blocks=[1, 2],
        length=100,
        hot_probability=0.8,
        seed=0,
    )

    assert all(0 <= block_id < 10 for block_id in pattern)


def test_hotspot_pattern_rejects_empty_hot_blocks() -> None:
    with pytest.raises(ValueError):
        hotspot_pattern(
            n_blocks=10,
            hot_blocks=[],
            length=10,
        )


def test_hotspot_pattern_rejects_out_of_range_hot_block() -> None:
    with pytest.raises(ValueError):
        hotspot_pattern(
            n_blocks=10,
            hot_blocks=[10],
            length=10,
        )
