"""
Diyabet Takip API - Auth Service
Authentication business logic
"""

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.user import UserCreate
from app.utils.security import (
    hash_password,
    verify_password,
    create_tokens,
    verify_refresh_token,
    generate_otp,
    store_otp,
    verify_otp,
    check_rate_limit
)
from app.utils.email import send_otp_email, send_welcome_email


async def register_user(
    db: AsyncSession,
    user_data: UserCreate,
    ip_address: Optional[str] = None
) -> Tuple[User, str, str]:
    """
    Register a new user
    Returns (user, access_token, refresh_token)
    """
    # Check if email already exists
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        raise ValueError("Bu e-posta adresi zaten kayıtlı")
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        name=user_data.name,
        age=user_data.age,
        diabetes_type=user_data.diabetes_type
    )
    
    db.add(user)
    await db.flush()
    
    # Create audit log
    audit = AuditLog(
        user_id=user.id,
        action="REGISTER",
        ip_address=ip_address
    )
    db.add(audit)
    
    # Create tokens
    access_token, refresh_token = create_tokens(user.id)
    
    # Send welcome email (async, don't wait)
    await send_welcome_email(user.email, user.name)
    
    return user, access_token, refresh_token


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: Optional[str] = None
) -> Tuple[User, str, str, bool]:
    """
    Login a user
    Returns (user, access_token, refresh_token, requires_mfa)
    """
    # Rate limiting
    rate_key = f"login:{email}"
    if not await check_rate_limit(rate_key, limit=5, window_seconds=300):
        raise ValueError("Çok fazla giriş denemesi. Lütfen 5 dakika bekleyin.")
    
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("E-posta veya şifre hatalı")
    
    if not user.is_active:
        raise ValueError("Hesabınız devre dışı bırakılmış")
    
    # Check if MFA is enabled
    if user.mfa_enabled:
        # Generate and send OTP
        otp = generate_otp()
        await store_otp(email, otp)
        await send_otp_email(email, otp, user.name)
        return user, "", "", True
    
    # Create tokens
    access_token, refresh_token = create_tokens(user.id)
    
    # Create audit log
    audit = AuditLog(
        user_id=user.id,
        action="LOGIN",
        ip_address=ip_address
    )
    db.add(audit)
    
    return user, access_token, refresh_token, False


async def verify_mfa(
    db: AsyncSession,
    email: str,
    otp: str,
    ip_address: Optional[str] = None
) -> Tuple[User, str, str]:
    """
    Verify MFA OTP and return tokens
    """
    # Find user
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise ValueError("Kullanıcı bulunamadı")
    
    # Verify OTP
    if not await verify_otp(email, otp):
        raise ValueError("Geçersiz veya süresi dolmuş doğrulama kodu")
    
    # Create tokens
    access_token, refresh_token = create_tokens(user.id)
    
    # Create audit log
    audit = AuditLog(
        user_id=user.id,
        action="MFA_VERIFY",
        ip_address=ip_address
    )
    db.add(audit)
    
    return user, access_token, refresh_token


async def enable_mfa(
    db: AsyncSession,
    user: User
) -> bool:
    """Enable MFA for a user and send initial OTP"""
    otp = generate_otp()
    await store_otp(user.email, otp)
    await send_otp_email(user.email, otp, user.name)
    return True


async def confirm_mfa_setup(
    db: AsyncSession,
    user: User,
    otp: str
) -> bool:
    """Confirm MFA setup by verifying OTP"""
    if not await verify_otp(user.email, otp):
        raise ValueError("Geçersiz doğrulama kodu")
    
    user.mfa_enabled = True
    return True


async def refresh_tokens(
    db: AsyncSession,
    refresh_token: str
) -> Tuple[str, str]:
    """
    Refresh access token using refresh token
    """
    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        raise ValueError("Geçersiz veya süresi dolmuş yenileme token'ı")
    
    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise ValueError("Kullanıcı bulunamadı veya hesap devre dışı")
    
    # Create new tokens
    return create_tokens(user.id)


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """Get user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
