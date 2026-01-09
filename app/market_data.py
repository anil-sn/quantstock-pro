import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool

async def fetch_stock_data(ticker: str) -> Dict[str, Any]:
    """Fetch comprehensive stock data with validation"""
    try:
        stock = yf.Ticker(ticker)
        
        # Get info and history in parallel
        info_future = run_in_threadpool(lambda: stock.info)
        history_future = run_in_threadpool(
            lambda: stock.history(period="1y", interval="1d")
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
