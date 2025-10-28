from __future__ import annotations

import math
from typing import Dict, List

import streamlit as st

try:
    from .loaders import load_skillcorner_tracking  # type: ignore
    from .render import (  # type: ignore
        CLIP_DURATION_SECONDS,
        ClipRenderingError,
        RenderResult,
        render_clip,
    )
    from .transforms import (  # type: ignore
        TrackingMetadata,
        build_metadata,
        dataset_to_frame_payloads,
    )
except ImportError:
    from loaders import load_skillcorner_tracking
    from render import (
        CLIP_DURATION_SECONDS,
        ClipRenderingError,
        RenderResult,
        render_clip,
    )
    from transforms import (
        TrackingMetadata,
        build_metadata,
        dataset_to_frame_payloads,
    )


@st.cache_resource(show_spinner=True)
def _get_dataset(
    match_id: str,
    include_empty_frames: bool,
):
    # Fetch the SkillCorner dataset once per match/settings combination and reuse it.
    return load_skillcorner_tracking(
        match_id=match_id,
        sample_rate=None,
        include_empty_frames=include_empty_frames,
    )


@st.cache_data(show_spinner=True)
def _get_payload(
    match_id: str,
    include_empty_frames: bool,
):
    # Build frame payloads and metadata derived from the cached dataset.
    dataset = _get_dataset(
        match_id=match_id,
        include_empty_frames=include_empty_frames,
    )
    frames = dataset_to_frame_payloads(dataset)
    metadata = build_metadata(dataset, match_id=match_id)
    return frames, metadata


def _ensure_session_state() -> None:
    # Maintain session keys used to track the active clip window and match context.
    if "clip_window" not in st.session_state:
        st.session_state["clip_window"] = {"start": None, "end": None}
    if "active_match" not in st.session_state:
        st.session_state["active_match"] = None


def _frame_label(frame: Dict[str, float]) -> str:
    timestamp = frame.get("timestamp", 0.0) or 0.0
    frame_id = frame.get("frame", 0)
    mins, secs = divmod(int(timestamp), 60)
    tenths = int((timestamp - math.floor(timestamp)) * 10)
    return f"{mins:02d}:{secs:02d}.{tenths} / Frame {frame_id}"


def _render_tracking_visual(
    frames: List[Dict],
    index: int,
    metadata: TrackingMetadata,
    component_key: str = "tracking_component",
) -> None:
    try:
        from streamlit_soccer import TrackingComponent  # type: ignore
    except ImportError:
        # Fall back to a static Plotly rendering when the custom widget is unavailable.
        _render_plotly_pitch(frames[index], metadata)
        return

    TrackingComponent(
        frames=frames,
        initial_frame=index,
        pitch_dimensions={
            "length": metadata.pitch_length,
            "width": metadata.pitch_width,
        },
        key=component_key,
        autoplay=False,
    )


def _render_plotly_pitch(frame: Dict, metadata: TrackingMetadata) -> None:
    import plotly.graph_objects as go

    length = metadata.pitch_length
    width = metadata.pitch_width

    fig = go.Figure()
    fig.update_layout(
        xaxis=dict(range=[-length / 2, length / 2], visible=False),
        yaxis=dict(range=[-width / 2, width / 2], visible=False, scaleanchor="x"),
        height=600,
        width=900,
        plot_bgcolor="#0B641D",
        paper_bgcolor="#0B641D",
        margin=dict(l=10, r=10, t=10, b=10),
    )

    # Outline the pitch, halfway line, and center circle so players have spatial reference.
    fig.add_shape(
        type="rect",
        x0=-length / 2,
        y0=-width / 2,
        x1=length / 2,
        y1=width / 2,
        line=dict(color="#FFFFFF", width=2),
    )
    fig.add_shape(
        type="line",
        x0=0,
        y0=-width / 2,
        x1=0,
        y1=width / 2,
        line=dict(color="#FFFFFF", width=2),
    )
    fig.add_shape(
        type="circle",
        x0=-9.15,
        y0=-9.15,
        x1=9.15,
        y1=9.15,
        line=dict(color="#FFFFFF", width=2),
    )

    def _scatter(players: List[Dict], color: str, name: str):
        xs = [p["x"] for p in players if p.get("x") is not None]
        ys = [p["y"] for p in players if p.get("y") is not None]
        labels = [p.get("label") or p.get("id") for p in players]
        fig.add_trace(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                text=[str(lab) if lab is not None else "" for lab in labels],
                textposition="bottom center",
                marker=dict(size=14, color=color, opacity=0.9),
                name=name,
            ),
        )

    _scatter(frame.get("home_players", []), "#3498DB", metadata.home_team)
    _scatter(frame.get("away_players", []), "#E74C3C", metadata.away_team)

    ball = frame.get("ball")
    if ball and ball.get("x") is not None and ball.get("y") is not None:
        fig.add_trace(
            go.Scatter(
                x=[ball["x"]],
                y=[ball["y"]],
                mode="markers",
                marker=dict(size=12, color="#F1C40F", symbol="circle"),
                name="Ball",
            ),
        )

    st.plotly_chart(fig, use_container_width=True)


def _reset_clip_window() -> None:
    # Clear any previously marked in/out points.
    st.session_state["clip_window"] = {"start": None, "end": None}


