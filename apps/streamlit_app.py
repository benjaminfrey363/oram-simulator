from __future__ import annotations

from typing import Any, Sequence, cast

import streamlit as st

from oram_sim.comparison import ComparisonFrame, build_comparison_frames
from oram_sim.graphviz_renderer import access_snapshot_to_dot, snapshot_to_dot
from oram_sim.snapshot import AccessSnapshot, ORAMStateSnapshot
from oram_sim.viewer import ViewerFrame, build_viewer_frames
from oram_sim.workload_profiles import (
    WorkloadMode,
    build_workload_profile,
    format_workload_profile,
    parse_hot_blocks,
)


WORKLOAD_MODES = ["repeated", "sequential", "random", "hotspot", "mixed"]


def main() -> None:
    st.set_page_config(
        page_title="ORAM Simulator",
        layout="wide",
    )

    st.title("ORAM Simulator")
    st.caption(
        "Interactive Path ORAM visualization using the simulator's snapshot objects."
    )

    settings = sidebar_settings()

    try:
        profile = build_workload_profile(
            mode=settings["mode"],
            n_blocks=settings["n_blocks"],
            length=settings["length"],
            seed=settings["seed"],
            block_id=settings["block_id"],
            hot_blocks=settings["hot_blocks"],
            hot_probability=settings["hot_probability"],
        )
    except ValueError as exc:
        st.error(str(exc))
        return

    signature = (
        settings["viewer_kind"],
        settings["mode"],
        settings["n_blocks"],
        settings["height"],
        settings["bucket_capacity"],
        settings["length"],
        settings["seed"],
        settings["block_id"],
        tuple(settings["hot_blocks"]),
        settings["hot_probability"],
    )

    if (
        "frames" not in st.session_state
        or st.session_state.get("signature") != signature
        or st.sidebar.button("Build / reset simulation")
    ):
        frames = build_frames(
            viewer_kind=settings["viewer_kind"],
            profile=profile,
            n_blocks=settings["n_blocks"],
            bucket_capacity=settings["bucket_capacity"],
            height=settings["height"],
            seed=settings["seed"],
        )

        st.session_state.frames = frames
        st.session_state.frame_index = 0
        st.session_state.signature = signature
        st.session_state.show_values = bool(settings["show_values"])

    frames = cast(list[Any], st.session_state.frames)

    if not frames:
        st.warning("No frames to display.")
        return

    render_navigation(frame_count=len(frames))

    frame_index = int(st.session_state.frame_index)
    frame = frames[frame_index]
    show_values = bool(st.session_state.show_values)

    st.divider()
    st.subheader(frame.title)
    st.caption(
        f"Frame {frame_index + 1} of {len(frames)} · "
        f"values {'shown' if show_values else 'hidden'}"
    )

    if settings["viewer_kind"] == "Path ORAM phase viewer":
        render_path_frame(cast(ViewerFrame[str], frame), show_values=show_values)
    else:
        render_comparison_frame(
            cast(ComparisonFrame[str], frame),
            show_values=show_values,
        )


def sidebar_settings() -> dict[str, Any]:
    with st.sidebar:
        st.header("Simulation settings")

        viewer_kind = st.radio(
            "Viewer",
            [
                "Path ORAM phase viewer",
                "NaiveStorage vs PathORAM comparison",
            ],
        )

        mode = cast(
            WorkloadMode,
            st.selectbox(
                "Workload mode",
                WORKLOAD_MODES,
                index=WORKLOAD_MODES.index("mixed"),
            ),
        )

        n_blocks = int(
            st.number_input(
                "Logical blocks",
                min_value=1,
                max_value=128,
                value=8,
                step=1,
            )
        )

        length = int(
            st.number_input(
                "Workload length",
                min_value=0,
                max_value=200,
                value=6,
                step=1,
            )
        )

        bucket_capacity = int(
            st.number_input(
                "Bucket capacity",
                min_value=1,
                max_value=16,
                value=2,
                step=1,
            )
        )

        height_raw = int(
            st.number_input(
                "Tree height (-1 for default)",
                min_value=-1,
                max_value=12,
                value=-1,
                step=1,
            )
        )

        height = None if height_raw < 0 else height_raw

        seed = int(
            st.number_input(
                "Seed",
                min_value=0,
                max_value=1_000_000,
                value=0,
                step=1,
            )
        )

        block_id = int(
            st.number_input(
                "Repeated-mode block id",
                min_value=0,
                max_value=max(0, n_blocks - 1),
                value=min(3, max(0, n_blocks - 1)),
                step=1,
            )
        )

        hot_blocks_text = st.text_input(
            "Hotspot blocks",
            value="1,2,3",
        )

        hot_probability = float(
            st.slider(
                "Hot probability",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.05,
            )
        )

        show_values = st.checkbox(
            "Show block values",
            value=False,
        )

    hot_blocks = parse_hot_blocks(hot_blocks_text)

    return {
        "viewer_kind": viewer_kind,
        "mode": mode,
        "n_blocks": n_blocks,
        "length": length,
        "bucket_capacity": bucket_capacity,
        "height": height,
        "seed": seed,
        "block_id": block_id,
        "hot_blocks": hot_blocks,
        "hot_probability": hot_probability,
        "show_values": show_values,
    }


