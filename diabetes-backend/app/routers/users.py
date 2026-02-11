"""
Diyabet Takip API - Users Router
User profile management endpoints
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies import get_current_user, get_client_ip
from app.models.user import User
from app.models.health import HealthRecord
from app.models.chat import ChatHistory
from app.models.consent import ConsentLog
from app.models.audit import AuditLog
from app.schemas.user import UserUpdate, UserResponse, UserExport
from app.schemas.auth import MessageResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user profile
    """
    # Update fields
    if update_data.name is not None:
        current_user.name = update_data.name
    if update_data.age is not None:
        current_user.age = update_data.age
    if update_data.diabetes_type is not None:
        current_user.diabetes_type = update_data.diabetes_type
    if update_data.fcm_token is not None:
        current_user.fcm_token = update_data.fcm_token
    
    current_user.updated_at = datetime.utcnow()
    
    # Create audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="PROFILE_UPDATE",
        ip_address=get_client_ip(request)
    )
    db.add(audit)
    
    return current_user


@router.delete("/me", response_model=MessageResponse)
async def delete_account(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user account and all associated data (GDPR/KVKK)
    This is a hard delete - all data will be permanently removed
    """
    # Create final audit log before deletion
    audit = AuditLog(
        user_id=current_user.id,
        action="ACCOUNT_DELETE",
        ip_address=get_client_ip(request)
    )
    db.add(audit)
    await db.flush()
    
    # Delete user (cascade will delete related data)
    await db.delete(current_user)
    
    return MessageResponse(
        message="Hesabınız ve tüm verileriniz başarıyla silindi"
    )


@router.get("/export", response_model=UserExport)
async def export_data(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export all user data (GDPR/KVKK data portability)
    """
    # Get health records
    health_result = await db.execute(
        select(HealthRecord)
        .where(HealthRecord.user_id == current_user.id)
        .order_by(HealthRecord.timestamp.desc())
    )
    health_records = health_result.scalars().all()
    
    # Get chat history
    chat_result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
    )
    chat_history = chat_result.scalars().all()
    
    # Get consent logs
    consent_result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.user_id == current_user.id)
        .order_by(ConsentLog.accepted_at.desc())
    )
    consent_logs = consent_result.scalars().all()
    
    # Create audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DATA_EXPORT",
        ip_address=get_client_ip(request)
    )
    db.add(audit)
    
    return UserExport(
        user=current_user,
        health_records=[{
            "id": str(r.id),
            "type": r.type.value,
            "value": r.value,
            "unit": r.unit,
            "timestamp": r.timestamp.isoformat(),
            "note": r.note
        } for r in health_records],
        chat_history=[{
            "id": str(c.id),
            "question": c.question,
            "answer": c.answer,
            "created_at": c.created_at.isoformat()
        } for c in chat_history],
        consent_logs=[{
            "id": str(cl.id),
            "version": cl.version,
            "accepted_at": cl.accepted_at.isoformat()
        } for cl in consent_logs],
        exported_at=datetime.utcnow()
    )
