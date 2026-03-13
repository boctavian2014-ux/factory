"""
Celery worker: video rendering. Generates voiceover, subtitles, renders 1080x1920 video.
"""
import logging
import uuid
from pathlib import Path

from shared.celery_app import celery_app
from shared.config import settings
from shared.database import get_db
from shared.models import Video as VideoModel

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.video_worker.render_video", bind=True)
def render_video_task(
    self,
    script_id: int,
    hook_text: str,
    narration: str,
    scene_breakdown: list,
    duration_seconds: float = 30.0,
):
    """Render video from script and persist video record."""
    from services.video_service.voiceover_generator import generate_voiceover
    from services.video_service.subtitle_generator import generate_srt
    from services.video_service.video_renderer import render_video

    videos_dir = Path(settings.videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"script_{script_id}_{uuid.uuid4().hex[:8]}"
    audio_path = videos_dir / f"{base_name}_audio.wav"
    srt_path = videos_dir / f"{base_name}.srt"
    output_path = videos_dir / f"{base_name}.mp4"

    generate_voiceover(narration=narration, hook_text=hook_text, output_path=audio_path, duration_seconds=duration_seconds)
    generate_srt(scene_breakdown, srt_path)
    out_file = render_video(
        audio_path=audio_path,
        output_path=output_path,
        duration_seconds=duration_seconds,
        srt_path=srt_path,
        width=settings.video_width,
        height=settings.video_height,
        fps=settings.video_fps,
    )
    if not out_file:
        out_file = str(output_path)

    with get_db() as db:
        row = VideoModel(
            script_id=script_id,
            file_path=out_file,
            duration_seconds=duration_seconds,
            width=settings.video_width,
            height=settings.video_height,
        )
        db.add(row)
        db.flush()
        video_id = row.id
    logger.info("Video worker stored video id=%s path=%s", video_id, out_file)
    return {"video_id": video_id, "file_path": out_file}
