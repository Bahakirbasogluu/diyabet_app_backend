"""
Diyabet Takip API - Health Router
Health data management endpoints
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_client_ip
from app.models.user import User
from app.models.health import HealthRecordType
from app.schemas.health import (
    HealthRecordCreate,
    HealthRecordResponse,
    HealthRecordList,
    HealthStats
)
from app.schemas.auth import MessageResponse
from app.services.health_service import (
    create_health_record,
    get_health_history,
    get_health_stats,
    delete_health_record
)

router = APIRouter()


@router.post("/", response_model=HealthRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_health_record(
    data: HealthRecordCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new health record (glucose, weight, blood pressure, etc.)
    """
    try:
        record = await create_health_record(
            db, current_user.id, data, get_client_ip(request)
        )
        return record
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=HealthRecordList)
async def get_history(
    record_type: Optional[HealthRecordType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get health record history with optional filters
    """
    records, total = await get_health_history(
        db, current_user.id, record_type, start_date, end_date, page, page_size
    )
    
    return HealthRecordList(
        items=records,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total
    )


@router.get("/stats", response_model=HealthStats)
async def get_stats(
    record_type: HealthRecordType,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get statistics for a specific health record type
    """
    stats = await get_health_stats(db, current_user.id, record_type, days)
    return HealthStats(**stats)


@router.delete("/{record_id}", response_model=MessageResponse)
async def delete_record(
    record_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a health record
    """
    success = await delete_health_record(
        db, current_user.id, record_id, get_client_ip(request)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kayıt bulunamadı"
        )
    
    return MessageResponse(message="Kayıt silindi")
