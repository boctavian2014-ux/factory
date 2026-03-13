"""
Clip service: long-form to shorts (ClippedAI-style).
POST /clips/from-long-form — upload or URL → vertical shorts with subtitles.
"""
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, UploadFile, Form

from shared.config import settings

from .longform_to_short import longform_to_shorts

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/clips", tags=["clips"])


@router.post("/from-long-form")
def from_long_form(
    video_url: str | None = Form(None, description="URL of long-form video"),
    video_file: UploadFile | None = File(None),
    target_duration_seconds: int | None = Form(None),
    max_clips: int = Form(1, ge=1, le=10),
) -> dict[str, Any]:
    """
    Convert long-form video to vertical shorts.
    Provide either video_url or video_file.
    Uses Whisper for transcription and FFmpeg for vertical crop + subtitles.
    """
    if not video_url and not video_file:
        return {"status": "error", "message": "Provide video_url or video_file"}
    if video_url and video_file:
        return {"status": "error", "message": "Provide only one of video_url or video_file"}

    out_dir = Path(settings.videos_dir) / "clips"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir = out_dir / str(uuid.uuid4().hex[:8])
    out_dir.mkdir(parents=True, exist_ok=True)

    if video_file:
        path = out_dir / "input.mp4"
        with path.open("wb") as f:
            f.write(video_file.file.read())
        source = str(path)
    else:
        source = video_url.strip()

    target = float(target_duration_seconds) if target_duration_seconds else None
    results = longform_to_shorts(
        video_path_or_url=source,
        output_dir=out_dir,
        target_duration_seconds=target,
        max_clips=max_clips,
    )
    if not results:
        return {"status": "ok", "clips": [], "message": "No segments produced (check Whisper/FFmpeg)"}
    return {
        "status": "ok",
        "clips": [{"path": r["path"], "start": r["start"], "end": r["end"]} for r in results],
        "count": len(results),
    }
