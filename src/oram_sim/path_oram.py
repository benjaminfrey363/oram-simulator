from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Generic, TypeVar

from oram_sim.block import Block
from oram_sim.position_map import PositionMap
from oram_sim.stash import Stash
from oram_sim.tree import BinaryTreeServer, BucketFullError


T = TypeVar("T")


class PathORAM(Generic[T]):
    """
    A first Path ORAM wrapper.

    This version only implements initialization.

    It creates:
        - a binary tree server,
        - a private position map,
        - a private stash,
        - one Block per logical item.

    Full read/write access will be implemented in the next steps.
    """

    def __init__(
        self,
        initial_values: Sequence[T],
        bucket_capacity: int = 4,
        height: int | None = None,
        seed: int | None = None,
    ) -> None:
        if len(initial_values) == 0:
            raise ValueError("initial_values must be nonempty")

        if bucket_capacity <= 0:
            raise ValueError("bucket_capacity must be positive")

        self.n_blocks = len(initial_values)
        self.height = (
            height
            if height is not None
            else self._default_height(self.n_blocks)
        )

        if self.height < 0:
            raise ValueError("height must be nonnegative")

        self.bucket_capacity = bucket_capacity

        self.server: BinaryTreeServer[Block[T]] = BinaryTreeServer(
            height=self.height,
            bucket_capacity=bucket_capacity,
        )
        self.position_map = PositionMap(
            n_blocks=self.n_blocks,
            n_leaves=self.server.num_leaves,
            seed=seed,
        )
        self.stash: Stash[T] = Stash()

        self._initialize_blocks(initial_values)

    @property
    def num_leaves(self) -> int:
        return self.server.num_leaves

    @property
    def num_buckets(self) -> int:
        return self.server.num_buckets

    def position_entries(self) -> dict[int, int]:
        """
        Return a copy of the private position map.

        This is exposed for demos/tests. In a real ORAM, the server would not
        see this information.
        """
        return self.position_map.entries()

    def stash_blocks(self) -> list[Block[T]]:
        """
        Return the current private stash blocks.
        """
        return self.stash.blocks()

    def server_snapshot(self) -> dict[int, list[Block[T]]]:
        """
        Return a snapshot of nonempty server buckets.

        The keys are physical bucket indices.
        """
        snapshot: dict[int, list[Block[T]]] = {}

        for bucket_index in range(1, self.server.num_buckets + 1):
            blocks = self.server.bucket_blocks(bucket_index)
            if blocks:
                snapshot[bucket_index] = blocks

        return snapshot

    def all_blocks(self) -> list[Block[T]]:
        """
        Return every real block, whether it is on the server or in the stash.

        This is useful for checking invariants.
        """
        blocks: list[Block[T]] = []

        for bucket_blocks in self.server_snapshot().values():
            blocks.extend(bucket_blocks)

        blocks.extend(self.stash.blocks())

        return blocks

    def check_invariant(self) -> bool:
        """
        Check the basic Path ORAM placement invariant.

        Every block must appear exactly once, and every block stored on the
        server must lie on the path to its assigned leaf.
        """
        blocks = self.all_blocks()

        logical_ids = [block.logical_id for block in blocks]

        if sorted(logical_ids) != list(range(self.n_blocks)):
            return False

        for bucket_index, bucket_blocks in self.server_snapshot().items():
            for block in bucket_blocks:
                path = self.server.path_bucket_indices(block.leaf)
                if bucket_index not in path:
                    return False

        for block in blocks:
            if self.position_map.get_leaf(block.logical_id) != block.leaf:
                return False

        return True

    def physical_trace(self) -> list[int]:
        return self.server.physical_trace()

    def clear_physical_trace(self) -> None:
        self.server.clear_trace()

    def _initialize_blocks(self, initial_values: Sequence[T]) -> None:
        for logical_id, value in enumerate(initial_values):
            leaf = self.position_map.get_leaf(logical_id)

            block = Block(
                logical_id=logical_id,
                value=value,
                leaf=leaf,
            )

            placed = self._place_block_deepest(block)

            if not placed:
                self.stash.add(block)

    def _place_block_deepest(self, block: Block[T]) -> bool:
        """
        Try to place a block as deep as possible on its assigned path.

        Returns True if the block was placed on the server.
        Returns False if every bucket on the path was full.
        """
        path = self.server.path_bucket_indices(block.leaf)

        for bucket_index in reversed(path):
            if len(self.server.bucket_blocks(bucket_index)) < self.bucket_capacity:
                try:
                    self.server.place_block(bucket_index, block)
                    return True
                except BucketFullError:
                    # This should not happen because of the length check,
                    # but keeping the guard makes the method robust.
                    continue

        return False

    @staticmethod
    def _default_height(n_blocks: int) -> int:
        """
        Choose the smallest height with at least n_blocks leaves.

        Equivalently, choose height h such that 2^h >= n_blocks.
        """
        if n_blocks <= 0:
            raise ValueError("n_blocks must be positive")

        return math.ceil(math.log2(n_blocks))
    