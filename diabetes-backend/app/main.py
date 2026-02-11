"""
Diyabet Takip API - Main Application
FastAPI app initialization and configuration
"""

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import httpx

from app.config import get_settings
from app.database import init_db, close_db, get_db
from app.middleware import RateLimitMiddleware, LoggingMiddleware

# Import routers
from app.routers import auth, users, health, analytics, chatbot, compliance, cgm
from app.routers import admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Diyabet hastalarının sağlık verilerini takip edebileceği mobil uygulamanın backend API'si. KVKK/GDPR uyumlu, Store-ready.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware (order matters - last added runs first)
# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production'da spesifik origin'ler kullanılmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Logging
app.add_middleware(LoggingMiddleware)

# 3. Rate Limiting
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(health.router, prefix="/health", tags=["Health Data"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(chatbot.router, prefix="/chat", tags=["AI Chatbot"])
app.include_router(compliance.router, prefix="/compliance", tags=["Compliance & Privacy"])
app.include_router(cgm.router, prefix="/cgm", tags=["CGM Integration"])
app.include_router(admin.router, prefix="/admin", tags=["Admin Panel"])


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Diyabet Takip API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }


@app.get("/health", tags=["Root"])
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check endpoint.
    Checks database and Redis connectivity.
    """
    checks = {
        "api": "ok",
        "database": "unknown",
        "redis": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    overall = True
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)[:100]}"
        overall = False
    
    # Check Redis (Upstash)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.upstash_redis_rest_url}/ping",
                headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                timeout=3.0
            )
            if response.status_code == 200:
                checks["redis"] = "ok"
            else:
                checks["redis"] = f"error: status {response.status_code}"
                overall = False
    except Exception as e:
        checks["redis"] = f"error: {str(e)[:100]}"
        overall = False
    
    checks["status"] = "healthy" if overall else "degraded"
    
    return checks
