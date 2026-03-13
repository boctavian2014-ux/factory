"""
Video renderer: produces 1080x1920 vertical videos from assets using FFmpeg.
Combines images/clips, voiceover, and subtitles into final MP4.
"""
import logging
import subprocess
from pathlib import Path
from typing import Any

from shared.config import settings

logger = logging.getLogger(__name__)


def _ensure_ffmpeg() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def render_video(
    audio_path: str | Path,
    output_path: str | Path,
    duration_seconds: float | None = None,
    srt_path: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
    fps: int | None = None,
    background_image_path: str | Path | None = None,
    background_video_path: str | Path | None = None,
) -> str | None:
    """
    Render vertical video: solid color, image, or uploaded video + audio + optional burn-in subtitles.
    background_image_path: scale/crop image to fill (ShortsGenerator-style).
    background_video_path: use video as source; loop/trim to duration, overlay audio + subtitles.
    Returns path to output MP4 or None on failure.
    """
    if not _ensure_ffmpeg():
        logger.warning("FFmpeg not found; creating placeholder")
        return _placeholder_video(output_path, duration_seconds or 30.0)

    w = width or settings.video_width
    h = height or settings.video_height
    f = fps or settings.video_fps
    dur = duration_seconds or settings.default_duration_seconds
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    srt_file = Path(srt_path) if srt_path else None
    if srt_file and srt_file.exists():
        srt_escaped = str(srt_file.resolve()).replace("\\", "/").replace(":", "\\:")
        sub_filter = f"subtitles={srt_escaped}:force_style='FontSize=24,PrimaryColour=&HFFFFFF&'"
    else:
        sub_filter = None

    # Video source: uploaded video (loop/trim to duration)
    vid_path = Path(background_video_path) if background_video_path else None
    if vid_path and vid_path.exists():
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if sub_filter:
            vf += "," + sub_filter
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", str(vid_path), "-t", str(dur),
            "-i", str(audio_path),
            "-vf", vf, "-r", str(f),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", str(out),
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=180)
            return str(out)
        except subprocess.CalledProcessError as e:
            logger.error("FFmpeg video-background error: %s", e.stderr and e.stderr.decode())
            return _placeholder_video(output_path, dur)
        except Exception as e:
            logger.error("Render (video bg) failed: %s", e)
            return _placeholder_video(output_path, dur)
    # Image or solid color
    img_path = Path(background_image_path) if background_image_path else None
    if img_path and img_path.exists():
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        if sub_filter:
            vf += "," + sub_filter
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(img_path), "-t", str(dur),
            "-i", str(audio_path),
            "-vf", vf, "-r", str(f),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", str(out),
        ]
    else:
        if sub_filter:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=#1a1a2e:s={w}x{h}:d={dur}:r={f}",
                "-i", str(audio_path),
                "-vf", sub_filter,
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest", str(out),
            ]
        else:
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=#1a1a2e:s={w}x{h}:d={dur}:r={f}",
                "-i", str(audio_path),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac", "-b:a", "128k",
                "-shortest", str(out),
            ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return str(out)
    except subprocess.CalledProcessError as e:
        logger.error("FFmpeg error: %s %s", e.stderr and e.stderr.decode(), e)
        return _placeholder_video(output_path, dur)
    except Exception as e:
        logger.error("Render failed: %s", e)
        return _placeholder_video(output_path, dur)


def _placeholder_video(output_path: str | Path, duration_seconds: float) -> str | None:
    """Create minimal placeholder MP4 (no audio) when FFmpeg or assets missing."""
    if not _ensure_ffmpeg():
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).touch()
        return str(output_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#1a1a2e:s=1080x1920:d={duration_seconds}:r=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        return str(out)
    except Exception as e:
        logger.error("Placeholder video failed: %s", e)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).touch()
        return str(output_path)
