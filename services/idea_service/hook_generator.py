"""
Hook generator: creates attention-grabbing 3-second hooks for short-form video.
Uses OpenAI API for generation; falls back to templates when API unavailable.
"""
import logging
import os
import random
from typing import Optional

logger = logging.getLogger(__name__)

OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
except ImportError:
    pass

HOOK_TEMPLATES = [
    "Wait for it...",
    "You're doing it wrong.",
    "Nobody talks about this.",
    "Stop scrolling. This matters.",
    "I wish I knew this sooner.",
    "The one trick that changed everything.",
    "POV: You just discovered this.",
    "This went viral for a reason.",
    "Save this before it's gone.",
    "Experts don't want you to know this.",
]


def generate_hook_openai(topic: str, trend_angle: str, count: int = 5) -> list[str]:
    """Generate hooks using OpenAI API."""
    if not OPENAI_AVAILABLE:
        return [random.choice(HOOK_TEMPLATES) for _ in range(count)]
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "You write viral short-form video hooks (TikTok/Reels/Shorts). "
                    "Each hook must grab attention in the first 3 seconds. One short line per hook. No quotes.",
                },
                {
                    "role": "user",
                    "content": f"Topic: {topic}. Trend angle: {trend_angle}. Generate exactly {count} different hooks, one per line.",
                },
            ],
            max_tokens=200,
        )
        text = response.choices[0].message.content or ""
        hooks = [line.strip() for line in text.strip().split("\n") if line.strip()][:count]
        return hooks if hooks else [random.choice(HOOK_TEMPLATES) for _ in range(count)]
    except Exception as e:
        logger.warning("OpenAI hook generation failed: %s", e)
        return [random.choice(HOOK_TEMPLATES) for _ in range(count)]


def generate_hook(topic: str, trend_angle: str = "", use_openai: bool = True) -> str:
    """Return a single hook for the given topic and trend angle."""
    if use_openai and OPENAI_AVAILABLE:
        hooks = generate_hook_openai(topic, trend_angle, count=1)
        return hooks[0] if hooks else random.choice(HOOK_TEMPLATES)
    return random.choice(HOOK_TEMPLATES)
