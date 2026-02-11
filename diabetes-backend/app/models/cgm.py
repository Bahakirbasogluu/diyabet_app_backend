"""
Diyabet Takip API - CGM (Continuous Glucose Monitor) Models
Skeleton for future CGM device integration
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CGMDevice(Base):
    """CGM device model for tracking connected devices"""
    
    __tablename__ = "cgm_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_type = Column(String(50), nullable=False)  # e.g., "DEXCOM_G6", "FREESTYLE_LIBRE", "MEDTRONIC"
    device_id = Column(String(100), nullable=True)  # External device identifier
    device_name = Column(String(100), nullable=True)  # User-friendly name
    is_active = Column(Boolean, default=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="cgm_devices")
    readings = relationship("CGMReading", back_populates="device", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CGMDevice {self.device_type}>"


class CGMReading(Base):
    """CGM reading model for storing continuous glucose readings"""
    
    __tablename__ = "cgm_readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("cgm_devices.id", ondelete="CASCADE"), nullable=False, index=True)
    glucose_value = Column(Float, nullable=False)  # mg/dL
    trend = Column(String(20), nullable=True)  # e.g., "RISING", "FALLING", "STABLE"
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    device = relationship("CGMDevice", back_populates="readings")
    
    def __repr__(self):
        return f"<CGMReading {self.glucose_value} mg/dL>"
