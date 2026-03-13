"""
Long-form to shorts pipeline (ClippedAI-style).
Transcribe with Whisper → detect segments → crop to vertical → burn subtitles.
"""
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from shared.config import settings

logger = logging.getLogger(__name__)


def _ensure_ffmpeg() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def _transcribe_whisper(audio_path: str | Path) -> list[dict[str, Any]]:
    """Transcribe with faster-whisper; return list of {start, end, text}."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        logger.warning("faster_whisper not installed; returning empty segments")
        return []
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), word_timestamps=False)
    return [{"start": s.start, "end": s.end, "text": (s.text or "").strip()} for s in segments if (s.text or "").strip()]


def _get_video_duration(video_path: str | Path) -> float:
    """Get duration in seconds via ffprobe."""
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if out.returncode == 0 and out.stdout:
            return float(out.stdout.strip())
    except Exception:
        pass
    return 60.0


def _extract_audio_from_video(video_path: str | Path) -> str | None:
    """Extract WAV to temp file; return path."""
    out = Path(tempfile.gettempdir()) / f"clip_audio_{hash(str(video_path)) % 10**8}.wav"
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                str(out),
            ],
            check=True,
            capture_output=True,
            timeout=600,
        )
        return str(out)
    except Exception as e:
        logger.warning("Extract audio failed: %s", e)
        return None


def _highlight_segments(segments: list[dict], target_duration: float, max_duration: float) -> list[dict]:
    """Pick consecutive segments that fit in target_duration (up to max_duration)."""
    if not segments:
        return []
    chosen = []
    t_end = 0.0
    for s in segments:
        start, end = s["start"], s["end"]
        if t_end > 0 and start - t_end > 5.0:
            break  # gap > 5s, stop
        dur = end - start
        if (sum(d["end"] - d["start"] for d in chosen) + dur) > max_duration:
            break
        chosen.append(s)
        t_end = end
        if (chosen[-1]["end"] - chosen[0]["start"]) >= target_duration:
            break
    return chosen


def _crop_vertical_ffmpeg(
    input_path: str | Path,
    output_path: str | Path,
    start_sec: float,
    duration_sec: float,
    srt_path: str | Path | None = None,
) -> bool:
    """Crop segment to vertical 9:16 and optionally burn subtitles."""
    w = settings.clip_vertical_width
    h = settings.clip_vertical_height
    # Crop center of frame to w x h (portrait)
    vf = f"crop={w}:{h}:(iw-{w})/2:0,scale={w}:{h}"
    if srt_path and Path(srt_path).exists():
        srt_esc = str(Path(srt_path).resolve()).replace("\\", "/").replace(":", "\\:")
        vf += f",subtitles={srt_esc}:force_style='FontSize=22,PrimaryColour=&HFFFFFF&'"
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec), "-i", str(input_path),
        "-t", str(duration_sec),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        return True
    except Exception as e:
        logger.warning("FFmpeg crop failed: %s", e)
        return False


def longform_to_shorts(
    video_path_or_url: str,
    output_dir: str | Path,
    target_duration_seconds: float | None = None,
    max_clips: int = 3,
) -> list[dict[str, Any]]:
    """
    Convert long video to one or more vertical shorts.
    - If video_path_or_url is URL, download to temp first.
    - Transcribe with Whisper, pick highlight segments, crop to 9:16, burn subs.
    Returns list of { "path": str, "start": float, "end": float, "segment": [...] }.
    """
    if not _ensure_ffmpeg():
        logger.warning("FFmpeg not found")
        return []
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = target_duration_seconds or settings.clip_target_duration_seconds
    max_dur = settings.clip_max_duration_seconds

    video_path = video_path_or_url
    if video_path_or_url.startswith("http://") or video_path_or_url.startswith("https://"):
        video_path = Path(tempfile.gettempdir()) / f"clip_dl_{hash(video_path_or_url) % 10**8}.mp4"
        try:
            urlretrieve(video_path_or_url, video_path)
        except Exception as e:
            logger.warning("Download failed: %s", e)
            return []

    video_path = Path(video_path)
    if not video_path.exists():
        logger.warning("Video file not found: %s", video_path)
        return []

    audio_path = _extract_audio_from_video(video_path)
    if not audio_path:
        return []
    segments = _transcribe_whisper(audio_path)
    Path(audio_path).unlink(missing_ok=True)
    if not segments:
        dur = _get_video_duration(video_path)
        seg_dur = min(dur, target, max_dur)
        segments = [{"start": 0.0, "end": seg_dur, "text": "Highlight"}]
    highlight = _highlight_segments(segments, target_duration=target, max_duration=max_dur)
    if not highlight:
        logger.warning("No highlight segments found")
        return []

    start_sec = highlight[0]["start"]
    end_sec = highlight[-1]["end"]
    duration_sec = end_sec - start_sec

    # Build SRT for this clip (relative to segment start)
    srt_lines = []
    for i, s in enumerate(highlight, 1):
        rel_start = s["start"] - start_sec
        rel_end = s["end"] - start_sec
        h = int(rel_start // 3600)
        m = int((rel_start % 3600) // 60)
        sec = int(rel_start % 60)
        ms = int((rel_start % 1) * 1000)
        t1 = f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
        h = int(rel_end // 3600)
        m = int((rel_end % 3600) // 60)
        sec = int(rel_end % 60)
        ms = int((rel_end % 1) * 1000)
        t2 = f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"
        srt_lines.append(f"{i}\n{t1} --> {t2}\n{s['text']}\n\n")
    srt_path = out_dir / "clip_segment.srt"
    srt_path.write_text("".join(srt_lines), encoding="utf-8")

    out_path = out_dir / f"short_{start_sec:.0f}_{end_sec:.0f}.mp4"
    ok = _crop_vertical_ffmpeg(video_path, out_path, start_sec, duration_sec, srt_path)
    srt_path.unlink(missing_ok=True)
    if not ok:
        return []
    return [{"path": str(out_path), "start": start_sec, "end": end_sec, "segment": highlight}]
