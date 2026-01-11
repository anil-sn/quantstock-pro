from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd

class BaseDataProvider(ABC):
    """Abstract Base Class for financial data providers."""
    
    @abstractmethod
    async def fetch_price_history(self, ticker: str, interval: str, period: str) -> pd.DataFrame:
        """Fetch historical OHLCV data."""
        pass

    @abstractmethod
    async def fetch_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch fundamental company information."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return provider name."""
        pass
