import pytest

from oram_sim.workload import (
    Read,
    Write,
    alternating_read_write_workload,
    format_operation,
    format_workload,
    read_workload,
    write_workload,
)


def test_read_stores_logical_id() -> None:
    operation = Read(3)

    assert operation.logical_id == 3


def test_read_rejects_negative_logical_id() -> None:
    with pytest.raises(ValueError):
        Read(-1)


def test_write_stores_logical_id_and_value() -> None:
    operation = Write(logical_id=2, value="hello")

    assert operation.logical_id == 2
    assert operation.value == "hello"


def test_write_rejects_negative_logical_id() -> None:
    with pytest.raises(ValueError):
        Write(logical_id=-1, value="bad")


def test_read_workload() -> None:
    assert read_workload([1, 2, 1]) == [
        Read(1),
        Read(2),
        Read(1),
    ]


def test_write_workload() -> None:
    assert write_workload(
        logical_ids=[1, 2],
        values=["a", "b"],
    ) == [
        Write(logical_id=1, value="a"),
        Write(logical_id=2, value="b"),
    ]


def test_write_workload_rejects_mismatched_lengths() -> None:
    with pytest.raises(ValueError):
        write_workload(
            logical_ids=[1, 2],
            values=["a"],
        )


def test_alternating_read_write_workload() -> None:
    assert alternating_read_write_workload([1, 2]) == [
        Read(1),
        Write(logical_id=1, value="updated-1"),
        Read(1),
        Read(2),
        Write(logical_id=2, value="updated-2"),
        Read(2),
    ]


def test_format_operation() -> None:
    assert format_operation(Read(3)) == "read(3)"
    assert format_operation(Write(2, "x")) == "write(2, 'x')"


def test_format_workload() -> None:
    text = format_workload([Read(3), Write(2, "x")])

    assert text == "[read(3), write(2, 'x')]"
    