from oram_sim.graphviz_renderer import (
    access_snapshot_to_dot,
    snapshot_to_dot,
    write_dot_file,
)
from oram_sim.path_oram import PathORAM


def test_snapshot_to_dot_contains_graph_declaration() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    dot = snapshot_to_dot(oram.state_snapshot())

    assert "digraph ORAMTree" in dot
    assert "b1" in dot
    assert "b2" in dot
    assert "b3" in dot


def test_snapshot_to_dot_contains_bucket_labels() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    dot = snapshot_to_dot(oram.state_snapshot())

    assert "bucket 1" in dot
    assert "bucket 7" in dot


def test_snapshot_to_dot_contains_edges() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    dot = snapshot_to_dot(oram.state_snapshot())

    assert "b1 -> b2" in dot
    assert "b1 -> b3" in dot
    assert "b2 -> b4" in dot
    assert "b3 -> b7" in dot


def test_snapshot_to_dot_highlights_path() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = oram.state_snapshot(highlighted_buckets=[1, 3, 7])
    dot = snapshot_to_dot(snapshot)

    assert 'b1 [label=' in dot
    assert 'color="#cc0000"' in dot
    assert 'penwidth="3"' in dot


def test_snapshot_to_dot_can_show_values() -> None:
    oram = PathORAM(["a", "b"], bucket_capacity=2, height=1, seed=0)

    dot = snapshot_to_dot(oram.state_snapshot(), show_values=True)

    assert "B0@L" in dot
    assert "=a" in dot or "=b" in dot


def test_access_snapshot_to_dot_contains_phase_title() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    snapshot = next(oram.read_snapshots(2))
    dot = access_snapshot_to_dot(snapshot)

    assert "Before access" in dot
    assert "logical block 2" in dot
    assert "old leaf" in dot


def test_write_dot_file(tmp_path) -> None:
    output_path = tmp_path / "tree.dot"

    written = write_dot_file("digraph Test {}", output_path)

    assert written == output_path
    assert output_path.read_text(encoding="utf-8") == "digraph Test {}"
    