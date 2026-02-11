"""
Diyabet Takip API - Validators
Input validation utilities
"""

import re
from typing import Optional
from app.models.health import HealthRecordType


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır"
    
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az bir büyük harf içermelidir"
    
    if not re.search(r'[a-z]', password):
        return False, "Şifre en az bir küçük harf içermelidir"
    
    if not re.search(r'\d', password):
        return False, "Şifre en az bir rakam içermelidir"
    
    return True, None


def validate_health_value(record_type: HealthRecordType, value: float) -> tuple[bool, Optional[str]]:
    """
    Validate health record value is within reasonable range
    Returns (is_valid, error_message)
    """
    ranges = {
        HealthRecordType.GLUCOSE: (20, 600),  # mg/dL
        HealthRecordType.WEIGHT: (20, 300),  # kg
        HealthRecordType.BLOOD_PRESSURE_SYSTOLIC: (60, 250),  # mmHg
        HealthRecordType.BLOOD_PRESSURE_DIASTOLIC: (30, 150),  # mmHg
        HealthRecordType.HBA1C: (3, 20),  # %
        HealthRecordType.INSULIN: (0, 200),  # units
        HealthRecordType.CARBS: (0, 500),  # grams
        HealthRecordType.EXERCISE: (0, 480),  # minutes (8 hours max)
    }
    
    if record_type not in ranges:
        return True, None
    
    min_val, max_val = ranges[record_type]
    
    if value < min_val or value > max_val:
        return False, f"Değer {min_val} ile {max_val} arasında olmalıdır"
    
    return True, None


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize and truncate string input"""
    if not text:
        return ""
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Truncate to max length
    text = text[:max_length]
    
    # Strip whitespace
    text = text.strip()
    
    return text
