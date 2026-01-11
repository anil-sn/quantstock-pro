from typing import List, Optional
from .base import BaseDataProvider
from .yahoo import YahooProvider
from .polygon import PolygonProvider
from ..settings import settings

class ProviderFactory:
    """Orchestrates data providers with failover logic."""
    
    @staticmethod
    def get_providers() -> List[BaseDataProvider]:
        providers = []
        
        # 1. Primary: Polygon (if key exists)
        if hasattr(settings, "POLYGON_API_KEY") and settings.POLYGON_API_KEY:
            providers.append(PolygonProvider(settings.POLYGON_API_KEY))
            
        # 2. Fallback: Yahoo
        providers.append(YahooProvider())
        
        return providers

    @classmethod
    async def fetch_with_failover(cls, method_name: str, *args, **kwargs):
        """Execute a provider method with automatic failover."""
        last_error = None
        for provider in cls.get_providers():
            try:
                method = getattr(provider, method_name)
                return await method(*args, **kwargs), provider.get_name()
            except Exception as e:
                last_error = e
                continue
        raise last_error or RuntimeError("No providers available")
