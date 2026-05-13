from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from oram_sim.block import Block


T = TypeVar("T")


class DuplicateBlockError(Exception):
    """
    Raised when attempting to add a block whose logical id is already in the stash.
    """


class MissingBlockError(Exception):
    """
    Raised when attempting to remove a block that is not in the stash.
    """


class Stash(Generic[T]):
    """
    Private client-side storage for ORAM blocks.

    The stash is not visible to the server.

    We store at most one block per logical id. This is a simplifying invariant
    that makes the ORAM logic easier to reason about.
    """

    def __init__(self) -> None:
        self._blocks: dict[int, Block[T]] = {}

    def add(self, block: Block[T]) -> None:
        """
        Add a block to the stash.

        Raises DuplicateBlockError if a block with the same logical id is
        already present.
        """
        if block.logical_id in self._blocks:
            raise DuplicateBlockError(
                f"block {block.logical_id} is already in the stash"
            )

        self._blocks[block.logical_id] = block

    def add_many(self, blocks: Iterable[Block[T]]) -> None:
        """
        Add several blocks to the stash.
        """
        for block in blocks:
            self.add(block)

    def put(self, block: Block[T]) -> None:
        """
        Insert or replace a block.

        This is useful when an access updates the target block's value or leaf.
        """
        self._blocks[block.logical_id] = block

    def get(self, logical_id: int) -> Block[T] | None:
        """
        Return a block if it is in the stash, otherwise None.
        """
        self._check_logical_id(logical_id)
        return self._blocks.get(logical_id)

    def require(self, logical_id: int) -> Block[T]:
        """
        Return a block, or raise MissingBlockError if it is absent.
        """
        self._check_logical_id(logical_id)

        try:
            return self._blocks[logical_id]
        except KeyError as exc:
            raise MissingBlockError(
                f"block {logical_id} is not in the stash"
            ) from exc

    def remove(self, logical_id: int) -> Block[T]:
        """
        Remove and return a block from the stash.
        """
        self._check_logical_id(logical_id)

        try:
            return self._blocks.pop(logical_id)
        except KeyError as exc:
            raise MissingBlockError(
                f"block {logical_id} is not in the stash"
            ) from exc

    def contains(self, logical_id: int) -> bool:
        """
        Return True if the stash contains a block with this logical id.
        """
        self._check_logical_id(logical_id)
        return logical_id in self._blocks

    def blocks(self) -> list[Block[T]]:
        """
        Return a copy of the blocks currently in the stash.
        """
        return list(self._blocks.values())

    def clear(self) -> None:
        self._blocks.clear()

    def __len__(self) -> int:
        return len(self._blocks)

    def _check_logical_id(self, logical_id: int) -> None:
        if logical_id < 0:
            raise ValueError("logical_id must be nonnegative")
        