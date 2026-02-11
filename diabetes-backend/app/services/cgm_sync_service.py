"""
Diyabet Takip API - CGM Sync Service
Continuous Glucose Monitor data synchronization with device providers
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.cgm import CGMDevice, CGMReading
from app.models.audit import AuditLog
from app.config import get_settings

settings = get_settings()


class CGMProvider:
    """Base class for CGM device providers"""
    
    async def authenticate(self, credentials: dict) -> bool:
        raise NotImplementedError
    
    async def fetch_readings(self, device_id: str, since: datetime) -> List[Dict]:
        raise NotImplementedError


class DexcomProvider(CGMProvider):
    """
    Dexcom CGM Provider (G6, G7)
    
    API Docs: https://developer.dexcom.com/
    
    Note: Requires Dexcom Developer Account and OAuth2.
    This is a skeleton implementation for future integration.
    """
    
    BASE_URL = "https://api.dexcom.com/v3"
    SANDBOX_URL = "https://sandbox-api.dexcom.com/v3"
    
    def __init__(self, client_id: str = "", client_secret: str = "", sandbox: bool = True):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = self.SANDBOX_URL if sandbox else self.BASE_URL
        self.access_token = None
    
    async def authenticate(self, credentials: dict) -> bool:
        """OAuth2 authentication with Dexcom"""
        # In production: implement full OAuth2 flow
        # 1. Redirect user to Dexcom auth page
        # 2. Get authorization code
        # 3. Exchange code for access/refresh tokens
        print(f"[DEXCOM] Authentication requested (sandbox mode)")
        return False
    
    async def fetch_readings(self, device_id: str, since: datetime) -> List[Dict]:
        """Fetch glucose readings from Dexcom API"""
        if not self.access_token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/self/egvs",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    params={
                        "startDate": since.isoformat(),
                        "endDate": datetime.utcnow().isoformat()
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return [
                        {
                            "glucose_value": r["value"],
                            "trend": r.get("trend", "flat"),
                            "timestamp": r["systemTime"]
                        }
                        for r in data.get("records", [])
                    ]
        except Exception as e:
            print(f"[DEXCOM] Fetch error: {e}")
        
        return []


class FreestyleLibreProvider(CGMProvider):
    """
    Abbott FreeStyle Libre Provider
    
    Note: Abbott's LibreLink API is not publicly available.
    This uses the unofficial LibreLinkUp API approach.
    """
    
    BASE_URL = "https://api-eu.libreview.io"
    
    def __init__(self):
        self.token = None
    
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with LibreLinkUp"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/llu/auth/login",
                    headers={"Content-Type": "application/json", "product": "llu.android", "version": "4.7.0"},
                    json={
                        "email": credentials.get("email", ""),
                        "password": credentials.get("password", "")
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("data", {}).get("authTicket", {}).get("token")
                    return self.token is not None
        except Exception as e:
            print(f"[LIBRE] Auth error: {e}")
        
        return False
    
    async def fetch_readings(self, device_id: str, since: datetime) -> List[Dict]:
        """Fetch readings from LibreLinkUp"""
        if not self.token:
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                # Get connections
                response = await client.get(
                    f"{self.BASE_URL}/llu/connections",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json",
                        "product": "llu.android",
                        "version": "4.7.0"
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    connections = data.get("data", [])
                    
                    readings = []
                    for conn in connections:
                        glucose_item = conn.get("glucoseItem", {})
                        if glucose_item:
                            readings.append({
                                "glucose_value": glucose_item.get("Value", 0),
                                "trend": str(glucose_item.get("TrendArrow", "flat")),
                                "timestamp": glucose_item.get("Timestamp", datetime.utcnow().isoformat())
                            })
                    
                    return readings
        except Exception as e:
            print(f"[LIBRE] Fetch error: {e}")
        
        return []


# Provider factory
PROVIDERS = {
    "DEXCOM_G6": DexcomProvider,
    "DEXCOM_G7": DexcomProvider,
    "FREESTYLE_LIBRE": FreestyleLibreProvider,
    "FREESTYLE_LIBRE_2": FreestyleLibreProvider,
    "FREESTYLE_LIBRE_3": FreestyleLibreProvider,
}


def get_provider(device_type: str) -> Optional[CGMProvider]:
    """Get CGM provider for a device type"""
    provider_cls = PROVIDERS.get(device_type)
    if provider_cls:
        return provider_cls()
    return None


async def sync_device_readings(
    db: AsyncSession,
    device: CGMDevice,
    hours: int = 24
) -> int:
    """
    Sync readings from CGM device provider
    Returns number of new readings stored
    """
    provider = get_provider(device.device_type)
    if not provider:
        print(f"[CGM] No provider for {device.device_type}")
        return 0
    
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = await provider.fetch_readings(str(device.device_id), since)
    
    count = 0
    for reading in readings:
        # Check if reading already exists (avoid duplicates)
        existing = await db.execute(
            select(CGMReading).where(
                and_(
                    CGMReading.device_id == device.id,
                    CGMReading.timestamp == reading["timestamp"]
                )
            )
        )
        
        if not existing.scalar_one_or_none():
            new_reading = CGMReading(
                device_id=device.id,
                glucose_value=reading["glucose_value"],
                trend=reading.get("trend"),
                timestamp=reading["timestamp"]
            )
            db.add(new_reading)
            count += 1
    
    if count > 0:
        # Update last sync time
        device.last_sync = datetime.utcnow()
    
    return count
