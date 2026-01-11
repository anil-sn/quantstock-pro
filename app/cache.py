import json
import functools
import hashlib
import pandas as pd
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union, Callable
import redis.asyncio as redis
from async_lru import alru_cache

from .settings import settings
from .logger import pipeline_logger

class CacheManager:
    """Institutional-grade Distributed Cache Manager with In-Memory Fallback."""
    
    # Audit Fix: Incrementing this version invalidates all old cache entries globally
    CACHE_VERSION = "v2.1"

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection pool if configured."""
        try:
            url = settings.REDIS_URL or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            self.redis_client = redis.from_url(
                url, 
                password=settings.REDIS_PASSWORD,
                encoding="utf-8", 
                decode_responses=True
            )
            self.use_redis = True
            pipeline_logger.log_event("SYSTEM", "CACHE", "CONNECTED", f"Redis initialized at {settings.REDIS_HOST}")
        except Exception as e:
            self.use_redis = False
            pipeline_logger.log_error("SYSTEM", "CACHE", f"Redis connection failed: {e}. Falling back to in-memory.")

    def _get_key(self, key: str) -> str:
        """Helper to append global version to keys."""
        return f"qs:{self.CACHE_VERSION}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        if not self.use_redis or not self.redis_client:
            return None
        try:
            data = await self.redis_client.get(self._get_key(key))
            return json.loads(data) if data else None
        except Exception as e:
            pipeline_logger.log_error("SYSTEM", "CACHE", f"Redis GET failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Store a value in the cache with a specific TTL."""
        if not self.use_redis or not self.redis_client:
            return
        try:
            # Audit Fix: Deep recursive coercion for Redis compatibility
            def robust_coerce(obj):
                if isinstance(obj, (datetime, pd.Timestamp)):
                    return obj.isoformat()
                if isinstance(obj, Enum):
                    return obj.value
                if isinstance(obj, dict):
                    return {str(k): robust_coerce(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [robust_coerce(i) for i in obj]
                if isinstance(obj, tuple):
                    return [robust_coerce(i) for i in obj]
                return obj

            serialized = json.dumps(robust_coerce(value), default=str)
            await self.redis_client.set(self._get_key(key), serialized, ex=ttl)
        except Exception as e:
            pipeline_logger.log_error("SYSTEM", "CACHE", f"Redis SET failed for {key}: {repr(e)}")

    async def close(self):
        """Close the Redis connection pool."""
        if self.redis_client:
            await self.redis_client.aclose()
            self.use_redis = False
            pipeline_logger.log_event("SYSTEM", "CACHE", "DISCONNECTED", "Redis connection closed.")

    def distributed_cache(self, prefix: str, ttl: int = 300):
        """
        Decorator for distributed caching with in-memory fallback.
        """
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 1. Generate unique cache key
                arg_str = f"{args}{kwargs}"
                arg_hash = hashlib.sha256(arg_str.encode()).hexdigest()[:16]
                cache_key = f"{prefix}:{arg_hash}"
                
                if self.use_redis:
                    cached_val = await self.get(cache_key) # get() handles version prefix
                    if cached_val is not None:
                        return cached_val
                
                result = await func(*args, **kwargs)
                
                if self.use_redis and result is not None:
                    await self.set(cache_key, result, ttl=ttl) # set() handles version prefix
                
                return result
            
            # In-memory secondary layer
            return alru_cache(maxsize=settings.CACHE_MAXSIZE, ttl=ttl)(wrapper)
            
        return decorator

# Singleton Instance
cache_manager = CacheManager()