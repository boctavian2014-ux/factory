"""
SQLAlchemy and Pydantic models shared across services.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, JSON, Boolean

from shared.database import Base as SQLBase


# --- SQLAlchemy ORM Models ---


class Trend(SQLBase):
    """Stored trend from scrapers (TikTok, YouTube, Google Trends, Reddit)."""
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), index=True)  # tiktok, youtube, google_trends, reddit
    keyword = Column(String(255), index=True)
    hashtags = Column(JSON)  # list of str
    trend_score = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0)
    engagement_velocity = Column(Float, default=0.0)
    raw_signals = Column(JSON)  # raw counts, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoIdea(SQLBase):
    """Generated idea for a short-form video."""
    __tablename__ = "video_ideas"

    id = Column(Integer, primary_key=True, index=True)
    trend_id = Column(Integer, index=True)
    hook = Column(Text)
    concept = Column(Text)
    caption = Column(Text)
    hashtags = Column(JSON)
    trend_angle = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)


class Script(SQLBase):
    """Generated script for a video (hook + narration + scenes)."""
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    idea_id = Column(Integer, index=True)
    hook_text = Column(Text)
    narration = Column(Text)
    duration_seconds = Column(Float, default=30.0)
    scene_breakdown = Column(JSON)  # list of {start, end, text, overlay}
    text_overlays = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)


class Video(SQLBase):
    """Rendered video asset and metadata."""
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, index=True)
    file_path = Column(String(1024))
    duration_seconds = Column(Float)
    width = Column(Integer, default=1080)
    height = Column(Integer, default=1920)
    virality_score = Column(Float, nullable=True)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledPost(SQLBase):
    """Scheduled post for a platform."""
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, index=True)
    platform = Column(String(50))  # tiktok, instagram_reels, youtube_shorts
    caption = Column(Text)
    hashtags = Column(JSON)
    scheduled_time = Column(DateTime)
    exported = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Pydantic schemas (API / queues) ---


class TrendCreate(BaseModel):
    source: str
    keyword: str
    hashtags: list[str] = []
    trend_score: float = 0.0
    growth_rate: float = 0.0
    engagement_velocity: float = 0.0
    raw_signals: Optional[dict[str, Any]] = None


class TrendResponse(BaseModel):
    id: int
    source: str
    keyword: str
    trend_score: float
    growth_rate: float
    engagement_velocity: float
    created_at: datetime

    class Config:
        from_attributes = True


class IdeaPayload(BaseModel):
    hook: str
    concept: str
    caption: str
    hashtags: list[str]
    trend_angle: str


class ScriptPayload(BaseModel):
    hook_text: str
    narration: str
    duration_seconds: float = 30.0
    scene_breakdown: list[dict[str, Any]]
    text_overlays: list[str]


class ViralityInput(BaseModel):
    trend_score: float
    hashtags: list[str]
    caption_length: int
    video_duration: float
    topic_embedding: Optional[list[float]] = None


class ScheduleItem(BaseModel):
    video_file: str
    caption: str
    hashtags: list[str]
    platform: str
    scheduled_time: str
