"""
Diyabet Takip API - CGM Router (Skeleton)
Continuous Glucose Monitor integration endpoints for future implementation
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.cgm import CGMDevice, CGMReading

router = APIRouter()


# Schemas for CGM
class CGMDeviceCreate(BaseModel):
    device_type: str
    device_id: str | None = None
    device_name: str | None = None


class CGMDeviceResponse(BaseModel):
    id: UUID
    device_type: str
    device_id: str | None
    device_name: str | None
    is_active: bool
    
    class Config:
        from_attributes = True


class CGMReadingResponse(BaseModel):
    id: UUID
    glucose_value: float
    trend: str | None
    timestamp: str
    
    class Config:
        from_attributes = True


@router.post("/device", response_model=CGMDeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_device(
    data: CGMDeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new CGM device (skeleton for future integration)
    
    Supported device types:
    - DEXCOM_G6
    - DEXCOM_G7
    - FREESTYLE_LIBRE
    - FREESTYLE_LIBRE_2
    - FREESTYLE_LIBRE_3
    - MEDTRONIC_GUARDIAN
    """
    device = CGMDevice(
        user_id=current_user.id,
        device_type=data.device_type,
        device_id=data.device_id,
        device_name=data.device_name
    )
    db.add(device)
    await db.flush()
    
    return device


@router.get("/devices", response_model=List[CGMDeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all registered CGM devices
    """
    result = await db.execute(
        select(CGMDevice).where(CGMDevice.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/device/{device_id}")
async def remove_device(
    device_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a CGM device
    """
    result = await db.execute(
        select(CGMDevice).where(
            CGMDevice.id == device_id,
            CGMDevice.user_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cihaz bulunamadı"
        )
    
    await db.delete(device)
    return {"message": "Cihaz silindi"}


@router.get("/readings", response_model=List[CGMReadingResponse])
async def get_readings(
    device_id: UUID | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get CGM readings (skeleton - will be populated by device sync)
    """
    query = select(CGMReading).join(CGMDevice).where(
        CGMDevice.user_id == current_user.id
    )
    
    if device_id:
        query = query.where(CGMReading.device_id == device_id)
    
    query = query.order_by(CGMReading.timestamp.desc()).limit(limit)
    
    result = await db.execute(query)
    readings = result.scalars().all()
    
    return [
        CGMReadingResponse(
            id=r.id,
            glucose_value=r.glucose_value,
            trend=r.trend,
            timestamp=r.timestamp.isoformat()
        )
        for r in readings
    ]
