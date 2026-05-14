from oram_sim.cli import build_parser


def test_cli_parser_view_path_defaults() -> None:
    parser = build_parser()

    args = parser.parse_args(["view-path"])

    assert args.command == "view-path"
    assert args.mode == "mixed"
    assert args.n_blocks == 8
    assert args.length == 6


def test_cli_parser_view_path_custom_options() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "view-path",
            "random",
            "--n-blocks",
            "16",
            "--height",
            "4",
            "--length",
            "10",
            "--seed",
            "3",
            "--show-values",
        ]
    )

    assert args.command == "view-path"
    assert args.mode == "random"
    assert args.n_blocks == 16
    assert args.height == 4
    assert args.length == 10
    assert args.seed == 3
    assert args.show_values


def test_cli_parser_compare() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "compare",
            "repeated",
            "--length",
            "5",
            "--block-id",
            "2",
        ]
    )

    assert args.command == "compare"
    assert args.mode == "repeated"
    assert args.length == 5
    assert args.block_id == 2


def test_cli_parser_plot_stash() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "plot-stash",
            "mixed",
            "--output",
            "plots/example.png",
        ]
    )

    assert args.command == "plot-stash"
    assert args.mode == "mixed"
    assert str(args.output) == "plots/example.png"


def test_cli_parser_seed_sweep() -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            "seed-sweep",
            "random",
            "--seeds",
            "20",
            "--seed-start",
            "10",
        ]
    )

    assert args.command == "seed-sweep"
    assert args.mode == "random"
    assert args.seeds == 20
    assert args.seed_start == 10
    