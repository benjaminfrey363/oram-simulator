from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Generic, TypeVar, cast

from oram_sim.block import Block
from oram_sim.position_map import PositionMap
from oram_sim.stash import Stash
from oram_sim.tree import BinaryTreeServer, BucketFullError


T = TypeVar("T")


_NO_WRITE = object()


class PathORAM(Generic[T]):
    """
    A small Path ORAM simulator.

    This version supports initialization, read, and write.

    It models the main Path ORAM flow:
        - private position map,
        - private stash,
        - server-side binary tree,
        - path read,
        - remapping,
        - path write-back.

    It does not yet model encryption or dummy blocks.
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

    def read(self, logical_id: int) -> T:
        """
        Read a logical block.

        Even for a read, Path ORAM remaps the block and rewrites a path.
        This is what prevents repeated reads from producing the same obvious
        physical access pattern.
        """
        return self._access(logical_id, new_value=_NO_WRITE)

    def write(self, logical_id: int, value: T) -> None:
        """
        Write a logical block.

        This performs the same ORAM access procedure as read, but replaces the
        target block's value before writing back.
        """
        self._access(logical_id, new_value=value)

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

    def _access(self, logical_id: int, new_value: object) -> T:
        """
        Core Path ORAM access operation.

        The server-visible part is:
            read old path
            write old path

        The private client-side part is:
            use position map
            update stash
            remap target block
        """
        old_leaf = self.position_map.get_leaf(logical_id)
        new_leaf = self.position_map.remap(logical_id)

        path_blocks = self.server.read_path_blocks(old_leaf)
        self.stash.add_many(path_blocks)

        target_block = self.stash.require(logical_id)
        old_value = target_block.value

        updated_block = target_block.with_leaf(new_leaf)

        if new_value is not _NO_WRITE:
            updated_block = updated_block.with_value(cast(T, new_value))

        self.stash.put(updated_block)

        self._evict_to_path(old_leaf)

        return old_value

    def _evict_to_path(self, leaf: int) -> None:
        """
        Greedily evict stash blocks back onto the path to leaf.

        We process the path from leaf to root. At each bucket, we place up to
        bucket_capacity blocks whose assigned leaf path contains that bucket.

        This tries to push blocks as deep as possible.
        """
        path = self.server.path_bucket_indices(leaf)
        new_path_buckets: dict[int, list[Block[T]]] = {
            bucket_index: []
            for bucket_index in path
        }

        for bucket_index in reversed(path):
            eligible_blocks = [
                block
                for block in self.stash.blocks()
                if self._bucket_can_hold_block(bucket_index, block)
            ]

            eligible_blocks.sort(key=lambda block: block.logical_id)

            selected_blocks = eligible_blocks[: self.bucket_capacity]

            for block in selected_blocks:
                self.stash.remove(block.logical_id)

            new_path_buckets[bucket_index] = selected_blocks

        self.server.write_path(
            leaf,
            [new_path_buckets[bucket_index] for bucket_index in path],
        )

    def _bucket_can_hold_block(self, bucket_index: int, block: Block[T]) -> bool:
        """
        A bucket can hold a block if the bucket lies on the path to the block's
        assigned leaf.
        """
        return bucket_index in self.server.path_bucket_indices(block.leaf)

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
    