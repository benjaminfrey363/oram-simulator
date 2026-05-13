from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Block(Generic[T]):
    """
    A logical data block stored by the ORAM.

    logical_id:
        The client-facing block identifier.

    value:
        The data stored in the block.

    leaf:
        The currently assigned leaf for this block.
        In Path ORAM, the block is allowed to be stored somewhere
        along the path from the root to this leaf.
    """

    logical_id: int
    value: T
    leaf: int

    def __post_init__(self) -> None:
        if self.logical_id < 0:
            raise ValueError("logical_id must be nonnegative")

        if self.leaf < 0:
            raise ValueError("leaf must be nonnegative")

    def with_value(self, value: T) -> Block[T]:
        """
        Return a copy of this block with a new value.
        """
        return Block(
            logical_id=self.logical_id,
            value=value,
            leaf=self.leaf,
        )

    def with_leaf(self, leaf: int) -> Block[T]:
        """
        Return a copy of this block with a new assigned leaf.
        """
        return Block(
            logical_id=self.logical_id,
            value=self.value,
            leaf=leaf,
        )
    