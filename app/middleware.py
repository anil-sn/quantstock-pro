import time
from typing import Dict, List
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 30):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host
        now = time.time()
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
            
        # Clean old requests
        self.requests[client_ip] = [t for t in self.requests[client_ip] if now - t < 60]
        
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return Response(content="Rate limit exceeded", status_code=429)
            
        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response

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
