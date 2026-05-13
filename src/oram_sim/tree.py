from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Generic, TypeVar


T = TypeVar("T")


class BucketFullError(Exception):
    """
    Raised when trying to place too many blocks in a bucket.
    """


@dataclass
class Bucket(Generic[T]):
    """
    A fixed-capacity bucket in the ORAM server tree.
    """

    capacity: int
    _blocks: list[T] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.capacity <= 0:
            raise ValueError("bucket capacity must be positive")

        if len(self._blocks) > self.capacity:
            raise BucketFullError("initial bucket contents exceed capacity")

    def blocks(self) -> list[T]:
        return list(self._blocks)

    def set_blocks(self, blocks: Sequence[T]) -> None:
        if len(blocks) > self.capacity:
            raise BucketFullError(
                f"bucket capacity is {self.capacity}, but got {len(blocks)} blocks"
            )

        self._blocks = list(blocks)

    def add(self, block: T) -> None:
        if len(self._blocks) >= self.capacity:
            raise BucketFullError("bucket is full")

        self._blocks.append(block)

    def clear(self) -> None:
        self._blocks.clear()

    def is_full(self) -> bool:
        return len(self._blocks) == self.capacity

    def __len__(self) -> int:
        return len(self._blocks)


class BinaryTreeServer(Generic[T]):
    """
    Complete binary tree of fixed-capacity buckets.

    Buckets are stored using heap-style indexing:

        root: 1
        left child of i: 2i
        right child of i: 2i + 1

    Leaves are labelled 0, 1, ..., 2^height - 1.

    Example with height = 2:

              1
            /   \\
           2     3
          / \\   / \\
         4   5 6   7

    leaf 0 has path [1, 2, 4]
    leaf 1 has path [1, 2, 5]
    leaf 2 has path [1, 3, 6]
    leaf 3 has path [1, 3, 7]
    """

    def __init__(self, height: int, bucket_capacity: int) -> None:
        if height < 0:
            raise ValueError("height must be nonnegative")

        if bucket_capacity <= 0:
            raise ValueError("bucket_capacity must be positive")

        self.height = height
        self.bucket_capacity = bucket_capacity

        self._buckets: list[Bucket[T] | None] = [None] + [
            Bucket[T](capacity=bucket_capacity)
            for _ in range(self.num_buckets)
        ]

        self._physical_trace: list[int] = []

    @property
    def num_leaves(self) -> int:
        return 2**self.height

    @property
    def num_buckets(self) -> int:
        return 2 ** (self.height + 1) - 1

    def path_bucket_indices(self, leaf: int) -> list[int]:
        """
        Return the bucket indices on the root-to-leaf path.
        """
        self._check_leaf(leaf)

        index = self._leaf_to_bucket_index(leaf)
        path = []

        while index >= 1:
            path.append(index)
            index //= 2

        path.reverse()
        return path

    def read_path(self, leaf: int) -> list[list[T]]:
        """
        Read all buckets on a root-to-leaf path.

        This records the bucket indices in the physical trace, since these are
        the server-visible addresses.
        """
        path_indices = self.path_bucket_indices(leaf)

        for index in path_indices:
            self._physical_trace.append(index)

        return [self._bucket(index).blocks() for index in path_indices]

    def read_path_blocks(self, leaf: int) -> list[T]:
        """
        Read all blocks on a root-to-leaf path, flattened into one list.
        """
        path_buckets = self.read_path(leaf)
        return [block for bucket in path_buckets for block in bucket]

    def write_path(self, leaf: int, buckets: Sequence[Sequence[T]]) -> None:
        """
        Overwrite all buckets on a root-to-leaf path.

        The input should contain one sequence of blocks for each bucket on the
        path, ordered from root to leaf.
        """
        path_indices = self.path_bucket_indices(leaf)

        if len(buckets) != len(path_indices):
            raise ValueError(
                f"expected {len(path_indices)} buckets, got {len(buckets)}"
            )

        for index, blocks in zip(path_indices, buckets):
            self._physical_trace.append(index)
            self._bucket(index).set_blocks(blocks)

    def place_block(self, bucket_index: int, block: T) -> None:
        """
        Place a block directly into a bucket.

        This is useful for tests and setup. Path ORAM will usually use
        read_path/write_path instead.
        """
        self._check_bucket_index(bucket_index)
        self._bucket(bucket_index).add(block)

    def bucket_blocks(self, bucket_index: int) -> list[T]:
        """
        Return a copy of the blocks in a bucket.
        """
        self._check_bucket_index(bucket_index)
        return self._bucket(bucket_index).blocks()

    def physical_trace(self) -> list[int]:
        """
        Return the server-visible bucket access trace.
        """
        return list(self._physical_trace)

    def clear_trace(self) -> None:
        self._physical_trace.clear()

    def _leaf_to_bucket_index(self, leaf: int) -> int:
        return 2**self.height + leaf

    def _bucket(self, index: int) -> Bucket[T]:
        bucket = self._buckets[index]

        if bucket is None:
            raise RuntimeError("invalid internal bucket access")

        return bucket

    def _check_leaf(self, leaf: int) -> None:
        if leaf < 0 or leaf >= self.num_leaves:
            raise ValueError(
                f"leaf must be between 0 and {self.num_leaves - 1}, got {leaf}"
            )

    def _check_bucket_index(self, bucket_index: int) -> None:
        if bucket_index < 1 or bucket_index > self.num_buckets:
            raise ValueError(
                f"bucket index must be between 1 and {self.num_buckets}, "
                f"got {bucket_index}"
            )