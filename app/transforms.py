from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from kloppy.domain import Team, TrackingDataset

try:
    from kloppy.domain import TeamGround  # type: ignore
except ImportError:  # pragma: no cover
    TeamGround = None


@dataclass(frozen=True)
class TrackingMetadata:
    match_id: str
    home_team: str
    away_team: str
    frame_rate: float
    total_frames: int
    pitch_length: float
    pitch_width: float


def build_metadata(dataset: TrackingDataset, match_id: str) -> TrackingMetadata:
    # Normalize metadata values with fallbacks to handle variations in Kloppy datasets.
    metadata = getattr(dataset, "metadata", None)
    teams: List[Team] = []
    if metadata and getattr(metadata, "teams", None):
        teams = list(metadata.teams)

    pitch = getattr(dataset, "pitch_dimensions", None) or getattr(metadata, "pitch_dimensions", None)

    home_name = teams[0].name if teams else "Home"
    away_name = teams[1].name if len(teams) > 1 else "Away"

    frame_rate = float(getattr(dataset, "frame_rate", 0) or getattr(metadata, "frame_rate", 10))

    pitch_length = _resolve_pitch_length(pitch)
    pitch_width = _resolve_pitch_width(pitch)
    if pitch_length is None:
        pitch_length = 105.0
    if pitch_width is None:
        pitch_width = 68.0

    return TrackingMetadata(
        match_id=match_id,
        home_team=home_name,
        away_team=away_name,
        frame_rate=frame_rate,
        total_frames=len(dataset.frames),
        pitch_length=float(pitch_length),
        pitch_width=float(pitch_width),
    )


def dataset_to_frame_payloads(dataset: TrackingDataset) -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []

    for frame in dataset.frames:
        home_players: List[Dict[str, Any]] = []
        away_players: List[Dict[str, Any]] = []

        player_coordinates = getattr(frame, "players_coordinates", None) or {}
        players_data = getattr(frame, "players_data", None) or {}

        for player, coords in player_coordinates.items():
            if coords is None:
                continue

            player_data = players_data.get(player)
            # Flatten a player's attributes into serializable values the UI can consume.
            player_payload = {
                "id": str(getattr(player, "player_id", getattr(player, "id", ""))),
                "label": getattr(player, "jersey_no", None) or getattr(player, "name", None),
                "name": getattr(player, "name", None),
                "x": getattr(coords, "x", None),
                "y": getattr(coords, "y", None),
                "detected": _player_detected(player_data),
                "speed": getattr(player_data, "speed", None),
            }

            side = _team_side(player.team)
            if side == "home":
                home_players.append(player_payload)
            else:
                away_players.append(player_payload)

        ball_payload = _extract_ball_payload(frame)

        payloads.append(
            {
                "frame": getattr(frame, "frame_id", None) or getattr(frame, "frame", None),
                "timestamp": _timestamp_seconds(getattr(frame, "timestamp", None)),
                "period": _extract_period(frame),
                "home_players": home_players,
                "away_players": away_players,
                "ball": ball_payload,
                "possession_team": _extract_possession(frame),
            },
        )

    return payloads


def _extract_ball_payload(frame: Any) -> Optional[Dict[str, Any]]:
    ball_coords = getattr(frame, "ball_coordinates", None) or getattr(frame, "ball_position", None)
    if not ball_coords:
        return None
    # Keep ball coordinates if provided, preserving optional z-height.
    return {
        "x": getattr(ball_coords, "x", None),
        "y": getattr(ball_coords, "y", None),
        "z": getattr(ball_coords, "z", 0.0),
    }


def _extract_possession(frame: Any) -> Optional[str]:
    # Handle possession annotations that may be dicts, objects, or simple strings.
    possession = getattr(frame, "possession", None)
    if isinstance(possession, dict):
        return possession.get("group") or possession.get("player_id")
    owner = getattr(possession, "team", None)
    if owner is not None:
        return getattr(owner, "name", None)
    owning_team = getattr(frame, "ball_owning_team", None)
    if owning_team is not None:
        return getattr(owning_team, "name", None) if hasattr(owning_team, "name") else str(owning_team)
    return None


def _extract_period(frame: Any) -> Optional[int]:
    period = getattr(frame, "period", None)
    if isinstance(period, int):
        return period
    if hasattr(period, "id"):
        return getattr(period, "id")
    if hasattr(period, "number"):
        return getattr(period, "number")
    return None


def _timestamp_seconds(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, timedelta):
        return value.total_seconds()
    total_seconds = getattr(value, "total_seconds", None)
    if callable(total_seconds):
        return float(total_seconds())
    return None


def _team_side(team: Optional[Team]) -> str:
    if team is None:
        return "away"
    # Determine whether a player belongs to the home or away side across schema variants.
    team_type = getattr(team, "team_type", None) or getattr(team, "ground", None) or getattr(team, "side", None)
    if TeamGround is not None and isinstance(team_type, TeamGround):
        name = getattr(team_type, "name", "").lower()
        if "home" in name:
            return "home"
        if "away" in name:
            return "away"
    if hasattr(team_type, "name"):
        name = getattr(team_type, "name", "")
        if isinstance(name, str):
            lowercase = name.lower()
            if "home" in lowercase:
                return "home"
            if "away" in lowercase:
                return "away"
    if isinstance(team_type, str):
        lowered = team_type.lower()
        if "home" in lowered:
            return "home"
        if "away" in lowered:
            return "away"
    is_home = getattr(team, "is_home", None)
    if isinstance(is_home, bool):
        return "home" if is_home else "away"
    return "away"


def _resolve_pitch_length(pitch: Any) -> Optional[float]:
    if pitch is None:
        return None
    direct = getattr(pitch, "pitch_length", None) or getattr(pitch, "length", None)
    if direct:
        return float(direct)
    x_dim = getattr(pitch, "x_dim", None)
    if x_dim is not None:
        try:
            return float(getattr(x_dim, "max") - getattr(x_dim, "min"))
        except Exception:  # pragma: no cover - fallback
            return None
    return None


def _resolve_pitch_width(pitch: Any) -> Optional[float]:
    if pitch is None:
        return None
    direct = getattr(pitch, "pitch_width", None) or getattr(pitch, "width", None)
    if direct:
        return float(direct)
    y_dim = getattr(pitch, "y_dim", None)
    if y_dim is not None:
        try:
            return float(getattr(y_dim, "max") - getattr(y_dim, "min"))
        except Exception:  # pragma: no cover - fallback
            return None
    return None


def _player_detected(player_data: Any) -> bool:
    if player_data is None:
        return True
    detected = getattr(player_data, "is_visible", None)
    if detected is None:
        detected = getattr(player_data, "is_detected", None)
    if detected is None and hasattr(player_data, "other_data"):
        other = getattr(player_data, "other_data", {}) or {}
        detected = other.get("is_detected") or other.get("is_visible")
    if detected is None:
        return True
    if isinstance(detected, bool):
        return detected
    if isinstance(detected, str):
        lowered = detected.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return bool(detected)
