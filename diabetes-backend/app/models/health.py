"""
Diyabet Takip API - Health Record Model
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class HealthRecordType(str, PyEnum):
    """Sağlık verisi türleri"""
    GLUCOSE = "GLUCOSE"  # Kan şekeri (mg/dL)
    WEIGHT = "WEIGHT"  # Kilo (kg)
    BLOOD_PRESSURE_SYSTOLIC = "BLOOD_PRESSURE_SYSTOLIC"  # Sistolik (mmHg)
    BLOOD_PRESSURE_DIASTOLIC = "BLOOD_PRESSURE_DIASTOLIC"  # Diastolik (mmHg)
    HBA1C = "HBA1C"  # HbA1c (%)
    INSULIN = "INSULIN"  # İnsülin dozu (ünite)
    CARBS = "CARBS"  # Karbonhidrat alımı (gram)
    EXERCISE = "EXERCISE"  # Egzersiz süresi (dakika)
    HEART_RATE = "HEART_RATE"  # Nabız (bpm)


class HealthRecord(Base):
    """Health record model for storing health data"""
    
    __tablename__ = "health_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(HealthRecordType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="health_records")
    
    def __repr__(self):
        return f"<HealthRecord {self.type}: {self.value} {self.unit}>"
    
    @staticmethod
    def get_default_unit(record_type: HealthRecordType) -> str:
        """Get default unit for a health record type"""
        units = {
            HealthRecordType.GLUCOSE: "mg/dL",
            HealthRecordType.WEIGHT: "kg",
            HealthRecordType.BLOOD_PRESSURE_SYSTOLIC: "mmHg",
            HealthRecordType.BLOOD_PRESSURE_DIASTOLIC: "mmHg",
            HealthRecordType.HBA1C: "%",
            HealthRecordType.INSULIN: "ünite",
            HealthRecordType.CARBS: "g",
            HealthRecordType.EXERCISE: "dakika",
            HealthRecordType.HEART_RATE: "bpm"
        }
        return units.get(record_type, "")
