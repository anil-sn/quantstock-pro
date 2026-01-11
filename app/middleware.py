import time
import redis
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from .settings import settings

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Global rate limiting using Redis. 
    Falls back to in-memory if Redis is not configured or unavailable.
    """
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}
        
        # Initialize Redis client
        try:
            if settings.REDIS_URL:
                self.redis = redis.from_url(settings.REDIS_URL)
            else:
                self.redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
            self.redis.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False
            print("WARNING: Redis unavailable for RateLimiter. Falling back to in-memory.")

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        now = time.time()
        window = int(now) // 60
        key = f"rate_limit:{client_ip}:{window}"

        if self.use_redis:
            try:
                count = self.redis.incr(key)
                if count == 1:
                    self.redis.expire(key, 60)
                
                if count > self.requests_per_minute:
                    return Response(content="Rate limit exceeded", status_code=429)
            except redis.RedisError:
                # If Redis fails during operation, allow request but log
                pass
        else:
            # In-memory fallback logic
            if client_ip not in self.requests:
                self.requests[client_ip] = []
            
            # Clean old requests
            self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
            
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return Response(content="Rate limit exceeded", status_code=429)
                
            self.requests[client_ip].append(now)

        return await call_next(request)

class APIKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, api_key: str = None):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip auth for health check
        if request.url.path == "/health" or request.url.path == "/metrics":
            return await call_next(request)
            
        if self.api_key:
            auth_header = request.headers.get("X-API-Key")
            if auth_header != self.api_key:
                return Response(content="Unauthorized", status_code=401)
                
        return await call_next(request)
