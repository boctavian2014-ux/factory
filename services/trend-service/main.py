"""
Trend service: HTTP API for trend detection.
POST /trends/update triggers scraping + analysis and stores trends in PostgreSQL.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db_dependency
from shared.models import Trend

from .trend_scraper import scrape_all
from .trend_analyzer import analyze_signals

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trends", tags=["trends"])


class UpdateTrendsRequest(BaseModel):
    tiktok_hashtags: list[str] | None = None
    youtube_keywords: list[str] | None = None
    reddit_subs: list[str] | None = None


class UpdateTrendsResponse(BaseModel):
    status: str
    trends_created: int
    trend_ids: list[int]


@router.post("/update", response_model=UpdateTrendsResponse)
def update_trends(
    body: UpdateTrendsRequest | None = None,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """
    Scrape trend signals from TikTok, YouTube, Google Trends, Reddit;
    analyze and store emerging trends in PostgreSQL.
    """
    body = body or UpdateTrendsRequest()
    signals = scrape_all(
        tiktok_hashtags=body.tiktok_hashtags,
        youtube_keywords=body.youtube_keywords,
        reddit_subs=body.reddit_subs,
    )
    analyzed = analyze_signals(signals)
    trend_ids = []
    for a in analyzed:
        trend = Trend(
            source=a["source"],
            keyword=a["keyword"],
            hashtags=a.get("hashtags") or [],
            trend_score=a["trend_score"],
            growth_rate=a["growth_rate"],
            engagement_velocity=a["engagement_velocity"],
            raw_signals=a.get("raw_signals"),
        )
        db.add(trend)
        db.flush()
        trend_ids.append(trend.id)
    db.commit()
    logger.info("Stored %d trends", len(trend_ids))
    return UpdateTrendsResponse(
        status="ok",
        trends_created=len(trend_ids),
        trend_ids=trend_ids,
    )
