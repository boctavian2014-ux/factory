"""
Celery worker: virality scoring. Scores video and updates approved flag.
"""
import logging
from shared.celery_app import celery_app
from shared.config import settings
from shared.database import get_db
from shared.models import Video as VideoModel

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.virality_worker.score_video", bind=True)
def score_video_task(
    self,
    video_id: int,
    trend_score: float,
    hashtags: list,
    caption_length: int,
    video_duration: float,
    topic_embedding: list | None = None,
):
    """Score video for virality and update DB."""
    from services.virality_service.virality_model import load_model, predict_virality

    model = load_model(settings.virality_model_path)
    score = predict_virality(
        trend_score=trend_score,
        hashtags=hashtags or [],
        caption_length=caption_length,
        video_duration=video_duration,
        topic_embedding=topic_embedding,
        model=model,
    )
    approved = score >= settings.virality_threshold
    with get_db() as db:
        video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
        if video:
            video.virality_score = score
            video.approved = approved
            db.commit()
    logger.info("Virality worker video_id=%s score=%.4f approved=%s", video_id, score, approved)
    return {"video_id": video_id, "virality_score": score, "approved": approved}
