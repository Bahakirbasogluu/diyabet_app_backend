"""
Diyabet Takip API - Notification Service
Firebase Cloud Messaging for push notifications
"""

from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.config import get_settings

settings = get_settings()


async def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> bool:
    """
    Send push notification via Firebase Cloud Messaging
    
    Note: In production, initialize Firebase Admin SDK with credentials:
    
    import firebase_admin
    from firebase_admin import credentials, messaging
    
    cred = credentials.Certificate("path/to/firebase-adminsdk.json")
    firebase_admin.initialize_app(cred)
    """
    # For now, just log the notification
    # In production, use Firebase Admin SDK
    print(f"[PUSH] To: {fcm_token[:20]}... Title: {title}, Body: {body}")
    return True


async def send_high_glucose_alert(
    db: AsyncSession,
    user_id: UUID,
    glucose_value: float
):
    """Send alert for high glucose reading"""
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.fcm_token:
        await send_push_notification(
            fcm_token=user.fcm_token,
            title="⚠️ Yüksek Kan Şekeri Uyarısı",
            body=f"Kan şekeriniz {glucose_value} mg/dL olarak ölçüldü. Lütfen kontrol edin.",
            data={"type": "glucose_alert", "value": str(glucose_value)}
        )


async def send_low_glucose_alert(
    db: AsyncSession,
    user_id: UUID,
    glucose_value: float
):
    """Send alert for low glucose reading"""
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user and user.fcm_token:
        await send_push_notification(
            fcm_token=user.fcm_token,
            title="🔴 Düşük Kan Şekeri Uyarısı",
            body=f"Kan şekeriniz {glucose_value} mg/dL. Acil müdahale gerekebilir!",
            data={"type": "glucose_alert_low", "value": str(glucose_value)}
        )


async def send_reminder(
    db: AsyncSession,
    user_id: UUID,
    reminder_type: str
):
    """Send reminder notification"""
    
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.fcm_token:
        return
    
    reminders = {
        "glucose_check": ("⏰ Ölçüm Hatırlatması", "Kan şekerinizi ölçme zamanı geldi!"),
        "medication": ("💊 İlaç Hatırlatması", "İlaçlarınızı alma zamanı!"),
        "exercise": ("🏃 Egzersiz Hatırlatması", "Günlük egzersiz zamanı!"),
    }
    
    if reminder_type in reminders:
        title, body = reminders[reminder_type]
        await send_push_notification(
            fcm_token=user.fcm_token,
            title=title,
            body=body,
            data={"type": "reminder", "reminder_type": reminder_type}
        )
