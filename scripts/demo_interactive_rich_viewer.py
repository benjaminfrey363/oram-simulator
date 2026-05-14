from __future__ import annotations

import argparse

from rich.console import Console
from rich.panel import Panel

from oram_sim.path_oram import PathORAM
from oram_sim.rich_renderer import rich_access_snapshot, rich_state_snapshot
from oram_sim.workload import Read, WorkloadOperation, Write, format_operation
from oram_sim.workload_profiles import (
    WorkloadMode,
    build_workload_profile,
    format_workload_profile,
    parse_hot_blocks,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Interactive step-by-step Path ORAM terminal viewer.",
    )

    parser.add_argument(
        "mode",
        nargs="?",
        default="mixed",
        choices=["repeated", "sequential", "random", "hotspot", "mixed"],
        help="Workload mode to visualize.",
    )

    parser.add_argument(
        "--n-blocks",
        type=int,
        default=8,
        help="Number of logical blocks.",
    )

    parser.add_argument(
        "--height",
        type=int,
        default=None,
        help="Tree height. Defaults to the PathORAM default height.",
    )

    parser.add_argument(
        "--bucket-capacity",
        type=int,
        default=2,
        help="Number of slots per bucket.",
    )

    parser.add_argument(
        "--length",
        type=int,
        default=6,
        help="Number of workload operations.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed.",
    )

    parser.add_argument(
        "--block-id",
        type=int,
        default=3,
        help="Logical block used by repeated mode.",
    )

    parser.add_argument(
        "--hot-blocks",
        type=str,
        default="1,2,3",
        help="Comma-separated hot blocks used by hotspot mode.",
    )

    parser.add_argument(
        "--hot-probability",
        type=float,
        default=0.8,
        help="Probability of selecting a hot block in hotspot mode.",
    )

    parser.add_argument(
        "--show-values",
        action="store_true",
        help="Show stored values in the tree and stash.",
    )

    parser.add_argument(
        "--no-clear",
        action="store_true",
        help="Do not clear the terminal between phases.",
    )

    return parser


def wait_for_enter(console: Console, message: str = "Press Enter to continue...") -> None:
    console.print()
    console.input(f"[bold bright_black]{message}[/bold bright_black]")


def render_screen(
    console: Console,
    title: str,
    renderable,
    clear: bool = True,
) -> None:
    if clear:
        console.clear()

    console.rule(f"[bold]{title}[/bold]")
    console.print()
    console.print(renderable)


def render_profile_summary(
    console: Console,
    profile_text: str,
    clear: bool,
) -> None:
    render_screen(
        console,
        title="Path ORAM interactive viewer",
        renderable=Panel(
            profile_text,
            title="Workload profile",
            border_style="cyan",
        ),
        clear=clear,
    )


def run_operation_snapshots(
    oram: PathORAM[str],
    operation: WorkloadOperation,
):
    if isinstance(operation, Read):
        return oram.read_snapshots(operation.logical_id)

    if isinstance(operation, Write):
        return oram.write_snapshots(operation.logical_id, operation.value)

    raise TypeError(f"Unsupported operation: {operation!r}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    console = Console()

    mode: WorkloadMode = args.mode
    hot_blocks = parse_hot_blocks(args.hot_blocks)

    profile = build_workload_profile(
        mode=mode,
        n_blocks=args.n_blocks,
        length=args.length,
        seed=args.seed,
        block_id=args.block_id,
        hot_blocks=hot_blocks,
        hot_probability=args.hot_probability,
    )

    oram = PathORAM(
        initial_values=[f"value-{i}" for i in range(args.n_blocks)],
        bucket_capacity=args.bucket_capacity,
        height=args.height,
        seed=args.seed,
    )

    clear = not args.no_clear

    render_profile_summary(
        console,
        profile_text=format_workload_profile(profile),
        clear=clear,
    )
    wait_for_enter(console)

    render_screen(
        console,
        title="Initial Path ORAM state",
        renderable=rich_state_snapshot(
            oram.state_snapshot(),
            show_values=args.show_values,
        ),
        clear=clear,
    )
    wait_for_enter(console)

    for query_index, operation in enumerate(profile.operations, start=1):
        operation_label = format_operation(operation)

        for snapshot in run_operation_snapshots(oram, operation):
            render_screen(
                console,
                title=f"Query {query_index}/{profile.operation_count}: {operation_label}",
                renderable=rich_access_snapshot(
                    snapshot,
                    show_values=args.show_values,
                ),
                clear=clear,
            )

            if snapshot.phase == "after_path_read":
                console.print()
                console.print(
                    "[yellow]Debug note:[/yellow] path blocks have been copied "
                    "into the stash, but the server path has not yet been "
                    "rewritten. The placement invariant can be temporarily false."
                )

            if snapshot.phase == "after_remap":
                console.print()
                console.print(
                    "[magenta]Debug note:[/magenta] the target block now has its "
                    "new leaf assignment in the stash. Eviction has not happened yet."
                )

            wait_for_enter(console)

    render_screen(
        console,
        title="Final Path ORAM state",
        renderable=rich_state_snapshot(
            oram.state_snapshot(),
            show_values=args.show_values,
        ),
        clear=clear,
    )

    console.print()
    console.print("[bold green]Done.[/bold green]")


if __name__ == "__main__":
    main()
    