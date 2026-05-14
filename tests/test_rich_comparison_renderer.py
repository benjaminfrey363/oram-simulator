import pytest

pytest.importorskip("rich")

from rich.panel import Panel

from oram_sim.comparison import build_comparison_frames
from oram_sim.rich_comparison_renderer import rich_comparison_frame
from oram_sim.workload import Read


def test_rich_comparison_profile_frame_returns_panel() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    renderable = rich_comparison_frame(frames[0])

    assert isinstance(renderable, Panel)


def test_rich_comparison_initial_frame_builds_renderable() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    renderable = rich_comparison_frame(frames[1])

    assert renderable is not None


def test_rich_comparison_operation_frame_builds_renderable() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    renderable = rich_comparison_frame(frames[2])

    assert renderable is not None
    