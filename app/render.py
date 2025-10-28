from __future__ import annotations

import io
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

try:
    from .transforms import TrackingMetadata  # type: ignore
except ImportError:
    from transforms import TrackingMetadata

CLIP_DURATION_SECONDS = 10.0


class ClipRenderingError(Exception):
    """Raised when clip rendering fails."""


@dataclass(frozen=True)
class RenderResult:
    payload: bytes
    mime_type: str
    extension: str
    file_name: str
    preview_component: str
    preview_image: Optional[np.ndarray] = None


def render_clip(
    frames: Iterable[Dict[str, Any]],
    metadata: TrackingMetadata,
    fps: float,
    output_format: str = "gif",
    image_size: Tuple[int, int] = (960, 600),
) -> RenderResult:
    frames_list = list(frames)
    if not frames_list:
        raise ClipRenderingError("No frames provided.")

    if fps <= 0:
        raise ClipRenderingError("FPS must be greater than zero.")

    # Convert each frame payload to a rendered image upfront so both GIF and MP4 writers share the same data.
    frame_arrays: List[np.ndarray] = [
        np.asarray(_frame_to_image(frame, metadata, image_size=image_size))
        for frame in frames_list
    ]

    output_format = output_format.lower()

    if output_format == "gif":
        buffer = io.BytesIO()
        duration = 1.0 / fps
        imageio.mimsave(buffer, frame_arrays, format="GIF", duration=duration)
        mime_type = "image/gif"
        extension = "gif"
        preview_component = "image"
        preview_image = frame_arrays[0]
    elif output_format == "mp4":
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
            temp_path = tmp.name
        try:
            with imageio.get_writer(
                temp_path,
                format="FFMPEG",
                mode="I",
                fps=fps,
                codec="libx264",
                quality=8,
            ) as writer:
                for array in frame_arrays:
                    writer.append_data(array)
            with open(temp_path, "rb") as file_obj:
                payload = file_obj.read()
        finally:
            try:
                import os

                os.remove(temp_path)
            except OSError:
                pass
        mime_type = "video/mp4"
        extension = "mp4"
        preview_component = "video"
        preview_image = None
    else:
        raise ClipRenderingError(f"Unsupported output format: {output_format}")

    start_frame = frames_list[0].get("frame", 0)
    end_frame = frames_list[-1].get("frame", start_frame)
    file_name = f"clip_{metadata.match_id}_{start_frame}-{end_frame}.{extension}"

    if output_format == "gif":
        buffer.seek(0)
        payload = buffer.getvalue()

    return RenderResult(
        payload=payload,
        mime_type=mime_type,
        extension=extension,
        file_name=file_name,
        preview_component=preview_component,
        preview_image=preview_image,
    )


def _frame_to_image(
    frame: Dict[str, Any],
    metadata: TrackingMetadata,
    image_size: Tuple[int, int],
) -> Image.Image:
    img = Image.new("RGB", image_size, "#0B641D")
    draw = ImageDraw.Draw(img)

    # Compose the frame by layering pitch, players, ball, and overlay text.
    _draw_pitch(draw, metadata, image_size)
    _draw_players(draw, frame.get("home_players", []), metadata, image_size, "#3498DB")
    _draw_players(draw, frame.get("away_players", []), metadata, image_size, "#E74C3C")
    _draw_ball(draw, frame.get("ball"), metadata, image_size)
    _draw_timestamp(draw, frame, image_size)

    return img


def _draw_pitch(
    draw: ImageDraw.ImageDraw,
    metadata: TrackingMetadata,
    image_size: Tuple[int, int],
) -> None:
    length = metadata.pitch_length
    width = metadata.pitch_width

    margin = 20
    frame = (
        margin,
        margin,
        image_size[0] - margin,
        image_size[1] - margin,
    )
    draw.rectangle(frame, outline="#FFFFFF", width=3)

    mid_x = (frame[0] + frame[2]) / 2
    draw.line([(mid_x, frame[1]), (mid_x, frame[3])], fill="#FFFFFF", width=2)

    # Center circle approximation scaled to match real-world dimensions.
    circle_radius = _scale_x(9.15, length, image_size[0] - 2 * margin)
    center = ((frame[0] + frame[2]) / 2, (frame[1] + frame[3]) / 2)
    draw.ellipse(
        [
            (center[0] - circle_radius, center[1] - circle_radius),
            (center[0] + circle_radius, center[1] + circle_radius),
        ],
        outline="#FFFFFF",
        width=2,
    )


def _draw_players(
    draw: ImageDraw.ImageDraw,
    players: List[Dict[str, Any]],
    metadata: TrackingMetadata,
    image_size: Tuple[int, int],
    color: str,
) -> None:
    for player in players:
        x = player.get("x")
        y = player.get("y")
        if x is None or y is None:
            continue
        # Project metric coordinates onto the 2D canvas and draw a colored marker.
        px, py = _project_to_image(
            x,
            y,
            metadata.pitch_length,
            metadata.pitch_width,
            image_size,
        )
        radius = 10
        draw.ellipse(
            [(px - radius, py - radius), (px + radius, py + radius)],
            fill=color,
            outline="#FFFFFF",
            width=2,
        )


def _draw_ball(
    draw: ImageDraw.ImageDraw,
    ball: Optional[Dict[str, Any]],
    metadata: TrackingMetadata,
    image_size: Tuple[int, int],
) -> None:
    if not ball:
        return
    x = ball.get("x")
    y = ball.get("y")
    if x is None or y is None:
        return
    # Render the ball as a smaller marker to distinguish it from players.
    px, py = _project_to_image(
        x,
        y,
        metadata.pitch_length,
        metadata.pitch_width,
        image_size,
    )
    radius = 6
    draw.ellipse(
        [(px - radius, py - radius), (px + radius, py + radius)],
        fill="#F1C40F",
        outline="#2C3E50",
        width=2,
    )


def _draw_timestamp(
    draw: ImageDraw.ImageDraw,
    frame: Dict[str, Any],
    image_size: Tuple[int, int],
) -> None:
    timestamp = frame.get("timestamp")
    frame_id = frame.get("frame")
    text = f"t={timestamp:.1f}s | frame={frame_id}" if timestamp is not None else f"frame={frame_id}"
    draw.text((24, 20), text, fill="#FFFFFF")


def _project_to_image(
    x: float,
    y: float,
    pitch_length: float,
    pitch_width: float,
    image_size: Tuple[int, int],
) -> Tuple[float, float]:
    margin = 20
    usable_width = image_size[0] - (2 * margin)
    usable_height = image_size[1] - (2 * margin)

    px = (x + pitch_length / 2) / pitch_length
    py = (y + pitch_width / 2) / pitch_width

    px = min(max(px, 0.0), 1.0)
    py = min(max(py, 0.0), 1.0)

    # Translate normalized field coordinates into pixel positions, top-left origin.
    px = margin + px * usable_width
    py = margin + (1 - py) * usable_height

    return px, py


def _scale_x(distance: float, pitch_length: float, canvas_length: float) -> float:
    return (distance / pitch_length) * canvas_length
