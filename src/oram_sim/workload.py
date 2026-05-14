from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Generic, TypeAlias, TypeVar


T = TypeVar("T")


@dataclass(frozen=True)
class Read:
    """
    A logical read operation.
    """

    logical_id: int

    def __post_init__(self) -> None:
        if self.logical_id < 0:
            raise ValueError("logical_id must be nonnegative")


@dataclass(frozen=True)
class Write(Generic[T]):
    """
    A logical write operation.
    """

    logical_id: int
    value: T

    def __post_init__(self) -> None:
        if self.logical_id < 0:
            raise ValueError("logical_id must be nonnegative")


WorkloadOperation: TypeAlias = Read | Write[Any]


def read_workload(logical_pattern: Sequence[int]) -> list[Read]:
    """
    Convert a sequence of logical ids into read operations.
    """
    return [Read(logical_id) for logical_id in logical_pattern]


def write_workload(
    logical_ids: Sequence[int],
    values: Sequence[T],
) -> list[Write[T]]:
    """
    Convert logical ids and values into write operations.
    """
    if len(logical_ids) != len(values):
        raise ValueError("logical_ids and values must have the same length")

    return [
        Write(logical_id=logical_id, value=value)
        for logical_id, value in zip(logical_ids, values)
    ]


def alternating_read_write_workload(
    logical_ids: Sequence[int],
    write_value_prefix: str = "updated",
) -> list[WorkloadOperation]:
    """
    Create a simple alternating read/write workload.

    For each logical id i, generate:

        Read(i)
        Write(i, f"{write_value_prefix}-{i}")
        Read(i)

    This is useful for small demos.
    """
    operations: list[WorkloadOperation] = []

    for logical_id in logical_ids:
        operations.append(Read(logical_id))
        operations.append(
            Write(
                logical_id=logical_id,
                value=f"{write_value_prefix}-{logical_id}",
            )
        )
        operations.append(Read(logical_id))

    return operations


def format_operation(operation: WorkloadOperation) -> str:
    """
    Format a workload operation for demos.
    """
    if isinstance(operation, Read):
        return f"read({operation.logical_id})"

    return f"write({operation.logical_id}, {operation.value!r})"


def format_workload(operations: Sequence[WorkloadOperation]) -> str:
    """
    Format a workload as a compact list.
    """
    return "[" + ", ".join(format_operation(operation) for operation in operations) + "]"
