from __future__ import annotations

import argparse

from rich.console import Console, Group
from rich.panel import Panel
from rich.text import Text

from oram_sim.path_oram import PathORAM
from oram_sim.rich_renderer import rich_access_snapshot, rich_state_snapshot
from oram_sim.viewer import (
    ViewerFrame,
    build_viewer_frames,
    parse_viewer_command,
    viewer_help_text,
)
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
        help="Do not clear the terminal between frames.",
    )

    return parser


def render_frame(
    frame: ViewerFrame[str],
    show_values: bool,
):
    if frame.kind == "profile":
        return Panel(
            frame.profile_text or "",
            title="Workload profile",
            border_style="cyan",
        )

    if frame.kind == "state":
        if frame.state_snapshot is None:
            raise RuntimeError("state frame is missing state_snapshot")

        return rich_state_snapshot(
            frame.state_snapshot,
            show_values=show_values,
        )

    if frame.kind == "access":
        if frame.access_snapshot is None:
            raise RuntimeError("access frame is missing access_snapshot")

        renderable = rich_access_snapshot(
            frame.access_snapshot,
            show_values=show_values,
        )

        if frame.note is None:
            return renderable

        return Group(
            renderable,
            Text(""),
            Panel(
                Text(frame.note),
                title="Note",
                border_style="yellow",
            ),
        )

    raise RuntimeError(f"unsupported frame kind: {frame.kind}")


def render_screen(
    console: Console,
    frame: ViewerFrame[str],
    frame_index: int,
    frame_count: int,
    show_values: bool,
    clear: bool,
) -> None:
    if clear:
        console.clear()

    values_text = "on" if show_values else "off"

    console.rule(
        f"[bold]{frame.title}[/bold] "
        f"[bright_black]({frame_index + 1}/{frame_count}, values {values_text})[/bright_black]"
    )
    console.print()
    console.print(render_frame(frame, show_values=show_values))
    console.print()
    console.print(
        "[bright_black]Controls: Enter/n next · b previous · v toggle values · "
        "h help · q quit[/bright_black]"
    )


def prompt_command(console: Console) -> str:
    return console.input("[bold bright_black]> [/bold bright_black]")


def show_help(console: Console, clear: bool) -> None:
    if clear:
        console.clear()

    console.rule("[bold]Help[/bold]")
    console.print()
    console.print(Panel(viewer_help_text(), title="Interactive controls"))
    console.print()
    console.input("[bold bright_black]Press Enter to return...[/bold bright_black]")


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

    frames = build_viewer_frames(
        oram=oram,
        operations=profile.operations,
        profile_text=format_workload_profile(profile),
    )

    clear = not args.no_clear
    show_values = bool(args.show_values)
    frame_index = 0

    while True:
        render_screen(
            console=console,
            frame=frames[frame_index],
            frame_index=frame_index,
            frame_count=len(frames),
            show_values=show_values,
            clear=clear,
        )

        command = parse_viewer_command(prompt_command(console))

        if command == "next":
            if frame_index < len(frames) - 1:
                frame_index += 1
            continue

        if command == "previous":
            if frame_index > 0:
                frame_index -= 1
            continue

        if command == "toggle_values":
            show_values = not show_values
            continue

        if command == "help":
            show_help(console, clear=clear)
            continue

        if command == "quit":
            break

        console.print("[red]Unknown command. Press h for help.[/red]")


if __name__ == "__main__":
    main()
    