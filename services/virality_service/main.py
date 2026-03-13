"""
Virality service: HTTP API for scoring video virality.
POST /virality/score returns virality_score (0-1) and optional approval flag.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.config import settings
from shared.database import get_db_dependency
from shared.models import Video as VideoModel

from .virality_model import load_model, predict_virality

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/virality", tags=["virality"])

_model_cache = None


def get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = load_model(settings.virality_model_path)
    return _model_cache


class ScoreViralityRequest(BaseModel):
    video_id: int
    trend_score: float
    hashtags: list[str]
    caption_length: int
    video_duration: float
    topic_embedding: list[float] | None = None


class ScoreViralityResponse(BaseModel):
    status: str
    video_id: int
    virality_score: float
    approved: bool


@router.post("/score", response_model=ScoreViralityResponse)
def score_virality(
    body: ScoreViralityRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Score a video for virality and update DB; set approved if above threshold."""
    model = get_model()
    score = predict_virality(
        trend_score=body.trend_score,
        hashtags=body.hashtags,
        caption_length=body.caption_length,
        video_duration=body.video_duration,
        topic_embedding=body.topic_embedding,
        model=model,
    )
    approved = score >= settings.virality_threshold
    video = db.query(VideoModel).filter(VideoModel.id == body.video_id).first()
    if video:
        video.virality_score = score
        video.approved = approved
        db.commit()
    return ScoreViralityResponse(
        status="ok",
        video_id=body.video_id,
        virality_score=round(score, 4),
        approved=approved,
    )
