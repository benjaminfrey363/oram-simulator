from oram_sim.comparison import build_comparison_frames
from oram_sim.workload import Read, Write


def test_build_comparison_frames_for_one_read() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    assert len(frames) == 4
    assert frames[0].kind == "profile"
    assert frames[1].kind == "initial"
    assert frames[2].kind == "operation"
    assert frames[3].kind == "final"


def test_comparison_frame_records_naive_observation() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2), Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    first_operation = frames[2]
    second_operation = frames[3]

    assert first_operation.naive_observation is not None
    assert second_operation.naive_observation is not None

    assert first_operation.naive_observation.observed_address == 2
    assert first_operation.naive_observation.physical_trace == (2,)

    assert second_operation.naive_observation.observed_address == 2
    assert second_operation.naive_observation.physical_trace == (2, 2)


def test_comparison_frame_records_path_oram_observation() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    operation_frame = frames[2]
    observation = operation_frame.path_oram_observation

    assert observation is not None
    assert 0 <= observation.observed_leaf < 4
    assert len(observation.observed_path) == 3
    assert observation.observed_leaves_so_far == (observation.observed_leaf,)
    assert len(observation.physical_trace) == 6


def test_comparison_read_values_match() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[Read(2)],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    operation_frame = frames[2]

    assert operation_frame.read_values_match is True
    assert operation_frame.naive_observation is not None
    assert operation_frame.path_oram_observation is not None

    assert operation_frame.naive_observation.read_value == "c"
    assert operation_frame.path_oram_observation.read_value == "c"


def test_comparison_write_then_read() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Write(1, "new-b"),
            Read(1),
        ],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    write_frame = frames[2]
    read_frame = frames[3]

    assert write_frame.read_values_match is None
    assert read_frame.read_values_match is True

    assert read_frame.naive_observation is not None
    assert read_frame.path_oram_observation is not None

    assert read_frame.naive_observation.read_value == "new-b"
    assert read_frame.path_oram_observation.read_value == "new-b"


def test_comparison_final_state_invariant_holds() -> None:
    frames = build_comparison_frames(
        initial_values=["a", "b", "c", "d"],
        operations=[
            Read(2),
            Write(1, "new-b"),
            Read(1),
        ],
        profile_text="test profile",
        bucket_capacity=2,
        height=2,
        seed=0,
    )

    final_frame = frames[-1]

    assert final_frame.kind == "final"
    assert final_frame.path_oram_state is not None
    assert final_frame.path_oram_state.invariant_holds
    