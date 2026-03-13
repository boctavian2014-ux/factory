"""
Idea service: HTTP API for generating video ideas from trends.
POST /ideas/generate creates 50–100 ideas per trend and stores them.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db_dependency
from shared.models import VideoIdea as VideoIdeaModel

from .idea_generator import generate_ideas_for_trend

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ideas", tags=["ideas"])


class GenerateIdeasRequest(BaseModel):
    trend_id: int
    keyword: str
    trend_score: float = 0.5
    source: str = "tiktok"
    count: int | None = None


class GenerateIdeasResponse(BaseModel):
    status: str
    ideas_created: int
    idea_ids: list[int]


@router.post("/generate", response_model=GenerateIdeasResponse)
def generate_ideas(
    body: GenerateIdeasRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Generate 50–100 video ideas for a trend and persist to PostgreSQL."""
    ideas = generate_ideas_for_trend(
        trend_id=body.trend_id,
        keyword=body.keyword,
        trend_score=body.trend_score,
        source=body.source,
        count=body.count,
    )
    idea_ids = []
    for idea in ideas:
        row = VideoIdeaModel(
            trend_id=body.trend_id,
            hook=idea["hook"],
            concept=idea["concept"],
            caption=idea["caption"],
            hashtags=idea["hashtags"],
            trend_angle=idea["trend_angle"],
        )
        db.add(row)
        db.flush()
        idea_ids.append(row.id)
    db.commit()
    logger.info("Stored %d ideas for trend %s", len(idea_ids), body.trend_id)
    return GenerateIdeasResponse(
        status="ok",
        ideas_created=len(idea_ids),
        idea_ids=idea_ids,
    )
