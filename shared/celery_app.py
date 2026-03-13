"""
Celery application for AI Content Factory.
Broker: Redis. Result backend: Redis.
Queues: trend, idea, script, video, virality.
"""
from celery import Celery

from shared.config import settings

app = Celery(
    "ai_content_factory",
    broker=settings.redis_celery_broker,
    backend=settings.redis_celery_result,
    include=[
        "workers.trend_worker",
        "workers.idea_worker",
        "workers.script_worker",
        "workers.video_worker",
        "workers.virality_worker",
    ],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_routes={
        "workers.trend_worker.*": {"queue": settings.celery_trend_queue},
        "workers.idea_worker.*": {"queue": settings.celery_idea_queue},
        "workers.script_worker.*": {"queue": settings.celery_script_queue},
        "workers.video_worker.*": {"queue": settings.celery_video_queue},
        "workers.virality_worker.*": {"queue": settings.celery_virality_queue},
    },
)
