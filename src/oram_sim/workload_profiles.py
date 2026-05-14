from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from oram_sim.access_patterns import (
    hotspot_pattern,
    random_pattern,
    repeated_pattern,
    sequential_pattern,
)
from oram_sim.workload import (
    Read,
    WorkloadOperation,
    Write,
    format_workload,
    read_workload,
)


WorkloadMode = Literal[
    "repeated",
    "sequential",
    "random",
    "hotspot",
    "mixed",
]


@dataclass(frozen=True)
class WorkloadProfile:
    """
    A named workload profile for demos and interactive viewers.
    """

    mode: WorkloadMode
    n_blocks: int
    operations: Sequence[WorkloadOperation]

    @property
    def operation_count(self) -> int:
        return len(self.operations)


def parse_hot_blocks(text: str) -> list[int]:
    """
    Parse a comma-separated list of hot blocks.

    Example:
        "1,2,3" -> [1, 2, 3]
    """
    if text.strip() == "":
        raise ValueError("hot block list must be nonempty")

    blocks = [int(part.strip()) for part in text.split(",")]

    if len(blocks) == 0:
        raise ValueError("hot block list must be nonempty")

    if any(block < 0 for block in blocks):
        raise ValueError("hot blocks must be nonnegative")

    return blocks


def build_workload_profile(
    mode: WorkloadMode,
    n_blocks: int = 8,
    length: int = 6,
    seed: int | None = 0,
    block_id: int = 3,
    hot_blocks: Sequence[int] = (1, 2, 3),
    hot_probability: float = 0.8,
    write_value_prefix: str = "updated",
) -> WorkloadProfile:
    """
    Build a workload profile for interactive demos.

    length means number of operations for all modes.
    """
    if n_blocks <= 0:
        raise ValueError("n_blocks must be positive")

    if length < 0:
        raise ValueError("length must be nonnegative")

    if mode == "repeated":
        _check_logical_id(block_id, n_blocks)

        operations = read_workload(
            repeated_pattern(block_id=block_id, length=length)
        )

    elif mode == "sequential":
        operations = read_workload(
            sequential_pattern(n_blocks=n_blocks, length=length)
        )

    elif mode == "random":
        operations = read_workload(
            random_pattern(n_blocks=n_blocks, length=length, seed=seed)
        )

    elif mode == "hotspot":
        for hot_block in hot_blocks:
            _check_logical_id(hot_block, n_blocks)

        operations = read_workload(
            hotspot_pattern(
                n_blocks=n_blocks,
                hot_blocks=hot_blocks,
                length=length,
                hot_probability=hot_probability,
                seed=seed,
            )
        )

    elif mode == "mixed":
        operations = _mixed_workload(
            n_blocks=n_blocks,
            length=length,
            seed=seed,
            write_value_prefix=write_value_prefix,
        )

    else:
        raise ValueError(f"unsupported workload mode: {mode}")

    return WorkloadProfile(
        mode=mode,
        n_blocks=n_blocks,
        operations=operations,
    )


def format_workload_profile(profile: WorkloadProfile) -> str:
    """
    Format a workload profile for display.
    """
    return "\n".join(
        [
            f"mode:             {profile.mode}",
            f"logical blocks:   {profile.n_blocks}",
            f"operations:       {profile.operation_count}",
            f"workload:         {format_workload(profile.operations)}",
        ]
    )


def _mixed_workload(
    n_blocks: int,
    length: int,
    seed: int | None,
    write_value_prefix: str,
) -> list[WorkloadOperation]:
    """
    Build a simple mixed read/write workload.

    The target block sequence is random/reproducible. Every third operation is
    a write; the others are reads.
    """
    logical_ids = random_pattern(
        n_blocks=n_blocks,
        length=length,
        seed=seed,
    )

    operations: list[WorkloadOperation] = []

    for index, logical_id in enumerate(logical_ids, start=1):
        if index % 3 == 0:
            operations.append(
                Write(
                    logical_id=logical_id,
                    value=f"{write_value_prefix}-{logical_id}-{index}",
                )
            )
        else:
            operations.append(Read(logical_id))

    return operations


def _check_logical_id(logical_id: int, n_blocks: int) -> None:
    if logical_id < 0 or logical_id >= n_blocks:
        raise ValueError(
            f"logical_id must be between 0 and {n_blocks - 1}, got {logical_id}"
        )
    