import yfinance as yf
import pandas as pd
from typing import Dict, Any
from fastapi.concurrency import run_in_threadpool
from .base import BaseDataProvider
from ..exceptions import TickerNotFoundError, SensorError

class YahooProvider(BaseDataProvider):
    """Fallback provider using yfinance."""

    async def fetch_price_history(self, ticker: str, interval: str, period: str) -> pd.DataFrame:
        try:
            stock = yf.Ticker(ticker)
            df = await run_in_threadpool(
                lambda: stock.history(period=period, interval=interval)
            )
            if df.empty:
                raise TickerNotFoundError(f"Yahoo: No data for {ticker}")
            return df
        except TickerNotFoundError:
            raise
        except Exception as e:
            raise SensorError(f"Yahoo History Error: {e}")

    async def fetch_ticker_info(self, ticker: str) -> Dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            info = await run_in_threadpool(lambda: stock.info)
            
            # Junk detection: yfinance sometimes returns a dict with only meta keys
            # but missing core business identity fields.
            is_junk = not info or len(info) < 10 or not (info.get("longName") or info.get("shortName"))
            
            if is_junk:
                # Fallback to reconstructing from fast_info and statements
                fast = await run_in_threadpool(lambda: stock.fast_info)
                income = await run_in_threadpool(lambda: stock.income_stmt)
                
                reconstructed = {
                    "quoteType": fast.get("quoteType", "EQUITY"),
                    "marketCap": fast.get("market_cap"),
                    "longName": ticker.upper(),
                    "currentPrice": fast.get("last_price")
                }
                if income is not None and not income.empty:
                    latest = income.iloc[:, 0]
                    reconstructed["totalRevenue"] = latest.get("Total Revenue")
                    reconstructed["netIncome"] = latest.get("Net Income")
                return reconstructed
            return info
        except Exception as e:
            from ..logger import pipeline_logger
            pipeline_logger.log_error(ticker, "YAHOO_PROVIDER", f"Info fetch failed: {e}")
            return {}

    def get_name(self) -> str:
        return "YahooFinance"
