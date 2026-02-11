"""
Diyabet Takip API - Chat Schemas
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Schema for chat request"""
    message: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    id: UUID
    question: str
    answer: str
    disclaimer: str = "⚠️ Bu yanıt tıbbi tavsiye değildir. Sağlık kararları için lütfen doktorunuza danışın."
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryItem(BaseModel):
    """Schema for a single chat history item"""
    id: UUID
    question: str
    answer: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    """Schema for chat history list"""
    items: List[ChatHistoryItem]
    total: int
