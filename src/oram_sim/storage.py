from typing import TypeVar, Generic

from oram_sim.trace import AccessTrace


T = TypeVar("T")


class NaiveStorage(Generic[T]):
    """
    A deliberately insecure baseline.

    Logical block i is stored at physical address i.
    Therefore, the server sees the exact logical access pattern.
    """

    def __init__(self, initial_blocks: list[T]) -> None:
        self._blocks = list(initial_blocks)
        self.trace = AccessTrace()

    def read(self, logical_id: int) -> T:
        self._check_id(logical_id)

        physical_address = logical_id
        self.trace.record(
            operation="read",
            logical_id=logical_id,
            physical_address=physical_address,
        )

        return self._blocks[physical_address]

    def write(self, logical_id: int, value: T) -> None:
        self._check_id(logical_id)

        physical_address = logical_id
        self.trace.record(
            operation="write",
            logical_id=logical_id,
            physical_address=physical_address,
        )

        self._blocks[physical_address] = value

    def _check_id(self, logical_id: int) -> None:
        if logical_id < 0 or logical_id >= len(self._blocks):
            raise IndexError(f"logical_id {logical_id} is out of range")
    