def build_frames(
    viewer_kind: str,
    profile,
    n_blocks: int,
    bucket_capacity: int,
    height: int | None,
    seed: int,
):
    initial_values = [f"value-{i}" for i in range(n_blocks)]

    profile_text = format_workload_profile(profile)

    if viewer_kind == "Path ORAM phase viewer":
        from oram_sim.path_oram import PathORAM

        oram = PathORAM(
            initial_values=initial_values,
            bucket_capacity=bucket_capacity,
            height=height,
            seed=seed,
        )

        return build_viewer_frames(
            oram=oram,
            operations=profile.operations,
            profile_text=profile_text,
        )

    return build_comparison_frames(
        initial_values=initial_values,
        operations=profile.operations,
        profile_text=profile_text,
        bucket_capacity=bucket_capacity,
        height=height,
        seed=seed,
    )


def render_navigation(frame_count: int) -> None:
    previous_col, next_col, reset_col, values_col = st.columns(4)

    with previous_col:
        if st.button("Previous", use_container_width=True):
            st.session_state.frame_index = max(
                0,
                int(st.session_state.frame_index) - 1,
            )

    with next_col:
        if st.button("Next", use_container_width=True):
            st.session_state.frame_index = min(
                frame_count - 1,
                int(st.session_state.frame_index) + 1,
            )

    with reset_col:
        if st.button("Reset to first frame", use_container_width=True):
            st.session_state.frame_index = 0

    with values_col:
        if st.button("Toggle values", use_container_width=True):
            st.session_state.show_values = not bool(st.session_state.show_values)


def render_path_frame(frame: ViewerFrame[str], show_values: bool) -> None:
    if frame.kind == "profile":
        st.info(frame.profile_text or "")
        return

    if frame.kind == "state":
        if frame.state_snapshot is None:
            st.error("State frame is missing its snapshot.")
            return

        render_state_snapshot(
            frame.state_snapshot,
            title=frame.title,
            show_values=show_values,
        )
        return

    if frame.kind == "access":
        if frame.access_snapshot is None:
            st.error("Access frame is missing its snapshot.")
            return

        render_access_snapshot(
            frame.access_snapshot,
            show_values=show_values,
        )

        if frame.note is not None:
            st.warning(frame.note)

        return

    st.error(f"Unsupported frame kind: {frame.kind}")


