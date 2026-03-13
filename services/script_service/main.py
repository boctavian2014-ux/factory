"""
Script service: HTTP API for generating scripts from video ideas.
POST /scripts/generate creates script (hook + narration + scene breakdown) and stores it.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db_dependency
from shared.models import Script as ScriptModel

from .script_generator import generate_script

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scripts", tags=["scripts"])


class GenerateScriptRequest(BaseModel):
    idea_id: int
    hook: str
    concept: str
    trend_angle: str = ""
    duration_seconds: float = 30.0


class GenerateScriptResponse(BaseModel):
    status: str
    script_id: int


@router.post("/generate", response_model=GenerateScriptResponse)
def create_script(
    body: GenerateScriptRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Generate script from idea and persist to PostgreSQL."""
    script_data = generate_script(
        idea_id=body.idea_id,
        hook=body.hook,
        concept=body.concept,
        trend_angle=body.trend_angle,
        duration_seconds=body.duration_seconds,
    )
    row = ScriptModel(
        idea_id=body.idea_id,
        hook_text=script_data["hook_text"],
        narration=script_data["narration"],
        duration_seconds=script_data["duration_seconds"],
        scene_breakdown=script_data["scene_breakdown"],
        text_overlays=script_data["text_overlays"],
    )
    db.add(row)
    db.commit()
    logger.info("Stored script id=%s for idea_id=%s", row.id, body.idea_id)
    return GenerateScriptResponse(status="ok", script_id=row.id)
