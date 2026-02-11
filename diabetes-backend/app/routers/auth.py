"""
Diyabet Takip API - Auth Router
Authentication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import (
    TokenResponse,
    RefreshTokenRequest,
    MFASetupResponse,
    MFAVerifyRequest,
    MessageResponse
)
from app.services.auth_service import (
    register_user,
    login_user,
    verify_mfa,
    enable_mfa,
    confirm_mfa_setup,
    refresh_tokens
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account
    """
    try:
        ip_address = get_client_ip(request)
        user, access_token, refresh_token = await register_user(db, user_data, ip_address)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=TokenResponse | MFASetupResponse)
async def login(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password.
    If MFA is enabled, returns MFA required response.
    """
    try:
        ip_address = get_client_ip(request)
        user, access_token, refresh_token, requires_mfa = await login_user(
            db, user_data.email, user_data.password, ip_address
        )
        
        if requires_mfa:
            return MFASetupResponse(
                message="Doğrulama kodu e-posta adresinize gönderildi",
                otp_sent=True
            )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/mfa/verify", response_model=TokenResponse)
async def mfa_verify(
    mfa_data: MFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify MFA OTP code and get tokens
    """
    try:
        ip_address = get_client_ip(request)
        user, access_token, refresh_token = await verify_mfa(
            db, mfa_data.email, mfa_data.otp, ip_address
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enable MFA for current user - sends OTP to email
    """
    if current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA zaten aktif"
        )
    
    await enable_mfa(db, current_user)
    return MFASetupResponse(
        message="Doğrulama kodu e-posta adresinize gönderildi. MFA'yı aktifleştirmek için kodu doğrulayın.",
        otp_sent=True
    )


@router.post("/mfa/confirm", response_model=MessageResponse)
async def mfa_confirm(
    mfa_data: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Confirm MFA setup with OTP
    """
    try:
        await confirm_mfa_setup(db, current_user, mfa_data.otp)
        return MessageResponse(message="MFA başarıyla aktifleştirildi")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        access_token, refresh_token = await refresh_tokens(db, token_data.refresh_token)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return current_user


# Password Reset Endpoints
from app.schemas.auth import PasswordResetRequest, PasswordResetConfirm, PasswordChangeRequest
from app.services.password_reset_service import request_password_reset, reset_password, change_password


@router.post("/password/forgot", response_model=MessageResponse)
async def forgot_password(
    data: PasswordResetRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset - sends email with reset link
    """
    ip_address = get_client_ip(request)
    await request_password_reset(db, data.email, ip_address)
    # Always return success for security (don't reveal if email exists)
    return MessageResponse(
        message="Şifre sıfırlama linki e-posta adresinize gönderildi"
    )


@router.post("/password/reset", response_model=MessageResponse)
async def reset_password_endpoint(
    data: PasswordResetConfirm,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using token from email
    """
    ip_address = get_client_ip(request)
    success = await reset_password(db, data.token, data.new_password, ip_address)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçersiz veya süresi dolmuş token"
        )
    
    return MessageResponse(message="Şifreniz başarıyla değiştirildi")


@router.post("/password/change", response_model=MessageResponse)
async def change_password_endpoint(
    data: PasswordChangeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for authenticated user
    """
    ip_address = get_client_ip(request)
    success = await change_password(
        db, current_user, data.current_password, data.new_password, ip_address
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mevcut şifre yanlış"
        )
    
    return MessageResponse(message="Şifreniz başarıyla değiştirildi")
