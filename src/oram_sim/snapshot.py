from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Literal, TypeVar

from oram_sim.block import Block, DummyBlock


T = TypeVar("T")


AccessPhase = Literal[
    "before_access",
    "after_path_read",
    "after_remap",
    "after_eviction",
]


@dataclass(frozen=True)
class ORAMStateSnapshot(Generic[T]):
    """
    A captured view of the ORAM state.

    This is intended for visualization and experiments. It contains a padded
    server-visible tree view, plus the private client-side position map and
    stash.

    The snapshot is a copy of the relevant state at one moment in time.
    """

    height: int
    bucket_capacity: int
    tree: dict[int, tuple[Block[T] | DummyBlock, ...]]
    position_map: dict[int, int]
    stash: tuple[Block[T], ...]
    physical_trace: tuple[int, ...]
    highlighted_buckets: frozenset[int]
    invariant_holds: bool

    def bucket(self, bucket_index: int) -> tuple[Block[T] | DummyBlock, ...]:
        return self.tree[bucket_index]

    @property
    def num_buckets(self) -> int:
        return 2 ** (self.height + 1) - 1

    @property
    def num_leaves(self) -> int:
        return 2**self.height


@dataclass(frozen=True)
class AccessSnapshot(Generic[T]):
    """
    A captured ORAM state together with metadata for one access phase.
    """

    phase: AccessPhase
    logical_id: int
    old_leaf: int
    path: tuple[int, ...]
    state: ORAMStateSnapshot[T]
    new_leaf: int | None = None
    read_value: T | None = None

    @property
    def stash_size(self) -> int:
        return len(self.state.stash)

    @property
    def physical_trace(self) -> tuple[int, ...]:
        return self.state.physical_trace
    