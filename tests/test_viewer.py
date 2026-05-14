from oram_sim.path_oram import PathORAM
from oram_sim.viewer import (
    build_viewer_frames,
    parse_viewer_command,
    viewer_help_text,
)
from oram_sim.workload import Read, Write


def test_parse_viewer_command_next() -> None:
    assert parse_viewer_command("") == "next"
    assert parse_viewer_command("n") == "next"
    assert parse_viewer_command("next") == "next"


def test_parse_viewer_command_previous() -> None:
    assert parse_viewer_command("b") == "previous"
    assert parse_viewer_command("p") == "previous"
    assert parse_viewer_command("previous") == "previous"


def test_parse_viewer_command_quit() -> None:
    assert parse_viewer_command("q") == "quit"
    assert parse_viewer_command("quit") == "quit"


def test_parse_viewer_command_toggle_values() -> None:
    assert parse_viewer_command("v") == "toggle_values"
    assert parse_viewer_command("values") == "toggle_values"


def test_parse_viewer_command_help() -> None:
    assert parse_viewer_command("h") == "help"
    assert parse_viewer_command("?") == "help"


def test_parse_viewer_command_unknown_stays() -> None:
    assert parse_viewer_command("unknown") == "stay"


def test_viewer_help_text_contains_controls() -> None:
    text = viewer_help_text()

    assert "Enter" in text
    assert "previous" in text
    assert "toggle values" in text
    assert "quit" in text


def test_build_viewer_frames_for_one_read() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    frames = build_viewer_frames(
        oram=oram,
        operations=[Read(2)],
        profile_text="test profile",
    )

    # profile + initial + 4 access phases + final
    assert len(frames) == 7

    assert frames[0].kind == "profile"
    assert frames[1].kind == "state"
    assert [frame.kind for frame in frames[2:6]] == [
        "access",
        "access",
        "access",
        "access",
    ]
    assert frames[-1].kind == "state"


def test_build_viewer_frames_for_mixed_workload() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    frames = build_viewer_frames(
        oram=oram,
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        profile_text="test profile",
    )

    # profile + initial + 3 operations * 4 phases + final
    assert len(frames) == 15
    assert frames[-1].state_snapshot is not None
    assert frames[-1].state_snapshot.invariant_holds


def test_build_viewer_frames_adds_notes_for_intermediate_phases() -> None:
    oram = PathORAM(["a", "b", "c", "d"], bucket_capacity=2, height=2, seed=0)

    frames = build_viewer_frames(
        oram=oram,
        operations=[Read(2)],
        profile_text="test profile",
    )

    notes = [frame.note for frame in frames if frame.note is not None]

    assert any("path blocks have been copied" in note for note in notes)
    assert any("new leaf assignment" in note for note in notes)
    