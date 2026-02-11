"""
Diyabet Takip API - Celery Configuration
Background task queue for scheduled tasks and reminders
"""

from celery import Celery
from datetime import timedelta
import os

# Get Redis URL from environment
REDIS_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://localhost:6379/0"
)

# Create Celery app
celery_app = Celery(
    "diyabet_api",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.reminders", "app.tasks.notifications"]
)

# Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Daily reminder check at 9 AM
        "morning-reminder-check": {
            "task": "app.tasks.reminders.send_morning_reminders",
            "schedule": timedelta(hours=24),
            "args": (),
        },
        # Hourly glucose check reminder
        "glucose-check-reminder": {
            "task": "app.tasks.reminders.send_glucose_check_reminders",
            "schedule": timedelta(hours=4),
            "args": (),
        },
        # Daily analytics summary
        "daily-analytics": {
            "task": "app.tasks.reminders.generate_daily_summaries",
            "schedule": timedelta(hours=24),
            "args": (),
        },
    },
    
    # Worker settings
    worker_pool_restarts=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Optional: Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
