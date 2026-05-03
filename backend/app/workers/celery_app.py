from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ticket_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.tasks.ticket_tasks",
        "app.workers.tasks.embedding_tasks",
        "app.workers.tasks.notification_tasks",
        "app.workers.tasks.analytics_tasks",
    ],
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
    task_routes={
        "app.workers.tasks.ticket_tasks.*":       {"queue": "ticket_processing"},
        "app.workers.tasks.embedding_tasks.*":    {"queue": "embedding"},
        "app.workers.tasks.notification_tasks.*": {"queue": "notification"},
        "app.workers.tasks.analytics_tasks.*":    {"queue": "analytics"},
    },
    beat_schedule={
        "sla-monitor-every-5min": {
            "task": "analytics_tasks.monitor_sla_breaches",
            "schedule": 300.0,
        },
        "daily-report-midnight": {
            "task": "analytics_tasks.generate_daily_report",
            "schedule": 86400.0,
        },
    },
)
