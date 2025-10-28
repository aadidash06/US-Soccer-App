from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import requests
from kloppy import skillcorner
from kloppy.domain import TrackingDataset

CACHE_ROOT = Path(__file__).resolve().parent / "data_cache"
GITHUB_REPO = "SkillCorner/opendata"
GITHUB_BRANCH = "master"
DOWNLOAD_CHUNK_SIZE = 1 << 20  # 1 MiB per chunk


def _ensure_cached_match(match_id: str) -> tuple[Path, Path]:
    # Ensure both metadata and tracking files are cached locally for the given match.
    match_id_str = str(match_id)
    match_dir = CACHE_ROOT / "matches" / match_id_str
    meta_path = match_dir / f"{match_id_str}_match.json"
    tracking_path = match_dir / f"{match_id_str}_tracking_extrapolated.jsonl"

    if meta_path.exists() and tracking_path.exists():
        return meta_path, tracking_path

    match_dir.mkdir(parents=True, exist_ok=True)
    base_url = "https://raw.githubusercontent.com/SkillCorner/opendata/master/data/matches"

    file_map = (
        (meta_path, f"{match_id_str}_match.json"),
        (tracking_path, f"{match_id_str}_tracking_extrapolated.jsonl"),
    )
    for target_path, filename in file_map:
        if target_path.exists() and not _is_lfs_pointer(target_path):
            continue
        remote_path = f"data/matches/{match_id_str}/{filename}"
        # Download fresh content whenever the cached file is missing or still an LFS pointer.
        _download_github_file(remote_path, target_path)

    return meta_path, tracking_path


def _download_github_file(remote_path: str, destination: Path) -> None:
    raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{remote_path}"
    try:
        response = requests.get(raw_url, timeout=45)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FileNotFoundError(
            f"Unable to download file from GitHub ({raw_url}): {exc}",
        ) from exc

    content = response.content
    if content.startswith(b"version https://git-lfs.github.com/spec/v1"):
        # Git LFS pointer detected -> fetch actual binary payload.
        media_url = f"https://media.githubusercontent.com/media/{GITHUB_REPO}/{GITHUB_BRANCH}/{remote_path}"
        try:
            with requests.get(media_url, timeout=300, stream=True) as media_response:
                media_response.raise_for_status()
                with destination.open("wb") as target_fp:
                    for chunk in media_response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                        if chunk:
                            target_fp.write(chunk)
        except requests.RequestException as exc:
            raise FileNotFoundError(
                f"Unable to download LFS file from GitHub ({media_url}): {exc}",
            ) from exc
    else:
        destination.write_bytes(content)


def _is_lfs_pointer(path: Path) -> bool:
    try:
        with path.open("rb") as fp:
            header = fp.read(200)
    except FileNotFoundError:
        return False
    return header.startswith(b"version https://git-lfs.github.com/spec/v1")


@lru_cache(maxsize=8)
def load_skillcorner_tracking(
    match_id: str,
    sample_rate: Optional[float] = None,
    include_empty_frames: bool = False,
    coordinates: Optional[str] = "skillcorner",
    only_alive: bool = False,
) -> TrackingDataset:
    """
    Fetch and standardize tracking data for a SkillCorner open data match.
    Data is cached locally under app/data_cache/ to avoid repeated network fetches.
    """
    if not match_id:
        raise ValueError("A match_id is required to load tracking data.")

    meta_path, tracking_path = _ensure_cached_match(match_id)

    dataset = skillcorner.load(
        meta_data=meta_path,
        raw_data=tracking_path,
        sample_rate=sample_rate,
        include_empty_frames=include_empty_frames,
        coordinates=coordinates,
        only_alive=only_alive,
    )
    return dataset
