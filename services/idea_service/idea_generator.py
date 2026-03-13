"""
Idea generator: produces 50–100 video ideas per trend.
Each idea: hook, concept, caption, hashtags, trend_angle.
"""
import logging
import os
import random
from dataclasses import dataclass
from typing import Any

from .hook_generator import generate_hook, generate_hook_openai

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
except ImportError:
    pass


@dataclass
class VideoIdea:
    hook: str
    concept: str
    caption: str
    hashtags: list[str]
    trend_angle: str


def _default_hashtags(keyword: str, source: str) -> list[str]:
    base = ["#viral", "#fyp", "#foryou", "#trending", "#explore"]
    tag = f"#{keyword.replace(' ', '')}" if keyword else "#content"
    return [tag] + base[:4] + [f"#{source}"]


def _default_caption(concept: str, hook: str) -> str:
    return f"{hook}\n\n{concept}\n\nDouble tap if you agree! Follow for more."


def generate_ideas_openai(
    keyword: str,
    trend_score: float,
    source: str,
    count: int = 50,
) -> list[dict[str, Any]]:
    """Generate video ideas using OpenAI."""
    if not OPENAI_AVAILABLE or count <= 0:
        return _generate_ideas_fallback(keyword, source, count or 10)
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a viral short-form content strategist. For each idea output one line: "
                    "HOOK|CONCEPT|TREND_ANGLE. Hook = 3-sec attention grab. Concept = one sentence. Trend angle = how it ties to the trend.",
                },
                {
                    "role": "user",
                    "content": f"Trend: {keyword} (source: {source}, score: {trend_score}). Generate {min(count, 100)} unique video ideas. One per line, format: HOOK|CONCEPT|TREND_ANGLE",
                },
            ],
            max_tokens=4000,
        )
        text = response.choices[0].message.content or ""
        ideas = []
        for line in text.strip().split("\n")[:count]:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|", 2)]
            if len(parts) < 3:
                continue
            hook, concept, trend_angle = parts[0], parts[1], parts[2]
            caption = _default_caption(concept, hook)
            hashtags = _default_hashtags(keyword, source)
            ideas.append({
                "hook": hook,
                "concept": concept,
                "caption": caption,
                "hashtags": hashtags,
                "trend_angle": trend_angle,
            })
        if ideas:
            return ideas
    except Exception as e:
        logger.warning("OpenAI idea generation failed: %s", e)
    return _generate_ideas_fallback(keyword, source, count)


def _generate_ideas_fallback(keyword: str, source: str, count: int) -> list[dict[str, Any]]:
    """Fallback: generate ideas from templates."""
    concepts = [
        f"The truth about {keyword} nobody tells you",
        f"5 quick tips for {keyword}",
        f"Why {keyword} is blowing up right now",
        f"How I went viral with {keyword}",
        f"The {keyword} hack that changed everything",
        f"POV: You just discovered {keyword}",
        f"{keyword} explained in 30 seconds",
        f"Stop sleeping on {keyword}",
    ]
    ideas = []
    for i in range(count):
        concept = random.choice(concepts) if concepts else f"Viral take on {keyword}"
        hook = generate_hook(keyword, source, use_openai=False)
        caption = _default_caption(concept, hook)
        ideas.append({
            "hook": hook,
            "concept": concept,
            "caption": caption,
            "hashtags": _default_hashtags(keyword, source),
            "trend_angle": f"Riding the {keyword} trend from {source}",
        })
    return ideas


def generate_ideas_for_trend(
    trend_id: int,
    keyword: str,
    trend_score: float,
    source: str,
    count: int | None = None,
) -> list[dict[str, Any]]:
    """
    Generate 50–100 (or count) video ideas for a given trend.
    Returns list of dicts with hook, concept, caption, hashtags, trend_angle.
    """
    from shared.config import settings
    n = count or settings.ideas_per_trend
    n = max(10, min(100, n))
    return generate_ideas_openai(keyword, trend_score, source, count=n)
