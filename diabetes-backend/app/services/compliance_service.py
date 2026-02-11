"""
Diyabet Takip API - Compliance Service
GDPR/KVKK compliance operations
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.consent import ConsentLog
from app.models.audit import AuditLog

# Privacy policy versions and content
PRIVACY_POLICY = {
    "version": "1.0.0",
    "last_updated": datetime(2024, 1, 1),
    "title": "Gizlilik Politikası",
    "content": """
# Diyabet Takip Uygulaması Gizlilik Politikası

## 1. Veri Sorumlusu
Bu uygulama, kullanıcıların diyabet yönetimi için sağlık verilerini kaydetmelerine yardımcı olur.

## 2. Toplanan Veriler
- Hesap bilgileri (e-posta, ad)
- Sağlık verileri (kan şekeri, kilo, tansiyon vb.)
- Sohbet geçmişi

## 3. Verilerin Kullanımı
Verileriniz yalnızca:
- Size kişiselleştirilmiş sağlık takibi sunmak
- AI asistanın size yardımcı olması
- Trend ve analiz grafikleri oluşturmak
amacıyla kullanılır.

## 4. Veri Güvenliği
- Tüm veriler şifreli olarak saklanır
- HTTPS ile güvenli iletişim
- JWT tabanlı kimlik doğrulama

## 5. Veri Saklama
- Hesabınızı sildiğinizde tüm verileriniz kalıcı olarak silinir
- Yedekleme sistemlerinden 30 gün içinde temizlenir

## 6. Haklarınız (KVKK/GDPR)
- Verilerinize erişim hakkı
- Verilerinizi düzeltme hakkı
- Verilerinizi silme hakkı
- Verilerinizi dışa aktarma hakkı

## 7. İletişim
Sorularınız için: destek@diyabet-takip.com
"""
}

TERMS_OF_SERVICE = {
    "version": "1.0.0",
    "last_updated": datetime(2024, 1, 1),
    "title": "Kullanım Koşulları",
    "content": """
# Diyabet Takip Uygulaması Kullanım Koşulları

## 1. Kabul
Bu uygulamayı kullanarak aşağıdaki koşulları kabul etmiş olursunuz.

## 2. Hizmet Tanımı
Bu uygulama, diyabet hastalarının sağlık verilerini takip etmelerine yardımcı olan bir araçtır.

## 3. Tıbbi Sorumluluk Reddi
⚠️ ÖNEMLİ: Bu uygulama TIBBİ TAVSİYE VERMEZ.
- AI asistanın yanıtları sadece bilgi amaçlıdır
- Tedavi kararları için mutlaka doktorunuza danışın
- Acil durumlarda 112'yi arayın

## 4. Kullanıcı Sorumlulukları
- Doğru bilgi girişi yapmak
- Hesap güvenliğini sağlamak
- Uygulamayı kötüye kullanmamak

## 5. Hesap Silme
İstediğiniz zaman hesabınızı ve tüm verilerinizi silebilirsiniz.

## 6. Değişiklikler
Bu koşullar değişebilir. Önemli değişikliklerde bilgilendirilirsiniz.
"""
}


async def record_consent(
    db: AsyncSession,
    user: User,
    version: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
) -> ConsentLog:
    """Record user consent"""
    
    consent = ConsentLog(
        user_id=user.id,
        version=version,
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(consent)
    
    # Update user consent status
    user.consent_given = True
    
    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="CONSENT_GIVEN",
        details={"version": version},
        ip_address=ip_address
    )
    db.add(audit)
    
    return consent


async def get_consent_status(
    db: AsyncSession,
    user_id: UUID
) -> Optional[ConsentLog]:
    """Get latest consent for user"""
    
    result = await db.execute(
        select(ConsentLog)
        .where(ConsentLog.user_id == user_id)
        .order_by(ConsentLog.accepted_at.desc())
        .limit(1)
    )
    
    return result.scalar_one_or_none()


def get_privacy_policy() -> dict:
    """Get current privacy policy"""
    return PRIVACY_POLICY


def get_terms_of_service() -> dict:
    """Get current terms of service"""
    return TERMS_OF_SERVICE
