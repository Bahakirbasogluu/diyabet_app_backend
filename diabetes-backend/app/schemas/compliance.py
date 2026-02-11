"""
Diyabet Takip API - Compliance Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ConsentRequest(BaseModel):
    """Schema for consent submission"""
    version: str = Field(..., description="Privacy policy version")
    accepted: bool = Field(..., description="Must be true")


class ConsentResponse(BaseModel):
    """Schema for consent status response"""
    consent_given: bool
    version: Optional[str]
    accepted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PrivacyPolicyResponse(BaseModel):
    """Schema for privacy policy response"""
    version: str
    title: str
    content: str
    last_updated: datetime


class TermsResponse(BaseModel):
    """Schema for terms of service response"""
    version: str
    title: str
    content: str
    last_updated: datetime


class DataDeleteRequest(BaseModel):
    """Schema for data deletion request"""
    confirm: bool = Field(..., description="Must be true to confirm deletion")
    reason: Optional[str] = Field(None, max_length=500)


class DataDeleteResponse(BaseModel):
    """Schema for data deletion response"""
    message: str
    deleted_at: datetime
    data_retained_until: Optional[datetime] = None  # For backup retention period
