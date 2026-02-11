"""
Diyabet Takip API - Health Service
Health data business logic
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.health import HealthRecord, HealthRecordType
from app.models.audit import AuditLog
from app.schemas.health import HealthRecordCreate
from app.utils.validators import validate_health_value


async def create_health_record(
    db: AsyncSession,
    user_id: UUID,
    data: HealthRecordCreate,
    ip_address: Optional[str] = None
) -> HealthRecord:
    """Create a new health record"""
    
    # Validate value
    is_valid, error = validate_health_value(data.type, data.value)
    if not is_valid:
        raise ValueError(error)
    
    # Get default unit if not provided
    unit = data.unit or HealthRecord.get_default_unit(data.type)
    
    # Use provided timestamp or current time
    timestamp = data.timestamp or datetime.utcnow()
    
    record = HealthRecord(
        user_id=user_id,
        type=data.type,
        value=data.value,
        unit=unit,
        timestamp=timestamp,
        note=data.note
    )
    
    db.add(record)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="HEALTH_RECORD_CREATE",
        resource="health_record",
        details={"type": data.type.value, "value": data.value},
        ip_address=ip_address
    )
    db.add(audit)
    
    return record


async def get_health_history(
    db: AsyncSession,
    user_id: UUID,
    record_type: Optional[HealthRecordType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20
) -> Tuple[List[HealthRecord], int]:
    """Get paginated health records with optional filters"""
    
    # Build base query
    query = select(HealthRecord).where(HealthRecord.user_id == user_id)
    count_query = select(func.count(HealthRecord.id)).where(HealthRecord.user_id == user_id)
    
    # Apply filters
    if record_type:
        query = query.where(HealthRecord.type == record_type)
        count_query = count_query.where(HealthRecord.type == record_type)
    
    if start_date:
        query = query.where(HealthRecord.timestamp >= start_date)
        count_query = count_query.where(HealthRecord.timestamp >= start_date)
    
    if end_date:
        query = query.where(HealthRecord.timestamp <= end_date)
        count_query = count_query.where(HealthRecord.timestamp <= end_date)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination and ordering
    query = query.order_by(HealthRecord.timestamp.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return list(records), total


async def get_health_stats(
    db: AsyncSession,
    user_id: UUID,
    record_type: HealthRecordType,
    days: int = 30
) -> dict:
    """Get statistics for a specific health record type"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get aggregated stats
    result = await db.execute(
        select(
            func.count(HealthRecord.id).label("count"),
            func.avg(HealthRecord.value).label("average"),
            func.min(HealthRecord.value).label("min_value"),
            func.max(HealthRecord.value).label("max_value")
        )
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.type == record_type,
                HealthRecord.timestamp >= start_date
            )
        )
    )
    
    stats = result.one()
    
    # Get latest value
    latest_result = await db.execute(
        select(HealthRecord)
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.type == record_type
            )
        )
        .order_by(HealthRecord.timestamp.desc())
        .limit(1)
    )
    latest = latest_result.scalar_one_or_none()
    
    return {
        "type": record_type,
        "count": stats.count or 0,
        "average": round(stats.average, 2) if stats.average else 0,
        "min_value": stats.min_value or 0,
        "max_value": stats.max_value or 0,
        "latest_value": latest.value if latest else 0,
        "latest_timestamp": latest.timestamp if latest else datetime.utcnow()
    }


async def delete_health_record(
    db: AsyncSession,
    user_id: UUID,
    record_id: UUID,
    ip_address: Optional[str] = None
) -> bool:
    """Delete a health record"""
    
    result = await db.execute(
        select(HealthRecord).where(
            and_(
                HealthRecord.id == record_id,
                HealthRecord.user_id == user_id
            )
        )
    )
    record = result.scalar_one_or_none()
    
    if not record:
        return False
    
    await db.delete(record)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="HEALTH_RECORD_DELETE",
        resource="health_record",
        resource_id=str(record_id),
        ip_address=ip_address
    )
    db.add(audit)
    
    return True
