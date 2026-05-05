"""
Udyam Setu — Celery Application
Configured to use Redis as both broker and result backend.
"""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "udyam_setu",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks in app.services
celery_app.autodiscover_tasks(["app.services"])