def render_comparison_frame(
    frame: ComparisonFrame[str],
    show_values: bool,
) -> None:
    if frame.kind == "profile":
        st.info(frame.profile_text or "")
        return

    if frame.kind in {"initial", "final"}:
        if frame.path_oram_state is None:
            st.error("Comparison state frame is missing Path ORAM state.")
            return

        render_state_snapshot(
            frame.path_oram_state,
            title=frame.title,
            show_values=show_values,
        )
        return

    if frame.kind != "operation":
        st.error(f"Unsupported comparison frame kind: {frame.kind}")
        return

    naive = frame.naive_observation
    path = frame.path_oram_observation

    if naive is None or path is None:
        st.error("Operation comparison frame is incomplete.")
        return

    header_cols = st.columns(3)
    header_cols[0].metric("Operation", frame.operation or "-")
    header_cols[1].metric("Naive observed address", naive.observed_address)
    header_cols[2].metric("Path ORAM observed leaf", path.observed_leaf)

    if frame.read_values_match is True:
        st.success("Read values match.")
    elif frame.read_values_match is False:
        st.error("Read values do not match.")
    else:
        st.caption("Write operation: no read-value comparison.")

    naive_col, path_col = st.columns(2)

    with naive_col:
        st.markdown("### NaiveStorage")
        st.table(
            table_rows(
                [
                    {
                        "Field": "server-visible address",
                        "Value": naive.observed_address,
                    },
                    {
                        "Field": "physical trace so far",
                        "Value": list(naive.physical_trace),
                    },
                    {
                        "Field": "read result",
                        "Value": repr(naive.read_value)
                        if naive.read_value is not None
                        else "-",
                    },
                    {
                        "Field": "leakage story",
                        "Value": "logical id is directly visible",
                    },
                ]
            )
        )

    with path_col:
        st.markdown("### PathORAM")
        st.table(
            table_rows(
                [
                    {
                        "Field": "observed leaf",
                        "Value": path.observed_leaf,
                    },
                    {
                        "Field": "observed path",
                        "Value": list(path.observed_path),
                    },
                    {
                        "Field": "observed leaves so far",
                        "Value": list(path.observed_leaves_so_far),
                    },
                    {
                        "Field": "bucket-index trace",
                        "Value": list(path.physical_trace),
                    },
                    {
                        "Field": "read result",
                        "Value": repr(path.read_value)
                        if path.read_value is not None
                        else "-",
                    },
                    {
                        "Field": "leakage story",
                        "Value": "logical id is hidden behind remapped paths",
                    },
                ]
            )
        )

    st.markdown("### Path ORAM state after operation")
    render_state_snapshot(
        path.final_snapshot.state,
        title="Path ORAM state",
        show_values=show_values,
    )


def render_access_snapshot(
    snapshot: AccessSnapshot[str],
    show_values: bool,
) -> None:
    metadata_col, graph_col = st.columns([1, 2])

    with metadata_col:
        st.markdown("### Access phase")
        st.table(
            table_rows(
                [
                    {"Field": "phase", "Value": snapshot.phase},
                    {"Field": "logical block", "Value": snapshot.logical_id},
                    {"Field": "old leaf", "Value": snapshot.old_leaf},
                    {"Field": "new leaf", "Value": snapshot.new_leaf},
                    {"Field": "path", "Value": list(snapshot.path)},
                    {"Field": "read value", "Value": repr(snapshot.read_value)},
                    {"Field": "stash size", "Value": snapshot.stash_size},
                    {
                        "Field": "invariant holds",
                        "Value": snapshot.state.invariant_holds,
                    },
                    {
                        "Field": "trace so far",
                        "Value": list(snapshot.physical_trace),
                    },
                ]
            )
        )

    with graph_col:
        dot = access_snapshot_to_dot(
            snapshot,
            show_values=show_values,
            show_dummy_ids=False,
        )
        st.graphviz_chart(dot)

    render_state_tables(snapshot.state, show_values=show_values)


def render_state_snapshot(
    snapshot: ORAMStateSnapshot[str],
    title: str,
    show_values: bool,
) -> None:
    graph_col, table_col = st.columns([2, 1])

    with graph_col:
        dot = snapshot_to_dot(
            snapshot,
            title=title,
            show_values=show_values,
            show_dummy_ids=False,
        )
        st.graphviz_chart(dot)

    with table_col:
        st.metric("Invariant holds", str(snapshot.invariant_holds))
        st.metric("Trace length", len(snapshot.physical_trace))
        st.write("Physical trace")
        st.code(str(list(snapshot.physical_trace)))

    render_state_tables(snapshot, show_values=show_values)


def render_state_tables(
    snapshot: ORAMStateSnapshot[str],
    show_values: bool,
) -> None:
    position_col, stash_col = st.columns(2)

    with position_col:
        st.markdown("### Private position map")
        st.table(
            [
                {"Block": logical_id, "Leaf": leaf}
                for logical_id, leaf in sorted(snapshot.position_map.items())
            ]
        )

    with stash_col:
        st.markdown("### Private stash")

        if not snapshot.stash:
            st.info("Stash is empty.")
            return

        rows: list[dict[str, Any]] = []

        for block in sorted(snapshot.stash, key=lambda item: item.logical_id):
            row: dict[str, Any] = {
                "Block": block.logical_id,
                "Leaf": block.leaf,
            }

            if show_values:
                row["Value"] = repr(block.value)

            rows.append(row)

        st.table(rows)


def table_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    """
    Convert Streamlit table row values to strings.

    This avoids PyArrow serialization warnings caused by mixed-type columns.
    """
    return [
        {key: str(value) for key, value in row.items()}
        for row in rows
    ]


if __name__ == "__main__":
    main()
