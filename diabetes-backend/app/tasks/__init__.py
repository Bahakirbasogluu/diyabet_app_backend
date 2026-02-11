"""
Diyabet Takip API - Tasks Package
Celery background tasks
"""

from app.tasks.reminders import (
    send_morning_reminders,
    send_glucose_check_reminders,
    generate_daily_summaries,
    send_medication_reminder,
    send_appointment_reminder
)

from app.tasks.notifications import (
    send_glucose_alert,
    send_bulk_notification,
    send_topic_notification,
    sync_cgm_data
)

__all__ = [
    "send_morning_reminders",
    "send_glucose_check_reminders",
    "generate_daily_summaries",
    "send_medication_reminder",
    "send_appointment_reminder",
    "send_glucose_alert",
    "send_bulk_notification",
    "send_topic_notification",
    "sync_cgm_data"
]
