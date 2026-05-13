import pytest

from oram_sim.tree import BinaryTreeServer, Bucket, BucketFullError


def test_bucket_add_and_blocks() -> None:
    bucket = Bucket[str](capacity=2)

    bucket.add("a")
    bucket.add("b")

    assert bucket.blocks() == ["a", "b"]
    assert bucket.is_full()


def test_bucket_rejects_too_many_blocks() -> None:
    bucket = Bucket[str](capacity=1)

    bucket.add("a")

    with pytest.raises(BucketFullError):
        bucket.add("b")


def test_tree_basic_sizes() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=3)

    assert server.height == 2
    assert server.bucket_capacity == 3
    assert server.num_leaves == 4
    assert server.num_buckets == 7


def test_path_bucket_indices_height_two() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=3)

    assert server.path_bucket_indices(0) == [1, 2, 4]
    assert server.path_bucket_indices(1) == [1, 2, 5]
    assert server.path_bucket_indices(2) == [1, 3, 6]
    assert server.path_bucket_indices(3) == [1, 3, 7]


def test_rejects_out_of_range_leaf() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=3)

    with pytest.raises(ValueError):
        server.path_bucket_indices(4)


def test_place_block_directly() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.place_block(1, "root-block")
    server.place_block(4, "leaf-block")

    assert server.bucket_blocks(1) == ["root-block"]
    assert server.bucket_blocks(4) == ["leaf-block"]


def test_read_path_returns_bucket_contents() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.place_block(1, "a")
    server.place_block(2, "b")
    server.place_block(4, "c")
    server.place_block(7, "not-on-path")

    path = server.read_path(0)

    assert path == [["a"], ["b"], ["c"]]


def test_read_path_blocks_flattens_contents() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.place_block(1, "a")
    server.place_block(2, "b")
    server.place_block(4, "c")

    blocks = server.read_path_blocks(0)

    assert blocks == ["a", "b", "c"]


def test_write_path_overwrites_path() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.write_path(
        leaf=0,
        buckets=[
            ["root"],
            ["middle"],
            ["leaf"],
        ],
    )

    assert server.bucket_blocks(1) == ["root"]
    assert server.bucket_blocks(2) == ["middle"]
    assert server.bucket_blocks(4) == ["leaf"]


def test_write_path_rejects_wrong_number_of_buckets() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    with pytest.raises(ValueError):
        server.write_path(
            leaf=0,
            buckets=[
                ["root"],
                ["middle"],
            ],
        )


def test_write_path_rejects_overfull_bucket() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    with pytest.raises(BucketFullError):
        server.write_path(
            leaf=0,
            buckets=[
                ["root"],
                ["middle-1", "middle-2", "middle-3"],
                ["leaf"],
            ],
        )


def test_physical_trace_records_read_path() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.read_path(3)

    assert server.physical_trace() == [1, 3, 7]


def test_physical_trace_records_write_path() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.write_path(
        leaf=1,
        buckets=[
            [],
            [],
            [],
        ],
    )

    assert server.physical_trace() == [1, 2, 5]


def test_clear_physical_trace() -> None:
    server = BinaryTreeServer[str](height=2, bucket_capacity=2)

    server.read_path(0)
    server.clear_trace()

    assert server.physical_trace() == []
    