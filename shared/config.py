"""
Central configuration for the AI Content Factory.
Environment variables override defaults. Used by all services and workers.
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App
    app_name: str = "AI Content Factory"
    debug: bool = False
    environment: str = "development"

    # Redis (Celery broker + result backend)
    redis_url: str = "redis://redis:6379/0"
    redis_celery_broker: str = "redis://redis:6379/1"
    redis_celery_result: str = "redis://redis:6379/2"

    # PostgreSQL
    database_url: str = "postgresql://postgres:postgres@postgres:5432/ai_content_factory"

    # OpenAI
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    # Celery queues (for horizontal scaling)
    celery_trend_queue: str = "trend"
    celery_idea_queue: str = "idea"
    celery_script_queue: str = "script"
    celery_video_queue: str = "video"
    celery_virality_queue: str = "virality"

    # Paths (defaults work local; in Docker set VIDEOS_DIR=/app/outputs/videos etc.)
    outputs_dir: str = "outputs"
    videos_dir: str = "outputs/videos"
    uploads_dir: str = "outputs/uploads"
    csv_dir: str = "outputs/csv"
    ml_models_dir: str = "ml"

    # Virality
    virality_threshold: float = 0.5
    virality_model_path: str = "/app/ml/virality_model/checkpoint.pt"

    # Trend
    trend_model_path: str = "/app/ml/trend_model/checkpoint.pt"

    # Video
    video_width: int = 1080
    video_height: int = 1920
    video_fps: int = 30
    default_duration_seconds: int = 30
    # Backend: "native" (voiceover + FFmpeg) or "external_api" (Open-Sora / Sora-2 style API)
    video_generation_backend: str = "native"
    video_api_url: Optional[str] = None  # e.g. http://localhost:8001/generate
    # Stock media (ShortsGenerator-style: images per scene)
    pexels_api_key: Optional[str] = os.getenv("PEXELS_API_KEY", "")
    enable_stock_media: bool = False

    # Long-form to shorts (ClippedAI-style)
    clip_max_duration_seconds: int = 60
    clip_target_duration_seconds: int = 45
    clip_vertical_width: int = 1080
    clip_vertical_height: int = 1920

    # Limits
    ideas_per_trend: int = 75
    max_scripts_per_batch: int = 100
    max_videos_per_batch: int = 500

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
