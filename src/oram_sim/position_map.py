from __future__ import annotations

import random


class PositionMap:
    """
    Private client-side map from logical block ids to assigned leaves.

    The server should not see this map.

    In Path ORAM, every logical block is assigned to a leaf. The block may
    physically appear in any bucket along the path from the root to that leaf.
    """

    def __init__(
        self,
        n_blocks: int,
        n_leaves: int,
        seed: int | None = None,
    ) -> None:
        if n_blocks <= 0:
            raise ValueError("n_blocks must be positive")

        if n_leaves <= 0:
            raise ValueError("n_leaves must be positive")

        self.n_blocks = n_blocks
        self.n_leaves = n_leaves
        self._rng = random.Random(seed)

        self._positions: dict[int, int] = {
            logical_id: self._random_leaf()
            for logical_id in range(n_blocks)
        }

    def get_leaf(self, logical_id: int) -> int:
        """
        Return the currently assigned leaf for a logical block.
        """
        self._check_logical_id(logical_id)
        return self._positions[logical_id]

    def remap(self, logical_id: int) -> int:
        """
        Assign a fresh random leaf to a logical block and return it.

        The new leaf is sampled uniformly from all leaves. It is allowed to
        equal the old leaf; this is standard and keeps the sampling simple.
        """
        self._check_logical_id(logical_id)

        new_leaf = self._random_leaf()
        self._positions[logical_id] = new_leaf

        return new_leaf

    def set_leaf(self, logical_id: int, leaf: int) -> None:
        """
        Manually set a block's leaf.

        This is mainly useful for tests and small deterministic examples.
        """
        self._check_logical_id(logical_id)
        self._check_leaf(leaf)

        self._positions[logical_id] = leaf

    def entries(self) -> dict[int, int]:
        """
        Return a copy of the full position map.
        """
        return dict(self._positions)

    def _random_leaf(self) -> int:
        return self._rng.randrange(self.n_leaves)

    def _check_logical_id(self, logical_id: int) -> None:
        if logical_id < 0 or logical_id >= self.n_blocks:
            raise ValueError(
                f"logical_id must be between 0 and {self.n_blocks - 1}, "
                f"got {logical_id}"
            )

    def _check_leaf(self, leaf: int) -> None:
        if leaf < 0 or leaf >= self.n_leaves:
            raise ValueError(
                f"leaf must be between 0 and {self.n_leaves - 1}, got {leaf}"
            )
        