"""
Celery worker: idea generation. Generates 50–100 ideas per trend and stores in PostgreSQL.
"""
import logging
from shared.celery_app import celery_app
from shared.database import get_db
from shared.models import VideoIdea as VideoIdeaModel

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.idea_worker.generate_ideas", bind=True)
def generate_ideas(self, trend_id: int, keyword: str, trend_score: float = 0.5, source: str = "tiktok", count: int | None = None):
    """Generate video ideas for a trend and persist."""
    from services.idea_service.idea_generator import generate_ideas_for_trend

    ideas = generate_ideas_for_trend(trend_id, keyword, trend_score, source, count)
    idea_ids = []
    with get_db() as db:
        for idea in ideas:
            row = VideoIdeaModel(
                trend_id=trend_id,
                hook=idea["hook"],
                concept=idea["concept"],
                caption=idea["caption"],
                hashtags=idea["hashtags"],
                trend_angle=idea["trend_angle"],
            )
            db.add(row)
            db.flush()
            idea_ids.append(row.id)
    logger.info("Idea worker stored %d ideas for trend %s", len(idea_ids), trend_id)
    return {"idea_ids": idea_ids}
