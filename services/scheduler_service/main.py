"""
Scheduler service: HTTP API for creating schedule and exporting CSV.
POST /schedule/create creates scheduled posts for approved videos and optionally exports CSV.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.config import settings
from shared.database import get_db_dependency
from shared.models import Video as VideoModel
from shared.models import Script as ScriptModel
from shared.models import VideoIdea as VideoIdeaModel
from shared.models import ScheduledPost

from .scheduler import schedule_videos
from .exporter import export_to_csv

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/schedule", tags=["schedule"])


class CreateScheduleRequest(BaseModel):
    video_ids: list[int] | None = None  # If None, use all approved
    platforms: list[str] | None = None
    interval_minutes: int = 180
    export_csv: bool = True


class CreateScheduleResponse(BaseModel):
    status: str
    scheduled_count: int
    csv_path: str | None = None


@router.post("/create", response_model=CreateScheduleResponse)
def create_schedule(
    body: CreateScheduleRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """Create scheduled posts for approved videos; optionally export CSV."""
    if body.video_ids:
        videos = db.query(VideoModel).filter(
            VideoModel.id.in_(body.video_ids),
            VideoModel.approved == True,
        ).all()
    else:
        videos = db.query(VideoModel).filter(VideoModel.approved == True).all()

    video_ids = [v.id for v in videos]
    if not video_ids:
        return CreateScheduleResponse(status="ok", scheduled_count=0, csv_path=None)

    slots = schedule_videos(
        video_ids,
        platforms=body.platforms,
        interval_minutes=body.interval_minutes,
    )
    video_by_id = {v.id: v for v in videos}
    script_by_id = {v.script_id: db.get(ScriptModel, v.script_id) for v in videos if v.script_id}
    idea_by_script_id = {}
    for script_id, script in script_by_id.items():
        if script and script.idea_id:
            idea_by_script_id[script_id] = db.get(VideoIdeaModel, script.idea_id)
    rows = []
    for s in slots:
        vid = video_by_id.get(s["video_id"])
        if not vid:
            continue
        idea = idea_by_script_id.get(vid.script_id) if vid.script_id else None
        caption = (idea.caption or "") if idea else ""
        hashtags = list(idea.hashtags or []) if idea else []
        post = ScheduledPost(
            video_id=vid.id,
            platform=s["platform"],
            caption=caption,
            hashtags=hashtags,
            scheduled_time=s["scheduled_time"],
        )
        db.add(post)
        db.flush()
        rows.append({
            "video_file": vid.file_path,
            "caption": caption,
            "hashtags": hashtags,
            "platform": post.platform,
            "scheduled_time": post.scheduled_time,
        })
    db.commit()

    csv_path = None
    if body.export_csv and rows:
        csv_dir = Path(settings.csv_dir)
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_dir / f"schedule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        export_to_csv(rows, csv_path)
        csv_path = str(csv_path)

    logger.info("Scheduled %d posts", len(rows))
    return CreateScheduleResponse(
        status="ok",
        scheduled_count=len(rows),
        csv_path=csv_path,
    )
