"""
Diyabet Takip API - User Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from app.models.user import DiabetesType


# Request schemas
class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 karakter")
    name: str = Field(..., min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    diabetes_type: Optional[DiabetesType] = None


class UserUpdate(BaseModel):
    """Schema for user profile update"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    diabetes_type: Optional[DiabetesType] = None
    fcm_token: Optional[str] = None


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


# Response schemas
class UserResponse(BaseModel):
    """Schema for user response"""
    id: UUID
    email: str
    name: str
    age: Optional[int]
    diabetes_type: Optional[DiabetesType]
    consent_given: bool
    mfa_enabled: bool
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserExport(BaseModel):
    """Schema for GDPR data export"""
    user: UserResponse
    health_records: list
    chat_history: list
    consent_logs: list
    exported_at: datetime
