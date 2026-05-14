from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence, cast

from oram_sim.comparison import ComparisonFrame, build_comparison_frames
from oram_sim.experiments import (
    format_seed_sweep_report,
    run_path_oram_mixed_seed_sweep,
    run_path_oram_mixed_workload,
)
from oram_sim.path_oram import PathORAM
from oram_sim.plotting import (
    max_stash_size_series_from_seed_sweep,
    save_max_stash_size_boxplot,
    save_stash_size_comparison_plot,
    stash_size_phase_series_from_mixed_result,
)
from oram_sim.viewer import (
    ViewerFrame,
    build_viewer_frames,
    parse_viewer_command,
    viewer_help_text,
)
from oram_sim.workload_profiles import (
    WorkloadMode,
    WorkloadProfile,
    build_workload_profile,
    format_workload_profile,
    parse_hot_blocks,
)


WORKLOAD_MODES = ["repeated", "sequential", "random", "hotspot", "mixed"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oram-sim",
        description="ORAM simulator command-line interface.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    view_path = subparsers.add_parser(
        "view-path",
        help="Interactive Path ORAM step-by-step viewer.",
    )
    _add_workload_arguments(view_path)
    _add_oram_arguments(view_path)
    _add_viewer_arguments(view_path)
    view_path.set_defaults(handler=_run_path_viewer)

    compare = subparsers.add_parser(
        "compare",
        help="Interactive NaiveStorage vs PathORAM comparison viewer.",
    )
    _add_workload_arguments(compare)
    _add_oram_arguments(compare)
    _add_viewer_arguments(compare)
    compare.set_defaults(handler=_run_comparison_viewer)

    plot_stash = subparsers.add_parser(
        "plot-stash",
        help="Plot stash size by access phase for one workload.",
    )
    _add_workload_arguments(plot_stash)
    _add_oram_arguments(plot_stash)
    plot_stash.add_argument(
        "--output",
        type=Path,
        default=Path("plots/stash-size-by-phase.png"),
        help="Output image path.",
    )
    plot_stash.set_defaults(handler=_run_plot_stash)

    seed_sweep = subparsers.add_parser(
        "seed-sweep",
        help="Run a many-seed max-stash-size experiment.",
    )
    _add_workload_arguments(seed_sweep)
    _add_oram_arguments(seed_sweep)
    seed_sweep.add_argument(
        "--seeds",
        type=int,
        default=50,
        help="Number of ORAM random seeds to test.",
    )
    seed_sweep.add_argument(
        "--seed-start",
        type=int,
        default=0,
        help="First ORAM random seed.",
    )
    seed_sweep.add_argument(
        "--output",
        type=Path,
        default=Path("plots/max-stash-size-seed-sweep.png"),
        help="Output plot path.",
    )
    seed_sweep.set_defaults(handler=_run_seed_sweep)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.handler(args)
    except ValueError as exc:
        parser.error(str(exc))

    return 0


