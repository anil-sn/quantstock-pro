import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool
from async_lru import alru_cache

from .providers.factory import ProviderFactory
from .exceptions import TickerNotFoundError, SensorError, LiquidityHaltError
from .cache import cache_manager

async def fetch_stock_data(ticker: str, interval: str = "1d") -> Dict[str, Any]:
    """Fetch comprehensive stock data using multi-vendor failover with distributed caching."""
    cache_key = f"market_v3.2:{ticker.upper()}:{interval}"
    
    # 1. Try to get from cache first
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        # Reconstruct DataFrame from serialized dict (index orientation)
        cached_data["dataframe"] = pd.DataFrame.from_dict(cached_data["dataframe"], orient="index")
        # Re-parse index
        cached_data["dataframe"].index = pd.to_datetime(cached_data["dataframe"].index)
        return cached_data

    # 2. Cache miss - Fetch from providers
    period = "1y"
    if interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]:
        period = "60d"

    try:
        # Fetch history with failover
        df, provider_name = await ProviderFactory.fetch_with_failover(
            "fetch_price_history", ticker=ticker, interval=interval, period=period
        )
        
        # Fetch info with failover
        info, _ = await ProviderFactory.fetch_with_failover("fetch_ticker_info", ticker=ticker)

        if df.empty:
            raise TickerNotFoundError(f"No data found for {ticker} via {provider_name}")
            
        if len(df) < 20:
            raise LiquidityHaltError(f"Insufficient historical bars for {ticker} via {provider_name}")
        
        # Calculate returns
        returns = df['Close'].pct_change().dropna()
        
        result = {
            "info": info,
            "dataframe": df, # This will be serialized to dict by cache_manager
            "returns": returns.tolist(), # Serialize Series to list
            "current_price": float(df['Close'].iloc[-1]),
            "provider": provider_name
        }
        
        # 3. Store in cache
        # Convert DF to dict for JSON serialization
        serializable_result = result.copy()
        serializable_result["dataframe"] = df.to_dict(orient="index") # Use index orientation for string keys
        await cache_manager.set(cache_key, serializable_result, ttl=300) # 5 min TTL
        
        return result
    except (TickerNotFoundError, LiquidityHaltError):
        raise
    except Exception as e:
        raise SensorError(f"Failed to fetch data for {ticker}: {str(e)}")

def fetch_ohlcv(symbol: str, period="1y", interval="1d") -> pd.DataFrame:
    """Synchronous wrapper for internal technical analysis calls if needed"""
    df = yf.Ticker(symbol).history(period=period, interval=interval)
    if df is None or df.empty:
        raise ValueError(f"No market data available for symbol: {symbol}")
    return df
