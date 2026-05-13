from __future__ import annotations

import random
from collections.abc import Sequence


def sequential_pattern(n_blocks: int, length: int | None = None) -> list[int]:
    """
    Generate a sequential logical access pattern.

    Example:
        sequential_pattern(4, length=10)
        -> [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
    """
    _check_positive("n_blocks", n_blocks)

    if length is None:
        length = n_blocks

    _check_nonnegative("length", length)

    return [i % n_blocks for i in range(length)]


def repeated_pattern(block_id: int, length: int) -> list[int]:
    """
    Generate a repeated access pattern to one logical block.

    Example:
        repeated_pattern(3, length=5)
        -> [3, 3, 3, 3, 3]
    """
    _check_nonnegative("block_id", block_id)
    _check_nonnegative("length", length)

    return [block_id for _ in range(length)]


def random_pattern(
    n_blocks: int,
    length: int,
    seed: int | None = None,
) -> list[int]:
    """
    Generate a uniformly random logical access pattern.

    The seed makes experiments reproducible.
    """
    _check_positive("n_blocks", n_blocks)
    _check_nonnegative("length", length)

    rng = random.Random(seed)

    return [rng.randrange(n_blocks) for _ in range(length)]


def hotspot_pattern(
    n_blocks: int,
    hot_blocks: Sequence[int],
    length: int,
    hot_probability: float = 0.8,
    seed: int | None = None,
) -> list[int]:
    """
    Generate an access pattern with locality.

    With probability hot_probability, access one of the hot blocks.
    Otherwise, access one of the remaining cold blocks.

    Example:
        hotspot_pattern(
            n_blocks=10,
            hot_blocks=[1, 2],
            length=20,
            hot_probability=0.8,
            seed=0,
        )
    """
    _check_positive("n_blocks", n_blocks)
    _check_nonnegative("length", length)

    if not 0.0 <= hot_probability <= 1.0:
        raise ValueError("hot_probability must be between 0 and 1")

    if len(hot_blocks) == 0:
        raise ValueError("hot_blocks must be nonempty")

    hot = list(dict.fromkeys(hot_blocks))

    for block_id in hot:
        if block_id < 0 or block_id >= n_blocks:
            raise ValueError(f"hot block {block_id} is out of range")

    cold = [block_id for block_id in range(n_blocks) if block_id not in set(hot)]

    rng = random.Random(seed)
    pattern: list[int] = []

    for _ in range(length):
        should_use_hot_block = rng.random() < hot_probability

        if should_use_hot_block or not cold:
            pattern.append(rng.choice(hot))
        else:
            pattern.append(rng.choice(cold))

    return pattern


def _check_positive(name: str, value: int) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _check_nonnegative(name: str, value: int) -> None:
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    