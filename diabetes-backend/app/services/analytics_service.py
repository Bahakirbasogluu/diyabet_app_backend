"""
Diyabet Takip API - Analytics Service
Analytics and trend calculation logic
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.health import HealthRecord, HealthRecordType


async def get_summary(
    db: AsyncSession,
    user_id: UUID,
    days: int = 7
) -> Dict[str, Any]:
    """Get summary statistics for all health metrics"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get counts by type
    result = await db.execute(
        select(
            HealthRecord.type,
            func.count(HealthRecord.id).label("count"),
            func.avg(HealthRecord.value).label("average"),
            func.min(HealthRecord.value).label("min_value"),
            func.max(HealthRecord.value).label("max_value")
        )
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.timestamp >= start_date
            )
        )
        .group_by(HealthRecord.type)
    )
    
    stats = {}
    for row in result:
        stats[row.type.value] = {
            "count": row.count,
            "average": round(row.average, 2) if row.average else 0,
            "min": row.min_value or 0,
            "max": row.max_value or 0
        }
    
    # Get latest glucose value
    glucose_result = await db.execute(
        select(HealthRecord)
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.type == HealthRecordType.GLUCOSE
            )
        )
        .order_by(HealthRecord.timestamp.desc())
        .limit(1)
    )
    latest_glucose = glucose_result.scalar_one_or_none()
    
    # Calculate glucose status
    glucose_status = "normal"
    if latest_glucose:
        if latest_glucose.value < 70:
            glucose_status = "low"
        elif latest_glucose.value > 180:
            glucose_status = "high"
        elif latest_glucose.value > 140:
            glucose_status = "elevated"
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "stats_by_type": stats,
        "latest_glucose": {
            "value": latest_glucose.value if latest_glucose else None,
            "timestamp": latest_glucose.timestamp.isoformat() if latest_glucose else None,
            "status": glucose_status
        },
        "total_records": sum(s["count"] for s in stats.values())
    }


async def get_trends(
    db: AsyncSession,
    user_id: UUID,
    record_type: HealthRecordType,
    days: int = 30
) -> Dict[str, Any]:
    """Get trend data for charts"""
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all records in the period
    result = await db.execute(
        select(HealthRecord)
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.type == record_type,
                HealthRecord.timestamp >= start_date
            )
        )
        .order_by(HealthRecord.timestamp.asc())
    )
    records = result.scalars().all()
    
    if not records:
        return {
            "type": record_type.value,
            "period_days": days,
            "data_points": [],
            "trend": "no_data"
        }
    
    # Create data points for chart
    data_points = [
        {
            "timestamp": r.timestamp.isoformat(),
            "value": r.value,
            "date": r.timestamp.strftime("%d/%m")
        }
        for r in records
    ]
    
    # Calculate trend
    values = [r.value for r in records]
    if len(values) >= 2:
        first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
        second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half_avg > first_half_avg * 1.05:
            trend = "increasing"
        elif second_half_avg < first_half_avg * 0.95:
            trend = "decreasing"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    # Daily aggregates
    daily_data = {}
    for r in records:
        date_key = r.timestamp.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = []
        daily_data[date_key].append(r.value)
    
    daily_averages = [
        {
            "date": date,
            "average": round(sum(vals) / len(vals), 2),
            "count": len(vals)
        }
        for date, vals in sorted(daily_data.items())
    ]
    
    return {
        "type": record_type.value,
        "period_days": days,
        "data_points": data_points,
        "daily_averages": daily_averages,
        "trend": trend,
        "total_count": len(records),
        "average": round(sum(values) / len(values), 2),
        "min": min(values),
        "max": max(values)
    }
