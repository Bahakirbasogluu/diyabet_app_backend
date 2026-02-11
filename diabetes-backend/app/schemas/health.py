"""
Diyabet Takip API - Health Schemas
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.models.health import HealthRecordType


class HealthRecordCreate(BaseModel):
    """Schema for creating a health record"""
    type: HealthRecordType
    value: float = Field(..., description="Ölçüm değeri")
    unit: Optional[str] = Field(None, description="Birim (otomatik atanır)")
    timestamp: Optional[datetime] = Field(None, description="Ölçüm zamanı")
    note: Optional[str] = Field(None, max_length=500)


class HealthRecordResponse(BaseModel):
    """Schema for health record response"""
    id: UUID
    user_id: UUID
    type: HealthRecordType
    value: float
    unit: str
    timestamp: datetime
    note: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HealthRecordList(BaseModel):
    """Schema for paginated health records"""
    items: List[HealthRecordResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class HealthStats(BaseModel):
    """Schema for health statistics"""
    type: HealthRecordType
    count: int
    average: float
    min_value: float
    max_value: float
    latest_value: float
    latest_timestamp: datetime
