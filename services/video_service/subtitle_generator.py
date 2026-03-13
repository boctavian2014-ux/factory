"""
Subtitle generator: creates SRT or burned-in subtitle data from scene breakdown.
"""
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _sec_to_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt(scene_breakdown: list[dict[str, Any]], output_path: str | Path | None = None) -> str:
    """
    Generate SRT content from scene breakdown. If output_path given, write file.
    Returns SRT string.
    """
    lines = []
    for i, scene in enumerate(scene_breakdown, 1):
        start = scene.get("start", 0)
        end = scene.get("end", start + 3)
        text = scene.get("text", "").strip()
        if not text:
            continue
        lines.append(str(i))
        lines.append(f"{_sec_to_srt_time(start)} --> {_sec_to_srt_time(end)}")
        lines.append(text)
        lines.append("")
    srt = "\n".join(lines)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(srt, encoding="utf-8")
    return srt


def subtitles_from_script(scene_breakdown: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return list of {start, end, text} for use in renderer."""
    return [
        {"start": s.get("start", 0), "end": s.get("end", 0), "text": s.get("text", "")}
        for s in scene_breakdown
        if s.get("text")
    ]
