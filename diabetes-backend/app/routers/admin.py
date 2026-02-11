"""
Diyabet Takip API - Admin Router
Admin panel endpoints for user management and system monitoring
"""

from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from pydantic import BaseModel

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.health import HealthRecord
from app.models.chat import ChatHistory
from app.models.audit import AuditLog
from app.models.consent import ConsentLog

router = APIRouter()


# Admin schemas
class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    consent_given: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class SystemStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    mfa_enabled_users: int
    total_health_records: int
    total_chat_messages: int
    total_audit_logs: int
    users_with_consent: int
    new_users_today: int
    new_users_this_week: int


class UserDetailResponse(BaseModel):
    id: UUID
    email: str
    name: str
    age: Optional[int]
    diabetes_type: Optional[str]
    is_active: bool
    is_verified: bool
    mfa_enabled: bool
    consent_given: bool
    created_at: datetime
    updated_at: datetime
    health_record_count: int
    chat_count: int
    
    class Config:
        from_attributes = True


# Admin check dependency
async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if user is admin.
    
    Note: In production, add an 'is_admin' field to User model.
    For now, we check against a hardcoded admin email.
    """
    # TODO: Replace with proper admin role check
    admin_emails = ["admin@diyabet-takip.com"]
    
    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin yetkisi gerekli"
        )
    
    return current_user


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide statistics"""
    
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    
    # User counts
    total_users = await db.scalar(select(func.count(User.id)))
    active_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True))
    verified_users = await db.scalar(select(func.count(User.id)).where(User.is_verified == True))
    mfa_users = await db.scalar(select(func.count(User.id)).where(User.mfa_enabled == True))
    consent_users = await db.scalar(select(func.count(User.id)).where(User.consent_given == True))
    
    # New users
    new_today = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= today_start)
    )
    new_week = await db.scalar(
        select(func.count(User.id)).where(User.created_at >= week_start)
    )
    
    # Record counts
    total_records = await db.scalar(select(func.count(HealthRecord.id)))
    total_chats = await db.scalar(select(func.count(ChatHistory.id)))
    total_audits = await db.scalar(select(func.count(AuditLog.id)))
    
    return SystemStatsResponse(
        total_users=total_users or 0,
        active_users=active_users or 0,
        verified_users=verified_users or 0,
        mfa_enabled_users=mfa_users or 0,
        total_health_records=total_records or 0,
        total_chat_messages=total_chats or 0,
        total_audit_logs=total_audits or 0,
        users_with_consent=consent_users or 0,
        new_users_today=new_today or 0,
        new_users_this_week=new_week or 0
    )


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users with pagination and filtering"""
    
    query = select(User)
    count_query = select(func.count(User.id))
    
    # Filters
    if search:
        search_filter = User.email.ilike(f"%{search}%") | User.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.order_by(User.created_at.desc()).offset(offset).limit(per_page)
    
    # Execute
    total = await db.scalar(count_query) or 0
    result = await db.execute(query)
    users = result.scalars().all()
    
    return {
        "items": [AdminUserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed user information"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    # Get counts
    health_count = await db.scalar(
        select(func.count(HealthRecord.id)).where(HealthRecord.user_id == user_id)
    ) or 0
    
    chat_count = await db.scalar(
        select(func.count(ChatHistory.id)).where(ChatHistory.user_id == user_id)
    ) or 0
    
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        age=user.age,
        diabetes_type=user.diabetes_type.value if user.diabetes_type else None,
        is_active=user.is_active,
        is_verified=user.is_verified,
        mfa_enabled=user.mfa_enabled,
        consent_given=user.consent_given,
        created_at=user.created_at,
        updated_at=user.updated_at,
        health_record_count=health_count,
        chat_count=chat_count
    )


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activate/deactivate a user"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kullanıcı bulunamadı"
        )
    
    user.is_active = not user.is_active
    
    # Audit log
    audit = AuditLog(
        user_id=admin.id,
        action=f"ADMIN_{'ACTIVATE' if user.is_active else 'DEACTIVATE'}_USER",
        details={"target_user_id": str(user_id)}
    )
    db.add(audit)
    
    return {
        "message": f"Kullanıcı {'aktif' if user.is_active else 'pasif'} yapıldı",
        "user_id": str(user_id),
        "is_active": user.is_active
    }


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filtering"""
    
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
        count_query = count_query.where(AuditLog.user_id == user_id)
    
    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)
    
    total = await db.scalar(count_query) or 0
    offset = (page - 1) * per_page
    
    result = await db.execute(
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(per_page)
    )
    logs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "action": log.action,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page
    }
