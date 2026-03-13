"""
Script generator: converts a video idea into a full script (3s hook + 10–30s narration + scene breakdown).
"""
import logging
import os
import random
from typing import Any

from .scene_generator import scenes_from_narration, text_overlays_from_scenes

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
except ImportError:
    pass


def generate_script_openai(
    hook: str,
    concept: str,
    trend_angle: str,
    duration_seconds: float = 30.0,
) -> dict[str, Any]:
    """Generate narration and structure using OpenAI."""
    if not OPENAI_AVAILABLE:
        return _script_fallback(hook, concept, duration_seconds)
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You write short-form video scripts. Output ONLY the narration text (no hook repetition). "
                    "Keep it concise for a %d second video. 2-4 short sentences." % duration_seconds,
                },
                {
                    "role": "user",
                    "content": f"Hook: {hook}\nConcept: {concept}\nAngle: {trend_angle}\nWrite the %d second narration only." % duration_seconds,
                },
            ],
            max_tokens=300,
        )
        narration = (response.choices[0].message.content or "").strip()
        if not narration:
            return _script_fallback(hook, concept, duration_seconds)
        scene_breakdown = scenes_from_narration(
            narration, hook, total_duration_seconds=duration_seconds, hook_duration=3.0
        )
        text_overlays = text_overlays_from_scenes(scene_breakdown)
        return {
            "hook_text": hook,
            "narration": narration,
            "duration_seconds": duration_seconds,
            "scene_breakdown": scene_breakdown,
            "text_overlays": text_overlays,
        }
    except Exception as e:
        logger.warning("OpenAI script generation failed: %s", e)
        return _script_fallback(hook, concept, duration_seconds)


def _script_fallback(hook: str, concept: str, duration_seconds: float) -> dict[str, Any]:
    """Fallback script from concept."""
    narration = f"{concept} This is the kind of content that blows up when you get it right. Save this and try it."
    scene_breakdown = scenes_from_narration(
        narration, hook, total_duration_seconds=duration_seconds, hook_duration=3.0
    )
    text_overlays = text_overlays_from_scenes(scene_breakdown)
    return {
        "hook_text": hook,
        "narration": narration,
        "duration_seconds": duration_seconds,
        "scene_breakdown": scene_breakdown,
        "text_overlays": text_overlays,
    }


def generate_script(
    idea_id: int,
    hook: str,
    concept: str,
    trend_angle: str = "",
    duration_seconds: float = 30.0,
) -> dict[str, Any]:
    """Generate full script for an idea. Returns dict with hook_text, narration, duration_seconds, scene_breakdown, text_overlays."""
    return generate_script_openai(hook, concept, trend_angle, duration_seconds)
