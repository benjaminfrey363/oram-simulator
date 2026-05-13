import pytest

from oram_sim.storage import NaiveStorage


def test_naive_storage_read() -> None:
    storage = NaiveStorage(["a", "b", "c"])

    assert storage.read(1) == "b"

    accesses = storage.trace.accesses()
    assert len(accesses) == 1
    assert accesses[0].operation == "read"
    assert accesses[0].logical_id == 1
    assert accesses[0].physical_address == 1


def test_naive_storage_write() -> None:
    storage = NaiveStorage(["a", "b", "c"])

    storage.write(2, "new")

    assert storage.read(2) == "new"

    physical_addresses = storage.trace.physical_addresses()
    assert physical_addresses == [2, 2]


def test_out_of_range_access_fails() -> None:
    storage = NaiveStorage(["a", "b", "c"])

    with pytest.raises(IndexError):
        storage.read(10)