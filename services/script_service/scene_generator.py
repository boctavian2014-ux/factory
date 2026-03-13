"""
Scene generator: breaks script into timed scenes and text overlays for video editing.
"""
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _estimate_word_duration(words: int, wpm: float = 150.0) -> float:
    """Rough duration in seconds for word count at words-per-minute."""
    if wpm <= 0:
        return 0.0
    return (words / wpm) * 60.0


def _split_into_sentences(text: str) -> list[str]:
    """Simple sentence split."""
    text = text.strip()
    if not text:
        return []
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p.strip() for p in parts if p.strip()]


def scenes_from_narration(
    narration: str,
    hook_text: str,
    total_duration_seconds: float = 30.0,
    hook_duration: float = 3.0,
) -> list[dict[str, Any]]:
    """
    Build scene breakdown from narration and hook.
    Returns list of {start, end, text, overlay}.
    """
    scenes = []
    t = 0.0
    if hook_text:
        scenes.append({
            "start": t,
            "end": t + hook_duration,
            "text": hook_text,
            "overlay": True,
        })
        t += hook_duration
    remaining = total_duration_seconds - t
    if remaining <= 0 or not narration:
        return scenes
    sentences = _split_into_sentences(narration)
    if not sentences:
        scenes.append({"start": t, "end": total_duration_seconds, "text": narration, "overlay": True})
        return scenes
    total_words = sum(len(s.split()) for s in sentences)
    if total_words == 0:
        total_words = 1
    sec_per_word = remaining / total_words
    for sent in sentences:
        word_count = len(sent.split()) or 1
        dur = sec_per_word * word_count
        end = min(t + dur, total_duration_seconds)
        scenes.append({
            "start": round(t, 2),
            "end": round(end, 2),
            "text": sent,
            "overlay": True,
        })
        t = end
        if t >= total_duration_seconds:
            break
    return scenes


def text_overlays_from_scenes(scene_breakdown: list[dict[str, Any]]) -> list[str]:
    """Extract overlay text lines from scene breakdown."""
    return [s["text"] for s in scene_breakdown if s.get("overlay") and s.get("text")]
