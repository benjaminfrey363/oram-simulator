from dataclasses import dataclass
from typing import Literal


Operation = Literal["read", "write"]


# Client knows logical IDs, server should only see physical accesses
# In naive storage, passive viewing adversary can infer logical IDs from physical accesses
@dataclass(frozen=True)
class Access:
    operation: Operation
    logical_id: int
    physical_address: int


class AccessTrace:
    def __init__(self) -> None:
        self._accesses: list[Access] = []

    def record(
        self,
        operation: Operation,
        logical_id: int,
        physical_address: int,
    ) -> None:
        self._accesses.append(
            Access(
                operation=operation,
                logical_id=logical_id,
                physical_address=physical_address,
            )
        )

    def accesses(self) -> list[Access]:
        return list(self._accesses)

    def physical_addresses(self) -> list[int]:
        return [access.physical_address for access in self._accesses]

    def clear(self) -> None:
        self._accesses.clear()
