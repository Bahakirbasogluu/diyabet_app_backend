"""
Diyabet Takip API - Firebase Service
Firebase Admin SDK for push notifications
"""

import json
from typing import Optional, List
from pathlib import Path

# Firebase Admin SDK (optional import)
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from app.config import get_settings

settings = get_settings()


class FirebaseService:
    """Firebase Cloud Messaging service for push notifications"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls, credentials_path: Optional[str] = None):
        """
        Initialize Firebase Admin SDK
        
        Args:
            credentials_path: Path to firebase-adminsdk.json file
        """
        if not FIREBASE_AVAILABLE:
            print("[FIREBASE] firebase-admin not installed. Push notifications disabled.")
            return False
        
        if cls._initialized:
            return True
        
        # Try to find credentials
        if credentials_path is None:
            # Check common locations
            possible_paths = [
                "firebase-adminsdk.json",
                "app/firebase-adminsdk.json",
                "../firebase-adminsdk.json",
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    credentials_path = path
                    break
        
        if credentials_path is None or not Path(credentials_path).exists():
            print("[FIREBASE] firebase-adminsdk.json not found. Push notifications disabled.")
            return False
        
        try:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)
            cls._initialized = True
            print("[FIREBASE] Initialized successfully")
            return True
        except Exception as e:
            print(f"[FIREBASE] Initialization failed: {e}")
            return False
    
    @classmethod
    async def send_notification(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None
    ) -> bool:
        """
        Send push notification to a single device
        
        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Optional data payload
            image_url: Optional image URL
        """
        if not cls._initialized:
            print(f"[FIREBASE] Not initialized. Would send: {title}")
            return False
        
        try:
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="notification_icon",
                        color="#2563eb"
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            badge=1,
                            sound="default"
                        )
                    )
                )
            )
            
            response = messaging.send(message)
            print(f"[FIREBASE] Message sent: {response}")
            return True
            
        except Exception as e:
            print(f"[FIREBASE] Send failed: {e}")
            return False
    
    @classmethod
    async def send_multicast(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> int:
        """
        Send push notification to multiple devices
        
        Returns: Number of successful sends
        """
        if not cls._initialized or not tokens:
            return 0
        
        try:
            notification = messaging.Notification(title=title, body=body)
            message = messaging.MulticastMessage(
                notification=notification,
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            print(f"[FIREBASE] Multicast: {response.success_count}/{len(tokens)} successful")
            return response.success_count
            
        except Exception as e:
            print(f"[FIREBASE] Multicast failed: {e}")
            return 0
    
    @classmethod
    async def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: Optional[dict] = None
    ) -> bool:
        """Send push notification to a topic"""
        if not cls._initialized:
            return False
        
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                topic=topic
            )
            
            response = messaging.send(message)
            print(f"[FIREBASE] Topic message sent: {response}")
            return True
            
        except Exception as e:
            print(f"[FIREBASE] Topic send failed: {e}")
            return False
    
    @classmethod
    async def subscribe_to_topic(cls, token: str, topic: str) -> bool:
        """Subscribe a device to a topic"""
        if not cls._initialized:
            return False
        
        try:
            response = messaging.subscribe_to_topic([token], topic)
            return response.success_count > 0
        except Exception as e:
            print(f"[FIREBASE] Subscribe failed: {e}")
            return False


# Global instance
firebase = FirebaseService()


# Convenience functions
async def send_push_notification(
    fcm_token: str,
    title: str,
    body: str,
    data: Optional[dict] = None
) -> bool:
    """Send push notification to a device"""
    return await firebase.send_notification(fcm_token, title, body, data)


async def send_glucose_alert(fcm_token: str, value: float, alert_type: str = "high") -> bool:
    """Send glucose alert notification"""
    if alert_type == "high":
        title = "⚠️ Yüksek Kan Şekeri"
        body = f"Kan şekeriniz {value} mg/dL. Lütfen kontrol edin."
    else:
        title = "🔴 Düşük Kan Şekeri"
        body = f"Kan şekeriniz {value} mg/dL. Acil müdahale gerekebilir!"
    
    return await firebase.send_notification(
        fcm_token, title, body,
        data={"type": "glucose_alert", "value": str(value), "alert_type": alert_type}
    )


async def send_reminder(fcm_token: str, reminder_type: str) -> bool:
    """Send reminder notification"""
    reminders = {
        "glucose_check": ("⏰ Ölçüm Zamanı", "Kan şekerinizi ölçme zamanı geldi!"),
        "medication": ("💊 İlaç Hatırlatması", "İlaçlarınızı alma zamanı!"),
        "exercise": ("🏃 Egzersiz Zamanı", "Günlük egzersiz hedefiniz için hareket edin!"),
        "water": ("💧 Su İçin", "Sağlığınız için su içmeyi unutmayın!"),
    }
    
    if reminder_type not in reminders:
        return False
    
    title, body = reminders[reminder_type]
    return await firebase.send_notification(
        fcm_token, title, body,
        data={"type": "reminder", "reminder_type": reminder_type}
    )
