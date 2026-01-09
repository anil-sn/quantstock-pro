import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool

async def fetch_stock_data(ticker: str, interval: str = "1d") -> Dict[str, Any]:
    """Fetch comprehensive stock data with validation"""
    try:
        stock = yf.Ticker(ticker)
        
        # Determine period based on interval to ensure enough data
        period = "1y"
        if interval in ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"]:
            period = "1mo"  # Short period for intraday to save tokens/time
        
        # Get info and history in parallel
        info_future = run_in_threadpool(lambda: stock.info)
        history_future = run_in_threadpool(
            lambda: stock.history(period=period, interval=interval)
        )
        
        info, df = await asyncio.gather(info_future, history_future)
        
        if df.empty or len(df) < 50:
            raise ValueError(f"Insufficient data for {ticker}")
        
        # Calculate returns
        returns = df['Close'].pct_change().dropna()
        
        return {
            "info": info,
            "dataframe": df,
            "returns": returns,
            "current_price": float(df['Close'].iloc[-1])
        }
    except Exception as e:
        raise ValueError(f"Failed to fetch data for {ticker}: {str(e)}")

def fetch_ohlcv(symbol: str, period="1y", interval="1d") -> pd.DataFrame:
    """Synchronous wrapper for internal technical analysis calls if needed"""
    df = yf.Ticker(symbol).history(period=period, interval=interval)
    if df is None or df.empty:
        raise ValueError(f"No market data available for symbol: {symbol}")
    return df
