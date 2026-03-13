"""
Scheduler: assigns scheduled_time and platform to approved videos.
"""
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def next_slot(
    platform: str,
    existing_slots: list[datetime] | None = None,
    interval_minutes: int = 180,
) -> datetime:
    """Return next suggested scheduled_time for the platform."""
    base = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    if existing_slots:
        base = max(existing_slots) + timedelta(minutes=interval_minutes)
    return base


def schedule_videos(
    video_ids: list[int],
    platforms: list[str] | None = None,
    start_at: datetime | None = None,
    interval_minutes: int = 180,
) -> list[dict[str, Any]]:
    """
    Build schedule entries for videos. Returns list of dicts with
    video_id, platform, scheduled_time.
    """
    platforms = platforms or ["tiktok", "instagram_reels", "youtube_shorts"]
    start = start_at or datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    slots = []
    for i, vid in enumerate(video_ids):
        platform = platforms[i % len(platforms)]
        t = start + timedelta(minutes=interval_minutes * i)
        slots.append({"video_id": vid, "platform": platform, "scheduled_time": t})
    return slots
