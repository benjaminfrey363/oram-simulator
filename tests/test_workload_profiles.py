import pytest

from oram_sim.workload import Read, Write
from oram_sim.workload_profiles import (
    build_workload_profile,
    format_workload_profile,
    parse_hot_blocks,
)


def test_parse_hot_blocks() -> None:
    assert parse_hot_blocks("1,2,3") == [1, 2, 3]


def test_parse_hot_blocks_allows_spaces() -> None:
    assert parse_hot_blocks("1, 2, 3") == [1, 2, 3]


def test_parse_hot_blocks_rejects_empty_string() -> None:
    with pytest.raises(ValueError):
        parse_hot_blocks("")


def test_parse_hot_blocks_rejects_negative_block() -> None:
    with pytest.raises(ValueError):
        parse_hot_blocks("1,-2,3")


def test_build_repeated_workload_profile() -> None:
    profile = build_workload_profile(
        mode="repeated",
        n_blocks=8,
        length=4,
        block_id=3,
    )

    assert profile.mode == "repeated"
    assert profile.n_blocks == 8
    assert profile.operations == [
        Read(3),
        Read(3),
        Read(3),
        Read(3),
    ]


def test_build_sequential_workload_profile() -> None:
    profile = build_workload_profile(
        mode="sequential",
        n_blocks=4,
        length=6,
    )

    assert profile.operations == [
        Read(0),
        Read(1),
        Read(2),
        Read(3),
        Read(0),
        Read(1),
    ]


def test_build_random_workload_profile_is_reproducible() -> None:
    first = build_workload_profile(
        mode="random",
        n_blocks=8,
        length=10,
        seed=123,
    )
    second = build_workload_profile(
        mode="random",
        n_blocks=8,
        length=10,
        seed=123,
    )

    assert first.operations == second.operations


def test_build_hotspot_workload_profile() -> None:
    profile = build_workload_profile(
        mode="hotspot",
        n_blocks=8,
        length=10,
        hot_blocks=[1, 2],
        hot_probability=0.8,
        seed=0,
    )

    assert len(profile.operations) == 10
    assert all(isinstance(operation, Read) for operation in profile.operations)


def test_build_mixed_workload_profile_contains_reads_and_writes() -> None:
    profile = build_workload_profile(
        mode="mixed",
        n_blocks=8,
        length=6,
        seed=0,
    )

    assert len(profile.operations) == 6
    assert any(isinstance(operation, Read) for operation in profile.operations)
    assert any(isinstance(operation, Write) for operation in profile.operations)


def test_build_workload_profile_rejects_invalid_block_id() -> None:
    with pytest.raises(ValueError):
        build_workload_profile(
            mode="repeated",
            n_blocks=4,
            length=5,
            block_id=4,
        )


def test_build_workload_profile_rejects_invalid_hot_block() -> None:
    with pytest.raises(ValueError):
        build_workload_profile(
            mode="hotspot",
            n_blocks=4,
            length=5,
            hot_blocks=[1, 4],
        )


def test_format_workload_profile() -> None:
    profile = build_workload_profile(
        mode="repeated",
        n_blocks=8,
        length=2,
        block_id=3,
    )

    text = format_workload_profile(profile)

    assert "mode:" in text
    assert "logical blocks:" in text
    assert "operations:" in text
    assert "read(3)" in text
    