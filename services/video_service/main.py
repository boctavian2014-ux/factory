"""
Video service: HTTP API for rendering short-form videos from scripts.
POST /videos/render — full pipeline + DB. POST /videos/quick — fără DB, doar hook+concept → video.
POST /videos/upload — upload photo or video. POST /videos/from-upload — make video from uploaded file.
GET /videos/file/{filename} — servește fișierul video generat. GET /videos/uploaded/{filename} — servește fișier încărcat.
"""
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.config import settings
from shared.database import get_db_dependency
from shared.models import Video as VideoModel

from .video_renderer import render_video
from .voiceover_generator import generate_voiceover
from .subtitle_generator import generate_srt
from .stock_media import get_background_image_for_script
from .external_video_client import generate_video_via_api

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])


class RenderVideoRequest(BaseModel):
    script_id: int
    hook_text: str
    narration: str
    scene_breakdown: list[dict[str, Any]]
    duration_seconds: float = 30.0


class RenderVideoResponse(BaseModel):
    status: str
    video_id: int
    file_path: str
    video_url: str | None = None


@router.post("/render", response_model=RenderVideoResponse)
def render_video_endpoint(
    body: RenderVideoRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Generate voiceover, subtitles, and render 1080x1920 video; store in DB.
    Uses external API (Open-Sora / Sora-2 style) if video_generation_backend=external_api,
    else native voiceover + FFmpeg. Optional Pexels background when enable_stock_media=True."""
    videos_dir = Path(settings.videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"script_{body.script_id}_{uuid.uuid4().hex[:8]}"
    output_path = videos_dir / f"{base_name}.mp4"

    backend = (settings.video_generation_backend or "native").strip().lower()
    if backend == "external_api" and settings.video_api_url:
        prompt = f"{body.hook_text}\n\n{body.narration}"
        out_file = generate_video_via_api(
            prompt=prompt,
            duration_seconds=body.duration_seconds,
            output_dir=videos_dir,
        )
        if not out_file:
            logger.warning("External API failed; falling back to native render")
            backend = "native"
    else:
        out_file = None

    if out_file is None or backend == "native":
        audio_out = videos_dir / f"{base_name}_audio.wav"
        srt_path = videos_dir / f"{base_name}.srt"
        audio_path = generate_voiceover(
            narration=body.narration,
            hook_text=body.hook_text,
            output_path=audio_out,
            duration_seconds=body.duration_seconds,
        )
        if not audio_path:
            audio_path = str(audio_out)
        generate_srt(body.scene_breakdown, srt_path)
        bg_image = None
        if settings.enable_stock_media:
            bg_image = get_background_image_for_script(
                concept=body.narration[:200] or body.hook_text,
                hook=body.hook_text,
            )
        out_file = render_video(
            audio_path=audio_path,
            output_path=output_path,
            duration_seconds=body.duration_seconds,
            srt_path=srt_path,
            width=settings.video_width,
            height=settings.video_height,
            fps=settings.video_fps,
            background_image_path=bg_image,
        )
    if not out_file:
        out_file = str(output_path)

    video_id = 0
    try:
        row = VideoModel(
            script_id=body.script_id,
            file_path=out_file,
            duration_seconds=body.duration_seconds,
            width=settings.video_width,
            height=settings.video_height,
        )
        db.add(row)
        db.commit()
        video_id = row.id
        logger.info("Stored video id=%s path=%s", row.id, out_file)
    except Exception as e:
        logger.warning("DB save skipped: %s", e)
    out_path = Path(out_file)
    video_url = f"/videos/file/{out_path.name}" if out_path.name else None
    return RenderVideoResponse(status="ok", video_id=video_id, file_path=out_file, video_url=video_url)


class QuickVideoRequest(BaseModel):
    hook: str = "Stop scrolling."
    concept: str = "This is how you get more views."
    duration_seconds: float = 30.0


class QuickVideoResponse(BaseModel):
    status: str
    video_url: str
    file_path: str
    duration_seconds: float


@router.post("/quick", response_model=QuickVideoResponse)
def quick_video(body: QuickVideoRequest) -> Any:
    """
    Generează un video fără DB: hook + concept → script → voiceover → FFmpeg → MP4.
    Ideal pentru test rapid. Returnează video_url pentru redare/descărcare.
    """
    from services.script_service.script_generator import generate_script

    script_data = generate_script(
        idea_id=0,
        hook=body.hook or "Hook",
        concept=body.concept or "Concept",
        trend_angle="",
        duration_seconds=body.duration_seconds,
    )
    videos_dir = Path(settings.videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"quick_{uuid.uuid4().hex[:10]}"
    audio_out = videos_dir / f"{base_name}_audio.wav"
    srt_path = videos_dir / f"{base_name}.srt"
    output_path = videos_dir / f"{base_name}.mp4"

    audio_path = generate_voiceover(
        narration=script_data["narration"],
        hook_text=script_data["hook_text"],
        output_path=audio_out,
        duration_seconds=script_data["duration_seconds"],
    )
    if not audio_path:
        audio_path = str(audio_out)
    generate_srt(script_data["scene_breakdown"], srt_path)
    bg_image = None
    if settings.enable_stock_media:
        bg_image = get_background_image_for_script(
            concept=script_data["narration"][:200] or script_data["hook_text"],
            hook=script_data["hook_text"],
        )
    out_file = render_video(
        audio_path=audio_path,
        output_path=output_path,
        duration_seconds=script_data["duration_seconds"],
        srt_path=srt_path,
        width=settings.video_width,
        height=settings.video_height,
        fps=settings.video_fps,
        background_image_path=bg_image,
    )
    if not out_file:
        raise HTTPException(status_code=500, detail="Video render failed")
    out_path = Path(out_file)
    video_url = f"/videos/file/{out_path.name}"
    logger.info("Quick video: %s", video_url)
    return QuickVideoResponse(
        status="ok",
        video_url=video_url,
        file_path=out_file,
        duration_seconds=script_data["duration_seconds"],
    )


# --- Upload: photo / video then make video from it ---
UPLOAD_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
UPLOAD_VIDEO_EXT = {".mp4", ".mov", ".webm"}


def _upload_media_type(ext: str) -> str:
    ext_lower = (ext or "").lower()
    if ext_lower in UPLOAD_IMAGE_EXT:
        return "image"
    if ext_lower in UPLOAD_VIDEO_EXT:
        return "video"
    return ""


class UploadResponse(BaseModel):
    status: str
    filename: str
    url: str
    media_type: str  # "image" | "video"


@router.post("/upload", response_model=UploadResponse)
async def upload_photo_or_video(file: UploadFile = File(...)) -> Any:
    """Upload a photo or video; use the returned filename with POST /videos/from-upload to make a video."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in UPLOAD_IMAGE_EXT and ext not in UPLOAD_VIDEO_EXT:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed: image {sorted(UPLOAD_IMAGE_EXT)}, video {sorted(UPLOAD_VIDEO_EXT)}",
        )
    media_type = _upload_media_type(ext)
    uploads_dir = Path(settings.uploads_dir)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = uploads_dir / safe_name
    content = await file.read()
    file_path.write_bytes(content)
    logger.info("Uploaded %s: %s", media_type, safe_name)
    url = f"/videos/uploaded/{safe_name}"
    return UploadResponse(status="ok", filename=safe_name, url=url, media_type=media_type)


