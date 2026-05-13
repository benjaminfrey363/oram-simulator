from oram_sim.analysis import format_summary, summarize_physical_trace
from oram_sim.tree import BinaryTreeServer


def main() -> None:
    server = BinaryTreeServer[str](height=3, bucket_capacity=2)

    print("Tree parameters:")
    print(f"  height:          {server.height}")
    print(f"  leaves:          {server.num_leaves}")
    print(f"  buckets:         {server.num_buckets}")
    print(f"  bucket capacity: {server.bucket_capacity}")
    print()

    for leaf in [0, 3, 7, 3]:
        path = server.path_bucket_indices(leaf)
        print(f"leaf {leaf} path: {path}")
        server.read_path(leaf)

    print()
    print("server-visible physical trace:")
    print(server.physical_trace())
    print()
    print(format_summary(summarize_physical_trace(server.physical_trace())))


if __name__ == "__main__":
    main()
    