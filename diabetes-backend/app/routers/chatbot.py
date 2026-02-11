"""
Diyabet Takip API - Chatbot Router
AI Chatbot endpoints
"""

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryResponse, ChatHistoryItem
from app.services.chatbot_service import generate_chat_response, get_chat_history

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    data: ChatRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to the AI chatbot.
    The response is personalized based on the user's health data.
    
    ⚠️ All responses include a medical disclaimer.
    """
    chat_record = await generate_chat_response(
        db, current_user.id, data.message, get_client_ip(request)
    )
    
    return ChatResponse(
        id=chat_record.id,
        question=chat_record.question,
        answer=chat_record.answer,
        created_at=chat_record.created_at
    )


@router.get("/history", response_model=ChatHistoryResponse)
async def history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat history
    """
    chats = await get_chat_history(db, current_user.id, limit)
    
    return ChatHistoryResponse(
        items=[ChatHistoryItem(
            id=c.id,
            question=c.question,
            answer=c.answer,
            created_at=c.created_at
        ) for c in chats],
        total=len(chats)
    )
