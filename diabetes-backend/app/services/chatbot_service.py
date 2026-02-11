"""
Diyabet Takip API - Chatbot Service
RAG-based AI chatbot with OpenRouter
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx

from app.config import get_settings
from app.models.health import HealthRecord, HealthRecordType
from app.models.chat import ChatHistory
from app.models.audit import AuditLog

settings = get_settings()

# Medical disclaimer (required for store compliance)
MEDICAL_DISCLAIMER = """⚠️ Bu yanıt tıbbi tavsiye değildir. Sağlık kararları için lütfen doktorunuza danışın."""

# System prompt for the chatbot
SYSTEM_PROMPT = """Sen bir diyabet takip uygulaması asistanısın. Kullanıcının sağlık verilerini analiz edip bilgilendirici yanıtlar ver.

ÖNEMLİ KURALLAR:
1. ASLA tıbbi teşhis veya tedavi önerisi VERME
2. Her zaman "doktorunuza danışın" tavsiyesi ver
3. Sadece bilgilendirme amaçlı cevaplar ver
4. Kullanıcının verilerini analiz ederken genel bilgi ver
5. Türkçe yanıt ver
6. Kısa ve öz yanıtlar ver

Sen bir doktor DEĞİLSİN. Sadece bilgilendirici bir asistansın."""


async def get_user_health_context(db: AsyncSession, user_id: UUID) -> str:
    """Get recent health data for RAG context"""
    
    # Get last 30 days of data
    start_date = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(HealthRecord)
        .where(
            and_(
                HealthRecord.user_id == user_id,
                HealthRecord.timestamp >= start_date
            )
        )
        .order_by(HealthRecord.timestamp.desc())
        .limit(50)
    )
    records = result.scalars().all()
    
    if not records:
        return "Kullanıcının henüz sağlık verisi bulunmuyor."
    
    # Summarize by type
    context_parts = ["Kullanıcının son 30 günlük sağlık verileri:"]
    
    by_type = {}
    for r in records:
        if r.type not in by_type:
            by_type[r.type] = []
        by_type[r.type].append(r)
    
    type_names = {
        HealthRecordType.GLUCOSE: "Kan Şekeri",
        HealthRecordType.WEIGHT: "Kilo",
        HealthRecordType.BLOOD_PRESSURE_SYSTOLIC: "Tansiyon (Sistolik)",
        HealthRecordType.BLOOD_PRESSURE_DIASTOLIC: "Tansiyon (Diastolik)",
        HealthRecordType.HBA1C: "HbA1c",
        HealthRecordType.INSULIN: "İnsülin",
        HealthRecordType.CARBS: "Karbonhidrat",
        HealthRecordType.EXERCISE: "Egzersiz"
    }
    
    for record_type, type_records in by_type.items():
        values = [r.value for r in type_records]
        avg = sum(values) / len(values)
        name = type_names.get(record_type, record_type.value)
        unit = type_records[0].unit
        
        context_parts.append(
            f"- {name}: Ortalama {avg:.1f} {unit} (son {len(type_records)} kayıt)"
        )
        
        # Add latest value
        latest = type_records[0]
        context_parts.append(
            f"  Son değer: {latest.value} {unit} ({latest.timestamp.strftime('%d/%m/%Y')})"
        )
    
    return "\n".join(context_parts)


async def generate_chat_response(
    db: AsyncSession,
    user_id: UUID,
    question: str,
    ip_address: Optional[str] = None
) -> ChatHistory:
    """Generate AI response using OpenRouter and save to history"""
    
    # Get user health context
    health_context = await get_user_health_context(db, user_id)
    
    # Prepare messages for OpenRouter
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Kullanıcı Sağlık Bağlamı:\n{health_context}"},
        {"role": "user", "content": question}
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://diyabet-takip.com",
                    "X-Title": "Diyabet Takip Chatbot"
                },
                json={
                    "model": "mistralai/mistral-7b-instruct:free",  # Free model
                    "messages": messages,
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data["choices"][0]["message"]["content"]
            else:
                answer = "Üzgünüm, şu anda yanıt üretemiyorum. Lütfen daha sonra tekrar deneyin."
    
    except Exception as e:
        answer = "Bir hata oluştu. Lütfen daha sonra tekrar deneyin."
    
    # Add disclaimer to answer
    full_answer = f"{answer}\n\n{MEDICAL_DISCLAIMER}"
    
    # Save to chat history
    chat = ChatHistory(
        user_id=user_id,
        question=question,
        answer=full_answer
    )
    db.add(chat)
    
    # Audit log
    audit = AuditLog(
        user_id=user_id,
        action="CHAT_MESSAGE",
        ip_address=ip_address
    )
    db.add(audit)
    
    return chat


async def get_chat_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20
) -> list:
    """Get chat history for user"""
    
    result = await db.execute(
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(ChatHistory.created_at.desc())
        .limit(limit)
    )
    
    return result.scalars().all()
