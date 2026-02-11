"""
Diyabet Takip API - Email Service with Resend API
Production email sending for OTP, password reset, and notifications
"""

import httpx
from typing import Optional

from app.config import get_settings

settings = get_settings()


class EmailService:
    """Email service using Resend API"""
    
    BASE_URL = "https://api.resend.com/emails"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, 'resend_api_key', None)
        self.from_email = getattr(settings, 'email_from', 'noreply@diyabet-takip.com')
    
    async def send_email(
        self,
        to: str,
        subject: str,
        html: str,
        text: Optional[str] = None
    ) -> bool:
        """Send email via Resend API"""
        
        if not self.api_key:
            # Fallback to console logging in development
            print(f"[EMAIL] To: {to}")
            print(f"[EMAIL] Subject: {subject}")
            print(f"[EMAIL] Content: {text or html[:200]}...")
            return True
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.BASE_URL,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": self.from_email,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                        "text": text
                    },
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            return False


# Global instance
email_service = EmailService()


async def send_otp_email(to_email: str, otp: str, name: str = "Kullanıcı") -> bool:
    """Send OTP verification email"""
    
    subject = "Diyabet Takip - Doğrulama Kodu"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .logo {{ text-align: center; margin-bottom: 30px; }}
            .logo h1 {{ color: #2563eb; margin: 0; }}
            .otp-box {{ 
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                color: white;
                padding: 20px; 
                text-align: center; 
                font-size: 36px; 
                letter-spacing: 12px;
                font-weight: bold;
                margin: 30px 0;
                border-radius: 8px;
            }}
            .message {{ color: #374151; line-height: 1.6; }}
            .footer {{ color: #9ca3af; font-size: 12px; margin-top: 30px; text-align: center; }}
            .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">
                    <h1>🩺 Diyabet Takip</h1>
                </div>
                <p class="message">Merhaba <strong>{name}</strong>,</p>
                <p class="message">Hesabınıza giriş yapmak için aşağıdaki doğrulama kodunu kullanın:</p>
                <div class="otp-box">{otp}</div>
                <div class="warning">
                    ⏰ Bu kod <strong>5 dakika</strong> içinde geçerliliğini yitirecektir.
                </div>
                <p class="message">Eğer bu işlemi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.</p>
                <div class="footer">
                    <p>Bu otomatik bir mesajdır, lütfen yanıtlamayın.</p>
                    <p>© 2024 Diyabet Takip Uygulaması</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"Diyabet Takip - Doğrulama Kodunuz: {otp}. Bu kod 5 dakika içinde geçerliliğini yitirecektir."
    
    return await email_service.send_email(to_email, subject, html, text)


async def send_password_reset_email(to_email: str, reset_token: str, name: str = "Kullanıcı") -> bool:
    """Send password reset email"""
    
    reset_link = f"https://app.diyabet-takip.com/reset-password?token={reset_token}"
    subject = "Diyabet Takip - Şifre Sıfırlama"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .logo {{ text-align: center; margin-bottom: 30px; }}
            .logo h1 {{ color: #2563eb; margin: 0; }}
            .button {{ 
                display: inline-block;
                background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
                color: white !important;
                padding: 16px 32px; 
                text-decoration: none;
                border-radius: 8px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .message {{ color: #374151; line-height: 1.6; }}
            .footer {{ color: #9ca3af; font-size: 12px; margin-top: 30px; text-align: center; }}
            .link-box {{ background: #f3f4f6; padding: 12px; border-radius: 6px; word-break: break-all; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">
                    <h1>🩺 Diyabet Takip</h1>
                </div>
                <p class="message">Merhaba <strong>{name}</strong>,</p>
                <p class="message">Şifrenizi sıfırlamak için aşağıdaki butona tıklayın:</p>
                <p style="text-align: center;">
                    <a href="{reset_link}" class="button">Şifremi Sıfırla</a>
                </p>
                <p class="message">Veya bu linki tarayıcınıza yapıştırın:</p>
                <div class="link-box">{reset_link}</div>
                <p class="message" style="margin-top: 20px;">Bu link <strong>1 saat</strong> içinde geçerliliğini yitirecektir.</p>
                <p class="message">Eğer bu işlemi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.</p>
                <div class="footer">
                    <p>© 2024 Diyabet Takip Uygulaması</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"Şifrenizi sıfırlamak için bu linke tıklayın: {reset_link}. Link 1 saat geçerlidir."
    
    return await email_service.send_email(to_email, subject, html, text)


async def send_welcome_email(to_email: str, name: str) -> bool:
    """Send welcome email after registration"""
    
    subject = "Diyabet Takip'e Hoş Geldiniz! 🎉"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .logo {{ text-align: center; margin-bottom: 30px; }}
            .logo h1 {{ color: #2563eb; margin: 0; font-size: 28px; }}
            .hero {{ text-align: center; margin: 30px 0; }}
            .hero h2 {{ color: #1f2937; margin: 0; }}
            .features {{ margin: 30px 0; }}
            .feature {{ display: flex; align-items: center; margin: 15px 0; color: #374151; }}
            .feature-icon {{ font-size: 24px; margin-right: 15px; }}
            .footer {{ color: #9ca3af; font-size: 12px; margin-top: 30px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="logo">
                    <h1>🩺 Diyabet Takip</h1>
                </div>
                <div class="hero">
                    <h2>Hoş Geldiniz, {name}! 🎉</h2>
                </div>
                <p style="color: #374151; text-align: center;">
                    Sağlık yolculuğunuzda yanınızdayız. İşte yapabilecekleriniz:
                </p>
                <div class="features">
                    <div class="feature">
                        <span class="feature-icon">📊</span>
                        <span>Kan şekeri, kilo ve tansiyon takibi</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">📈</span>
                        <span>Detaylı grafikler ve trend analizi</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🤖</span>
                        <span>AI asistan ile kişiselleştirilmiş bilgi</span>
                    </div>
                    <div class="feature">
                        <span class="feature-icon">🔔</span>
                        <span>Hatırlatıcılar ve uyarılar</span>
                    </div>
                </div>
                <div class="footer">
                    <p>Sorularınız için: destek@diyabet-takip.com</p>
                    <p>© 2024 Diyabet Takip Uygulaması</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"Hoş Geldiniz {name}! Diyabet Takip uygulamasına kayıt olduğunuz için teşekkürler."
    
    return await email_service.send_email(to_email, subject, html, text)


async def send_high_glucose_alert_email(to_email: str, name: str, glucose_value: float) -> bool:
    """Send high glucose alert email"""
    
    subject = "⚠️ Yüksek Kan Şekeri Uyarısı"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; background: #f5f5f5; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
            .card {{ background: white; border-radius: 12px; padding: 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .alert {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 20px; margin: 20px 0; }}
            .value {{ font-size: 48px; font-weight: bold; color: #ef4444; text-align: center; }}
            .footer {{ color: #9ca3af; font-size: 12px; margin-top: 30px; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h2 style="color: #ef4444; text-align: center;">⚠️ Yüksek Kan Şekeri Uyarısı</h2>
                <p>Merhaba <strong>{name}</strong>,</p>
                <div class="alert">
                    <p style="margin: 0;">Son ölçümünüz yüksek görünüyor:</p>
                    <div class="value">{glucose_value} mg/dL</div>
                </div>
                <p style="color: #374151;">
                    Lütfen değerlerinizi kontrol edin. Şikayetleriniz devam ederse doktorunuza başvurun.
                </p>
                <div class="footer">
                    <p>⚠️ Bu bir tıbbi tavsiye değildir.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await email_service.send_email(to_email, subject, html)
