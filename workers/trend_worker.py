"""
Celery worker: trend detection. Scrapes signals, analyzes, stores in PostgreSQL.
"""
import logging
from shared.celery_app import celery_app
from shared.database import get_db
from shared.models import Trend

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.trend_worker.update_trends", bind=True)
def update_trends(self, tiktok_hashtags=None, youtube_keywords=None, reddit_subs=None):
    """Scrape and analyze trends; store in DB. Called by POST /trends/update or pipeline."""
    from services.trend_service.trend_scraper import scrape_all
    from services.trend_service.trend_analyzer import analyze_signals

    signals = scrape_all(
        tiktok_hashtags=tiktok_hashtags,
        youtube_keywords=youtube_keywords,
        reddit_subs=reddit_subs,
    )
    analyzed = analyze_signals(signals)
    trend_ids = []
    with get_db() as db:
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
    logger.info("Trend worker stored %d trends", len(trend_ids))
    return {"trend_ids": trend_ids}
