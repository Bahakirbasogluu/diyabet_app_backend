"""
Diyabet Takip API - Security Utilities
JWT, password hashing, and rate limiting
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID

from jose import jwt, JWTError
from passlib.context import CryptContext
import httpx

from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    }
    
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_tokens(user_id: UUID) -> Tuple[str, str]:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return access_token, refresh_token


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[str]:
    """Verify an access token and return user_id"""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload.get("sub")
    return None


def verify_refresh_token(token: str) -> Optional[str]:
    """Verify a refresh token and return user_id"""
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        return payload.get("sub")
    return None


def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


async def check_rate_limit(key: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """
    Check if a rate limit has been exceeded using Upstash Redis REST API
    Returns True if request is allowed, False if rate limited
    """
    try:
        async with httpx.AsyncClient() as client:
            # Increment the counter
            response = await client.post(
                f"{settings.upstash_redis_rest_url}/incr/{key}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
            )
            data = response.json()
            count = data.get("result", 0)
            
            # Set expiry on first request
            if count == 1:
                await client.post(
                    f"{settings.upstash_redis_rest_url}/expire/{key}/{window_seconds}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
                )
            
            return count <= limit
    except Exception:
        # If Redis is unavailable, allow the request
        return True


async def store_otp(email: str, otp: str, expire_seconds: int = 300) -> bool:
    """Store OTP in Redis with expiration"""
    try:
        async with httpx.AsyncClient() as client:
            key = f"otp:{email}"
            response = await client.post(
                f"{settings.upstash_redis_rest_url}/setex/{key}/{expire_seconds}/{otp}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
            )
            return response.status_code == 200
    except Exception:
        return False


async def verify_otp(email: str, otp: str) -> bool:
    """Verify OTP from Redis"""
    try:
        async with httpx.AsyncClient() as client:
            key = f"otp:{email}"
            response = await client.get(
                f"{settings.upstash_redis_rest_url}/get/{key}",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
            )
            data = response.json()
            stored_otp = data.get("result")
            
            if stored_otp == otp:
                # Delete OTP after successful verification
                await client.post(
                    f"{settings.upstash_redis_rest_url}/del/{key}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"}
                )
                return True
            return False
    except Exception:
        return False
