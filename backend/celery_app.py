from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "wexa",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.ingestion", "app.tasks.alerts", "app.tasks.reports"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Celery Beat schedule
    beat_schedule={
        "evaluate-alert-rules": {
            "task": "app.tasks.alerts.evaluate_all_rules",
            "schedule": 60.0,  # Every 60 seconds
        },
    },
)