def _add_workload_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "mode",
        nargs="?",
        default="mixed",
        choices=WORKLOAD_MODES,
        help="Workload mode.",
    )

    parser.add_argument(
        "--n-blocks",
        type=int,
        default=8,
        help="Number of logical blocks.",
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
        help="Workload random seed and default ORAM seed.",
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


def _add_oram_arguments(parser: argparse.ArgumentParser) -> None:
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


def _add_viewer_arguments(parser: argparse.ArgumentParser) -> None:
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


def _build_profile(args: argparse.Namespace) -> WorkloadProfile:
    mode = cast(WorkloadMode, args.mode)
    hot_blocks = parse_hot_blocks(args.hot_blocks)

    return build_workload_profile(
        mode=mode,
        n_blocks=args.n_blocks,
        length=args.length,
        seed=args.seed,
        block_id=args.block_id,
        hot_blocks=hot_blocks,
        hot_probability=args.hot_probability,
    )


def _initial_values(n_blocks: int) -> list[str]:
    return [f"value-{i}" for i in range(n_blocks)]


def _run_path_viewer(args: argparse.Namespace) -> None:
    from rich.console import Console

    profile = _build_profile(args)
    console = Console()

    oram = PathORAM(
        initial_values=_initial_values(args.n_blocks),
        bucket_capacity=args.bucket_capacity,
        height=args.height,
        seed=args.seed,
    )

    frames = build_viewer_frames(
        oram=oram,
        operations=profile.operations,
        profile_text=format_workload_profile(profile),
    )

    _run_viewer_loop(
        console=console,
        frames=frames,
        render_frame=_render_path_frame,
        show_values=bool(args.show_values),
        clear=not args.no_clear,
    )


def _run_comparison_viewer(args: argparse.Namespace) -> None:
    from rich.console import Console

    profile = _build_profile(args)
    console = Console()

    frames = build_comparison_frames(
        initial_values=_initial_values(args.n_blocks),
        operations=profile.operations,
        profile_text=format_workload_profile(profile),
        bucket_capacity=args.bucket_capacity,
        height=args.height,
        seed=args.seed,
    )

    _run_viewer_loop(
        console=console,
        frames=frames,
        render_frame=_render_comparison_frame,
        show_values=bool(args.show_values),
        clear=not args.no_clear,
    )


def _run_plot_stash(args: argparse.Namespace) -> None:
    profile = _build_profile(args)

    result = run_path_oram_mixed_workload(
        initial_values=_initial_values(args.n_blocks),
        operations=profile.operations,
        bucket_capacity=args.bucket_capacity,
        height=args.height,
        seed=args.seed,
    )

    series_list = stash_size_phase_series_from_mixed_result(
        name=profile.mode,
        result=result,
    )

    output_path = save_stash_size_comparison_plot(
        series_list=series_list,
        output_path=args.output,
        title=f"Path ORAM stash size by phase ({profile.mode})",
    )

    print(f"Wrote {output_path}")
    print(f"Max stash size: {result.max_stash_size}")
    print(f"Final stash size: {result.final_stash_size}")
    print(f"Invariant holds: {result.invariant_holds}")


def _run_seed_sweep(args: argparse.Namespace) -> None:
    profile = _build_profile(args)

    if args.seeds <= 0:
        raise ValueError("--seeds must be positive")

    seeds = list(range(args.seed_start, args.seed_start + args.seeds))

    result = run_path_oram_mixed_seed_sweep(
        initial_values=_initial_values(args.n_blocks),
        operations=profile.operations,
        seeds=seeds,
        workload_name=profile.mode,
        bucket_capacity=args.bucket_capacity,
        height=args.height,
    )

    print(format_seed_sweep_report(result))

    series = max_stash_size_series_from_seed_sweep(result)

    output_path = save_max_stash_size_boxplot(
        series_list=[series],
        output_path=args.output,
        title=f"Max stash size over {args.seeds} seeds ({profile.mode})",
    )

    print()
    print(f"Wrote {output_path}")


def _run_viewer_loop(
    console,
    frames,
    render_frame,
    show_values: bool,
    clear: bool,
) -> None:
    frame_index = 0

    while True:
        frame = frames[frame_index]

        _render_screen(
            console=console,
            frame=frame,
            frame_index=frame_index,
            frame_count=len(frames),
            render_frame=render_frame,
            show_values=show_values,
            clear=clear,
        )

        command = parse_viewer_command(
            console.input("[bold bright_black]> [/bold bright_black]")
        )

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
            _show_help(console, clear=clear)
            continue

        if command == "quit":
            break

        console.print("[red]Unknown command. Press h for help.[/red]")


def _render_screen(
    console,
    frame,
    frame_index: int,
    frame_count: int,
    render_frame,
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


def _render_path_frame(
    frame: ViewerFrame[str],
    show_values: bool,
):
    from rich.console import Group
    from rich.panel import Panel
    from rich.text import Text

    from oram_sim.rich_renderer import rich_access_snapshot, rich_state_snapshot

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


def _render_comparison_frame(
    frame: ComparisonFrame[str],
    show_values: bool,
):
    from oram_sim.rich_comparison_renderer import rich_comparison_frame

    return rich_comparison_frame(
        frame,
        show_values=show_values,
    )


def _show_help(console, clear: bool) -> None:
    from rich.panel import Panel

    if clear:
        console.clear()

    console.rule("[bold]Help[/bold]")
    console.print()
    console.print(Panel(viewer_help_text(), title="Interactive controls"))
    console.print()
    console.input("[bold bright_black]Press Enter to return...[/bold bright_black]")


if __name__ == "__main__":
    sys.exit(main())
    