"""
Diyabet Takip API - Configuration Module
Environment variables and settings management
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App
    app_name: str = Field(default="Diyabet Takip API")
    debug: bool = Field(default=False)
    
    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anon key")
    database_url: str = Field(..., description="PostgreSQL connection string")
    
    # Upstash Redis
    upstash_redis_rest_url: str = Field(..., description="Upstash Redis REST URL")
    upstash_redis_rest_token: str = Field(..., description="Upstash Redis REST token")
    
    # OpenRouter
    openrouter_api_key: str = Field(..., description="OpenRouter API key")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    
    # JWT
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)
    
    # Email (Resend)
    resend_api_key: str = Field(default="", description="Resend API key for email sending")
    email_from: str = Field(default="noreply@diyabet-takip.com", description="From email address")
    
    # Firebase
    firebase_credentials_path: str = Field(default="firebase-adminsdk.json", description="Path to Firebase credentials")
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/0", description="Celery broker URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
