"""
Celery worker: script generation. Converts idea to script and stores in PostgreSQL.
"""
import logging
from shared.celery_app import celery_app
from shared.database import get_db
from shared.models import Script as ScriptModel

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.script_worker.generate_script", bind=True)
def generate_script_task(
    self,
    idea_id: int,
    hook: str,
    concept: str,
    trend_angle: str = "",
    duration_seconds: float = 30.0,
):
    """Generate script for an idea and persist."""
    from services.script_service.script_generator import generate_script

    script_data = generate_script(idea_id, hook, concept, trend_angle, duration_seconds)
    with get_db() as db:
        row = ScriptModel(
            idea_id=idea_id,
            hook_text=script_data["hook_text"],
            narration=script_data["narration"],
            duration_seconds=script_data["duration_seconds"],
            scene_breakdown=script_data["scene_breakdown"],
            text_overlays=script_data["text_overlays"],
        )
        db.add(row)
        db.flush()
        script_id = row.id
    logger.info("Script worker stored script id=%s for idea_id=%s", script_id, idea_id)
    return {"script_id": script_id, "scene_breakdown": script_data["scene_breakdown"], "narration": script_data["narration"], "hook_text": script_data["hook_text"], "duration_seconds": script_data["duration_seconds"]}
