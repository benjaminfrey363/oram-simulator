import pytest

pytest.importorskip("rich")

from rich.panel import Panel
from rich.tree import Tree

from oram_sim.path_oram import PathORAM
from oram_sim.rich_renderer import (
    rich_access_metadata,
    rich_access_snapshot,
    rich_position_map,
    rich_state_snapshot,
    rich_stash,
    rich_trace_panel,
    rich_tree_snapshot,
)


def test_rich_tree_snapshot_returns_tree() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    tree = rich_tree_snapshot(oram.state_snapshot())

    assert isinstance(tree, Tree)


def test_rich_access_metadata_returns_panel() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = next(oram.read_snapshots(2))
    panel = rich_access_metadata(snapshot)

    assert isinstance(panel, Panel)


def test_rich_position_map_returns_table() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    table = rich_position_map(oram.state_snapshot())

    assert table.title == "Position map"


def test_rich_stash_returns_table() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    table = rich_stash(oram.state_snapshot())

    assert table.title == "Stash"


def test_rich_trace_panel_returns_panel() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    panel = rich_trace_panel(oram.state_snapshot())

    assert isinstance(panel, Panel)


def test_rich_access_snapshot_builds_renderable() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = next(oram.read_snapshots(2))
    renderable = rich_access_snapshot(snapshot)

    assert renderable is not None


def test_rich_state_snapshot_builds_renderable() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    renderable = rich_state_snapshot(oram.state_snapshot())

    assert renderable is not None
    