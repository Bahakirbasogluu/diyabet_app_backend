"""
Diyabet Takip API - Rate Limiting Middleware
Redis-based rate limiting for API protection
"""

import time
from typing import Callable, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import httpx

from app.config import get_settings

settings = get_settings()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Upstash Redis
    
    Default limits:
    - 100 requests per minute for authenticated users
    - 20 requests per minute for unauthenticated users
    - Specific limits for sensitive endpoints (login, register)
    """
    
    # Endpoint-specific rate limits (requests, window_seconds)
    ENDPOINT_LIMITS = {
        "/auth/login": (5, 300),      # 5 requests per 5 minutes
        "/auth/register": (3, 600),    # 3 requests per 10 minutes
        "/auth/mfa/verify": (5, 300),  # 5 requests per 5 minutes
        "/chat": (20, 60),             # 20 requests per minute
    }
    
    # Default limits
    DEFAULT_AUTHENTICATED_LIMIT = (100, 60)    # 100/min
    DEFAULT_UNAUTHENTICATED_LIMIT = (20, 60)   # 20/min
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        
        # Determine rate limit key and limits
        endpoint_key = self._get_endpoint_key(request.url.path)
        
        if endpoint_key in self.ENDPOINT_LIMITS:
            limit, window = self.ENDPOINT_LIMITS[endpoint_key]
            rate_key = f"rate:{endpoint_key}:{client_ip}"
        elif user_id:
            limit, window = self.DEFAULT_AUTHENTICATED_LIMIT
            rate_key = f"rate:user:{user_id}"
        else:
            limit, window = self.DEFAULT_UNAUTHENTICATED_LIMIT
            rate_key = f"rate:ip:{client_ip}"
        
        # Check rate limit
        is_allowed, current_count, reset_time = await self._check_rate_limit(
            rate_key, limit, window
        )
        
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": "Çok fazla istek gönderdiniz. Lütfen bekleyin.",
                    "retry_after": reset_time
                },
                headers={
                    "Retry-After": str(reset_time),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + reset_time)
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current_count))
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from JWT token if present"""
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # We just use presence of token for now
            # Full validation happens in the endpoint
            return auth_header[7:20]  # Use part of token as key
        return None
    
    def _get_endpoint_key(self, path: str) -> str:
        """Normalize endpoint path for rate limiting"""
        # Remove trailing slash and normalize
        path = path.rstrip("/")
        
        # Check exact matches first
        if path in self.ENDPOINT_LIMITS:
            return path
        
        # Check prefix matches for specific paths
        for endpoint in self.ENDPOINT_LIMITS:
            if path.startswith(endpoint):
                return endpoint
        
        return path
    
    async def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, int, int]:
        """
        Check rate limit using Upstash Redis REST API
        Returns: (is_allowed, current_count, seconds_until_reset)
        """
        try:
            async with httpx.AsyncClient() as client:
                # Increment counter
                response = await client.post(
                    f"{settings.upstash_redis_rest_url}/incr/{key}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                    timeout=2.0
                )
                
                if response.status_code != 200:
                    return True, 0, 0  # Allow on Redis error
                
                data = response.json()
                count = data.get("result", 0)
                
                # Set expiry on first request
                if count == 1:
                    await client.post(
                        f"{settings.upstash_redis_rest_url}/expire/{key}/{window}",
                        headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                        timeout=2.0
                    )
                
                # Get TTL
                ttl_response = await client.get(
                    f"{settings.upstash_redis_rest_url}/ttl/{key}",
                    headers={"Authorization": f"Bearer {settings.upstash_redis_rest_token}"},
                    timeout=2.0
                )
                ttl = ttl_response.json().get("result", window) if ttl_response.status_code == 200 else window
                
                return count <= limit, count, max(0, ttl)
                
        except Exception as e:
            print(f"[RATE LIMIT ERROR] {e}")
            return True, 0, 0  # Allow on error
