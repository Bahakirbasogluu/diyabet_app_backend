"""
Diyabet Takip API - Password Reset Service
Complete password reset flow with email verification
"""

import secrets
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from app.config import get_settings
from app.models.user import User
from app.models.audit import AuditLog
from app.utils.security import hash_password
from app.utils.email import send_password_reset_email

settings = get_settings()


class PasswordResetService:
    """Password reset token management using Redis"""
    
    TOKEN_TTL = 3600  # 1 hour
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random reset token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    async def store_reset_token(email: str, token: str) -> bool:
        """Store reset token in Redis"""
        try:
            key = f"password_reset:{token}"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.upstash_redis_rest_url}/set/{key}/{email}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    # Set expiry
                    await client.post(
                        f"{settings.upstash_redis_rest_url}/expire/{key}/{PasswordResetService.TOKEN_TTL}",
                        headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                        timeout=5.0
                    )
                    return True
            return False
        except Exception as e:
            print(f"[PASSWORD RESET] Store token error: {e}")
            return False
    
    @staticmethod
    async def verify_reset_token(token: str) -> Optional[str]:
        """Verify reset token and return associated email"""
        try:
            key = f"password_reset:{token}"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.upstash_redis_rest_url}/get/{key}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    data = response.json()
                    email = data.get("result")
                    if email:
                        return email
            return None
        except Exception as e:
            print(f"[PASSWORD RESET] Verify token error: {e}")
            return None
    
    @staticmethod
    async def invalidate_reset_token(token: str) -> bool:
        """Invalidate (delete) reset token"""
        try:
            key = f"password_reset:{token}"
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{settings.upstash_redis_rest_url}/del/{key}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                    timeout=5.0
                )
                return True
        except Exception as e:
            print(f"[PASSWORD RESET] Invalidate token error: {e}")
            return False


async def request_password_reset(
    db: AsyncSession,
    email: str,
    ip_address: Optional[str] = None
) -> bool:
    """
    Request password reset - sends email with reset link
    Returns True if email was sent (or user doesn't exist - for security)
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if user exists
        return True
    
    # Generate token
    token = PasswordResetService.generate_reset_token()
    
    # Store token
    stored = await PasswordResetService.store_reset_token(user.email, token)
    if not stored:
        return False
    
    # Send email
    await send_password_reset_email(user.email, token, user.name)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="PASSWORD_RESET_REQUESTED",
        ip_address=ip_address
    )
    db.add(audit)
    
    return True


async def reset_password(
    db: AsyncSession,
    token: str,
    new_password: str,
    ip_address: Optional[str] = None
) -> bool:
    """
    Reset password using token
    """
    # Verify token
    email = await PasswordResetService.verify_reset_token(token)
    if not email:
        return False
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        return False
    
    # Update password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    
    # Invalidate token
    await PasswordResetService.invalidate_reset_token(token)
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="PASSWORD_RESET_COMPLETED",
        ip_address=ip_address
    )
    db.add(audit)
    
    return True


async def change_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
    ip_address: Optional[str] = None
) -> bool:
    """
    Change password for authenticated user
    """
    from app.utils.security import verify_password
    
    # Verify current password
    if not verify_password(current_password, user.password_hash):
        return False
    
    # Update password
    user.password_hash = hash_password(new_password)
    user.updated_at = datetime.utcnow()
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="PASSWORD_CHANGED",
        ip_address=ip_address
    )
    db.add(audit)
    
    return True