def main() -> None:
    st.set_page_config(
        page_title="US Soccer Tracking Clip Builder",
        layout="wide",
    )
    _ensure_session_state()

    st.title("Tracking Clip Builder")
    st.caption(
        "Scrub through tracking data, mark 0–10 second windows, and export clips for analysis.",
    )

    with st.sidebar:
        st.header("Data Source")
        match_id = st.text_input("SkillCorner match id", value="2221637")
        include_empty_frames = st.checkbox(
            "Include dead ball frames",
            value=False,
            help="Include periods where the tracking provider did not detect all actors.",
        )

        load_button = st.button("Load tracking data", type="primary")

        if load_button:
            st.session_state["active_match"] = (
                match_id.strip(),
                include_empty_frames,
            )
            _reset_clip_window()

    active_match = st.session_state.get("active_match")

    if not active_match or not active_match[0]:
        st.info("Enter a SkillCorner match id and load the tracking data to begin.")
        return

    try:
        with st.spinner("Fetching and processing tracking data…"):
            frames, metadata = _get_payload(*active_match)
    except FileNotFoundError as exc:
        st.error(
            "Unable to load the tracking dataset. "
            "Confirm the match id is valid and that you have an active internet connection. "
            f"Details: {exc}",
        )
        st.stop()
    except Exception as exc:  # pragma: no cover - surface to UI
        st.error(f"Unexpected error loading tracking data: {exc}")
        st.stop()

    if not frames:
        st.warning("No frames were returned for this match.")
        return

    frame_count = len(frames)
    frame_rate = metadata.frame_rate
    duration_seconds = frame_count / frame_rate if frame_rate else 0

    st.subheader(
        f"{metadata.home_team} vs {metadata.away_team}",
    )
    info_line = (
        f"{frame_count} frames • {duration_seconds:.1f}s at {frame_rate:.1f} FPS "
        f"• Pitch {metadata.pitch_length}m x {metadata.pitch_width}m"
    )
    st.write(info_line)

    current_frame_index = st.slider(
        "Scrub frames",
        min_value=0,
        max_value=frame_count - 1,
        value=0,
        help="Drag to scrub through the tracking timeline frame-by-frame.",
    )
    current_frame = frames[current_frame_index]

    _render_tracking_visual(frames, current_frame_index, metadata)

    status_line = (
        f"Frame {current_frame_index} | "
        f"{_frame_label(current_frame)} | "
        f"Possession: {current_frame.get('possession_team', 'Unknown')}"
    )
    tooltip = (
        "Frame index reflects the slider position; the middle section shows match time and "
        "provider frame id; possession indicates which team holds the ball if available."
    )
    st.caption(status_line, help=tooltip)

    clip_window = st.session_state["clip_window"]

    col_set_in, col_set_out, col_clear = st.columns([1, 1, 1])
    with col_set_in:
        if st.button("Mark In", use_container_width=True):
            clip_window["start"] = current_frame_index
            if clip_window["end"] is not None and clip_window["end"] < clip_window["start"]:
                clip_window["end"] = None
    with col_set_out:
        if st.button("Mark Out", use_container_width=True):
            clip_window["end"] = current_frame_index
            if clip_window["start"] is not None and clip_window["end"] < clip_window["start"]:
                clip_window["start"] = clip_window["end"]
    with col_clear:
        if st.button("Clear Marks", use_container_width=True):
            _reset_clip_window()
            clip_window = st.session_state["clip_window"]

    st.write(
        f"Marked window: "
        f"{clip_window['start'] if clip_window['start'] is not None else '—'} → "
        f"{clip_window['end'] if clip_window['end'] is not None else '—'}",
    )

    clip_len_seconds = None
    renderable = False
    if clip_window["start"] is not None and clip_window["end"] is not None:
        start = clip_window["start"]
        end = clip_window["end"]
        if end < start:
            # Normalize the window if the user marked OUT before IN.
            start, end = end, start
            clip_window["start"], clip_window["end"] = start, end
        total_frames = (end - start) + 1
        clip_len_seconds = total_frames / frame_rate
        renderable = clip_len_seconds <= CLIP_DURATION_SECONDS
        st.write(
            f"Clip duration: {clip_len_seconds:.2f}s "
            f"({total_frames} frames). Maximum allowed: {CLIP_DURATION_SECONDS}s",
        )

    format_choice = st.selectbox(
        "Clip format",
        options=["gif", "mp4"],
        index=0,
        help="GIF renders quickly in-app; MP4 requires ffmpeg but offers higher quality.",
    )

    if st.button("Render clip", type="primary", disabled=not renderable):
        if clip_window["start"] is None or clip_window["end"] is None:
            st.error("Mark both an IN and OUT point before rendering.")
        elif clip_len_seconds and clip_len_seconds > CLIP_DURATION_SECONDS:
            st.error(
                f"Clip length exceeds {CLIP_DURATION_SECONDS} seconds. "
                "Adjust the OUT point.",
            )
        else:
            start = clip_window["start"]
            end = clip_window["end"]
            selected_frames = frames[start : end + 1]
            try:
                result: RenderResult = render_clip(
                    selected_frames,
                    metadata=metadata,
                    fps=frame_rate,
                    output_format=format_choice,
                )
            except ClipRenderingError as exc:
                st.error(f"Unable to render clip: {exc}")
            else:
                st.success("Clip rendered successfully.")
                st.download_button(
                    label=f"Download clip ({result.extension})",
                    data=result.payload,
                    file_name=result.file_name,
                    mime=result.mime_type,
                )
                if result.preview_component == "video":
                    st.video(result.payload)
                elif result.preview_component == "image":
                    st.image(result.preview_image)


if __name__ == "__main__":
    main()