@router.get("/uploaded/{filename}")
def serve_uploaded_file(filename: str):
    """Serve an uploaded photo or video (preview)."""
    safe_name = Path(filename).name
    ext = Path(safe_name).suffix.lower()
    if ext not in UPLOAD_IMAGE_EXT and ext not in UPLOAD_VIDEO_EXT:
        raise HTTPException(status_code=400, detail="Invalid file type")
    uploads_dir = Path(settings.uploads_dir).resolve()
    file_path = (uploads_dir / safe_name).resolve()
    if not file_path.is_file() or not str(file_path).startswith(str(uploads_dir)):
        raise HTTPException(status_code=404, detail="File not found")
    if ext in UPLOAD_IMAGE_EXT:
        mime = "image/" + ("png" if ext == ".png" else "jpeg" if ext in (".jpg", ".jpeg") else "webp" if ext == ".webp" else "gif")
        return FileResponse(file_path, media_type=mime)
    mime = "video/mp4" if ext == ".mp4" else "video/quicktime" if ext == ".mov" else "video/webm"
    return FileResponse(file_path, media_type=mime)


class FromUploadRequest(BaseModel):
    uploaded_filename: str
    hook: str = "Stop scrolling."
    concept: str = "Make a short that stands out."
    duration_seconds: float = 30.0


