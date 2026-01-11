import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool
from async_lru import alru_cache

from .providers.factory import ProviderFactory
from .exceptions import TickerNotFoundError, SensorError, LiquidityHaltError

@alru_cache(maxsize=128, ttl=300)
async def fetch_stock_data(ticker: str, interval: str = "1d") -> Dict[str, Any]:
    """Fetch comprehensive stock data using multi-vendor failover."""
    # Determine period based on interval
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
        
        return {
            "info": info,
            "dataframe": df,
            "returns": returns,
            "current_price": float(df['Close'].iloc[-1]),
            "provider": provider_name
        }
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
