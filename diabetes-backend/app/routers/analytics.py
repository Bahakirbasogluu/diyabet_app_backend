"""
Diyabet Takip API - Analytics Router
Analytics and trend endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.health import HealthRecordType
from app.services.analytics_service import get_summary, get_trends

router = APIRouter()


@router.get("/summary")
async def summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary statistics for the user's health data
    """
    return await get_summary(db, current_user.id, days)


@router.get("/trends")
async def trends(
    record_type: HealthRecordType,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get trend data for charts
    """
    return await get_trends(db, current_user.id, record_type, days)
