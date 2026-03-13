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


class TrendItem(BaseModel):
    id: int
    source: str
    keyword: str
    hashtags: list[str]
    trend_score: float
    growth_rate: float
    engagement_velocity: float


class UpdateTrendsResponse(BaseModel):
    status: str
    trends_created: int
    trend_ids: list[int]
    trends: list[TrendItem] = []


@router.get("/list", response_model=list[TrendItem])
def list_trends(
    limit: int = 30,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Return latest viral trends from DB (for frontend display)."""
    rows = db.query(Trend).order_by(Trend.updated_at.desc()).limit(max(1, min(limit, 100))).all()
    return [
        TrendItem(
            id=r.id,
            source=r.source or "",
            keyword=r.keyword or "",
            hashtags=r.hashtags or [],
            trend_score=r.trend_score or 0.0,
            growth_rate=r.growth_rate or 0.0,
            engagement_velocity=r.engagement_velocity or 0.0,
        )
        for r in rows
    ]


@router.post("/update", response_model=UpdateTrendsResponse)
def update_trends(
    body: UpdateTrendsRequest | None = None,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """
    Scrape trend signals from TikTok, YouTube, Google Trends, Reddit;
    analyze and store emerging trends in PostgreSQL.
    Returns the created trends so the frontend can show last viral trends.
    """
    body = body or UpdateTrendsRequest()
    signals = scrape_all(
        tiktok_hashtags=body.tiktok_hashtags,
        youtube_keywords=body.youtube_keywords,
        reddit_subs=body.reddit_subs,
    )
    analyzed = analyze_signals(signals)
    trend_ids = []
    trend_items: list[TrendItem] = []
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
        trend_items.append(TrendItem(
            id=trend.id,
            source=trend.source or "",
            keyword=trend.keyword or "",
            hashtags=trend.hashtags or [],
            trend_score=trend.trend_score or 0.0,
            growth_rate=trend.growth_rate or 0.0,
            engagement_velocity=trend.engagement_velocity or 0.0,
        ))
    db.commit()
    logger.info("Stored %d trends", len(trend_ids))
    return UpdateTrendsResponse(
        status="ok",
        trends_created=len(trend_ids),
        trend_ids=trend_ids,
        trends=trend_items,
    )