class FromUploadResponse(BaseModel):
    status: str
    video_url: str
    file_path: str
    duration_seconds: float


@router.post("/from-upload", response_model=FromUploadResponse)
def make_video_from_upload(body: FromUploadRequest) -> Any:
    """
    Make a video from an uploaded photo or video: script from hook+concept, voiceover, subtitles,
    then render using the upload as background (image) or video source (video).
    """
    from services.script_service.script_generator import generate_script

    safe_name = Path(body.uploaded_filename).name
    ext = Path(safe_name).suffix.lower()
    if ext not in UPLOAD_IMAGE_EXT and ext not in UPLOAD_VIDEO_EXT:
        raise HTTPException(status_code=400, detail="Invalid uploaded file type")
    uploads_dir = Path(settings.uploads_dir)
    source_path = uploads_dir / safe_name
    if not source_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    script_data = generate_script(
        idea_id=0,
        hook=body.hook or "Hook",
        concept=body.concept or "Concept",
        trend_angle="",
        duration_seconds=body.duration_seconds,
    )
    videos_dir = Path(settings.videos_dir)
    videos_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"from_upload_{uuid.uuid4().hex[:10]}"
    audio_out = videos_dir / f"{base_name}_audio.wav"
    srt_path = videos_dir / f"{base_name}.srt"
    output_path = videos_dir / f"{base_name}.mp4"

    audio_path = generate_voiceover(
        narration=script_data["narration"],
        hook_text=script_data["hook_text"],
        output_path=audio_out,
        duration_seconds=script_data["duration_seconds"],
    )
    if not audio_path:
        audio_path = str(audio_out)
    generate_srt(script_data["scene_breakdown"], srt_path)

    bg_image = str(source_path) if ext in UPLOAD_IMAGE_EXT else None
    bg_video = str(source_path) if ext in UPLOAD_VIDEO_EXT else None
    out_file = render_video(
        audio_path=audio_path,
        output_path=output_path,
        duration_seconds=script_data["duration_seconds"],
        srt_path=srt_path,
        width=settings.video_width,
        height=settings.video_height,
        fps=settings.video_fps,
        background_image_path=bg_image,
        background_video_path=bg_video,
    )
    if not out_file:
        raise HTTPException(status_code=500, detail="Video render failed")
    out_path = Path(out_file)
    video_url = f"/videos/file/{out_path.name}"
    logger.info("From-upload video: %s (source %s)", video_url, body.uploaded_filename)
    return FromUploadResponse(
        status="ok",
        video_url=video_url,
        file_path=out_file,
        duration_seconds=script_data["duration_seconds"],
    )


@router.get("/file/{filename}")
def serve_video_file(filename: str):
    """Serve a generated video file (safe path)."""
    safe_name = Path(filename).name
    if not safe_name.endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Invalid file")
    videos_dir = Path(settings.videos_dir)
    file_path = videos_dir / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(file_path, media_type="video/mp4")
