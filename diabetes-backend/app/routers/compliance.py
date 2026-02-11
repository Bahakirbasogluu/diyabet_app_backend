"""
Diyabet Takip API - Compliance Router
Privacy, terms, and consent endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_client_ip
from app.models.user import User
from app.schemas.compliance import (
    ConsentRequest,
    ConsentResponse,
    PrivacyPolicyResponse,
    TermsResponse
)
from app.schemas.auth import MessageResponse
from app.services.compliance_service import (
    record_consent,
    get_consent_status,
    get_privacy_policy,
    get_terms_of_service
)

router = APIRouter()


@router.post("/consent", response_model=MessageResponse)
async def submit_consent(
    data: ConsentRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit consent for privacy policy
    """
    if not data.accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gizlilik politikasını kabul etmelisiniz"
        )
    
    user_agent = request.headers.get("User-Agent")
    await record_consent(
        db, current_user, data.version, get_client_ip(request), user_agent
    )
    
    return MessageResponse(message="Onayınız kaydedildi")


@router.get("/consent", response_model=ConsentResponse)
async def get_consent(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current consent status
    """
    consent = await get_consent_status(db, current_user.id)
    
    return ConsentResponse(
        consent_given=current_user.consent_given,
        version=consent.version if consent else None,
        accepted_at=consent.accepted_at if consent else None
    )


@router.get("/privacy-policy", response_model=PrivacyPolicyResponse)
async def privacy_policy():
    """
    Get current privacy policy
    """
    policy = get_privacy_policy()
    return PrivacyPolicyResponse(
        version=policy["version"],
        title=policy["title"],
        content=policy["content"],
        last_updated=policy["last_updated"]
    )


@router.get("/terms", response_model=TermsResponse)
async def terms():
    """
    Get current terms of service
    """
    tos = get_terms_of_service()
    return TermsResponse(
        version=tos["version"],
        title=tos["title"],
        content=tos["content"],
        last_updated=tos["last_updated"]
    )
