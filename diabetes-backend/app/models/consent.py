"""
Diyabet Takip API - Consent Log Model
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ConsentLog(Base):
    """Consent log model for GDPR/KVKK compliance"""
    
    __tablename__ = "consent_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(20), nullable=False)  # Privacy policy version
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(255), nullable=True)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="consent_logs")
    
    def __repr__(self):
        return f"<ConsentLog {self.user_id} v{self.version}>"
