"""
Repo service: GitHub repo to video idea (RepoClip-style).
POST /repo/analyze — returns idea payload for use in pipeline.
POST /repo/to-video — analyze repo, create trend + idea in DB, return idea_id for script/video.
"""
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db_dependency
from shared.models import Trend, VideoIdea as VideoIdeaModel

from .repo_analyzer import analyze_repo

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/repo", tags=["repo"])


class RepoAnalyzeRequest(BaseModel):
    repo_url: str  # e.g. https://github.com/owner/repo


@router.post("/analyze")
def repo_analyze(body: RepoAnalyzeRequest) -> dict[str, Any]:
    """
    Analyze a GitHub repo and return a video idea (hook, concept, caption, hashtags).
    Use the returned idea with POST /ideas/generate (with a synthetic trend_id) or /scripts/generate.
    """
    return analyze_repo(body.repo_url.strip())


class RepoToVideoRequest(BaseModel):
    repo_url: str


class RepoToVideoResponse(BaseModel):
    status: str
    trend_id: int
    idea_id: int
    idea: dict[str, Any]


@router.post("/to-video", response_model=RepoToVideoResponse)
def repo_to_video(
    body: RepoToVideoRequest,
    db: Session = Depends(get_db_dependency),
) -> Any:
    """
    Analyze repo, create a synthetic trend and one video idea in DB.
    Returns trend_id and idea_id so you can call POST /scripts/generate then POST /videos/render.
    """
    result = analyze_repo(body.repo_url.strip())
    if not result.get("ok") or not result.get("idea"):
        raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
    idea_payload = result["idea"]
    repo_info = result.get("repo") or {}
    trend = Trend(
        source="github",
        keyword=repo_info.get("repo", "repo"),
        hashtags=idea_payload.get("hashtags", []),
        trend_score=0.5,
        growth_rate=0.0,
        engagement_velocity=0.0,
        raw_signals={"repo_url": body.repo_url, "owner": repo_info.get("owner")},
    )
    db.add(trend)
    db.flush()
    idea_row = VideoIdeaModel(
        trend_id=trend.id,
        hook=idea_payload["hook"],
        concept=idea_payload["concept"],
        caption=idea_payload.get("caption", ""),
        hashtags=idea_payload.get("hashtags", []),
        trend_angle=idea_payload.get("trend_angle", "repo"),
    )
    db.add(idea_row)
    db.flush()
    db.commit()
    logger.info("Repo to video: trend_id=%s idea_id=%s", trend.id, idea_row.id)
    return RepoToVideoResponse(
        status="ok",
        trend_id=trend.id,
        idea_id=idea_row.id,
        idea=idea_payload,
    )
